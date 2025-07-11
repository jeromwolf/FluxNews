"""감정 분석 통합 파이프라인"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import asyncio
from dataclasses import dataclass
from app.core.supabase import get_supabase_client
from .finbert_analyzer import FinBERTAnalyzer, SentimentResult
from .korean_analyzer import KoreanSentimentAnalyzer, KoreanSentimentResult

logger = logging.getLogger(__name__)

@dataclass
class CombinedSentimentResult:
    """통합 감정 분석 결과"""
    article_id: int
    language: str
    finbert_result: Optional[SentimentResult]
    korean_result: Optional[KoreanSentimentResult]
    combined_sentiment: str
    combined_score: float
    confidence: float
    analysis_time: float

class SentimentPipeline:
    """뉴스 감정 분석 파이프라인"""
    
    def __init__(self, enable_gpu: bool = True):
        """
        Args:
            enable_gpu: GPU 사용 여부
        """
        # FinBERT 분석기 (영어)
        device = 'cuda' if enable_gpu else 'cpu'
        self.finbert = FinBERTAnalyzer(device=device)
        
        # 한국어 분석기
        self.korean_analyzer = KoreanSentimentAnalyzer()
        
        # Supabase 클라이언트
        self.supabase = get_supabase_client()
        
        # 캐시 (메모리)
        self._cache = {}
        self._cache_size = 1000
        
    def _detect_language(self, text: str) -> str:
        """텍스트 언어 감지 (간단한 휴리스틱)"""
        # 한글 비율 계산
        korean_chars = sum(1 for c in text if '가' <= c <= '힣')
        total_chars = len(text.replace(' ', ''))
        
        if total_chars == 0:
            return 'unknown'
            
        korean_ratio = korean_chars / total_chars
        
        if korean_ratio > 0.3:
            return 'ko'
        else:
            return 'en'
            
    async def analyze_article(
        self,
        article_id: int,
        title: str,
        content: str,
        force_reanalysis: bool = False
    ) -> CombinedSentimentResult:
        """
        단일 기사 감정 분석
        
        Args:
            article_id: 기사 ID
            title: 기사 제목
            content: 기사 내용
            force_reanalysis: 캐시 무시하고 재분석
            
        Returns:
            통합 감정 분석 결과
        """
        start_time = datetime.now()
        
        # 캐시 확인
        if not force_reanalysis and article_id in self._cache:
            logger.debug(f"Using cached result for article {article_id}")
            return self._cache[article_id]
            
        # 제목과 내용 결합 (제목에 더 가중치)
        full_text = f"{title}\n{title}\n{content}"
        
        # 언어 감지
        language = self._detect_language(full_text)
        
        # 언어별 분석
        finbert_result = None
        korean_result = None
        
        try:
            if language == 'ko':
                # 한국어 분석
                korean_result = await self.korean_analyzer.analyze_async(full_text)
                
                # 영어 번역 후 FinBERT 분석도 가능 (선택사항)
                # 현재는 한국어 분석만 사용
                
            else:
                # 영어 분석 (FinBERT)
                finbert_result = await self.finbert.analyze(full_text)
                
        except Exception as e:
            logger.error(f"Sentiment analysis error for article {article_id}: {str(e)}")
            
        # 결과 통합
        combined_result = self._combine_results(
            article_id,
            language,
            finbert_result,
            korean_result
        )
        
        # 분석 시간 계산
        analysis_time = (datetime.now() - start_time).total_seconds()
        combined_result.analysis_time = analysis_time
        
        # 캐시 저장
        self._update_cache(article_id, combined_result)
        
        # 데이터베이스 업데이트
        await self._save_to_database(combined_result)
        
        return combined_result
        
    def _combine_results(
        self,
        article_id: int,
        language: str,
        finbert_result: Optional[SentimentResult],
        korean_result: Optional[KoreanSentimentResult]
    ) -> CombinedSentimentResult:
        """분석 결과 통합"""
        # 기본값
        combined_sentiment = 'neutral'
        combined_score = 0.5
        confidence = 0.0
        
        if finbert_result:
            # FinBERT 결과 사용
            combined_sentiment = finbert_result.label
            combined_score = finbert_result.score
            confidence = finbert_result.confidence
            
        elif korean_result:
            # 한국어 분석 결과 사용
            combined_sentiment = korean_result.sentiment
            combined_score = korean_result.score
            confidence = 0.7  # 규칙 기반이므로 신뢰도 고정
            
        # 감정 점수 정규화 (0~1)
        if combined_sentiment == 'positive':
            # positive일 때 점수를 0.5~1.0으로 매핑
            combined_score = 0.5 + (combined_score * 0.5)
        elif combined_sentiment == 'negative':
            # negative일 때 점수를 0.0~0.5로 매핑
            combined_score = combined_score * 0.5
        else:
            # neutral은 0.4~0.6
            combined_score = 0.4 + (combined_score * 0.2)
            
        return CombinedSentimentResult(
            article_id=article_id,
            language=language,
            finbert_result=finbert_result,
            korean_result=korean_result,
            combined_sentiment=combined_sentiment,
            combined_score=float(combined_score),
            confidence=float(confidence),
            analysis_time=0.0
        )
        
    async def analyze_batch(
        self,
        articles: List[Dict],
        batch_size: int = 10
    ) -> List[CombinedSentimentResult]:
        """
        배치 감정 분석
        
        Args:
            articles: 기사 정보 리스트 (id, title, content 포함)
            batch_size: 동시 처리 크기
            
        Returns:
            분석 결과 리스트
        """
        results = []
        
        # 배치 단위로 처리
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            
            # 비동기 분석
            batch_tasks = [
                self.analyze_article(
                    article['id'],
                    article['title'],
                    article['content']
                )
                for article in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # 에러 처리
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch analysis error: {str(result)}")
                else:
                    results.append(result)
                    
        return results
        
    async def _save_to_database(self, result: CombinedSentimentResult):
        """데이터베이스에 결과 저장"""
        try:
            # 기사 테이블 업데이트
            update_data = {
                'sentiment_score': result.combined_score,
                'sentiment_label': result.combined_sentiment,
                'sentiment_confidence': result.confidence,
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('news_articles')\
                .update(update_data)\
                .eq('id', result.article_id)\
                .execute()
                
            logger.debug(f"Saved sentiment analysis for article {result.article_id}")
            
        except Exception as e:
            logger.error(f"Failed to save sentiment analysis: {str(e)}")
            
    def _update_cache(self, article_id: int, result: CombinedSentimentResult):
        """캐시 업데이트"""
        # 크기 제한
        if len(self._cache) >= self._cache_size:
            # 가장 오래된 항목 제거 (FIFO)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            
        self._cache[article_id] = result
        
    async def get_market_sentiment(
        self,
        time_window_hours: int = 24,
        company_id: Optional[int] = None
    ) -> Dict[str, float]:
        """
        시장 전체 또는 특정 기업의 감정 지표
        
        Args:
            time_window_hours: 분석 시간 범위
            company_id: 특정 기업 ID (None이면 전체)
            
        Returns:
            시장 감정 지표
        """
        try:
            # 시간 범위 계산
            from datetime import timedelta
            cutoff_time = (datetime.utcnow() - timedelta(hours=time_window_hours)).isoformat()
            
            # 쿼리 구성
            query = self.supabase.table('news_articles')\
                .select('sentiment_score, sentiment_label, sentiment_confidence')\
                .gte('published_date', cutoff_time)\
                .not_.is_('sentiment_score', 'null')
                
            # 특정 기업 필터
            if company_id:
                # 해당 기업과 관련된 기사만
                impacts = self.supabase.table('news_company_impacts')\
                    .select('article_id')\
                    .eq('company_id', company_id)\
                    .execute()
                    
                article_ids = [i['article_id'] for i in impacts.data]
                if article_ids:
                    query = query.in_('id', article_ids)
                else:
                    return self._default_market_sentiment()
                    
            # 실행
            response = query.execute()
            articles = response.data
            
            if not articles:
                return self._default_market_sentiment()
                
            # 집계
            total = len(articles)
            positive = sum(1 for a in articles if a['sentiment_label'] == 'positive')
            negative = sum(1 for a in articles if a['sentiment_label'] == 'negative')
            neutral = total - positive - negative
            
            avg_score = sum(a['sentiment_score'] for a in articles) / total
            avg_confidence = sum(a['sentiment_confidence'] for a in articles) / total
            
            # 시장 감정 계산
            bullish_ratio = positive / total
            bearish_ratio = negative / total
            
            if bullish_ratio > bearish_ratio + 0.1:
                market_sentiment = 'bullish'
            elif bearish_ratio > bullish_ratio + 0.1:
                market_sentiment = 'bearish'
            else:
                market_sentiment = 'neutral'
                
            return {
                'total_articles': total,
                'positive_ratio': float(positive / total),
                'negative_ratio': float(negative / total),
                'neutral_ratio': float(neutral / total),
                'average_score': float(avg_score),
                'average_confidence': float(avg_confidence),
                'market_sentiment': market_sentiment,
                'time_window_hours': time_window_hours
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate market sentiment: {str(e)}")
            return self._default_market_sentiment()
            
    def _default_market_sentiment(self) -> Dict[str, float]:
        """기본 시장 감정 값"""
        return {
            'total_articles': 0,
            'positive_ratio': 0.33,
            'negative_ratio': 0.33,
            'neutral_ratio': 0.34,
            'average_score': 0.5,
            'average_confidence': 0.0,
            'market_sentiment': 'neutral',
            'time_window_hours': 0
        }
        
    def cleanup(self):
        """리소스 정리"""
        self.finbert.cleanup()
        self._cache.clear()