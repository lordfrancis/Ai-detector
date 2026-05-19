"""Paragraph and sentence segmentation utilities."""

from __future__ import annotations

import regex


def split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs while ignoring empty paragraph breaks."""
    return [paragraph.strip() for paragraph in regex.split(r"\n\s*\n", text) if paragraph.strip()]


def split_sentences(paragraph: str) -> list[str]:
    """Split a paragraph into sentences with a simple regex-based heuristic."""
    normalized = paragraph.strip()
    if not normalized:
        return []

    return [
        sentence.strip()
        for sentence in regex.split(r"(?<=[.!?])\s+", normalized)
        if sentence.strip()
    ]
