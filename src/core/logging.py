"""
Aurora Pro AI - Logging Configuration
"""
import logging
import sys
from typing import Any
from pythonjsonlogger import jsonlogger

from .config import get_settings


def setup_logging() -> logging.Logger:
    """Configure structured JSON logging"""
    settings = get_settings()
    
    logger = logging.getLogger("aurora")
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler with JSON formatting
    handler = logging.StreamHandler(sys.stdout)
    
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
        rename_fields={
            'asctime': 'timestamp',
            'levelname': 'level',
            'name': 'logger'
        }
    )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance"""
    if name:
        return logging.getLogger(f"aurora.{name}")
    return logging.getLogger("aurora")
