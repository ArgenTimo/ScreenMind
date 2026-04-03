import os
import sys
from typing import Any

import requests
from dotenv import dotenv_values

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")


def read_env_value(key: str) -> str:
    values = dotenv_values(ENV_PATH)
    return str(values.get(key, "") or "").strip()


def update_env_value(key: str, value: str) -> None:
    if not os.path.isfile(ENV_PATH):
        raise FileNotFoundError(f".env file not found: {ENV_PATH}")

    with open(ENV_PATH, "r", encoding="utf-8") as file:
        lines = file.readlines()

    updated = False
    new_lines = []

    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"{key}={value}\n")

    with open(ENV_PATH, "w", encoding="utf-8") as file:
        file.writelines(new_lines)


def main() -> None:
    token = read_env_value("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing in .env")

    print("1. Open Telegram.")
    print("2. Find your bot.")
    print("3. Send /start to the bot.")
    input("After that, press Enter here... ")

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    response = requests.get(url, timeout=60)

    if not response.ok:
        raise RuntimeError(f"getUpdates failed: {response.text}")

    payload: dict[str, Any] = response.json()
    results = payload.get("result", [])

    found = []
    for item in results:
        message = item.get("message", {})
        chat = message.get("chat", {})
        text = message.get("text", "")
        chat_id = chat.get("id")
        username = chat.get("username", "")
        first_name = chat.get("first_name", "")
        chat_type = chat.get("type", "")

        if chat_id is not None:
            found.append(
                {
                    "chat_id": str(chat_id),
                    "username": username,
                    "first_name": first_name,
                    "chat_type": chat_type,
                    "text": text,
                }
            )

    if not found:
        print("No chats found in getUpdates.")
        print("Make sure you started the bot and sent at least one message.")
        sys.exit(1)

    print("\nFound chats:\n")
    for index, item in enumerate(found, start=1):
        print(
            f"{index}. chat_id={item['chat_id']} | "
            f"type={item['chat_type']} | "
            f"username={item['username']} | "
            f"first_name={item['first_name']} | "
            f"last_text={item['text']}"
        )

    choice = input("\nEnter the number of the chat to save into .env: ").strip()
    selected = found[int(choice) - 1]
    update_env_value("TELEGRAM_CHAT_ID", selected["chat_id"])

    print(f"Saved TELEGRAM_CHAT_ID={selected['chat_id']} into {ENV_PATH}")


if __name__ == "__main__":
    main()