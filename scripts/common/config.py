import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class AppConfig:
    project_dir: str
    default_image_dir: str
    default_log_dir: str
    default_prompt_path: str
    openai_api_key: str
    openai_model: str
    log_level: str
    telegram_bot_token: str
    telegram_chat_id: str
    telegram_send_image: bool


def _to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def load_config() -> AppConfig:
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_path = os.path.join(project_root, ".env")
    load_dotenv(env_path)

    return AppConfig(
        project_dir=project_root,
        default_image_dir=os.getenv("DEFAULT_IMAGE_DIR", "images"),
        default_log_dir=os.getenv("DEFAULT_LOG_DIR", "logs"),
        default_prompt_path=os.getenv("DEFAULT_PROMPT_PATH", "prompts/default_prompt.txt"),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip(),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip(),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
        telegram_send_image=_to_bool(os.getenv("TELEGRAM_SEND_IMAGE", "true")),
    )