#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
LISTENER_SCRIPT="$PROJECT_DIR/scripts/audio_output_recorder.py"
LOG_FILE="$PROJECT_DIR/logs/audio_listener_launcher.log"

mkdir -p "$PROJECT_DIR/logs"
touch "$LOG_FILE"

{
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting audio output listener"
  exec "$VENV_PYTHON" "$LISTENER_SCRIPT"
} >> "$LOG_FILE" 2>&1