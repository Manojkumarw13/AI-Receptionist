"""
Centralized Logging Configuration for AI Receptionist
Provides consistent logging setup across all modules
"""

import logging
import sys
from pathlib import Path

# BUG-17 FIX: Import LOGS_DIR from config.py so both config and logging_config
# agree on the log directory. Previously, logging_config.py used Path("logs")
# (relative to CWD) while config.py used BASE_DIR / "logs" (absolute), causing
# logs to be written to different directories depending on launch directory.
try:
    from config import LOGS_DIR
except ImportError:
    # Fallback if running standalone (e.g., during tests)
    LOGS_DIR = Path(__file__).parent.parent / "logs"

LOGS_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging(name: str = "ai_receptionist", level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger with consistent formatting.
    
    Args:
        name: Logger name (usually __name__ from calling module)
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(level)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # File handler
        file_handler = logging.FileHandler(LOGS_DIR / "app.log")
        file_handler.setLevel(level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger


# Create default logger
logger = setup_logging()
