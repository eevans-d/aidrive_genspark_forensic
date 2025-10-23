"""
Notification Service - Email, SMS, WebSocket real-time notifications
SEMANA 2.1 Implementation
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import sqlite3

# Configure logging with request_id support
logger = logging.getLogger("notification_service")


class NotificationType(str, Enum):
    """Tipos de notificación soportados"""
    STOCK_ALERT = "stock_alert"
    ORDER_PENDING = "order_pending"
    ORDER_READY = "order_ready"
    SYSTEM_ALERT = "system_alert"
    PRICE_CHANGE = "price_change"
    INVENTORY_LOW = "inventory_low"


class NotificationChannel(str, Enum):
    """Canales de entrega de notificaciones"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationPriority(str, Enum):
    """Prioridad de notificaciones"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationService:
    """
    Servicio centralizado de notificaciones
    - Email delivery via SMTP
    - SMS delivery via Twilio (simulated)
    - In-app notifications en base de datos
    - WebSocket push real-time
    """

    def __init__(self, db_path: str = None):
        """
        Inicializa el servicio de notificaciones

        Args:
            db_path: Ruta a base de datos SQLite
        """
        self.db_path = db_path or os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "agente_negocio",
            "minimarket_inventory.db"
        )
        self.email_config = {
            "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "sender_email": os.getenv("NOTIFICATION_EMAIL", "noreply@minimarket.local"),
            "sender_password": os.getenv("NOTIFICATION_EMAIL_PASSWORD", "dummy_password"),
        }
        self.sms_config = {
            "account_sid": os.getenv("TWILIO_ACCOUNT_SID", "dummy_sid"),
            "auth_token": os.getenv("TWILIO_AUTH_TOKEN", "dummy_token"),
            "from_number": os.getenv("TWILIO_FROM_NUMBER", "+1234567890"),
        }
        self._init_db()
        logger.info("✅ Notification Service initialized")

    def _init_db(self):
        """Inicializa tabla de notificaciones en base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Crear tabla de notificaciones si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    notification_type VARCHAR(50),
                    channel VARCHAR(50),
                    priority VARCHAR(20),
                    subject VARCHAR(255),
                    message TEXT,
                    data JSON,
                    read BOOLEAN DEFAULT 0,
                    sent_at TIMESTAMP,
                    read_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES usuarios(id)
                )
            """)

            # Crear tabla de preferencias de notificación
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notification_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    email_enabled BOOLEAN DEFAULT 1,
                    sms_enabled BOOLEAN DEFAULT 1,
                    push_enabled BOOLEAN DEFAULT 1,
                    stock_alerts BOOLEAN DEFAULT 1,
                    order_alerts BOOLEAN DEFAULT 1,
                    system_alerts BOOLEAN DEFAULT 1,
                    quiet_hours_start TIME,
                    quiet_hours_end TIME,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES usuarios(id)
                )
            """)

            # Crear índices para performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at)"
            )

            conn.commit()
            conn.close()
            logger.info("✅ Database initialized with notification tables")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {str(e)}")

    async def send_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        subject: str,
        message: str,
        channels: List[NotificationChannel] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Dict = None,
        request_id: str = "unknown"
    ) -> Dict:
        """
        Envía una notificación por múltiples canales

        Args:
            user_id: ID del usuario
            notification_type: Tipo de notificación
            subject: Asunto
            message: Cuerpo del mensaje
            channels: Lista de canales (por defecto: in-app)
            priority: Prioridad
            data: Datos adicionales JSON
            request_id: ID de request para tracking

        Returns:
            {"success": bool, "notification_id": int, "channels_sent": list, "errors": list}
        """
        channels = channels or [NotificationChannel.IN_APP]
        result = {
            "success": True,
            "notification_id": None,
            "channels_sent": [],
            "errors": []
        }

        try:
            # Guardar en base de datos
            notification_id = await self._save_notification(
                user_id, notification_type, subject, message, priority, data
            )
            result["notification_id"] = notification_id

            logger.info(
                f"📨 Notification queued | user_id={user_id} | "
                f"type={notification_type} | channels={[ch.value for ch in channels]} | "
                f"request_id={request_id}"
            )

            # Enviar por cada canal
            for channel in channels:
                try:
                    if channel == NotificationChannel.EMAIL:
                        await self.send_email(user_id, subject, message, request_id)
                        result["channels_sent"].append("email")
                    elif channel == NotificationChannel.SMS:
                        await self.send_sms(user_id, message, request_id)
                        result["channels_sent"].append("sms")
                    elif channel == NotificationChannel.PUSH:
                        await self.send_push(user_id, subject, message, request_id)
                        result["channels_sent"].append("push")
                    elif channel == NotificationChannel.IN_APP:
                        # Ya guardada en DB
                        result["channels_sent"].append("in_app")
                except Exception as e:
                    error_msg = f"Failed to send {channel.value}: {str(e)}"
                    result["errors"].append(error_msg)
                    logger.error(error_msg)

            # Broadcast via WebSocket si hay conexiones activas
            try:
                # Lazy import para evitar circular dependencies
                from services.websocket_manager import get_websocket_manager
                
                manager = get_websocket_manager()
                notification_data = {
                    "id": notification_id,
                    "type": notification_type.value,
                    "subject": subject,
                    "message": message,
                    "priority": priority.value,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                broadcast_result = await manager.broadcast_notification(
                    user_id,
                    notification_data
                )
                
                if broadcast_result["sent"] > 0:
                    result["channels_sent"].append("websocket")
                    logger.info(
                        f"📡 WebSocket broadcast successful",
                        extra={
                            "request_id": request_id,
                            "user_id": user_id,
                            "notification_id": notification_id,
                            "sent": broadcast_result["sent"]
                        }
                    )
            except Exception as e:
                # WebSocket broadcasting es opcional, no fallar si no funciona
                logger.warning(
                    f"⚠️ WebSocket broadcast failed",
                    extra={
                        "request_id": request_id,
                        "user_id": user_id,
                        "error": str(e)
                    }
                )

            return result

        except Exception as e:
            result["success"] = False
            result["errors"].append(str(e))
            logger.error(f"❌ Notification send failed: {str(e)} | request_id={request_id}")
            return result

    async def _save_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        subject: str,
        message: str,
        priority: NotificationPriority,
        data: Dict = None
    ) -> int:
        """Guarda notificación en base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            data_json = json.dumps(data or {})
            cursor.execute("""
                INSERT INTO notifications 
                (user_id, notification_type, channel, priority, subject, message, data, sent_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, notification_type.value, NotificationChannel.IN_APP.value, 
                  priority.value, subject, message, data_json))

            conn.commit()
            notification_id = cursor.lastrowid
            conn.close()

            return notification_id
        except Exception as e:
            logger.error(f"❌ Failed to save notification: {str(e)}")
            raise

    async def send_email(
        self,
        user_id: int,
        subject: str,
        message: str,
        request_id: str = "unknown"
    ) -> bool:
        """
        Envía email (SMTP)
        En desarrollo: simula envío
        """
        try:
            # Get user email from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM usuarios WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            conn.close()

            if not user:
                logger.warning(f"⚠️ User {user_id} not found for email delivery")
                return False

            recipient_email = user[0]

            # En producción, esto enviaría un email real
            logger.info(
                f"📧 Email simulated | to={recipient_email} | subject={subject} | "
                f"request_id={request_id}"
            )

            # Simulación de envío exitoso
            return True

        except Exception as e:
            logger.error(f"❌ Email send failed: {str(e)}")
            return False

    async def send_sms(
        self,
        user_id: int,
        message: str,
        request_id: str = "unknown"
    ) -> bool:
        """
        Envía SMS (Twilio)
        En desarrollo: simula envío
        """
        try:
            # Get user phone from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT phone FROM usuarios WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            conn.close()

            if not user or not user[0]:
                logger.warning(f"⚠️ User {user_id} has no phone for SMS delivery")
                return False

            phone = user[0]
            logger.info(
                f"📱 SMS simulated | to={phone} | message_len={len(message)} | "
                f"request_id={request_id}"
            )

            # Simulación de envío exitoso
            return True

        except Exception as e:
            logger.error(f"❌ SMS send failed: {str(e)}")
            return False

    async def send_push(
        self,
        user_id: int,
        subject: str,
        message: str,
        request_id: str = "unknown"
    ) -> bool:
        """Envía push notification vía WebSocket (será manejado por WebSocketManager)"""
        try:
            logger.info(
                f"🔔 Push notification queued | user_id={user_id} | "
                f"subject={subject} | request_id={request_id}"
            )
            return True
        except Exception as e:
            logger.error(f"❌ Push notification failed: {str(e)}")
            return False

    async def get_user_notifications(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False
    ) -> List[Dict]:
        """
        Obtiene notificaciones del usuario

        Args:
            user_id: ID del usuario
            limit: Límite de resultados
            offset: Offset para paginación
            unread_only: Si True, solo no leídas

        Returns:
            Lista de notificaciones
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM notifications WHERE user_id = ?"
            params = [user_id]

            if unread_only:
                query += " AND read = 0"

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            notifications = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return notifications

        except Exception as e:
            logger.error(f"❌ Failed to get notifications: {str(e)}")
            return []

    async def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Marca notificación como leída"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE notifications 
                SET read = 1, read_at = CURRENT_TIMESTAMP 
                WHERE id = ? AND user_id = ?
            """, (notification_id, user_id))

            conn.commit()
            success = cursor.rowcount > 0
            conn.close()

            return success

        except Exception as e:
            logger.error(f"❌ Failed to mark notification as read: {str(e)}")
            return False

    async def get_unread_count(self, user_id: int) -> int:
        """Obtiene cantidad de notificaciones no leídas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read = 0", 
                         (user_id,))
            count = cursor.fetchone()[0]
            conn.close()

            return count

        except Exception as e:
            logger.error(f"❌ Failed to get unread count: {str(e)}")
            return 0

    async def set_preferences(
        self,
        user_id: int,
        preferences: Dict
    ) -> bool:
        """
        Actualiza preferencias de notificación del usuario

        Args:
            user_id: ID del usuario
            preferences: Dict con preferencias (email_enabled, sms_enabled, etc.)

        Returns:
            True si se actualizó exitosamente
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if preferences exist
            cursor.execute("SELECT id FROM notification_preferences WHERE user_id = ?", (user_id,))
            exists = cursor.fetchone()

            if exists:
                # Update
                updates = []
                params = []
                for key, value in preferences.items():
                    updates.append(f"{key} = ?")
                    params.append(value)
                params.append(user_id)

                query = f"UPDATE notification_preferences SET {', '.join(updates)} WHERE user_id = ?"
                cursor.execute(query, params)
            else:
                # Insert
                keys = ", ".join(preferences.keys())
                placeholders = ", ".join(["?"] * len(preferences))
                query = f"INSERT INTO notification_preferences (user_id, {keys}) VALUES (?, {placeholders})"
                cursor.execute(query, [user_id] + list(preferences.values()))

            conn.commit()
            conn.close()
            logger.info(f"✅ Preferences updated for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to set preferences: {str(e)}")
            return False

    async def get_preferences(self, user_id: int) -> Dict:
        """Obtiene preferencias de notificación del usuario"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM notification_preferences WHERE user_id = ?", (user_id,))
            prefs = cursor.fetchone()
            conn.close()

            if prefs:
                return dict(prefs)

            # Return defaults if not set
            return {
                "user_id": user_id,
                "email_enabled": True,
                "sms_enabled": True,
                "push_enabled": True,
                "stock_alerts": True,
                "order_alerts": True,
                "system_alerts": True,
            }

        except Exception as e:
            logger.error(f"❌ Failed to get preferences: {str(e)}")
            return {}


# Global notification service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Factory function para obtener instancia de NotificationService"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
