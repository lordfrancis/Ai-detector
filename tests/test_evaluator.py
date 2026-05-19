from pathlib import Path

from engine.evaluator import DATASET_CATEGORIES, evaluate_datasets


def test_evaluate_empty_dataset_folders_returns_zero_totals(tmp_path: Path) -> None:
    _create_dataset_dirs(tmp_path)
    rule_path = _write_rule_file(tmp_path)

    result = evaluate_datasets(dataset_root=tmp_path, rule_path=rule_path)

    assert result["total_files"] == 0
    assert result["file_results"] == []
    assert result["top_triggered_rules"] == []
    assert all(
        summary["total_files"] == 0
        and summary["average_risk_score"] == 0.0
        and summary["false_positive_count"] == 0
        and summary["false_negative_count"] == 0
        for summary in result["category_summaries"]
    )


def test_human_positive_result_counts_as_false_positive(tmp_path: Path) -> None:
    _create_dataset_dirs(tmp_path)
    rule_path = _write_rule_file(tmp_path)
    (tmp_path / "human" / "sample.txt").write_text(
        "This plays a crucial role.",
        encoding="utf-8",
    )

    result = evaluate_datasets(dataset_root=tmp_path, rule_path=rule_path)
    human_summary = _summary_for(result, "human")

    assert human_summary["total_files"] == 1
    assert human_summary["very_high_count"] == 1
    assert human_summary["false_positive_count"] == 1


def test_ai_low_result_counts_as_false_negative(tmp_path: Path) -> None:
    _create_dataset_dirs(tmp_path)
    rule_path = _write_rule_file(tmp_path)
    (tmp_path / "ai_raw" / "sample.txt").write_text(
        "This draft uses direct observations and plain claims.",
        encoding="utf-8",
    )
    (tmp_path / "ai_humanized" / "sample.txt").write_text(
        "The paragraph describes the method and reports the result.",
        encoding="utf-8",
    )

    result = evaluate_datasets(dataset_root=tmp_path, rule_path=rule_path)

    assert _summary_for(result, "ai_raw")["false_negative_count"] == 1
    assert _summary_for(result, "ai_humanized")["false_negative_count"] == 1


def test_average_risk_score_is_computed_per_category(tmp_path: Path) -> None:
    _create_dataset_dirs(tmp_path)
    rule_path = _write_rule_file(tmp_path)
    (tmp_path / "ai_edited" / "positive.txt").write_text(
        "This plays a crucial role.",
        encoding="utf-8",
    )
    (tmp_path / "ai_edited" / "low.txt").write_text(
        "This text has no matching calibration phrase.",
        encoding="utf-8",
    )

    result = evaluate_datasets(dataset_root=tmp_path, rule_path=rule_path)

    assert _summary_for(result, "ai_edited")["average_risk_score"] == 50.0


def test_top_triggered_rules_are_counted_per_category(tmp_path: Path) -> None:
    _create_dataset_dirs(tmp_path)
    rule_path = _write_rule_file(tmp_path)
    (tmp_path / "mixed" / "sample.txt").write_text(
        "This plays a crucial role. It plays a crucial role again.",
        encoding="utf-8",
    )

    result = evaluate_datasets(dataset_root=tmp_path, rule_path=rule_path)

    assert result["top_triggered_rules"] == [
        {
            "category": "mixed",
            "rule_id": "test_001",
            "rule_category": "Inflated significance",
            "count": 2,
            "percentage_of_category_matches": 100.0,
        }
    ]


def _create_dataset_dirs(root: Path) -> None:
    for category in DATASET_CATEGORIES:
        (root / category).mkdir()


def _write_rule_file(root: Path) -> Path:
    rule_path = root / "rules.yaml"
    rule_path.write_text(
        """
- id: test_001
  category: Inflated significance
  severity: high
  weight: 4
  pattern_type: phrase
  patterns:
    - "plays a crucial role"
  explanation: "Test phrase."
""".lstrip(),
        encoding="utf-8",
    )
    return rule_path


def _summary_for(result: dict, category: str) -> dict:
    return next(
        summary
        for summary in result["category_summaries"]
        if summary["category"] == category
    )
