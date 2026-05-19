"""Dataset evaluation utilities for calibration runs."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from engine.analyzer import DEFAULT_RULE_PATH, analyze_text


DATASET_CATEGORIES = ["human", "ai_raw", "ai_humanized", "ai_edited", "mixed"]
POSITIVE_RISK_LEVELS = {"Moderate", "High", "Very high"}


def evaluate_datasets(
    dataset_root: str | Path = "datasets",
    rule_path: str | Path = DEFAULT_RULE_PATH,
) -> dict[str, Any]:
    """Run the analyzer over dataset text files and return calibration metrics."""
    root_path = Path(dataset_root)
    file_results: list[dict[str, Any]] = []
    category_scores: dict[str, list[float]] = defaultdict(list)
    category_level_counts: dict[str, Counter[str]] = defaultdict(Counter)
    category_rule_counts: dict[str, Counter[str]] = defaultdict(Counter)
    rule_categories: dict[str, str] = {}

    for category in DATASET_CATEGORIES:
        category_path = root_path / category
        for text_path in sorted(category_path.glob("*.txt")):
            text = text_path.read_text(encoding="utf-8")
            analysis_result = analyze_text(text, rule_path=rule_path)
            document_score = analysis_result["document_score"]
            risk_score = float(document_score["overall_risk_score"])
            risk_level = str(document_score["overall_risk_level"])

            category_scores[category].append(risk_score)
            category_level_counts[category].update([risk_level])

            for match in analysis_result["matches"]:
                rule_id = str(match["rule_id"])
                category_rule_counts[category].update([rule_id])
                rule_categories[rule_id] = str(match["category"])

            file_results.append(
                {
                    "category": category,
                    "filename": str(text_path.relative_to(root_path)),
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "total_matches": document_score["total_matches"],
                    "word_count": document_score["total_word_count"],
                }
            )

    category_summaries = [
        _category_summary(
            category=category,
            scores=category_scores[category],
            level_counts=category_level_counts[category],
        )
        for category in DATASET_CATEGORIES
    ]

    return {
        "dataset_root": str(root_path),
        "total_files": len(file_results),
        "category_summaries": category_summaries,
        "top_triggered_rules": _top_triggered_rules(
            category_rule_counts=category_rule_counts,
            rule_categories=rule_categories,
        ),
        "file_results": file_results,
    }


def _category_summary(
    category: str,
    scores: list[float],
    level_counts: Counter[str],
) -> dict[str, Any]:
    total_files = len(scores)
    positive_count = sum(level_counts[level] for level in POSITIVE_RISK_LEVELS)

    return {
        "category": category,
        "total_files": total_files,
        "average_risk_score": round(sum(scores) / total_files, 2)
        if total_files
        else 0.0,
        "low_count": level_counts["Low"],
        "moderate_count": level_counts["Moderate"],
        "high_count": level_counts["High"],
        "very_high_count": level_counts["Very high"],
        "false_positive_count": positive_count if category == "human" else 0,
        "false_negative_count": _false_negative_count(category, level_counts),
    }


def _false_negative_count(category: str, level_counts: Counter[str]) -> int:
    if category not in {"ai_raw", "ai_humanized"}:
        return 0
    return level_counts["Low"]


def _top_triggered_rules(
    category_rule_counts: dict[str, Counter[str]],
    rule_categories: dict[str, str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for category in DATASET_CATEGORIES:
        rule_counts = category_rule_counts[category]
        total_matches = sum(rule_counts.values())
        for rule_id, count in rule_counts.most_common():
            rows.append(
                {
                    "category": category,
                    "rule_id": rule_id,
                    "rule_category": rule_categories.get(rule_id, ""),
                    "count": count,
                    "percentage_of_category_matches": round(
                        (count / total_matches) * 100,
                        2,
                    )
                    if total_matches
                    else 0.0,
                }
            )

    return rows
