from engine.rule_checker import check_paragraph, check_text, load_rules


def test_load_rules_reads_yaml_rules() -> None:
    rules = load_rules("rules/ai_patterns.yaml")

    assert rules
    assert rules[0]["id"] == "inflated_001"
    assert rules[0]["pattern_type"] == "phrase"


def test_load_rules_covers_initial_category_set() -> None:
    rules = load_rules("rules/ai_patterns.yaml")
    categories = {rule["category"] for rule in rules}

    assert len(categories) >= 20


def test_check_text_finds_phrase_rule_case_insensitively() -> None:
    rules = load_rules("rules/ai_patterns.yaml")
    text = "The project Plays a Crucial Role in student support."

    matches = check_text(text, rules)

    assert any(match["matched_text"] == "Plays a Crucial Role" for match in matches)
    assert any(match["rule_id"] == "inflated_001" for match in matches)


def test_check_text_finds_regex_rule() -> None:
    rules = load_rules("rules/ai_patterns.yaml")
    text = "The claim is broad — polished — balanced — and needs evidence."

    matches = check_text(text, rules)

    assert any(match["rule_id"] == "emdash_001" for match in matches)


def test_emdash_rule_ignores_single_em_dash() -> None:
    rules = load_rules("rules/ai_patterns.yaml")
    text = "The claim is broad — and needs more evidence."

    matches = check_text(text, rules)

    assert not any(match["rule_id"] == "emdash_001" for match in matches)


def test_load_rules_defaults_weight_from_severity(tmp_path) -> None:
    rule_path = tmp_path / "rules.yaml"
    rule_path.write_text(
        "\n".join(
            [
                "- id: default_weight_001",
                "  category: Default weight",
                "  severity: high",
                "  pattern_type: phrase",
                "  patterns:",
                '    - "default weight"',
                '  explanation: "Uses configured severity weight."',
            ]
        ),
        encoding="utf-8",
    )

    rules = load_rules(str(rule_path))

    assert rules[0]["weight"] == 5


def test_check_paragraph_includes_paragraph_index() -> None:
    rules = load_rules("rules/ai_patterns.yaml")
    paragraph = "This wording underscores the importance of evidence."

    matches = check_paragraph(paragraph, paragraph_index=2, rules=rules)

    assert matches[0]["paragraph_index"] == 2
    assert matches[0]["start_offset"] == paragraph.index("underscores")


def test_check_text_includes_paragraph_and_sentence_indexes() -> None:
    rules = load_rules("rules/ai_patterns.yaml")
    text = (
        "This first paragraph is direct.\n\n"
        "The second paragraph is clear. It plays a crucial role in the review."
    )

    matches = check_text(text, rules)

    assert matches[0]["paragraph_index"] == 1
    assert matches[0]["sentence_index"] == 1
    assert matches[0]["start_offset"] == text.index("plays")


def test_case_sensitive_regex_rule_does_not_match_lowercase_heading() -> None:
    rules = load_rules("rules/ai_patterns.yaml")
    text = "method and findings"

    matches = check_text(text, rules)

    assert not any(match["rule_id"] == "title_heading_001" for match in matches)
