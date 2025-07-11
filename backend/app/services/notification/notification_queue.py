"""알림 큐 및 전송 로직"""
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import deque
from .notification_models import Notification, NotificationPriority, NotificationChannel
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)

class NotificationQueue:
    """알림 큐 관리"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        
        # 우선순위별 큐
        self.queues = {
            NotificationPriority.CRITICAL: deque(),
            NotificationPriority.HIGH: deque(),
            NotificationPriority.MEDIUM: deque(),
            NotificationPriority.LOW: deque()
        }
        
        # 처리 중인 알림 추적
        self.processing = set()
        
        # 재시도 큐
        self.retry_queue = deque()
        
        # 통계
        self.stats = {
            'enqueued': 0,
            'sent': 0,
            'failed': 0,
            'retried': 0
        }
        
        self.supabase = get_supabase_client()
        
    def enqueue(self, notification: Notification) -> bool:
        """알림을 큐에 추가"""
        # 크기 제한 확인
        total_size = sum(len(q) for q in self.queues.values())
        if total_size >= self.max_size:
            logger.warning("Notification queue is full")
            return False
            
        # 우선순위별 큐에 추가
        priority_queue = self.queues[notification.priority]
        priority_queue.append(notification)
        
        self.stats['enqueued'] += 1
        logger.debug(f"Enqueued notification {notification.id} with priority {notification.priority.value}")
        
        return True
        
    def dequeue(self) -> Optional[Notification]:
        """우선순위에 따라 다음 알림 가져오기"""
        # 우선순위 순서대로 확인
        for priority in NotificationPriority:
            queue = self.queues[priority]
            if queue:
                notification = queue.popleft()
                self.processing.add(notification.id)
                return notification
                
        # 재시도 큐 확인
        if self.retry_queue:
            retry_item = self.retry_queue[0]
            if retry_item['retry_at'] <= datetime.utcnow():
                self.retry_queue.popleft()
                notification = retry_item['notification']
                self.processing.add(notification.id)
                self.stats['retried'] += 1
                return notification
                
        return None
        
    def mark_sent(self, notification_id: str):
        """알림 전송 완료 표시"""
        if notification_id in self.processing:
            self.processing.remove(notification_id)
            self.stats['sent'] += 1
            
    def mark_failed(self, notification: Notification, retry: bool = True):
        """알림 전송 실패 표시"""
        if notification.id in self.processing:
            self.processing.remove(notification.id)
            
        self.stats['failed'] += 1
        
        if retry and self._should_retry(notification):
            # 재시도 큐에 추가
            retry_delay = self._get_retry_delay(notification)
            self.retry_queue.append({
                'notification': notification,
                'retry_at': datetime.utcnow() + retry_delay,
                'retry_count': notification.data.get('retry_count', 0) + 1
            })
            notification.data['retry_count'] = notification.data.get('retry_count', 0) + 1
            
    def _should_retry(self, notification: Notification) -> bool:
        """재시도 여부 결정"""
        retry_count = notification.data.get('retry_count', 0)
        max_retries = 3 if notification.priority == NotificationPriority.CRITICAL else 2
        
        return retry_count < max_retries
        
    def _get_retry_delay(self, notification: Notification) -> timedelta:
        """재시도 지연 시간 계산"""
        retry_count = notification.data.get('retry_count', 0)
        
        # 지수 백오프
        if notification.priority == NotificationPriority.CRITICAL:
            base_delay = 5  # 5초
        else:
            base_delay = 30  # 30초
            
        delay_seconds = base_delay * (2 ** retry_count)
        return timedelta(seconds=min(delay_seconds, 300))  # 최대 5분
        
    def get_stats(self) -> Dict:
        """큐 통계 반환"""
        queue_sizes = {
            priority.value: len(queue)
            for priority, queue in self.queues.items()
        }
        
        return {
            'queue_sizes': queue_sizes,
            'total_queued': sum(queue_sizes.values()),
            'processing': len(self.processing),
            'retry_queue_size': len(self.retry_queue),
            'stats': self.stats
        }
        
    async def save_to_database(self, notification: Notification):
        """알림을 데이터베이스에 저장"""
        try:
            record = {
                'id': notification.id,
                'user_id': notification.user_id,
                'type': notification.type.value,
                'priority': notification.priority.value,
                'title': notification.title,
                'message': notification.message,
                'data': notification.data,
                'article_id': notification.article_id,
                'company_id': notification.company_id,
                'channels': [c.value for c in notification.channels],
                'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
                'read_at': notification.read_at.isoformat() if notification.read_at else None,
                'created_at': notification.created_at.isoformat(),
                'expires_at': notification.expires_at.isoformat() if notification.expires_at else None
            }
            
            self.supabase.table('notifications').insert(record).execute()
            
        except Exception as e:
            logger.error(f"Failed to save notification to database: {str(e)}")
            
    async def load_pending_notifications(self) -> List[Notification]:
        """데이터베이스에서 미전송 알림 로드"""
        try:
            # 미전송 알림 조회
            response = self.supabase.table('notifications')\
                .select('*')\
                .is_('sent_at', 'null')\
                .order('created_at', desc=False)\
                .limit(100)\
                .execute()
                
            notifications = []
            for record in response.data:
                # Notification 객체로 변환
                notification = Notification(
                    id=record['id'],
                    user_id=record['user_id'],
                    type=NotificationType(record['type']),
                    priority=NotificationPriority(record['priority']),
                    title=record['title'],
                    message=record['message'],
                    data=record.get('data', {}),
                    article_id=record.get('article_id'),
                    company_id=record.get('company_id'),
                    channels=[NotificationChannel(c) for c in record.get('channels', [])],
                    created_at=datetime.fromisoformat(record['created_at'].replace('Z', '+00:00'))
                )
                
                # 만료되지 않은 알림만 추가
                if not notification.is_expired():
                    notifications.append(notification)
                    
            return notifications
            
        except Exception as e:
            logger.error(f"Failed to load pending notifications: {str(e)}")
            return []
            
    async def cleanup_old_notifications(self, days: int = 30):
        """오래된 알림 정리"""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            self.supabase.table('notifications')\
                .delete()\
                .lt('created_at', cutoff_date)\
                .execute()
                
            logger.info(f"Cleaned up notifications older than {days} days")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old notifications: {str(e)}")