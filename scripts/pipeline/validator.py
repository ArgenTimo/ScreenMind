import os

from common.config import load_config
from common.logger import setup_logger
from common.schemas import (
    ClassifyResult,
    CodeExecutionResult,
    CodeReconstructionResult,
    ExtractResult,
    FinalAnswer,
    QASolverResult,
)


def build_incomplete_condition_answer(classify_result: ClassifyResult, extract_result: ExtractResult) -> FinalAnswer:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.pipeline.validator", level=config.log_level)

    if extract_result.task_relevant_code.strip() and extract_result.code_appears_complete:
        logger.info("Validator ignored incomplete UI because task-relevant code is complete")
        return FinalAnswer(
            answer="Internal routing error: code path should have continued.",
            answer_kind="internal_error",
            confidence=min(classify_result.confidence, extract_result.confidence),
            source="validator",
        )

    message = "Condition appears incomplete."
    if extract_result.missing_or_cut_off_parts:
        message = f"Condition appears incomplete: {'; '.join(extract_result.missing_or_cut_off_parts)}"

    logger.info("Validator produced incomplete condition answer")

    return FinalAnswer(
        answer=message,
        answer_kind="fallback",
        confidence=min(classify_result.confidence, extract_result.confidence),
        source="validator",
    )


def validate_qa_answer(qa_result: QASolverResult, classify_result: ClassifyResult) -> FinalAnswer:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.pipeline.validator", level=config.log_level)

    answer = qa_result.final_answer.strip()
    if not answer:
        answer = "Could not determine the answer reliably."

    logger.info("Validator accepted QA answer")

    return FinalAnswer(
        answer=answer,
        answer_kind=qa_result.answer_type,
        confidence=min(qa_result.confidence, classify_result.confidence),
        source="qa_solver",
    )


def build_from_code_execution(
    classify_result: ClassifyResult,
    code_result: CodeReconstructionResult,
    execution_result: CodeExecutionResult,
) -> FinalAnswer:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.pipeline.validator", level=config.log_level)

    if execution_result.status == "ok":
        answer = execution_result.stdout if execution_result.stdout else ""
        if not answer:
            answer = "Program executed successfully with no output."

        logger.info("Validator selected execution stdout as final answer")

        return FinalAnswer(
            answer=answer,
            answer_kind="execution_output",
            confidence=min(classify_result.confidence, code_result.confidence),
            source="code_executor",
        )

    if classify_result.task_type in {"code_fix", "code_write"} and code_result.code.strip():
        logger.info("Validator returned code because execution failed but code may still be the requested output")
        return FinalAnswer(
            answer=code_result.code,
            answer_kind=f"{(code_result.language or 'text')}_code",
            confidence=min(classify_result.confidence, code_result.confidence),
            source="code_reconstructor",
        )

    error_text = execution_result.stderr.strip() or "Code execution failed."
    logger.info("Validator returned execution error as final answer")

    return FinalAnswer(
        answer=error_text,
        answer_kind="execution_error",
        confidence=min(classify_result.confidence, code_result.confidence),
        source="code_executor",
    )


def build_code_without_execution(
    classify_result: ClassifyResult,
    code_result: CodeReconstructionResult,
) -> FinalAnswer:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.pipeline.validator", level=config.log_level)

    logger.info("Validator returned code without execution")

    return FinalAnswer(
        answer=code_result.code.strip() if code_result.code.strip() else "Could not reconstruct code reliably.",
        answer_kind=f"{(code_result.language or 'text')}_code",
        confidence=min(classify_result.confidence, code_result.confidence),
        source="code_reconstructor",
    )