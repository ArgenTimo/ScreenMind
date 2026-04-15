import logging
import os
import threading
from logging.handlers import RotatingFileHandler

_service_handler: RotatingFileHandler | None = None
_service_handler_lock = threading.Lock()


def _service_log_handler(logs_dir: str, log_format: logging.Formatter) -> RotatingFileHandler:
    global _service_handler
    with _service_handler_lock:
        if _service_handler is None:
            os.makedirs(logs_dir, exist_ok=True)
            path = os.path.join(logs_dir, "service.log")
            _service_handler = RotatingFileHandler(
                filename=path,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            _service_handler.setFormatter(log_format)
        return _service_handler


def setup_logger(logs_dir: str, logger_name: str = "screen_tool", level: str = "INFO") -> logging.Logger:
    os.makedirs(logs_dir, exist_ok=True)

    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if logger.handlers:
        return logger

    log_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        filename=os.path.join(logs_dir, "app.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(log_format)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(_service_log_handler(logs_dir, log_format))
    logger.propagate = False

    return logger