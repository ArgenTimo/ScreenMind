import base64
import json
import mimetypes
import os

from openai import OpenAI

from common.config import load_config
from common.logger import setup_logger
from common.schemas import ExtractResult


def _detect_mime_type(file_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type
    return "image/png"


def _encode_file_base64(file_path: str) -> str:
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


def _extract_json_text(text: str) -> str:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        return cleaned[start:end + 1]

    raise ValueError("No JSON object found in model output")


def run_extractor(image_path: str) -> ExtractResult:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.pipeline.extractor", level=config.log_level)

    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    if not config.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")

    client = OpenAI(api_key=config.openai_api_key)
    mime_type = _detect_mime_type(image_path)
    base64_image = _encode_file_base64(image_path)

    prompt = """
Extract all visible information from the image and separate task-relevant content from interface noise.

Return JSON with exactly these fields:
{
  "raw_text": "all visible text",
  "visible_code": "all visible code if any",
  "task_relevant_text": "only the visible text that is relevant to the actual task or question",
  "task_relevant_code": "only the visible code relevant to the task, preserve indentation exactly",
  "irrelevant_ui_text": ["text that belongs to interface, menus, chat chrome, notebook chrome, headers, tabs, status bars, etc."],
  "ui_hints": ["short ui hints"],
  "language_guess": "python or javascript or null",
  "confidence": 0.0,
  "missing_or_cut_off_parts": ["describe cut off or missing areas"],
  "code_appears_complete": true,
  "task_text_appears_complete": true
}

Rules:
- Extract only what is visible.
- Do not solve the task.
- Separate interface noise from task-relevant content.
- If code is clearly visible and self-contained, set code_appears_complete=true even if unrelated UI text is cut off.
- If task-relevant text is enough to solve the task, set task_text_appears_complete=true.
- confidence must be from 0 to 1.
- Output JSON only.
""".strip()

    logger.info("Extractor started for image: %s", image_path)

    response = client.responses.create(
        model=config.openai_model,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt,
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:{mime_type};base64,{base64_image}",
                    },
                ],
            }
        ],
    )

    response_text = response.output_text.strip()
    logger.info("Extractor raw response length: %s", len(response_text))

    payload = json.loads(_extract_json_text(response_text))
    result = ExtractResult.model_validate(payload)

    logger.info(
        "Extractor finished: confidence=%s, language_guess=%s, task_code_len=%s, code_complete=%s, text_complete=%s",
        result.confidence,
        result.language_guess,
        len(result.task_relevant_code),
        result.code_appears_complete,
        result.task_text_appears_complete,
    )

    return result