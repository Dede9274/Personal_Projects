from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Callable
from uuid import uuid4

from .classifier import Classification, classify_text
from .ocr import ExtractionResult, extract_text


ARCHIVE_DIRECTORIES = {
    "invoice": Path("archive/invoices"),
    "receipt": Path("archive/receipts"),
    "delivery_note": Path("archive/delivery_notes"),
    "needs_review": Path("needs_review"),
}
PARTIAL_FILE_PREFIX = ".smart-archive-"
PARTIAL_FILE_SUFFIX = ".partial"


@dataclass(frozen=True)
class ProcessResult:
    source: Path
    destination: Path
    extraction: ExtractionResult
    classification: Classification


def process_document(
    source: Path,
    archive_root: Path = Path("data"),
    languages: str = "deu+eng",
    text_extractor: Callable[[Path, str], ExtractionResult] = extract_text,
) -> ProcessResult:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"PDF does not exist: {source}")
    if source.suffix.casefold() != ".pdf":
        raise ValueError(f"Only PDF files are supported: {source.name}")

    extraction = text_extractor(source, languages)
    classification = classify_text(extraction.text)
    destination_directory = archive_root / ARCHIVE_DIRECTORIES[classification.category]
    destination_directory.mkdir(parents=True, exist_ok=True)
    destination = _available_destination(destination_directory / source.name)
    _copy_atomically(source, destination)

    return ProcessResult(source, destination, extraction, classification)


def _copy_atomically(source: Path, destination: Path) -> None:
    temporary_path = destination.parent / (
        f"{PARTIAL_FILE_PREFIX}{uuid4().hex}{PARTIAL_FILE_SUFFIX}"
    )
    try:
        shutil.copy2(source, temporary_path)
        temporary_path.replace(destination)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def _available_destination(requested_path: Path) -> Path:
    if not requested_path.exists():
        return requested_path

    counter = 2
    while True:
        candidate = requested_path.with_stem(f"{requested_path.stem}_{counter}")
        if not candidate.exists():
            return candidate
        counter += 1
