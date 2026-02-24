# Website Uptime Monitor - Specification

## Project Overview

- **Project Name:** Website Uptime Monitor
- **Type:** Telegram-based SaaS
- **Core Functionality:** Monitor websites uptime via Telegram bot, alert users when sites go down
- **Target Users:** Developers, sysadmins, small business owners who need simple website monitoring

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Telegram Bot                          │
│  (User Interface - Add/Remove/List websites)            │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   Monitor Service                        │
│  - Scheduler (every 2 minutes)                          │
│  - Website checker (HTTP requests)                      │
│  - Alert sender (Telegram notifications)               │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   SQLite Database                       │
│  - Users (chat_id, settings)                            │
│  - Websites (url, user_id, status)                     │
│  - History (website_id, status, timestamp, response_time)│
└─────────────────────────────────────────────────────────┘
```

## Core Features

### 1. Telegram Bot Commands
- `/start` - Welcome message, show help
- `/add <url>` - Add website to monitor
- `/remove <url>` - Remove website from monitoring
- `/list` - List all monitored websites
- `/history <url>` - Show uptime history for a website
- `/status` - Show overall status of all websites
- `/help` - Show available commands

### 2. Monitoring Engine
- Check website every 2 minutes
- Use HTTP HEAD request (faster)
- Timeout: 10 seconds
- Track response time
- Handle redirects
- Detect down status (non-2xx or timeout)

### 3. Alert System
- Send Telegram message when website goes down
- Send recovery message when website comes back up
- Avoid spam: only alert on status change

### 4. Data Storage (SQLite)
- **users** table: chat_id, created_at
- **websites** table: id, chat_id, url, name, enabled, created_at
- **history** table: id, website_id, status, response_time, checked_at

### 5. Self-Healing
- Process restart on crash (supervisord or systemd)
- Database connection retry
- Network error handling
- Graceful degradation

## Technical Stack

- **Language:** Python 3.11+
- **Bot:** python-telegram-bot 21.x
- **Database:** SQLite3 (built-in)
- **HTTP Client:** httpx (async)
- **Scheduler:** APScheduler
- **Docker:** Python slim image
- **Memory:** < 512MB

## File Structure

```
website-uptime-monitor/
├── SPEC.md
├── README.md
├── requirements.txt
├── Dockerfile
├── .env.example
├── .gitignore
├── config.py
├── main.py
├── src/
│   ├── __init__.py
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── handlers.py      # Telegram command handlers
│   │   └── keyboard.py      # Inline keyboards
│   ├── monitor/
│   │   ├── __init__.py
│   │   ├── checker.py        # Website uptime checker
│   │   ├── scheduler.py      # Monitoring scheduler
│   │   └── alerts.py        # Alert sending
│   └── database/
│       ├── __init__.py
│       ├── models.py         # Database models
│       └── repository.py    # DB operations
└── tests/
    ├── __init__.py
    ├── test_checker.py
    └── test_database.py
```

## Constraints

- **Memory:** < 512MB
- **VPS:** Must run on cheap VPS (1 CPU, 512MB RAM)
- **Recovery:** Auto-restart on crash
- **Storage:** SQLite file-based (no external DB needed)

## Acceptance Criteria

1. ✅ Bot responds to /start with welcome message
2. ✅ User can add website with /add command
3. ✅ User can remove website with /remove command
4. ✅ User can list all monitored websites
5. ✅ Websites checked every 2 minutes automatically
6. ✅ Alert sent when website goes down
7. ✅ Alert sent when website recovers
8. ✅ History stored in SQLite
9. ✅ Bot handles errors gracefully
10. ✅ Docker build < 200MB
11. ✅ Memory usage < 512MB
