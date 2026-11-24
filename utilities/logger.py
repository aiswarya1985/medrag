"""Central loguru setup. Call setup_logger() ONCE at each entry point
(pipeline __main__, streamlit_app, scripts). Other modules just do:
    from loguru import logger
"""

import sys
import json

from loguru import logger

from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent   # utilities/ -> project root

LOG_DIR = REPO_ROOT / "logs"
LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{name}:{function}:{line} - {message}"
)
FILE_LOG_FORMAT = LOG_FORMAT + "\n"  



def pretty(obj) -> str:
    """Pretty-print dicts/lists for log messages; falls back to str() for non-JSON types."""
    try:
        return json.dumps(obj, indent=2, default=str, ensure_ascii=False)
    except Exception:
        return str(obj)


def setup_logger(level: str = "INFO",service: str = "app") -> None:
    LOG_DIR.mkdir(exist_ok=True)
    logger.remove()  # clear default + any earlier handlers (safe on Streamlit reruns)

    # Console: level is configurable (use "DEBUG" while learning)
    logger.add(sys.stderr, format=LOG_FORMAT, level=level)

    # File: always DEBUG, so the full detail is saved even if the console is quieter
    logger.add(
        LOG_DIR / f"logs_medrag_{service}.txt",
        format=FILE_LOG_FORMAT,
        level="DEBUG",
        colorize=False,
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
    )
