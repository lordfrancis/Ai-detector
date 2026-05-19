"""Document and paragraph scoring utilities."""

from __future__ import annotations

from collections import Counter
from typing import Any

import regex


def score_paragraph(
    paragraph: str,
    matches: list[dict[str, Any]],
    paragraph_index: int | None = None,
) -> dict[str, Any]:
    """Compute paragraph-level risk from rule matches."""
    word_count = _count_words(paragraph)
    total_weight = sum(int(match.get("weight", 0)) for match in matches)
    risk_score = _normalized_risk_score(total_weight, word_count)
    categories = Counter(match["category"] for match in matches)

    return {
        "paragraph_number": _paragraph_number(matches, paragraph_index),
        "word_count": word_count,
        "match_count": len(matches),
        "total_weight": total_weight,
        "risk_score": risk_score,
        "risk_level": get_risk_level(risk_score),
        "top_categories": [category for category, _ in categories.most_common(3)],
    }


def score_document(
    text: str,
    paragraph_scores: list[dict[str, Any]],
    matches: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compute document-level risk from paragraph scores and optional matches."""
    total_word_count = _count_words(text)
    total_matches = sum(score["match_count"] for score in paragraph_scores)
    total_weight = sum(score["total_weight"] for score in paragraph_scores)
    risk_score = _normalized_risk_score(total_weight, total_word_count)

    category_counts: Counter[str] = Counter()
    if matches is not None:
        category_counts.update(match["category"] for match in matches)
    else:
        for score in paragraph_scores:
            category_counts.update(score.get("top_categories", []))

    highest_risk_paragraphs = sorted(
        paragraph_scores,
        key=lambda score: score["risk_score"],
        reverse=True,
    )[:3]

    return {
        "overall_risk_score": risk_score,
        "overall_risk_level": get_risk_level(risk_score),
        "total_word_count": total_word_count,
        "total_matches": total_matches,
        "total_weight": total_weight,
        "top_5_rule_categories": [
            category for category, _ in category_counts.most_common(5)
        ],
        "highest_risk_paragraphs": highest_risk_paragraphs,
    }


def get_risk_level(score: float) -> str:
    """Map a 0-100 risk score to a readable risk level."""
    if score <= 20:
        return "Low"
    if score <= 50:
        return "Moderate"
    if score <= 80:
        return "High"
    return "Very high"


def _count_words(text: str) -> int:
    return len(regex.findall(r"\b[\p{L}\p{N}']+\b", text))


def _normalized_risk_score(total_weight: int, word_count: int) -> float:
    if word_count <= 0:
        return 0.0

    normalized_score = (total_weight / word_count) * 1000
    return round(min(100.0, normalized_score * 5), 2)


def _paragraph_number(
    matches: list[dict[str, Any]],
    paragraph_index: int | None,
) -> int | None:
    if paragraph_index is None and matches:
        paragraph_index = matches[0].get("paragraph_index")

    if paragraph_index is None:
        return None

    return int(paragraph_index) + 1
