"""Top-level analysis orchestration for AWARE Local."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from engine.preprocessor import clean_text
from engine.rule_checker import check_text, load_rules
from engine.scorer import score_document, score_paragraph
from engine.segmenter import split_paragraphs


DEFAULT_RULE_PATH = Path("rules/ai_patterns.yaml")


def analyze_text(
    text: str,
    rule_path: str | Path = DEFAULT_RULE_PATH,
) -> dict[str, Any]:
    """Clean text, run rule checks, and return document-level analysis."""
    cleaned_text = clean_text(text)
    rules = load_rules(str(rule_path))
    paragraphs = split_paragraphs(cleaned_text)
    matches = check_text(cleaned_text, rules)

    paragraph_scores = []
    for paragraph_index, paragraph in enumerate(paragraphs):
        paragraph_matches = [
            match for match in matches if match["paragraph_index"] == paragraph_index
        ]
        paragraph_scores.append(
            score_paragraph(
                paragraph=paragraph,
                matches=paragraph_matches,
                paragraph_index=paragraph_index,
            )
        )

    document_score = score_document(
        text=cleaned_text,
        paragraph_scores=paragraph_scores,
        matches=matches,
    )

    return {
        "text": cleaned_text,
        "rules_used": len(rules),
        "paragraphs": paragraphs,
        "matches": matches,
        "paragraph_scores": paragraph_scores,
        "document_score": document_score,
        "interpretation": document_score["interpretation"],
        "reviewer_recommendation": document_score["reviewer_recommendation"],
        "top_reasons": document_score["top_reasons"],
        "category_summary": document_score["category_summary"],
        "highest_risk_paragraphs": document_score["highest_risk_paragraphs"],
    }
