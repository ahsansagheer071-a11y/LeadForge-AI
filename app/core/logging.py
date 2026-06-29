import logging
import sys
from logging.handlers import RotatingFileHandler
import os
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """
    Configure and setup centralized logging.
    """
    logger = logging.getLogger("leadforge")
    logger.setLevel(settings.LOG_LEVEL.upper())

    # Avoid adding duplicate handlers if setup is called multiple times
    if logger.handlers:
        return logger

    # Log Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler (Stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)

    # Rotating File Handler
    file_handler = RotatingFileHandler(
        filename=os.path.join(logs_dir, "app.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Configure root logger to have same level
    logging.getLogger().setLevel(logging.WARNING)
    
    # Configure specific third party library loggers if needed
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger.info("Centralized logging has been initialized successfully.")
    return logger


# Instantiate logger
logger = setup_logging()
