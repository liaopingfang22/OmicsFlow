"""
Production logging configuration for OmicsFlow.
Structured JSON logging with request tracing.
"""
import logging
import json
import sys
from datetime import datetime, timezone
from typing import Optional


class JSONFormatter(logging.Formatter):
    """JSON log formatter for production use."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "task_id"):
            log_entry["task_id"] = record.task_id

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(level: str = "INFO", json_format: bool = False):
    """Configure application logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)

    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))

    root_logger.addHandler(handler)

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return root_logger


class RequestLogger:
    """Middleware-compatible request logger with tracing."""

    def __init__(self, logger_name: str = "omicsflow.request"):
        self.logger = logging.getLogger(logger_name)

    def log_request(self, method: str, path: str, status_code: int,
                    duration_ms: float, user_id: Optional[str] = None,
                    request_id: Optional[str] = None):
        level = logging.WARNING if status_code >= 400 else logging.INFO
        extra = {}
        if request_id:
            extra["request_id"] = request_id
        if user_id:
            extra["user_id"] = user_id

        self.logger.log(
            level,
            f"{method} {path} {status_code} {duration_ms:.1f}ms",
            extra=extra,
        )


request_logger = RequestLogger()