from pathlib import Path

from smart_archive.ocr import ExtractionResult
from smart_archive.pipeline import process_document


def invoice_extractor(path: Path, languages: str) -> ExtractionResult:
    return ExtractionResult(
        "Rechnung Rechnungsnummer 1482 Zahlungsziel 14 Tage MwSt 19%",
        used_ocr=True,
        languages=languages,
    )


def unknown_extractor(path: Path, languages: str) -> ExtractionResult:
    return ExtractionResult(
        "Unrecognized document text",
        used_ocr=True,
        languages=languages,
    )


def test_copies_invoice_without_modifying_source(tmp_path: Path) -> None:
    source = tmp_path / "input" / "test_invoice.pdf"
    source.parent.mkdir()
    source.write_bytes(b"synthetic-pdf-content")

    result = process_document(
        source,
        archive_root=tmp_path / "data",
        text_extractor=invoice_extractor,
    )

    assert source.read_bytes() == b"synthetic-pdf-content"
    assert result.destination == tmp_path / "data/archive/invoices/test_invoice.pdf"
    assert result.destination.read_bytes() == source.read_bytes()
    assert not list(result.destination.parent.glob(".smart-archive-*.partial"))


def test_routes_unknown_document_to_review(tmp_path: Path) -> None:
    source = tmp_path / "unknown.pdf"
    source.write_bytes(b"synthetic-pdf-content")

    result = process_document(
        source,
        archive_root=tmp_path / "data",
        text_extractor=unknown_extractor,
    )

    assert result.destination.parent == tmp_path / "data/needs_review"


def test_does_not_overwrite_existing_archive_file(tmp_path: Path) -> None:
    source = tmp_path / "invoice.pdf"
    source.write_bytes(b"new-content")
    archive = tmp_path / "data/archive/invoices"
    archive.mkdir(parents=True)
    (archive / "invoice.pdf").write_bytes(b"existing-content")

    result = process_document(
        source,
        archive_root=tmp_path / "data",
        text_extractor=invoice_extractor,
    )

    assert (archive / "invoice.pdf").read_bytes() == b"existing-content"
    assert result.destination.name == "invoice_2.pdf"
    assert result.destination.read_bytes() == b"new-content"
