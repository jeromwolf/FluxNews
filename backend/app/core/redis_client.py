"""Redis 캐싱 클라이언트"""
import redis
import json
import logging
from typing import Optional, Any, Union
from datetime import timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis 캐시 관리 클라이언트"""
    
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._client: Optional[redis.Redis] = None
        self._connected = False
        
    @property
    def client(self) -> redis.Redis:
        """Redis 클라이언트 인스턴스 반환"""
        if not self._connected:
            self.connect()
        return self._client
        
    def connect(self):
        """Redis 서버 연결"""
        try:
            self._client = redis.Redis.from_url(
                self.redis_url,
                decode_responses=True,
                health_check_interval=30,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 30,  # TCP_KEEPINTVL
                    3: 5,  # TCP_KEEPCNT
                }
            )
            # 연결 테스트
            self._client.ping()
            self._connected = True
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self._connected = False
            raise
            
    def disconnect(self):
        """Redis 연결 해제"""
        if self._client:
            self._client.close()
            self._connected = False
            logger.info("Redis disconnected")
            
    async def get(self, key: str) -> Optional[Any]:
        """캐시된 값 조회"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except json.JSONDecodeError:
            # 문자열 값인 경우 그대로 반환
            return value
        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {str(e)}")
            return None
            
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """값 캐싱"""
        try:
            # JSON 직렬화 가능한 객체는 JSON으로 저장
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            # 만료 시간 설정
            if isinstance(expire, timedelta):
                expire = int(expire.total_seconds())
                
            if expire:
                return self.client.setex(key, expire, value)
            else:
                return self.client.set(key, value)
        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {str(e)}")
            return False
            
    async def delete(self, key: str) -> bool:
        """캐시 삭제"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {str(e)}")
            return False
            
    async def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Error checking existence for key {key}: {str(e)}")
            return False
            
    async def expire(self, key: str, seconds: int) -> bool:
        """키 만료 시간 설정"""
        try:
            return bool(self.client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Error setting expiry for key {key}: {str(e)}")
            return False
            
    async def ttl(self, key: str) -> int:
        """키 남은 만료 시간 조회 (초)"""
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {str(e)}")
            return -2  # 키가 존재하지 않음
            
    async def incr(self, key: str, amount: int = 1) -> int:
        """카운터 증가"""
        try:
            return self.client.incr(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key}: {str(e)}")
            return 0
            
    async def decr(self, key: str, amount: int = 1) -> int:
        """카운터 감소"""
        try:
            return self.client.decr(key, amount)
        except Exception as e:
            logger.error(f"Error decrementing key {key}: {str(e)}")
            return 0
            
    async def lpush(self, key: str, *values) -> int:
        """리스트 왼쪽에 값 추가"""
        try:
            return self.client.lpush(key, *values)
        except Exception as e:
            logger.error(f"Error pushing to list {key}: {str(e)}")
            return 0
            
    async def rpop(self, key: str) -> Optional[str]:
        """리스트 오른쪽에서 값 제거 및 반환"""
        try:
            return self.client.rpop(key)
        except Exception as e:
            logger.error(f"Error popping from list {key}: {str(e)}")
            return None
            
    async def lrange(self, key: str, start: int, end: int) -> list:
        """리스트 범위 조회"""
        try:
            return self.client.lrange(key, start, end)
        except Exception as e:
            logger.error(f"Error getting list range for {key}: {str(e)}")
            return []
            
    async def hset(self, name: str, key: str, value: Any) -> int:
        """해시맵에 값 설정"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            return self.client.hset(name, key, value)
        except Exception as e:
            logger.error(f"Error setting hash {name}[{key}]: {str(e)}")
            return 0
            
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """해시맵에서 값 조회"""
        try:
            value = self.client.hget(name, key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Error getting hash {name}[{key}]: {str(e)}")
            return None
            
    async def hgetall(self, name: str) -> dict:
        """해시맵 전체 조회"""
        try:
            data = self.client.hgetall(name)
            result = {}
            for key, value in data.items():
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = value
            return result
        except Exception as e:
            logger.error(f"Error getting all hash {name}: {str(e)}")
            return {}
            
    async def flush_pattern(self, pattern: str) -> int:
        """패턴과 일치하는 모든 키 삭제"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error flushing pattern {pattern}: {str(e)}")
            return 0

# 싱글톤 인스턴스
redis_client = RedisClient()

async def get_redis() -> RedisClient:
    """Redis 클라이언트 의존성"""
    return redis_client