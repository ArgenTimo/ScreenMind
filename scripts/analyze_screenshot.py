import base64
import json
import mimetypes
import os
import sys
from datetime import datetime

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


def ensure_directory(directory_path: str) -> None:
    os.makedirs(directory_path, exist_ok=True)


def save_response_files(response_dir: str, image_path: str, prompt_text: str, model_name: str, output_text: str) -> str:
    ensure_directory(response_dir)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    txt_path = os.path.join(response_dir, f"response_{timestamp}.txt")
    json_path = os.path.join(response_dir, f"response_{timestamp}.json")

    with open(txt_path, "w", encoding="utf-8") as file:
        file.write(output_text)

    payload = {
        "timestamp": timestamp,
        "model": model_name,
        "image_path": image_path,
        "prompt": prompt_text,
        "response_text": output_text,
    }

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    return txt_path


def analyze_image(image_path: str, prompt_path: str, response_subfolder: str) -> str:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.analyze", level=config.log_level)

    logger.info("Starting screenshot analysis")
    logger.info("Image path: %s", image_path)
    logger.info("Prompt path: %s", prompt_path)
    logger.info("Response subfolder: %s", response_subfolder)

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
    response_dir = os.path.join(config.project_dir, response_subfolder)

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

    saved_txt_path = save_response_files(
        response_dir=response_dir,
        image_path=image_path,
        prompt_text=prompt_text,
        model_name=config.openai_model,
        output_text=output_text,
    )

    logger.info("Saved response text to: %s", saved_txt_path)
    return saved_txt_path


if __name__ == "__main__":
    config = load_config()

    if len(sys.argv) != 4:
        raise SystemExit(
            "Usage: python analyze_screenshot.py <image_path> <prompt_path> <response_subfolder>"
        )

    image_path = sys.argv[1]
    prompt_path = sys.argv[2]
    response_subfolder = sys.argv[3]

    saved_path = analyze_image(image_path, prompt_path, response_subfolder)
    print(saved_path)