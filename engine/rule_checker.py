"""Rule loading and pattern matching utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import regex
import yaml

from engine.config import get_scoring_config
from engine.segmenter import split_paragraphs, split_sentences


SUPPORTED_PATTERN_TYPES = {"phrase", "regex"}


def load_rules(path: str) -> list[dict[str, Any]]:
    """Load and validate AI-writing pattern rules from a YAML file."""
    rule_path = Path(path)
    if not rule_path.exists():
        raise FileNotFoundError(f"Rule file not found: {path}")

    with rule_path.open("r", encoding="utf-8") as file:
        rules = yaml.safe_load(file) or []

    if not isinstance(rules, list):
        raise ValueError("Rule file must contain a list of rules.")

    return [_validate_rule(rule, index) for index, rule in enumerate(rules, start=1)]


def check_text(text: str, rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply rules to a full text block and return structured matches."""
    matches: list[dict[str, Any]] = []
    search_start = 0

    for paragraph_index, paragraph in enumerate(split_paragraphs(text)):
        paragraph_start = text.find(paragraph, search_start)
        if paragraph_start == -1:
            paragraph_start = search_start

        paragraph_matches = _check_text_segment(
            text=paragraph,
            rules=rules,
            paragraph_index=paragraph_index,
            base_offset=paragraph_start,
        )
        matches.extend(paragraph_matches)
        search_start = paragraph_start + len(paragraph)

    return sorted(matches, key=lambda match: (match["start_offset"], match["end_offset"]))


def check_paragraph(
    paragraph: str,
    paragraph_index: int,
    rules: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Apply rules to a single paragraph and include its paragraph index."""
    return _check_text_segment(
        text=paragraph,
        rules=rules,
        paragraph_index=paragraph_index,
        base_offset=0,
    )


def _validate_rule(rule: Any, index: int) -> dict[str, Any]:
    if not isinstance(rule, dict):
        raise ValueError(f"Rule #{index} must be a mapping.")

    required_fields = [
        "id",
        "category",
        "severity",
        "pattern_type",
        "patterns",
        "explanation",
    ]
    missing_fields = [field for field in required_fields if field not in rule]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise ValueError(f"Rule #{index} is missing required field(s): {missing}")

    pattern_type = rule["pattern_type"]
    if pattern_type not in SUPPORTED_PATTERN_TYPES:
        raise ValueError(
            f"Rule {rule['id']} uses unsupported pattern_type: {pattern_type}"
        )

    if not isinstance(rule["patterns"], list) or not rule["patterns"]:
        raise ValueError(f"Rule {rule['id']} must define at least one pattern.")

    if not all(isinstance(pattern, str) for pattern in rule["patterns"]):
        raise ValueError(f"Rule {rule['id']} patterns must all be strings.")

    rule["weight"] = _rule_weight(rule)

    if pattern_type == "regex":
        for pattern in rule["patterns"]:
            try:
                regex.compile(pattern, flags=_regex_flags(rule))
            except regex.error as error:
                raise ValueError(
                    f"Rule {rule['id']} has invalid regex pattern: {pattern}"
                ) from error

    return rule


def _rule_weight(rule: dict[str, Any]) -> int:
    if "weight" in rule:
        try:
            return int(rule["weight"])
        except (TypeError, ValueError) as error:
            raise ValueError(f"Rule {rule['id']} weight must be an integer.") from error

    severity_weights = get_scoring_config()["severity_weights"]
    severity = str(rule["severity"]).lower()
    if severity not in severity_weights:
        raise ValueError(
            f"Rule {rule['id']} has no weight and uses unknown severity: {severity}"
        )
    return int(severity_weights[severity])


def _check_text_segment(
    text: str,
    rules: list[dict[str, Any]],
    paragraph_index: int | None,
    base_offset: int,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []

    for rule in rules:
        if rule["pattern_type"] == "phrase":
            matches.extend(_match_phrase_rule(text, rule, paragraph_index, base_offset))
        elif rule["pattern_type"] == "regex":
            matches.extend(_match_regex_rule(text, rule, paragraph_index, base_offset))

    return sorted(matches, key=lambda match: (match["start_offset"], match["end_offset"]))


def _match_phrase_rule(
    text: str,
    rule: dict[str, Any],
    paragraph_index: int | None,
    base_offset: int,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []

    for phrase in rule["patterns"]:
        escaped_phrase = regex.escape(phrase)
        pattern = rf"(?<!\w){escaped_phrase}(?!\w)"
        for match in regex.finditer(pattern, text, flags=regex.IGNORECASE):
            matches.append(_build_match(rule, match, paragraph_index, text, base_offset))

    return matches


def _match_regex_rule(
    text: str,
    rule: dict[str, Any],
    paragraph_index: int | None,
    base_offset: int,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []

    for pattern in rule["patterns"]:
        for match in regex.finditer(pattern, text, flags=_regex_flags(rule)):
            matches.append(_build_match(rule, match, paragraph_index, text, base_offset))

    return matches


def _build_match(
    rule: dict[str, Any],
    match: regex.Match[str],
    paragraph_index: int | None,
    text: str,
    base_offset: int,
) -> dict[str, Any]:
    return {
        "rule_id": rule["id"],
        "category": rule["category"],
        "severity": rule["severity"],
        "weight": rule["weight"],
        "matched_text": match.group(0),
        "paragraph_index": paragraph_index,
        "sentence_index": _sentence_index_for_offset(text, match.start()),
        "start_offset": base_offset + match.start(),
        "end_offset": base_offset + match.end(),
        "explanation": rule["explanation"],
        "reviewer_note": rule.get("reviewer_note", ""),
    }


def _sentence_index_for_offset(text: str, offset: int) -> int | None:
    search_start = 0

    for sentence_index, sentence in enumerate(split_sentences(text)):
        sentence_start = text.find(sentence, search_start)
        if sentence_start == -1:
            continue

        sentence_end = sentence_start + len(sentence)
        if sentence_start <= offset < sentence_end:
            return sentence_index

        search_start = sentence_end

    return None


def _regex_flags(rule: dict[str, Any]) -> int:
    if rule.get("case_sensitive", False):
        return 0
    return regex.IGNORECASE
