"""영향도 분석 파이프라인"""
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.core.supabase import get_supabase_client
from app.services.ai import CompanyExtractor, ImpactAnalyzer
from app.services.sentiment import SentimentPipeline
from .impact_calculator import ImpactCalculator
from .impact_models import ImpactFactors, RelationshipType

logger = logging.getLogger(__name__)

class ImpactAnalysisPipeline:
    """뉴스 영향도 분석 통합 파이프라인"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.calculator = ImpactCalculator()
        self.company_extractor = CompanyExtractor()
        self.impact_analyzer = ImpactAnalyzer()
        self.sentiment_pipeline = SentimentPipeline(enable_gpu=False)
        
    async def analyze_article_impacts(
        self,
        article_id: int,
        force_reanalysis: bool = False
    ) -> List[Dict]:
        """
        단일 기사의 모든 관련 기업에 대한 영향도 분석
        
        Args:
            article_id: 기사 ID
            force_reanalysis: 재분석 강제 실행
            
        Returns:
            기업별 영향도 점수 리스트
        """
        try:
            # 1. 기사 정보 조회
            article = await self._get_article(article_id)
            if not article:
                logger.error(f"Article {article_id} not found")
                return []
                
            # 2. 이미 분석된 경우 스킵 (force_reanalysis가 아닌 경우)
            if not force_reanalysis:
                existing_impacts = await self._get_existing_impacts(article_id)
                if existing_impacts:
                    logger.info(f"Article {article_id} already analyzed")
                    return existing_impacts
                    
            # 3. 기업 추출
            extraction_result = await self.company_extractor.extract_companies(
                article['content']
            )
            
            # 4. 추출된 기업 매칭
            matched_companies = await self._match_companies(
                extraction_result['companies']
            )
            
            if not matched_companies:
                logger.info(f"No companies found in article {article_id}")
                return []
                
            # 5. 각 기업에 대한 영향도 계산
            impact_results = []
            
            for company_info in matched_companies:
                impact_score = await self._calculate_company_impact(
                    article,
                    company_info,
                    extraction_result
                )
                
                if impact_score:
                    impact_results.append(impact_score)
                    
            # 6. 데이터베이스 저장
            await self._save_impacts(impact_results)
            
            return impact_results
            
        except Exception as e:
            logger.error(f"Error analyzing article impacts: {str(e)}")
            return []
            
    async def _get_article(self, article_id: int) -> Optional[Dict]:
        """기사 정보 조회"""
        try:
            response = self.supabase.table('news_articles')\
                .select('*')\
                .eq('id', article_id)\
                .single()\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching article: {str(e)}")
            return None
            
    async def _get_existing_impacts(self, article_id: int) -> List[Dict]:
        """기존 영향도 분석 결과 조회"""
        try:
            response = self.supabase.table('news_company_impacts')\
                .select('*')\
                .eq('article_id', article_id)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching existing impacts: {str(e)}")
            return []
            
    async def _match_companies(self, extracted_companies: List[Dict]) -> List[Dict]:
        """추출된 기업명을 데이터베이스와 매칭"""
        matched = []
        
        for company in extracted_companies:
            # 정규화된 이름으로 검색
            normalized_name = company.get('normalized_name', company['name'])
            
            try:
                # 먼저 정확한 매칭 시도
                response = self.supabase.table('companies')\
                    .select('*')\
                    .ilike('name', f"{normalized_name}%")\
                    .limit(1)\
                    .execute()
                    
                if response.data:
                    company_data = response.data[0]
                    company_data['extraction_info'] = company
                    matched.append(company_data)
                else:
                    # 부분 매칭 시도
                    response = self.supabase.table('companies')\
                        .select('*')\
                        .ilike('name', f"%{normalized_name}%")\
                        .limit(1)\
                        .execute()
                        
                    if response.data:
                        company_data = response.data[0]
                        company_data['extraction_info'] = company
                        matched.append(company_data)
                        
            except Exception as e:
                logger.error(f"Error matching company {normalized_name}: {str(e)}")
                
        return matched
        
    async def _calculate_company_impact(
        self,
        article: Dict,
        company: Dict,
        extraction_result: Dict
    ) -> Optional[Dict]:
        """특정 기업에 대한 영향도 계산"""
        try:
            # 감정 분석 결과 가져오기
            sentiment_data = {
                'score': article.get('sentiment_score', 0.5),
                'confidence': article.get('sentiment_confidence', 0.5)
            }
            
            # 관련성 점수 계산
            extraction_info = company.get('extraction_info', {})
            relevance_score = extraction_info.get('confidence', 0.5)
            mention_count = len(extraction_info.get('mentions', []))
            
            # 주요 주제 여부 판단
            is_primary = extraction_info.get('relevance') == 'primary'
            
            # 관계 유형 결정
            relationship_type = await self._determine_relationship(
                company['id'],
                extraction_result.get('relationships', [])
            )
            
            # 뉴스 규모 판단
            news_magnitude = self._classify_news_magnitude(article)
            
            # ImpactFactors 생성
            factors = ImpactFactors(
                sentiment_score=sentiment_data['score'],
                sentiment_confidence=sentiment_data['confidence'],
                relevance_score=relevance_score,
                company_mentioned_count=mention_count,
                is_primary_subject=is_primary,
                relationship_type=relationship_type,
                published_date=datetime.fromisoformat(article['published_date'].replace('Z', '+00:00')),
                analysis_date=datetime.utcnow(),
                source_credibility=self._get_source_credibility(article['source']),
                news_magnitude=news_magnitude,
                sector_impact=self._check_sector_impact(article, company),
                market_impact=self._check_market_impact(article)
            )
            
            # 영향도 계산
            impact_score = self.calculator.calculate_impact(
                factors,
                article['id'],
                company['id']
            )
            
            return impact_score.to_dict()
            
        except Exception as e:
            logger.error(f"Error calculating impact for company {company['id']}: {str(e)}")
            return None
            
    async def _determine_relationship(
        self,
        company_id: int,
        relationships: List[Dict]
    ) -> Optional[RelationshipType]:
        """기업 간 관계 유형 결정"""
        # 추출된 관계에서 확인
        for rel in relationships:
            if rel.get('company2') == company_id:
                rel_type = rel.get('relationship', '').lower()
                if 'competitor' in rel_type:
                    return RelationshipType.COMPETITOR
                elif 'partner' in rel_type:
                    return RelationshipType.PARTNER
                elif 'supplier' in rel_type:
                    return RelationshipType.SUPPLIER
                elif 'customer' in rel_type:
                    return RelationshipType.CUSTOMER
                    
        # 데이터베이스에서 관계 조회
        try:
            response = self.supabase.table('company_relationships')\
                .select('relationship_type')\
                .or_(f"company1_id.eq.{company_id},company2_id.eq.{company_id}")\
                .limit(1)\
                .execute()
                
            if response.data:
                rel_type = response.data[0]['relationship_type']
                return RelationshipType(rel_type)
                
        except Exception as e:
            logger.error(f"Error fetching company relationship: {str(e)}")
            
        return None
        
    def _classify_news_magnitude(self, article: Dict) -> str:
        """뉴스 규모 분류"""
        content = article.get('content', '').lower()
        title = article.get('title', '').lower()
        
        # 중대한 키워드
        critical_keywords = [
            'bankruptcy', '파산', 'merger', '인수', '합병', 'ipo',
            'recall', '리콜', 'scandal', '스캔들', 'lawsuit', '소송'
        ]
        
        major_keywords = [
            'partnership', '파트너십', 'investment', '투자', 'expansion', '확장',
            'launch', '출시', 'contract', '계약', 'development', '개발'
        ]
        
        moderate_keywords = [
            'update', '업데이트', 'announcement', '발표', 'report', '보고서',
            'earnings', '실적', 'revenue', '매출'
        ]
        
        # 키워드 체크
        text = f"{title} {content}"
        
        if any(kw in text for kw in critical_keywords):
            return "critical"
        elif any(kw in text for kw in major_keywords):
            return "major"
        elif any(kw in text for kw in moderate_keywords):
            return "moderate"
        else:
            return "minor"
            
    def _get_source_credibility(self, source: str) -> float:
        """뉴스 출처 신뢰도"""
        high_credibility = [
            'Reuters', 'Bloomberg', 'Financial Times', 'Wall Street Journal',
            '연합뉴스', '한국경제', '매일경제', '조선비즈'
        ]
        
        medium_credibility = [
            'TechCrunch', 'The Verge', 'Engadget',
            '전자신문', '디지털타임스', 'ZDNet Korea'
        ]
        
        if any(src in source for src in high_credibility):
            return 0.9
        elif any(src in source for src in medium_credibility):
            return 0.7
        else:
            return 0.5
            
    def _check_sector_impact(self, article: Dict, company: Dict) -> bool:
        """섹터 전반 영향 여부 확인"""
        sector_keywords = {
            'mobility': ['자율주행', 'autonomous', '전기차', 'ev', '모빌리티'],
            'robotics': ['로봇', 'robot', '자동화', 'automation', 'ai']
        }
        
        company_sector = company.get('sector', '').lower()
        if company_sector in sector_keywords:
            keywords = sector_keywords[company_sector]
            content = article.get('content', '').lower()
            return any(kw in content for kw in keywords)
            
        return False
        
    def _check_market_impact(self, article: Dict) -> bool:
        """시장 전체 영향 여부 확인"""
        market_keywords = [
            'market crash', '시장 폭락', 'recession', '경기 침체',
            'interest rate', '금리', 'inflation', '인플레이션',
            'regulation', '규제', 'policy', '정책'
        ]
        
        content = f"{article.get('title', '')} {article.get('content', '')}".lower()
        return any(kw in content for kw in market_keywords)
        
    async def _save_impacts(self, impact_scores: List[Dict]):
        """영향도 점수 저장"""
        if not impact_scores:
            return
            
        try:
            # news_company_impacts 테이블에 저장
            records = []
            for score in impact_scores:
                record = {
                    'article_id': score['article_id'],
                    'company_id': score['company_id'],
                    'impact_score': score['final_score'],
                    'confidence_score': score['confidence'],
                    'impact_type': score['impact_type'],
                    'explanation': score['explanation'],
                    'analysis_data': score
                }
                records.append(record)
                
            self.supabase.table('news_company_impacts')\
                .insert(records)\
                .execute()
                
            logger.info(f"Saved {len(records)} impact scores")
            
        except Exception as e:
            logger.error(f"Error saving impact scores: {str(e)}")
            
    async def get_company_impact_summary(
        self,
        company_id: int,
        days: int = 7
    ) -> Dict:
        """특정 기업의 영향도 요약"""
        try:
            from datetime import timedelta
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            # 최근 영향도 데이터 조회
            response = self.supabase.table('news_company_impacts')\
                .select('impact_score, impact_type, created_at')\
                .eq('company_id', company_id)\
                .gte('created_at', cutoff_date)\
                .execute()
                
            if not response.data:
                return {
                    'company_id': company_id,
                    'average_impact': 0.0,
                    'total_articles': 0,
                    'impact_trend': 'stable'
                }
                
            impacts = response.data
            
            # 평균 영향도
            avg_impact = sum(i['impact_score'] for i in impacts) / len(impacts)
            
            # 영향 유형별 분포
            impact_types = {}
            for impact in impacts:
                impact_type = impact['impact_type']
                impact_types[impact_type] = impact_types.get(impact_type, 0) + 1
                
            # 추세 분석 (간단한 버전)
            recent_avg = sum(i['impact_score'] for i in impacts[:5]) / min(5, len(impacts))
            older_avg = sum(i['impact_score'] for i in impacts[5:]) / max(1, len(impacts) - 5)
            
            if recent_avg > older_avg * 1.2:
                trend = 'increasing'
            elif recent_avg < older_avg * 0.8:
                trend = 'decreasing'
            else:
                trend = 'stable'
                
            return {
                'company_id': company_id,
                'average_impact': float(avg_impact),
                'total_articles': len(impacts),
                'impact_types': impact_types,
                'impact_trend': trend,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting company impact summary: {str(e)}")
            return {'error': str(e)}