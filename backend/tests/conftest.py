"""테스트 설정 및 fixtures"""
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import Mock, patch

from app.main import app
from app.core.config import settings
from app.core.supabase import get_supabase_client

# 테스트용 환경 설정
settings.ENVIRONMENT = "test"
settings.DATABASE_URL = "postgresql://test:test@localhost:5432/test"
settings.REDIS_URL = "redis://localhost:6379/1"

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """이벤트 루프 fixture"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client() -> TestClient:
    """동기 테스트 클라이언트"""
    return TestClient(app)

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """비동기 테스트 클라이언트"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_supabase():
    """Supabase 클라이언트 모킹"""
    with patch("app.core.supabase.get_supabase_client") as mock:
        client = Mock()
        mock.return_value = client
        yield client

@pytest.fixture
def mock_redis():
    """Redis 클라이언트 모킹"""
    with patch("app.core.redis_client.redis_client") as mock:
        redis = Mock()
        redis.get = Mock(return_value=None)
        redis.set = Mock(return_value=True)
        redis.delete = Mock(return_value=True)
        mock.client = redis
        yield redis

@pytest.fixture
def mock_openai():
    """OpenAI 클라이언트 모킹"""
    with patch("app.services.ai.openai_client.OpenAIClient") as mock:
        client = Mock()
        client.complete = Mock(return_value={
            "result": "mocked response",
            "usage": {"total_tokens": 100}
        })
        mock.return_value = client
        yield client

@pytest.fixture
def test_user():
    """테스트 사용자 데이터"""
    return {
        "id": "test-user-123",
        "email": "test@example.com",
        "name": "Test User",
        "subscription_tier": "free"
    }

@pytest.fixture
def test_news_article():
    """테스트 뉴스 기사 데이터"""
    return {
        "id": 1,
        "title": "Test News Article",
        "content": "This is a test news article about technology.",
        "source": "Test Source",
        "url": "https://example.com/news/1",
        "published_date": "2025-01-12T10:00:00Z",
        "category": "technology",
        "language": "en"
    }

@pytest.fixture
def test_company():
    """테스트 기업 데이터"""
    return {
        "id": 1,
        "name": "현대자동차",
        "name_en": "Hyundai Motor Company",
        "ticker": "005380",
        "sector": "automotive",
        "description": "Leading automotive manufacturer"
    }

@pytest.fixture
def auth_headers(test_user):
    """인증 헤더"""
    # 실제로는 JWT 토큰 생성
    return {"Authorization": f"Bearer test-token-{test_user['id']}"}

# 테스트 데이터베이스 설정
@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """테스트 데이터베이스 설정"""
    # 테스트 시작 시 실행
    print("Setting up test database...")
    
    yield
    
    # 테스트 종료 시 정리
    print("Cleaning up test database...")

# 비동기 테스트 마커
pytestmark = pytest.mark.asyncio