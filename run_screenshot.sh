#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="/home/skotwind/PycharmProjects/I_can_help"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
SCREENSHOT_SCRIPT="$PROJECT_DIR/scripts/take_screenshot.py"
ANALYZE_SCRIPT="$PROJECT_DIR/scripts/analyze_screenshot.py"
PROMPT_PATH="$PROJECT_DIR/prompts/default_prompt.txt"
RESPONSE_DIR="$PROJECT_DIR/responces"

TARGET_FOLDER="${1:-images}"

if [ -f "$HOME/.openai_api_key" ]; then
    export OPENAI_API_KEY="$(cat "$HOME/.openai_api_key")"
fi

IMAGE_PATH="$("$VENV_PYTHON" "$SCREENSHOT_SCRIPT" "$TARGET_FOLDER")"
"$VENV_PYTHON" "$ANALYZE_SCRIPT" "$IMAGE_PATH" "$PROMPT_PATH" "$RESPONSE_DIR"