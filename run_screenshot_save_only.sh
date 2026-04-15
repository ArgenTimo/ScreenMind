#!/usr/bin/env bash
# Save-only screenshot: same capture path as run_screenshot.sh (take_screenshot.py), no LLM/Telegram.
# Bind in ~/.config/sxhkd/sxhkdrc, e.g.:
#   F9
#       /absolute/path/to/I_can_help/run_screenshot_save_only.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
SCREENSHOT_SCRIPT="$PROJECT_DIR/scripts/take_screenshot.py"
DEFAULT_IMAGE_SUBFOLDER="images"
LOG_FILE="$PROJECT_DIR/logs/screenshot_save_only.log"

mkdir -p "$PROJECT_DIR/logs"
touch "$LOG_FILE"

{
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Save-only screenshot started"
  IMAGE_SUBFOLDER="${1:-$DEFAULT_IMAGE_SUBFOLDER}"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] IMAGE_SUBFOLDER=$IMAGE_SUBFOLDER"
  IMAGE_PATH="$("$VENV_PYTHON" "$SCREENSHOT_SCRIPT" "$IMAGE_SUBFOLDER")"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Screenshot saved: $IMAGE_PATH"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Finished successfully"
} >> "$LOG_FILE" 2>&1
