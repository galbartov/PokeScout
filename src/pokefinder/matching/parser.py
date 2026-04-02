"""
Detect category and parse grade from listing titles.
"""
from __future__ import annotations

import re
import unicodedata

_GRADE_RE = re.compile(r"\b(PSA|BGS|CGC|SGC)\s*(\d+(?:\.\d)?)\b", re.IGNORECASE)

_SEALED_KW = {
    "booster box", "בוסטר בוקס", "etb", "elite trainer", "tin",
    "collection box", "קופסת אוסף", "starter deck", "starter kit",
    "gift box", "מוצר סגור", "sealed", "אריזה סגורה", "blister",
    "theme deck",
}
_GRADED_KW = {"psa", "bgs", "cgc", "sgc", "graded", "מדורג", "ציון"}
_BULK_KW = {
    "lot", "לוט", "bulk", "באלק", "collection", "אוסף", "x100",
    "x50", "100 cards", "50 cards", "mixed lot", "assorted",
}


def detect_category(title: str) -> str:
    """Detect listing category: sealed / graded / bulk / singles"""
    low = title.lower()

    if any(kw in low for kw in _GRADED_KW):
        return "graded"
    if any(kw in low for kw in _SEALED_KW):
        return "sealed"
    if any(kw in low for kw in _BULK_KW):
        return "bulk"
    return "singles"


def parse_grade(title: str) -> tuple[str | None, str | None, float | None]:
    """
    Parse grading company, full grade string, and numeric grade value.
    Returns (company, grade_str, grade_value), e.g. ("PSA", "PSA 10", 10.0)
    """
    m = _GRADE_RE.search(title)
    if not m:
        return None, None, None
    company = m.group(1).upper()
    grade_val = float(m.group(2))
    grade_str = f"{company} {grade_val:.0f}" if grade_val == int(grade_val) else f"{company} {grade_val}"
    return company, grade_str, grade_val


def normalize_title(title: str) -> str:
    """Lowercase, strip punctuation, normalize whitespace for fuzzy comparison."""
    # Remove diacritics
    nfkd = unicodedata.normalize("NFKD", title)
    text = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Lowercase and remove punctuation except spaces
    text = re.sub(r"[^\w\s\u0590-\u05FF]", " ", text.lower())
    # Collapse whitespace
    return re.sub(r"\s+", " ", text).strip()
