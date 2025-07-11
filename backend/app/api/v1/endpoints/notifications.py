"""알림 관련 API 엔드포인트"""
from fastapi import APIRouter, HTTPException, WebSocket, Query, Depends
from typing import List, Dict, Optional
from pydantic import BaseModel
from app.core.supabase import get_supabase_client
from app.services.notification import (
    notification_service,
    NotificationSettings,
    NotificationType,
    NotificationChannel
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class NotificationSettingsUpdate(BaseModel):
    """알림 설정 업데이트 모델"""
    enabled: Optional[bool] = None
    type_settings: Optional[Dict[str, bool]] = None
    channel_settings: Optional[Dict[str, bool]] = None
    impact_threshold: Optional[float] = None
    sentiment_change_threshold: Optional[float] = None
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None

class MarkReadRequest(BaseModel):
    """읽음 표시 요청"""
    notification_ids: List[str]

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket 연결 엔드포인트"""
    await notification_service.websocket_manager.handle_websocket(websocket, user_id)

@router.get("/")
async def get_notifications(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(50, description="Maximum number of notifications"),
    unread_only: bool = Query(False, description="Only return unread notifications")
):
    """사용자 알림 목록 조회"""
    notifications = await notification_service.get_user_notifications(
        user_id=user_id,
        limit=limit,
        unread_only=unread_only
    )
    
    return {
        "notifications": notifications,
        "total": len(notifications),
        "unread_count": sum(1 for n in notifications if n.get('read_at') is None)
    }

@router.post("/mark-read")
async def mark_notifications_read(
    user_id: str = Query(..., description="User ID"),
    request: MarkReadRequest = None
):
    """알림 읽음 표시"""
    await notification_service.mark_as_read(user_id, request.notification_ids)
    
    return {
        "success": True,
        "marked_count": len(request.notification_ids)
    }

@router.get("/settings")
async def get_notification_settings(user_id: str = Query(..., description="User ID")):
    """알림 설정 조회"""
    settings = await notification_service.get_user_settings(user_id)
    return settings.to_dict()

@router.put("/settings")
async def update_notification_settings(
    user_id: str = Query(..., description="User ID"),
    update: NotificationSettingsUpdate = None
):
    """알림 설정 업데이트"""
    # 현재 설정 가져오기
    settings = await notification_service.get_user_settings(user_id)
    
    # 업데이트 적용
    if update.enabled is not None:
        settings.enabled = update.enabled
        
    if update.type_settings:
        for type_str, enabled in update.type_settings.items():
            try:
                ntype = NotificationType(type_str)
                settings.type_settings[ntype] = enabled
            except ValueError:
                logger.warning(f"Invalid notification type: {type_str}")
                
    if update.channel_settings:
        for channel_str, enabled in update.channel_settings.items():
            try:
                channel = NotificationChannel(channel_str)
                settings.channel_settings[channel] = enabled
            except ValueError:
                logger.warning(f"Invalid notification channel: {channel_str}")
                
    if update.impact_threshold is not None:
        settings.impact_threshold = max(0.0, min(1.0, update.impact_threshold))
        
    if update.sentiment_change_threshold is not None:
        settings.sentiment_change_threshold = max(0.0, min(1.0, update.sentiment_change_threshold))
        
    if update.quiet_hours_start is not None:
        settings.quiet_hours_start = max(0, min(23, update.quiet_hours_start))
        
    if update.quiet_hours_end is not None:
        settings.quiet_hours_end = max(0, min(23, update.quiet_hours_end))
        
    # 저장
    await notification_service.update_user_settings(settings)
    
    return {
        "success": True,
        "settings": settings.to_dict()
    }

@router.get("/stats")
async def get_notification_stats():
    """알림 시스템 통계"""
    queue_stats = notification_service.queue.get_stats()
    ws_stats = notification_service.websocket_manager.get_connection_stats()
    
    return {
        "queue": queue_stats,
        "websocket": ws_stats
    }

@router.post("/test")
async def send_test_notification(
    user_id: str = Query(..., description="User ID"),
    title: str = Query("테스트 알림", description="Notification title"),
    message: str = Query("이것은 테스트 알림입니다", description="Notification message")
):
    """테스트 알림 전송"""
    notification = await notification_service.create_notification(
        user_id=user_id,
        type=NotificationType.SYSTEM,
        title=title,
        message=message,
        data={"test": True}
    )
    
    return {
        "success": True,
        "notification_id": notification.id,
        "message": "Test notification queued"
    }