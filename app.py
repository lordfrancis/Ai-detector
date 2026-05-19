from typing import Any

import pandas as pd
import streamlit as st

from engine.analyzer import analyze_text
from engine.evaluator import evaluate_datasets
from engine.extractor import extract_text
from engine.highlighter import highlight_matches
from engine.report_generator import (
    generate_json_report_text,
    generate_markdown_report,
    generate_pdf_report,
)


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

    st.sidebar.header("Mode")
    mode = st.sidebar.radio("Mode", ["Analyze Text", "Calibration Mode"], index=0)

    if mode == "Calibration Mode":
        display_calibration_mode()
        return

    st.sidebar.header("Input")
    input_method = st.sidebar.radio("Input method", ["Paste text", "Upload file"], index=0)
    st.sidebar.slider("Rule sensitivity", min_value=1, max_value=5, value=3)

    st.sidebar.header("Displayed severities")
    selected_severities = _selected_severities()

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

        display_analysis_result(analysis_result, selected_severities)

        with st.expander("Preview pasted text", expanded=False):
            st.write(analysis_result["text"])


def display_calibration_mode() -> None:
    st.subheader("Calibration Mode")
    st.caption("Dataset folder: datasets/")

    if not st.button("Run Evaluation", type="primary"):
        st.info("Add .txt samples to datasets/ folders, then run evaluation.")
        return

    try:
        evaluation_result = evaluate_datasets()
    except Exception as error:
        st.error(f"Evaluation failed: {error}")
        return

    if evaluation_result["total_files"] == 0:
        st.info("No .txt files found in datasets/. Add samples before evaluating.")

    st.subheader("Category Metrics")
    st.dataframe(
        _category_metrics_dataframe(evaluation_result["category_summaries"]),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Top Triggered Rules")
    top_rules = evaluation_result["top_triggered_rules"]
    if top_rules:
        st.dataframe(
            _top_rules_dataframe(top_rules),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No rule triggers found in the current dataset.")

    with st.expander("File-level results", expanded=False):
        file_results = evaluation_result["file_results"]
        if file_results:
            st.dataframe(
                _file_results_dataframe(file_results),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No file-level results to show.")


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
    selected_severities: set[str],
) -> None:
    document_score = analysis_result["document_score"]
    matches = [
        match
        for match in analysis_result["matches"]
        if str(match["severity"]).lower() in selected_severities
    ]

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

    st.subheader("Result Interpretation")
    st.write(analysis_result["interpretation"])

    st.subheader("Reviewer Recommendation")
    st.write(analysis_result["reviewer_recommendation"])

    st.subheader("Top Reasons for This Score")
    if analysis_result["top_reasons"]:
        st.dataframe(
            _top_reasons_dataframe(analysis_result["top_reasons"]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No triggered categories found.")

    st.subheader("Highest-Risk Paragraphs")
    if analysis_result["highest_risk_paragraphs"]:
        st.dataframe(
            _highest_risk_paragraphs_dataframe(
                analysis_result["highest_risk_paragraphs"]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No paragraph-level risk detected.")

    st.subheader("Category Summary")
    if analysis_result["category_summary"]:
        st.dataframe(
            _single_document_category_summary_dataframe(
                analysis_result["category_summary"]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No category-level matches found.")

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

    st.subheader("Export Report")
    export_columns = st.columns(3)
    export_columns[0].download_button(
        "Download Markdown",
        data=generate_markdown_report(analysis_result),
        file_name="aware-local-report.md",
        mime="text/markdown",
    )
    export_columns[1].download_button(
        "Download PDF",
        data=generate_pdf_report(analysis_result),
        file_name="aware-local-report.pdf",
        mime="application/pdf",
    )
    export_columns[2].download_button(
        "Download JSON",
        data=generate_json_report_text(analysis_result),
        file_name="aware-local-result.json",
        mime="application/json",
    )


def _selected_severities() -> set[str]:
    selected = set()
    for severity in ("low", "medium", "high", "critical"):
        if st.sidebar.checkbox(
            f"Show {severity} severity flags",
            value=True,
            key=f"show_{severity}_severity",
        ):
            selected.add(severity)
    return selected


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


def _top_reasons_dataframe(top_reasons: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for reason in top_reasons:
        rows.append(
            {
                "Category": reason["category"],
                "Matches": reason["match_count"],
                "Weight": reason["total_weight"],
            }
        )
    return pd.DataFrame(rows)


def _highest_risk_paragraphs_dataframe(
    paragraph_scores: list[dict[str, Any]],
) -> pd.DataFrame:
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
                "Excerpt": score["excerpt"],
            }
        )
    return pd.DataFrame(rows)


def _single_document_category_summary_dataframe(
    category_summary: list[dict[str, Any]],
) -> pd.DataFrame:
    rows = []
    for summary in category_summary:
        severity_distribution = summary["severity_distribution"]
        rows.append(
            {
                "Category": summary["category"],
                "Matches": summary["match_count"],
                "Weight": summary["total_weight"],
                "Low": severity_distribution["low"],
                "Medium": severity_distribution["medium"],
                "High": severity_distribution["high"],
                "Critical": severity_distribution["critical"],
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


def _category_metrics_dataframe(category_summaries: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for summary in category_summaries:
        rows.append(
            {
                "Category": summary["category"],
                "Total files": summary["total_files"],
                "Average risk score": summary["average_risk_score"],
                "Low": summary["low_count"],
                "Moderate": summary["moderate_count"],
                "High": summary["high_count"],
                "Very high": summary["very_high_count"],
                "False positives": summary["false_positive_count"],
                "False negatives": summary["false_negative_count"],
            }
        )
    return pd.DataFrame(rows)


def _top_rules_dataframe(top_rules: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for rule in top_rules:
        rows.append(
            {
                "Category": rule["category"],
                "Rule ID": rule["rule_id"],
                "Rule category": rule["rule_category"],
                "Count": rule["count"],
                "% of category matches": rule["percentage_of_category_matches"],
            }
        )
    return pd.DataFrame(rows)


def _file_results_dataframe(file_results: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for result in file_results:
        rows.append(
            {
                "Category": result["category"],
                "Filename": result["filename"],
                "Risk score": result["risk_score"],
                "Risk level": result["risk_level"],
                "Total matches": result["total_matches"],
                "Word count": result["word_count"],
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
