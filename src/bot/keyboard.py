# src/bot/keyboard.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_keyboard():
    """Main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Website", callback_data="add"),
            InlineKeyboardButton("🗑️ Remove Website", callback_data="remove")
        ],
        [
            InlineKeyboardButton("📋 My Websites", callback_data="list"),
            InlineKeyboardButton("📊 Status", callback_data="status")
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_yes_no_keyboard(confirm_data: str, cancel_data: str = "cancel"):
    """Yes/No confirmation keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=confirm_data),
            InlineKeyboardButton("❌ No", callback_data=cancel_data)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
