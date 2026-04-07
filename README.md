Ниже — обновлённый `README.md`, с учётом текущей архитектуры пайплайна, автоопределения `chat_id`, выполнения Python-кода и `OUTPUT_LANGUAGE`. Основано на твоём текущем README и черновике структуры/позиционирования. 

````md
# ScreenMind

ScreenMind is a local AI utility that lets you press a hotkey, capture your screen, solve what is visible, and receive the answer directly in Telegram.

It is designed for short tasks that appear on screen, including:
- code output questions
- coding tasks
- code bug explanation tasks
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
3. The screenshot is processed through a multi-step pipeline:
   - extract visible information
   - isolate task-relevant content from UI noise
   - classify the task
   - route to the correct solver
   - execute Python code when needed
   - validate and format the final answer
4. The final answer is sent to Telegram
5. The process exits

## Features

- Global hotkey screenshot capture
- Local on-demand execution
- Telegram delivery
- Automatic Telegram `chat_id` discovery on first run
- Multi-step pipeline instead of a single prompt
- Python code execution for output-based code questions
- Support for code bug explanation tasks
- Structured logs
- Configurable output language through `.env`

## Project Structure

```text
.
├── images/                      # saved screenshots
├── logs/                        # runtime logs (ignored by git)
├── prompts/                     # optional prompt templates
├── scripts/
│   ├── analyze_screenshot.py
│   ├── send_telegram.py
│   ├── take_screenshot.py
│   ├── common/
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── schemas.py
│   └── pipeline/
│       ├── extractor.py
│       ├── classifier.py
│       ├── qa_solver.py
│       ├── code_reconstructor.py
│       ├── code_executor.py
│       ├── validator.py
│       ├── formatter.py
│       └── orchestrator.py
├── run_screenshot.sh            # main entrypoint
├── .env                         # secrets and runtime config (not in git)
├── .env.example
├── requirements.txt
└── README.md
````

## Requirements

* Linux
* Python 3.10+
* Telegram account
* OpenAI API key
* Telegram bot token
* `sxhkd` for global hotkeys

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-account/screenmind.git
cd screenmind
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create `.env`

```bash
cp .env.example .env
```

Edit `.env` and fill in your secrets:

```dotenv
OPENAI_API_KEY=your_openai_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=

OPENAI_MODEL=gpt-4.1-mini
OUTPUT_LANGUAGE=en

TELEGRAM_SEND_IMAGE=true

DEFAULT_IMAGE_DIR=images
DEFAULT_LOG_DIR=logs
DEFAULT_PROMPT_PATH=prompts/default_prompt.txt

LOG_LEVEL=INFO
```

## Telegram Setup

### 1. Create a bot

Open Telegram and use:

```text
@BotFather
```

Create a new bot with:

```text
/newbot
```

Copy the bot token into `.env` as `TELEGRAM_BOT_TOKEN`.

### 2. Start the bot

Open your bot and send:

```text
/start
```

This is required so ScreenMind can detect your Telegram `chat_id` automatically.

## First Run

Run the project manually once:

```bash
./run_screenshot.sh
```

What happens on first run:

1. A screenshot is captured
2. The screenshot is analyzed
3. ScreenMind validates the Telegram bot token
4. If `TELEGRAM_CHAT_ID` is empty, it tries to resolve it automatically
5. The resolved `chat_id` is saved into `.env`
6. The answer is sent to Telegram

After the first successful run, no manual `chat_id` setup is needed.

## Hotkey Setup

Install `sxhkd`:

```bash
sudo apt update
sudo apt install sxhkd
```

Create config directory if needed:

```bash
mkdir -p ~/.config/sxhkd
```

Edit hotkey config:

```bash
nano ~/.config/sxhkd/sxhkdrc
```

Add:

```text
ctrl + alt + q
    /home/YOUR_USERNAME/path_to_project/run_screenshot.sh
```

Replace `/home/YOUR_USERNAME/path_to_project/` with the real absolute path to your project.

### Start `sxhkd`

```bash
sxhkd &
```

### Enable autostart

```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/sxhkd.desktop
```

Paste:

```ini
[Desktop Entry]
Type=Application
Exec=sxhkd
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=sxhkd
```

## Usage

Press your configured hotkey:

```text
CTRL + ALT + Q
```

Result:

* screenshot is captured
* visible task is analyzed
* answer is sent to Telegram
* process exits

## Pipeline Overview

ScreenMind does not rely on one single prompt.

It uses a staged pipeline:

1. **Extractor**

   * extracts all visible text/code
   * separates task-relevant content from surrounding UI noise

2. **Classifier**

   * determines what kind of task is shown:

     * code output
     * code fix
     * code write
     * code bug explanation
     * logic
     * math
     * short question
     * unknown

3. **Router**

   * sends the task to the correct solving path

4. **Solver**

   * QA solver for reasoning tasks
   * code reconstruction + execution for Python output tasks

5. **Validator**

   * selects the most reliable final answer

6. **Formatter**

   * formats the final Telegram message

## Supported Task Types

ScreenMind currently works best with:

* Python code output questions
* short code understanding tasks
* code bug explanation tasks
* small logic questions
* short direct questions
* basic math tasks

It is less reliable when:

* the visible task is incomplete
* the screenshot cuts off crucial lines
* the image is too noisy or too small
* the task depends on hidden context outside the screenshot

## Configuration

### `.env` variables

```dotenv
OPENAI_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

OPENAI_MODEL=gpt-4.1-mini
OUTPUT_LANGUAGE=en

TELEGRAM_SEND_IMAGE=true

DEFAULT_IMAGE_DIR=images
DEFAULT_LOG_DIR=logs
DEFAULT_PROMPT_PATH=prompts/default_prompt.txt

LOG_LEVEL=INFO
```

### `OUTPUT_LANGUAGE`

Controls the language of reasoning-based answers.

Examples:

```dotenv
OUTPUT_LANGUAGE=en
```

```dotenv
OUTPUT_LANGUAGE=ru
```

```dotenv
OUTPUT_LANGUAGE=es
```

This affects text answers produced by the QA reasoning path. Code execution output remains unchanged.

## Logs

Logs are stored in:

```text
logs/
```

Main files:

* `logs/launcher.log` — shell launcher lifecycle
* `logs/app.log` — Python pipeline logs

Useful commands:

```bash
tail -f logs/launcher.log
```

```bash
tail -f logs/app.log
```

```bash
tail -f logs/launcher.log logs/app.log
```

To watch only pipeline logs:

```bash
tail -f logs/app.log | grep --line-buffered "screen_tool.pipeline"
```

## Troubleshooting

### Telegram: `Unauthorized`

Your bot token is invalid.

Fix:

* regenerate token via BotFather
* update `TELEGRAM_BOT_TOKEN` in `.env`

### Telegram: `chat not found`

Usually means:

* you did not send `/start` to the bot
* `TELEGRAM_CHAT_ID` contains an invalid value
* `TELEGRAM_CHAT_ID` should be empty on first run if you want auto-detection

### Nothing happens on hotkey

Check that `sxhkd` is running:

```bash
ps aux | grep sxhkd
```

### Logs are not updating

Check:

```bash
tail -f logs/launcher.log
```

If launcher works but Python pipeline does not, also check:

```bash
tail -f logs/app.log
```

### The system says the condition is incomplete

This usually means:

* the task-relevant content is actually cut off
* or the classifier detected missing lines in code/task text

Try:

* making the code larger on screen
* ensuring the full task is visible
* removing surrounding clutter when possible

## Security Notes

* Never commit `.env`
* Telegram bot token gives full control over the bot
* OpenAI API key is billable
* This project is intended for local personal use

## Roadmap

* better isolation of task-relevant content from UI noise
* stronger support for bug explanation tasks
* support for more code languages
* better handling of partially visible tasks
* multiple hotkeys for different modes
* optional Dockerized execution sandbox

## License

MIT

```
```
