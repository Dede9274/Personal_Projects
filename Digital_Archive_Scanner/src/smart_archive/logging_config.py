import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
MANAGED_HANDLER_ATTRIBUTE = "_smart_archive_handler"


def configure_logging(
    archive_root: Path,
    level: str = "INFO",
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 5,
    console: bool = True,
) -> Path:
    log_directory = archive_root.resolve() / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)
    log_path = log_directory / "smart_archive.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    _remove_managed_handlers(root_logger)

    formatter = logging.Formatter(LOG_FORMAT)
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    setattr(file_handler, MANAGED_HANDLER_ATTRIBUTE, True)
    root_logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        setattr(console_handler, MANAGED_HANDLER_ATTRIBUTE, True)
        root_logger.addHandler(console_handler)

    return log_path


def close_logging() -> None:
    _remove_managed_handlers(logging.getLogger())


def _remove_managed_handlers(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        if getattr(handler, MANAGED_HANDLER_ATTRIBUTE, False):
            logger.removeHandler(handler)
            handler.close()
