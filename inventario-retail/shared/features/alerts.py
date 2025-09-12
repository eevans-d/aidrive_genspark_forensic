"""
Sistema de alertas Telegram en español
"""
import asyncio
from telegram import Bot
from shared.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class TelegramAlerter:
    def __init__(self):
        self.bot = None
        if settings.is_alertas_enabled():
            try:
                self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
                logger.info("✅ Bot Telegram inicializado")
            except Exception as e:
                logger.error(f"Error inicializando bot Telegram: {e}")

    async def send_alert(self, message: str, level: str = "info"):
        """Enviar alerta por Telegram"""
        if not self.bot:
            return

        try:
            # Formatear mensaje según nivel
            emoji_map = {
                "info": "ℹ️",
                "warning": "⚠️", 
                "error": "❌",
                "critical": "🚨"
            }

            formatted_msg = f"{emoji_map.get(level, 'ℹ️')} **{level.upper()}**\n{message}"

            await self.bot.send_message(
                chat_id=settings.TELEGRAM_CHAT_ID,
                text=formatted_msg,
                parse_mode="Markdown"
            )

            logger.info(f"Alerta Telegram enviada: {level}")

        except Exception as e:
            logger.error(f"Error enviando alerta Telegram: {e}")

    async def alert_stock_critico(self, productos_criticos: list):
        """Alerta por stock crítico"""
        if not productos_criticos:
            return

        message = f"🏪 **STOCK CRÍTICO DETECTADO**\n\n"
        for producto in productos_criticos[:5]:  # Máximo 5 productos
            message += f"• {producto['codigo']}: {producto['stock_actual']} unidades\n"

        if len(productos_criticos) > 5:
            message += f"\n... y {len(productos_criticos) - 5} productos más"

        await self.send_alert(message, "warning")

    async def alert_inflacion_alta(self):
        """Alerta por inflación alta"""
        if settings.INFLACION_MENSUAL > 15:
            message = f"📈 **INFLACIÓN ALTA DETECTADA**\n\nInflación actual: {settings.INFLACION_MENSUAL}% mensual\nRevisar precios urgentemente."
            await self.send_alert(message, "critical")
