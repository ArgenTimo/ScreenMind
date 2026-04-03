#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="/home/skotwind/PycharmProjects/I_can_help"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
SCREENSHOT_SCRIPT="$PROJECT_DIR/scripts/take_screenshot.py"
ANALYZE_SCRIPT="$PROJECT_DIR/scripts/analyze_screenshot.py"
DEFAULT_PROMPT_PATH="$PROJECT_DIR/prompts/default_prompt.txt"
DEFAULT_RESPONSE_SUBFOLDER="responces"
DEFAULT_IMAGE_SUBFOLDER="images"
LOG_FILE="$PROJECT_DIR/logs/launcher.log"

mkdir -p "$PROJECT_DIR/logs"
touch "$LOG_FILE"

{
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Launcher started"

  IMAGE_SUBFOLDER="${1:-$DEFAULT_IMAGE_SUBFOLDER}"
  PROMPT_PATH="${2:-$DEFAULT_PROMPT_PATH}"
  RESPONSE_SUBFOLDER="${3:-$DEFAULT_RESPONSE_SUBFOLDER}"

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] IMAGE_SUBFOLDER=$IMAGE_SUBFOLDER"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] PROMPT_PATH=$PROMPT_PATH"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] RESPONSE_SUBFOLDER=$RESPONSE_SUBFOLDER"

  IMAGE_PATH="$("$VENV_PYTHON" "$SCREENSHOT_SCRIPT" "$IMAGE_SUBFOLDER")"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Screenshot created: $IMAGE_PATH"

  RESPONSE_PATH="$("$VENV_PYTHON" "$ANALYZE_SCRIPT" "$IMAGE_PATH" "$PROMPT_PATH" "$RESPONSE_SUBFOLDER")"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Analysis saved: $RESPONSE_PATH"

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Launcher finished successfully"
} >> "$LOG_FILE" 2>&1