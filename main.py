#!/usr/bin/env python3
"""
Website Uptime Monitor
Main entry point for the Telegram bot
"""

import asyncio
import logging
import signal
import sys
import os

from telegram.ext import Application

import config
from src.database import DatabaseRepository
from src.bot import setup_handlers
from src.monitor import WebsiteChecker, AlertManager, MonitorScheduler

logger = logging.getLogger(__name__)


async def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Starting Website Uptime Monitor")
    logger.info("=" * 60)
    
    # Initialize database
    db = DatabaseRepository()
    logger.info("Database initialized")
    
    # Create application
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Setup handlers
    setup_handlers(application, db)
    logger.info("Bot handlers registered")
    
    # Create alert manager
    alert_manager = AlertManager(application.bot, db)
    alert_manager.load_previous_statuses()
    
    # Create scheduler
    scheduler = MonitorScheduler(db, alert_manager)
    
    # Initialize and start
    await application.initialize()
    await application.start()
    
    # Start scheduler in background
    scheduler_task = asyncio.create_task(scheduler.start())
    
    logger.info("Bot ready! Press Ctrl+C to stop.")
    
    try:
        # Run until interrupted
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Shutting down...")
    finally:
        # Stop scheduler
        scheduler.running = False
        await scheduler.stop()
        
        # Stop application
        try:
            await application.stop()
            await application.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        logger.info("Shutdown complete")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Setup signal handlers
    def signal_handler(sig):
        logger.info(f"Received signal {sig}")
        loop.stop()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, signal_handler)
        except (OSError, ValueError):
            pass
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Interrupted")
    finally:
        loop.close()
