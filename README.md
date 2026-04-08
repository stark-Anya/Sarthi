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
<details>
  <summary><b>✨ Features (Click to Expand)</b></summary>

## 🚀 Overview
Powerful all-in-one **JEE/NEET Preparation Assistant Bot** — designed to manage your entire study workflow efficiently.

---

### 📅 Today Dashboard
Your daily command center.

- Add tasks with subject prefixes  
- Mark tasks as done / pending  
- Built-in focus timer (15 / 25 / 50 min)  
- Track test scores  
- Manage doubts & revisions  

📌 Everything — in one clean dashboard.

---

### 🧠 Smart Memories
Never repeat mistakes again.

- Save:
  - Silly mistakes 🤦‍♂️  
  - Errors ❌  
  - Important concepts 💡  
- Add title, content (text/photo), answer & key points  
- Browse history anytime  

---

### 📚 Materials Library
All study resources in one place.

- Class-wise Books (Class 11 / 12)  
- Formulas  
- PYQs (JEE Mains / Advanced / NEET)  
- Mixed (11 + 12) books  
- Smooth inline navigation  

---

### 📊 Progress Stats
Track your improvement visually.

- Weekly / Monthly / All-time stats  
- Study hours tracking  
- Subject-wise breakdown (bars)  
- Streak graph 🔥  
- Test score trends & improvement  

---

### 🔄 Spaced Revision
Science-backed revision system.

- Mark lecture as watched  
- Auto-schedules revision at:
  - 1 day  
  - 3 days  
  - 7 days  
  - 30 days  
- Daily reminder at **9 AM**

---

### 🎯 Lecture Manager
Never miss a lecture again.

- Save lecture links  
- Set alert time  
- Add subject & custom message  
- Get buttons:
  - Open Link  
  - Mark Watched  
  - Snooze  

---

### 🔍 Universal Search
Find anything instantly.

```
/search query
```

- Searches across:
  - Memories  
  - Daily reports  
  - Formulas  
  - Books  
  - PYQs  
- Delete directly from results  

---

### 🛡️ Admin Panel
Full control access.

- Password-protected login  
- Upload:
  - Formulas  
  - Books  
  - PYQs (multi-file support)  
- Edit / delete content  
- Broadcast messages  
- Manage users  

---

### 🔔 Smart Reminders
Automated daily system ⏰

- **6 AM** → Morning message + streak  
- **7 AM** → Formula flashcard  
- **9 AM** → Revision alert  
- **8 PM** → Doubt reminder (if pending 2+ days)  
- **11 PM** → Daily DB backup  
- **Sunday** → Weekly report  

---

### 🗄️ Daily DB Backup
Your data is always safe.

- Full SQLite database backup  
- Sent automatically to admin at **11 PM daily**  

---

### 💭 Thoughts & Motivation
Private vault system.

- Save random thoughts  
- Store motivational quotes/images  
- Add / delete / browse anytime  

---

### 📒 Daily Reports
Track your daily study.

- Write report (text or photo)  
- Edit anytime  
- Browse all past reports easily  

---

</details>

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
<details>
  <summary><b>🖥️ VPS / Ubuntu Server (Recommended · Full Control)</b></summary>

## 🚀 Step 1 — Setup Server & Install Dependencies

### 🔄 Update system & install required packages
```bash
sudo apt update && sudo apt install -y python3.11 python3-pip git screen
```

### 📥 Clone the repository
```bash
git clone https://github.com/stark-Anya/Sarthi
cd Sarthi
```

### 🧪 Create & activate virtual environment
```bash
python3 -m venv myenv
source myenv/bin/activate
```

### 📦 Install dependencies
```bash
pip install -r requirements.txt
```

### ⚙️ Configure your bot
```bash
nano config.py
```

---

## ⚡ Step 2 — Run Bot Using Screen (Recommended)

Keeps your bot running even after SSH disconnect.

```bash
screen -S jeebot
python bot.py
```

### 🔌 Useful Screen Commands
- Detach: `Ctrl + A` then `D`
- Reattach: `screen -r jeebot`

---

## 🔁 Step 3 — Setup Auto-Restart (systemd Service) *(Optional)*

### Create service file
```bash
sudo nano /etc/systemd/system/jeebot.service
```

### Paste the following configuration
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

### Enable & start the service
```bash
sudo systemctl daemon-reload
sudo systemctl enable jeebot
sudo systemctl start jeebot
sudo systemctl status jeebot
```

</details>

---
<details>
  <summary><b>🌐 Render (Free Tier Available · Beginner Friendly · Auto Deploy)</b></summary>

## 🚀 Overview
Render ek cloud platform hai jahan tum bina VPS manage kiye apna Telegram bot easily deploy kar sakte ho.  
Free tier me bhi bot smoothly chal jata hai (with some limits).

---

## 🧾 Step 1 — Create `render.yaml`

Project ke root folder me ek file banao:

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

### 📌 Explanation:
- `type: worker` → Background bot (no web server)
- `buildCommand` → Dependencies install karega
- `startCommand` → Bot run karega
- `envVars` → Secrets (token, admin id)

---

## 🔗 Step 2 — Deploy on Render

1. Code ko GitHub pe push karo  
2. Open 👉 https://render.com  
3. Click **New → Background Worker**  
4. Apna repo connect karo  
5. Environment variables verify/add karo  
6. Click **Create Service**

⏳ First deploy me 2–5 min lag sakte hain

---

## 💾 Step 3 — Add Persistent Storage (IMPORTANT)

By default Render storage temporary hota hai ❌  
Restart ke baad data delete ho jayega

### ✅ Fix:

- Dashboard → **Disks**
- Click **Add Disk**
- Mount Path set karo:

```
/data
```

---

## ⚙️ Step 4 — Update Database Path

Apne code/config me DB path change karo:

```python
DB_PATH = "/data/jee_saarthi.db"
```

---

## 🔁 Auto Deploy Feature

Render ka best feature 🔥

- GitHub me push karte hi bot automatically redeploy ho jayega
- Manual restart ki need nahi

---

## ⚠️ Notes

- Free tier me bot idle ho sakta hai (no activity → sleep)
- Logs dekhne ke liye dashboard ka use karo
- Large bots ke liye paid plan better rahega

</details>

---

<details>
  <summary><b>🚂 Railway ($5/mo · Fastest Deploy · Developer Friendly)</b></summary>

## 🚀 Overview
Railway ek powerful platform hai jo fast deploy + better performance deta hai.  
Thoda paid hai, but serious bots ke liye best option 🔥

---

## 📁 Step 1 — Create `Procfile`

Project root me file banao:

```
Procfile
```

Aur isme likho:

```
worker: python bot.py
```

### 📌 Explanation:
- `worker` → Background process define karta hai
- `python bot.py` → Bot start command

---

## 🛠️ Step 2 — Install & Deploy via CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy project
railway up
```

---

## 🔑 Step 3 — Set Environment Variables

```bash
railway variables set BOT_TOKEN=your_token
railway variables set ADMIN_ID=123456789
```

💡 Alternative: Dashboard se bhi set kar sakte ho

---

## 💾 Step 4 — Add Persistent Volume

Data loss avoid karne ke liye ye step MUST hai ⚠️

### Steps:

- Railway Dashboard open karo  
- Apna project select karo  
- Click **Add Volume**  
- Mount Path set karo:

```
/app/data
```

---

## ⚙️ Step 5 — Update Database Path

```python
DB_PATH = "/app/data/jee_saarthi.db"
```

---

## ⚡ Features

- 🚀 Super fast deployment
- 🔄 Instant redeploy
- 📊 Better logs & monitoring
- 🔒 Stable uptime (no sleep issue like free tier)

---

## ⚠️ Notes

- Free trial ke baad ~$5/month cost aata hai
- Beginners ke liye thoda complex ho sakta hai
- Production bots ke liye highly recommended

</details>

---
<details>
  <summary><b>⚡ Koyeb (Free Tier · Global Edge · Fast Deploy)</b></summary>

## 🚀 Overview
Koyeb ek modern cloud platform hai jo global edge infrastructure pe run karta hai.  
Iska matlab — aapka bot duniya ke multiple regions me fast response de sakta hai 🌍⚡

Free tier available hai aur deployment kaafi smooth hota hai.

---

## 🧾 Step 1 — Create `koyeb.yaml`

Project ke root folder me ek file banao:

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

---

## 📌 Configuration Explanation

- `type: worker` → Background bot (no web server needed)
- `buildpack: python` → Auto Python environment setup
- `command: python bot.py` → Bot start command
- `env` → Sensitive data (token, admin id)

---

## 🔗 Step 2 — Deploy on Koyeb

1. Open 👉 https://koyeb.com  
2. Click **Create App**  
3. Connect your **GitHub repository**  
4. Select your project repo  
5. Add / verify environment variables  
6. Click **Deploy**

⏳ Deployment usually takes 1–3 minutes

---

## ⚙️ Auto Detection Feature

Koyeb automatically:
- Detects Python project 🐍  
- Installs dependencies from `requirements.txt` 📦  
- Builds and runs your bot 🚀  

No manual setup required 🔥

---

## 💾 Step 3 — Add Persistent Storage (Important)

By default storage temporary hota hai ❌  
Restart hone pe SQLite DB delete ho sakta hai

### ✅ Fix:

- Koyeb Dashboard → **Volumes**
- Add new volume  
- Mount path set karo:

```
/mnt/data
```

---

## 🗄️ Update Database Path

```python
DB_PATH = "/mnt/data/jee_saarthi.db"
```

---

## ⚠️ Notes

- Free tier me limited resources milte hain
- Logs dashboard me easily available hote hain
- Production bots ke liye scaling option available hai

</details>

---

<details>
  <summary><b>🟣 Heroku ($7/mo · Easy Setup · Classic Platform)</b></summary>

## 🚀 Overview
Heroku ek popular cloud platform hai jo beginners ke liye kaafi easy hai.  
Lekin ab ye fully paid ho chuka hai 💰

---

## 📁 Step 1 — Create Required Files

### `Procfile`
```
worker: python bot.py
```

### `runtime.txt`
```
python-3.11.9
```

---

## 📌 Explanation

- `Procfile` → Bot ka run command define karta hai
- `runtime.txt` → Python version fix karta hai

---

## 🛠️ Step 2 — Deploy via Heroku CLI

```bash
# Login
heroku login

# Create app
heroku create jee-saarthi-bot

# Set environment variables
heroku config:set BOT_TOKEN=your_bot_token
heroku config:set ADMIN_ID=123456789

# Deploy code
git push heroku main

# Enable worker (disable web)
heroku ps:scale web=0 worker=1

# View logs
heroku logs --tail
```

---

## ⚠️ Important — Storage Limitation

Heroku ka filesystem **ephemeral** hota hai ❌  
Matlab:

- Restart → Data delete  
- SQLite reliable nahi hai  

---

## ✅ Recommended Solution

### Option 1 — Use PostgreSQL (Best)
- Heroku Postgres addon use karo  
- Production ke liye recommended

### Option 2 — Backup System
- Daily DB backup admin ko send karo  
- (Aap already use kar rahe ho 👍)

---

## ⚡ Features

- Easy deployment 🚀  
- Clean dashboard 📊  
- Good for small to medium bots  

---

## ⚠️ Notes

- Free plan available nahi hai  
- Monthly ~$7 cost  
- Heavy bots ke liye costly ho sakta hai  

</details>

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
