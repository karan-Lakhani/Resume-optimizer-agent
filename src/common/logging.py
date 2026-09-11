import logging
import sys
from config.settings import get_settings

_CONFIGURED = False

def setup_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings()
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(settings.log_level or "INFO")
    root.handlers = [handler]

    _CONFIGURED = True

def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)