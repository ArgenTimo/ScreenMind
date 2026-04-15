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


def run_extractor(
    image_paths: str | list[str],
    supplemental_context: str = "",
) -> ExtractResult:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.pipeline.extractor", level=config.log_level)

    if isinstance(image_paths, str):
        paths = [image_paths]
    else:
        paths = list(image_paths)

    if not paths:
        raise ValueError("At least one image path is required")

    for p in paths:
        if not os.path.isfile(p):
            raise FileNotFoundError(f"Image file not found: {p}")

    if not config.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")

    client = OpenAI(api_key=config.openai_api_key)

    prompt_body = """
Extract all visible information from the image and separate task-relevant content from surrounding UI noise.

Return JSON with exactly these fields:
{
  "raw_text": "all visible text",
  "visible_code": "all visible code, preserve indentation exactly",
  "task_relevant_text": "only the text directly relevant to the task/question",
  "task_relevant_code": "only the code directly relevant to the task",
  "ui_hints": ["short ui hints"],
  "language_guess": "python or javascript or null",
  "confidence": 0.0,
  "missing_or_cut_off_parts": ["describe anything cut off or missing"],
  "code_appears_complete": true,
  "task_text_appears_complete": true
}

Rules:
- Extract only what is visible.
- Do not solve the task.
- Do not infer hidden text.
- Preserve code indentation exactly.
- If no code is visible, set visible_code and task_relevant_code to empty strings.
- If no clear task text is visible, set task_relevant_text to an empty string.
- code_appears_complete=true only if the task-relevant code is visible as a complete usable fragment.
- task_text_appears_complete=true only if the task-relevant text is fully visible enough to understand the task.
- confidence must be a number from 0 to 1.
- Output JSON only.
""".strip()

    extra = ""
    if supplemental_context.strip():
        extra = (
            "The following is transcribed audio from the user's session. Use it together with the screenshot(s).\n\n"
            + supplemental_context.strip()
            + "\n\n---\n\n"
        )
    if len(paths) > 1:
        extra += "Multiple screenshots are provided in chronological order; merge information across them as needed.\n\n---\n\n"

    prompt = extra + prompt_body

    logger.info("Extractor started for %s image(s): %s", len(paths), paths)

    content: list[dict] = [{"type": "input_text", "text": prompt}]
    for image_path in paths:
        mime_type = _detect_mime_type(image_path)
        base64_image = _encode_file_base64(image_path)
        content.append(
            {
                "type": "input_image",
                "image_url": f"data:{mime_type};base64,{base64_image}",
            }
        )

    response = client.responses.create(
        model=config.openai_model,
        input=[
            {
                "role": "user",
                "content": content,
            }
        ],
    )

    response_text = response.output_text.strip()
    logger.info("Extractor raw response length: %s", len(response_text))

    payload = json.loads(_extract_json_text(response_text))
    result = ExtractResult.model_validate(payload)

    logger.info(
        "Extractor finished: confidence=%s, language_guess=%s, visible_code_len=%s, task_relevant_code_len=%s, code_appears_complete=%s, task_text_appears_complete=%s",
        result.confidence,
        result.language_guess,
        len(result.visible_code),
        len(result.task_relevant_code),
        result.code_appears_complete,
        result.task_text_appears_complete,
    )

    return result