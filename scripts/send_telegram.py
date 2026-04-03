import os
import sys
from typing import List, Optional

import requests

from common.config import load_config
from common.logger import setup_logger


def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_env_path() -> str:
    return os.path.join(get_project_root(), ".env")


def update_env_value(key: str, value: str) -> None:
    env_path = get_env_path()

    if not os.path.exists(env_path):
        with open(env_path, "w", encoding="utf-8") as file:
            file.write(f"{key}={value}\n")
        return

    with open(env_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    found = False
    updated_lines: List[str] = []

    for line in lines:
        if line.startswith(f"{key}="):
            updated_lines.append(f"{key}={value}\n")
            found = True
        else:
            updated_lines.append(line)

    if not found:
        updated_lines.append(f"{key}={value}\n")

    with open(env_path, "w", encoding="utf-8") as file:
        file.writelines(updated_lines)


def split_text(text: str, chunk_size: int = 3500) -> List[str]:
    cleaned_text = text.strip()
    if not cleaned_text:
        return ["Empty message"]

    result: List[str] = []
    start = 0

    while start < len(cleaned_text):
        result.append(cleaned_text[start:start + chunk_size])
        start += chunk_size

    return result


def validate_bot_token(bot_token: str, logger) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    response = requests.get(url, timeout=30)

    if not response.ok:
        logger.error("Telegram getMe failed: %s", response.text)
        raise RuntimeError(
            "Telegram bot token is invalid or rejected by Telegram. "
            "Check TELEGRAM_BOT_TOKEN in .env."
        )

    logger.info("Telegram token validated successfully")


def clear_webhook_if_needed(bot_token: str, logger) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
    response = requests.get(url, timeout=30)

    if response.ok:
        logger.info("Telegram webhook cleared or was not set")
    else:
        logger.warning("Telegram deleteWebhook failed: %s", response.text)


def try_resolve_chat_id(bot_token: str, logger) -> Optional[str]:
    clear_webhook_if_needed(bot_token, logger)

    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url, timeout=30)

    if not response.ok:
        logger.error("Telegram getUpdates failed: %s", response.text)
        raise RuntimeError(
            "Failed to read updates from Telegram. "
            "Open your bot in Telegram, send /start, then try again."
        )

    payload = response.json()
    updates = payload.get("result", [])

    logger.info("Telegram returned %s update(s)", len(updates))

    private_chat_candidates: List[str] = []

    for update in reversed(updates):
        message = update.get("message")
        if not isinstance(message, dict):
            continue

        chat = message.get("chat", {})
        if not isinstance(chat, dict):
            continue

        chat_id = chat.get("id")
        chat_type = chat.get("type")
        text = message.get("text", "")

        if chat_id is None:
            continue

        if chat_type == "private":
            logger.info("Found private update chat_id=%s text=%s", chat_id, text)
            private_chat_candidates.append(str(chat_id))

    if private_chat_candidates:
        return private_chat_candidates[0]

    return None


def ensure_chat_id(config, logger) -> str:
    if config.telegram_chat_id:
        logger.info("Using TELEGRAM_CHAT_ID from .env: %s", config.telegram_chat_id)
        return config.telegram_chat_id

    logger.info("TELEGRAM_CHAT_ID is empty, trying to resolve it automatically")

    chat_id = try_resolve_chat_id(config.telegram_bot_token, logger)

    if not chat_id:
        raise RuntimeError(
            "Could not determine Telegram chat id automatically. "
            "Open the bot in Telegram, send /start, then run the script again."
        )

    update_env_value("TELEGRAM_CHAT_ID", chat_id)
    logger.info("Resolved and saved TELEGRAM_CHAT_ID=%s", chat_id)

    return chat_id


def send_message(text: str) -> None:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.telegram", level=config.log_level)

    if not config.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in .env")

    validate_bot_token(config.telegram_bot_token, logger)
    chat_id = ensure_chat_id(config, logger)

    url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"

    chunks = split_text(text)
    logger.info("Sending Telegram message in %s chunk(s)", len(chunks))

    for index, chunk in enumerate(chunks, start=1):
        response = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "text": chunk,
            },
            timeout=60,
        )

        if not response.ok:
            logger.error("Telegram sendMessage failed on chunk %s: %s", index, response.text)
            raise RuntimeError(f"Telegram sendMessage failed: {response.text}")

    logger.info("Telegram message sent successfully")


def send_photo(photo_path: str, caption: str = "") -> None:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.telegram", level=config.log_level)

    if not config.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in .env")

    validate_bot_token(config.telegram_bot_token, logger)
    chat_id = ensure_chat_id(config, logger)

    if not os.path.isfile(photo_path):
        raise FileNotFoundError(f"Photo file not found: {photo_path}")

    url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendPhoto"

    with open(photo_path, "rb") as photo_file:
        response = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "caption": caption,
            },
            files={
                "photo": photo_file,
            },
            timeout=120,
        )

    if not response.ok:
        logger.error("Telegram sendPhoto failed: %s", response.text)
        raise RuntimeError(f"Telegram sendPhoto failed: {response.text}")

    logger.info("Telegram photo sent successfully")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("Usage: python send_telegram.py text 'message' OR python send_telegram.py photo '/path/to/file.png'")

    mode = sys.argv[1]
    value = sys.argv[2]

    if mode == "text":
        send_message(value)
    elif mode == "photo":
        send_photo(value, "Screenshot")
    else:
        raise SystemExit("Mode must be 'text' or 'photo'")