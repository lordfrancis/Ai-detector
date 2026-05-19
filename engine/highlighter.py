"""Highlighted text rendering utilities."""

from __future__ import annotations

from html import escape
from typing import Any


SEVERITY_CLASS_BY_LEVEL = {
    "low": "aware-highlight-low",
    "medium": "aware-highlight-medium",
    "high": "aware-highlight-high",
    "critical": "aware-highlight-critical",
}


def highlight_matches(text: str, matches: list[dict[str, Any]]) -> str:
    """Return HTML with non-overlapping matches highlighted."""
    ordered_matches = sorted(
        matches,
        key=lambda match: (match["start_offset"], match["end_offset"]),
    )

    fragments: list[str] = []
    cursor = 0

    for match in ordered_matches:
        start = max(0, int(match["start_offset"]))
        end = min(len(text), int(match["end_offset"]))
        if start < cursor or end <= start:
            continue

        fragments.append(_render_plain_text(text[cursor:start]))
        fragments.append(_render_highlight(text[start:end], match))
        cursor = end

    fragments.append(_render_plain_text(text[cursor:]))
    return '<div class="aware-highlighted-text">' + "".join(fragments) + "</div>"


def _render_plain_text(text: str) -> str:
    return escape(text).replace("\n", "<br>")


def _render_highlight(text: str, match: dict[str, Any]) -> str:
    severity = str(match.get("severity", "")).lower()
    css_class = SEVERITY_CLASS_BY_LEVEL.get(severity, "aware-highlight-medium")
    title = escape(f"{match.get('category', 'Flagged pattern')}: {match.get('explanation', '')}")
    content = _render_plain_text(text)
    return f'<mark class="{css_class}" title="{title}">{content}</mark>'
