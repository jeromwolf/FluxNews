"""AI 분석기 구현"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from .openai_client import OpenAIClient
from .prompts import PromptTemplates
from .response_parser import ResponseParser
from .cost_tracker import CostTracker
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)

class BaseAnalyzer:
    """기본 분석기 클래스"""
    
    def __init__(self, openai_client: OpenAIClient = None, cost_tracker: CostTracker = None):
        self.client = openai_client or OpenAIClient()
        self.cost_tracker = cost_tracker or CostTracker()
        self.parser = ResponseParser()
        self.supabase = get_supabase_client()
        
    async def _analyze_with_tracking(
        self,
        user_id: str,
        prompt: str,
        system_prompt: str,
        request_type: str
    ) -> Optional[Dict[str, Any]]:
        """비용 추적과 함께 분석 수행"""
        try:
            # API 호출
            result = await self.client.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                response_format={"type": "json_object"}
            )
            
            # 비용 추적
            if self.cost_tracker and user_id:
                await self.cost_tracker.track_usage(
                    user_id=user_id,
                    model=self.client.model,
                    usage=result["usage"],
                    request_type=request_type
                )
                
            return result
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            return None

class NewsAnalyzer(BaseAnalyzer):
    """뉴스 기사 분석기"""
    
    async def analyze_article(
        self,
        article_id: int,
        article_title: str,
        article_content: str,
        user_id: str = None,
        target_companies: List[str] = None
    ) -> Dict[str, Any]:
        """
        뉴스 기사 분석
        
        Args:
            article_id: 기사 ID
            article_title: 기사 제목
            article_content: 기사 내용
            user_id: 사용자 ID (비용 추적용)
            target_companies: 특별히 주목할 기업 목록
            
        Returns:
            분석 결과
        """
        # 프롬프트 생성
        prompt = PromptTemplates.news_analysis_prompt(
            article_title=article_title,
            article_content=article_content,
            target_companies=target_companies
        )
        
        system_prompt = PromptTemplates.SYSTEM_PROMPTS["news_analyzer"]
        
        # 분석 수행
        result = await self._analyze_with_tracking(
            user_id=user_id,
            prompt=prompt,
            system_prompt=system_prompt,
            request_type="news_analysis"
        )
        
        if not result or not result.get("parsed_content"):
            return {
                "error": "Failed to analyze article",
                "article_id": article_id
            }
            
        analysis = result["parsed_content"]
        
        # 검증
        is_valid, errors = self.parser.validate_news_analysis(analysis)
        if not is_valid:
            logger.warning(f"Invalid analysis for article {article_id}: {errors}")
            
        # 메타데이터 추가
        analysis["article_id"] = article_id
        analysis["analyzed_at"] = datetime.utcnow().isoformat()
        analysis["model"] = self.client.model
        analysis["cost"] = self.client.estimate_cost(result["usage"])
        
        # 데이터베이스 업데이트
        try:
            # 기사 처리 상태 업데이트
            self.supabase.table("news_articles")\
                .update({
                    "processed": True,
                    "sentiment_score": analysis["sentiment"]["score"],
                    "analysis_data": analysis
                })\
                .eq("id", article_id)\
                .execute()
                
            # 기업별 영향도 저장
            if "companies_mentioned" in analysis:
                await self._save_company_impacts(article_id, analysis)
                
        except Exception as e:
            logger.error(f"Error saving analysis: {str(e)}")
            
        return analysis
        
    async def _save_company_impacts(self, article_id: int, analysis: Dict):
        """기업별 영향도 저장"""
        impacts = []
        
        for company in analysis.get("companies_mentioned", []):
            # 회사 ID 조회
            company_name = self.parser.normalize_company_name(company["name"])
            company_response = self.supabase.table("companies")\
                .select("id")\
                .ilike("name", f"%{company_name}%")\
                .limit(1)\
                .execute()
                
            if company_response.data:
                company_id = company_response.data[0]["id"]
                
                # 영향도 계산 (기본값)
                impact_score = 0.5
                confidence = company.get("confidence", 0.5)
                
                # 투자 신호에서 영향도 추출
                for signal in analysis.get("investment_signals", []):
                    if signal["company"] == company["name"]:
                        if signal["signal"] == "bullish":
                            impact_score = 0.7
                        elif signal["signal"] == "bearish":
                            impact_score = 0.3
                        break
                        
                impacts.append({
                    "article_id": article_id,
                    "company_id": company_id,
                    "impact_score": impact_score,
                    "confidence_score": confidence,
                    "explanation": f"{company.get('context', 'Mentioned in article')}"
                })
                
        if impacts:
            self.supabase.table("news_company_impacts").insert(impacts).execute()

class CompanyExtractor(BaseAnalyzer):
    """뉴스에서 기업 추출"""
    
    async def extract_companies(
        self,
        article_content: str,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        기사에서 기업 추출
        
        Args:
            article_content: 기사 내용
            user_id: 사용자 ID
            
        Returns:
            추출된 기업 목록
        """
        # 알려진 기업 목록 가져오기
        known_companies = await self._get_known_companies()
        
        # 프롬프트 생성
        prompt = PromptTemplates.company_extraction_prompt(
            article_content=article_content,
            known_companies=known_companies
        )
        
        system_prompt = PromptTemplates.SYSTEM_PROMPTS["company_extractor"]
        
        # 추출 수행
        result = await self._analyze_with_tracking(
            user_id=user_id,
            prompt=prompt,
            system_prompt=system_prompt,
            request_type="company_extraction"
        )
        
        if not result or not result.get("parsed_content"):
            return {"companies": [], "relationships": []}
            
        extraction = result["parsed_content"]
        
        # 검증
        is_valid, errors = self.parser.validate_company_extraction(extraction)
        if not is_valid:
            logger.warning(f"Invalid extraction: {errors}")
            
        # 회사명 정규화
        for company in extraction.get("companies", []):
            company["normalized_name"] = self.parser.normalize_company_name(company["name"])
            
        return extraction
        
    async def _get_known_companies(self) -> List[Dict]:
        """데이터베이스에서 알려진 기업 목록 조회"""
        try:
            response = self.supabase.table("companies")\
                .select("name, ticker, sector")\
                .limit(100)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching companies: {str(e)}")
            return []

class ImpactAnalyzer(BaseAnalyzer):
    """기업별 영향도 분석"""
    
    async def analyze_impact(
        self,
        article_summary: str,
        company_id: int,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        특정 기업에 대한 뉴스 영향도 분석
        
        Args:
            article_summary: 기사 요약
            company_id: 기업 ID
            user_id: 사용자 ID
            
        Returns:
            영향도 분석 결과
        """
        # 기업 정보 조회
        company_info = await self._get_company_info(company_id)
        if not company_info:
            return {"error": "Company not found"}
            
        # 관련 기업 조회
        related_companies = await self._get_related_companies(company_id)
        
        # 프롬프트 생성
        prompt = PromptTemplates.impact_analysis_prompt(
            article_summary=article_summary,
            company_name=company_info["name"],
            company_info=company_info,
            related_companies=related_companies
        )
        
        system_prompt = PromptTemplates.SYSTEM_PROMPTS["impact_analyzer"]
        
        # 분석 수행
        result = await self._analyze_with_tracking(
            user_id=user_id,
            prompt=prompt,
            system_prompt=system_prompt,
            request_type="impact_analysis"
        )
        
        if not result or not result.get("parsed_content"):
            return {
                "error": "Failed to analyze impact",
                "company_id": company_id
            }
            
        impact = result["parsed_content"]
        
        # 검증
        is_valid, errors = self.parser.validate_impact_analysis(impact)
        if not is_valid:
            logger.warning(f"Invalid impact analysis: {errors}")
            
        # 메타데이터 추가
        impact["company_id"] = company_id
        impact["company_name"] = company_info["name"]
        impact["analyzed_at"] = datetime.utcnow().isoformat()
        
        return impact
        
    async def _get_company_info(self, company_id: int) -> Optional[Dict]:
        """기업 상세 정보 조회"""
        try:
            response = self.supabase.table("companies")\
                .select("*")\
                .eq("id", company_id)\
                .single()\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching company info: {str(e)}")
            return None
            
    async def _get_related_companies(self, company_id: int) -> List[str]:
        """관련 기업 목록 조회"""
        try:
            # 경쟁사 조회
            competitors = self.supabase.table("company_relationships")\
                .select("company2_id")\
                .eq("company1_id", company_id)\
                .eq("relationship_type", "competitor")\
                .execute()
                
            # 파트너사 조회
            partners = self.supabase.table("company_relationships")\
                .select("company2_id")\
                .eq("company1_id", company_id)\
                .eq("relationship_type", "partner")\
                .execute()
                
            related_ids = [r["company2_id"] for r in competitors.data + partners.data]
            
            if related_ids:
                companies = self.supabase.table("companies")\
                    .select("name")\
                    .in_("id", related_ids)\
                    .execute()
                return [c["name"] for c in companies.data]
                
            return []
            
        except Exception as e:
            logger.error(f"Error fetching related companies: {str(e)}")
            return []

# 배치 분석기
class BatchAnalyzer:
    """여러 기사를 배치로 분석"""
    
    def __init__(self, max_concurrent: int = 5):
        self.news_analyzer = NewsAnalyzer()
        self.company_extractor = CompanyExtractor()
        self.impact_analyzer = ImpactAnalyzer()
        self.max_concurrent = max_concurrent
        self.supabase = get_supabase_client()
        
    async def analyze_batch(
        self,
        article_ids: List[int],
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        여러 기사 배치 분석
        
        Args:
            article_ids: 분석할 기사 ID 목록
            user_id: 사용자 ID
            
        Returns:
            배치 분석 결과
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def _analyze_article(article_id: int):
            async with semaphore:
                try:
                    # 기사 조회
                    response = self.supabase.table("news_articles")\
                        .select("*")\
                        .eq("id", article_id)\
                        .single()\
                        .execute()
                        
                    if not response.data:
                        return {"article_id": article_id, "error": "Article not found"}
                        
                    article = response.data
                    
                    # 분석 수행
                    analysis = await self.news_analyzer.analyze_article(
                        article_id=article_id,
                        article_title=article["title"],
                        article_content=article["content"],
                        user_id=user_id
                    )
                    
                    return analysis
                    
                except Exception as e:
                    logger.error(f"Error analyzing article {article_id}: {str(e)}")
                    return {"article_id": article_id, "error": str(e)}
                    
        # 동시 분석 수행
        tasks = [_analyze_article(aid) for aid in article_ids]
        results = await asyncio.gather(*tasks)
        
        # 결과 집계
        successful = [r for r in results if "error" not in r]
        failed = [r for r in results if "error" in r]
        
        return {
            "total": len(article_ids),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
            "summary": {
                "avg_sentiment": sum(r["sentiment"]["score"] for r in successful) / len(successful) if successful else 0.5,
                "total_companies": sum(len(r.get("companies_mentioned", [])) for r in successful),
                "total_cost_usd": sum(r.get("cost", {}).get("total_cost", 0) for r in successful)
            }
        }