"""알림 서비스 메인 로직"""
import logging
import asyncio
from typing import List, Dict, Optional, Set
from datetime import datetime
from app.core.supabase import get_supabase_client
from .notification_models import (
    Notification, NotificationSettings,
    NotificationType, NotificationPriority, NotificationChannel
)
from .websocket_manager import websocket_manager
from .notification_queue import NotificationQueue

logger = logging.getLogger(__name__)

class NotificationService:
    """통합 알림 서비스"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.queue = NotificationQueue()
        self.websocket_manager = websocket_manager
        
        # 사용자 설정 캐시
        self._settings_cache: Dict[str, NotificationSettings] = {}
        
        # 처리 작업
        self._processor_task = None
        self._running = False
        
    async def start(self):
        """알림 서비스 시작"""
        self._running = True
        
        # WebSocket 매니저 시작
        await self.websocket_manager.start()
        
        # 미전송 알림 로드
        pending = await self.queue.load_pending_notifications()
        for notification in pending:
            self.queue.enqueue(notification)
            
        # 알림 처리 작업 시작
        self._processor_task = asyncio.create_task(self._process_notifications())
        
        logger.info("Notification service started")
        
    async def stop(self):
        """알림 서비스 중지"""
        self._running = False
        
        if self._processor_task:
            self._processor_task.cancel()
            
        await self.websocket_manager.stop()
        
        logger.info("Notification service stopped")
        
    async def _process_notifications(self):
        """알림 큐 처리"""
        while self._running:
            try:
                # 다음 알림 가져오기
                notification = self.queue.dequeue()
                
                if notification:
                    # 알림 전송
                    success = await self._send_notification(notification)
                    
                    if success:
                        self.queue.mark_sent(notification.id)
                    else:
                        self.queue.mark_failed(notification)
                else:
                    # 큐가 비어있으면 잠시 대기
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing notifications: {str(e)}")
                await asyncio.sleep(1)
                
    async def _send_notification(self, notification: Notification) -> bool:
        """알림 전송"""
        try:
            # 사용자 설정 확인
            settings = await self.get_user_settings(notification.user_id)
            
            current_hour = datetime.utcnow().hour
            if not settings.should_send(notification.type, current_hour):
                logger.debug(f"Notification {notification.id} blocked by user settings")
                return True  # 설정에 의해 차단된 것은 성공으로 처리
                
            # 채널별 전송
            sent_channels = []
            
            for channel in notification.channels:
                if settings.channel_settings.get(channel, False):
                    if channel == NotificationChannel.WEBSOCKET:
                        # WebSocket 전송
                        if await self.websocket_manager.send_notification(
                            notification.user_id,
                            notification.to_dict()
                        ):
                            sent_channels.append(channel)
                            
                    elif channel == NotificationChannel.IN_APP:
                        # 인앱 알림 (DB 저장)
                        await self.queue.save_to_database(notification)
                        sent_channels.append(channel)
                        
                    # EMAIL, PUSH는 추후 구현
                    
            if sent_channels:
                notification.mark_as_sent()
                
                # 전송 상태 업데이트
                self.supabase.table('notifications')\
                    .update({'sent_at': notification.sent_at.isoformat()})\
                    .eq('id', notification.id)\
                    .execute()
                    
                logger.info(f"Notification {notification.id} sent via {sent_channels}")
                return True
            else:
                logger.warning(f"No channels available for notification {notification.id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send notification {notification.id}: {str(e)}")
            return False
            
    async def create_notification(
        self,
        user_id: str,
        type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Dict = None,
        article_id: Optional[int] = None,
        company_id: Optional[int] = None
    ) -> Notification:
        """새 알림 생성"""
        notification = Notification(
            user_id=user_id,
            type=type,
            priority=priority,
            title=title,
            message=message,
            data=data or {},
            article_id=article_id,
            company_id=company_id
        )
        
        # 큐에 추가
        self.queue.enqueue(notification)
        
        return notification
        
    async def create_high_impact_notification(
        self,
        article_id: int,
        company_id: int,
        impact_score: float,
        user_ids: List[str]
    ):
        """높은 영향도 뉴스 알림 생성"""
        # 기사 정보 조회
        article_response = self.supabase.table('news_articles')\
            .select('title, url')\
            .eq('id', article_id)\
            .single()\
            .execute()
            
        company_response = self.supabase.table('companies')\
            .select('name, ticker')\
            .eq('id', company_id)\
            .single()\
            .execute()
            
        if not article_response.data or not company_response.data:
            return
            
        article = article_response.data
        company = company_response.data
        
        # 각 사용자에게 알림 생성
        for user_id in user_ids:
            settings = await self.get_user_settings(user_id)
            
            # 임계값 확인
            if impact_score >= settings.impact_threshold:
                await self.create_notification(
                    user_id=user_id,
                    type=NotificationType.HIGH_IMPACT_NEWS,
                    title=f"⚡ {company['name']} 주요 뉴스",
                    message=f"영향도 {impact_score:.1%}: {article['title'][:100]}",
                    priority=NotificationPriority.HIGH,
                    data={
                        'impact_score': impact_score,
                        'article_url': article['url'],
                        'company_ticker': company['ticker']
                    },
                    article_id=article_id,
                    company_id=company_id
                )
                
    async def create_sentiment_alert(
        self,
        company_id: int,
        old_sentiment: float,
        new_sentiment: float,
        user_ids: List[str]
    ):
        """감정 변화 알림 생성"""
        sentiment_change = abs(new_sentiment - old_sentiment)
        
        company_response = self.supabase.table('companies')\
            .select('name, ticker')\
            .eq('id', company_id)\
            .single()\
            .execute()
            
        if not company_response.data:
            return
            
        company = company_response.data
        
        # 변화 방향
        if new_sentiment > old_sentiment:
            direction = "긍정적"
            emoji = "📈"
        else:
            direction = "부정적"
            emoji = "📉"
            
        for user_id in user_ids:
            settings = await self.get_user_settings(user_id)
            
            if sentiment_change >= settings.sentiment_change_threshold:
                await self.create_notification(
                    user_id=user_id,
                    type=NotificationType.SENTIMENT_ALERT,
                    title=f"{emoji} {company['name']} 감정 변화",
                    message=f"시장 감정이 {direction}으로 {sentiment_change:.1%} 변화했습니다",
                    priority=NotificationPriority.MEDIUM,
                    data={
                        'old_sentiment': old_sentiment,
                        'new_sentiment': new_sentiment,
                        'change': sentiment_change,
                        'company_ticker': company['ticker']
                    },
                    company_id=company_id
                )
                
    async def get_user_settings(self, user_id: str) -> NotificationSettings:
        """사용자 알림 설정 조회"""
        # 캐시 확인
        if user_id in self._settings_cache:
            return self._settings_cache[user_id]
            
        try:
            # 데이터베이스에서 조회
            response = self.supabase.table('user_notification_settings')\
                .select('*')\
                .eq('user_id', user_id)\
                .single()\
                .execute()
                
            if response.data:
                settings = NotificationSettings(
                    user_id=user_id,
                    enabled=response.data.get('enabled', True),
                    impact_threshold=response.data.get('impact_threshold', 0.7),
                    sentiment_change_threshold=response.data.get('sentiment_change_threshold', 0.3),
                    quiet_hours_start=response.data.get('quiet_hours_start'),
                    quiet_hours_end=response.data.get('quiet_hours_end')
                )
                
                # 알림 유형 설정
                type_settings = response.data.get('type_settings', {})
                for ntype in NotificationType:
                    if ntype.value in type_settings:
                        settings.type_settings[ntype] = type_settings[ntype.value]
                        
                # 채널 설정
                channel_settings = response.data.get('channel_settings', {})
                for channel in NotificationChannel:
                    if channel.value in channel_settings:
                        settings.channel_settings[channel] = channel_settings[channel.value]
                        
                # 관심 기업
                settings.watchlist_company_ids = response.data.get('watchlist_company_ids', [])
                
            else:
                # 기본 설정
                settings = NotificationSettings(user_id=user_id)
                
            # 캐시에 저장
            self._settings_cache[user_id] = settings
            
            return settings
            
        except Exception as e:
            logger.error(f"Failed to get user settings: {str(e)}")
            return NotificationSettings(user_id=user_id)
            
    async def update_user_settings(self, settings: NotificationSettings):
        """사용자 알림 설정 업데이트"""
        try:
            # 데이터베이스 업데이트
            self.supabase.table('user_notification_settings')\
                .upsert(settings.to_dict())\
                .execute()
                
            # 캐시 업데이트
            self._settings_cache[settings.user_id] = settings
            
        except Exception as e:
            logger.error(f"Failed to update user settings: {str(e)}")
            
    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Dict]:
        """사용자 알림 목록 조회"""
        try:
            query = self.supabase.table('notifications')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)
                
            if unread_only:
                query = query.is_('read_at', 'null')
                
            response = query.execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Failed to get user notifications: {str(e)}")
            return []
            
    async def mark_as_read(self, user_id: str, notification_ids: List[str]):
        """알림 읽음 표시"""
        try:
            self.supabase.table('notifications')\
                .update({'read_at': datetime.utcnow().isoformat()})\
                .eq('user_id', user_id)\
                .in_('id', notification_ids)\
                .execute()
                
        except Exception as e:
            logger.error(f"Failed to mark notifications as read: {str(e)}")
            
    async def get_watchlist_users(self, company_id: int) -> List[str]:
        """특정 기업을 관심 목록에 추가한 사용자 조회"""
        try:
            response = self.supabase.table('user_watchlists')\
                .select('user_id')\
                .eq('company_id', company_id)\
                .execute()
                
            return [r['user_id'] for r in response.data]
            
        except Exception as e:
            logger.error(f"Failed to get watchlist users: {str(e)}")
            return []

# 전역 알림 서비스 인스턴스
notification_service = NotificationService()