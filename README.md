<div align="center">

<img src="https://img.shields.io/badge/🎓_JEE_Saarthi-Bot-5b8dee?style=for-the-badge&labelColor=0a0d14" alt="JEE Saarthi"/>

# 🎓 JEE Saarthi

### Your AI-powered study companion for JEE & NEET
> Tasks · Memories · Formulas · Books · PYQs · Stats & more — all inside Telegram.

<br/>

[![Demo Bot](https://img.shields.io/badge/🚀_Demo_Bot-Try_Live-5b8dee?style=for-the-badge&logoColor=white)](https://t.me/JeeSarthi_bot)
[![Owner](https://img.shields.io/badge/👤_Owner-Mister_Stark-fb923c?style=for-the-badge)](https://t.me/carelessxowner)
[![Support](https://img.shields.io/badge/💬_Support-Group-64748b?style=for-the-badge)](https://t.me/CarelessxWorld)
[![Updates](https://img.shields.io/badge/📢_Updates-Channel-a78bfa?style=for-the-badge)](https://t.me/CarelessxCoder)
[![More Bots](https://img.shields.io/badge/🤖_More-Bots-34d399?style=for-the-badge)](https://t.me/Anya_Bots)

<br/>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-WAL-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Telegram](https://img.shields.io/badge/python--telegram--bot-v20+-26A5E4?style=flat-square&logo=telegram&logoColor=white)
![APScheduler](https://img.shields.io/badge/APScheduler-IST-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Lines of Code](https://img.shields.io/badge/Lines_of_Code-5100+-blueviolet?style=flat-square)

</div>

---

## 📊 Stats at a Glance

| 🐍 Python Files | 📝 Lines of Code | 🗄️ DB Tables | ✨ Features | ⏰ Scheduled Jobs |
|:-:|:-:|:-:|:-:|:-:|
| **16** | **5100+** | **12** | **50+** | **6** |

---

## ✨ Features

### 📅 Today Dashboard
Add tasks with subject prefixes, toggle done, focus timer (15/25/50 min), test scores, doubts, revisions — all in one place.

### 🧠 Smart Memories
Save Silly mistakes, Errors, Important concepts — with title, content (photo/text), answer, and key points. Browse history anytime.

### 📚 Materials Library
Class-wise Books (Class 11/12), Formulas, PYQs (JEE Mains/Adv/NEET), and 11&12 Mix books — all with inline navigation.

### 📊 Progress Stats
Weekly, Monthly and All-Time dashboard — study hours, subject breakdown with bars, streak graph, test score trends, and improvement tracking.

### 🔄 Spaced Revision
Mark a lecture as watched → auto-schedule revisions at 1 day, 3 days, 7 days, 30 days. Daily reminder at 9 AM.

### 🎯 Lecture Manager
Save lecture links with alert times, subject, and custom messages. Get pinged at exact time with Open Link, Mark Watched, Snooze buttons.

### 🔍 Universal Search
`/search query` — searches across memories, daily reports, formulas, books, PYQs, mix books all at once. Delete directly from results.

### 🛡️ Admin Panel
Password-based access. Upload formulas, books, PYQs with multiple PDFs. Edit titles, delete content, broadcast, manage users.

### 🔔 Smart Reminders
- **6 AM** — morning message with streak
- **7 AM** — formula flash card
- **8 PM** — doubt reminder (if pending 2+ days)
- **9 AM** — revision alert
- **11 PM** — daily SQLite DB backup to admin
- **Sunday** — weekly report

### 🗄️ Daily DB Backup
Entire SQLite database automatically sent to admin at 11 PM every day. Never lose your data.

### 💭 Thoughts & Motivation
Private vaults for random thoughts and motivational quotes/images. Navigate, add, delete — all inline.

### 📒 Daily Reports
Write today's study report (text or photo). View & update anytime. Browse all past reports with navigation.

---

## ⌨️ Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Launch the bot, see home screen with streak and date |
| `/stats` | Open your personal progress dashboard — weekly, monthly, all-time |
| `/search <query>` | Search across all memories, books, formulas, PYQs instantly |
| `/ban <user_id>` | Admin — ban a user from the bot |
| `/unban <user_id>` | Admin — unban a user and notify them |

> Everything else is driven by **inline buttons** — clean, fast, no typing needed.

---

## 📁 Project Structure

```
jee_saarthi/
├── bot.py             # Entry point — all ConversationHandlers registered
├── config.py          # BOT_TOKEN, ADMIN_PASS, DB_CLEAR_PASS, TIMEZONE
├── database.py        # 12 tables, helper functions, init_db()
├── ui.py              # Centralized keyboard builders
├── scheduler.py       # 6 APScheduler jobs (IST timezone)
├── requirements.txt
└── handlers/
    ├── common.py      # /start, home_callback, ban/unban, check_banned
    ├── today.py       # Tasks, Lectures, Timer, Scores, Doubts, Revisions
    ├── memories.py    # Silly / Error / Important + Daily Report
    ├── materials.py   # Books, Formulas, PYQs, Mix — with pagination
    ├── formulas.py    # Formula viewer: Class → Subject → Chapter
    ├── motivation.py  # Motivation + Thoughts vault (add/view/delete)
    ├── thought.py     # Re-exports from motivation.py
    ├── stats.py       # /stats — weekly/monthly/alltime dashboard + log
    ├── search.py      # /search — universal search with delete
    └── admin.py       # Admin panel: upload/edit/delete/broadcast/stats
```

---

## 🚀 Deployment Guide

### ⚙️ Step 0 — Configure `config.py`

```python
BOT_TOKEN      = "your_bot_token_here"       # From @BotFather
ADMIN_ID       = 123456789                   # Your Telegram user ID
ADMIN_PASS     = "your_admin_password"       # Admin panel password
DB_CLEAR_PASS  = "your_db_clear_password"   # Separate clear DB password
DB_PATH        = "jee_saarthi.db"
TIMEZONE       = "Asia/Kolkata"
```

---

### 🖥️ VPS / Ubuntu Server *(Recommended · Full Control)*

**Step 1 — SSH into server & install dependencies**
```bash
# Update & install Python
sudo apt update && sudo apt install -y python3.11 python3-pip git screen

# Clone your project
git clone https://github.com/yourusername/jee-saarthi.git
cd jee-saarthi

# Create virtual environment
python3 -m venv myenv
source myenv/bin/activate

# Install requirements
pip install -r requirements.txt

# Edit config with your credentials
nano config.py
```

**Step 2 — Run with screen (keeps bot alive after SSH disconnect)**
```bash
screen -S jeebot
python bot.py

# Detach: Ctrl+A then D
# Reattach later: screen -r jeebot
```

**Step 3 — Optional: systemd service for auto-restart**
```bash
sudo nano /etc/systemd/system/jeebot.service
```
```ini
[Unit]
Description=JEE Saarthi Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/jee-saarthi
ExecStart=/home/ubuntu/jee-saarthi/myenv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable jeebot
sudo systemctl start jeebot
sudo systemctl status jeebot
```

---

### 🌐 Render *(Free Tier Available · Easy Setup)*

**Step 1 — Create `render.yaml` in project root**
```yaml
services:
  - type: worker
    name: jee-saarthi-bot
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python bot.py"
    envVars:
      - key: BOT_TOKEN
        value: your_bot_token_here
      - key: ADMIN_ID
        value: "123456789"
```

**Step 2 —** Push to GitHub → Connect on Render dashboard → Add Environment Variables → Deploy

> Go to render.com → New → Background Worker → Connect repo → Set env vars → Create Service

**Step 3 — Add a persistent disk**

In Render dashboard: `Disks → Add → Mount Path: /data`  
Update in config: `DB_PATH = "/data/jee_saarthi.db"`

---

### 🚂 Railway *($5/mo · Super Fast Deploy)*

**Step 1 — Create `Procfile` in project root**
```
worker: python bot.py
```

**Step 2 — Deploy via Railway CLI**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login & deploy
railway login
railway init
railway up

# Set environment variables
railway variables set BOT_TOKEN=your_token
railway variables set ADMIN_ID=123456789
```

**Step 3 —** Dashboard → Add Volume → Mount at `/app/data`  
Set `DB_PATH = "/app/data/jee_saarthi.db"`

---

### ⚡ Koyeb *(Free Tier · Global Edge)*

**Step 1 — Create `koyeb.yaml` in project root**
```yaml
name: jee-saarthi-bot
services:
  - name: bot
    type: worker
    git:
      repository: github.com/yourusername/jee-saarthi
      branch: main
    build:
      buildpack: python
    run:
      command: python bot.py
    env:
      - key: BOT_TOKEN
        value: your_bot_token
      - key: ADMIN_ID
        value: "123456789"
```

**Step 2 —** Go to koyeb.com → Create App → Connect GitHub → Select repo → Set env vars → Deploy

> Koyeb auto-detects Python and installs `requirements.txt`

**Step 3 —** For SQLite persistence, use Koyeb Volumes. Add a persistent volume and set `DB_PATH = "/mnt/data/jee_saarthi.db"`

---

### 🟣 Heroku *($7/mo · Eco Dyno)*

**Step 1 — Create required files**

`Procfile`:
```
worker: python bot.py
```

`runtime.txt`:
```
python-3.11.9
```

**Step 2 — Deploy via Heroku CLI**
```bash
# Login & create app
heroku login
heroku create jee-saarthi-bot

# Set environment variables
heroku config:set BOT_TOKEN=your_bot_token
heroku config:set ADMIN_ID=123456789

# Deploy
git push heroku main

# Scale worker dyno (no web dyno needed)
heroku ps:scale web=0 worker=1

# Check logs
heroku logs --tail
```

> ⚠️ **Important:** Heroku has ephemeral filesystem. SQLite won't persist between restarts. Use Heroku Postgres addon or backup DB regularly (already done via daily backup job to admin).

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Bot Framework | python-telegram-bot v20+ |
| Database | SQLite (WAL mode) |
| Scheduler | APScheduler (IST timezone) |
| UI | Inline Keyboards |
| Hosting | VPS / Render / Railway / Koyeb / Heroku |

---

## 👨‍💻 Developer

<div align="center">

### 🦾 Mister Stark
**@carelessxowner**

[![Telegram](https://img.shields.io/badge/💬_Telegram-Message_Me-5b8dee?style=for-the-badge)](https://t.me/carelessxowner)
[![Support Group](https://img.shields.io/badge/🌍_Support-CarelessxWorld-64748b?style=for-the-badge)](https://t.me/CarelessxWorld)
[![Updates Channel](https://img.shields.io/badge/📢_Updates-CarelessxCoder-a78bfa?style=for-the-badge)](https://t.me/CarelessxCoder)
[![More Bots](https://img.shields.io/badge/🤖_More_Bots-Anya_Bots-34d399?style=for-the-badge)](https://t.me/Anya_Bots)
[![Demo](https://img.shields.io/badge/🎓_Demo-JeeSarthi_bot-fb923c?style=for-the-badge)](https://t.me/JeeSarthi_bot)

</div>

---

<div align="center">

**Built with ❤️ using Python · python-telegram-bot · SQLite · APScheduler**

*Made by [Mister Stark](https://t.me/carelessxowner) · [Support](https://t.me/CarelessxWorld) · [More Bots](https://t.me/Anya_Bots)*

</div>
