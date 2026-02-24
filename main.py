#!/usr/bin/env python3
"""
Website Uptime Monitor
Main entry point for the Telegram bot
"""

import asyncio
import logging
import signal
import sys

import telegram.ext as tg
from telegram import Bot

import config
from src.database import DatabaseRepository
from src.bot import setup_handlers
from src.monitor import WebsiteChecker, AlertManager, MonitorScheduler

logger = logging.getLogger(__name__)


class UptimeMonitor:
    """Main application class"""
    
    def __init__(self):
        self.db = None
        self.scheduler = None
        self.application = None
        self.running = False
    
    async def start(self):
        """Start the application"""
        logger.info("=" * 60)
        logger.info("Starting Website Uptime Monitor")
        logger.info("=" * 60)
        
        # Initialize database
        self.db = DatabaseRepository()
        logger.info("Database initialized")
        
        # Create bot
        bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        
        # Create application
        self.application = tg.Application.builder().bot(bot).build()
        
        # Setup handlers
        setup_handlers(self.application, self.db)
        logger.info("Bot handlers registered")
        
        # Create alert manager
        alert_manager = AlertManager(bot, self.db)
        alert_manager.load_previous_statuses()
        
        # Create scheduler
        self.scheduler = MonitorScheduler(self.db, alert_manager)
        
        # Start scheduler in background
        scheduler_task = asyncio.create_task(self.scheduler.start())
        
        self.running = True
        
        # Start polling
        logger.info("Starting bot polling...")
        
        try:
            await self.application.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query']
            )
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown gracefully"""
        logger.info("Shutting down...")
        self.running = False
        
        # Stop scheduler
        if self.scheduler:
            await self.scheduler.stop()
        
        # Stop bot
        if self.application:
            await self.application.stop()
        
        logger.info("Shutdown complete")


async def main():
    """Main entry point"""
    app = UptimeMonitor()
    
    # Setup signal handlers
    loop = asyncio.get_running_loop()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(app.shutdown())
        )
    
    await app.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Exiting...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
