"""AI API 비용 추적 및 제한 관리"""
import json
import logging
from typing import Dict, Optional, Any, List, Tuple, Set
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import asyncio
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)

class CostTracker:
    """AI API 사용량 및 비용 추적"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        # 메모리 캐시 (빠른 조회용)
        self._cache = defaultdict(lambda: {
            "daily_cost": 0.0,
            "monthly_cost": 0.0,
            "daily_requests": 0,
            "last_updated": None
        })
        self._lock = asyncio.Lock()
        
        # 모델별 가격 (1K 토큰당 USD)
        self.pricing = {
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
        }
        
        # 사용자 티어별 제한
        self.limits = {
            "free": {
                "daily_requests": 3,
                "daily_cost_usd": 0.1,
                "monthly_cost_usd": 3.0
            },
            "premium": {
                "daily_requests": 1000,
                "daily_cost_usd": 5.0,
                "monthly_cost_usd": 100.0
            },
            "enterprise": {
                "daily_requests": 10000,
                "daily_cost_usd": 50.0,
                "monthly_cost_usd": 1000.0
            }
        }
        
    async def track_usage(
        self,
        user_id: str,
        model: str,
        usage: Dict[str, int],
        request_type: str = "analysis"
    ) -> Dict[str, Any]:
        """
        API 사용량 추적
        
        Args:
            user_id: 사용자 ID
            model: 사용한 모델
            usage: 토큰 사용량 (prompt_tokens, completion_tokens)
            request_type: 요청 유형
            
        Returns:
            추적 결과
        """
        async with self._lock:
            # 비용 계산
            cost = self._calculate_cost(model, usage)
            
            # 현재 시간
            now = datetime.now(timezone.utc)
            today = now.date().isoformat()
            
            try:
                # 데이터베이스에 기록
                record = {
                    "user_id": user_id,
                    "date": today,
                    "model": model,
                    "request_type": request_type,
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "cost_usd": cost["total_cost"],
                    "cost_krw": cost["total_cost_krw"]
                }
                
                self.supabase.table("ai_usage").insert(record).execute()
                
                # 캐시 업데이트
                await self._update_cache(user_id)
                
                # 현재 사용량 반환
                return {
                    "success": True,
                    "cost": cost,
                    "daily_usage": self._cache[user_id]["daily_cost"],
                    "monthly_usage": self._cache[user_id]["monthly_cost"],
                    "daily_requests": self._cache[user_id]["daily_requests"]
                }
                
            except Exception as e:
                logger.error(f"Error tracking usage: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "cost": cost
                }
                
    async def check_limits(self, user_id: str, user_tier: str = "free") -> Tuple[bool, Optional[str]]:
        """
        사용자 제한 확인
        
        Args:
            user_id: 사용자 ID
            user_tier: 사용자 티어
            
        Returns:
            (허용 여부, 제한 사유)
        """
        async with self._lock:
            # 캐시 업데이트
            await self._update_cache(user_id)
            
            user_usage = self._cache[user_id]
            tier_limits = self.limits.get(user_tier, self.limits["free"])
            
            # 일일 요청 수 확인
            if user_usage["daily_requests"] >= tier_limits["daily_requests"]:
                return False, f"Daily request limit reached ({tier_limits['daily_requests']} requests)"
                
            # 일일 비용 확인
            if user_usage["daily_cost"] >= tier_limits["daily_cost_usd"]:
                return False, f"Daily cost limit reached (${tier_limits['daily_cost_usd']})"
                
            # 월간 비용 확인
            if user_usage["monthly_cost"] >= tier_limits["monthly_cost_usd"]:
                return False, f"Monthly cost limit reached (${tier_limits['monthly_cost_usd']})"
                
            return True, None
            
    async def get_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """
        사용자 사용량 통계 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            사용량 통계
        """
        now = datetime.now(timezone.utc)
        today = now.date()
        month_start = today.replace(day=1)
        
        try:
            # 오늘 사용량
            daily_response = self.supabase.table("ai_usage")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("date", today.isoformat())\
                .execute()
                
            # 이번 달 사용량
            monthly_response = self.supabase.table("ai_usage")\
                .select("*")\
                .eq("user_id", user_id)\
                .gte("date", month_start.isoformat())\
                .execute()
                
            # 통계 계산
            daily_stats = self._aggregate_usage(daily_response.data)
            monthly_stats = self._aggregate_usage(monthly_response.data)
            
            # 모델별 사용량
            model_usage = defaultdict(lambda: {"requests": 0, "tokens": 0, "cost": 0.0})
            for record in monthly_response.data:
                model = record["model"]
                model_usage[model]["requests"] += 1
                model_usage[model]["tokens"] += record["total_tokens"]
                model_usage[model]["cost"] += record["cost_usd"]
                
            return {
                "daily": {
                    "requests": daily_stats["requests"],
                    "tokens": daily_stats["tokens"],
                    "cost_usd": daily_stats["cost"],
                    "cost_krw": daily_stats["cost"] * 1400
                },
                "monthly": {
                    "requests": monthly_stats["requests"],
                    "tokens": monthly_stats["tokens"],
                    "cost_usd": monthly_stats["cost"],
                    "cost_krw": monthly_stats["cost"] * 1400
                },
                "by_model": dict(model_usage),
                "last_updated": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {str(e)}")
            return {
                "error": str(e),
                "daily": {"requests": 0, "tokens": 0, "cost_usd": 0.0},
                "monthly": {"requests": 0, "tokens": 0, "cost_usd": 0.0}
            }
            
    async def get_global_stats(self) -> Dict[str, Any]:
        """전체 시스템 사용량 통계"""
        now = datetime.now(timezone.utc)
        today = now.date()
        month_start = today.replace(day=1)
        
        try:
            # 오늘 전체 사용량
            daily_response = self.supabase.table("ai_usage")\
                .select("*")\
                .eq("date", today.isoformat())\
                .execute()
                
            # 이번 달 전체 사용량
            monthly_response = self.supabase.table("ai_usage")\
                .select("*")\
                .gte("date", month_start.isoformat())\
                .execute()
                
            # 통계 계산
            daily_stats = self._aggregate_usage(daily_response.data)
            monthly_stats = self._aggregate_usage(monthly_response.data)
            
            # 사용자 수
            unique_users_today = len(set(r["user_id"] for r in daily_response.data))
            unique_users_month = len(set(r["user_id"] for r in monthly_response.data))
            
            return {
                "daily": {
                    "requests": daily_stats["requests"],
                    "tokens": daily_stats["tokens"],
                    "cost_usd": daily_stats["cost"],
                    "unique_users": unique_users_today
                },
                "monthly": {
                    "requests": monthly_stats["requests"],
                    "tokens": monthly_stats["tokens"],
                    "cost_usd": monthly_stats["cost"],
                    "unique_users": unique_users_month
                },
                "monthly_budget_used": (monthly_stats["cost"] / 71.43) * 100,  # $71.43 = 100,000원 / 1400
                "last_updated": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting global stats: {str(e)}")
            return {"error": str(e)}
            
    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> Dict[str, float]:
        """비용 계산"""
        model_pricing = self.pricing.get(model, self.pricing["gpt-4o-mini"])
        
        input_cost = (usage.get("prompt_tokens", 0) / 1000) * model_pricing["input"]
        output_cost = (usage.get("completion_tokens", 0) / 1000) * model_pricing["output"]
        total_cost = input_cost + output_cost
        
        return {
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6),
            "total_cost_krw": round(total_cost * 1400, 2)
        }
        
    def _aggregate_usage(self, records: List[Dict]) -> Dict[str, Any]:
        """사용량 레코드 집계"""
        return {
            "requests": len(records),
            "tokens": sum(r["total_tokens"] for r in records),
            "cost": sum(r["cost_usd"] for r in records)
        }
        
    async def _update_cache(self, user_id: str):
        """캐시 업데이트"""
        now = datetime.now(timezone.utc)
        today = now.date()
        
        # 캐시가 최신인지 확인
        if self._cache[user_id]["last_updated"]:
            last_update = self._cache[user_id]["last_updated"]
            if (now - last_update).seconds < 300:  # 5분 이내면 스킵
                return
                
        # 데이터베이스에서 조회
        try:
            # 오늘 사용량
            daily_response = self.supabase.table("ai_usage")\
                .select("cost_usd")\
                .eq("user_id", user_id)\
                .eq("date", today.isoformat())\
                .execute()
                
            # 이번 달 사용량
            month_start = today.replace(day=1)
            monthly_response = self.supabase.table("ai_usage")\
                .select("cost_usd")\
                .eq("user_id", user_id)\
                .gte("date", month_start.isoformat())\
                .execute()
                
            # 캐시 업데이트
            self._cache[user_id] = {
                "daily_cost": sum(r["cost_usd"] for r in daily_response.data),
                "monthly_cost": sum(r["cost_usd"] for r in monthly_response.data),
                "daily_requests": len(daily_response.data),
                "last_updated": now
            }
            
        except Exception as e:
            logger.error(f"Error updating cache: {str(e)}")