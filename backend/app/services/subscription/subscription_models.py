"""구독 관련 모델 정의"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from enum import Enum
from decimal import Decimal

class SubscriptionTier(Enum):
    """구독 등급"""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(Enum):
    """구독 상태"""
    ACTIVE = "active"
    TRIAL = "trial"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    SUSPENDED = "suspended"  # 결제 실패 등

class PaymentMethod(Enum):
    """결제 방법"""
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    TOSS_PAYMENTS = "toss_payments"  # 한국 결제
    NAVER_PAY = "naver_pay"
    KAKAO_PAY = "kakao_pay"

@dataclass
class SubscriptionLimits:
    """티어별 제한 사항"""
    tier: SubscriptionTier
    
    # 기능 제한
    daily_ai_analyses: int
    watchlist_companies: int
    real_time_alerts: bool
    advanced_analytics: bool
    api_access: bool
    export_data: bool
    
    # 데이터 제한
    news_history_days: int  # 과거 뉴스 조회 기간
    concurrent_sessions: int  # 동시 접속 수
    
    # 알림 설정
    email_notifications: bool
    push_notifications: bool
    webhook_alerts: bool
    
    @classmethod
    def get_limits(cls, tier: SubscriptionTier) -> 'SubscriptionLimits':
        """티어별 기본 제한 설정"""
        limits_config = {
            SubscriptionTier.FREE: {
                'daily_ai_analyses': 3,
                'watchlist_companies': 3,
                'real_time_alerts': False,
                'advanced_analytics': False,
                'api_access': False,
                'export_data': False,
                'news_history_days': 7,
                'concurrent_sessions': 1,
                'email_notifications': True,
                'push_notifications': False,
                'webhook_alerts': False
            },
            SubscriptionTier.PREMIUM: {
                'daily_ai_analyses': -1,  # 무제한
                'watchlist_companies': 50,
                'real_time_alerts': True,
                'advanced_analytics': True,
                'api_access': False,
                'export_data': True,
                'news_history_days': 90,
                'concurrent_sessions': 3,
                'email_notifications': True,
                'push_notifications': True,
                'webhook_alerts': False
            },
            SubscriptionTier.ENTERPRISE: {
                'daily_ai_analyses': -1,
                'watchlist_companies': -1,  # 무제한
                'real_time_alerts': True,
                'advanced_analytics': True,
                'api_access': True,
                'export_data': True,
                'news_history_days': 365,
                'concurrent_sessions': -1,  # 무제한
                'email_notifications': True,
                'push_notifications': True,
                'webhook_alerts': True
            }
        }
        
        config = limits_config[tier]
        return cls(tier=tier, **config)

@dataclass
class SubscriptionPlan:
    """구독 플랜 정보"""
    id: str
    tier: SubscriptionTier
    name: str
    description: str
    
    # 가격 정보
    price_krw: int  # 원화
    price_usd: Decimal  # 달러
    billing_period: str  # 'monthly', 'yearly'
    
    # 할인 정보
    discount_percentage: int = 0  # 연간 결제 할인 등
    trial_days: int = 0
    
    # 플랜 특징
    features: List[str] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = []
            
    def get_price(self, currency: str = 'KRW') -> float:
        """통화별 가격 반환"""
        if currency == 'KRW':
            return self.price_krw
        elif currency == 'USD':
            return float(self.price_usd)
        else:
            raise ValueError(f"Unsupported currency: {currency}")
            
    @classmethod
    def get_default_plans(cls) -> List['SubscriptionPlan']:
        """기본 구독 플랜 목록"""
        return [
            cls(
                id='free_tier',
                tier=SubscriptionTier.FREE,
                name='무료',
                description='개인 투자자를 위한 기본 기능',
                price_krw=0,
                price_usd=Decimal('0'),
                billing_period='monthly',
                features=[
                    '하루 3회 AI 분석',
                    '3개 기업 관심 목록',
                    '7일간 뉴스 히스토리',
                    '기본 대시보드'
                ]
            ),
            cls(
                id='premium_monthly',
                tier=SubscriptionTier.PREMIUM,
                name='프리미엄',
                description='전문 투자자를 위한 고급 기능',
                price_krw=9900,
                price_usd=Decimal('9.99'),
                billing_period='monthly',
                trial_days=7,
                features=[
                    '무제한 AI 분석',
                    '50개 기업 관심 목록',
                    '실시간 알림',
                    '고급 분석 도구',
                    '90일 뉴스 히스토리',
                    '데이터 내보내기'
                ]
            ),
            cls(
                id='premium_yearly',
                tier=SubscriptionTier.PREMIUM,
                name='프리미엄 (연간)',
                description='연간 결제 시 20% 할인',
                price_krw=95040,  # 9900 * 12 * 0.8
                price_usd=Decimal('95.99'),  # 9.99 * 12 * 0.8
                billing_period='yearly',
                discount_percentage=20,
                features=[
                    '프리미엄 월간의 모든 기능',
                    '20% 할인 혜택'
                ]
            ),
            cls(
                id='enterprise',
                tier=SubscriptionTier.ENTERPRISE,
                name='엔터프라이즈',
                description='기업 고객을 위한 맞춤 솔루션',
                price_krw=99000,
                price_usd=Decimal('99'),
                billing_period='monthly',
                features=[
                    '모든 프리미엄 기능',
                    'API 액세스',
                    '무제한 사용',
                    '전담 지원',
                    'Webhook 알림',
                    'SLA 보장'
                ]
            )
        ]

@dataclass
class Subscription:
    """사용자 구독 정보"""
    id: str
    user_id: str
    plan_id: str
    tier: SubscriptionTier
    status: SubscriptionStatus
    
    # 구독 기간
    started_at: datetime
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # 결제 정보
    payment_method: Optional[PaymentMethod] = None
    last_payment_date: Optional[datetime] = None
    next_payment_date: Optional[datetime] = None
    
    # 메타데이터
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
            
    def is_active(self) -> bool:
        """활성 구독 여부"""
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
        
    def is_trial(self) -> bool:
        """무료 체험 중인지"""
        return self.status == SubscriptionStatus.TRIAL and self.trial_end and datetime.utcnow() < self.trial_end
        
    def days_until_renewal(self) -> int:
        """갱신일까지 남은 일수"""
        if self.next_payment_date:
            delta = self.next_payment_date - datetime.utcnow()
            return max(0, delta.days)
        return 0
        
    def cancel(self, immediate: bool = False):
        """구독 취소"""
        self.cancelled_at = datetime.utcnow()
        
        if immediate:
            self.status = SubscriptionStatus.CANCELLED
        else:
            # 현재 기간 종료 시 취소
            self.status = SubscriptionStatus.ACTIVE
            self.metadata['cancel_at_period_end'] = True
            
    def renew(self, plan: SubscriptionPlan):
        """구독 갱신"""
        now = datetime.utcnow()
        
        if plan.billing_period == 'monthly':
            delta = timedelta(days=30)
        else:  # yearly
            delta = timedelta(days=365)
            
        self.current_period_start = self.current_period_end
        self.current_period_end = self.current_period_end + delta
        self.next_payment_date = self.current_period_end
        self.last_payment_date = now
        self.status = SubscriptionStatus.ACTIVE

@dataclass
class UsageTracking:
    """사용량 추적"""
    user_id: str
    date: datetime
    
    # 일일 사용량
    ai_analyses_used: int = 0
    api_calls_made: int = 0
    notifications_sent: int = 0
    
    # 데이터 사용량
    news_articles_viewed: int = 0
    companies_analyzed: int = 0
    exports_generated: int = 0
    
    # 세션 정보
    active_sessions: int = 0
    total_session_minutes: int = 0
    
    def increment_ai_analysis(self):
        """AI 분석 사용량 증가"""
        self.ai_analyses_used += 1
        
    def can_use_ai_analysis(self, limit: int) -> bool:
        """AI 분석 사용 가능 여부"""
        if limit == -1:  # 무제한
            return True
        return self.ai_analyses_used < limit