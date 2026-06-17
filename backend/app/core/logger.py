from pathlib import Path

from loguru import logger

BACKEND_DIR = Path(__file__).parent.parent.parent
LOG_DIR = BACKEND_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger.add(
    LOG_DIR / "app.log",
    rotation="10 MB",
    retention="30 days",
    level="INFO",
    enqueue=True,
    backtrace=True,
    diagnose=True,
)

__all__ = ["logger"]
