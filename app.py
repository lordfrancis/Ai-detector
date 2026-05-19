import streamlit as st


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

    st.sidebar.header("Input")
    input_method = st.sidebar.radio("Input method", ["Paste text"], index=0)
    st.sidebar.slider("Rule sensitivity", min_value=1, max_value=5, value=3)
    st.sidebar.checkbox("Show low severity flags", value=True)

    st.subheader("Text to Analyze")

    text = ""
    if input_method == "Paste text":
        text = st.text_area(
            "Paste academic text",
            height=280,
            placeholder="Paste the text you want to review...",
        )

    analyze_clicked = st.button("Analyze", type="primary")

    if analyze_clicked:
        cleaned_text = text.strip()
        if not cleaned_text:
            st.warning("Paste text before running the analysis.")
            return

        st.success("Text received. The analysis engine will be connected in the next milestone.")

        st.subheader("Current Input Summary")
        words = cleaned_text.split()
        st.metric("Word count", len(words))

        with st.expander("Preview pasted text", expanded=False):
            st.write(cleaned_text)


if __name__ == "__main__":
    main()
