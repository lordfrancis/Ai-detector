"""Text cleaning utilities."""

from __future__ import annotations

import regex


def normalize_quotes(text: str) -> str:
    """Normalize curly single and double quotes while preserving em dashes."""
    replacements = {
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
    }
    normalized = text
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return normalized


def normalize_whitespace(text: str) -> str:
    """Normalize horizontal whitespace without collapsing paragraph breaks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = regex.sub(r"[^\S\n]+", " ", text)
    return "\n".join(line.strip() for line in text.split("\n"))


def remove_extra_blank_lines(text: str) -> str:
    """Collapse repeated blank lines to a single paragraph break."""
    return regex.sub(r"\n\s*\n+", "\n\n", text).strip()


def clean_text(text: str) -> str:
    """Apply light cleanup before analysis without rewriting the content."""
    text = normalize_quotes(text)
    text = normalize_whitespace(text)
    return remove_extra_blank_lines(text)
