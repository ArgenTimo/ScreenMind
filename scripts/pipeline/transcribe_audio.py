import os

from openai import OpenAI

from common.config import load_config
from common.logger import setup_logger


def transcribe_wav_files(wav_paths: list[str]) -> str:
    if not wav_paths:
        return ""

    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.transcribe", level=config.log_level)

    if not config.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")

    client = OpenAI(api_key=config.openai_api_key)
    parts: list[str] = []

    for path in sorted(wav_paths):
        logger.info("Transcribing: %s", path)
        with open(path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(model=config.openai_transcription_model, file=audio_file)
        parts.append(f"[{os.path.basename(path)}]\n{transcript.text.strip()}")

    return "\n\n".join(parts)
