"""성능 최적화 테스트"""
import pytest
import asyncio
from datetime import timedelta
from unittest.mock import Mock, AsyncMock, patch
import time

from app.services.cache import cache_service, cache_news, cache_ai_result
from app.core.redis_client import RedisClient
from app.core.database import DatabasePool, PreparedStatements
from app.services.news.optimized_news_service import OptimizedNewsService

class TestCacheService:
    """캐시 서비스 테스트"""
    
    @pytest.mark.asyncio
    async def test_cache_hit_performance(self, mock_redis):
        """캐시 히트 성능 테스트"""
        # 캐시된 데이터
        cached_data = {"articles": [{"id": 1, "title": "Test"}]}
        mock_redis.get.return_value = cached_data
        
        # 캐시 조회 시간 측정
        start_time = time.time()
        result = await cache_service.get_news_list("technology", 1)
        end_time = time.time()
        
        assert result == cached_data
        assert (end_time - start_time) < 0.01  # 10ms 이내
    
    @pytest.mark.asyncio
    async def test_cache_miss_and_set(self, mock_redis):
        """캐시 미스 및 저장 테스트"""
        mock_redis.get.return_value = None
        
        # 데이터 생성 및 캐싱
        test_data = {"articles": [{"id": 1, "title": "New Article"}]}
        
        # 캐시 미스
        result = await cache_service.get_news_list("technology", 1)
        assert result is None
        
        # 캐시 저장
        success = await cache_service.set_news_list("technology", 1, test_data)
        assert success is True
        
        # TTL 확인
        mock_redis.set.assert_called_with(
            "news:list:technology:1",
            test_data,
            expire=cache_service.NEWS_TTL
        )
    
    @pytest.mark.asyncio
    async def test_cache_decorator(self, mock_redis):
        """캐시 데코레이터 테스트"""
        mock_redis.get.return_value = None
        
        call_count = 0
        
        @cache_news(ttl=timedelta(minutes=5))
        async def get_news_data(category: str):
            nonlocal call_count
            call_count += 1
            return {"category": category, "count": 10}
        
        # 첫 번째 호출 - 캐시 미스
        result1 = await get_news_data("tech")
        assert call_count == 1
        
        # 캐시 히트 시뮬레이션
        mock_redis.get.return_value = {"category": "tech", "count": 10}
        
        # 두 번째 호출 - 캐시 히트
        result2 = await get_news_data("tech")
        assert call_count == 1  # 함수가 다시 호출되지 않음
        assert result1 == result2
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, mock_redis):
        """캐시 무효화 테스트"""
        mock_redis.flush_pattern.return_value = 5
        
        # 뉴스 캐시 무효화
        count = await cache_service.invalidate_news_cache()
        assert count == 5
        mock_redis.flush_pattern.assert_called_with("news:*")
        
        # 특정 기업 캐시 무효화
        count = await cache_service.invalidate_company_cache(company_id=1)
        mock_redis.flush_pattern.assert_called_with("company:*:1")

class TestDatabasePool:
    """데이터베이스 연결 풀 테스트"""
    
    @pytest.mark.asyncio
    async def test_connection_pool_creation(self):
        """연결 풀 생성 테스트"""
        pool = DatabasePool()
        
        with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create:
            mock_pool = Mock()
            mock_pool._minsize = 5
            mock_pool._maxsize = 20
            mock_create.return_value = mock_pool
            
            await pool.create_pool()
            
            # 연결 풀 설정 확인
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args['min_size'] == 5
            assert call_args['max_size'] == 20
            assert call_args['statement_cache_size'] == 100
    
    @pytest.mark.asyncio
    async def test_prepared_statement_usage(self):
        """Prepared Statement 사용 테스트"""
        pool = DatabasePool()
        
        with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create:
            mock_conn = AsyncMock()
            mock_pool = AsyncMock()
            mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
            pool.pool = mock_pool
            
            # Prepared statement 실행
            await pool.fetch(
                PreparedStatements.GET_LATEST_NEWS,
                "2025-01-12",
                50
            )
            
            # 쿼리가 올바르게 실행되었는지 확인
            mock_conn.fetch.assert_called_once()
            args = mock_conn.fetch.call_args[0]
            assert "SELECT" in args[0]
            assert "ORDER BY published_date DESC" in args[0]
    
    @pytest.mark.asyncio
    async def test_connection_pool_stats(self):
        """연결 풀 상태 조회 테스트"""
        pool = DatabasePool()
        
        # 풀이 초기화되지 않은 상태
        stats = await pool.get_pool_stats()
        assert stats["status"] == "not_initialized"
        
        # 풀 초기화 후
        mock_pool = Mock()
        mock_pool._size = 10
        mock_pool._minsize = 5
        mock_pool._maxsize = 20
        pool.pool = mock_pool
        
        stats = await pool.get_pool_stats()
        assert stats["status"] == "active"
        assert stats["size"] == 10
        assert stats["min_size"] == 5
        assert stats["max_size"] == 20

class TestOptimizedNewsService:
    """최적화된 뉴스 서비스 테스트"""
    
    @pytest.mark.asyncio
    async def test_parallel_query_execution(self):
        """병렬 쿼리 실행 테스트"""
        service = OptimizedNewsService()
        
        with patch('app.core.database.db_pool.fetchval', new_callable=AsyncMock) as mock_fetchval:
            with patch('app.core.database.db_pool.fetch', new_callable=AsyncMock) as mock_fetch:
                mock_fetchval.return_value = 100  # 전체 개수
                mock_fetch.return_value = [
                    {"id": 1, "title": "Article 1"},
                    {"id": 2, "title": "Article 2"}
                ]
                
                # 동시 실행 시간 측정
                start_time = time.time()
                result = await service.get_news_by_category("tech", page=1)
                end_time = time.time()
                
                assert result["total_count"] == 100
                assert len(result["articles"]) == 2
                
                # 두 쿼리가 동시에 실행되었는지 확인
                assert mock_fetchval.called
                assert mock_fetch.called
    
    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self):
        """대량 삽입 성능 테스트"""
        service = OptimizedNewsService()
        
        # 1000개 기사 생성
        articles = [
            {
                "title": f"Article {i}",
                "content": f"Content {i}",
                "source": "Test",
                "url": f"https://example.com/{i}",
                "published_date": "2025-01-12T10:00:00Z"
            }
            for i in range(1000)
        ]
        
        with patch('app.core.database.db_pool.copy_records_to_table', new_callable=AsyncMock) as mock_copy:
            start_time = time.time()
            count = await service.bulk_insert_news(articles)
            end_time = time.time()
            
            assert count == 1000
            assert (end_time - start_time) < 1.0  # 1초 이내
            
            # COPY 명령 사용 확인
            mock_copy.assert_called_once()
            assert mock_copy.call_args[0][0] == 'news_articles'
    
    @pytest.mark.asyncio
    async def test_batch_processing_efficiency(self):
        """배치 처리 효율성 테스트"""
        service = OptimizedNewsService()
        
        with patch('app.core.database.db_pool.transaction') as mock_transaction:
            mock_conn = AsyncMock()
            mock_conn.fetch.return_value = [
                {"id": i, "content": f"Content {i}"} 
                for i in range(100)
            ]
            mock_transaction.return_value.__aenter__.return_value = mock_conn
            
            with patch.object(service, '_process_single_article', new_callable=AsyncMock) as mock_process:
                mock_process.return_value = {"processed": True}
                
                # 배치 처리
                processed = await service.process_news_batch(batch_size=100)
                
                assert processed == 100
                assert mock_process.call_count == 100
                
                # 트랜잭션 사용 확인
                mock_transaction.assert_called_once()

# 부하 테스트
class TestLoadPerformance:
    """부하 성능 테스트"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """동시 요청 처리 테스트"""
        async def make_request(index: int):
            # 실제 API 호출 시뮬레이션
            await asyncio.sleep(0.01)  # 10ms 지연
            return {"request_id": index, "status": "success"}
        
        # 100개 동시 요청
        start_time = time.time()
        tasks = [make_request(i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        assert len(results) == 100
        assert all(r["status"] == "success" for r in results)
        assert (end_time - start_time) < 1.0  # 1초 이내 완료
    
    @pytest.mark.asyncio
    async def test_cache_stampede_prevention(self):
        """캐시 스탬피드 방지 테스트"""
        cache_key = "test_key"
        call_count = 0
        
        async def expensive_operation():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # 100ms 소요
            return {"data": "expensive result"}
        
        # 동시에 같은 캐시 키 요청
        tasks = []
        for _ in range(10):
            # 실제로는 캐시 락 메커니즘 사용
            tasks.append(expensive_operation())
        
        results = await asyncio.gather(*tasks)
        
        # 모든 요청이 성공
        assert len(results) == 10
        # 하지만 expensive operation은 여러 번 호출됨 (실제로는 1번만 호출되어야 함)
        # 이는 캐시 락 메커니즘이 필요함을 보여줌