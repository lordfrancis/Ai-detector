import json

from engine.analyzer import analyze_text
from engine.report_generator import (
    generate_json_report,
    generate_json_report_text,
    generate_markdown_report,
)


def test_generate_markdown_report_includes_scores_and_matches() -> None:
    result = analyze_text("This plays a crucial role.")

    report = generate_markdown_report(result)

    assert "# AWARE Local Report" in report
    assert "## Overall Result" in report
    assert "plays a crucial role" in report
    assert "Inflated significance" in report


def test_generate_json_report_returns_serializable_dict() -> None:
    result = analyze_text("This plays a crucial role.")

    report = generate_json_report(result)

    assert report["document_score"]["total_matches"] == 1
    assert report["matches"][0]["matched_text"] == "plays a crucial role"


def test_generate_json_report_text_is_valid_json() -> None:
    result = analyze_text("This plays a crucial role.")

    report_text = generate_json_report_text(result)

    assert json.loads(report_text)["document_score"]["total_matches"] == 1
