#!/usr/bin/env python3
"""
Website Uptime Monitor - Simple Bot
Uses httpx for Telegram API
"""

import asyncio
import logging
import sqlite3
from datetime import datetime
import httpx
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")

DB_PATH = "data/monitor.db"
CHECK_INTERVAL = 120

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (chat_id INTEGER PRIMARY KEY)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS websites (id INTEGER PRIMARY KEY, chat_id INTEGER, url TEXT, name TEXT, enabled INTEGER DEFAULT 1, last_status TEXT, last_checked TIMESTAMP)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, website_id INTEGER, status TEXT, response_time REAL, checked_at TIMESTAMP)''')
    conn.commit()
    conn.close()

class Bot:
    def __init__(self, token):
        self.token = token
        self.base = f"https://api.telegram.org/bot{token}"
        self.offset = None
    
    async def send(self, chat_id, text):
        logger.info(f"Sending message to {chat_id}")
        async with httpx.AsyncClient() as c:
            try:
                r = await c.post(f"{self.base}/sendMessage", data={'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'})
                logger.info(f"Send response: {r.status_code}")
            except Exception as e:
                logger.error(f"Send error: {e}")
    
    async def get_updates(self):
        async with httpx.AsyncClient() as c:
            params = {'timeout': 2}
            if self.offset:
                params['offset'] = self.offset
            try:
                r = await c.get(f"{self.base}/getUpdates", params=params, timeout=5)
                data = r.json()
                logger.info(f"getUpdates: {len(data.get('result', []))} results")
                if data.get('ok') and data.get('result'):
                    for u in data['result']:
                        self.offset = u['update_id'] + 1
                    return data['result']
            except Exception as e:
                logger.error(f"Get updates error: {e}")
        return []

async def check(url):
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as c:
            r = await c.head(url)
            return ('up', r.elapsed.total_seconds()) if 200 <= r.status_code < 300 else ('down', None)
    except Exception as e:
        return ('down', str(e))

async def handle(bot, update):
    msg = update.get('message', {})
    chat = msg.get('chat', {})
    text = msg.get('text', '')
    chat_id = chat.get('id')
    
    if not text or not chat_id:
        return
    
    parts = text.split()
    cmd = parts[0][1:].lower() if parts else ''
    args = parts[1:]
    
    conn = sqlite3.connect(DB_PATH)
    
    if cmd == 'start':
        conn.execute('INSERT OR IGNORE INTO users (chat_id) VALUES (?)', (chat_id,))
        conn.commit()
        reply = "👋 <b>Welcome!</b>\n\n/add url - Add website\n/list - Your sites\n/status - Check status\n/help - Help"
    
    elif cmd == 'help':
        reply = "📖 <b>Commands</b>\n\n/add url - Add website\n/remove url - Remove\n/list - All websites\n/status - Current status"
    
    elif cmd == 'add':
        url = args[0] if args else ''
        if not url:
            reply = "❌ Usage: /add https://example.com"
        else:
            url = url if url.startswith('http') else 'https://' + url
            conn.execute('INSERT OR IGNORE INTO users (chat_id) VALUES (?)', (chat_id,))
            conn.execute('INSERT OR IGNORE INTO websites (chat_id, url, name) VALUES (?, ?, ?)', (chat_id, url, url))
            conn.commit()
            reply = f"✅ Added: {url}"
    
    elif cmd == 'list':
        cur = conn.execute('SELECT url, last_status FROM websites WHERE chat_id = ?', (chat_id,))
        rows = cur.fetchall()
        reply = "<b>Your Sites</b>\n\n" + "\n".join(f"{'🟢' if s=='up' else '🔴' if s=='down' else '⚪'} {u}" for u,s in rows) if rows else "No sites yet"
    
    elif cmd == 'status':
        cur = conn.execute('SELECT url, last_status FROM websites WHERE chat_id = ?', (chat_id,))
        rows = cur.fetchall()
        reply = "<b>Status</b>\n\n" + "\n".join(f"{'🟢' if s=='up' else '🔴' if s=='down' else '⚪'} {u}" for u,s in rows) if rows else "No sites"
    
    else:
        reply = "❓ Unknown. Try /help"
    
    conn.close()
    await bot.send(chat_id, reply)

async def monitor(bot):
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.execute('SELECT id, chat_id, url FROM websites WHERE enabled = 1')
            sites = cur.fetchall()
            conn.close()
            
            for sid, cid, url in sites:
                status, resp = await check(url)
                conn = sqlite3.connect(DB_PATH)
                conn.execute('INSERT INTO history (website_id, status, response_time, checked_at) VALUES (?, ?, ?, ?)',
                           (sid, status, resp if isinstance(resp, float) else None, datetime.now().isoformat()))
                conn.execute('UPDATE websites SET last_status = ?, last_checked = ? WHERE id = ?',
                           (status, datetime.now().isoformat(), sid))
                conn.commit()
                conn.close()
                logger.info(f"Checked {url}: {status}")
            
            await asyncio.sleep(CHECK_INTERVAL)
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            await asyncio.sleep(10)

async def main():
    init_db()
    bot = Bot(BOT_TOKEN)
    asyncio.create_task(monitor(bot))
    
    while True:
        try:
            updates = await bot.get_updates()
            for u in updates:
                await handle(bot, u)
        except Exception as e:
            logger.error(f"Poll error: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
