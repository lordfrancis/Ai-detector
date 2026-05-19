from engine.analyzer import analyze_text


def test_analyze_text_returns_document_scores_and_matches() -> None:
    result = analyze_text("This plays a crucial role in the evolving landscape.")

    assert result["rules_used"] > 0
    assert result["document_score"]["total_matches"] == 2
    assert result["paragraph_scores"][0]["paragraph_number"] == 1
    assert result["matches"][0]["paragraph_index"] == 0
    assert result["interpretation"]
    assert result["reviewer_recommendation"]
    assert result["top_reasons"]
    assert result["category_summary"]
    assert result["highest_risk_paragraphs"]


def test_analyze_text_cleans_whitespace_before_analysis() -> None:
    result = analyze_text("  This   plays a crucial role.\n\n\n")

    assert result["text"] == "This plays a crucial role."
    assert result["document_score"]["total_matches"] == 1


def test_analyze_text_threads_sensitivity_into_scores() -> None:
    text = "This plays a crucial role. " + ("plain wording " * 120)
    low_result = analyze_text(text, sensitivity=1)
    high_result = analyze_text(text, sensitivity=5)

    assert (
        low_result["document_score"]["overall_risk_score"]
        < high_result["document_score"]["overall_risk_score"]
    )
