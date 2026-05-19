from engine.preprocessor import clean_text


def test_clean_text_normalizes_quotes_and_whitespace() -> None:
    text = "  “Quoted”   text\r\n\r\n\r\nNext   line.  "

    assert clean_text(text) == '"Quoted" text\n\nNext line.'


def test_clean_text_preserves_em_dash() -> None:
    assert clean_text("Before — after") == "Before — after"
