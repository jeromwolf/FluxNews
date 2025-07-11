"""WebSocket 연결 관리"""
import logging
from typing import Dict, Set, List
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        # user_id -> WebSocket 연결 매핑
        self.active_connections: Dict[str, WebSocket] = {}
        # 연결 메타데이터
        self.connection_info: Dict[str, Dict] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """새 연결 수락"""
        await websocket.accept()
        
        # 기존 연결이 있으면 종료
        if user_id in self.active_connections:
            old_ws = self.active_connections[user_id]
            try:
                await old_ws.close()
            except:
                pass
                
        self.active_connections[user_id] = websocket
        self.connection_info[user_id] = {
            'connected_at': datetime.utcnow().isoformat(),
            'last_ping': datetime.utcnow().isoformat()
        }
        
        logger.info(f"User {user_id} connected via WebSocket")
        
        # 연결 확인 메시지
        await self.send_personal_message(
            user_id,
            {
                'type': 'connection',
                'status': 'connected',
                'message': 'WebSocket connection established'
            }
        )
        
    def disconnect(self, user_id: str):
        """연결 종료"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            del self.connection_info[user_id]
            logger.info(f"User {user_id} disconnected from WebSocket")
            
    async def send_personal_message(self, user_id: str, message: Dict):
        """특정 사용자에게 메시지 전송"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_json(message)
                return True
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {str(e)}")
                self.disconnect(user_id)
                return False
        return False
        
    async def broadcast(self, message: Dict, user_ids: List[str] = None):
        """여러 사용자에게 브로드캐스트"""
        if user_ids is None:
            user_ids = list(self.active_connections.keys())
            
        disconnected_users = []
        
        for user_id in user_ids:
            if user_id in self.active_connections:
                success = await self.send_personal_message(user_id, message)
                if not success:
                    disconnected_users.append(user_id)
                    
        # 연결이 끊긴 사용자 정리
        for user_id in disconnected_users:
            self.disconnect(user_id)
            
    def get_online_users(self) -> List[str]:
        """현재 온라인 사용자 목록"""
        return list(self.active_connections.keys())
        
    def is_online(self, user_id: str) -> bool:
        """사용자 온라인 여부 확인"""
        return user_id in self.active_connections
        
    async def ping_all(self):
        """모든 연결에 핑 전송 (연결 유지)"""
        ping_message = {
            'type': 'ping',
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.broadcast(ping_message)

class WebSocketManager:
    """WebSocket 기반 실시간 알림 관리"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self._ping_task = None
        
    async def start(self):
        """백그라운드 작업 시작"""
        # 주기적 핑 전송 (30초마다)
        self._ping_task = asyncio.create_task(self._periodic_ping())
        
    async def stop(self):
        """백그라운드 작업 중지"""
        if self._ping_task:
            self._ping_task.cancel()
            
    async def _periodic_ping(self):
        """주기적으로 핑 전송"""
        while True:
            try:
                await asyncio.sleep(30)
                await self.connection_manager.ping_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic ping: {str(e)}")
                
    async def handle_websocket(self, websocket: WebSocket, user_id: str):
        """WebSocket 연결 처리"""
        await self.connection_manager.connect(websocket, user_id)
        
        try:
            while True:
                # 클라이언트 메시지 수신
                data = await websocket.receive_json()
                
                # 메시지 타입별 처리
                if data.get('type') == 'pong':
                    # 핑에 대한 응답
                    self.connection_manager.connection_info[user_id]['last_ping'] = \
                        datetime.utcnow().isoformat()
                        
                elif data.get('type') == 'subscribe':
                    # 특정 이벤트 구독 (추후 구현)
                    await self.connection_manager.send_personal_message(
                        user_id,
                        {
                            'type': 'subscription',
                            'status': 'subscribed',
                            'channel': data.get('channel')
                        }
                    )
                    
                elif data.get('type') == 'ack':
                    # 알림 수신 확인
                    notification_id = data.get('notification_id')
                    logger.debug(f"User {user_id} acknowledged notification {notification_id}")
                    
        except WebSocketDisconnect:
            self.connection_manager.disconnect(user_id)
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {str(e)}")
            self.connection_manager.disconnect(user_id)
            
    async def send_notification(self, user_id: str, notification: Dict) -> bool:
        """특정 사용자에게 알림 전송"""
        message = {
            'type': 'notification',
            'data': notification,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return await self.connection_manager.send_personal_message(user_id, message)
        
    async def send_bulk_notifications(self, notifications: List[tuple]) -> Dict[str, bool]:
        """여러 사용자에게 알림 전송
        
        Args:
            notifications: (user_id, notification_data) 튜플 리스트
            
        Returns:
            user_id -> 전송 성공 여부 매핑
        """
        results = {}
        
        for user_id, notification_data in notifications:
            success = await self.send_notification(user_id, notification_data)
            results[user_id] = success
            
        return results
        
    def get_connection_stats(self) -> Dict:
        """연결 통계"""
        online_users = self.connection_manager.get_online_users()
        
        return {
            'online_users': len(online_users),
            'user_ids': online_users,
            'connection_info': self.connection_manager.connection_info
        }

# 전역 WebSocket 매니저 인스턴스
websocket_manager = WebSocketManager()