"""캐싱 서비스"""
import hashlib
import json
from typing import Optional, Any, Callable, Union
from datetime import timedelta
from functools import wraps
import logging
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)

class CacheService:
    """캐시 관리 서비스"""
    
    # 캐시 키 접두사
    PREFIX_NEWS = "news:"
    PREFIX_AI = "ai:"
    PREFIX_COMPANY = "company:"
    PREFIX_USER = "user:"
    PREFIX_API = "api:"
    
    # 기본 만료 시간
    DEFAULT_TTL = timedelta(minutes=15)
    NEWS_TTL = timedelta(hours=1)
    AI_RESULT_TTL = timedelta(hours=24)
    COMPANY_DATA_TTL = timedelta(hours=6)
    USER_SESSION_TTL = timedelta(hours=2)
    
    def __init__(self):
        self.client = redis_client
        
    async def get_news_list(self, category: str, page: int) -> Optional[dict]:
        """뉴스 목록 캐시 조회"""
        key = f"{self.PREFIX_NEWS}list:{category}:{page}"
        return await self.client.get(key)
        
    async def set_news_list(self, category: str, page: int, data: dict) -> bool:
        """뉴스 목록 캐시 저장"""
        key = f"{self.PREFIX_NEWS}list:{category}:{page}"
        return await self.client.set(key, data, expire=self.NEWS_TTL)
        
    async def get_news_article(self, article_id: int) -> Optional[dict]:
        """뉴스 기사 캐시 조회"""
        key = f"{self.PREFIX_NEWS}article:{article_id}"
        return await self.client.get(key)
        
    async def set_news_article(self, article_id: int, data: dict) -> bool:
        """뉴스 기사 캐시 저장"""
        key = f"{self.PREFIX_NEWS}article:{article_id}"
        return await self.client.set(key, data, expire=self.NEWS_TTL)
        
    async def get_ai_analysis(self, content_hash: str) -> Optional[dict]:
        """AI 분석 결과 캐시 조회"""
        key = f"{self.PREFIX_AI}analysis:{content_hash}"
        return await self.client.get(key)
        
    async def set_ai_analysis(self, content_hash: str, result: dict) -> bool:
        """AI 분석 결과 캐시 저장"""
        key = f"{self.PREFIX_AI}analysis:{content_hash}"
        return await self.client.set(key, result, expire=self.AI_RESULT_TTL)
        
    async def get_sentiment_score(self, text_hash: str) -> Optional[dict]:
        """감정 분석 결과 캐시 조회"""
        key = f"{self.PREFIX_AI}sentiment:{text_hash}"
        return await self.client.get(key)
        
    async def set_sentiment_score(self, text_hash: str, score: dict) -> bool:
        """감정 분석 결과 캐시 저장"""
        key = f"{self.PREFIX_AI}sentiment:{text_hash}"
        return await self.client.set(key, score, expire=self.AI_RESULT_TTL)
        
    async def get_company_data(self, company_id: int) -> Optional[dict]:
        """기업 데이터 캐시 조회"""
        key = f"{self.PREFIX_COMPANY}data:{company_id}"
        return await self.client.get(key)
        
    async def set_company_data(self, company_id: int, data: dict) -> bool:
        """기업 데이터 캐시 저장"""
        key = f"{self.PREFIX_COMPANY}data:{company_id}"
        return await self.client.set(key, data, expire=self.COMPANY_DATA_TTL)
        
    async def get_company_impacts(self, company_id: int) -> Optional[list]:
        """기업 영향도 목록 캐시 조회"""
        key = f"{self.PREFIX_COMPANY}impacts:{company_id}"
        return await self.client.get(key)
        
    async def set_company_impacts(self, company_id: int, impacts: list) -> bool:
        """기업 영향도 목록 캐시 저장"""
        key = f"{self.PREFIX_COMPANY}impacts:{company_id}"
        return await self.client.set(key, impacts, expire=timedelta(minutes=30))
        
    async def get_user_session(self, user_id: str) -> Optional[dict]:
        """사용자 세션 캐시 조회"""
        key = f"{self.PREFIX_USER}session:{user_id}"
        return await self.client.get(key)
        
    async def set_user_session(self, user_id: str, session_data: dict) -> bool:
        """사용자 세션 캐시 저장"""
        key = f"{self.PREFIX_USER}session:{user_id}"
        return await self.client.set(key, session_data, expire=self.USER_SESSION_TTL)
        
    async def get_api_response(self, endpoint: str, params_hash: str) -> Optional[dict]:
        """API 응답 캐시 조회"""
        key = f"{self.PREFIX_API}{endpoint}:{params_hash}"
        return await self.client.get(key)
        
    async def set_api_response(
        self, 
        endpoint: str, 
        params_hash: str, 
        response: dict,
        ttl: Optional[timedelta] = None
    ) -> bool:
        """API 응답 캐시 저장"""
        key = f"{self.PREFIX_API}{endpoint}:{params_hash}"
        expire = ttl or self.DEFAULT_TTL
        return await self.client.set(key, response, expire=expire)
        
    async def invalidate_news_cache(self):
        """뉴스 관련 캐시 무효화"""
        count = await self.client.flush_pattern(f"{self.PREFIX_NEWS}*")
        logger.info(f"Invalidated {count} news cache entries")
        return count
        
    async def invalidate_company_cache(self, company_id: Optional[int] = None):
        """기업 관련 캐시 무효화"""
        if company_id:
            pattern = f"{self.PREFIX_COMPANY}*:{company_id}"
        else:
            pattern = f"{self.PREFIX_COMPANY}*"
        count = await self.client.flush_pattern(pattern)
        logger.info(f"Invalidated {count} company cache entries")
        return count
        
    async def invalidate_user_cache(self, user_id: str):
        """사용자 관련 캐시 무효화"""
        pattern = f"{self.PREFIX_USER}*:{user_id}"
        count = await self.client.flush_pattern(pattern)
        logger.info(f"Invalidated {count} user cache entries for {user_id}")
        return count
        
    @staticmethod
    def generate_hash(content: Union[str, dict]) -> str:
        """콘텐츠 해시 생성"""
        if isinstance(content, dict):
            content = json.dumps(content, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
        
    @staticmethod
    def cache_key_wrapper(
        prefix: str,
        ttl: Optional[timedelta] = None,
        key_generator: Optional[Callable] = None
    ):
        """캐시 데코레이터"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 캐시 키 생성
                if key_generator:
                    cache_key = key_generator(*args, **kwargs)
                else:
                    # 기본 키 생성: 함수명 + 인자 해시
                    params = f"{args}{kwargs}"
                    params_hash = CacheService.generate_hash(params)
                    cache_key = f"{prefix}{func.__name__}:{params_hash}"
                    
                # 캐시 조회
                cached = await redis_client.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached
                    
                # 함수 실행
                result = await func(*args, **kwargs)
                
                # 결과 캐싱
                if result is not None:
                    await redis_client.set(cache_key, result, expire=ttl)
                    logger.debug(f"Cached result for {cache_key}")
                    
                return result
            return wrapper
        return decorator

# 데코레이터 예제
def cache_news(ttl: timedelta = CacheService.NEWS_TTL):
    """뉴스 캐싱 데코레이터"""
    return CacheService.cache_key_wrapper(
        prefix=CacheService.PREFIX_NEWS,
        ttl=ttl
    )

def cache_ai_result(ttl: timedelta = CacheService.AI_RESULT_TTL):
    """AI 결과 캐싱 데코레이터"""
    return CacheService.cache_key_wrapper(
        prefix=CacheService.PREFIX_AI,
        ttl=ttl
    )

def cache_api_response(ttl: timedelta = CacheService.DEFAULT_TTL):
    """API 응답 캐싱 데코레이터"""
    return CacheService.cache_key_wrapper(
        prefix=CacheService.PREFIX_API,
        ttl=ttl
    )

# 싱글톤 인스턴스
cache_service = CacheService()