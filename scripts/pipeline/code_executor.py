import os
import subprocess
import tempfile

from common.config import load_config
from common.logger import setup_logger
from common.schemas import CodeExecutionResult


def run_python_code(code: str, timeout_seconds: int = 5) -> CodeExecutionResult:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.pipeline.code_executor", level=config.log_level)

    logger.info("Python executor started")

    if not code.strip():
        logger.error("Executor received empty code")
        return CodeExecutionResult(
            status="error",
            stdout="",
            stderr="Empty code",
            returncode=1,
        )

    temp_path = ""

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as file:
            file.write(code)
            temp_path = file.name

        result = subprocess.run(
            ["python3", temp_path],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )

        execution_result = CodeExecutionResult(
            status="ok" if result.returncode == 0 else "error",
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip(),
            returncode=result.returncode,
        )

        logger.info(
            "Python executor finished: status=%s returncode=%s stdout_len=%s stderr_len=%s",
            execution_result.status,
            execution_result.returncode,
            len(execution_result.stdout),
            len(execution_result.stderr),
        )

        return execution_result

    except subprocess.TimeoutExpired:
        logger.error("Python executor timeout after %s seconds", timeout_seconds)
        return CodeExecutionResult(
            status="error",
            stdout="",
            stderr=f"Execution timed out after {timeout_seconds} seconds",
            returncode=124,
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)