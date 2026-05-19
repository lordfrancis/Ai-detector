"""Report generation utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DISCLAIMER = (
    "This report identifies writing patterns that may be associated with "
    "AI-generated or AI-assisted academic text. The result is not conclusive "
    "proof of AI use and should be reviewed with human judgment."
)


def generate_markdown_report(analysis_result: dict[str, Any]) -> str:
    """Generate a Markdown report from an analysis result."""
    document_score = analysis_result["document_score"]
    lines = [
        "# AWARE Local Report",
        "",
        "## Disclaimer",
        "",
        DISCLAIMER,
        "",
        "## Overall Result",
        "",
        f"- Risk score: {document_score['overall_risk_score']:.2f}",
        f"- Risk level: {document_score['overall_risk_level']}",
        f"- Total word count: {document_score['total_word_count']}",
        f"- Total matches: {document_score['total_matches']}",
        "",
        "## Paragraph Scores",
        "",
        "| Paragraph | Risk score | Risk level | Words | Matches | Top categories |",
        "| --- | ---: | --- | ---: | ---: | --- |",
    ]

    for score in analysis_result["paragraph_scores"]:
        lines.append(
            "| {paragraph} | {risk_score:.2f} | {risk_level} | {words} | {matches} | {categories} |".format(
                paragraph=score["paragraph_number"],
                risk_score=score["risk_score"],
                risk_level=score["risk_level"],
                words=score["word_count"],
                matches=score["match_count"],
                categories=", ".join(score["top_categories"]),
            )
        )

    lines.extend(
        [
            "",
            "## Flagged Matches",
            "",
            "| Paragraph | Sentence | Matched text | Category | Severity | Explanation | Reviewer note |",
            "| ---: | ---: | --- | --- | --- | --- | --- |",
        ]
    )

    if analysis_result["matches"]:
        for match in analysis_result["matches"]:
            lines.append(
                "| {paragraph} | {sentence} | {matched_text} | {category} | {severity} | {explanation} | {reviewer_note} |".format(
                    paragraph=_one_based(match["paragraph_index"]),
                    sentence=_one_based(match["sentence_index"]),
                    matched_text=_escape_markdown_table_text(match["matched_text"]),
                    category=_escape_markdown_table_text(match["category"]),
                    severity=match["severity"],
                    explanation=_escape_markdown_table_text(match["explanation"]),
                    reviewer_note=_escape_markdown_table_text(match["reviewer_note"]),
                )
            )
    else:
        lines.append("|  |  | No matches found. |  |  |  |  |")

    return "\n".join(lines) + "\n"


def generate_json_report(analysis_result: dict[str, Any]) -> dict[str, Any]:
    """Return the analysis result as a JSON-serializable dictionary."""
    return {
        "disclaimer": DISCLAIMER,
        "document_score": analysis_result["document_score"],
        "paragraph_scores": analysis_result["paragraph_scores"],
        "matches": analysis_result["matches"],
        "rules_used": analysis_result["rules_used"],
        "text": analysis_result["text"],
    }


def generate_json_report_text(analysis_result: dict[str, Any]) -> str:
    """Generate pretty JSON text for download."""
    return json.dumps(generate_json_report(analysis_result), indent=2, ensure_ascii=False)


def save_report(content: str, filename: str) -> str:
    """Save report content under the reports directory and return the path."""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    output_path = reports_dir / Path(filename).name
    output_path.write_text(content, encoding="utf-8")
    return str(output_path)


def _one_based(index: int | None) -> int | str:
    if index is None:
        return ""
    return index + 1


def _escape_markdown_table_text(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")
