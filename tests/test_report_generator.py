import json

import fitz

from engine.analyzer import analyze_text
from engine.report_generator import (
    generate_json_report,
    generate_json_report_text,
    generate_markdown_report,
    generate_pdf_report,
)


def test_generate_markdown_report_includes_scores_and_matches() -> None:
    result = analyze_text("This plays a crucial role.")

    report = generate_markdown_report(result)

    assert "# AWARE Local Report" in report
    assert "## Overall Result" in report
    assert "## Result Interpretation" in report
    assert "## Reviewer Recommendation" in report
    assert "## Top Reasons for This Score" in report
    assert "## Highest-Risk Paragraphs" in report
    assert "## Category Summary" in report
    assert "plays a crucial role" in report
    assert "Inflated significance" in report


def test_generate_json_report_returns_serializable_dict() -> None:
    result = analyze_text("This plays a crucial role.")

    report = generate_json_report(result)

    assert report["document_score"]["total_matches"] == 1
    assert report["interpretation"]
    assert report["reviewer_recommendation"]
    assert report["top_reasons"]
    assert report["category_summary"]
    assert report["highest_risk_paragraphs"]
    assert report["matches"][0]["matched_text"] == "plays a crucial role"


def test_generate_markdown_report_handles_no_matches() -> None:
    result = analyze_text("This paragraph has direct wording.")

    report = generate_markdown_report(result)

    assert "No triggered categories." in report
    assert "No paragraph-level risk detected." in report
    assert "No category-level matches." in report
    assert "No matches found." in report


def test_generate_json_report_text_is_valid_json() -> None:
    result = analyze_text("This plays a crucial role.")

    report_text = generate_json_report_text(result)

    assert json.loads(report_text)["document_score"]["total_matches"] == 1


def test_generate_pdf_report_includes_overall_result_and_highlighted_text_only() -> None:
    result = analyze_text("This plays a crucial role.")

    report_bytes = generate_pdf_report(result)

    assert report_bytes.startswith(b"%PDF")
    document = fitz.open(stream=report_bytes, filetype="pdf")
    pdf_text = "\n".join(page.get_text() for page in document)
    document.close()

    assert "Overall Result" in pdf_text
    assert "RISK SCORE" in pdf_text
    assert "Highlighted Document" in pdf_text
    assert "plays a crucial role" in pdf_text
    assert "Top Reasons for This Score" not in pdf_text
    assert "Category Summary" not in pdf_text
    assert "Inflated significance" not in pdf_text
