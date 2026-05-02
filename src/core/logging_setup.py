"""
Configuración centralizada de logging (nivel desde LOG_LEVEL en .env / Config).
"""
from __future__ import annotations

import logging
import sys
from typing import Optional

_log = logging.getLogger(__name__)


def configure_logging(log_level: Optional[str] = None) -> None:
    """
    Configura el root logger con formato estándar.
    Si `log_level` es None, usa `config.log_level`.
    """
    from src.core.config import config

    name = (log_level or getattr(config, "log_level", None) or "INFO").upper()
    level = getattr(logging, name, logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root.addHandler(handler)
    else:
        for h in root.handlers:
            h.setLevel(level)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    _log.info("Logging configurado a nivel %s", name)
