import logging
from pathlib import Path

from smart_archive.logging_config import close_logging, configure_logging


def test_writes_and_rotates_persistent_log_files(tmp_path: Path) -> None:
    archive_root = tmp_path / "data"
    log_path = configure_logging(
        archive_root,
        level="INFO",
        max_bytes=200,
        backup_count=2,
        console=False,
    )
    logger = logging.getLogger("smart_archive.test")

    try:
        for entry_number in range(20):
            logger.info(
                "Persistent log entry %s with enough text to rotate",
                entry_number,
            )
    finally:
        close_logging()

    assert log_path.is_file()
    assert log_path.with_name("smart_archive.log.1").is_file()
    log_contents = "".join(
        path.read_text(encoding="utf-8")
        for path in sorted(log_path.parent.glob("smart_archive.log*"))
    )
    assert "Persistent log entry" in log_contents
