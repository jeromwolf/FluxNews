"""알림 관련 모델 정의"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import json

class NotificationType(Enum):
    """알림 유형"""
    HIGH_IMPACT_NEWS = "high_impact_news"  # 높은 영향도 뉴스
    SENTIMENT_ALERT = "sentiment_alert"  # 감정 변화 알림
    PRICE_MOVEMENT = "price_movement"  # 가격 변동 (향후 구현)
    WATCHLIST_UPDATE = "watchlist_update"  # 관심 기업 업데이트
    MARKET_ALERT = "market_alert"  # 시장 전반 알림
    SYSTEM = "system"  # 시스템 알림

class NotificationPriority(Enum):
    """알림 우선순위"""
    CRITICAL = "critical"  # 즉시 전송
    HIGH = "high"  # 높음
    MEDIUM = "medium"  # 보통
    LOW = "low"  # 낮음

class NotificationChannel(Enum):
    """알림 전송 채널"""
    WEBSOCKET = "websocket"  # 실시간 웹소켓
    EMAIL = "email"  # 이메일
    PUSH = "push"  # 푸시 알림 (모바일)
    IN_APP = "in_app"  # 앱 내 알림

@dataclass
class NotificationSettings:
    """사용자별 알림 설정"""
    user_id: str
    enabled: bool = True
    
    # 알림 유형별 설정
    type_settings: Dict[NotificationType, bool] = None
    
    # 채널별 설정
    channel_settings: Dict[NotificationChannel, bool] = None
    
    # 임계값 설정
    impact_threshold: float = 0.7  # 영향도 임계값
    sentiment_change_threshold: float = 0.3  # 감정 변화 임계값
    
    # 시간 설정
    quiet_hours_start: Optional[int] = None  # 방해 금지 시작 시간 (0-23)
    quiet_hours_end: Optional[int] = None  # 방해 금지 종료 시간
    
    # 관심 기업
    watchlist_company_ids: List[int] = None
    
    def __post_init__(self):
        if self.type_settings is None:
            # 기본값: 모든 알림 활성화
            self.type_settings = {
                NotificationType.HIGH_IMPACT_NEWS: True,
                NotificationType.SENTIMENT_ALERT: True,
                NotificationType.WATCHLIST_UPDATE: True,
                NotificationType.MARKET_ALERT: True,
                NotificationType.SYSTEM: True
            }
            
        if self.channel_settings is None:
            # 기본값: 웹소켓과 인앱 알림만 활성화
            self.channel_settings = {
                NotificationChannel.WEBSOCKET: True,
                NotificationChannel.IN_APP: True,
                NotificationChannel.EMAIL: False,
                NotificationChannel.PUSH: False
            }
            
        if self.watchlist_company_ids is None:
            self.watchlist_company_ids = []
            
    def should_send(self, notification_type: NotificationType, current_hour: int) -> bool:
        """알림을 보내야 하는지 확인"""
        if not self.enabled:
            return False
            
        # 알림 유형 확인
        if not self.type_settings.get(notification_type, True):
            return False
            
        # 방해 금지 시간 확인
        if self.quiet_hours_start is not None and self.quiet_hours_end is not None:
            if self.quiet_hours_start <= current_hour < self.quiet_hours_end:
                # Critical 알림은 방해 금지 시간에도 전송
                return notification_type == NotificationType.HIGH_IMPACT_NEWS
                
        return True
        
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'user_id': self.user_id,
            'enabled': self.enabled,
            'type_settings': {k.value: v for k, v in self.type_settings.items()},
            'channel_settings': {k.value: v for k, v in self.channel_settings.items()},
            'impact_threshold': self.impact_threshold,
            'sentiment_change_threshold': self.sentiment_change_threshold,
            'quiet_hours_start': self.quiet_hours_start,
            'quiet_hours_end': self.quiet_hours_end,
            'watchlist_company_ids': self.watchlist_company_ids
        }

@dataclass
class Notification:
    """알림 객체"""
    id: Optional[str] = None
    user_id: str = None
    type: NotificationType = None
    priority: NotificationPriority = NotificationPriority.MEDIUM
    
    # 알림 내용
    title: str = ""
    message: str = ""
    data: Dict[str, Any] = None
    
    # 관련 정보
    article_id: Optional[int] = None
    company_id: Optional[int] = None
    
    # 전송 정보
    channels: List[NotificationChannel] = None
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    # 메타데이터
    created_at: datetime = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
            
        if self.channels is None:
            self.channels = [NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP]
            
        if self.data is None:
            self.data = {}
            
        if self.id is None:
            # 간단한 ID 생성
            import uuid
            self.id = str(uuid.uuid4())
            
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type.value,
            'priority': self.priority.value,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'article_id': self.article_id,
            'company_id': self.company_id,
            'channels': [c.value for c in self.channels],
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
        
    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_dict())
        
    def mark_as_sent(self):
        """전송 완료 표시"""
        self.sent_at = datetime.utcnow()
        
    def mark_as_read(self):
        """읽음 표시"""
        self.read_at = datetime.utcnow()
        
    def is_expired(self) -> bool:
        """만료 여부 확인"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at