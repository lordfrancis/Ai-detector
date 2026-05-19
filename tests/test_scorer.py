from engine.config import clear_scoring_config_cache
from engine.scorer import (
    _normalized_risk_score,
    get_risk_level,
    one_based,
    score_document,
    score_paragraph,
    sensitivity_multiplier,
)


def test_get_risk_level_boundaries() -> None:
    assert get_risk_level(20) == "Low"
    assert get_risk_level(21) == "Moderate"
    assert get_risk_level(51) == "High"
    assert get_risk_level(81) == "Very high"


def test_scoring_uses_runtime_config(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "scoring_config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "risk_bands:",
                "  low_max: 10",
                "  moderate_max: 30",
                "  high_max: 60",
                "calibration:",
                "  multiplier: 10",
                "severity_weights:",
                "  low: 1",
                "  medium: 3",
                "  high: 5",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("AWARE_SCORING_CONFIG", str(config_path))
    clear_scoring_config_cache()

    try:
        assert get_risk_level(11) == "Moderate"
        assert _normalized_risk_score(1, 100, sensitivity=3) == 100.0
    finally:
        monkeypatch.delenv("AWARE_SCORING_CONFIG", raising=False)
        clear_scoring_config_cache()


def test_score_paragraph_applies_sensitivity_multiplier() -> None:
    paragraph = "word " * 100
    matches = [{"paragraph_index": 0, "category": "Test", "weight": 1}]

    low_score = score_paragraph(paragraph, matches, paragraph_index=0, sensitivity=1)
    default_score = score_paragraph(paragraph, matches, paragraph_index=0, sensitivity=3)
    high_score = score_paragraph(paragraph, matches, paragraph_index=0, sensitivity=5)

    assert low_score["risk_score"] < default_score["risk_score"] < high_score["risk_score"]


def test_sensitivity_multiplier_matches_ui_scale() -> None:
    assert sensitivity_multiplier(1) == 0.50
    assert sensitivity_multiplier(3) == 1.00
    assert round(sensitivity_multiplier(5), 2) == 1.67


def test_one_based_handles_none_and_zero_based_indexes() -> None:
    assert one_based(None) is None
    assert one_based(0) == 1


def test_score_paragraph_counts_matches_and_weight() -> None:
    paragraph = "This paragraph plays a crucial role in the argument."
    matches = [
        {
            "paragraph_index": 0,
            "category": "Inflated significance",
            "weight": 4,
        }
    ]

    score = score_paragraph(paragraph, matches, paragraph_index=0)

    assert score["paragraph_number"] == 1
    assert score["match_count"] == 1
    assert score["total_weight"] == 4
    assert score["risk_score"] > 0
    assert score["top_categories"] == ["Inflated significance"]


def test_score_paragraph_keeps_number_without_matches() -> None:
    score = score_paragraph("This paragraph has no matches.", [], paragraph_index=2)

    assert score["paragraph_number"] == 3
    assert score["match_count"] == 0
    assert score["risk_level"] == "Low"


def test_score_document_summarizes_paragraph_scores() -> None:
    text = "First paragraph.\n\nSecond paragraph plays a crucial role."
    paragraph_scores = [
        {
            "paragraph_number": 1,
            "word_count": 2,
            "match_count": 0,
            "total_weight": 0,
            "risk_score": 0,
            "risk_level": "Low",
            "top_categories": [],
        },
        {
            "paragraph_number": 2,
            "word_count": 6,
            "match_count": 1,
            "total_weight": 4,
            "risk_score": 100,
            "risk_level": "Very high",
            "top_categories": ["Inflated significance"],
        },
    ]
    matches = [
        {
            "category": "Inflated significance",
            "severity": "high",
            "weight": 4,
        }
    ]

    score = score_document(text, paragraph_scores, matches)

    assert score["total_matches"] == 1
    assert score["total_weight"] == 4
    assert score["top_5_rule_categories"] == ["Inflated significance"]
    assert score["highest_risk_paragraphs"][0]["paragraph_number"] == 2
    assert score["interpretation"]
    assert score["reviewer_recommendation"]
    assert score["top_reasons"][0]["match_count"] == 1
    assert score["category_summary"][0]["severity_distribution"]["high"] == 1


def test_score_document_orders_categories_by_frequency_then_weight() -> None:
    paragraph_scores = [
        {
            "paragraph_number": 1,
            "word_count": 20,
            "match_count": 4,
            "total_weight": 9,
            "risk_score": 100,
            "risk_level": "Very high",
            "top_categories": ["Repeated", "Weighted"],
            "excerpt": "Example paragraph.",
        }
    ]
    matches = [
        {"category": "Weighted", "severity": "critical", "weight": 6},
        {"category": "Repeated", "severity": "low", "weight": 1},
        {"category": "Repeated", "severity": "medium", "weight": 2},
    ]

    score = score_document("Example paragraph.", paragraph_scores, matches)

    assert score["top_5_rule_categories"] == ["Repeated", "Weighted"]
    assert score["category_summary"][0]["category"] == "Repeated"
    assert score["category_summary"][0]["match_count"] == 2
    assert score["category_summary"][0]["total_weight"] == 3
    assert score["category_summary"][0]["severity_distribution"] == {
        "low": 1,
        "medium": 1,
        "high": 0,
        "critical": 0,
    }


def test_score_document_keeps_top_five_positive_risk_paragraphs() -> None:
    paragraph_scores = [
        {
            "paragraph_number": number,
            "word_count": 10,
            "match_count": 1,
            "total_weight": number,
            "risk_score": float(number),
            "risk_level": "Low",
            "top_categories": [],
            "excerpt": f"Paragraph {number}",
        }
        for number in range(1, 7)
    ]

    score = score_document("Example text.", paragraph_scores, [])

    assert [row["paragraph_number"] for row in score["highest_risk_paragraphs"]] == [
        6,
        5,
        4,
        3,
        2,
    ]
