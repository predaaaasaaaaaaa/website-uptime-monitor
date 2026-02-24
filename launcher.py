#!/usr/bin/env python3
"""
Website Uptime Monitor - Launcher
Spawns bot in separate process to avoid event loop issues
"""

import subprocess
import sys
import os
import signal

BOT_SCRIPT = '''#!/usr/bin/env python3
import asyncio
import logging
import sys
import os

# Add project to path
script_dir = os.path.dirname(os.path.abspath("__file__"))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

from telegram.ext import Application
import config
from src.database import DatabaseRepository
from src.bot import setup_handlers
from src.monitor import AlertManager, MonitorScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting bot...")
    db = DatabaseRepository()
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    setup_handlers(app, db)
    
    alert_mgr = AlertManager(app.bot, db)
    alert_mgr.load_previous_statuses()
    sched = MonitorScheduler(db, alert_mgr)
    
    asyncio.create_task(sched.start())
    
    logger.info("Bot ready, starting polling...")
    await app.run_polling(
        poll_interval=1.0,
        drop_pending_updates=True,
        allowed_updates=["message"]
    )

if __name__ == "__main__":
    asyncio.run(main())
'''

def main():
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__)) or '.'
    
    # Write temp bot script
    bot_path = os.path.join(script_dir, '_bot_run.py')
    with open(bot_path, 'w') as f:
        f.write(BOT_SCRIPT)
    
    # Start subprocess
    print("Starting bot in subprocess...")
    proc = subprocess.Popen(
        [sys.executable, bot_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=script_dir,
        preexec_fn=os.setsid
    )
    
    print(f"Bot started with PID: {proc.pid}")
    
    # Handle shutdown
    def shutdown(signum, frame):
        print("Shutting down...")
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except:
            pass
        proc.wait()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    
    # Stream output
    try:
        for line in proc.stdout:
            print(line.decode(), end='')
    except KeyboardInterrupt:
        shutdown(None, None)

if __name__ == "__main__":
    main()
