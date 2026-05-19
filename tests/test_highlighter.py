from engine.highlighter import highlight_matches


def test_highlight_matches_wraps_matching_offsets() -> None:
    text = "This plays a crucial role."
    matches = [
        {
            "start_offset": 5,
            "end_offset": 25,
            "severity": "high",
            "category": "Inflated significance",
            "explanation": "Review this phrase.",
        }
    ]

    html = highlight_matches(text, matches)

    assert '<mark class="aware-highlight-high"' in html
    assert "plays a crucial role" in html


def test_highlight_matches_escapes_html() -> None:
    text = "<script>alert('x')</script> plays a crucial role."
    matches = [
        {
            "start_offset": 29,
            "end_offset": 49,
            "severity": "medium",
            "category": "Category",
            "explanation": "Explanation",
        }
    ]

    html = highlight_matches(text, matches)

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_highlight_matches_skips_overlapping_ranges() -> None:
    text = "evolving landscape"
    matches = [
        {
            "start_offset": 0,
            "end_offset": 18,
            "severity": "high",
            "category": "First",
            "explanation": "",
        },
        {
            "start_offset": 9,
            "end_offset": 18,
            "severity": "medium",
            "category": "Second",
            "explanation": "",
        },
    ]

    html = highlight_matches(text, matches)

    assert html.count("<mark") == 1
