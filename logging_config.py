import logging
import logging.handlers
import json
import os
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'query_time'):
            log_entry['query_time'] = record.query_time
        if hasattr(record, 'agent_type'):
            log_entry['agent_type'] = record.agent_type
        if hasattr(record, 'sql_query'):
            log_entry['sql_query'] = record.sql_query
        if hasattr(record, 'error_details'):
            log_entry['error_details'] = record.error_details
            
        return json.dumps(log_entry)


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "logs/snowgpt.log",
    max_file_size_mb: int = 10,
    backup_count: int = 5,
    enable_console: bool = True
) -> logging.Logger:
    """
    Set up comprehensive logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file
        max_file_size_mb: Maximum size of each log file in MB
        backup_count: Number of backup files to keep
        enable_console: Whether to enable console logging
        
    Returns:
        Configured logger instance
    """
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("snowgpt")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_file_size_mb * 1024 * 1024,
        backupCount=backup_count
    )
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Console handler (optional)
    if enable_console:
        console_handler = logging.StreamHandler()
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = "snowgpt") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


# Initialize default logger
logger = setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE", "logs/snowgpt.log"),
    enable_console=os.getenv("ENABLE_CONSOLE_LOGGING", "true").lower() == "true"
)