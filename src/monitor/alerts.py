# src/monitor/alerts.py
import logging
from typing import Dict

import telegram as tg
from telegram import Bot

import config
from src.database import Website, DatabaseRepository

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages alert notifications"""
    
    def __init__(self, bot: Bot, db: DatabaseRepository):
        self.bot = bot
        self.db = db
        # Track last alert status to avoid spam
        self.last_alert_status: Dict[int, str] = {}
    
    async def send_alert(self, website: Website, result) -> bool:
        """Send alert if status changed"""
        previous_status = self.last_alert_status.get(website.id)
        current_status = result.status
        
        # Only alert on status change
        if previous_status == current_status:
            logger.debug(f"No status change for {website.url}, skipping alert")
            return False
        
        # Update last status
        self.last_alert_status[website.id] = current_status
        
        # Prepare message
        if current_status == 'down':
            message = self._build_down_message(website, result)
        else:
            message = self._build_up_message(website, result)
        
        try:
            await self.bot.send_message(
                chat_id=website.chat_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info(f"Alert sent to {website.chat_id} for {website.url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False
    
    def _build_down_message(self, website: Website, result) -> str:
        """Build down alert message"""
        emoji = "🔴"
        message = f"{emoji} <b>Website Down!</b>\n\n"
        message += f"🌐 <b>URL:</b> {website.url}\n"
        
        if result.error_message:
            message += f"⚠️ <b>Error:</b> {result.error_message}\n"
        
        message += f"⏰ <b>Time:</b> {result.checked_at.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
    
    def _build_up_message(self, website: Website, result) -> str:
        """Build up recovery message"""
        emoji = "🟢"
        message = f"{emoji} <b>Website Recovered!</b>\n\n"
        message += f"🌐 <b>URL:</b> {website.url}\n"
        
        if result.response_time:
            message += f"⏱️ <b>Response Time:</b> {result.response_time:.2f}s\n"
        
        message += f"⏰ <b>Time:</b> {result.checked_at.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
    
    def load_previous_statuses(self):
        """Load last known statuses from database"""
        try:
            websites = self.db.get_all_websites()
            for website in websites:
                last_status = self.db.get_website_last_status(website.id)
                if last_status:
                    self.last_alert_status[website.id] = last_status
            logger.info(f"Loaded {len(self.last_alert_status)} previous statuses")
        except Exception as e:
            logger.error(f"Failed to load previous statuses: {e}")
