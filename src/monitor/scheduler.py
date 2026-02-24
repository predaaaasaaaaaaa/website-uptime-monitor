# src/monitor/scheduler.py
import asyncio
import logging
from datetime import datetime

import config
from src.database import DatabaseRepository, Website
from .checker import WebsiteChecker
from .alerts import AlertManager

logger = logging.getLogger(__name__)


class MonitorScheduler:
    """Scheduler for periodic website checks"""
    
    def __init__(self, db: DatabaseRepository, alert_manager: AlertManager):
        self.db = db
        self.alert_manager = alert_manager
        self.checker = WebsiteChecker()
        self.running = False
        self.check_interval = config.CHECK_INTERVAL_MINUTES * 60  # Convert to seconds
    
    async def start(self):
        """Start the monitoring scheduler"""
        self.running = True
        logger.info(f"Monitor scheduler started (interval: {config.CHECK_INTERVAL_MINUTES} minutes)")
        
        # Initial check
        await self.check_all_websites()
        
        # Schedule periodic checks
        while self.running:
            try:
                await asyncio.sleep(self.check_interval)
                if self.running:
                    await self.check_all_websites()
            except asyncio.CancelledError:
                logger.info("Scheduler cancelled")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}", exc_info=True)
                await asyncio.sleep(10)  # Brief pause on error
    
    async def stop(self):
        """Stop the monitoring scheduler"""
        self.running = False
        await self.checker.close()
        logger.info("Monitor scheduler stopped")
    
    async def check_all_websites(self):
        """Check all enabled websites"""
        try:
            websites = self.db.get_all_websites()
            if not websites:
                logger.debug("No websites to check")
                return
            
            logger.info(f"Checking {len(websites)} websites...")
            
            # Check all websites concurrently
            tasks = [self.check_website(website) for website in websites]
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error checking websites: {e}", exc_info=True)
    
    async def check_website(self, website: Website):
        """Check a single website"""
        try:
            result = await self.checker.check(website)
            
            # Add to history
            self.db.add_history(
                website_id=website.id,
                status=result.status,
                response_time=result.response_time,
                error_message=result.error_message
            )
            
            # Update website status
            self.db.update_website_status(website.id, result.status)
            
            # Send alert if needed
            await self.alert_manager.send_alert(website, result)
            
        except Exception as e:
            logger.error(f"Error checking {website.url}: {e}", exc_info=True)
