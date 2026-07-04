import sys
from loguru import logger

def setup_logging(log_level: str = "INFO") -> None:
    """Configures loguru logging to output to stdout with colorized formatting.

    Args:
        log_level: Minimum logging level to output (e.g., DEBUG, INFO, WARNING)
    """
    logger.remove()  # Remove default logger configuration

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    import sys
    import codecs
    
    # Ensure stdout handles UTF-8 on Windows
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

    logger.add(
        sys.stdout,
        colorize=True,
        format=log_format,
        level=log_level,
        backtrace=True,
        diagnose=True,
    )
    
    logger.info(f"Logger initialized with level: {log_level}")

# Setup logging on module import
import os
setup_logging(os.getenv("LOG_LEVEL", "INFO"))
