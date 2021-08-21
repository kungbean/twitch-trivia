import logging
from logging.handlers import RotatingFileHandler


def setup_base_logger(logger: logging.Logger, level: str = "INFO"):
    logger.setLevel(level)
    add_stream_handler(logger, "%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def add_stream_handler(logger: logging.Logger, format_str: str, level: str = "INFO"):
    formatter = formatter = logging.Formatter(format_str)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def add_rotating_file_handler(
    logger: logging.Logger,
    format_str: str,
    filename: str,
    max_bytes: int = 0,
    backup_count: int = 0,
    level: str = "INFO",
):
    formatter = formatter = logging.Formatter(format_str)
    fh = RotatingFileHandler(filename, maxBytes=max_bytes, backupCount=backup_count)
    fh.setLevel(level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
