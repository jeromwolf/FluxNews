"""데이터베이스 연결 풀 관리"""
import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import asyncpg
from app.core.config import settings

logger = logging.getLogger(__name__)

class DatabasePool:
    """PostgreSQL 연결 풀 관리자"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.dsn = self._build_dsn()
        
    def _build_dsn(self) -> str:
        """데이터베이스 연결 문자열 생성"""
        # Supabase URL 파싱
        # postgresql://[user]:[password]@[host]:[port]/[database]
        return settings.DATABASE_URL.replace("postgres://", "postgresql://")
        
    async def create_pool(self) -> asyncpg.Pool:
        """연결 풀 생성"""
        try:
            self.pool = await asyncpg.create_pool(
                dsn=self.dsn,
                min_size=5,                    # 최소 연결 수
                max_size=20,                   # 최대 연결 수
                max_queries=50000,             # 연결당 최대 쿼리 수
                max_inactive_connection_lifetime=300,  # 유휴 연결 타임아웃 (초)
                timeout=60,                    # 연결 타임아웃
                command_timeout=60,            # 명령 타임아웃
                statement_cache_size=100,      # prepared statement 캐시 크기
                
                # 연결 설정
                server_settings={
                    'application_name': 'fluxnews_backend',
                    'jit': 'off',              # JIT 컴파일 비활성화 (작은 쿼리에서는 오버헤드)
                    'search_path': 'public',
                },
                
                # 연결 초기화 콜백
                init=self._init_connection
            )
            
            logger.info(f"Database pool created with {self.pool._minsize}-{self.pool._maxsize} connections")
            return self.pool
            
        except Exception as e:
            logger.error(f"Failed to create database pool: {str(e)}")
            raise
            
    async def _init_connection(self, conn: asyncpg.Connection):
        """개별 연결 초기화"""
        # 타입 코덱 설정
        await conn.set_type_codec(
            'json',
            encoder=lambda v: json.dumps(v, ensure_ascii=False),
            decoder=json.loads,
            schema='pg_catalog'
        )
        
        # 타임존 설정
        await conn.execute("SET timezone TO 'UTC'")
        
    async def close_pool(self):
        """연결 풀 종료"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
            
    @asynccontextmanager
    async def acquire(self):
        """연결 획득 컨텍스트 매니저"""
        if not self.pool:
            await self.create_pool()
            
        async with self.pool.acquire() as conn:
            yield conn
            
    @asynccontextmanager
    async def transaction(self):
        """트랜잭션 컨텍스트 매니저"""
        async with self.acquire() as conn:
            async with conn.transaction():
                yield conn
                
    async def execute(self, query: str, *args, timeout: float = None) -> str:
        """쿼리 실행"""
        async with self.acquire() as conn:
            return await conn.execute(query, *args, timeout=timeout)
            
    async def fetch(self, query: str, *args, timeout: float = None) -> list:
        """여러 행 조회"""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)
            
    async def fetchrow(self, query: str, *args, timeout: float = None) -> Optional[asyncpg.Record]:
        """단일 행 조회"""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)
            
    async def fetchval(self, query: str, *args, column: int = 0, timeout: float = None) -> Any:
        """단일 값 조회"""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args, column=column, timeout=timeout)
            
    async def execute_many(self, query: str, args: list, timeout: float = None):
        """배치 실행"""
        async with self.acquire() as conn:
            await conn.executemany(query, args, timeout=timeout)
            
    async def copy_records_to_table(
        self,
        table_name: str,
        records: list,
        columns: list = None,
        schema_name: str = None
    ):
        """대량 데이터 삽입 (COPY)"""
        async with self.acquire() as conn:
            await conn.copy_records_to_table(
                table_name,
                records=records,
                columns=columns,
                schema_name=schema_name
            )
            
    async def get_pool_stats(self) -> Dict[str, Any]:
        """연결 풀 상태 조회"""
        if not self.pool:
            return {"status": "not_initialized"}
            
        return {
            "status": "active",
            "size": self.pool._size,
            "min_size": self.pool._minsize,
            "max_size": self.pool._maxsize,
            "free_connections": self.pool._queue.qsize() if hasattr(self.pool._queue, 'qsize') else 0,
            "used_connections": self.pool._size - (self.pool._queue.qsize() if hasattr(self.pool._queue, 'qsize') else 0),
        }
        
    async def health_check(self) -> bool:
        """데이터베이스 연결 상태 확인"""
        try:
            async with self.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False

# Prepared Statement 캐시
class PreparedStatements:
    """자주 사용되는 쿼리의 Prepared Statement 관리"""
    
    # 뉴스 관련 쿼리
    GET_LATEST_NEWS = """
        SELECT id, title, content, source, url, published_date, category
        FROM news_articles
        WHERE published_date > $1
        ORDER BY published_date DESC
        LIMIT $2
    """
    
    GET_NEWS_BY_CATEGORY = """
        SELECT id, title, content, source, url, published_date
        FROM news_articles
        WHERE category = $1 AND published_date > $2
        ORDER BY published_date DESC
        LIMIT $3
    """
    
    # 기업 영향도 쿼리
    GET_COMPANY_IMPACTS = """
        SELECT 
            nci.*, 
            na.title, 
            na.published_date
        FROM news_company_impacts nci
        JOIN news_articles na ON nci.article_id = na.id
        WHERE nci.company_id = $1 AND nci.impact_score > $2
        ORDER BY nci.impact_score DESC, na.published_date DESC
        LIMIT $3
    """
    
    # 사용자 관심목록 쿼리
    GET_USER_WATCHLIST = """
        SELECT 
            c.id, 
            c.name, 
            c.ticker, 
            c.sector,
            uw.added_at
        FROM user_watchlists uw
        JOIN companies c ON uw.company_id = c.id
        WHERE uw.user_id = $1
        ORDER BY uw.priority ASC, uw.added_at DESC
    """
    
    # 구독 상태 확인
    CHECK_SUBSCRIPTION = """
        SELECT 
            s.tier,
            s.status,
            s.current_period_end
        FROM subscriptions s
        WHERE s.user_id = $1 AND s.status IN ('active', 'trial')
        ORDER BY s.created_at DESC
        LIMIT 1
    """

# 싱글톤 인스턴스
db_pool = DatabasePool()

# 의존성 함수
async def get_db_pool() -> DatabasePool:
    """데이터베이스 풀 의존성"""
    return db_pool

# 시작/종료 이벤트
async def startup_db_pool():
    """애플리케이션 시작 시 풀 생성"""
    await db_pool.create_pool()
    
async def shutdown_db_pool():
    """애플리케이션 종료 시 풀 정리"""
    await db_pool.close_pool()

import json  # 상단에 추가 필요