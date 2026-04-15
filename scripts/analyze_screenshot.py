import os
import sys

from common.config import load_config
from common.logger import setup_logger
from pipeline.formatter import format_for_telegram
from pipeline.orchestrator import run_pipeline_session
from send_telegram import send_message


def _format_debug_section(image_paths: list[str], audio_paths: list[str], transcript: str) -> str:
    lines = [
        "--- Debug: inputs ---",
        f"Images ({len(image_paths)}):",
    ]
    for p in image_paths:
        lines.append(f"  • {p}")
    lines.append(f"Audio ({len(audio_paths)}):")
    for p in audio_paths:
        lines.append(f"  • {p}")
    lines.append("--- Transcriptions (Whisper) ---")
    if transcript.strip():
        lines.append(transcript.strip())
    else:
        lines.append("(none)")
    lines.append("--- Pipeline response ---")
    return "\n".join(lines)


def _append_debug_if_enabled(
    config,
    body: str,
    image_paths: list[str],
    audio_paths: list[str],
    transcript: str,
) -> str:
    if not config.debug_telegram:
        return body
    return _format_debug_section(image_paths, audio_paths, transcript) + "\n\n" + body


def delete_capture_files(paths: list[str]) -> None:
    for p in paths:
        if os.path.isfile(p):
            os.remove(p)


def validate_session_files(image_paths: list[str], audio_paths: list[str]) -> None:
    """Ensure every path exists before one batched pipeline run."""
    for path in image_paths:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Image file not found: {path}")
    for path in audio_paths:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Audio file not found: {path}")


def analyze_image(image_path: str, prompt_path: str) -> str:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.analyze", level=config.log_level)

    logger.info("Starting screenshot analysis")
    logger.info("DEBUG_TELEGRAM=%s (from .env after override)", config.debug_telegram)
    logger.info("Image path: %s", image_path)
    logger.info("Prompt path is ignored because pipeline prompts are internal: %s", prompt_path)

    if not os.path.isfile(image_path):
        logger.error("Image file not found: %s", image_path)
        raise FileNotFoundError(f"Image file not found: {image_path}")

    final_answer, transcript = run_pipeline_session([image_path], [])
    message = format_for_telegram(final_answer)
    message = _append_debug_if_enabled(config, message, [image_path], [], transcript)

    logger.info("Analysis finished: answer_kind=%s source=%s confidence=%s", final_answer.answer_kind, final_answer.source, final_answer.confidence)
    if config.debug_telegram:
        logger.info("Debug block included in stdout/CLI output (length %s chars)", len(message))

    return message


def analyze_session(image_paths: list[str], audio_paths: list[str], prompt_path: str) -> str:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.analyze", level=config.log_level)

    logger.info("Starting session analysis")
    logger.info("DEBUG_TELEGRAM=%s", config.debug_telegram)
    logger.info("Images: %s", image_paths)
    logger.info("Audio: %s", audio_paths)
    logger.info("Prompt path is ignored because pipeline prompts are internal: %s", prompt_path)

    validate_session_files(image_paths, audio_paths)

    final_answer, transcript = run_pipeline_session(image_paths, audio_paths)
    message = format_for_telegram(final_answer)
    message = _append_debug_if_enabled(config, message, image_paths, audio_paths, transcript)

    logger.info("Session analysis finished: answer_kind=%s source=%s confidence=%s", final_answer.answer_kind, final_answer.source, final_answer.confidence)

    return message


def send_session_to_telegram(image_paths: list[str], audio_paths: list[str], prompt_path: str) -> None:
    """Run session pipeline, send to Telegram. When DEBUG_TELEGRAM, sends two messages (debug, then answer). Deletes inputs only when DEBUG_TELEGRAM is false."""
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.analyze", level=config.log_level)

    logger.info("send_session_to_telegram: images=%s audio=%s DEBUG_TELEGRAM=%s", image_paths, audio_paths, config.debug_telegram)

    validate_session_files(image_paths, audio_paths)

    logger.info(
        "Running batched session pipeline: %s image(s) in one extractor request, %s WAV(s) transcribed then merged into context",
        len(image_paths),
        len(audio_paths),
    )
    final_answer, transcript = run_pipeline_session(image_paths, audio_paths)
    body = format_for_telegram(final_answer)
    logger.info("Pipeline done: answer_kind=%s len(answer)=%s", final_answer.answer_kind, len(body))

    if config.debug_telegram:
        debug_text = _format_debug_section(image_paths, audio_paths, transcript)
        logger.info("Sending Telegram message 1/2 (debug inputs, len=%s)", len(debug_text))
        send_message("[Session analysis · debug]\n\n" + debug_text)
        logger.info("Sending Telegram message 2/2 (answer only, len=%s)", len(body))
        send_message("[Session analysis · answer]\n\n" + body)
        logger.info("DEBUG_TELEGRAM=true: skipping deletion of session files until service restart")
    else:
        combined = _append_debug_if_enabled(config, body, image_paths, audio_paths, transcript)
        logger.info("Sending single Telegram message (len=%s)", len(combined))
        send_message("[Session analysis]\n\n" + combined)
        logger.info("Deleting session capture files after successful send")
        delete_capture_files(image_paths + audio_paths)


def send_screen_hotkey_to_telegram(image_path: str, prompt_path: str) -> None:
    """Ctrl+Alt+Q path: pipeline + Telegram. When DEBUG_TELEGRAM, two messages. Does not delete image when DEBUG_TELEGRAM (caller removes file)."""
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.analyze", level=config.log_level)

    logger.info("send_screen_hotkey_to_telegram: image=%s DEBUG_TELEGRAM=%s", image_path, config.debug_telegram)
    logger.info("Prompt path ignored for pipeline internals: %s", prompt_path)

    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    logger.info("Running pipeline (screen hotkey)")
    final_answer, transcript = run_pipeline_session([image_path], [])
    body = format_for_telegram(final_answer)

    if config.debug_telegram:
        debug_text = _format_debug_section([image_path], [], transcript)
        logger.info("Sending Telegram 1/2 debug (len=%s)", len(debug_text))
        send_message("[Screen analysis · debug]\n\n" + debug_text)
        logger.info("Sending Telegram 2/2 answer (len=%s)", len(body))
        send_message("[Screen analysis · answer]\n\n" + body)
        logger.info("DEBUG_TELEGRAM=true: screenshot file not deleted by notify (caller should skip rm)")
    else:
        combined = _append_debug_if_enabled(config, body, [image_path], [], transcript)
        send_message("[Screen analysis]\n\n" + combined)
        logger.info("Sent single Telegram message (len=%s)", len(combined))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python analyze_screenshot.py <image_path> <prompt_path>")

    image_path = sys.argv[1]
    prompt_path = sys.argv[2]

    result_text = analyze_image(image_path, prompt_path)
    print(result_text)
