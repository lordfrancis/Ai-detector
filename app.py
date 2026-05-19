from typing import Any

import pandas as pd
import streamlit as st

from engine.analyzer import analyze_text
from engine.extractor import extract_text
from engine.highlighter import highlight_matches


DISCLAIMER = (
    "This tool identifies writing patterns that may be associated with "
    "AI-generated or AI-assisted academic text. The result is not conclusive "
    "proof of AI use. Use this report as a review aid together with drafts, "
    "version history, oral explanation, and human judgment."
)


def main() -> None:
    st.set_page_config(
        page_title="AWARE Local",
        page_icon=":mag:",
        layout="wide",
    )

    st.title("AWARE Local")
    st.caption("AI Writing Academic Review Engine")

    st.info(DISCLAIMER)
    _inject_highlight_styles()

    st.sidebar.header("Input")
    input_method = st.sidebar.radio("Input method", ["Paste text", "Upload file"], index=0)
    st.sidebar.slider("Rule sensitivity", min_value=1, max_value=5, value=3)
    show_low_severity = st.sidebar.checkbox("Show low severity flags", value=True)

    st.subheader("Text to Analyze")

    text = ""
    uploaded_file = None
    if input_method == "Paste text":
        text = st.text_area(
            "Paste academic text",
            height=280,
            placeholder="Paste the text you want to review...",
        )
    else:
        uploaded_file = st.file_uploader(
            "Upload a document",
            type=["txt", "docx", "pdf"],
        )

    analyze_clicked = st.button("Analyze", type="primary")

    if analyze_clicked:
        try:
            source_text = _get_source_text(input_method, text, uploaded_file)
            analysis_result = analyze_text(source_text)
        except Exception as error:
            st.error(f"Analysis failed: {error}")
            return

        display_analysis_result(analysis_result, show_low_severity)

        with st.expander("Preview pasted text", expanded=False):
            st.write(analysis_result["text"])


def _get_source_text(input_method: str, text: str, uploaded_file: Any) -> str:
    if input_method == "Paste text":
        if not text.strip():
            raise ValueError("Paste text before running the analysis.")
        return text

    if uploaded_file is None:
        raise ValueError("Upload a TXT, DOCX, or PDF file before running the analysis.")

    extracted_text = extract_text(uploaded_file)
    if not extracted_text.strip():
        raise ValueError("No text could be extracted from the uploaded file.")
    return extracted_text


def display_analysis_result(
    analysis_result: dict[str, Any],
    show_low_severity: bool,
) -> None:
    document_score = analysis_result["document_score"]
    matches = analysis_result["matches"]
    if not show_low_severity:
        matches = [match for match in matches if match["severity"] != "low"]

    st.subheader("Overall Result")
    score_columns = st.columns(4)
    score_columns[0].metric(
        "Risk score",
        f"{document_score['overall_risk_score']:.2f}",
    )
    score_columns[1].metric("Risk level", document_score["overall_risk_level"])
    score_columns[2].metric("Total matches", document_score["total_matches"])
    score_columns[3].metric("Word count", document_score["total_word_count"])

    if document_score["top_5_rule_categories"]:
        st.caption(
            "Top categories: "
            + ", ".join(document_score["top_5_rule_categories"])
        )

    st.subheader("Paragraph Risk")
    st.dataframe(
        _paragraph_scores_dataframe(analysis_result["paragraph_scores"]),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Flagged Matches")
    if matches:
        st.dataframe(
            _matches_dataframe(matches),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No rule matches found for the current display settings.")

    st.subheader("Highlighted Document")
    st.markdown(
        highlight_matches(analysis_result["text"], matches),
        unsafe_allow_html=True,
    )


def _paragraph_scores_dataframe(paragraph_scores: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for score in paragraph_scores:
        rows.append(
            {
                "Paragraph": score["paragraph_number"],
                "Risk score": score["risk_score"],
                "Risk level": score["risk_level"],
                "Words": score["word_count"],
                "Matches": score["match_count"],
                "Weight": score["total_weight"],
                "Top categories": ", ".join(score["top_categories"]),
            }
        )
    return pd.DataFrame(rows)


def _matches_dataframe(matches: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for match in matches:
        rows.append(
            {
                "Paragraph": _one_based(match["paragraph_index"]),
                "Sentence": _one_based(match["sentence_index"]),
                "Matched text": match["matched_text"],
                "Category": match["category"],
                "Severity": match["severity"],
                "Weight": match["weight"],
                "Explanation": match["explanation"],
                "Reviewer note": match["reviewer_note"],
            }
        )
    return pd.DataFrame(rows)


def _one_based(index: int | None) -> int | None:
    if index is None:
        return None
    return index + 1


def _inject_highlight_styles() -> None:
    st.markdown(
        """
        <style>
        .aware-highlighted-text {
            border: 1px solid rgba(49, 51, 63, 0.2);
            border-radius: 6px;
            line-height: 1.7;
            padding: 1rem;
            white-space: normal;
        }
        .aware-highlighted-text mark {
            border-radius: 4px;
            color: inherit;
            padding: 0.08rem 0.2rem;
        }
        .aware-highlight-low {
            background: #e7f4ff;
        }
        .aware-highlight-medium {
            background: #fff1a8;
        }
        .aware-highlight-high {
            background: #ffd1a6;
        }
        .aware-highlight-critical {
            background: #ffb3b3;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
