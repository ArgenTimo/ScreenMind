import os

from common.config import load_config
from common.logger import setup_logger
from common.schemas import FinalAnswer
from pipeline.classifier import classify_task
from pipeline.code_executor import run_python_code
from pipeline.code_reconstructor import reconstruct_code
from pipeline.extractor import run_extractor
from pipeline.qa_solver import solve_qa_task
from pipeline.transcribe_audio import transcribe_wav_files
from pipeline.validator import (
    build_from_code_execution,
    build_incomplete_condition_answer,
    build_code_without_execution,
    validate_qa_answer,
)


def run_pipeline(image_path: str) -> FinalAnswer:
    final_answer, _transcript = run_pipeline_session([image_path], [])
    return final_answer


def run_pipeline_session(image_paths: list[str], audio_paths: list[str]) -> tuple[FinalAnswer, str]:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.pipeline.orchestrator", level=config.log_level)

    logger.info("Pipeline started for images=%s audio=%s", image_paths, audio_paths)

    transcript = transcribe_wav_files(audio_paths)
    extract_result = run_extractor(image_paths, supplemental_context=transcript)
    classify_result = classify_task(extract_result)

    has_complete_code = bool(extract_result.task_relevant_code.strip()) and extract_result.code_appears_complete
    code_like_task = classify_result.task_type in {"code_output", "code_fix", "code_write"}

    if not classify_result.task_relevant_content_complete and not (code_like_task and has_complete_code):
        logger.info("Pipeline stopped: task-relevant content incomplete")
        return build_incomplete_condition_answer(classify_result, extract_result), transcript

    if code_like_task:
        code_result = reconstruct_code(extract_result, classify_result)

        language = (code_result.language or classify_result.programming_language or extract_result.language_guess or "").strip().lower()

        if classify_result.requires_execution and language == "python":
            execution_result = run_python_code(code_result.code)
            final_answer = build_from_code_execution(classify_result, code_result, execution_result)
            logger.info("Pipeline finished through python execution path")
            return final_answer, transcript

        final_answer = build_code_without_execution(classify_result, code_result)
        logger.info("Pipeline finished through code without execution path")
        return final_answer, transcript

    if classify_result.task_type in {"code_bug_explanation", "code_review"}:
        qa_result = solve_qa_task(extract_result, classify_result)
        final_answer = validate_qa_answer(qa_result, classify_result)
        return final_answer, transcript

    qa_result = solve_qa_task(extract_result, classify_result)
    final_answer = validate_qa_answer(qa_result, classify_result)
    logger.info("Pipeline finished through QA path")
    return final_answer, transcript