import argparse
from collections.abc import Callable
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import hashlib
import logging
import os
from pathlib import Path
from queue import Empty, Queue
import shutil
import sqlite3
from threading import Event, Lock, Thread
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .logging_config import configure_logging
from .pipeline import (
    PARTIAL_FILE_PREFIX,
    PARTIAL_FILE_SUFFIX,
    ProcessResult,
    process_document,
)


LOGGER = logging.getLogger(__name__)

DocumentProcessor = Callable[[Path, Path, str], ProcessResult]
StabilityChecker = Callable[[Path, float, float, float], bool]
ReadinessChecker = Callable[[Path], bool]
SleepFunction = Callable[[float], None]


@dataclass(frozen=True)
class DuplicateResult:
    checksum: str
    duplicate_path: Path
    original_destination: Path


@dataclass(frozen=True)
class RecoveryResult:
    checksum: str
    destination: Path


ProcessingResult = ProcessResult | DuplicateResult | RecoveryResult


class ChecksumIndex:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    checksum TEXT PRIMARY KEY,
                    destination TEXT NOT NULL,
                    processed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def find(self, checksum: str) -> Path | None:
        with sqlite3.connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT destination FROM documents WHERE checksum = ?",
                (checksum,),
            ).fetchone()
            if row is None:
                return None

            destination = Path(row[0])
            if destination.is_file():
                return destination

            connection.execute(
                "DELETE FROM documents WHERE checksum = ?",
                (checksum,),
            )
            return None

    def record(self, checksum: str, destination: Path) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO documents (checksum, destination)
                VALUES (?, ?)
                """,
                (checksum, str(destination.resolve())),
            )

    def remove(self, checksum: str) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                "DELETE FROM documents WHERE checksum = ?",
                (checksum,),
            )


class ProcessingJournal:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS processing_jobs (
                    checksum TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    last_error TEXT,
                    failed_path TEXT,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def attempts_for(self, checksum: str) -> int:
        with sqlite3.connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT attempts FROM processing_jobs WHERE checksum = ?",
                (checksum,),
            ).fetchone()
        return 0 if row is None else int(row[0])

    def status_for(self, checksum: str) -> str | None:
        with sqlite3.connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT status FROM processing_jobs WHERE checksum = ?",
                (checksum,),
            ).fetchone()
        return None if row is None else str(row[0])

    def begin_attempt(self, checksum: str, filename: str) -> int:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO processing_jobs (
                    checksum, filename, attempts, status, updated_at
                )
                VALUES (?, ?, 1, 'processing', CURRENT_TIMESTAMP)
                ON CONFLICT(checksum) DO UPDATE SET
                    filename = excluded.filename,
                    attempts = processing_jobs.attempts + 1,
                    status = 'processing',
                    last_error = NULL,
                    failed_path = NULL,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (checksum, filename),
            )
            row = connection.execute(
                "SELECT attempts FROM processing_jobs WHERE checksum = ?",
                (checksum,),
            ).fetchone()
        if row is None:
            raise RuntimeError(f"Could not record processing attempt for {filename}")
        return int(row[0])

    def record_error(self, checksum: str, error: Exception) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                UPDATE processing_jobs
                SET status = 'retrying', last_error = ?, updated_at = CURRENT_TIMESTAMP
                WHERE checksum = ?
                """,
                (str(error), checksum),
            )

    def mark_failed(
        self,
        checksum: str,
        failed_path: Path,
        error: Exception,
    ) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                UPDATE processing_jobs
                SET status = 'failed', last_error = ?, failed_path = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE checksum = ?
                """,
                (str(error), str(failed_path.resolve()), checksum),
            )

    def clear(self, checksum: str) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                "DELETE FROM processing_jobs WHERE checksum = ?",
                (checksum,),
            )


class PendingPathQueue:
    def __init__(self) -> None:
        self._queue: Queue[Path] = Queue()
        self._pending: set[Path] = set()
        self._lock = Lock()

    def submit(self, path: Path) -> bool:
        normalized_path = path.resolve()
        if normalized_path.suffix.casefold() != ".pdf":
            return False

        with self._lock:
            if normalized_path in self._pending:
                return False
            self._pending.add(normalized_path)

        self._queue.put(normalized_path)
        return True

    def get(self, timeout: float) -> Path:
        return self._queue.get(timeout=timeout)

    def complete(self, path: Path) -> None:
        with self._lock:
            self._pending.discard(path)
        self._queue.task_done()

    def join(self) -> None:
        self._queue.join()

    def empty(self) -> bool:
        return self._queue.empty()


class IncomingEventHandler(FileSystemEventHandler):
    def __init__(self, pending_paths: PendingPathQueue) -> None:
        self._pending_paths = pending_paths

    def on_created(self, event: object) -> None:
        self._submit_event_path(event, "src_path")

    def on_modified(self, event: object) -> None:
        self._submit_event_path(event, "src_path")

    def on_moved(self, event: object) -> None:
        self._submit_event_path(event, "dest_path")

    def _submit_event_path(self, event: object, attribute: str) -> None:
        if getattr(event, "is_directory", False):
            return
        event_path = getattr(event, attribute, None)
        if event_path is not None:
            self._pending_paths.submit(Path(event_path))


def wait_until_stable(
    path: Path,
    stable_seconds: float = 2.0,
    poll_interval: float = 0.5,
    timeout: float = 300.0,
    readiness_checker: ReadinessChecker | None = None,
) -> bool:
    if readiness_checker is None:
        readiness_checker = is_complete_pdf

    deadline = time.monotonic() + timeout
    previous_signature: tuple[int, int] | None = None
    stable_since: float | None = None

    while time.monotonic() < deadline:
        try:
            file_status = path.stat()
        except FileNotFoundError:
            return False
        except OSError:
            time.sleep(poll_interval)
            continue

        current_time = time.monotonic()
        signature = (file_status.st_size, file_status.st_mtime_ns)
        if signature == previous_signature:
            if stable_since is not None and current_time - stable_since >= stable_seconds:
                if readiness_checker(path):
                    return True
        else:
            previous_signature = signature
            stable_since = current_time

        time.sleep(poll_interval)

    return False


def is_complete_pdf(path: Path) -> bool:
    try:
        file_size = path.stat().st_size
        if file_size < 8 or not _can_open_exclusively(path):
            return False

        with path.open("rb") as pdf_file:
            if pdf_file.read(5) != b"%PDF-":
                return False
            pdf_file.seek(max(file_size - 4096, 0))
            if b"%%EOF" not in pdf_file.read():
                return False

        import fitz

        with fitz.open(path) as document:
            return document.page_count > 0
    except (ImportError, OSError, RuntimeError, ValueError):
        return False


def calculate_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as document:
        while chunk := document.read(chunk_size):
            checksum.update(chunk)
    return checksum.hexdigest()


def cleanup_partial_archive_files(archive_root: Path) -> list[Path]:
    archive_root = archive_root.resolve()
    removed_paths = []
    pattern = f"{PARTIAL_FILE_PREFIX}*{PARTIAL_FILE_SUFFIX}"
    for relative_directory in (Path("archive"), Path("needs_review")):
        directory = archive_root / relative_directory
        if not directory.is_dir():
            continue
        for partial_path in sorted(directory.rglob(pattern)):
            try:
                partial_path.unlink()
            except FileNotFoundError:
                continue
            except OSError:
                LOGGER.exception(
                    "Could not remove interrupted archive copy %s",
                    partial_path,
                )
                continue
            removed_paths.append(partial_path)
            LOGGER.warning("Removed interrupted archive copy %s", partial_path)
    return removed_paths


def _can_open_exclusively(path: Path) -> bool:
    if os.name != "nt":
        try:
            with path.open("rb"):
                return True
        except OSError:
            return False

    create_file = ctypes.WinDLL("kernel32", use_last_error=True).CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    close_handle = ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle
    close_handle.argtypes = (wintypes.HANDLE,)
    close_handle.restype = wintypes.BOOL

    handle = create_file(
        str(path),
        0x80000000,
        0,
        None,
        3,
        0x80,
        None,
    )
    if handle == ctypes.c_void_p(-1).value:
        return False

    try:
        return True
    finally:
        close_handle(handle)


def process_incoming_document(
    source: Path,
    archive_root: Path = Path("data"),
    languages: str = "deu+eng",
    stable_seconds: float = 2.0,
    poll_interval: float = 0.5,
    stability_timeout: float = 300.0,
    max_attempts: int = 3,
    retry_delay: float = 2.0,
    document_processor: DocumentProcessor = process_document,
    stability_checker: StabilityChecker = wait_until_stable,
    sleep_function: SleepFunction = time.sleep,
) -> ProcessingResult | None:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if retry_delay < 0:
        raise ValueError("retry_delay cannot be negative")

    archive_root = archive_root.resolve()
    processing_directory = archive_root / "processing"
    failed_directory = archive_root / "failed"
    duplicates_directory = archive_root / "duplicates"
    processing_directory.mkdir(parents=True, exist_ok=True)
    failed_directory.mkdir(parents=True, exist_ok=True)
    duplicates_directory.mkdir(parents=True, exist_ok=True)

    source = source.resolve()
    processing_source = source.parent == processing_directory
    if not processing_source:
        is_stable = stability_checker(
            source,
            stable_seconds,
            poll_interval,
            stability_timeout,
        )
        if not is_stable:
            LOGGER.warning("File did not become stable before timeout: %s", source)
            return None

        staged_path = _available_path(processing_directory / source.name)
        shutil.move(source, staged_path)
        LOGGER.info("Staged %s at %s", source, staged_path)
    else:
        staged_path = source
        LOGGER.warning("Resuming interrupted processing for %s", staged_path)

    checksum: str | None = None
    processing_journal: ProcessingJournal | None = None
    try:
        checksum = calculate_sha256(staged_path)
        database_path = archive_root / "smart_archive.db"
        checksum_index = ChecksumIndex(database_path)
        processing_journal = ProcessingJournal(database_path)
        original_destination = checksum_index.find(checksum)
        if original_destination is not None and not _matches_checksum(
            original_destination,
            checksum,
            staged_path.stat().st_size,
        ):
            LOGGER.error(
                "Indexed archive copy failed checksum verification: %s",
                original_destination,
            )
            checksum_index.remove(checksum)
            original_destination = None
        if original_destination is not None:
            if processing_source:
                staged_path.unlink()
                processing_journal.clear(checksum)
                LOGGER.warning(
                    "Recovered completed archive copy for %s at %s",
                    staged_path.name,
                    original_destination,
                )
                return RecoveryResult(checksum, original_destination)

            duplicate_path = _available_path(duplicates_directory / staged_path.name)
            shutil.move(staged_path, duplicate_path)
            processing_journal.clear(checksum)
            return DuplicateResult(checksum, duplicate_path, original_destination)

        previous_attempts = processing_journal.attempts_for(checksum)
        if processing_source and previous_attempts > 0:
            recovered_destination = _find_matching_archived_copy(
                archive_root,
                staged_path,
                checksum,
            )
            if recovered_destination is not None:
                checksum_index.record(checksum, recovered_destination)
                staged_path.unlink()
                processing_journal.clear(checksum)
                LOGGER.warning(
                    "Recovered unindexed archive copy for %s at %s",
                    staged_path.name,
                    recovered_destination,
                )
                return RecoveryResult(checksum, recovered_destination)

        if previous_attempts >= max_attempts:
            raise RuntimeError(
                f"Retry limit already reached for {staged_path.name} "
                f"({previous_attempts}/{max_attempts} attempts)"
            )

        while True:
            attempt_number = processing_journal.begin_attempt(
                checksum,
                staged_path.name,
            )
            LOGGER.info(
                "Processing attempt %s/%s for %s",
                attempt_number,
                max_attempts,
                staged_path.name,
            )
            result: ProcessResult | None = None
            checksum_recorded = False
            try:
                result = document_processor(staged_path, archive_root, languages)
                if not result.destination.is_file():
                    raise RuntimeError(
                        f"Archive copy was not created: {result.destination}"
                    )
                if result.destination.stat().st_size != staged_path.stat().st_size:
                    raise RuntimeError(
                        f"Archive copy size does not match source: {staged_path}"
                    )
                checksum_index.record(checksum, result.destination)
                checksum_recorded = True
                staged_path.unlink()
                try:
                    processing_journal.clear(checksum)
                except sqlite3.Error:
                    LOGGER.exception(
                        "Could not clear completed processing job for %s",
                        staged_path.name,
                    )
                LOGGER.info(
                    "Completed processing for %s at %s",
                    staged_path.name,
                    result.destination,
                )
                return result
            except Exception as error:
                if checksum_recorded:
                    checksum_index.remove(checksum)
                _remove_uncommitted_destination(result)
                processing_journal.record_error(checksum, error)
                if attempt_number >= max_attempts:
                    raise

                delay = retry_delay * (2 ** (attempt_number - 1))
                LOGGER.warning(
                    "Processing attempt %s/%s failed for %s: %s. Retrying in %.1f seconds",
                    attempt_number,
                    max_attempts,
                    staged_path.name,
                    error,
                    delay,
                )
                sleep_function(delay)
    except Exception as error:
        if staged_path.exists():
            failed_path = _available_path(failed_directory / staged_path.name)
            shutil.move(staged_path, failed_path)
            if checksum is not None and processing_journal is not None:
                processing_journal.mark_failed(checksum, failed_path, error)
            LOGGER.error("Preserved failed document at %s", failed_path)
        raise


def watch_incoming(
    archive_root: Path = Path("data"),
    languages: str = "deu+eng",
    stable_seconds: float = 2.0,
    poll_interval: float = 0.5,
    stability_timeout: float = 300.0,
    max_attempts: int = 3,
    retry_delay: float = 2.0,
) -> None:
    archive_root = archive_root.resolve()
    incoming_directory = archive_root / "incoming"
    processing_directory = archive_root / "processing"
    incoming_directory.mkdir(parents=True, exist_ok=True)
    processing_directory.mkdir(parents=True, exist_ok=True)
    cleanup_partial_archive_files(archive_root)

    pending_paths = PendingPathQueue()
    stop_requested = Event()
    worker = Thread(
        target=_worker_loop,
        args=(
            pending_paths,
            stop_requested,
            archive_root,
            languages,
            stable_seconds,
            poll_interval,
            stability_timeout,
            max_attempts,
            retry_delay,
        ),
        name="smart-archive-worker",
        daemon=True,
    )
    worker.start()

    event_handler = IncomingEventHandler(pending_paths)
    observer = Observer()
    observer.schedule(event_handler, str(incoming_directory), recursive=False)

    interrupted_paths = sorted(processing_directory.glob("*.pdf"))
    if interrupted_paths:
        LOGGER.warning(
            "Found %s interrupted document(s) in processing",
            len(interrupted_paths),
        )
    for existing_path in interrupted_paths:
        pending_paths.submit(existing_path)
    for existing_path in sorted(incoming_directory.glob("*.pdf")):
        pending_paths.submit(existing_path)

    observer.start()
    LOGGER.info("Monitoring %s", incoming_directory)
    LOGGER.info("Press Ctrl+C to stop")

    try:
        while observer.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        LOGGER.info("Stopping watcher after queued documents finish")
    finally:
        observer.stop()
        observer.join()
        stop_requested.set()
        pending_paths.join()
        worker.join()


def _worker_loop(
    pending_paths: PendingPathQueue,
    stop_requested: Event,
    archive_root: Path,
    languages: str,
    stable_seconds: float,
    poll_interval: float,
    stability_timeout: float,
    max_attempts: int,
    retry_delay: float,
) -> None:
    while not stop_requested.is_set() or not pending_paths.empty():
        try:
            source = pending_paths.get(timeout=0.2)
        except Empty:
            continue

        try:
            result = process_incoming_document(
                source,
                archive_root=archive_root,
                languages=languages,
                stable_seconds=stable_seconds,
                poll_interval=poll_interval,
                stability_timeout=stability_timeout,
                max_attempts=max_attempts,
                retry_delay=retry_delay,
            )
            if result is not None:
                if isinstance(result, RecoveryResult):
                    LOGGER.warning(
                        "Recovered %s using existing archive copy at %s",
                        source.name,
                        result.destination,
                    )
                elif isinstance(result, DuplicateResult):
                    LOGGER.warning(
                        "Duplicate %s preserved at %s; original is %s",
                        source.name,
                        result.duplicate_path,
                        result.original_destination,
                    )
                else:
                    LOGGER.info(
                        "Archived %s as %s at %s",
                        source.name,
                        result.classification.category,
                        result.destination,
                    )
        except Exception:
            LOGGER.exception("Could not process %s", source)
        finally:
            pending_paths.complete(source)


def retry_failed_documents(
    archive_root: Path = Path("data"),
    failed_file: Path | None = None,
) -> list[Path]:
    archive_root = archive_root.resolve()
    failed_directory = (archive_root / "failed").resolve()
    incoming_directory = archive_root / "incoming"
    failed_directory.mkdir(parents=True, exist_ok=True)
    incoming_directory.mkdir(parents=True, exist_ok=True)

    if failed_file is None:
        failed_paths = sorted(failed_directory.glob("*.pdf"))
    else:
        failed_path = (
            failed_file.resolve()
            if failed_file.is_absolute()
            else (failed_directory / failed_file).resolve()
        )
        try:
            failed_path.relative_to(failed_directory)
        except ValueError as error:
            raise ValueError(
                f"Failed PDF must be inside {failed_directory}"
            ) from error
        if not failed_path.is_file():
            raise FileNotFoundError(f"Failed PDF does not exist: {failed_path}")
        if failed_path.suffix.casefold() != ".pdf":
            raise ValueError(f"Only PDF files can be retried: {failed_path.name}")
        failed_paths = [failed_path]

    processing_journal = ProcessingJournal(archive_root / "smart_archive.db")
    requeued_paths = []
    for failed_path in failed_paths:
        checksum = calculate_sha256(failed_path)
        processing_journal.clear(checksum)
        incoming_path = _available_path(incoming_directory / failed_path.name)
        shutil.move(failed_path, incoming_path)
        requeued_paths.append(incoming_path)
        LOGGER.info("Requeued failed document %s at %s", failed_path, incoming_path)

    return requeued_paths


def _remove_uncommitted_destination(result: ProcessResult | None) -> None:
    if result is None or not result.destination.is_file():
        return
    try:
        result.destination.unlink()
    except OSError:
        LOGGER.exception(
            "Could not remove incomplete archive copy %s",
            result.destination,
        )


def _find_matching_archived_copy(
    archive_root: Path,
    staged_path: Path,
    checksum: str,
) -> Path | None:
    staged_size = staged_path.stat().st_size
    for relative_directory in (Path("archive"), Path("needs_review")):
        directory = archive_root / relative_directory
        if not directory.is_dir():
            continue
        for candidate in sorted(directory.rglob("*")):
            if not candidate.is_file() or candidate.suffix.casefold() != ".pdf":
                continue
            if _matches_checksum(candidate, checksum, staged_size):
                return candidate.resolve()
    return None


def _matches_checksum(path: Path, checksum: str, expected_size: int) -> bool:
    try:
        return (
            path.stat().st_size == expected_size
            and calculate_sha256(path) == checksum
        )
    except OSError:
        LOGGER.warning("Could not verify archive copy %s", path)
        return False


def _available_path(requested_path: Path) -> Path:
    if not requested_path.exists():
        return requested_path

    counter = 2
    while True:
        candidate = requested_path.with_stem(f"{requested_path.stem}_{counter}")
        if not candidate.exists():
            return candidate
        counter += 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Monitor an incoming folder and automatically archive scanned PDFs."
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=Path("data"),
        help="Root containing incoming, processing, archive, and failed folders",
    )
    parser.add_argument(
        "--languages",
        default="deu+eng",
        help="Tesseract language expression (default: deu+eng)",
    )
    parser.add_argument("--stable-seconds", type=float, default=2.0)
    parser.add_argument("--poll-interval", type=float, default=0.5)
    parser.add_argument("--stability-timeout", type=float, default=300.0)
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Maximum processing attempts before moving a PDF to failed (default: 3)",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=2.0,
        help="Initial retry delay in seconds; later waits use backoff (default: 2)",
    )
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
    )
    return parser


def build_retry_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Move failed PDFs back to incoming and reset their retry history."
    )
    parser.add_argument(
        "failed_file",
        nargs="?",
        type=Path,
        help="One PDF name from the failed folder; omit to retry every failed PDF",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=Path("data"),
        help="Root containing incoming and failed folders (default: data)",
    )
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
    )
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    log_path = configure_logging(arguments.archive_root, arguments.log_level)
    LOGGER.info("Logging to %s", log_path)
    try:
        watch_incoming(
            archive_root=arguments.archive_root,
            languages=arguments.languages,
            stable_seconds=arguments.stable_seconds,
            poll_interval=arguments.poll_interval,
            stability_timeout=arguments.stability_timeout,
            max_attempts=arguments.max_attempts,
            retry_delay=arguments.retry_delay,
        )
    except Exception:
        LOGGER.exception("Watcher stopped unexpectedly")
        return 1
    return 0


def retry_main() -> int:
    arguments = build_retry_parser().parse_args()
    log_path = configure_logging(arguments.archive_root, arguments.log_level)
    LOGGER.info("Logging to %s", log_path)
    try:
        requeued_paths = retry_failed_documents(
            archive_root=arguments.archive_root,
            failed_file=arguments.failed_file,
        )
    except Exception as error:
        LOGGER.exception("Could not requeue failed documents")
        print(f"Error: {error}")
        return 1

    if not requeued_paths:
        print("No failed PDFs to retry.")
        return 0

    for requeued_path in requeued_paths:
        print(f"Requeued: {requeued_path}")
    return 0
