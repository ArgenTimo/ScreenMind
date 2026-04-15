import os
import re
from dataclasses import dataclass
from dotenv import dotenv_values, load_dotenv


@dataclass
class AppConfig:
    project_dir: str
    default_image_dir: str
    default_log_dir: str
    default_prompt_path: str
    openai_api_key: str
    openai_model: str
    openai_transcription_model: str
    log_level: str
    telegram_bot_token: str
    telegram_chat_id: str
    telegram_send_image: bool
    output_language: str
    debug_telegram: bool
    session_hotkey_record: str
    session_hotkey_screenshot: str
    session_hotkey_submit: str


def _to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _session_hotkey_env(var: str, default: str) -> str:
    """Return env value or default if missing/blank. Ignores legacy AUDIO_OUTPUT_HOTKEY (was confusing f1 vs f8)."""
    raw = os.getenv(var)
    if raw is None or not str(raw).strip():
        return default
    return str(raw).strip().lower()


def _read_env_key_from_file(env_path: str, key: str) -> str | None:
    """Parse KEY=value from .env without relying solely on python-dotenv (handles odd lines, BOM)."""
    if not os.path.isfile(env_path):
        return None
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=\s*(.*?)\s*(?:#.*)?\s*$")
    with open(env_path, encoding="utf-8-sig") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            match = pattern.match(line)
            if match:
                val = match.group(1).strip()
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                elif val.startswith("'") and val.endswith("'"):
                    val = val[1:-1]
                return val
    return None


def load_config() -> AppConfig:
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_path = os.path.join(project_root, ".env")
    # .env must override pre-existing environment variables so edits apply reliably.
    load_dotenv(env_path, override=True)

    file_vals = dotenv_values(env_path, encoding="utf-8-sig") if os.path.isfile(env_path) else {}
    debug_raw = (file_vals or {}).get("DEBUG_TELEGRAM")
    if debug_raw is None or str(debug_raw).strip() == "":
        debug_raw = _read_env_key_from_file(env_path, "DEBUG_TELEGRAM")
    if debug_raw is not None:
        os.environ["DEBUG_TELEGRAM"] = str(debug_raw).strip()

    return AppConfig(
        project_dir=project_root,
        default_image_dir=os.getenv("DEFAULT_IMAGE_DIR", "images"),
        default_log_dir=os.getenv("DEFAULT_LOG_DIR", "logs"),
        default_prompt_path=os.getenv("DEFAULT_PROMPT_PATH", "prompts/default_prompt.txt"),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip(),
        openai_transcription_model=os.getenv("OPENAI_TRANSCRIPTION_MODEL", "whisper-1").strip(),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip(),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
        telegram_send_image=_to_bool((os.getenv("TELEGRAM_SEND_IMAGE") or "true").strip()),
        output_language=os.getenv("OUTPUT_LANGUAGE", "en").strip(),
        debug_telegram=_to_bool((os.getenv("DEBUG_TELEGRAM") or "false").strip()),
        session_hotkey_record=_session_hotkey_env("SESSION_HOTKEY_RECORD", "f8"),
        session_hotkey_screenshot=_session_hotkey_env("SESSION_HOTKEY_SCREENSHOT", "f9"),
        session_hotkey_submit=_session_hotkey_env("SESSION_HOTKEY_SUBMIT", "f2"),
    )