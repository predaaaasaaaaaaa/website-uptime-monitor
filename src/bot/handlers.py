# src/bot/handlers.py
import logging
import re
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

import config
from src.database import DatabaseRepository
from src.bot.keyboard import get_main_keyboard

logger = logging.getLogger(__name__)


def setup_handlers(application, db: DatabaseRepository):
    """Setup bot command handlers"""
    
    # Register command handlers
    application.add_handler(
        telegram.CommandHandler("start", start_command)
    )
    application.add_handler(
        telegram.CommandHandler("help", help_command)
    )
    application.add_handler(
        telegram.CommandHandler("add", add_command)
    )
    application.add_handler(
        telegram.CommandHandler("remove", remove_command)
    )
    application.add_handler(
        telegram.CommandHandler("list", list_command)
    )
    application.add_handler(
        telegram.CommandHandler("status", status_command)
    )
    application.add_handler(
        telegram.CommandHandler("history", history_command)
    )
    
    # Store db in context
    application.bot_data['db'] = db


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    chat_id = update.effective_chat.id
    
    welcome_message = """
👋 <b>Welcome to Website Uptime Monitor!</b>

I'll help you monitor your websites and alert you when they go down.

<b>Commands:</b>
/add &lt;url&gt; - Add website to monitor
/remove &lt;url&gt; - Remove website from monitoring
/list - List all monitored websites
/status - Show status of all websites
/history &lt;url&gt; - Show uptime history
/help - Show this help message

<b>How it works:</b>
• I check your websites every 2 minutes
• You'll get instant alerts when sites go down
• You'll be notified when they recover

Let's get started! 🚀
"""
    await update.message.reply_text(
        welcome_message,
        parse_mode='HTML',
        reply_markup=get_main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_message = """
📖 <b>Help</b>

<b>Commands:</b>

/add &lt;url&gt; - Add a website to monitor
Example: /add https://example.com

/remove &lt;url&gt; - Remove a website from monitoring
Example: /remove https://example.com

/list - Show all your monitored websites

/status - Show current status of all websites

/history &lt;url&gt; - Show uptime history for a website

<b>Features:</b>
• Checks every 2 minutes
• Alerts on status change only
• Stores 100 history entries per website

Need help? Just ask! 😊
"""
    await update.message.reply_text(
        help_message,
        parse_mode='HTML'
    )


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add command"""
    chat_id = update.effective_chat.id
    
    # Get URL from command args
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a URL to monitor.\n"
            "Example: /add https://example.com"
        )
        return
    
    url = context.args[0]
    
    # Validate URL
    if not is_valid_url(url):
        await update.message.reply_text(
            "❌ Invalid URL. Please provide a valid URL starting with http:// or https://"
        )
        return
    
    # Add to database
    db = context.bot_data['db']
    website = db.add_website(chat_id, url)
    
    await update.message.reply_text(
        f"✅ <b>Website Added!</b>\n\n"
        f"🌐 {url}\n\n"
        f"I'll start monitoring it immediately.",
        parse_mode='HTML'
    )


async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /remove command"""
    chat_id = update.effective_chat.id
    
    # Get URL from command args
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a URL to remove.\n"
            "Example: /remove https://example.com"
        )
        return
    
    url = context.args[0]
    
    # Remove from database
    db = context.bot_data['db']
    removed = db.remove_website(chat_id, url)
    
    if removed:
        await update.message.reply_text(
            f"✅ <b>Website Removed!</b>\n\n"
            f"🌐 {url}\n\n"
            f"It's no longer being monitored.",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            f"❌ Website not found.\n\n"
            f"🌐 {url}\n\n"
            f"You're not monitoring this website.",
            parse_mode='HTML'
        )


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list command"""
    chat_id = update.effective_chat.id
    
    db = context.bot_data['db']
    websites = db.get_user_websites(chat_id)
    
    if not websites:
        await update.message.reply_text(
            "📭 <b>No websites monitored</b>\n\n"
            "Use /add &lt;url&gt; to add a website.",
            parse_mode='HTML'
        )
        return
    
    message = "<b>📋 Your Monitored Websites</b>\n\n"
    
    for i, website in enumerate(websites, 1):
        status_emoji = "🟢" if website.last_status == "up" else "🔴" if website.last_status == "down" else "⚪"
        message += f"{i}. {status_emoji} {website.url}\n"
        if website.last_checked:
            message += f"   Last checked: {website.last_checked.strftime('%H:%M:%S')}\n"
        message += "\n"
    
    await update.message.reply_text(message, parse_mode='HTML')


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    chat_id = update.effective_chat.id
    
    db = context.bot_data['db']
    websites = db.get_user_websites(chat_id)
    
    if not websites:
        await update.message.reply_text(
            "📭 <b>No websites monitored</b>\n\n"
            "Use /add &lt;url&gt; to add a website.",
            parse_mode='HTML'
        )
        return
    
    message = "<b>📊 Website Status</b>\n\n"
    
    up_count = 0
    down_count = 0
    
    for website in websites:
        if website.last_status == "up":
            up_count += 1
            emoji = "🟢"
        elif website.last_status == "down":
            down_count += 1
            emoji = "🔴"
        else:
            emoji = "⚪"
        
        message += f"{emoji} <b>{website.url}</b>\n"
        
        if website.last_status:
            status_text = "UP" if website.last_status == "up" else "DOWN"
            message += f"   Status: {status_text}\n"
        
        if website.last_checked:
            message += f"   Last: {website.last_checked.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        message += "\n"
    
    message += f"<b>Summary:</b> {up_count} up, {down_count} down"
    
    await update.message.reply_text(message, parse_mode='HTML')


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /history command"""
    chat_id = update.effective_chat.id
    
    # Get URL from command args
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a URL.\n"
            "Example: /history https://example.com"
        )
        return
    
    url = context.args[0]
    
    db = context.bot_data['db']
    website = db.get_website_by_url(chat_id, url)
    
    if not website:
        await update.message.reply_text(
            f"❌ Website not found.\n\n"
            f"🌐 {url}\n\n"
            f"You're not monitoring this website.",
            parse_mode='HTML'
        )
        return
    
    history = db.get_website_history(website.id, limit=20)
    
    if not history:
        await update.message.reply_text(
            f"📊 <b>No history yet</b>\n\n"
            f"🌐 {url}\n\n"
            f"Checking soon...",
            parse_mode='HTML'
        )
        return
    
    message = f"<b>📊 History: {url}</b>\n\n"
    
    up_count = sum(1 for h in history if h.status == "up")
    down_count = sum(1 for h in history if h.status == "down")
    uptime = (up_count / len(history) * 100) if history else 0
    
    message += f"Uptime: {uptime:.1f}%\n"
    message += f"Checks: {len(history)}\n\n"
    
    for h in history[:10]:
        emoji = "🟢" if h.status == "up" else "🔴"
        time = h.checked_at.strftime('%m/%d %H:%M')
        response = f"{h.response_time:.2f}s" if h.response_time else "N/A"
        message += f"{emoji} {time} - {response}\n"
    
    await update.message.reply_text(message, parse_mode='HTML')


def is_valid_url(url: str) -> bool:
    """Validate URL format"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))


# Import telegram at module level for handlers
import telegram
