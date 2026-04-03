import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class AppConfig:
    project_dir: str
    default_image_dir: str
    default_response_dir: str
    default_log_dir: str
    default_prompt_path: str
    openai_api_key: str
    openai_model: str
    log_level: str


def load_config() -> AppConfig:
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_path = os.path.join(project_root, ".env")

    load_dotenv(env_path)

    project_dir = os.getenv("PROJECT_DIR", project_root)
    default_image_dir = os.getenv("DEFAULT_IMAGE_DIR", "images")
    default_response_dir = os.getenv("DEFAULT_RESPONSE_DIR", "responces")
    default_log_dir = os.getenv("DEFAULT_LOG_DIR", "logs")
    default_prompt_path = os.getenv("DEFAULT_PROMPT_PATH", "prompts/default_prompt.txt")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    log_level = os.getenv("LOG_LEVEL", "INFO")

    return AppConfig(
        project_dir=project_dir,
        default_image_dir=default_image_dir,
        default_response_dir=default_response_dir,
        default_log_dir=default_log_dir,
        default_prompt_path=default_prompt_path,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        log_level=log_level,
    )