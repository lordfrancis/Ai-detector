"""Report generation utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import fitz
import regex


DISCLAIMER = (
    "This report identifies writing patterns that may be associated with "
    "AI-generated or AI-assisted academic text. The result is not conclusive "
    "proof of AI use and should be reviewed with human judgment."
)

PDF_HIGHLIGHT_COLORS = {
    "low": (0.90, 0.96, 1.00),
    "medium": (1.00, 0.95, 0.66),
    "high": (1.00, 0.82, 0.65),
    "critical": (1.00, 0.70, 0.70),
}

PDF_PAGE_WIDTH = 612
PDF_PAGE_HEIGHT = 792
PDF_MARGIN = 54
PDF_CONTENT_RIGHT = PDF_PAGE_WIDTH - PDF_MARGIN
PDF_CONTENT_WIDTH = PDF_CONTENT_RIGHT - PDF_MARGIN
PDF_FOOTER_Y = PDF_PAGE_HEIGHT - 30
PDF_BODY_FONT_SIZE = 10.5
PDF_BODY_LINE_HEIGHT = 15
PDF_SMALL_FONT_SIZE = 8.5
PDF_TEXT_COLOR = (0.12, 0.13, 0.15)
PDF_MUTED_COLOR = (0.42, 0.45, 0.49)
PDF_RULE_COLOR = (0.82, 0.84, 0.87)
PDF_ACCENT_COLOR = (0.12, 0.32, 0.52)
PDF_CALLOUT_FILL = (0.96, 0.97, 0.98)
PDF_PANEL_FILL = (0.985, 0.988, 0.992)
PDF_RISK_COLORS = {
    "Low": (0.10, 0.48, 0.36),
    "Moderate": (0.74, 0.49, 0.12),
    "High": (0.78, 0.31, 0.12),
    "Very high": (0.68, 0.18, 0.18),
}
PDF_FONT_REGULAR = "Helvetica"
PDF_FONT_BOLD = "Helvetica-Bold"


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
        "## Result Interpretation",
        "",
        analysis_result["interpretation"],
        "",
        "## Reviewer Recommendation",
        "",
        analysis_result["reviewer_recommendation"],
        "",
        "## Top Reasons for This Score",
        "",
        "| Category | Matches | Total weight |",
        "| --- | ---: | ---: |",
    ]

    if analysis_result["top_reasons"]:
        for reason in analysis_result["top_reasons"]:
            lines.append(
                "| {category} | {matches} | {weight} |".format(
                    category=_escape_markdown_table_text(reason["category"]),
                    matches=reason["match_count"],
                    weight=reason["total_weight"],
                )
            )
    else:
        lines.append("| No triggered categories. | 0 | 0 |")

    lines.extend(
        [
            "",
            "## Highest-Risk Paragraphs",
            "",
            "| Paragraph | Risk score | Risk level | Words | Matches | Total weight | Top categories | Excerpt |",
            "| ---: | ---: | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )

    if analysis_result["highest_risk_paragraphs"]:
        for score in analysis_result["highest_risk_paragraphs"]:
            lines.append(
                "| {paragraph} | {risk_score:.2f} | {risk_level} | {words} | {matches} | {weight} | {categories} | {excerpt} |".format(
                    paragraph=score["paragraph_number"],
                    risk_score=score["risk_score"],
                    risk_level=score["risk_level"],
                    words=score["word_count"],
                    matches=score["match_count"],
                    weight=score["total_weight"],
                    categories=_escape_markdown_table_text(
                        ", ".join(score["top_categories"])
                    ),
                    excerpt=_escape_markdown_table_text(score["excerpt"]),
                )
            )
    else:
        lines.append("|  |  | No paragraph-level risk detected. |  |  |  |  |  |")

    lines.extend(
        [
            "",
            "## Category Summary",
            "",
            "| Category | Matches | Total weight | Low | Medium | High | Critical |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    if analysis_result["category_summary"]:
        for summary in analysis_result["category_summary"]:
            severity_distribution = summary["severity_distribution"]
            lines.append(
                "| {category} | {matches} | {weight} | {low} | {medium} | {high} | {critical} |".format(
                    category=_escape_markdown_table_text(summary["category"]),
                    matches=summary["match_count"],
                    weight=summary["total_weight"],
                    low=severity_distribution["low"],
                    medium=severity_distribution["medium"],
                    high=severity_distribution["high"],
                    critical=severity_distribution["critical"],
                )
            )
    else:
        lines.append("| No category-level matches. | 0 | 0 | 0 | 0 | 0 | 0 |")

    lines.extend(
        [
            "",
            "## Paragraph Scores",
            "",
            "| Paragraph | Risk score | Risk level | Words | Matches | Top categories |",
            "| --- | ---: | --- | ---: | ---: | --- |",
        ]
    )

    for score in analysis_result["paragraph_scores"]:
        lines.append(
            "| {paragraph} | {risk_score:.2f} | {risk_level} | {words} | {matches} | {categories} |".format(
                paragraph=score["paragraph_number"],
                risk_score=score["risk_score"],
                risk_level=score["risk_level"],
                words=score["word_count"],
                matches=score["match_count"],
                categories=_escape_markdown_table_text(
                    ", ".join(score["top_categories"])
                ),
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
        "interpretation": analysis_result["interpretation"],
        "reviewer_recommendation": analysis_result["reviewer_recommendation"],
        "top_reasons": analysis_result["top_reasons"],
        "highest_risk_paragraphs": analysis_result["highest_risk_paragraphs"],
        "category_summary": analysis_result["category_summary"],
        "paragraph_scores": analysis_result["paragraph_scores"],
        "matches": analysis_result["matches"],
        "rules_used": analysis_result["rules_used"],
        "text": analysis_result["text"],
    }


def generate_json_report_text(analysis_result: dict[str, Any]) -> str:
    """Generate pretty JSON text for download."""
    return json.dumps(generate_json_report(analysis_result), indent=2, ensure_ascii=False)


def generate_pdf_report(analysis_result: dict[str, Any]) -> bytes:
    """Generate a PDF report with overall results and highlighted text only."""
    document = fitz.open()
    page = document.new_page(width=PDF_PAGE_WIDTH, height=PDF_PAGE_HEIGHT)
    state = {
        "page": page,
        "x": PDF_MARGIN,
        "y": PDF_MARGIN,
        "left": PDF_MARGIN,
        "right": PDF_CONTENT_RIGHT,
        "text_panel_active": False,
    }

    _write_pdf_title(state)
    _write_pdf_callout(document, state, "Review aid only", DISCLAIMER)

    document_score = analysis_result["document_score"]
    _write_pdf_section_heading(document, state, "Overall Result")
    _write_pdf_metric_cards(document, state, document_score)
    _write_pdf_text_block(
        document,
        state,
        "Interpretation",
        analysis_result["interpretation"],
    )
    _write_pdf_text_block(
        document,
        state,
        "Reviewer Recommendation",
        analysis_result["reviewer_recommendation"],
    )
    _write_pdf_section_heading(document, state, "Highlighted Document")
    _start_pdf_text_panel(document, state)
    _write_highlighted_pdf_text(
        document=document,
        state=state,
        text=analysis_result["text"],
        matches=analysis_result["matches"],
    )

    _add_pdf_footers(document)
    pdf_bytes = document.tobytes(garbage=4, deflate=True)
    document.close()
    return pdf_bytes


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


def _write_pdf_title(state: dict[str, Any]) -> None:
    page = state["page"]
    page.insert_text(
        fitz.Point(PDF_MARGIN, state["y"]),
        "AWARE Local",
        fontsize=10,
        fontname=PDF_FONT_BOLD,
        color=PDF_ACCENT_COLOR,
    )
    state["y"] += 24
    page.insert_text(
        fitz.Point(PDF_MARGIN, state["y"]),
        "AWARE Local Report",
        fontsize=22,
        fontname=PDF_FONT_BOLD,
        color=PDF_TEXT_COLOR,
    )
    state["y"] += 18
    page.insert_text(
        fitz.Point(PDF_MARGIN, state["y"]),
        "Single-document AI-writing pattern review",
        fontsize=10,
        fontname=PDF_FONT_REGULAR,
        color=PDF_MUTED_COLOR,
    )
    state["y"] += 20
    page.draw_line(
        fitz.Point(PDF_MARGIN, state["y"]),
        fitz.Point(PDF_CONTENT_RIGHT, state["y"]),
        color=PDF_RULE_COLOR,
        width=0.8,
    )
    state["y"] += 20


def _write_pdf_callout(
    document: fitz.Document,
    state: dict[str, Any],
    label: str,
    text: str,
) -> None:
    label_height = 13
    padding = 12
    body_lines = _wrap_pdf_text(
        text,
        PDF_CONTENT_WIDTH - (padding * 2),
        PDF_SMALL_FONT_SIZE,
        PDF_FONT_REGULAR,
    )
    height = padding + label_height + 5 + (len(body_lines) * 12) + padding
    _ensure_pdf_space(document, state, height + 8)

    page = state["page"]
    rect = fitz.Rect(
        PDF_MARGIN,
        state["y"],
        PDF_CONTENT_RIGHT,
        state["y"] + height,
    )
    page.draw_rect(rect, color=PDF_RULE_COLOR, fill=PDF_CALLOUT_FILL, width=0.5)
    page.draw_rect(
        fitz.Rect(PDF_MARGIN, state["y"], PDF_MARGIN + 4, state["y"] + height),
        color=None,
        fill=PDF_ACCENT_COLOR,
    )
    page.insert_text(
        fitz.Point(PDF_MARGIN + padding, state["y"] + padding),
        label,
        fontsize=9,
        fontname=PDF_FONT_BOLD,
        color=PDF_TEXT_COLOR,
    )

    y = state["y"] + padding + label_height + 5
    for line in body_lines:
        page.insert_text(
            fitz.Point(PDF_MARGIN + padding, y),
            line,
            fontsize=PDF_SMALL_FONT_SIZE,
            fontname=PDF_FONT_REGULAR,
            color=PDF_MUTED_COLOR,
        )
        y += 12

    state["y"] += height + 18
    state["x"] = PDF_MARGIN


def _write_pdf_section_heading(
    document: fitz.Document,
    state: dict[str, Any],
    text: str,
) -> None:
    _ensure_pdf_space(document, state, 36)
    page = state["page"]
    page.insert_text(
        fitz.Point(PDF_MARGIN, state["y"]),
        text,
        fontsize=13,
        fontname=PDF_FONT_BOLD,
        color=PDF_TEXT_COLOR,
    )
    state["y"] += 9
    page.draw_line(
        fitz.Point(PDF_MARGIN, state["y"]),
        fitz.Point(PDF_CONTENT_RIGHT, state["y"]),
        color=PDF_RULE_COLOR,
        width=0.6,
    )
    state["y"] += 18
    state["x"] = PDF_MARGIN


def _write_pdf_metric_cards(
    document: fitz.Document,
    state: dict[str, Any],
    document_score: dict[str, Any],
) -> None:
    card_gap = 8
    card_width = (PDF_CONTENT_WIDTH - (card_gap * 3)) / 4
    card_height = 54
    _ensure_pdf_space(document, state, card_height + 18)

    metrics = [
        ("Risk score", f"{document_score['overall_risk_score']:.2f}", None),
        (
            "Risk level",
            document_score["overall_risk_level"],
            PDF_RISK_COLORS.get(document_score["overall_risk_level"]),
        ),
        ("Word count", str(document_score["total_word_count"]), None),
        ("Matches", str(document_score["total_matches"]), None),
    ]

    page = state["page"]
    for index, (label, value, accent_color) in enumerate(metrics):
        x0 = PDF_MARGIN + index * (card_width + card_gap)
        rect = fitz.Rect(x0, state["y"], x0 + card_width, state["y"] + card_height)
        fill = accent_color or PDF_CALLOUT_FILL
        label_color = (1, 1, 1) if accent_color else PDF_MUTED_COLOR
        value_color = (1, 1, 1) if accent_color else PDF_TEXT_COLOR
        border_color = accent_color or PDF_RULE_COLOR

        page.draw_rect(rect, color=border_color, fill=fill, width=0.5)
        page.insert_text(
            fitz.Point(x0 + 10, state["y"] + 17),
            label.upper(),
            fontsize=7.5,
            fontname=PDF_FONT_BOLD,
            color=label_color,
        )
        page.insert_text(
            fitz.Point(x0 + 10, state["y"] + 39),
            value,
            fontsize=14,
            fontname=PDF_FONT_BOLD,
            color=value_color,
        )

    state["y"] += card_height + 22
    state["x"] = PDF_MARGIN


def _write_pdf_text_block(
    document: fitz.Document,
    state: dict[str, Any],
    label: str,
    text: str,
) -> None:
    padding = 12
    body_width = PDF_CONTENT_WIDTH - (padding * 2)
    body_lines = _wrap_pdf_text(text, body_width, PDF_BODY_FONT_SIZE, PDF_FONT_REGULAR)
    height = padding + 13 + 5 + (len(body_lines) * PDF_BODY_LINE_HEIGHT) + padding
    _ensure_pdf_space(document, state, height + 12)

    page = state["page"]
    rect = fitz.Rect(
        PDF_MARGIN,
        state["y"],
        PDF_CONTENT_RIGHT,
        state["y"] + height,
    )
    page.draw_rect(rect, color=PDF_RULE_COLOR, fill=(1, 1, 1), width=0.5)
    page.insert_text(
        fitz.Point(PDF_MARGIN + padding, state["y"] + padding),
        label,
        fontsize=9,
        fontname=PDF_FONT_BOLD,
        color=PDF_ACCENT_COLOR,
    )

    y = state["y"] + padding + 18
    for line in body_lines:
        page.insert_text(
            fitz.Point(PDF_MARGIN + padding, y),
            line,
            fontsize=PDF_BODY_FONT_SIZE,
            fontname=PDF_FONT_REGULAR,
            color=PDF_TEXT_COLOR,
        )
        y += PDF_BODY_LINE_HEIGHT

    state["y"] += height + 14
    state["x"] = PDF_MARGIN


def _write_highlighted_pdf_text(
    document: fitz.Document,
    state: dict[str, Any],
    text: str,
    matches: list[dict[str, Any]],
) -> None:
    for segment_text, severity in _highlight_segments(text, matches):
        for token in _pdf_tokens(segment_text):
            if token == "\n":
                _pdf_new_line(document, state, PDF_BODY_LINE_HEIGHT)
                continue
            _write_pdf_token(
                document,
                state,
                token,
                PDF_HIGHLIGHT_COLORS.get(str(severity).lower()) if severity else None,
                PDF_BODY_FONT_SIZE,
                PDF_BODY_LINE_HEIGHT,
            )
    state["text_panel_active"] = False
    state["left"] = PDF_MARGIN
    state["right"] = PDF_CONTENT_RIGHT


def _write_pdf_token(
    document: fitz.Document,
    state: dict[str, Any],
    token: str,
    highlight_color: tuple[float, float, float] | None,
    font_size: float,
    line_height: int,
) -> None:
    if not token:
        return

    token = " " if token.isspace() else token
    token_width = fitz.get_text_length(
        token,
        fontname=PDF_FONT_REGULAR,
        fontsize=font_size,
    )
    left_edge = float(state.get("left", PDF_MARGIN))
    right_edge = float(state.get("right", PDF_CONTENT_RIGHT))

    if state["x"] > left_edge and state["x"] + token_width > right_edge:
        _pdf_new_line(document, state, line_height)

    if state["x"] == left_edge and token.isspace():
        return

    _ensure_pdf_space(document, state, line_height)
    page = state["page"]

    if highlight_color:
        rect = fitz.Rect(
            state["x"] - 0.5,
            state["y"] - font_size,
            state["x"] + token_width + 0.5,
            state["y"] + 2,
        )
        page.draw_rect(rect, color=None, fill=highlight_color, overlay=True)

    page.insert_text(
        fitz.Point(state["x"], state["y"]),
        token,
        fontsize=font_size,
        fontname=PDF_FONT_REGULAR,
        color=(0, 0, 0),
        overlay=True,
    )
    state["x"] += token_width


def _pdf_new_line(
    document: fitz.Document,
    state: dict[str, Any],
    line_height: int,
) -> None:
    state["x"] = float(state.get("left", PDF_MARGIN))
    state["y"] += line_height
    _ensure_pdf_space(document, state, line_height)


def _ensure_pdf_space(
    document: fitz.Document,
    state: dict[str, Any],
    needed_height: int,
) -> None:
    if state["y"] + needed_height <= PDF_PAGE_HEIGHT - PDF_MARGIN:
        return

    state["page"] = document.new_page(width=PDF_PAGE_WIDTH, height=PDF_PAGE_HEIGHT)
    state["x"] = float(state.get("left", PDF_MARGIN))
    state["y"] = PDF_MARGIN
    if state.get("text_panel_active"):
        _draw_pdf_text_panel(state)


def _start_pdf_text_panel(document: fitz.Document, state: dict[str, Any]) -> None:
    _ensure_pdf_space(document, state, 80)
    state["text_panel_active"] = True
    state["left"] = PDF_MARGIN + 14
    state["right"] = PDF_CONTENT_RIGHT - 14
    state["x"] = state["left"]
    state["y"] += 4
    _draw_pdf_text_panel(state)
    state["y"] += 15


def _draw_pdf_text_panel(state: dict[str, Any]) -> None:
    page = state["page"]
    top = max(PDF_MARGIN - 8, state["y"] - 10)
    rect = fitz.Rect(
        PDF_MARGIN,
        top,
        PDF_CONTENT_RIGHT,
        PDF_PAGE_HEIGHT - PDF_MARGIN,
    )
    page.draw_rect(rect, color=PDF_RULE_COLOR, fill=PDF_PANEL_FILL, width=0.5)


def _add_pdf_footers(document: fitz.Document) -> None:
    total_pages = document.page_count
    for page_number, page in enumerate(document, start=1):
        page.draw_line(
            fitz.Point(PDF_MARGIN, PDF_FOOTER_Y - 12),
            fitz.Point(PDF_CONTENT_RIGHT, PDF_FOOTER_Y - 12),
            color=PDF_RULE_COLOR,
            width=0.5,
        )
        page.insert_text(
            fitz.Point(PDF_MARGIN, PDF_FOOTER_Y),
            "AWARE Local",
            fontsize=PDF_SMALL_FONT_SIZE,
            fontname=PDF_FONT_REGULAR,
            color=PDF_MUTED_COLOR,
        )
        page_label = f"Page {page_number} of {total_pages}"
        label_width = fitz.get_text_length(
            page_label,
            fontname=PDF_FONT_REGULAR,
            fontsize=PDF_SMALL_FONT_SIZE,
        )
        page.insert_text(
            fitz.Point(PDF_CONTENT_RIGHT - label_width, PDF_FOOTER_Y),
            page_label,
            fontsize=PDF_SMALL_FONT_SIZE,
            fontname=PDF_FONT_REGULAR,
            color=PDF_MUTED_COLOR,
        )


def _highlight_segments(
    text: str,
    matches: list[dict[str, Any]],
) -> list[tuple[str, str | None]]:
    ordered_matches = sorted(
        matches,
        key=lambda match: (match["start_offset"], match["end_offset"]),
    )
    segments: list[tuple[str, str | None]] = []
    cursor = 0

    for match in ordered_matches:
        start = max(0, int(match["start_offset"]))
        end = min(len(text), int(match["end_offset"]))
        if start < cursor or end <= start:
            continue

        if start > cursor:
            segments.append((text[cursor:start], None))
        segments.append((text[start:end], str(match.get("severity", "")).lower()))
        cursor = end

    if cursor < len(text):
        segments.append((text[cursor:], None))
    return segments


def _pdf_tokens(text: str) -> list[str]:
    return regex.findall(r"\n|[^\S\n]+|\S+", text)


def _wrap_pdf_text(
    text: str,
    max_width: float,
    font_size: float,
    fontname: str,
) -> list[str]:
    lines: list[str] = []
    for source_line in text.splitlines() or [""]:
        words = source_line.split()
        if not words:
            lines.append("")
            continue

        current = words[0]
        for word in words[1:]:
            candidate = current + " " + word
            if (
                fitz.get_text_length(
                    candidate,
                    fontname=fontname,
                    fontsize=font_size,
                )
                <= max_width
            ):
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines

