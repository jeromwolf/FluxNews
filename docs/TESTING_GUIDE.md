# FluxNews 테스트 가이드

## 🧪 테스트 전략

FluxNews는 다층 테스트 전략을 사용하여 코드 품질과 안정성을 보장합니다.

### 테스트 피라미드
```
        E2E 테스트
       /          \
    통합 테스트     API 테스트
   /              \
유닛 테스트        서비스 테스트
```

## 🚀 빠른 시작

### 1. 테스트 환경 설정
```bash
cd backend

# 개발 의존성 설치
pip install -r requirements-dev.txt

# 테스트 데이터베이스 설정
export DATABASE_URL=postgresql://test:test@localhost:5432/fluxnews_test
export REDIS_URL=redis://localhost:6379/1
```

### 2. 전체 테스트 실행
```bash
# 모든 테스트 실행
make test

# 또는 직접 실행
pytest
```

### 3. 특정 테스트 실행
```bash
# 유닛 테스트만
pytest -m unit

# API 테스트만
pytest -m api

# 특정 파일
pytest tests/test_services_news.py

# 특정 테스트 함수
pytest tests/test_services_news.py::TestRSSParser::test_parse_feed_success
```

## 📋 테스트 종류

### 1. 유닛 테스트 (`@pytest.mark.unit`)
개별 함수와 클래스 메서드를 독립적으로 테스트

**예시: 뉴스 중복 제거**
```python
def test_is_duplicate_by_title_similarity(self):
    dedup = NewsDeduplicator()
    
    articles = [
        {"url": "https://site1.com/1", "title": "현대차, 전기차 신모델 출시"},
        {"url": "https://site2.com/2", "title": "현대차 전기차 신모델 출시"},
        {"url": "https://site3.com/3", "title": "삼성전자 반도체 실적 발표"}
    ]
    
    unique = dedup.deduplicate(articles)
    assert len(unique) == 2  # 유사한 제목 하나만 포함
```

### 2. 서비스 테스트 (`@pytest.mark.service`)
비즈니스 로직과 서비스 레이어 테스트

**예시: OpenAI 클라이언트**
```python
@pytest.mark.asyncio
async def test_extract_companies(self):
    client = OpenAIClient()
    
    # Mock 설정
    with patch.object(client, 'complete', new_callable=AsyncMock) as mock:
        mock.return_value = {"result": {"companies": ["현대자동차"]}}
        
        companies, _ = await client.extract_companies("뉴스 내용")
        assert len(companies) == 1
```

### 3. API 테스트 (`@pytest.mark.api`)
HTTP 엔드포인트 테스트

**예시: 뉴스 목록 API**
```python
@pytest.mark.asyncio
async def test_get_news_list(self, async_client, mock_supabase):
    response = await async_client.get("/api/v1/news")
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
```

### 4. 통합 테스트 (`@pytest.mark.integration`)
여러 컴포넌트 간 상호작용 테스트

**예시: 뉴스 파이프라인**
```python
@pytest.mark.asyncio
async def test_news_pipeline_integration(self):
    pipeline = NewsPipeline()
    
    # RSS + Google News + 중복 제거 + 저장
    result = await pipeline.collect_news()
    
    assert result["total_collected"] > 0
    assert result["duplicates_removed"] >= 0
```

### 5. 성능 테스트 (`@pytest.mark.performance`)
응답 시간과 처리량 테스트

**예시: 캐시 성능**
```python
@pytest.mark.asyncio
async def test_cache_hit_performance(self):
    start_time = time.time()
    result = await cache_service.get_news_list("tech", 1)
    end_time = time.time()
    
    assert (end_time - start_time) < 0.01  # 10ms 이내
```

## 🔧 테스트 Fixtures

### 기본 Fixtures
```python
@pytest.fixture
def test_user():
    """테스트 사용자"""
    return {
        "id": "test-user-123",
        "email": "test@example.com",
        "subscription_tier": "free"
    }

@pytest.fixture
def auth_headers(test_user):
    """인증 헤더"""
    return {"Authorization": f"Bearer test-token-{test_user['id']}"}
```

### Mock Fixtures
```python
@pytest.fixture
def mock_openai():
    """OpenAI 클라이언트 모킹"""
    with patch("app.services.ai.openai_client.OpenAIClient") as mock:
        client = Mock()
        client.complete = Mock(return_value={
            "result": "mocked response",
            "usage": {"total_tokens": 100}
        })
        yield client
```

## 📊 테스트 커버리지

### 커버리지 실행
```bash
# 커버리지와 함께 테스트 실행
make coverage

# HTML 리포트 생성
pytest --cov=app --cov-report=html
# 브라우저에서 htmlcov/index.html 열기
```

### 커버리지 목표
- 전체: 80% 이상
- 핵심 비즈니스 로직: 90% 이상
- API 엔드포인트: 95% 이상

## 🐛 디버깅

### 1. 상세 출력
```bash
# 상세 로그 출력
pytest -v -s

# 특정 테스트만 상세히
pytest -v -s -k "test_extract_companies"
```

### 2. 디버거 사용
```python
def test_complex_logic(self):
    import pdb; pdb.set_trace()  # 브레이크포인트
    
    result = complex_function()
    assert result == expected
```

### 3. 실패한 테스트만 재실행
```bash
# 마지막 실패한 테스트만
pytest --lf

# 처음 실패한 테스트에서 중단
pytest -x
```

## 🔄 CI/CD 통합

### GitHub Actions 설정
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
    
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: pytest --cov=app
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 💡 베스트 프랙티스

### 1. 테스트 작성 원칙
- **Arrange-Act-Assert** 패턴 사용
- 한 테스트는 하나의 기능만 검증
- 테스트 이름은 명확하고 설명적으로

### 2. Mock 사용
- 외부 의존성은 항상 Mock
- 실제 API 호출은 통합 테스트에서만
- Mock은 실제 동작과 최대한 유사하게

### 3. 비동기 테스트
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### 4. 테스트 데이터
- Fixture로 재사용 가능한 테스트 데이터 생성
- Factory 패턴으로 동적 데이터 생성
- 테스트 후 데이터 정리

## 🚨 주의사항

1. **테스트 격리**: 각 테스트는 독립적으로 실행 가능해야 함
2. **실제 API 호출 금지**: 유닛/서비스 테스트에서는 Mock 사용
3. **테스트 DB 사용**: 프로덕션 DB에 절대 연결하지 않음
4. **민감 정보**: 테스트 코드에 실제 API 키 포함 금지

## 📚 추가 리소스

- [pytest 공식 문서](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [테스트 주도 개발(TDD)](https://en.wikipedia.org/wiki/Test-driven_development)