"""Document and paragraph scoring utilities."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

import regex

from engine.config import get_scoring_config


SEVERITY_LEVELS = ("low", "medium", "high", "critical")
DEFAULT_SENSITIVITY = 3
SENSITIVITY_MULTIPLIERS = {
    1: 0.50,
    2: 0.75,
    3: 1.00,
    4: 1.33,
    5: 5 / 3,
}

INTERPRETATION_BY_RISK_LEVEL = {
    "Low": (
        "The document shows few or no rule-based AI-writing signals. This does "
        "not prove human authorship, but the current pattern density is low."
    ),
    "Moderate": (
        "The document shows some repeated AI-associated writing signals. Review "
        "the flagged passages in context before drawing any conclusion."
    ),
    "High": (
        "The document shows multiple or higher-weight AI-associated writing "
        "signals. A closer human review is recommended."
    ),
    "Very high": (
        "The document shows dense or high-weight AI-associated writing signals. "
        "Treat this as a priority for human review, not as automatic proof of AI use."
    ),
}

RECOMMENDATION_BY_RISK_LEVEL = {
    "Low": (
        "No special action is suggested from this score alone. Keep normal review "
        "practices and consider the student's drafting context if concerns remain."
    ),
    "Moderate": (
        "Review the top flagged categories and ask for normal supporting evidence "
        "such as drafts, notes, or version history if the result conflicts with expectations."
    ),
    "High": (
        "Prioritize the highest-risk paragraphs for review and compare them with "
        "known student writing, drafts, version history, and an oral explanation."
    ),
    "Very high": (
        "Escalate for careful human review using multiple evidence sources, including "
        "draft history and direct discussion with the writer."
    ),
}


def score_paragraph(
    paragraph: str,
    matches: list[dict[str, Any]],
    paragraph_index: int | None = None,
    sensitivity: int = DEFAULT_SENSITIVITY,
) -> dict[str, Any]:
    """Compute paragraph-level risk from rule matches."""
    word_count = _count_words(paragraph)
    total_weight = sum(int(match.get("weight", 0)) for match in matches)
    risk_score = _normalized_risk_score(total_weight, word_count, sensitivity)
    categories = Counter(match["category"] for match in matches)

    return {
        "paragraph_number": _paragraph_number(matches, paragraph_index),
        "word_count": word_count,
        "match_count": len(matches),
        "total_weight": total_weight,
        "risk_score": risk_score,
        "risk_level": get_risk_level(risk_score),
        "top_categories": [category for category, _ in categories.most_common(3)],
        "excerpt": _excerpt(paragraph),
    }


def score_document(
    text: str,
    paragraph_scores: list[dict[str, Any]],
    matches: list[dict[str, Any]] | None = None,
    sensitivity: int = DEFAULT_SENSITIVITY,
) -> dict[str, Any]:
    """Compute document-level risk from paragraph scores and optional matches."""
    total_word_count = _count_words(text)
    total_matches = sum(score["match_count"] for score in paragraph_scores)
    total_weight = sum(score["total_weight"] for score in paragraph_scores)
    risk_score = _normalized_risk_score(total_weight, total_word_count, sensitivity)

    category_summary = _category_summary(matches or [])
    top_reasons = category_summary[:5]

    highest_risk_paragraphs = sorted(
        [
            score
            for score in paragraph_scores
            if float(score.get("risk_score", 0)) > 0
        ],
        key=lambda score: (
            float(score["risk_score"]),
            int(score["total_weight"]),
            -int(score["paragraph_number"] or 0),
        ),
        reverse=True,
    )[:5]

    risk_level = get_risk_level(risk_score)

    return {
        "overall_risk_score": risk_score,
        "overall_risk_level": risk_level,
        "total_word_count": total_word_count,
        "total_matches": total_matches,
        "total_weight": total_weight,
        "sensitivity": sensitivity,
        "sensitivity_multiplier": sensitivity_multiplier(sensitivity),
        "interpretation": INTERPRETATION_BY_RISK_LEVEL[risk_level],
        "reviewer_recommendation": RECOMMENDATION_BY_RISK_LEVEL[risk_level],
        "top_reasons": top_reasons,
        "category_summary": category_summary,
        "top_5_rule_categories": [reason["category"] for reason in top_reasons],
        "highest_risk_paragraphs": highest_risk_paragraphs,
    }


def get_risk_level(score: float) -> str:
    """Map a 0-100 risk score to a readable risk level."""
    risk_bands = get_scoring_config()["risk_bands"]
    if score <= risk_bands["low_max"]:
        return "Low"
    if score <= risk_bands["moderate_max"]:
        return "Moderate"
    if score <= risk_bands["high_max"]:
        return "High"
    return "Very high"


def one_based(index: int | None) -> int | None:
    """Convert a zero-based index to one-based display form."""
    if index is None:
        return None
    return index + 1


def sensitivity_multiplier(sensitivity: int) -> float:
    """Map UI sensitivity level to the weight multiplier used in scoring."""
    return SENSITIVITY_MULTIPLIERS[max(1, min(5, int(sensitivity)))]


def _count_words(text: str) -> int:
    return len(regex.findall(r"\b[\p{L}\p{N}']+\b", text))


def _normalized_risk_score(
    total_weight: int,
    word_count: int,
    sensitivity: int = DEFAULT_SENSITIVITY,
) -> float:
    if word_count <= 0:
        return 0.0

    calibration_multiplier = float(get_scoring_config()["calibration"]["multiplier"])
    adjusted_weight = total_weight * sensitivity_multiplier(sensitivity)
    normalized_score = (adjusted_weight / word_count) * 1000
    return round(min(100.0, normalized_score * calibration_multiplier), 2)


def _category_summary(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    category_counts: Counter[str] = Counter()
    category_weights: Counter[str] = Counter()
    severity_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for match in matches:
        category = str(match["category"])
        severity = str(match.get("severity", "")).lower()
        category_counts[category] += 1
        category_weights[category] += int(match.get("weight", 0))
        if severity in SEVERITY_LEVELS:
            severity_counts[category][severity] += 1

    rows = []
    for category, match_count in category_counts.items():
        rows.append(
            {
                "category": category,
                "match_count": match_count,
                "total_weight": category_weights[category],
                "severity_distribution": {
                    severity: severity_counts[category][severity]
                    for severity in SEVERITY_LEVELS
                },
            }
        )

    return sorted(
        rows,
        key=lambda row: (
            -int(row["match_count"]),
            -int(row["total_weight"]),
            str(row["category"]).lower(),
        ),
    )


def _excerpt(paragraph: str, max_length: int = 180) -> str:
    excerpt = regex.sub(r"\s+", " ", paragraph).strip()
    if len(excerpt) <= max_length:
        return excerpt
    return excerpt[: max_length - 3].rstrip() + "..."


def _paragraph_number(
    matches: list[dict[str, Any]],
    paragraph_index: int | None,
) -> int | None:
    if paragraph_index is None and matches:
        paragraph_index = matches[0].get("paragraph_index")

    if paragraph_index is None:
        return None

    return one_based(int(paragraph_index))
