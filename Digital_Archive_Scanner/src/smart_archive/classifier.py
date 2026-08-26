from dataclasses import dataclass
import re
import unicodedata


CATEGORY_KEYWORDS = {
    "invoice": (
        "rechnung",
        "rechnungsnummer",
        "rechnungsdatum",
        "zahlungsziel",
        "mehrwertsteuer",
        "mwst",
        "invoice",
        "invoice number",
        "amount due",
        "faturë tatimore",
        "faturë elektronike",
        "numri i faturës",
        "data e faturës",
        "afati i pagesës",
        "shuma për pagesë",
        "tvsh",
    ),
    "receipt": (
        "kassenbon",
        "rückgeld",
        "kassierer",
        "bar bezahlt",
        "receipt",
        "cash",
        "change due",
        "kupon tatimor",
        "numri i kuponit",
        "data dhe ora",
        "para në dorë",
        "mënyra e pagesës",
        "logo fiskale",
        "pajisje fiskale",
    ),
    "delivery_note": (
        "lieferschein",
        "lieferdatum",
        "gelieferte menge",
        "wareneingang",
        "delivery note",
        "delivery date",
        "quantity delivered",
        "fletë-dorëzimi",
        "fletë dorëzimi",
        "data e dorëzimit",
        "sasia e dorëzuar",
        "mallra të dorëzuara",
        "pranimi i mallrave",
    ),
}


@dataclass(frozen=True)
class Classification:
    category: str
    confidence: float
    matched_keywords: tuple[str, ...]
    requires_review: bool


def classify_text(text: str) -> Classification:
    normalized_text = _normalize(text)
    matches = {
        category: tuple(
            keyword
            for keyword in keywords
            if _normalize(keyword) in normalized_text
        )
        for category, keywords in CATEGORY_KEYWORDS.items()
    }
    ranked = sorted(matches.items(), key=lambda item: len(item[1]), reverse=True)
    top_category, top_matches = ranked[0]
    top_score = len(top_matches)
    second_score = len(ranked[1][1])
    total_matches = sum(len(category_matches) for category_matches in matches.values())

    if top_score == 0:
        return Classification("needs_review", 0.0, (), True)

    evidence_strength = min(top_score / 3, 1.0)
    category_dominance = top_score / total_matches
    confidence = round(evidence_strength * category_dominance, 2)
    requires_review = top_score < 2 or top_score == second_score or confidence < 0.6

    if requires_review:
        return Classification("needs_review", confidence, top_matches, True)

    return Classification(top_category, confidence, top_matches, False)


def _normalize(value: str) -> str:
    decomposed_value = unicodedata.normalize("NFKD", value.casefold())
    value_without_diacritics = "".join(
        character
        for character in decomposed_value
        if not unicodedata.combining(character)
    )
    return re.sub(r"\s+", " ", value_without_diacritics).strip()
