from loguru import logger
import sys
from mangaba.config import config


def get_logger(name: str = "MangabaAI"):
    """Get a configured logger instance with colored console output.

    Args:
        name: Name to associate with the logger (default "MangabaAI").

    Returns:
        A configured logger instance with colorized console output.
    """

    # Remove handlers padrão
    logger.remove()

    # Adiciona handler colorido para console
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[name]}</cyan> | <level>{message}</level>",
        level=config.log_level,
        colorize=True,
    )

    return logger.bind(name=name)
