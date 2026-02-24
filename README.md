# 🌐 Website Uptime Monitor

A Telegram-based SaaS for monitoring website uptime with automatic alerts.

![Python](https://img.shields.io/badge/python-3.11+-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

- **Telegram Bot Interface** - Add/remove/list websites via simple commands
- **Automatic Monitoring** - Checks websites every 2 minutes
- **Smart Alerts** - Get notified only when status changes (no spam!)
- **Uptime History** - Store and view historical uptime data
- **Self-Healing** - Automatic recovery from errors
- **Docker Ready** - Deploy anywhere with Docker
- **Low Memory** - Optimized for 512MB VPS

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (for local development)
- Docker (for deployment)
- Telegram Bot Token

### Get Your Telegram Bot Token

1. Open Telegram and search for @BotFather
2. Send `/newbot` to create a new bot
3. Follow the instructions and get your bot token
4. Start your bot by sending `/start`

### Local Development

```bash
# Clone the repository
cd ~/PythonProjects/python-for-ai
git clone https://github.com/predaaaasaaaaaaa/website-uptime-monitor.git
cd website-uptime-monitor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your TELEGRAM_BOT_TOKEN

# Run the bot
python main.py
```

### Docker Deployment

```bash
# Build the image
docker build -t website-uptime-monitor .

# Run the container
docker run -d \
  --name uptime-monitor \
  -v $(pwd)/data:/app/data \
  -e TELEGRAM_BOT_TOKEN=your_token_here \
  website-uptime-monitor
```

### Docker Compose

```yaml
version: '3.8'

services:
  monitor:
    build: .
    restart: unless-stopped
    volumes:
      - ./data:/app/data
    environment:
      - TELEGRAM_BOT_TOKEN=your_token_here
      - CHECK_INTERVAL_MINUTES=2
      - REQUEST_TIMEOUT_SECONDS=10
```

## 📖 Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/add <url>` | Add website to monitor |
| `/remove <url>` | Remove website |
| `/list` | List all monitored websites |
| `/status` | Show status of all websites |
| `/history <url>` | Show uptime history |
| `/help` | Show help message |

## 🔧 Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Required |
| `TELEGRAM_USER_ID` | Optional: restrict to specific user | None |
| `CHECK_INTERVAL_MINUTES` | Check interval in minutes | 2 |
| `REQUEST_TIMEOUT_SECONDS` | HTTP request timeout | 10 |
| `LOG_LEVEL` | Logging level | INFO |

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           Telegram Bot                   │
│  /add, /remove, /list, /status          │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         Monitor Service                  │
│  • Scheduler (every 2 min)              │
│  • HTTP Checker                         │
│  • Alert Manager                        │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         SQLite Database                  │
│  • users, websites, history             │
└─────────────────────────────────────────┘
```

## 📁 Project Structure

```
website-uptime-monitor/
├── main.py              # Entry point
├── config.py            # Configuration
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker image
├── src/
│   ├── bot/           # Telegram bot handlers
│   ├── monitor/       # Monitoring engine
│   └── database/      # SQLite operations
└── tests/             # Unit tests
```

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## 💾 Data Storage

All data is stored in `data/monitor.db`:
- **users** - Telegram chat IDs
- **websites** - Monitored URLs
- **history** - Check results with timestamps

## 🔒 Security

- Store sensitive data in `.env` (never commit!)
- Use Docker secrets for production
- Optionally restrict to specific Telegram user

## 📝 License

MIT License - feel free to use and modify!

## 🙌 Acknowledgments

Built with python-telegram-bot and httpx.

---

Made with ❤️ by PREDA
