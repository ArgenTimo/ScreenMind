#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
SCREENSHOT_SCRIPT="$PROJECT_DIR/scripts/take_screenshot.py"
DEFAULT_PROMPT_PATH="$PROJECT_DIR/prompts/default_prompt.txt"
DEFAULT_IMAGE_SUBFOLDER="images"
LOG_FILE="$PROJECT_DIR/logs/launcher.log"
TMP_DIR="$PROJECT_DIR/logs/tmp"

mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$TMP_DIR"
touch "$LOG_FILE"

{
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Launcher started"

  IMAGE_SUBFOLDER="${1:-$DEFAULT_IMAGE_SUBFOLDER}"
  PROMPT_PATH="${2:-$DEFAULT_PROMPT_PATH}"

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] IMAGE_SUBFOLDER=$IMAGE_SUBFOLDER"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] PROMPT_PATH=$PROMPT_PATH"

  IMAGE_PATH="$("$VENV_PYTHON" "$SCREENSHOT_SCRIPT" "$IMAGE_SUBFOLDER")"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Screenshot created: $IMAGE_PATH"

  export SCREENSHOT_NOTIFY_IMAGE="$IMAGE_PATH"
  export SCREENSHOT_NOTIFY_PROMPT="$PROMPT_PATH"
  "$VENV_PYTHON" -c 'import os,sys; sys.path.insert(0,"scripts"); from analyze_screenshot import send_screen_hotkey_to_telegram; send_screen_hotkey_to_telegram(os.environ["SCREENSHOT_NOTIFY_IMAGE"], os.environ["SCREENSHOT_NOTIFY_PROMPT"])'
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Analysis and Telegram notify completed"

  SEND_IMAGE_FLAG="$(grep '^TELEGRAM_SEND_IMAGE=' "$PROJECT_DIR/.env" | cut -d= -f2- | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] SEND_IMAGE_FLAG=$SEND_IMAGE_FLAG"

  if [ "$SEND_IMAGE_FLAG" = "true" ]; then
      "$VENV_PYTHON" "$PROJECT_DIR/scripts/send_telegram.py" photo "$IMAGE_PATH"
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] Telegram image sent"
  fi

  SKIP_RM="$("$VENV_PYTHON" -c 'import sys; sys.path.insert(0,"scripts"); from common.config import load_config; print("1" if load_config().debug_telegram else "0")')"
  if [ "$SKIP_RM" != "1" ]; then
    rm -f "$IMAGE_PATH"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Screenshot file removed after successful send"
  else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] DEBUG_TELEGRAM=true: keeping screenshot on disk until service restart"
  fi

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Launcher finished successfully"
} >> "$LOG_FILE" 2>&1
