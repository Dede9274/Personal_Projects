from smart_archive.classifier import classify_text


def test_classifies_german_invoice() -> None:
    result = classify_text(
        "RECHNUNG Rechnungsnummer 1482 Rechnungsdatum 06.08.2026 MwSt 19%"
    )

    assert result.category == "invoice"
    assert result.confidence == 1.0
    assert result.requires_review is False


def test_classifies_english_delivery_note() -> None:
    result = classify_text(
        "DELIVERY NOTE Delivery date 2026-08-06 Quantity delivered: 12"
    )

    assert result.category == "delivery_note"
    assert result.requires_review is False


def test_classifies_albanian_invoice() -> None:
    result = classify_text(
        "FATURË TATIMORE Numri i faturës 1482 Data e faturës 07.08.2026 "
        "Afati i pagesës 14 ditë TVSH 20%"
    )

    assert result.category == "invoice"
    assert result.confidence == 1.0
    assert result.requires_review is False


def test_classifies_albanian_receipt() -> None:
    result = classify_text(
        "KUPON TATIMOR Numri i kuponit 502 Data dhe ora 07.08.2026 10:30 "
        "Mënyra e pagesës: para në dorë Logo fiskale"
    )

    assert result.category == "receipt"
    assert result.confidence == 1.0
    assert result.requires_review is False


def test_classifies_accentless_albanian_delivery_note() -> None:
    result = classify_text(
        "FLETE-DOREZIMI Data e dorezimit 07.08.2026 "
        "Sasia e dorezuar 12 Mallra te dorezuara"
    )

    assert result.category == "delivery_note"
    assert result.confidence == 1.0
    assert result.requires_review is False


def test_sends_weak_match_to_review() -> None:
    result = classify_text("Invoice")

    assert result.category == "needs_review"
    assert result.requires_review is True


def test_sends_unknown_document_to_review() -> None:
    result = classify_text("Meeting notes for next Tuesday")

    assert result.category == "needs_review"
    assert result.confidence == 0.0
