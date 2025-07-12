"""최적화된 뉴스 서비스 예제"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.core.database import db_pool, PreparedStatements
from app.services.cache import cache_service, cache_news
from app.services.news.news_pipeline import NewsPipeline

logger = logging.getLogger(__name__)

class OptimizedNewsService:
    """성능 최적화가 적용된 뉴스 서비스"""
    
    def __init__(self):
        self.pipeline = NewsPipeline()
        
    @cache_news(ttl=timedelta(hours=1))
    async def get_latest_news(
        self, 
        limit: int = 50, 
        hours_ago: int = 24
    ) -> List[Dict]:
        """최신 뉴스 조회 (캐싱 적용)"""
        try:
            # Prepared statement 사용
            since = datetime.utcnow() - timedelta(hours=hours_ago)
            
            rows = await db_pool.fetch(
                PreparedStatements.GET_LATEST_NEWS,
                since,
                limit
            )
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error fetching latest news: {str(e)}")
            return []
            
    async def get_news_by_category(
        self,
        category: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """카테고리별 뉴스 조회 (캐싱 적용)"""
        # 캐시 확인
        cached = await cache_service.get_news_list(category, page)
        if cached:
            return cached
            
        try:
            # DB 조회
            offset = (page - 1) * page_size
            since = datetime.utcnow() - timedelta(days=7)
            
            # 병렬로 전체 개수와 데이터 조회
            count_query = """
                SELECT COUNT(*) 
                FROM news_articles 
                WHERE category = $1 AND published_date > $2
            """
            
            # 동시 실행
            count_task = db_pool.fetchval(count_query, category, since)
            rows_task = db_pool.fetch(
                PreparedStatements.GET_NEWS_BY_CATEGORY,
                category,
                since,
                page_size
            )
            
            total_count, rows = await asyncio.gather(count_task, rows_task)
            
            result = {
                "category": category,
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size,
                "articles": [dict(row) for row in rows]
            }
            
            # 캐시 저장
            await cache_service.set_news_list(category, page, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching news by category: {str(e)}")
            return {
                "category": category,
                "page": page,
                "articles": [],
                "error": str(e)
            }
            
    async def get_company_news_impacts(
        self,
        company_id: int,
        min_impact_score: float = 0.5,
        limit: int = 100
    ) -> List[Dict]:
        """기업별 뉴스 영향도 조회 (캐싱 적용)"""
        # 캐시 확인
        cache_key = f"company_impacts:{company_id}:{min_impact_score}"
        cached = await cache_service.get_company_impacts(company_id)
        if cached:
            # 캐시된 데이터에서 필터링
            filtered = [
                impact for impact in cached 
                if impact['impact_score'] >= min_impact_score
            ][:limit]
            return filtered
            
        try:
            # Prepared statement로 조회
            rows = await db_pool.fetch(
                PreparedStatements.GET_COMPANY_IMPACTS,
                company_id,
                min_impact_score,
                limit
            )
            
            impacts = [dict(row) for row in rows]
            
            # 전체 영향도 목록 캐싱 (필터링 전)
            all_impacts = await db_pool.fetch(
                PreparedStatements.GET_COMPANY_IMPACTS,
                company_id,
                0.0,  # 모든 영향도
                500   # 최대 500개
            )
            
            await cache_service.set_company_impacts(
                company_id,
                [dict(row) for row in all_impacts]
            )
            
            return impacts
            
        except Exception as e:
            logger.error(f"Error fetching company impacts: {str(e)}")
            return []
            
    async def bulk_insert_news(self, articles: List[Dict]) -> int:
        """대량 뉴스 삽입 (COPY 사용)"""
        if not articles:
            return 0
            
        try:
            # 레코드 준비
            records = []
            columns = [
                'title', 'content', 'source', 'url',
                'published_date', 'category', 'language',
                'image_url', 'author'
            ]
            
            for article in articles:
                records.append((
                    article['title'],
                    article['content'],
                    article['source'],
                    article['url'],
                    article['published_date'],
                    article.get('category', 'general'),
                    article.get('language', 'en'),
                    article.get('image_url'),
                    article.get('author')
                ))
                
            # COPY를 사용한 대량 삽입
            await db_pool.copy_records_to_table(
                'news_articles',
                records=records,
                columns=columns
            )
            
            # 뉴스 캐시 무효화
            await cache_service.invalidate_news_cache()
            
            return len(records)
            
        except Exception as e:
            logger.error(f"Error bulk inserting news: {str(e)}")
            return 0
            
    async def process_news_batch(self, batch_size: int = 100):
        """배치로 뉴스 처리"""
        try:
            # 트랜잭션으로 배치 처리
            async with db_pool.transaction() as conn:
                # 미처리 뉴스 조회
                unprocessed = await conn.fetch("""
                    SELECT id, content
                    FROM news_articles
                    WHERE processed = false
                    LIMIT $1
                    FOR UPDATE SKIP LOCKED
                """, batch_size)
                
                if not unprocessed:
                    return 0
                    
                # 병렬 처리 준비
                tasks = []
                for row in unprocessed:
                    article_id = row['id']
                    content = row['content']
                    
                    # AI 분석 태스크 추가
                    tasks.append(self._process_single_article(article_id, content))
                    
                # 병렬 실행
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 처리 완료 표시
                processed_ids = [
                    row['id'] for i, row in enumerate(unprocessed)
                    if not isinstance(results[i], Exception)
                ]
                
                if processed_ids:
                    await conn.execute("""
                        UPDATE news_articles
                        SET processed = true, processed_at = NOW()
                        WHERE id = ANY($1)
                    """, processed_ids)
                    
                return len(processed_ids)
                
        except Exception as e:
            logger.error(f"Error processing news batch: {str(e)}")
            return 0
            
    async def _process_single_article(self, article_id: int, content: str):
        """개별 기사 처리 (AI 분석 등)"""
        # 캐시된 분석 결과 확인
        content_hash = cache_service.generate_hash(content)
        cached_result = await cache_service.get_ai_analysis(content_hash)
        
        if cached_result:
            # 캐시된 결과 사용
            return cached_result
            
        # 실제 AI 분석 수행 (pipeline 사용)
        # ... AI 분석 로직 ...
        
        # 결과 캐싱
        # await cache_service.set_ai_analysis(content_hash, result)
        
        return {"processed": True}
        
    async def search_news(
        self,
        query: str,
        language: str = 'en',
        limit: int = 50
    ) -> List[Dict]:
        """전체 텍스트 검색 (GIN 인덱스 활용)"""
        try:
            if language == 'ko':
                # 한국어 검색
                search_query = """
                    SELECT 
                        id, title_kr as title, content_kr as content,
                        source, url, published_date,
                        ts_rank(
                            to_tsvector('simple', coalesce(title_kr, '') || ' ' || coalesce(content_kr, '')),
                            plainto_tsquery('simple', $1)
                        ) as rank
                    FROM news_articles
                    WHERE to_tsvector('simple', coalesce(title_kr, '') || ' ' || coalesce(content_kr, ''))
                          @@ plainto_tsquery('simple', $1)
                    ORDER BY rank DESC, published_date DESC
                    LIMIT $2
                """
            else:
                # 영어 검색
                search_query = """
                    SELECT 
                        id, title, content, source, url, published_date,
                        ts_rank(
                            to_tsvector('english', title || ' ' || content),
                            plainto_tsquery('english', $1)
                        ) as rank
                    FROM news_articles
                    WHERE to_tsvector('english', title || ' ' || content) 
                          @@ plainto_tsquery('english', $1)
                    ORDER BY rank DESC, published_date DESC
                    LIMIT $2
                """
                
            rows = await db_pool.fetch(search_query, query, limit)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error searching news: {str(e)}")
            return []

# 성능 모니터링
class PerformanceMonitor:
    """성능 지표 모니터링"""
    
    @staticmethod
    async def get_cache_stats() -> Dict:
        """캐시 통계"""
        # Redis INFO 명령으로 통계 수집
        info = await redis_client.client.info()
        
        return {
            "hits": info.get('keyspace_hits', 0),
            "misses": info.get('keyspace_misses', 0),
            "hit_rate": info.get('keyspace_hits', 0) / 
                       (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1)),
            "memory_used_mb": info.get('used_memory', 0) / 1024 / 1024,
            "keys_count": info.get('db0', {}).get('keys', 0)
        }
        
    @staticmethod
    async def get_db_pool_stats() -> Dict:
        """DB 연결 풀 통계"""
        return await db_pool.get_pool_stats()
        
    @staticmethod
    async def get_slow_operations() -> List[Dict]:
        """느린 작업 조회"""
        # 실제로는 APM 도구나 로그 분석 필요
        return [
            {
                "operation": "news_batch_processing",
                "avg_duration_ms": 2500,
                "count": 150,
                "recommendation": "배치 크기를 50으로 줄이기"
            }
        ]

import asyncio
from app.core.redis_client import redis_client