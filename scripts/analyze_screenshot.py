import os
import sys

from common.config import load_config
from common.logger import setup_logger
from pipeline.formatter import format_for_telegram
from pipeline.orchestrator import run_pipeline


def analyze_image(image_path: str, prompt_path: str) -> str:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.analyze", level=config.log_level)

    logger.info("Starting screenshot analysis")
    logger.info("Image path: %s", image_path)
    logger.info("Prompt path is ignored because pipeline prompts are internal: %s", prompt_path)

    if not os.path.isfile(image_path):
        logger.error("Image file not found: %s", image_path)
        raise FileNotFoundError(f"Image file not found: {image_path}")

    final_answer = run_pipeline(image_path)
    message = format_for_telegram(final_answer)

    logger.info("Analysis finished: answer_kind=%s source=%s confidence=%s", final_answer.answer_kind, final_answer.source, final_answer.confidence)

    return message


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python analyze_screenshot.py <image_path> <prompt_path>")

    image_path = sys.argv[1]
    prompt_path = sys.argv[2]

    result_text = analyze_image(image_path, prompt_path)
    print(result_text)