"""구독 관리 서비스"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from app.core.supabase import get_supabase_client
from .subscription_models import (
    Subscription, SubscriptionPlan, SubscriptionTier,
    SubscriptionStatus, SubscriptionLimits, PaymentMethod
)
from .usage_tracker import UsageTracker

logger = logging.getLogger(__name__)

class SubscriptionService:
    """구독 관리 통합 서비스"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.usage_tracker = UsageTracker()
        self._plans_cache: Dict[str, SubscriptionPlan] = {}
        self._load_plans()
        
    def _load_plans(self):
        """구독 플랜 캐시 로드"""
        for plan in SubscriptionPlan.get_default_plans():
            self._plans_cache[plan.id] = plan
            
    async def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """사용자 구독 정보 조회"""
        try:
            response = self.supabase.table('subscriptions')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('status', 'active')\
                .single()\
                .execute()
                
            if not response.data:
                # 무료 플랜 기본 생성
                return await self._create_free_subscription(user_id)
                
            data = response.data
            return Subscription(
                id=data['id'],
                user_id=data['user_id'],
                plan_id=data['plan_id'],
                tier=SubscriptionTier(data['tier']),
                status=SubscriptionStatus(data['status']),
                started_at=datetime.fromisoformat(data['started_at'].replace('Z', '+00:00')),
                current_period_start=datetime.fromisoformat(data['current_period_start'].replace('Z', '+00:00')),
                current_period_end=datetime.fromisoformat(data['current_period_end'].replace('Z', '+00:00')),
                trial_end=datetime.fromisoformat(data['trial_end'].replace('Z', '+00:00')) if data.get('trial_end') else None,
                cancelled_at=datetime.fromisoformat(data['cancelled_at'].replace('Z', '+00:00')) if data.get('cancelled_at') else None,
                payment_method=PaymentMethod(data['payment_method']) if data.get('payment_method') else None,
                last_payment_date=datetime.fromisoformat(data['last_payment_date'].replace('Z', '+00:00')) if data.get('last_payment_date') else None,
                next_payment_date=datetime.fromisoformat(data['next_payment_date'].replace('Z', '+00:00')) if data.get('next_payment_date') else None,
                metadata=data.get('metadata', {})
            )
            
        except Exception as e:
            logger.error(f"Error getting user subscription: {str(e)}")
            return None
            
    async def create_subscription(
        self,
        user_id: str,
        plan_id: str,
        payment_method: Optional[PaymentMethod] = None,
        trial: bool = True
    ) -> Tuple[bool, Optional[Subscription], Optional[str]]:
        """새 구독 생성"""
        try:
            # 플랜 확인
            plan = self._plans_cache.get(plan_id)
            if not plan:
                return False, None, "Invalid plan ID"
                
            # 기존 구독 확인
            existing = await self.get_user_subscription(user_id)
            if existing and existing.is_active():
                return False, None, "Active subscription already exists"
                
            now = datetime.utcnow()
            
            # 구독 기간 계산
            if plan.billing_period == 'monthly':
                period_end = now + timedelta(days=30)
            else:  # yearly
                period_end = now + timedelta(days=365)
                
            # 무료 체험 기간
            trial_end = None
            status = SubscriptionStatus.ACTIVE
            
            if trial and plan.trial_days > 0:
                trial_end = now + timedelta(days=plan.trial_days)
                status = SubscriptionStatus.TRIAL
                
            # 구독 생성
            subscription = Subscription(
                id=self._generate_subscription_id(),
                user_id=user_id,
                plan_id=plan_id,
                tier=plan.tier,
                status=status,
                started_at=now,
                current_period_start=now,
                current_period_end=period_end,
                trial_end=trial_end,
                payment_method=payment_method,
                next_payment_date=period_end if not trial else trial_end
            )
            
            # DB 저장
            await self._save_subscription(subscription)
            
            # 사용자 티어 업데이트
            await self._update_user_tier(user_id, plan.tier)
            
            return True, subscription, None
            
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            return False, None, str(e)
            
    async def upgrade_subscription(
        self,
        user_id: str,
        new_plan_id: str
    ) -> Tuple[bool, Optional[str]]:
        """구독 업그레이드"""
        try:
            # 현재 구독 확인
            current = await self.get_user_subscription(user_id)
            if not current or not current.is_active():
                return False, "No active subscription found"
                
            # 새 플랜 확인
            new_plan = self._plans_cache.get(new_plan_id)
            if not new_plan:
                return False, "Invalid plan ID"
                
            # 같은 티어로는 변경 불가
            if current.tier == new_plan.tier:
                return False, "Already on this tier"
                
            # 업그레이드만 허용 (다운그레이드는 별도 처리)
            if new_plan.tier.value < current.tier.value:
                return False, "Use downgrade_subscription for downgrades"
                
            # 즉시 업그레이드
            current.plan_id = new_plan_id
            current.tier = new_plan.tier
            
            # 비례 배분 계산 (선택사항)
            # ... 생략 ...
            
            # DB 업데이트
            await self._save_subscription(current)
            await self._update_user_tier(user_id, new_plan.tier)
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error upgrading subscription: {str(e)}")
            return False, str(e)
            
    async def cancel_subscription(
        self,
        user_id: str,
        immediate: bool = False,
        reason: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """구독 취소"""
        try:
            subscription = await self.get_user_subscription(user_id)
            if not subscription or not subscription.is_active():
                return False, "No active subscription found"
                
            # 무료 플랜은 취소 불가
            if subscription.tier == SubscriptionTier.FREE:
                return False, "Cannot cancel free tier"
                
            subscription.cancel(immediate)
            
            if reason:
                subscription.metadata['cancellation_reason'] = reason
                
            # DB 업데이트
            await self._save_subscription(subscription)
            
            # 즉시 취소인 경우 무료 플랜으로 전환
            if immediate:
                await self._create_free_subscription(user_id)
                
            return True, None
            
        except Exception as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            return False, str(e)
            
    async def process_payment(
        self,
        user_id: str,
        amount: Decimal,
        payment_method: PaymentMethod,
        payment_data: Dict
    ) -> Tuple[bool, Optional[str]]:
        """결제 처리 (실제 결제 게이트웨이 연동 필요)"""
        try:
            subscription = await self.get_user_subscription(user_id)
            if not subscription:
                return False, "No subscription found"
                
            # TODO: 실제 결제 처리
            # - Stripe, Toss Payments 등 연동
            # - 결제 검증
            # - 영수증 생성
            
            # 결제 성공 시
            subscription.last_payment_date = datetime.utcnow()
            subscription.payment_method = payment_method
            
            # 구독 갱신
            plan = self._plans_cache.get(subscription.plan_id)
            if plan:
                subscription.renew(plan)
                
            await self._save_subscription(subscription)
            
            # 결제 기록 저장
            await self._save_payment_record(
                user_id=user_id,
                subscription_id=subscription.id,
                amount=amount,
                payment_method=payment_method,
                payment_data=payment_data
            )
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            return False, str(e)
            
    async def check_subscription_limits(
        self,
        user_id: str,
        feature: str
    ) -> Tuple[bool, Optional[str]]:
        """구독 제한 확인"""
        try:
            subscription = await self.get_user_subscription(user_id)
            if not subscription:
                return False, "No subscription found"
                
            limits = SubscriptionLimits.get_limits(subscription.tier)
            
            # 기능별 제한 확인
            if feature == 'ai_analysis':
                can_use, message = await self.usage_tracker.track_ai_analysis(
                    user_id, subscription.tier
                )
                return can_use, message
                
            elif feature == 'watchlist':
                # 관심 목록 제한 확인
                watchlist_count = await self._get_watchlist_count(user_id)
                if limits.watchlist_companies != -1 and watchlist_count >= limits.watchlist_companies:
                    return False, f"관심 목록 한도({limits.watchlist_companies}개)에 도달했습니다."
                    
            elif feature == 'export':
                if not limits.export_data:
                    return False, "데이터 내보내기는 프리미엄 기능입니다."
                    
            elif feature == 'api':
                if not limits.api_access:
                    return False, "API 액세스는 엔터프라이즈 기능입니다."
                    
            elif feature == 'real_time_alerts':
                if not limits.real_time_alerts:
                    return False, "실시간 알림은 프리미엄 기능입니다."
                    
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking limits: {str(e)}")
            return False, str(e)
            
    async def get_subscription_stats(self, user_id: str) -> Dict:
        """구독 통계 조회"""
        try:
            subscription = await self.get_user_subscription(user_id)
            if not subscription:
                return {}
                
            usage_summary = await self.usage_tracker.get_usage_summary(user_id)
            limits = SubscriptionLimits.get_limits(subscription.tier)
            
            # 오늘 사용량
            today_usage = await self.usage_tracker.get_daily_usage(user_id)
            
            return {
                'subscription': {
                    'tier': subscription.tier.value,
                    'status': subscription.status.value,
                    'days_until_renewal': subscription.days_until_renewal(),
                    'is_trial': subscription.is_trial()
                },
                'limits': {
                    'daily_ai_analyses': limits.daily_ai_analyses,
                    'watchlist_companies': limits.watchlist_companies,
                    'news_history_days': limits.news_history_days
                },
                'usage_today': {
                    'ai_analyses': today_usage.ai_analyses_used,
                    'ai_analyses_remaining': 
                        limits.daily_ai_analyses - today_usage.ai_analyses_used 
                        if limits.daily_ai_analyses != -1 else -1
                },
                'usage_summary': usage_summary
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription stats: {str(e)}")
            return {}
            
    async def _create_free_subscription(self, user_id: str) -> Subscription:
        """무료 구독 생성"""
        now = datetime.utcnow()
        subscription = Subscription(
            id=self._generate_subscription_id(),
            user_id=user_id,
            plan_id='free_tier',
            tier=SubscriptionTier.FREE,
            status=SubscriptionStatus.ACTIVE,
            started_at=now,
            current_period_start=now,
            current_period_end=now + timedelta(days=3650)  # 10년
        )
        
        await self._save_subscription(subscription)
        await self._update_user_tier(user_id, SubscriptionTier.FREE)
        
        return subscription
        
    async def _save_subscription(self, subscription: Subscription):
        """구독 정보 저장"""
        data = {
            'id': subscription.id,
            'user_id': subscription.user_id,
            'plan_id': subscription.plan_id,
            'tier': subscription.tier.value,
            'status': subscription.status.value,
            'started_at': subscription.started_at.isoformat(),
            'current_period_start': subscription.current_period_start.isoformat(),
            'current_period_end': subscription.current_period_end.isoformat(),
            'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None,
            'cancelled_at': subscription.cancelled_at.isoformat() if subscription.cancelled_at else None,
            'payment_method': subscription.payment_method.value if subscription.payment_method else None,
            'last_payment_date': subscription.last_payment_date.isoformat() if subscription.last_payment_date else None,
            'next_payment_date': subscription.next_payment_date.isoformat() if subscription.next_payment_date else None,
            'metadata': subscription.metadata
        }
        
        self.supabase.table('subscriptions').upsert(data).execute()
        
    async def _update_user_tier(self, user_id: str, tier: SubscriptionTier):
        """사용자 티어 업데이트"""
        self.supabase.table('users')\
            .update({'subscription_tier': tier.value})\
            .eq('id', user_id)\
            .execute()
            
    async def _save_payment_record(
        self,
        user_id: str,
        subscription_id: str,
        amount: Decimal,
        payment_method: PaymentMethod,
        payment_data: Dict
    ):
        """결제 기록 저장"""
        self.supabase.table('payment_history').insert({
            'user_id': user_id,
            'subscription_id': subscription_id,
            'amount': float(amount),
            'currency': 'KRW',
            'payment_method': payment_method.value,
            'payment_data': payment_data,
            'paid_at': datetime.utcnow().isoformat()
        }).execute()
        
    async def _get_watchlist_count(self, user_id: str) -> int:
        """관심 목록 개수 조회"""
        response = self.supabase.table('user_watchlists')\
            .select('id', count='exact')\
            .eq('user_id', user_id)\
            .execute()
        return response.count
        
    def _generate_subscription_id(self) -> str:
        """구독 ID 생성"""
        import uuid
        return f"sub_{uuid.uuid4().hex[:16]}"