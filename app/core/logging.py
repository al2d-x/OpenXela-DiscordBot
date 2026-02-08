from __future__ import annotations

import json
import logging
import os
import uuid
from contextlib import contextmanager
from contextvars import ContextVar, Token
from logging.handlers import RotatingFileHandler
from typing import Any, Iterator


_event_id: ContextVar[str] = ContextVar("event_id", default="-")


def new_event_id() -> str:
    return uuid.uuid4().hex[:10]


def set_event_id(event_id: str) -> Token:
    return _event_id.set(event_id)


def reset_event_id(token: Token) -> None:
    _event_id.reset(token)


@contextmanager
def bind_event_id(event_id: str) -> Iterator[None]:
    token = _event_id.set(event_id)
    try:
        yield
    finally:
        _event_id.reset(token)


class _ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.event_id = _event_id.get()
        if not hasattr(record, "action"):
            record.action = "-"
        return True


class _KeyValueFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        extras: dict[str, Any] = {}
        for key in ("action", "guild_id", "user_id", "channel_id", "resource_id"):
            value = getattr(record, key, None)
            if value is not None and value != "-":
                extras[key] = value
        if extras:
            suffix = " ".join(f"{k}={v}" for k, v in extras.items())
            return f"{base} {suffix}"
        return base


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "event_id": getattr(record, "event_id", "-"),
        }
        for key in ("action", "guild_id", "user_id", "channel_id", "resource_id"):
            value = getattr(record, key, None)
            if value is not None and value != "-":
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str | None = None) -> None:
    log_level = (level or os.getenv("LOG_LEVEL", "WARNING")).upper()
    log_json = os.getenv("LOG_JSON", "false").strip().lower() == "true"
    log_to_file = os.getenv("LOG_TO_FILE", "false").strip().lower() == "true"
    log_file = os.getenv("LOG_FILE", "logs/app.log").strip() or "logs/app.log"
    log_max_bytes = int(os.getenv("LOG_MAX_BYTES", "10485760"))
    log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    audit_file = os.getenv("LOG_AUDIT_FILE", "").strip()

    formatter: logging.Formatter
    if log_json:
        formatter = _JsonFormatter()
    else:
        formatter = _KeyValueFormatter("%(asctime)s %(levelname)s %(name)s - %(message)s event_id=%(event_id)s")

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level, logging.WARNING))
    root.handlers.clear()

    context_filter = _ContextFilter()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(context_filter)
    root.addHandler(console_handler)

    if log_to_file:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=log_max_bytes, backupCount=log_backup_count, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(context_filter)
        root.addHandler(file_handler)

    if audit_file:
        audit_logger = logging.getLogger("app.audit")
        audit_logger.setLevel(logging.INFO)
        audit_logger.propagate = False
        audit_handler = RotatingFileHandler(
            audit_file, maxBytes=log_max_bytes, backupCount=log_backup_count, encoding="utf-8"
        )
        audit_handler.setFormatter(formatter)
        audit_handler.addFilter(context_filter)
        audit_logger.handlers.clear()
        audit_logger.addHandler(audit_handler)
