from __future__ import annotations

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Any

from .settings import Settings

# LogRecord attributes that are not custom "extra" fields (approximate allowlist).
_BUILTIN_LOGRECORD_KEYS = frozenset(
    {
        "name",
        "msg",
        "args",
        "created",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "thread",
        "threadName",
        "exc_info",
        "exc_text",
        "stack_info",
        "taskName",
    }
)


class JsonFormatter(logging.Formatter):
    """Одна строка JSON на событие — удобно для Loki / ELK в Kubernetes."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in _BUILTIN_LOGRECORD_KEYS or key.startswith("_"):
                continue
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(settings: Settings) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(settings.log_level.upper())

    if settings.log_format == "json":
        fmt = JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S%z")
    else:
        fmt = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)
    root.addHandler(stream)

    if settings.log_file_path:
        max_bytes = max(1, settings.log_file_max_megabytes) * 1024 * 1024
        fh = RotatingFileHandler(
            settings.log_file_path,
            maxBytes=max_bytes,
            backupCount=max(1, settings.log_file_backup_count),
            encoding="utf-8",
        )
        fh.setFormatter(fmt)
        root.addHandler(fh)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "httpx"):
        logging.getLogger(name).setLevel(settings.log_level.upper())
