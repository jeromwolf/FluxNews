#!/usr/bin/env python
"""간단한 테스트 실행 스크립트"""
import sys
import os

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 환경 변수 설정
os.environ['ENVIRONMENT'] = 'test'
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'
os.environ['REDIS_URL'] = 'redis://localhost:6379/1'
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
os.environ['SUPABASE_KEY'] = 'test-key'
os.environ['OPENAI_API_KEY'] = 'test-key'

# 간단한 테스트
def test_subscription_tiers():
    """구독 티어 테스트"""
    from app.services.subscription import SubscriptionTier, SubscriptionLimits
    
    print("🧪 구독 티어 테스트 시작...")
    
    # Free tier 테스트
    free_limits = SubscriptionLimits.get_limits(SubscriptionTier.FREE)
    assert free_limits.daily_ai_analyses == 3
    assert free_limits.watchlist_companies == 3
    print("✅ Free tier 테스트 통과")
    
    # Premium tier 테스트
    premium_limits = SubscriptionLimits.get_limits(SubscriptionTier.PREMIUM)
    assert premium_limits.daily_ai_analyses == -1  # 무제한
    assert premium_limits.watchlist_companies == 50
    print("✅ Premium tier 테스트 통과")
    
    # Enterprise tier 테스트
    enterprise_limits = SubscriptionLimits.get_limits(SubscriptionTier.ENTERPRISE)
    assert enterprise_limits.api_access is True
    assert enterprise_limits.watchlist_companies == -1  # 무제한
    print("✅ Enterprise tier 테스트 통과")
    
    return True

def test_impact_calculator():
    """영향도 계산기 테스트"""
    from app.services.impact import ImpactCalculator, ImpactFactors
    
    print("\n🧪 영향도 계산기 테스트 시작...")
    
    calculator = ImpactCalculator()
    
    # 높은 영향도 테스트
    factors = ImpactFactors(
        sentiment_score=0.9,
        relevance_score=0.95,
        magnitude_score=0.8,
        source_credibility=0.9,
        time_decay=1.0
    )
    
    impact = calculator.calculate_impact(factors, article_id=1, company_id=1)
    assert impact.final_score > 0.8
    assert impact.category == "high"
    print("✅ 높은 영향도 계산 테스트 통과")
    
    # 시간 감쇠 테스트
    decay_1day = calculator._calculate_time_decay(hours_ago=24)
    assert 0.8 < decay_1day < 1.0
    print("✅ 시간 감쇠 계산 테스트 통과")
    
    return True

def test_news_deduplication():
    """뉴스 중복 제거 테스트"""
    from app.services.news.deduplication import NewsDeduplicator
    
    print("\n🧪 뉴스 중복 제거 테스트 시작...")
    
    dedup = NewsDeduplicator()
    
    articles = [
        {"url": "https://example.com/news/1", "title": "Article 1"},
        {"url": "https://example.com/news/1?utm=123", "title": "Article 1"},
        {"url": "https://example.com/news/2", "title": "Article 2"}
    ]
    
    unique = dedup.deduplicate(articles)
    assert len(unique) == 2
    print("✅ URL 기반 중복 제거 테스트 통과")
    
    # URL 정규화 테스트
    url1 = "https://example.com/news?utm_source=twitter&id=123"
    url2 = "https://example.com/news?id=123&utm_campaign=social"
    
    normalized1 = dedup._normalize_url(url1)
    normalized2 = dedup._normalize_url(url2)
    assert normalized1 == normalized2
    print("✅ URL 정규화 테스트 통과")
    
    return True

def main():
    """메인 테스트 실행"""
    print("🚀 FluxNews 백엔드 테스트 시작\n")
    
    tests = [
        ("구독 시스템", test_subscription_tiers),
        ("영향도 계산", test_impact_calculator),
        ("뉴스 중복 제거", test_news_deduplication)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} 테스트 실패: {str(e)}")
            failed += 1
    
    print(f"\n📊 테스트 결과: {passed} 통과, {failed} 실패")
    
    if failed == 0:
        print("🎉 모든 테스트 통과!")
        return 0
    else:
        print("😢 일부 테스트 실패")
        return 1

if __name__ == "__main__":
    sys.exit(main())