# PrayerBot

A second OpenClaw instance on the Raspberry Pi that delivers daily scripture, manages a prayer list, and provides theological/philosophical reflections — all via Telegram.

## Architecture

```
prayerbot/
├── scripture.py       # Daily verse selection + Telegram delivery
├── prayerlist.py      # Prayer list CRUD + weekly review
├── theologian.py      # Daily quote + reflection prompt
├── data/
│   ├── verses.json       # 365+ curated verses by theme
│   ├── theologians.json  # 50+ quotes from major theologians
│   └── prayers.json      # User prayer list (JSON storage)
├── tests/
│   └── conftest.py
└── .github/
    └── workflows/
        └── ci.yml        # Flake8 + pytest + bandit
```

## Components

### scripture.py — Daily Verse
- Selects a verse from `data/verses.json` based on theme rotation
- Delivers via Telegram at **6:00 AM** daily
- Tracks which verses have been sent to avoid repeats
- Themes: faith, hope, love, strength, peace, wisdom

### prayerlist.py — Prayer List Manager
- **Add** prayers with optional category and date
- **Remove** prayers (mark as answered or delete)
- **List** active prayers
- **Review** — weekly Sunday summary at **7:00 AM**
- Persists to `data/prayers.json`

### theologian.py — Theological Reflections
- Selects a quote from `data/theologians.json`
- Generates a brief reflection prompt using the OpenClaw gateway
- Delivers via Telegram at **8:00 PM** daily
- Sources: Augustine, Aquinas, C.S. Lewis, Bonhoeffer, Kierkegaard, and more

## Setup

### Prerequisites
- Raspberry Pi with OpenClaw installed
- Telegram bot token (via [@BotFather](https://t.me/BotFather))
- Python 3.11+

### 1. Clone and install

```bash
git clone https://github.com/Blkbrd77/prayerbot.git
cd prayerbot
pip install -r requirements.txt  # (once created)
```

### 2. Configure OpenClaw profile

```bash
openclaw --profile prayerbot onboard
# Configure port 18790, openai-codex model
```

### 3. Environment variables

```bash
cp .env.example .env
# Edit .env with your Telegram bot token, chat ID, and OpenClaw settings
```

### 4. Set up systemd service

```bash
sudo cp openclaw-prayerbot-gateway.service /etc/systemd/system/
sudo systemctl enable --now openclaw-prayerbot-gateway
```

### 5. Configure cron

```bash
crontab -e
# 0 6 * * * /usr/bin/python3 /path/to/prayerbot/scripture.py
# 0 20 * * * /usr/bin/python3 /path/to/prayerbot/theologian.py
# 0 7 * * 0 /usr/bin/python3 /path/to/prayerbot/prayerlist.py --review
```

## Development

```bash
# Lint
flake8 .

# Test
pytest

# Security scan
bandit -r . -x ./tests
```

## License

MIT
