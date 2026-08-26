import argparse
import logging
from pathlib import Path

from .logging_config import configure_logging
from .pipeline import process_document


LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OCR, classify, and archive one scanned PDF."
    )
    parser.add_argument("pdf", type=Path, help="PDF document to process")
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=Path("data"),
        help="Root directory for archived documents (default: data)",
    )
    parser.add_argument(
        "--languages",
        default="deu+eng",
        help="Tesseract language expression (default: deu+eng)",
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
        result = process_document(
            arguments.pdf,
            archive_root=arguments.archive_root,
            languages=arguments.languages,
        )
    except Exception as error:
        LOGGER.exception("Could not process %s", arguments.pdf)
        print(f"Error: {error}")
        return 1

    extraction_method = "OCR" if result.extraction.used_ocr else "embedded PDF text"
    print(f"File: {result.source.name}")
    print(f"Text extraction: {extraction_method} ({result.extraction.languages})")
    print(f"Prediction: {result.classification.category}")
    print(f"Confidence: {result.classification.confidence:.0%}")
    print(f"Destination: {result.destination}")
    LOGGER.info("Archived %s at %s", result.source, result.destination)
    return 0
