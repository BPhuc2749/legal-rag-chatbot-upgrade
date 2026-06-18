import os
import json
import logging

from datetime import datetime, timezone
from typing import Any, Dict

from app.core.context import get_context


# =========================
# Config
# =========================

LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_FILE = os.getenv("LOG_FILE", "app.jsonl")


# =========================
# Logger Init
# =========================

def get_jsonl_logger(name: str = "app") -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # tránh duplicate handler
    if logger.handlers:
        return logger

    path = os.path.join(
        LOG_DIR,
        LOG_FILE
    )

    handler = logging.FileHandler(
        path,
        encoding="utf-8"
    )

    handler.setLevel(logging.INFO)

    # chỉ ghi raw JSON line
    handler.setFormatter(
        logging.Formatter("%(message)s")
    )

    logger.addHandler(handler)

    return logger


logger = get_jsonl_logger()


# =========================
# Utilities
# =========================

def now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


# =========================
# Core Logging
# =========================

def log_event(
    event: Dict[str, Any],
    logger_instance: logging.Logger = logger
):
    # timestamp
    event.setdefault(
        "ts",
        now_iso()
    )

    # inject context
    context = get_context()

    for key, value in context.items():
        event.setdefault(
            key,
            value
        )

    # default event
    event.setdefault(
        "event",
        "unknown"
    )

    # JSONL
    log_json = json.dumps(
        event,
        ensure_ascii=False
    )
    logger_instance.info(log_json)
    print(f"TRACE_LOG: {log_json}", flush=True)