"""구독 관련 API 엔드포인트"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Optional
from pydantic import BaseModel
from decimal import Decimal
from app.core.supabase import get_supabase_client
from app.services.subscription import (
    SubscriptionService, SubscriptionPlan,
    PaymentMethod
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class CreateSubscriptionRequest(BaseModel):
    """구독 생성 요청"""
    plan_id: str
    payment_method: Optional[str] = None
    trial: bool = True

class UpgradeSubscriptionRequest(BaseModel):
    """구독 업그레이드 요청"""
    new_plan_id: str

class CancelSubscriptionRequest(BaseModel):
    """구독 취소 요청"""
    immediate: bool = False
    reason: Optional[str] = None

class ProcessPaymentRequest(BaseModel):
    """결제 처리 요청"""
    amount: float
    payment_method: str
    payment_token: str  # 결제 게이트웨이 토큰
    metadata: Optional[Dict] = None

@router.get("/plans")
async def get_subscription_plans():
    """구독 플랜 목록 조회"""
    plans = SubscriptionPlan.get_default_plans()
    
    return {
        "plans": [
            {
                "id": plan.id,
                "tier": plan.tier.value,
                "name": plan.name,
                "description": plan.description,
                "price_krw": plan.price_krw,
                "price_usd": float(plan.price_usd),
                "billing_period": plan.billing_period,
                "discount_percentage": plan.discount_percentage,
                "trial_days": plan.trial_days,
                "features": plan.features
            }
            for plan in plans
        ]
    }

@router.get("/current")
async def get_current_subscription(user_id: str = Query(..., description="User ID")):
    """현재 구독 정보 조회"""
    service = SubscriptionService()
    subscription = await service.get_user_subscription(user_id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
        
    return {
        "subscription": {
            "id": subscription.id,
            "plan_id": subscription.plan_id,
            "tier": subscription.tier.value,
            "status": subscription.status.value,
            "is_active": subscription.is_active(),
            "is_trial": subscription.is_trial(),
            "started_at": subscription.started_at.isoformat(),
            "current_period_end": subscription.current_period_end.isoformat(),
            "trial_end": subscription.trial_end.isoformat() if subscription.trial_end else None,
            "cancelled_at": subscription.cancelled_at.isoformat() if subscription.cancelled_at else None,
            "days_until_renewal": subscription.days_until_renewal()
        }
    }

@router.post("/create")
async def create_subscription(
    user_id: str = Query(..., description="User ID"),
    request: CreateSubscriptionRequest = None
):
    """새 구독 생성"""
    service = SubscriptionService()
    
    payment_method = None
    if request.payment_method:
        try:
            payment_method = PaymentMethod(request.payment_method)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payment method")
    
    success, subscription, error = await service.create_subscription(
        user_id=user_id,
        plan_id=request.plan_id,
        payment_method=payment_method,
        trial=request.trial
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
        
    return {
        "success": True,
        "subscription": {
            "id": subscription.id,
            "plan_id": subscription.plan_id,
            "tier": subscription.tier.value,
            "status": subscription.status.value,
            "trial_end": subscription.trial_end.isoformat() if subscription.trial_end else None
        }
    }

@router.put("/upgrade")
async def upgrade_subscription(
    user_id: str = Query(..., description="User ID"),
    request: UpgradeSubscriptionRequest = None
):
    """구독 업그레이드"""
    service = SubscriptionService()
    
    success, error = await service.upgrade_subscription(
        user_id=user_id,
        new_plan_id=request.new_plan_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
        
    return {
        "success": True,
        "message": "Subscription upgraded successfully"
    }

@router.post("/cancel")
async def cancel_subscription(
    user_id: str = Query(..., description="User ID"),
    request: CancelSubscriptionRequest = None
):
    """구독 취소"""
    service = SubscriptionService()
    
    success, error = await service.cancel_subscription(
        user_id=user_id,
        immediate=request.immediate,
        reason=request.reason
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
        
    return {
        "success": True,
        "message": "Subscription cancelled successfully",
        "immediate": request.immediate
    }

@router.post("/payment")
async def process_payment(
    user_id: str = Query(..., description="User ID"),
    request: ProcessPaymentRequest = None
):
    """결제 처리"""
    service = SubscriptionService()
    
    try:
        payment_method = PaymentMethod(request.payment_method)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payment method")
    
    # TODO: 실제 결제 게이트웨이 연동
    # 여기서는 시뮬레이션만 수행
    payment_data = {
        "token": request.payment_token,
        "metadata": request.metadata or {}
    }
    
    success, error = await service.process_payment(
        user_id=user_id,
        amount=Decimal(str(request.amount)),
        payment_method=payment_method,
        payment_data=payment_data
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
        
    return {
        "success": True,
        "message": "Payment processed successfully"
    }

@router.get("/stats")
async def get_subscription_stats(user_id: str = Query(..., description="User ID")):
    """구독 및 사용량 통계"""
    service = SubscriptionService()
    stats = await service.get_subscription_stats(user_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="No subscription found")
        
    return stats

@router.get("/check-limit/{feature}")
async def check_feature_limit(
    feature: str,
    user_id: str = Query(..., description="User ID")
):
    """특정 기능 제한 확인"""
    service = SubscriptionService()
    
    can_use, message = await service.check_subscription_limits(
        user_id=user_id,
        feature=feature
    )
    
    return {
        "feature": feature,
        "can_use": can_use,
        "message": message
    }

@router.get("/usage/summary")
async def get_usage_summary(
    user_id: str = Query(..., description="User ID"),
    days: int = Query(30, description="Period in days")
):
    """사용량 요약 조회"""
    service = SubscriptionService()
    usage_tracker = service.usage_tracker
    
    summary = await usage_tracker.get_usage_summary(user_id, days)
    
    return summary