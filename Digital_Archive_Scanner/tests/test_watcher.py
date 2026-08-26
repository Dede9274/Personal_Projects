import os
from pathlib import Path

import fitz
import pytest

from smart_archive.ocr import ExtractionResult
from smart_archive.pipeline import ProcessResult, process_document
from smart_archive.watcher import (
    ChecksumIndex,
    DuplicateResult,
    PendingPathQueue,
    ProcessingJournal,
    RecoveryResult,
    calculate_sha256,
    cleanup_partial_archive_files,
    is_complete_pdf,
    process_incoming_document,
    retry_failed_documents,
    wait_until_stable,
)


def stable_file(
    path: Path,
    stable_seconds: float,
    poll_interval: float,
    timeout: float,
) -> bool:
    return True


def successful_processor(
    source: Path,
    archive_root: Path,
    languages: str,
) -> ProcessResult:
    return process_document(
        source,
        archive_root,
        languages,
        text_extractor=invoice_extractor,
    )


def failing_processor(
    source: Path,
    archive_root: Path,
    languages: str,
) -> ProcessResult:
    raise RuntimeError("synthetic processing failure")


def invoice_extractor(path: Path, languages: str) -> ExtractionResult:
    return ExtractionResult(
        "Invoice Invoice number 1482 Amount due 100.00",
        used_ocr=True,
        languages=languages,
    )


def test_waits_until_file_is_stable(tmp_path: Path) -> None:
    source = tmp_path / "scan.pdf"
    document = fitz.open()
    document.new_page()
    document.save(source)
    document.close()

    assert wait_until_stable(
        source,
        stable_seconds=0.02,
        poll_interval=0.005,
        timeout=0.2,
    )


def test_incomplete_pdf_does_not_become_ready(tmp_path: Path) -> None:
    source = tmp_path / "scan.pdf"
    source.write_bytes(b"%PDF-1.7\nscanner-is-still-writing")

    assert not wait_until_stable(
        source,
        stable_seconds=0.01,
        poll_interval=0.005,
        timeout=0.05,
    )
    assert not is_complete_pdf(source)


@pytest.mark.skipif(os.name != "nt", reason="Windows exclusive-access behavior")
def test_open_pdf_is_not_ready_until_writer_releases_it(tmp_path: Path) -> None:
    source = tmp_path / "scan.pdf"
    document = fitz.open()
    document.new_page()
    document.save(source)
    document.close()

    with source.open("rb"):
        assert not is_complete_pdf(source)

    assert is_complete_pdf(source)


def test_stability_waits_for_readiness_after_size_stops(tmp_path: Path) -> None:
    source = tmp_path / "scan.pdf"
    source.write_bytes(b"unchanged-size")
    readiness_results = iter((False, False, True))

    assert wait_until_stable(
        source,
        stable_seconds=0.01,
        poll_interval=0.005,
        timeout=0.1,
        readiness_checker=lambda path: next(readiness_results),
    )


def test_calculates_sha256_checksum(tmp_path: Path) -> None:
    source = tmp_path / "scan.pdf"
    source.write_bytes(b"same-document-content")

    assert calculate_sha256(source) == (
        "b165a17a8afc72b338df0560c5b56cc9951d9c183176cceb8d3c2c6bd8955677"
    )


def test_pending_queue_deduplicates_paths(tmp_path: Path) -> None:
    source = tmp_path / "scan.pdf"
    pending_paths = PendingPathQueue()

    assert pending_paths.submit(source)
    assert not pending_paths.submit(source)

    queued_path = pending_paths.get(timeout=0.1)
    pending_paths.complete(queued_path)
    assert pending_paths.submit(source)

    queued_path = pending_paths.get(timeout=0.1)
    pending_paths.complete(queued_path)


def test_successful_document_is_archived_and_removed_from_incoming(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "data"
    source = archive_root / "incoming/invoice.pdf"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"synthetic-pdf-content")

    result = process_incoming_document(
        source,
        archive_root=archive_root,
        document_processor=successful_processor,
        stability_checker=stable_file,
    )

    assert result is not None
    assert isinstance(result, ProcessResult)
    assert not source.exists()
    assert result.destination.read_bytes() == b"synthetic-pdf-content"
    assert not list((archive_root / "processing").glob("*.pdf"))
    assert (archive_root / "smart_archive.db").is_file()


def test_duplicate_document_is_preserved_without_second_archive(tmp_path: Path) -> None:
    archive_root = tmp_path / "data"
    first_source = archive_root / "incoming/first.pdf"
    first_source.parent.mkdir(parents=True)
    first_source.write_bytes(b"identical-document-content")

    first_result = process_incoming_document(
        first_source,
        archive_root=archive_root,
        document_processor=successful_processor,
        stability_checker=stable_file,
    )
    second_source = archive_root / "incoming/second.pdf"
    second_source.write_bytes(b"identical-document-content")
    second_result = process_incoming_document(
        second_source,
        archive_root=archive_root,
        document_processor=successful_processor,
        stability_checker=stable_file,
    )

    assert isinstance(first_result, ProcessResult)
    assert isinstance(second_result, DuplicateResult)
    assert second_result.original_destination == first_result.destination.resolve()
    assert second_result.duplicate_path.read_bytes() == b"identical-document-content"
    assert not (archive_root / "archive/invoices/second.pdf").exists()


def test_same_name_with_different_content_is_not_duplicate(tmp_path: Path) -> None:
    archive_root = tmp_path / "data"
    source = archive_root / "incoming/invoice.pdf"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"first-document-content")
    first_result = process_incoming_document(
        source,
        archive_root=archive_root,
        document_processor=successful_processor,
        stability_checker=stable_file,
    )

    source.write_bytes(b"different-document-content")
    second_result = process_incoming_document(
        source,
        archive_root=archive_root,
        document_processor=successful_processor,
        stability_checker=stable_file,
    )

    assert isinstance(first_result, ProcessResult)
    assert isinstance(second_result, ProcessResult)
    assert first_result.destination.name == "invoice.pdf"
    assert second_result.destination.name == "invoice_2.pdf"


def test_failed_document_is_preserved_in_failed(tmp_path: Path) -> None:
    archive_root = tmp_path / "data"
    source = archive_root / "incoming/broken.pdf"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"broken-pdf-content")
    checksum = calculate_sha256(source)

    with pytest.raises(RuntimeError, match="synthetic processing failure"):
        process_incoming_document(
            source,
            archive_root=archive_root,
            max_attempts=3,
            retry_delay=0,
            document_processor=failing_processor,
            stability_checker=stable_file,
            sleep_function=lambda delay: None,
        )

    assert not source.exists()
    failed_path = archive_root / "failed/broken.pdf"
    assert failed_path.read_bytes() == b"broken-pdf-content"
    assert not list((archive_root / "processing").glob("*.pdf"))
    journal = ProcessingJournal(archive_root / "smart_archive.db")
    assert journal.attempts_for(checksum) == 3
    assert journal.status_for(checksum) == "failed"


def test_transient_failure_retries_until_document_succeeds(tmp_path: Path) -> None:
    archive_root = tmp_path / "data"
    source = archive_root / "incoming/invoice.pdf"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"transient-document-content")
    checksum = calculate_sha256(source)
    calls = 0
    delays = []

    def transient_processor(
        staged_path: Path,
        data_root: Path,
        languages: str,
    ) -> ProcessResult:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise RuntimeError("temporary OCR failure")
        return successful_processor(staged_path, data_root, languages)

    result = process_incoming_document(
        source,
        archive_root=archive_root,
        max_attempts=3,
        retry_delay=0.25,
        document_processor=transient_processor,
        stability_checker=stable_file,
        sleep_function=delays.append,
    )

    assert isinstance(result, ProcessResult)
    assert calls == 3
    assert delays == [0.25, 0.5]
    assert not list((archive_root / "processing").glob("*.pdf"))
    assert not list((archive_root / "failed").glob("*.pdf"))
    assert ProcessingJournal(archive_root / "smart_archive.db").attempts_for(checksum) == 0


def test_processing_resumes_persisted_attempt_count(tmp_path: Path) -> None:
    archive_root = tmp_path / "data"
    staged_path = archive_root / "processing/interrupted.pdf"
    staged_path.parent.mkdir(parents=True)
    staged_path.write_bytes(b"interrupted-document-content")
    checksum = calculate_sha256(staged_path)
    journal = ProcessingJournal(archive_root / "smart_archive.db")
    journal.begin_attempt(checksum, staged_path.name)
    journal.record_error(checksum, RuntimeError("first failure"))
    journal.begin_attempt(checksum, staged_path.name)
    journal.record_error(checksum, RuntimeError("second failure"))
    calls = 0

    def final_failure(
        source: Path,
        data_root: Path,
        languages: str,
    ) -> ProcessResult:
        nonlocal calls
        calls += 1
        raise RuntimeError("third failure")

    with pytest.raises(RuntimeError, match="third failure"):
        process_incoming_document(
            staged_path,
            archive_root=archive_root,
            max_attempts=3,
            retry_delay=0,
            document_processor=final_failure,
            sleep_function=lambda delay: None,
        )

    assert calls == 1
    assert journal.attempts_for(checksum) == 3
    assert journal.status_for(checksum) == "failed"
    assert (archive_root / "failed/interrupted.pdf").is_file()


def test_recovers_completed_copy_already_in_checksum_index(tmp_path: Path) -> None:
    archive_root = tmp_path / "data"
    staged_path = archive_root / "processing/interrupted.pdf"
    destination = archive_root / "archive/invoices/interrupted.pdf"
    staged_path.parent.mkdir(parents=True)
    destination.parent.mkdir(parents=True)
    staged_path.write_bytes(b"completed-before-crash")
    destination.write_bytes(b"completed-before-crash")
    checksum = calculate_sha256(staged_path)
    ChecksumIndex(archive_root / "smart_archive.db").record(checksum, destination)

    def unexpected_processor(
        source: Path,
        data_root: Path,
        languages: str,
    ) -> ProcessResult:
        raise AssertionError("completed crash recovery must not process again")

    result = process_incoming_document(
        staged_path,
        archive_root=archive_root,
        document_processor=unexpected_processor,
    )

    assert isinstance(result, RecoveryResult)
    assert result.destination == destination.resolve()
    assert destination.read_bytes() == b"completed-before-crash"
    assert not staged_path.exists()
    assert not list((archive_root / "duplicates").glob("*.pdf"))


def test_recovers_completed_copy_missing_from_checksum_index(tmp_path: Path) -> None:
    archive_root = tmp_path / "data"
    staged_path = archive_root / "processing/interrupted.pdf"
    destination = archive_root / "needs_review/interrupted.pdf"
    staged_path.parent.mkdir(parents=True)
    destination.parent.mkdir(parents=True)
    staged_path.write_bytes(b"copied-before-index-crash")
    destination.write_bytes(b"copied-before-index-crash")
    checksum = calculate_sha256(staged_path)
    journal = ProcessingJournal(archive_root / "smart_archive.db")
    journal.begin_attempt(checksum, staged_path.name)

    def unexpected_processor(
        source: Path,
        data_root: Path,
        languages: str,
    ) -> ProcessResult:
        raise AssertionError("unindexed crash recovery must not process again")

    result = process_incoming_document(
        staged_path,
        archive_root=archive_root,
        document_processor=unexpected_processor,
    )

    assert isinstance(result, RecoveryResult)
    assert result.destination == destination.resolve()
    assert ChecksumIndex(archive_root / "smart_archive.db").find(checksum) == (
        destination.resolve()
    )
    assert journal.attempts_for(checksum) == 0
    assert not staged_path.exists()


def test_removes_partial_archive_files_left_by_crash(tmp_path: Path) -> None:
    archive_root = tmp_path / "data"
    archive_directory = archive_root / "archive/invoices"
    review_directory = archive_root / "needs_review"
    archive_directory.mkdir(parents=True)
    review_directory.mkdir(parents=True)
    archive_partial = archive_directory / ".smart-archive-one.partial"
    review_partial = review_directory / ".smart-archive-two.partial"
    completed_pdf = archive_directory / "invoice.pdf"
    archive_partial.write_bytes(b"incomplete")
    review_partial.write_bytes(b"incomplete")
    completed_pdf.write_bytes(b"complete")

    removed_paths = cleanup_partial_archive_files(archive_root)

    assert removed_paths == [archive_partial, review_partial]
    assert not archive_partial.exists()
    assert not review_partial.exists()
    assert completed_pdf.read_bytes() == b"complete"


def test_retry_failed_document_resets_attempts_and_requeues(tmp_path: Path) -> None:
    archive_root = tmp_path / "data"
    failed_path = archive_root / "failed/broken.pdf"
    failed_path.parent.mkdir(parents=True)
    failed_path.write_bytes(b"failed-document-content")
    checksum = calculate_sha256(failed_path)
    journal = ProcessingJournal(archive_root / "smart_archive.db")
    journal.begin_attempt(checksum, failed_path.name)
    journal.begin_attempt(checksum, failed_path.name)
    journal.mark_failed(checksum, failed_path, RuntimeError("still broken"))

    requeued_paths = retry_failed_documents(
        archive_root=archive_root,
        failed_file=Path("broken.pdf"),
    )

    assert requeued_paths == [archive_root / "incoming/broken.pdf"]
    assert requeued_paths[0].read_bytes() == b"failed-document-content"
    assert not failed_path.exists()
    assert journal.attempts_for(checksum) == 0
