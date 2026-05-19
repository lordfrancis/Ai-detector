from engine.segmenter import split_paragraphs, split_sentences


def test_split_paragraphs_ignores_blank_paragraphs() -> None:
    text = "First paragraph.\n\n\nSecond paragraph.\n\n"

    assert split_paragraphs(text) == ["First paragraph.", "Second paragraph."]


def test_split_sentences_uses_basic_punctuation_boundaries() -> None:
    paragraph = "First sentence. Second sentence? Third sentence!"

    assert split_sentences(paragraph) == [
        "First sentence.",
        "Second sentence?",
        "Third sentence!",
    ]
