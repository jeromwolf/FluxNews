# FluxNews 백엔드 테스트 빠른 시작 가이드

## 🚀 테스트 방법

### 1. 간단한 유닛 테스트
```bash
cd backend
python run_tests.py
```

### 2. pytest 사용 (전체 기능)
```bash
# 의존성 설치
pip install pytest pytest-asyncio pytest-cov pytest-mock

# 테스트 실행
pytest -v

# 특정 마커로 실행
pytest -m unit -v
```

### 3. Makefile 사용
```bash
# 전체 테스트
make test

# 커버리지 포함
make coverage

# 특정 테스트
make test-unit
make test-api
```

## 🧪 주요 테스트 포인트

### 1. 구독 시스템
- Free/Premium/Enterprise 티어 제한 확인
- 사용량 추적 및 제한 적용
- 구독 상태 변경 (업그레이드/다운그레이드)

### 2. AI 서비스
- OpenAI API 호출 모킹
- 기업 추출 정확도
- 비용 추적

### 3. 뉴스 수집
- RSS 피드 파싱
- 중복 제거 알고리즘
- 대량 데이터 처리

### 4. 성능 최적화
- Redis 캐싱 효과
- DB 연결 풀 효율성
- 동시 요청 처리

## 📝 테스트 작성 예제

### 간단한 유닛 테스트
```python
def test_subscription_tier():
    from app.services.subscription import SubscriptionTier
    
    assert SubscriptionTier.FREE.value == "free"
    assert SubscriptionTier.PREMIUM.value == "premium"
```

### 비동기 서비스 테스트
```python
@pytest.mark.asyncio
async def test_news_collection():
    from app.services.news import NewsPipeline
    
    pipeline = NewsPipeline()
    # Mock 외부 API
    with patch.object(pipeline, 'fetch_rss') as mock:
        mock.return_value = [{"title": "Test"}]
        
        result = await pipeline.collect_news()
        assert result["count"] > 0
```

## ⚠️ 주의사항

1. **환경 변수**: 테스트용 `.env.test` 파일 사용
2. **데이터베이스**: 실제 DB가 아닌 테스트 DB 사용
3. **외부 API**: 항상 Mock 사용 (비용 발생 방지)
4. **Redis**: 테스트용 별도 DB 번호 사용 (예: redis://localhost:6379/1)

## 🔍 디버깅 팁

1. **상세 출력**: `pytest -v -s`
2. **특정 테스트**: `pytest -k "test_name"`
3. **실패 시 중단**: `pytest -x`
4. **마지막 실패만**: `pytest --lf`

## 📊 커버리지 목표

- 핵심 비즈니스 로직: 90%+
- API 엔드포인트: 85%+
- 유틸리티 함수: 80%+
- 전체: 80%+