from pathlib import Path

from engine.analyzer import analyze_text


def test_ai_like_sample_produces_multiple_flags() -> None:
    text = Path("samples/sample_ai_like.txt").read_text(encoding="utf-8")

    result = analyze_text(text)

    assert result["document_score"]["total_matches"] >= 4
    assert result["document_score"]["overall_risk_score"] > 0


def test_human_like_sample_stays_lower_than_ai_like_sample() -> None:
    human_text = Path("samples/sample_human_like.txt").read_text(encoding="utf-8")
    ai_text = Path("samples/sample_ai_like.txt").read_text(encoding="utf-8")

    human_result = analyze_text(human_text)
    ai_result = analyze_text(ai_text)

    assert human_result["document_score"]["total_matches"] < ai_result["document_score"]["total_matches"]
