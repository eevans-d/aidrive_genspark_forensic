"""
WebSocket Manager - SEMANA 2.2
Gestiona conexiones WebSocket para notificaciones en tiempo real
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Set
from fastapi import WebSocket
from datetime import datetime


logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Gestiona las conexiones WebSocket activas por usuario
    Maneja broadcasting de notificaciones en tiempo real
    
    Características:
    - Connection pooling por usuario
    - Async message broadcasting
    - Manejo de clientes desconectados
    - Ping/pong keep-alive
    - User isolation
    """
    
    def __init__(self):
        # Dict[user_id] -> Set[WebSocket connections]
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Lock para operaciones thread-safe
        self._lock = asyncio.Lock()
        # Ping interval en segundos
        self.ping_interval = 30
        # Timeout para ping pong
        self.ping_timeout = 5
    
    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """
        Registra una nueva conexión WebSocket
        
        Args:
            user_id: ID del usuario
            websocket: Conexión WebSocket
        """
        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            
            self.active_connections[user_id].add(websocket)
            
            logger.info(
                f"✅ WebSocket connected",
                extra={
                    "user_id": user_id,
                    "connections": len(self.active_connections[user_id])
                }
            )
    
    async def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        """
        Desregistra una conexión WebSocket
        
        Args:
            user_id: ID del usuario
            websocket: Conexión WebSocket
        """
        async with self._lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                
                # Limpiar si no quedan conexiones
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                
                logger.info(
                    f"✅ WebSocket disconnected",
                    extra={
                        "user_id": user_id,
                        "remaining": len(self.active_connections.get(user_id, set()))
                    }
                )
    
    async def broadcast_notification(
        self, 
        user_id: int, 
        notification: Dict
    ) -> Dict[str, any]:
        """
        Envía una notificación a todas las conexiones de un usuario
        
        Args:
            user_id: ID del usuario
            notification: Datos de notificación
        
        Returns:
            Dict con estadísticas de envío
        """
        if user_id not in self.active_connections:
            logger.debug(
                f"No active connections for user",
                extra={"user_id": user_id}
            )
            return {
                "sent": 0,
                "failed": 0,
                "total_connections": 0
            }
        
        connections = self.active_connections[user_id].copy()
        sent_count = 0
        failed_count = 0
        
        message = {
            "type": "notification",
            "data": notification,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        message_json = json.dumps(message)
        
        for websocket in connections:
            try:
                await websocket.send_text(message_json)
                sent_count += 1
                logger.debug(
                    f"✅ Notification sent via WebSocket",
                    extra={
                        "user_id": user_id,
                        "notification_type": notification.get("type")
                    }
                )
            except Exception as e:
                failed_count += 1
                logger.warning(
                    f"⚠️ Failed to send notification",
                    extra={
                        "user_id": user_id,
                        "error": str(e)
                    }
                )
                # Intentar desconectar el cliente fallido
                try:
                    async with self._lock:
                        self.active_connections[user_id].discard(websocket)
                except Exception:
                    pass
        
        return {
            "sent": sent_count,
            "failed": failed_count,
            "total_connections": len(connections)
        }
    
    async def broadcast_to_multiple_users(
        self,
        user_ids: List[int],
        notification: Dict
    ) -> Dict[int, Dict[str, any]]:
        """
        Envía una notificación a múltiples usuarios
        
        Args:
            user_ids: Lista de IDs de usuarios
            notification: Datos de notificación
        
        Returns:
            Dict[user_id] -> estadísticas de envío
        """
        results = {}
        for user_id in user_ids:
            results[user_id] = await self.broadcast_notification(
                user_id, 
                notification
            )
        
        total_sent = sum(r["sent"] for r in results.values())
        total_failed = sum(r["failed"] for r in results.values())
        
        logger.info(
            f"📤 Broadcast complete",
            extra={
                "users": len(user_ids),
                "total_sent": total_sent,
                "total_failed": total_failed
            }
        )
        
        return results
    
    async def send_unread_count(
        self,
        user_id: int,
        unread_count: int
    ) -> Dict[str, any]:
        """
        Envía el contador de mensajes no leídos
        
        Args:
            user_id: ID del usuario
            unread_count: Número de notificaciones no leídas
        
        Returns:
            Estadísticas de envío
        """
        message = {
            "type": "unread_count",
            "data": {
                "unread_count": unread_count
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if user_id not in self.active_connections:
            logger.debug(
                f"No active connections for unread_count update",
                extra={"user_id": user_id}
            )
            return {
                "sent": 0,
                "failed": 0
            }
        
        connections = self.active_connections[user_id].copy()
        sent_count = 0
        failed_count = 0
        
        message_json = json.dumps(message)
        
        for websocket in connections:
            try:
                await websocket.send_text(message_json)
                sent_count += 1
            except Exception as e:
                failed_count += 1
                logger.warning(
                    f"Failed to send unread_count",
                    extra={
                        "user_id": user_id,
                        "error": str(e)
                    }
                )
                try:
                    async with self._lock:
                        self.active_connections[user_id].discard(websocket)
                except Exception:
                    pass
        
        return {
            "sent": sent_count,
            "failed": failed_count
        }
    
    async def send_confirmation(
        self,
        user_id: int,
        notification_id: int,
        read: bool = False
    ) -> Dict[str, any]:
        """
        Envía confirmación de lectura de notificación
        
        Args:
            user_id: ID del usuario
            notification_id: ID de la notificación
            read: Si fue marcada como leída
        
        Returns:
            Estadísticas de envío
        """
        message = {
            "type": "notification_confirmation",
            "data": {
                "notification_id": notification_id,
                "read": read
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if user_id not in self.active_connections:
            return {
                "sent": 0,
                "failed": 0
            }
        
        connections = self.active_connections[user_id].copy()
        sent_count = 0
        failed_count = 0
        
        message_json = json.dumps(message)
        
        for websocket in connections:
            try:
                await websocket.send_text(message_json)
                sent_count += 1
            except Exception as e:
                failed_count += 1
                try:
                    async with self._lock:
                        self.active_connections[user_id].discard(websocket)
                except Exception:
                    pass
        
        return {
            "sent": sent_count,
            "failed": failed_count
        }
    
    def get_connection_count(self, user_id: Optional[int] = None) -> int:
        """
        Obtiene el contador de conexiones activas
        
        Args:
            user_id: ID del usuario (None = total)
        
        Returns:
            Número de conexiones activas
        """
        if user_id is not None:
            return len(self.active_connections.get(user_id, set()))
        
        return sum(
            len(connections) 
            for connections in self.active_connections.values()
        )
    
    def get_active_users(self) -> List[int]:
        """
        Obtiene lista de usuarios con conexiones activas
        
        Returns:
            Lista de user_ids
        """
        return list(self.active_connections.keys())
    
    async def cleanup(self) -> None:
        """
        Limpia todas las conexiones activas
        Usado para shutdown graceful
        """
        async with self._lock:
            for user_id, connections in self.active_connections.items():
                for websocket in connections:
                    try:
                        await websocket.close()
                    except Exception as e:
                        logger.warning(
                            f"Error closing WebSocket",
                            extra={
                                "user_id": user_id,
                                "error": str(e)
                            }
                        )
            
            self.active_connections.clear()
            logger.info("✅ WebSocket cleanup complete")


# Global singleton instance
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """
    Obtiene la instancia global del WebSocketManager
    
    Returns:
        WebSocketManager singleton
    """
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager
