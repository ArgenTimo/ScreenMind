import json
import os

from openai import OpenAI

from common.config import load_config
from common.logger import setup_logger
from common.schemas import ClassifyResult, ExtractResult, QASolverResult


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


def solve_qa_task(extract_result: ExtractResult, classify_result: ClassifyResult) -> QASolverResult:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.pipeline.qa_solver", level=config.log_level)

    if not config.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")

    client = OpenAI(api_key=config.openai_api_key)

    prompt = f"""
Solve the task using only the visible extracted content.

Return JSON with exactly these fields:
{{
  "final_answer": "final answer only",
  "answer_type": "text | number | boolean | short_code",
  "confidence": 0.0,
  "notes": "short note"
}}

Rules:
- Use only visible content.
- Do not invent hidden conditions.
- If the condition is incomplete, say that in final_answer.
- Keep final_answer minimal.
- confidence must be from 0 to 1.
- Output JSON only.

When task_type is code_bug_explanation:
- identify the main bug or flaw
- explain only the relevant issue
- suggest the minimal correct fix
- do not discuss style unless style is the bug

Extracted data:
{extract_result.model_dump_json(indent=2)}

Classification:
{classify_result.model_dump_json(indent=2)}
""".strip()

    logger.info("QA solver started")

    response = client.responses.create(
        model=config.openai_model,
        input=prompt,
    )

    response_text = response.output_text.strip()
    logger.info("QA solver raw response length: %s", len(response_text))

    payload = json.loads(_extract_json_text(response_text))
    result = QASolverResult.model_validate(payload)

    logger.info("QA solver finished: answer_type=%s confidence=%s", result.answer_type, result.confidence)

    return result