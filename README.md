# Screen AI Assistant

A lightweight local utility that:
- takes a screenshot via hotkey
- sends it to an LLM (OpenAI)
- delivers the response directly to your Telegram

No background services required. Runs only on demand.

---

## Features

- Global hotkey screenshot capture
- LLM-based screen analysis
- Telegram delivery (text + optional image)
- Zero persistent services (runs → sends → exits)
- Auto-setup of Telegram chat_id
- Structured logging

---

## Project Structure

```

.
├── images/              # saved screenshots
├── logs/                # logs (ignored by git)
├── prompts/             # prompt templates
├── scripts/
│   ├── take_screenshot.py
│   ├── analyze_screenshot.py
│   ├── send_telegram.py
│   └── common/
├── run_screenshot.sh    # main entrypoint
├── .env                 # secrets (not in git)
├── .env.example
└── README.md

````

---

## Requirements

- Linux (tested on Ubuntu-based systems)
- Python 3.10+
- X11 (for global hotkeys via `sxhkd`)
- Telegram account

---

## Installation

### 1. Clone repository

```bash
git clone https://github.com/your_repo/screen-ai-assistant.git
cd screen-ai-assistant
````

---

### 2. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Setup environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```dotenv
OPENAI_API_KEY=your_openai_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# leave empty — will be auto-filled
TELEGRAM_CHAT_ID=
```

---

## Telegram Setup (IMPORTANT)

### Step 1. Create bot

Use Telegram:

```
@BotFather → /newbot
```

Copy token into `.env`.

---

### Step 2. Start bot

Open your bot and send:

```
/start
```

This is required for chat detection.

---

## First Run (Auto Initialization)

Run manually:

```bash
./run_screenshot.sh
```

What happens:

1. Screenshot is taken
2. Image sent to LLM
3. Bot automatically:

   * resolves your `chat_id`
   * saves it into `.env`
4. You receive message in Telegram

After this — no manual setup needed.

---

## Hotkey Setup (Global)

Install sxhkd:

```bash
sudo apt install sxhkd
```

Edit config:

```bash
nano ~/.config/sxhkd/sxhkdrc
```

Add:

```bash
ctrl + alt + q
    /home/YOUR_USERNAME/path_to_project/run_screenshot.sh
```

---

### Start sxhkd

```bash
sxhkd &
```

---

### Enable autostart

```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/sxhkd.desktop
```

```ini
[Desktop Entry]
Type=Application
Exec=sxhkd
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=sxhkd
```

---

## Usage

Press:

```text
CTRL + ALT + Q
```

Result:

* screenshot taken
* analyzed by AI
* response delivered to Telegram

---

## Configuration

### `.env` options

```dotenv
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.4-mini

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

TELEGRAM_SEND_IMAGE=true

DEFAULT_IMAGE_DIR=images
DEFAULT_LOG_DIR=logs
DEFAULT_PROMPT_PATH=prompts/default_prompt.txt

LOG_LEVEL=INFO
```

---

## Logs

Logs are stored in:

```
logs/
```

Includes:

* screenshot lifecycle
* LLM requests
* Telegram delivery
* errors

---

## Security Notes

* Never commit `.env`
* Telegram token gives full control over bot
* OpenAI key is billable — keep it private

---

## Troubleshooting

### 1. Telegram: "chat not found"

* ensure you sent `/start` to bot
* ensure `TELEGRAM_CHAT_ID` is empty on first run

---

### 2. Telegram: "Unauthorized"

* invalid bot token
* regenerate via BotFather

---

### 3. Nothing happens on hotkey

* check sxhkd is running:

```bash
ps aux | grep sxhkd
```

---

### 4. Logs not updating

Check:

```bash
tail -f logs/launcher.log
```

---

## Roadmap

* multiple hotkeys → multiple folders
* image classification (memes/work/etc)
* Docker packaging
* cross-platform support

---

## License

MIT

````

---

# .gitignore

Вот правильный вариант, чтобы:
- **логи не попадали в git**
- но папка `logs/` существовала

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.venv/

# Environment
.env

# Logs
logs/*
!logs/.gitkeep

# Images (optional — можно хранить или нет)
images/*
!images/.gitkeep

# OS
.DS_Store
Thumbs.db
````

# ScreenMind

ScreenMind is a local AI utility that lets you press a hotkey, capture your screen, solve what is visible, and receive the answer in Telegram.

It is designed for short tasks visible on screen:
- code output questions
- coding tasks
- logic questions
- short quiz-style prompts
- math questions

The project runs on demand only:
- no long-running bot process
- no background web server
- no Docker required for normal use

## How it works

1. A hotkey triggers `run_screenshot.sh`
2. A screenshot is saved locally
3. The image is analyzed through a multi-step pipeline:
   - extract visible information
   - classify the task
   - route to solver
   - execute Python code when needed
   - format final answer
4. The final answer is sent to Telegram
5. The process exits

## Features

- Global hotkey screenshot capture
- Telegram delivery
- Automatic Telegram `chat_id` discovery on first run
- Multi-step task pipeline
- Python code execution for output-based code questions
- Structured logs

## Requirements

- Linux
- Python 3.10+
- Telegram account
- OpenAI API key
- Telegram bot token
- `sxhkd` for global hotkeys

## Installation

### 1. Clone repository

```bash
git clone https://github.com/your-account/screenmind.git
cd screenmind