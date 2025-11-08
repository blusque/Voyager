"""Centralized logging configuration for Voyager project."""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[41m',   # Red background
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
                record.name = f"\033[35m{record.name}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str,
    log_dir: str = "logs",
    log_level: int = logging.INFO,
    console_level: Optional[int] = None,
    file_level: Optional[int] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Set up a logger with both console and file handlers.
    
    Args:
        name: Logger name (typically module name)
        log_dir: Directory for log files
        log_level: Default logging level
        console_level: Console handler level (defaults to log_level)
        file_level: File handler level (defaults to log_level)
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)  # Capture all levels, handlers will filter
    
    console_level = console_level if console_level is not None else log_level
    file_level = file_level if file_level is not None else log_level
    
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Console handler with color formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_format = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    timestamp = datetime.now().strftime('%Y%m%d')
    log_file = log_path / f"{name.replace('.', '_')}_{timestamp}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(file_level)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    logger.propagate = False  # Prevent duplicate logs from parent loggers
    
    return logger


def configure_root_logger(log_dir: str = "logs", level: int = logging.INFO):
    """
    Configure the root logger for the entire application.
    
    Args:
        log_dir: Directory for log files
        level: Logging level
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Root logger file handler
    timestamp = datetime.now().strftime('%Y%m%d')
    log_file = log_path / f"voyager_{timestamp}.log"
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding='utf-8'
            ),
            logging.StreamHandler(sys.stdout)
        ]
    )


def get_logger(name: str, log_dir: str = "logs") -> logging.Logger:
    """
    Get or create a logger for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        log_dir: Directory for log files
        
    Returns:
        Logger instance
    """
    # Use environment variable if set, otherwise use default
    log_level_str = os.environ.get('VOYAGER_LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    return setup_logger(name, log_dir=log_dir, log_level=log_level)


# Silence noisy third-party loggers
def silence_noisy_loggers():
    """Reduce verbosity of common noisy third-party libraries."""
    noisy_loggers = [
        'urllib3',
        'requests',
        'httpx',
        'httpcore',
        'openai',
        'langchain',
        'chromadb',
        'posthog',
    ]
    
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
