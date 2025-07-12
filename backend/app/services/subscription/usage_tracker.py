"""사용량 추적 서비스"""
import logging
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from app.core.supabase import get_supabase_client
from .subscription_models import UsageTracking, SubscriptionLimits, SubscriptionTier

logger = logging.getLogger(__name__)

class UsageTracker:
    """사용량 추적 및 제한 관리"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        # 메모리 캐시 (빠른 조회용)
        self._cache: Dict[str, UsageTracking] = {}
        
    async def get_daily_usage(self, user_id: str) -> UsageTracking:
        """오늘의 사용량 조회"""
        today = datetime.utcnow().date()
        cache_key = f"{user_id}_{today}"
        
        # 캐시 확인
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        try:
            # DB에서 조회
            response = self.supabase.table('usage_tracking')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('date', today.isoformat())\
                .single()\
                .execute()
                
            if response.data:
                usage = UsageTracking(
                    user_id=user_id,
                    date=today,
                    ai_analyses_used=response.data.get('ai_analyses_used', 0),
                    api_calls_made=response.data.get('api_calls_made', 0),
                    notifications_sent=response.data.get('notifications_sent', 0),
                    news_articles_viewed=response.data.get('news_articles_viewed', 0),
                    companies_analyzed=response.data.get('companies_analyzed', 0),
                    exports_generated=response.data.get('exports_generated', 0),
                    active_sessions=response.data.get('active_sessions', 0),
                    total_session_minutes=response.data.get('total_session_minutes', 0)
                )
            else:
                # 오늘 첫 사용
                usage = UsageTracking(user_id=user_id, date=today)
                await self._create_usage_record(usage)
                
            # 캐시 저장
            self._cache[cache_key] = usage
            return usage
            
        except Exception as e:
            logger.error(f"Error getting daily usage: {str(e)}")
            return UsageTracking(user_id=user_id, date=today)
            
    async def track_ai_analysis(self, user_id: str, tier: SubscriptionTier) -> Tuple[bool, Optional[str]]:
        """AI 분석 사용 추적"""
        usage = await self.get_daily_usage(user_id)
        limits = SubscriptionLimits.get_limits(tier)
        
        # 제한 확인
        if not usage.can_use_ai_analysis(limits.daily_ai_analyses):
            remaining_hours = 24 - datetime.utcnow().hour
            return False, f"일일 AI 분석 한도({limits.daily_ai_analyses}회)에 도달했습니다. {remaining_hours}시간 후 초기화됩니다."
            
        # 사용량 증가
        usage.increment_ai_analysis()
        await self._update_usage(usage, 'ai_analyses_used')
        
        return True, None
        
    async def track_api_call(self, user_id: str, endpoint: str):
        """API 호출 추적"""
        usage = await self.get_daily_usage(user_id)
        usage.api_calls_made += 1
        await self._update_usage(usage, 'api_calls_made')
        
        # API 사용 로그
        await self._log_api_usage(user_id, endpoint)
        
    async def track_notification(self, user_id: str, notification_type: str):
        """알림 전송 추적"""
        usage = await self.get_daily_usage(user_id)
        usage.notifications_sent += 1
        await self._update_usage(usage, 'notifications_sent')
        
    async def track_article_view(self, user_id: str, article_id: int):
        """뉴스 조회 추적"""
        usage = await self.get_daily_usage(user_id)
        usage.news_articles_viewed += 1
        await self._update_usage(usage, 'news_articles_viewed')
        
        # 개별 조회 기록
        await self._log_article_view(user_id, article_id)
        
    async def track_company_analysis(self, user_id: str, company_id: int):
        """기업 분석 추적"""
        usage = await self.get_daily_usage(user_id)
        usage.companies_analyzed += 1
        await self._update_usage(usage, 'companies_analyzed')
        
    async def track_export(self, user_id: str, export_type: str):
        """데이터 내보내기 추적"""
        usage = await self.get_daily_usage(user_id)
        usage.exports_generated += 1
        await self._update_usage(usage, 'exports_generated')
        
        # 내보내기 로그
        await self._log_export(user_id, export_type)
        
    async def track_session(self, user_id: str, session_minutes: int):
        """세션 시간 추적"""
        usage = await self.get_daily_usage(user_id)
        usage.total_session_minutes += session_minutes
        await self._update_usage(usage, 'total_session_minutes')
        
    async def check_concurrent_sessions(self, user_id: str, tier: SubscriptionTier) -> Tuple[bool, Optional[str]]:
        """동시 세션 제한 확인"""
        usage = await self.get_daily_usage(user_id)
        limits = SubscriptionLimits.get_limits(tier)
        
        if limits.concurrent_sessions != -1 and usage.active_sessions >= limits.concurrent_sessions:
            return False, f"동시 접속 제한({limits.concurrent_sessions}개)에 도달했습니다."
            
        return True, None
        
    async def get_usage_summary(self, user_id: str, days: int = 30) -> Dict:
        """사용량 요약 통계"""
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            response = self.supabase.table('usage_tracking')\
                .select('*')\
                .eq('user_id', user_id)\
                .gte('date', start_date.isoformat())\
                .lte('date', end_date.isoformat())\
                .execute()
                
            if not response.data:
                return self._empty_summary()
                
            # 집계
            total_ai_analyses = sum(r['ai_analyses_used'] for r in response.data)
            total_api_calls = sum(r['api_calls_made'] for r in response.data)
            total_notifications = sum(r['notifications_sent'] for r in response.data)
            total_articles = sum(r['news_articles_viewed'] for r in response.data)
            total_exports = sum(r['exports_generated'] for r in response.data)
            total_minutes = sum(r['total_session_minutes'] for r in response.data)
            
            # 일별 평균
            active_days = len(response.data)
            
            return {
                'period_days': days,
                'active_days': active_days,
                'totals': {
                    'ai_analyses': total_ai_analyses,
                    'api_calls': total_api_calls,
                    'notifications': total_notifications,
                    'articles_viewed': total_articles,
                    'exports': total_exports,
                    'session_hours': round(total_minutes / 60, 1)
                },
                'daily_average': {
                    'ai_analyses': round(total_ai_analyses / active_days, 1) if active_days > 0 else 0,
                    'articles_viewed': round(total_articles / active_days, 1) if active_days > 0 else 0,
                    'session_minutes': round(total_minutes / active_days, 1) if active_days > 0 else 0
                },
                'usage_trend': self._calculate_trend(response.data)
            }
            
        except Exception as e:
            logger.error(f"Error getting usage summary: {str(e)}")
            return self._empty_summary()
            
    async def _update_usage(self, usage: UsageTracking, field: str):
        """사용량 업데이트"""
        try:
            data = {
                field: getattr(usage, field),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('usage_tracking')\
                .update(data)\
                .eq('user_id', usage.user_id)\
                .eq('date', usage.date.isoformat())\
                .execute()
                
        except Exception as e:
            logger.error(f"Error updating usage: {str(e)}")
            
    async def _create_usage_record(self, usage: UsageTracking):
        """새 사용량 레코드 생성"""
        try:
            data = {
                'user_id': usage.user_id,
                'date': usage.date.isoformat(),
                'ai_analyses_used': 0,
                'api_calls_made': 0,
                'notifications_sent': 0,
                'news_articles_viewed': 0,
                'companies_analyzed': 0,
                'exports_generated': 0,
                'active_sessions': 0,
                'total_session_minutes': 0
            }
            
            self.supabase.table('usage_tracking').insert(data).execute()
            
        except Exception as e:
            logger.error(f"Error creating usage record: {str(e)}")
            
    async def _log_api_usage(self, user_id: str, endpoint: str):
        """API 사용 로그"""
        try:
            self.supabase.table('api_usage_logs').insert({
                'user_id': user_id,
                'endpoint': endpoint,
                'timestamp': datetime.utcnow().isoformat()
            }).execute()
        except:
            pass
            
    async def _log_article_view(self, user_id: str, article_id: int):
        """기사 조회 로그"""
        try:
            self.supabase.table('article_view_logs').insert({
                'user_id': user_id,
                'article_id': article_id,
                'viewed_at': datetime.utcnow().isoformat()
            }).execute()
        except:
            pass
            
    async def _log_export(self, user_id: str, export_type: str):
        """내보내기 로그"""
        try:
            self.supabase.table('export_logs').insert({
                'user_id': user_id,
                'export_type': export_type,
                'exported_at': datetime.utcnow().isoformat()
            }).execute()
        except:
            pass
            
    def _calculate_trend(self, usage_data: List[Dict]) -> str:
        """사용량 추세 계산"""
        if len(usage_data) < 7:
            return 'insufficient_data'
            
        # 최근 7일과 그 이전 7일 비교
        recent = usage_data[-7:]
        previous = usage_data[-14:-7] if len(usage_data) >= 14 else []
        
        if not previous:
            return 'increasing'
            
        recent_avg = sum(r['ai_analyses_used'] for r in recent) / 7
        previous_avg = sum(r['ai_analyses_used'] for r in previous) / len(previous)
        
        if recent_avg > previous_avg * 1.2:
            return 'increasing'
        elif recent_avg < previous_avg * 0.8:
            return 'decreasing'
        else:
            return 'stable'
            
    def _empty_summary(self) -> Dict:
        """빈 요약 데이터"""
        return {
            'period_days': 0,
            'active_days': 0,
            'totals': {
                'ai_analyses': 0,
                'api_calls': 0,
                'notifications': 0,
                'articles_viewed': 0,
                'exports': 0,
                'session_hours': 0
            },
            'daily_average': {
                'ai_analyses': 0,
                'articles_viewed': 0,
                'session_minutes': 0
            },
            'usage_trend': 'no_data'
        }
        
    async def cleanup_old_records(self, days_to_keep: int = 90):
        """오래된 사용 기록 정리"""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).date()
            
            self.supabase.table('usage_tracking')\
                .delete()\
                .lt('date', cutoff_date.isoformat())\
                .execute()
                
            logger.info(f"Cleaned up usage records older than {days_to_keep} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up old records: {str(e)}")