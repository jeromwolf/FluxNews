"""구독 서비스 테스트"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from decimal import Decimal

from app.services.subscription import (
    SubscriptionService, SubscriptionTier, SubscriptionStatus,
    SubscriptionPlan, UsageTracker, PaymentMethod
)

class TestSubscriptionService:
    """구독 서비스 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_user_subscription_free_tier(self, mock_supabase):
        """무료 구독 조회 테스트"""
        service = SubscriptionService()
        
        # 구독 정보 없음 -> 무료 구독 생성
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = None
        
        subscription = await service.get_user_subscription("user-123")
        
        assert subscription is not None
        assert subscription.tier == SubscriptionTier.FREE
        assert subscription.status == SubscriptionStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_create_premium_subscription(self, mock_supabase):
        """프리미엄 구독 생성 테스트"""
        service = SubscriptionService()
        
        # 기존 구독 없음
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = None
        
        success, subscription, error = await service.create_subscription(
            user_id="user-123",
            plan_id="premium_monthly",
            payment_method=PaymentMethod.CREDIT_CARD,
            trial=True
        )
        
        assert success is True
        assert subscription.tier == SubscriptionTier.PREMIUM
        assert subscription.status == SubscriptionStatus.TRIAL
        assert subscription.trial_end is not None
        assert error is None
    
    @pytest.mark.asyncio
    async def test_upgrade_subscription(self, mock_supabase):
        """구독 업그레이드 테스트"""
        service = SubscriptionService()
        
        # 현재 Free 구독
        current_sub = {
            "id": "sub-123",
            "user_id": "user-123",
            "plan_id": "free_tier",
            "tier": "free",
            "status": "active",
            "started_at": datetime.utcnow().isoformat(),
            "current_period_start": datetime.utcnow().isoformat(),
            "current_period_end": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = current_sub
        
        success, error = await service.upgrade_subscription(
            user_id="user-123",
            new_plan_id="premium_monthly"
        )
        
        assert success is True
        assert error is None
    
    @pytest.mark.asyncio
    async def test_cancel_subscription(self, mock_supabase):
        """구독 취소 테스트"""
        service = SubscriptionService()
        
        # 현재 Premium 구독
        current_sub = {
            "id": "sub-123",
            "user_id": "user-123",
            "plan_id": "premium_monthly",
            "tier": "premium",
            "status": "active",
            "started_at": datetime.utcnow().isoformat(),
            "current_period_start": datetime.utcnow().isoformat(),
            "current_period_end": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = current_sub
        
        success, error = await service.cancel_subscription(
            user_id="user-123",
            immediate=False,
            reason="Too expensive"
        )
        
        assert success is True
        assert error is None
    
    @pytest.mark.asyncio
    async def test_check_subscription_limits(self, mock_supabase):
        """구독 제한 확인 테스트"""
        service = SubscriptionService()
        
        # Free tier 구독
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "tier": "free",
            "status": "active"
        }
        
        # AI 분석 제한 확인
        with patch.object(service.usage_tracker, 'track_ai_analysis') as mock_track:
            mock_track.return_value = (False, "일일 한도 초과")
            
            can_use, message = await service.check_subscription_limits(
                user_id="user-123",
                feature="ai_analysis"
            )
            
            assert can_use is False
            assert "한도" in message

class TestUsageTracker:
    """사용량 추적 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_daily_usage_new(self, mock_supabase):
        """일일 사용량 조회 (신규) 테스트"""
        tracker = UsageTracker()
        
        # 오늘 사용 기록 없음
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = None
        
        usage = await tracker.get_daily_usage("user-123")
        
        assert usage.user_id == "user-123"
        assert usage.ai_analyses_used == 0
        assert usage.date == datetime.utcnow().date()
    
    @pytest.mark.asyncio
    async def test_track_ai_analysis_within_limit(self, mock_supabase):
        """AI 분석 사용 추적 (한도 내) 테스트"""
        tracker = UsageTracker()
        
        # 현재 사용량: 1회
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "user_id": "user-123",
            "date": datetime.utcnow().date().isoformat(),
            "ai_analyses_used": 1
        }
        
        can_use, message = await tracker.track_ai_analysis(
            "user-123",
            SubscriptionTier.FREE  # 일일 3회 제한
        )
        
        assert can_use is True
        assert message is None
    
    @pytest.mark.asyncio
    async def test_track_ai_analysis_exceed_limit(self, mock_supabase):
        """AI 분석 사용 추적 (한도 초과) 테스트"""
        tracker = UsageTracker()
        
        # 현재 사용량: 3회 (Free tier 한도)
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "user_id": "user-123",
            "date": datetime.utcnow().date().isoformat(),
            "ai_analyses_used": 3
        }
        
        can_use, message = await tracker.track_ai_analysis(
            "user-123",
            SubscriptionTier.FREE
        )
        
        assert can_use is False
        assert "한도" in message
        assert "3회" in message
    
    @pytest.mark.asyncio
    async def test_get_usage_summary(self, mock_supabase):
        """사용량 요약 통계 테스트"""
        tracker = UsageTracker()
        
        # 30일간 사용 데이터
        mock_data = [
            {"ai_analyses_used": 3, "api_calls_made": 10, "notifications_sent": 5,
             "news_articles_viewed": 20, "exports_generated": 1, "total_session_minutes": 60},
            {"ai_analyses_used": 2, "api_calls_made": 8, "notifications_sent": 3,
             "news_articles_viewed": 15, "exports_generated": 0, "total_session_minutes": 45},
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value.data = mock_data
        
        summary = await tracker.get_usage_summary("user-123", days=30)
        
        assert summary["totals"]["ai_analyses"] == 5
        assert summary["totals"]["api_calls"] == 18
        assert summary["daily_average"]["ai_analyses"] == 2.5
        assert summary["active_days"] == 2

class TestSubscriptionPlans:
    """구독 플랜 테스트"""
    
    def test_get_default_plans(self):
        """기본 플랜 목록 테스트"""
        plans = SubscriptionPlan.get_default_plans()
        
        assert len(plans) >= 3  # Free, Premium, Enterprise
        
        # Free 플랜 확인
        free_plan = next(p for p in plans if p.tier == SubscriptionTier.FREE)
        assert free_plan.price_krw == 0
        assert free_plan.features is not None
        
        # Premium 플랜 확인
        premium_plan = next(p for p in plans if p.tier == SubscriptionTier.PREMIUM and p.billing_period == "monthly")
        assert premium_plan.price_krw == 9900
        assert premium_plan.trial_days > 0
    
    def test_subscription_limits(self):
        """구독 제한 설정 테스트"""
        # Free tier
        free_limits = SubscriptionLimits.get_limits(SubscriptionTier.FREE)
        assert free_limits.daily_ai_analyses == 3
        assert free_limits.watchlist_companies == 3
        assert free_limits.real_time_alerts is False
        
        # Premium tier
        premium_limits = SubscriptionLimits.get_limits(SubscriptionTier.PREMIUM)
        assert premium_limits.daily_ai_analyses == -1  # 무제한
        assert premium_limits.watchlist_companies == 50
        assert premium_limits.real_time_alerts is True
        
        # Enterprise tier
        enterprise_limits = SubscriptionLimits.get_limits(SubscriptionTier.ENTERPRISE)
        assert enterprise_limits.watchlist_companies == -1  # 무제한
        assert enterprise_limits.api_access is True