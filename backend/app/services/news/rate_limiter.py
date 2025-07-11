import asyncio
import time
from typing import Dict, Optional, Callable, Any
from functools import wraps
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RateLimiter:
    """API 속도 제한 관리자"""
    
    def __init__(self):
        # 각 도메인별 요청 기록
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        # 도메인별 설정
        self.limits = {
            'default': {'requests': 60, 'window': 60},  # 분당 60회
            'news.google.com': {'requests': 100, 'window': 60},  # 분당 100회
            'rss': {'requests': 30, 'window': 60},  # RSS는 분당 30회
        }
        
    def get_domain_key(self, url: str) -> str:
        """URL에서 도메인 추출"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc or 'default'
        
    def get_limit_config(self, domain: str) -> Dict[str, int]:
        """도메인별 제한 설정 가져오기"""
        # RSS 피드인지 확인
        if 'rss' in domain or 'feed' in domain or '.xml' in domain:
            return self.limits['rss']
        return self.limits.get(domain, self.limits['default'])
        
    async def wait_if_needed(self, url: str) -> float:
        """필요한 경우 대기"""
        domain = self.get_domain_key(url)
        config = self.get_limit_config(domain)
        
        now = time.time()
        window_start = now - config['window']
        
        # 현재 윈도우 내의 요청 수 계산
        history = self.request_history[domain]
        recent_requests = [t for t in history if t > window_start]
        
        if len(recent_requests) >= config['requests']:
            # 가장 오래된 요청 시간 + 윈도우 시간까지 대기
            wait_time = recent_requests[0] + config['window'] - now
            if wait_time > 0:
                logger.info(f"Rate limit reached for {domain}, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                return wait_time
                
        # 요청 기록
        self.request_history[domain].append(now)
        return 0
        
    def reset_domain(self, domain: str):
        """특정 도메인의 요청 기록 초기화"""
        if domain in self.request_history:
            self.request_history[domain].clear()
            
    def get_stats(self) -> Dict[str, Dict]:
        """현재 속도 제한 상태"""
        stats = {}
        now = time.time()
        
        for domain, history in self.request_history.items():
            config = self.get_limit_config(domain)
            window_start = now - config['window']
            recent_count = sum(1 for t in history if t > window_start)
            
            stats[domain] = {
                'recent_requests': recent_count,
                'limit': config['requests'],
                'window': config['window'],
                'usage_percent': (recent_count / config['requests']) * 100
            }
            
        return stats


class RetryHandler:
    """재시도 로직 처리"""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_stats = defaultdict(int)
        
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """재시도 로직과 함께 함수 실행"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                result = await func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Succeeded after {attempt + 1} attempts")
                return result
                
            except asyncio.TimeoutError as e:
                last_exception = e
                wait_time = self.backoff_factor ** attempt
                logger.warning(f"Timeout error (attempt {attempt + 1}/{self.max_retries}), waiting {wait_time}s")
                self.retry_stats['timeout'] += 1
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(wait_time)
                    
            except Exception as e:
                if "aiohttp" in str(type(e).__module__):
                    last_exception = e
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(f"Client error (attempt {attempt + 1}/{self.max_retries}): {str(e)}, waiting {wait_time}s")
                    self.retry_stats['client_error'] += 1
                    
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(wait_time)
                else:
                    # 다른 예외는 즉시 발생
                    logger.error(f"Unexpected error: {str(e)}")
                    self.retry_stats['other_error'] += 1
                    raise
                
        # 모든 재시도 실패
        self.retry_stats['max_retries_exceeded'] += 1
        raise last_exception
        
    def get_stats(self) -> Dict[str, int]:
        """재시도 통계"""
        return dict(self.retry_stats)


class ThrottledClient:
    """속도 제한이 적용된 HTTP 클라이언트"""
    
    def __init__(self, rate_limiter: RateLimiter = None, retry_handler: RetryHandler = None):
        self.rate_limiter = rate_limiter or RateLimiter()
        self.retry_handler = retry_handler or RetryHandler()
        self.session = None
        
    async def __aenter__(self):
        import aiohttp
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def get(self, url: str, **kwargs):
        """속도 제한이 적용된 GET 요청"""
        # 속도 제한 확인
        await self.rate_limiter.wait_if_needed(url)
        
        # 재시도 로직과 함께 요청
        async def _make_request():
            return await self.session.get(url, **kwargs)
            
        return await self.retry_handler.execute_with_retry(_make_request)
        
    async def post(self, url: str, **kwargs):
        """속도 제한이 적용된 POST 요청"""
        await self.rate_limiter.wait_if_needed(url)
        
        async def _make_request():
            return await self.session.post(url, **kwargs)
            
        return await self.retry_handler.execute_with_retry(_make_request)


def rate_limited(requests_per_minute: int = 60):
    """속도 제한 데코레이터"""
    min_interval = 60.0 / requests_per_minute
    last_called = {}
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = func.__name__
            now = time.time()
            
            if key in last_called:
                elapsed = now - last_called[key]
                if elapsed < min_interval:
                    wait_time = min_interval - elapsed
                    logger.debug(f"Rate limiting {key}: waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    
            last_called[key] = time.time()
            return await func(*args, **kwargs)
            
        return wrapper
    return decorator


# 예제 사용
async def example_usage():
    """사용 예제"""
    rate_limiter = RateLimiter()
    retry_handler = RetryHandler()
    
    async with ThrottledClient(rate_limiter, retry_handler) as client:
        # 여러 요청 수행
        urls = [
            'https://example.com/api/1',
            'https://example.com/api/2',
            'https://example.com/api/3',
        ]
        
        for url in urls:
            try:
                response = await client.get(url)
                data = await response.json()
                print(f"Success: {url}")
            except Exception as e:
                print(f"Failed: {url} - {str(e)}")
                
        # 통계 출력
        print("Rate limiter stats:", rate_limiter.get_stats())
        print("Retry stats:", retry_handler.get_stats())