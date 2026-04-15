# ScreenMind

ScreenMind is a local Linux utility that captures what is on your screen (and optionally system audio), runs a multi-step LLM pipeline, and delivers the answer in **Telegram**.

It is aimed at short, on-screen tasks (code quizzes, logic, math, small questions). Everything runs **on demand**: there is no always-on Telegram bot server in the default setup.

---

## What you can run

| Flow | What it does |
|------|----------------|
| **Screen hotkey** | One screenshot → pipeline → Telegram (process exits). |
| **Session listener** (optional) | Record audio (F8), take screenshots (F9), then send **all** captures to the pipeline with **F2**. |

---

## Requirements

- **OS:** Linux (X11; global hotkeys via `pynput` / `sxhkd` expect a normal desktop session).
- **Python:** 3.10 or newer.
- **Network:** For OpenAI and Telegram APIs.
- **Audio capture (session mode only):** `ffmpeg`, PulseAudio/PipeWire (`pactl`).

---

## Quick setup (new users)

### 1. Clone and enter the project

```bash
git clone <your-repo-url> screenmind
cd screenmind
```

### 2. Virtual environment and dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

- `OPENAI_API_KEY` — from [OpenAI](https://platform.openai.com/api-keys)
- `TELEGRAM_BOT_TOKEN` — from [@BotFather](https://t.me/BotFather) (`/newbot`)

Leave `TELEGRAM_CHAT_ID` empty on first use; the app can fill it after you message the bot (see below).

**Save the file** after editing; the app reads the real file on disk.

### 4. Telegram bot (once)

1. Open your bot in Telegram and send `/start` (needed for automatic `chat_id` discovery).
2. Run a one-shot analysis (next step). On first success, `TELEGRAM_CHAT_ID` may be written into `.env`.

### 5. Test the pipeline (one screenshot)

From the project directory:

```bash
./run_screenshot.sh
```

You should get a new screenshot under `images/`, then a message in Telegram with the answer.

---

## Global hotkey: `Ctrl+Alt+Q` → analyze screen

Install `sxhkd` (example on Debian/Ubuntu):

```bash
sudo apt update
sudo apt install sxhkd
```

Create or edit `~/.config/sxhkd/sxhkdrc` and add (use **your** project path):

```text
ctrl + alt + q
    /home/YOUR_USER/path/to/screenmind/run_screenshot.sh
```

Start `sxhkd` (or add it to your session autostart). Then **Ctrl+Alt+Q** runs `run_screenshot.sh`: capture → pipeline → Telegram.

---

## Session mode: audio + screenshots + batch send

For **hold F8** (record system audio), **F9** (screenshot), and **F2** (send everything to the pipeline), start the long-running listener:

```bash
./run_audio_output_listener.sh
```

Keep this terminal open (or run it under `tmux`/systemd). On startup it clears previous captures in `images/` and `audio_captures/` (keeps `.gitkeep` files).

| Key | Action |
|-----|--------|
| **F8** (hold) | Record system output to `audio_captures/*.wav` |
| **F9** | Save a screenshot under `DEFAULT_IMAGE_DIR` (default `images/`) |
| **F2** | Transcribe audio (Whisper), run the pipeline on **all** PNGs + WAVs, send result to Telegram |

With `DEBUG_TELEGRAM=true`, Telegram receives **two** messages (debug bundle, then answer), and files are **not** deleted after a successful run; they are cleared on the **next listener start**.

---

## Optional: screenshot file only (no LLM)

`run_screenshot_save_only.sh` saves a PNG using the same capture code as the main flow, without analysis. You can bind it in `sxhkd` if you only want a file on disk.

---

## Configuration (`.env`)

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required). |
| `OPENAI_MODEL` | Model id for vision + text (default in example may vary). |
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather. |
| `TELEGRAM_CHAT_ID` | Your chat id; can be auto-filled on first run. |
| `TELEGRAM_SEND_IMAGE` | If `true`, `run_screenshot.sh` also sends the screenshot image to Telegram after text. |
| `OUTPUT_LANGUAGE` | Language for reasoning-style answers (e.g. `en`, `ru`). |
| `DEFAULT_IMAGE_DIR` | Where F9 / screenshots are stored (default `images`). |
| `DEBUG_TELEGRAM` | `true`: extra Telegram debug messages + keep session files until listener restart; `false`: normal behavior. |
| `LOG_LEVEL` | e.g. `INFO` or `DEBUG`. |

Copy from `.env.example` and adjust. Do not commit `.env`.

---

## Logs

| File | Content |
|------|---------|
| `logs/service.log` | **Recommended:** merged stream from Python components (listener, pipeline, Telegram). |
| `logs/app.log` | Rotating log for `screen_tool` loggers. |
| `logs/launcher.log` | `run_screenshot.sh` lifecycle. |
| `logs/audio_listener_launcher.log` | Wrapper output for `run_audio_output_listener.sh`. |

**Watch live activity:**

```bash
tail -f logs/service.log
```

You can also follow multiple files:

```bash
tail -f logs/service.log logs/audio_listener_launcher.log
```

---

## Pipeline (short)

1. **Extractor** — reads text/code from image(s); optional Whisper transcript for session mode.  
2. **Classifier** — task type.  
3. **Solver** — QA and/or Python execution when appropriate.  
4. **Validator / formatter** — final answer text for Telegram.

---

## Troubleshooting

- **`DEBUG_TELEGRAM` looks false in logs** — Ensure the line is **saved** in `.env`, then restart the listener.  
- **Nothing on hotkey** — Check `sxhkd` is running: `pgrep -a sxhkd`.  
- **Listener exits immediately** — See `logs/audio_listener_launcher.log` and `logs/service.log`; `pynput` needs a display (`DISPLAY`, typically X11).  
- **No audio in session mode** — Install `ffmpeg`; ensure `pactl`/PipeWire monitor works on your system.  
- **Telegram errors** — Confirm `/start` was sent to the bot; token and chat id are correct.

---

## Security

- Never commit `.env` or share API keys.  
- Bot token and OpenAI key are sensitive; this tool is intended for **local personal use**.

---

## License

MIT
