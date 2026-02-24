#!/usr/bin/env python3
"""
Website Uptime Monitor
Main entry point for the Telegram bot
"""

import asyncio
import logging
import sys
from telegram.ext import Application

import config
from src.database import DatabaseRepository
from src.bot import setup_handlers
from src.monitor import AlertManager, MonitorScheduler

logger = logging.getLogger(__name__)


async def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Starting Website Uptime Monitor")
    logger.info("=" * 60)
    
    # Initialize database
    db = DatabaseRepository()
    logger.info("Database initialized")
    
    # Create application with built-in updater
    application = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .build()
    )
    
    # Setup handlers
    setup_handlers(application, db)
    logger.info("Bot handlers registered")
    
    # Create alert manager
    alert_manager = AlertManager(application.bot, db)
    alert_manager.load_previous_statuses()
    
    # Create scheduler
    scheduler = MonitorScheduler(db, alert_manager)
    
    # Start scheduler in background
    scheduler_task = asyncio.create_task(scheduler.start())
    
    # Start polling - this blocks until interrupted
    await application.run_polling(
        poll_interval=1.0,
        timeout=10,
        drop_pending_updates=True,
        allowed_updates=['message']
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)
