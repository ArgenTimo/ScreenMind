#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
SCREENSHOT_SCRIPT="$PROJECT_DIR/scripts/take_screenshot.py"
ANALYZE_SCRIPT="$PROJECT_DIR/scripts/analyze_screenshot.py"
TELEGRAM_SCRIPT="$PROJECT_DIR/scripts/send_telegram.py"
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

  RESPONSE_TMP_FILE="$TMP_DIR/last_response.txt"
  "$VENV_PYTHON" "$ANALYZE_SCRIPT" "$IMAGE_PATH" "$PROMPT_PATH" > "$RESPONSE_TMP_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Analysis completed"

  MESSAGE_TEXT="$(cat "$RESPONSE_TMP_FILE")"
  "$VENV_PYTHON" "$TELEGRAM_SCRIPT" text $'[Screen analysis]\n\n'"$MESSAGE_TEXT"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Telegram text sent"

  SEND_IMAGE_FLAG="$("$VENV_PYTHON" -c 'from scripts.common.config import load_config; print("true" if load_config().telegram_send_image else "false")')"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] SEND_IMAGE_FLAG=$SEND_IMAGE_FLAG"

  if [ "$SEND_IMAGE_FLAG" = "true" ]; then
      "$VENV_PYTHON" "$TELEGRAM_SCRIPT" photo "$IMAGE_PATH"
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] Telegram image sent"
  fi

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Launcher finished successfully"
} >> "$LOG_FILE" 2>&1