import json
import os

from openai import OpenAI

from common.config import load_config
from common.logger import setup_logger
from common.schemas import ClassifyResult, CodeReconstructionResult, ExtractResult


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


def reconstruct_code(extract_result: ExtractResult, classify_result: ClassifyResult) -> CodeReconstructionResult:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.pipeline.code_reconstructor", level=config.log_level)

    if not config.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")

    client = OpenAI(api_key=config.openai_api_key)

    prompt = f"""
You are reconstructing or solving a coding task from visible screen data.

Return JSON with exactly these fields:
{{
  "language": "python or javascript or null",
  "code": "code only",
  "task_intent": "short description",
  "confidence": 0.0
}}

Rules:
- Prefer task_relevant_code over visible_code.
- If task_type is code_output, reconstruct the exact task-relevant code and preserve indentation.
- If task_type is code_fix or code_write, return correct runnable code that solves the visible task.
- Do not add markdown fences.
- Do not add explanations.
- confidence must be from 0 to 1.
- Output JSON only.

Extracted data:
{extract_result.model_dump_json(indent=2)}

Classification:
{classify_result.model_dump_json(indent=2)}
""".strip()

    logger.info("Code reconstructor started")

    response = client.responses.create(
        model=config.openai_model,
        input=prompt,
    )

    response_text = response.output_text.strip()
    logger.info("Code reconstructor raw response length: %s", len(response_text))

    payload = json.loads(_extract_json_text(response_text))
    result = CodeReconstructionResult.model_validate(payload)

    logger.info(
        "Code reconstructor finished: language=%s confidence=%s code_len=%s",
        result.language,
        result.confidence,
        len(result.code),
    )

    return result