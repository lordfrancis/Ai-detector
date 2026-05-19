from engine.analyzer import analyze_text


def test_analyze_text_returns_document_scores_and_matches() -> None:
    result = analyze_text("This plays a crucial role in the evolving landscape.")

    assert result["rules_used"] > 0
    assert result["document_score"]["total_matches"] == 2
    assert result["paragraph_scores"][0]["paragraph_number"] == 1
    assert result["matches"][0]["paragraph_index"] == 0


def test_analyze_text_cleans_whitespace_before_analysis() -> None:
    result = analyze_text("  This   plays a crucial role.\n\n\n")

    assert result["text"] == "This plays a crucial role."
    assert result["document_score"]["total_matches"] == 1
