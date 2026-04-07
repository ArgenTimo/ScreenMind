import json
import os

from openai import OpenAI

from common.config import load_config
from common.logger import setup_logger
from common.schemas import ClassifyResult, ExtractResult


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


def classify_task(extract_result: ExtractResult) -> ClassifyResult:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.pipeline.classifier", level=config.log_level)

    if not config.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")

    client = OpenAI(api_key=config.openai_api_key)

    prompt = f"""
You are a task classifier.

Given extracted screen data, classify the actual task shown on screen.

Return JSON with exactly these fields:
{{
  "task_type": "code_output | code_fix | code_write | code_review | code_bug_explanation | math | logic | quiz | short_question | unknown",
  "programming_language": "python or javascript or null",
  "requires_execution": true,
  "requires_reasoning": false,
  "is_condition_complete": true,
  "confidence": 0.0
}}

Rules:
- Focus on task_relevant_text and task_relevant_code first.
- Use code_output when task-relevant code mainly needs its exact output/result.
- Use code_fix when visible code must be corrected.
- Use code_write when the task asks to produce code.
- Use code_bug_explanation when visible code is shown together with prompts like:
  "what is wrong", "find the bug", "что тут не так", "что не так", "найди ошибку", "why is this wrong".
- Use code_review when the task asks to assess, review, or critique code quality/design.
- Use math, logic, quiz, short_question for non-code tasks.
- If some unrelated UI text is cut off but the actual task-relevant content is fully visible, set is_condition_complete=true.
- Set is_condition_complete=false only when the task-relevant content itself appears incomplete.
- confidence must be from 0 to 1.
- Output JSON only.

Extracted data:
{extract_result.model_dump_json(indent=2)}
""".strip()

    logger.info("Classifier started")

    response = client.responses.create(
        model=config.openai_model,
        input=prompt,
    )

    response_text = response.output_text.strip()
    logger.info("Classifier raw response length: %s", len(response_text))

    payload = json.loads(_extract_json_text(response_text))
    result = ClassifyResult.model_validate(payload)

    logger.info(
        "Classifier finished: task_type=%s, language=%s, requires_execution=%s, requires_reasoning=%s, complete=%s",
        result.task_type,
        result.programming_language,
        result.requires_execution,
        result.requires_reasoning,
        result.is_condition_complete,
    )

    return result