import base64
import mimetypes
import os
import sys

from openai import OpenAI

from common.config import load_config
from common.logger import setup_logger


def read_text_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read().strip()


def encode_file_base64(file_path: str) -> str:
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


def detect_mime_type(file_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        return "image/png"
    return mime_type


def analyze_image(image_path: str, prompt_path: str) -> str:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.analyze", level=config.log_level)

    logger.info("Starting screenshot analysis")
    logger.info("Image path: %s", image_path)
    logger.info("Prompt path: %s", prompt_path)

    if not os.path.isfile(image_path):
        logger.error("Image file not found: %s", image_path)
        raise FileNotFoundError(f"Image file not found: {image_path}")

    if not os.path.isfile(prompt_path):
        logger.error("Prompt file not found: %s", prompt_path)
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    if not config.openai_api_key:
        logger.error("OPENAI_API_KEY is missing in .env")
        raise RuntimeError("OPENAI_API_KEY is not set in .env")

    prompt_text = read_text_file(prompt_path)
    base64_image = encode_file_base64(image_path)
    mime_type = detect_mime_type(image_path)

    logger.info("Loaded prompt successfully")
    logger.info("Detected mime type: %s", mime_type)
    logger.info("Using model: %s", config.openai_model)

    client = OpenAI(api_key=config.openai_api_key)

    response = client.responses.create(
        model=config.openai_model,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt_text,
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:{mime_type};base64,{base64_image}",
                    },
                ],
            }
        ],
    )

    output_text = response.output_text.strip()
    if not output_text:
        output_text = "Model returned an empty text response."

    logger.info("Received response from model")
    logger.info("Response length: %s characters", len(output_text))

    return output_text


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: python analyze_screenshot.py <image_path> <prompt_path>"
        )

    image_path = sys.argv[1]
    prompt_path = sys.argv[2]

    result_text = analyze_image(image_path, prompt_path)
    print(result_text)