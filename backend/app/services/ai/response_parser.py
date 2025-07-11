"""AI 응답 파싱 및 검증"""
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ResponseParser:
    """AI 응답 파싱 및 검증 클래스"""
    
    @staticmethod
    def parse_json_response(response: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        JSON 응답 파싱
        
        Args:
            response: AI 응답 문자열
            
        Returns:
            (파싱된 데이터, 에러 메시지)
        """
        try:
            # 코드 블록 제거
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
                
            # JSON 파싱
            data = json.loads(response.strip())
            return data, None
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON parsing error: {str(e)}"
            logger.error(f"{error_msg}\nResponse: {response[:200]}...")
            return None, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected parsing error: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
            
    @staticmethod
    def validate_news_analysis(analysis: Dict) -> Tuple[bool, List[str]]:
        """
        뉴스 분석 결과 검증
        
        Args:
            analysis: 분석 결과 딕셔너리
            
        Returns:
            (유효 여부, 에러 메시지 리스트)
        """
        errors = []
        required_fields = ["summary", "sentiment", "companies_mentioned"]
        
        # 필수 필드 검사
        for field in required_fields:
            if field not in analysis:
                errors.append(f"Missing required field: {field}")
                
        # 감정 분석 검증
        if "sentiment" in analysis:
            sentiment = analysis["sentiment"]
            if not isinstance(sentiment, dict):
                errors.append("Sentiment must be a dictionary")
            else:
                if "overall" not in sentiment:
                    errors.append("Sentiment missing 'overall' field")
                elif sentiment["overall"] not in ["positive", "negative", "neutral"]:
                    errors.append(f"Invalid sentiment value: {sentiment['overall']}")
                    
                if "score" in sentiment:
                    score = sentiment["score"]
                    if not isinstance(score, (int, float)) or not 0 <= score <= 1:
                        errors.append(f"Invalid sentiment score: {score}")
                        
        # 기업 목록 검증
        if "companies_mentioned" in analysis:
            companies = analysis["companies_mentioned"]
            if not isinstance(companies, list):
                errors.append("companies_mentioned must be a list")
            else:
                for i, company in enumerate(companies):
                    if not isinstance(company, dict):
                        errors.append(f"Company {i} must be a dictionary")
                    elif "name" not in company:
                        errors.append(f"Company {i} missing 'name' field")
                        
        return len(errors) == 0, errors
        
    @staticmethod
    def validate_company_extraction(extraction: Dict) -> Tuple[bool, List[str]]:
        """
        기업 추출 결과 검증
        
        Args:
            extraction: 추출 결과 딕셔너리
            
        Returns:
            (유효 여부, 에러 메시지 리스트)
        """
        errors = []
        
        if "companies" not in extraction:
            errors.append("Missing 'companies' field")
            return False, errors
            
        companies = extraction["companies"]
        if not isinstance(companies, list):
            errors.append("'companies' must be a list")
            return False, errors
            
        for i, company in enumerate(companies):
            if not isinstance(company, dict):
                errors.append(f"Company {i} must be a dictionary")
                continue
                
            # 필수 필드
            if "name" not in company:
                errors.append(f"Company {i} missing 'name'")
            if "confidence" in company:
                conf = company["confidence"]
                if not isinstance(conf, (int, float)) or not 0 <= conf <= 1:
                    errors.append(f"Company {i} invalid confidence: {conf}")
                    
        return len(errors) == 0, errors
        
    @staticmethod
    def validate_impact_analysis(impact: Dict) -> Tuple[bool, List[str]]:
        """
        영향도 분석 결과 검증
        
        Args:
            impact: 영향도 분석 딕셔너리
            
        Returns:
            (유효 여부, 에러 메시지 리스트)
        """
        errors = []
        required_fields = ["impact_score", "confidence_score", "direction", "reasoning"]
        
        for field in required_fields:
            if field not in impact:
                errors.append(f"Missing required field: {field}")
                
        # 점수 검증
        for score_field in ["impact_score", "confidence_score"]:
            if score_field in impact:
                score = impact[score_field]
                if not isinstance(score, (int, float)) or not 0 <= score <= 1:
                    errors.append(f"Invalid {score_field}: {score}")
                    
        # 방향성 검증
        if "direction" in impact:
            valid_directions = ["positive", "negative", "mixed", "neutral"]
            if impact["direction"] not in valid_directions:
                errors.append(f"Invalid direction: {impact['direction']}")
                
        return len(errors) == 0, errors
        
    @staticmethod
    def normalize_company_name(name: str) -> str:
        """
        회사명 정규화
        
        Args:
            name: 원본 회사명
            
        Returns:
            정규화된 회사명
        """
        # 일반적인 접미사 제거
        suffixes = [
            " Inc.", " Inc", " Corp.", " Corp", " Corporation",
            " Ltd.", " Ltd", " Limited", " Co.", " Co",
            " LLC", " LLP", " plc", " PLC", " AG", " SA", " GmbH"
        ]
        
        normalized = name.strip()
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
                break
                
        # 괄호 내용 제거 (ticker 등)
        if "(" in normalized and ")" in normalized:
            normalized = normalized.split("(")[0].strip()
            
        return normalized
        
    @staticmethod
    def extract_key_metrics(analysis: Dict) -> Dict[str, Any]:
        """
        분석 결과에서 주요 지표 추출
        
        Args:
            analysis: 전체 분석 결과
            
        Returns:
            주요 지표 딕셔너리
        """
        metrics = {
            "sentiment_score": 0.5,
            "sentiment_label": "neutral",
            "impact_score": 0.0,
            "confidence": 0.0,
            "company_count": 0,
            "primary_companies": []
        }
        
        # 감정 분석 지표
        if "sentiment" in analysis:
            sentiment = analysis["sentiment"]
            metrics["sentiment_score"] = sentiment.get("score", 0.5)
            metrics["sentiment_label"] = sentiment.get("overall", "neutral")
            metrics["confidence"] = sentiment.get("confidence", 0.0)
            
        # 영향도 지표
        if "impact_score" in analysis:
            metrics["impact_score"] = analysis["impact_score"]
            
        # 기업 관련 지표
        if "companies_mentioned" in analysis:
            companies = analysis["companies_mentioned"]
            metrics["company_count"] = len(companies)
            
            # 주요 기업 추출 (relevance가 primary인 것들)
            primary = [c for c in companies if c.get("relevance") == "primary"]
            metrics["primary_companies"] = [c["name"] for c in primary[:5]]
            
        return metrics
        
    @staticmethod
    def merge_analysis_results(results: List[Dict]) -> Dict[str, Any]:
        """
        여러 분석 결과 병합
        
        Args:
            results: 분석 결과 리스트
            
        Returns:
            병합된 결과
        """
        if not results:
            return {}
            
        if len(results) == 1:
            return results[0]
            
        # 병합된 결과 초기화
        merged = {
            "companies_mentioned": [],
            "sentiment": {
                "overall": "neutral",
                "score": 0.0,
                "confidence": 0.0
            },
            "key_topics": set(),
            "investment_signals": []
        }
        
        # 회사 목록 병합 (중복 제거)
        seen_companies = set()
        for result in results:
            if "companies_mentioned" in result:
                for company in result["companies_mentioned"]:
                    normalized_name = ResponseParser.normalize_company_name(company["name"])
                    if normalized_name not in seen_companies:
                        seen_companies.add(normalized_name)
                        merged["companies_mentioned"].append(company)
                        
        # 감정 점수 평균
        sentiment_scores = []
        sentiment_labels = []
        for result in results:
            if "sentiment" in result:
                sentiment = result["sentiment"]
                if "score" in sentiment:
                    sentiment_scores.append(sentiment["score"])
                if "overall" in sentiment:
                    sentiment_labels.append(sentiment["overall"])
                    
        if sentiment_scores:
            merged["sentiment"]["score"] = sum(sentiment_scores) / len(sentiment_scores)
            
        # 가장 많이 나타난 감정 레이블
        if sentiment_labels:
            from collections import Counter
            label_counts = Counter(sentiment_labels)
            merged["sentiment"]["overall"] = label_counts.most_common(1)[0][0]
            
        # 주제 병합
        for result in results:
            if "key_topics" in result:
                merged["key_topics"].update(result["key_topics"])
                
        merged["key_topics"] = list(merged["key_topics"])
        
        # 투자 신호 병합
        for result in results:
            if "investment_signals" in result:
                merged["investment_signals"].extend(result["investment_signals"])
                
        return merged