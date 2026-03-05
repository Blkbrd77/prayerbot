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
        ├── ci.yml        # Flake8 + pytest + bandit
        └── deploy.yml    # Auto-deploy to Raspberry Pi on push to main
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

## Setup — Raspberry Pi Deployment

Follow the steps below **once** on your Raspberry Pi to get everything
running.  After that, every merge to `main` triggers the
`Deploy to Raspberry Pi` GitHub Actions workflow which automatically
pulls the latest code and restarts the gateway — no manual SSH required.

---

### Prerequisites
- Raspberry Pi (any model) running Raspberry Pi OS or similar Debian-based OS
- Python 3.11+ (`sudo apt install python3 python3-pip`)
- OpenClaw installed (`pip3 install openclaw` — or follow the OpenClaw docs)
- Telegram bot token (obtain one from [@BotFather](https://t.me/BotFather))
- GitHub account with access to this repository

---

### 1. Clone the repository onto the Pi

```bash
# Run on the Pi (SSH in or use a local terminal)
cd ~
git clone https://github.com/Blkbrd77/prayerbot.git
cd prayerbot
pip3 install -r requirements.txt
```

---

### 2. Configure environment variables

```bash
cp .env.example .env
nano .env   # or use your preferred editor
```

Fill in the three values:

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token from @BotFather |
| `TELEGRAM_CHAT_ID` | Your chat ID — use [@userinfobot](https://t.me/userinfobot) |
| `OPENCLAW_PORT` | Leave as `18790` unless you need a different port |

---

### 3. Configure and start the OpenClaw profile

```bash
openclaw --profile prayerbot onboard
# When prompted, set port to 18790 and choose the openai-codex model
```

---

### 4. Install the systemd service

This keeps the OpenClaw gateway running in the background and starts it
automatically on every boot.

```bash
# Edit the service file if your username is not 'pi'
nano openclaw-prayerbot-gateway.service   # update User= and paths if needed

sudo cp openclaw-prayerbot-gateway.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now openclaw-prayerbot-gateway

# Verify it is running
sudo systemctl status openclaw-prayerbot-gateway
```

---

### 5. Configure cron jobs

```bash
crontab -e
```

Add the following lines (adjust the path if you cloned to a location
other than `/home/pi/prayerbot`):

```cron
# PrayerBot — daily scripture at 6:00 AM
0 6 * * * /usr/bin/python3 /home/pi/prayerbot/scripture.py

# PrayerBot — evening theological reflection at 8:00 PM
0 20 * * * /usr/bin/python3 /home/pi/prayerbot/theologian.py

# PrayerBot — weekly Sunday prayer review at 7:00 AM
0 7 * * 0 /usr/bin/python3 /home/pi/prayerbot/prayerlist.py --review
```

---

### 6. Set up the GitHub Actions self-hosted runner (enables auto-deploy)

The `deploy.yml` workflow runs **on the Pi itself** using a GitHub
self-hosted runner.  This lets GitHub Actions SSH-free access to your Pi
without exposing any ports.

```bash
# ── On the Pi ──────────────────────────────────────────────────────────────
mkdir -p ~/actions-runner && cd ~/actions-runner

# Download the latest runner — check https://github.com/actions/runner/releases
# for the latest version and replace the version number below accordingly.
curl -o actions-runner-linux-arm64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-arm64-2.311.0.tar.gz

tar xzf actions-runner-linux-arm64-2.311.0.tar.gz
```

Generate a registration token:

1. Go to **GitHub → your repo → Settings → Actions → Runners**
2. Click **New self-hosted runner**
3. Select **Linux / ARM64** and copy the `--token` value shown on screen

```bash
# Back on the Pi — paste the token from GitHub
./config.sh \
  --url https://github.com/Blkbrd77/prayerbot \
  --token <PASTE_TOKEN_HERE>

# Install as a systemd service so it starts on every boot
sudo ./svc.sh install
sudo ./svc.sh start
```

The runner will now appear as **online** in GitHub → Settings → Actions → Runners.

**Allow the runner to restart the systemd service without a password prompt:**

```bash
sudo visudo
# Add this line at the bottom (replace 'pi' with your username if different):
pi ALL=(ALL) NOPASSWD: /bin/systemctl restart openclaw-prayerbot-gateway
```

From this point forward, every push to `main` will automatically:
1. Check out the latest code on the Pi
2. Upgrade Python dependencies
3. Restart the OpenClaw gateway

---

## Turning Off the PR Approver Requirement

You are seeing a **"Review required"** or **"Approval required"** status
check on your pull requests because the `main` branch has a **Branch
Protection Rule** that requires at least one approving review.

To disable it (since you review all PRs yourself):

1. Go to **GitHub → Blkbrd77/prayerbot → Settings → Branches**
2. Under **Branch protection rules**, click **Edit** next to the rule for
   `main`
3. Under **"Protect matching branches"**, find **"Require a pull request
   before merging"** and either:
   - **Uncheck** the entire option to remove all PR requirements, **or**
   - Keep it checked but set **"Required number of approvals"** to **0**
     (this still requires a PR but skips the reviewer approval step)
4. Scroll down and click **Save changes**

> **Tip:** As the repository owner you can also enable the
> *"Allow specified actors to bypass required pull requests"* option and
> add yourself, which lets you merge your own PRs without waiting for an
> approval even if the rule stays on for other contributors.

---

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
