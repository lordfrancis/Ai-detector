# AWARE Local

AI Writing Academic Review Engine - Local Edition

AWARE Local is a personal, offline AI-writing pattern checker for academic English text. It is designed as a review aid, not as a conclusive AI authorship detector.

## Disclaimer

This tool identifies writing patterns that may be associated with AI-generated or AI-assisted academic text. The result is not conclusive proof of AI use. Use this report as a review aid together with drafts, version history, oral explanation, and human judgment.

## Current Status

This repository has a functional local MVP:

- Streamlit project scaffold
- Pasted-text input
- TXT, DOCX, and extractable PDF upload
- YAML rule loading
- Phrase and regex matching
- Initial rule coverage across the planned category set
- Text cleanup
- Paragraph and sentence segmentation
- Document and paragraph risk scoring
- Streamlit result tables for paragraph risk and flagged matches
- Highlighted flagged text
- Markdown and JSON report downloads

## Installation

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

If you are using the included virtual environment on Windows:

```bash
.\.venv\Scripts\streamlit.exe run app.py
```

## Supported Input Types

Current:

- Pasted text
- TXT
- DOCX
- PDF with extractable text

## Limitations

- It cannot prove AI authorship.
- It may flag formal human academic writing.
- It may miss heavily edited AI text.
- It does not compare against a writer's history.
- It does not detect plagiarism.
- It does not verify citations.
- It does not perform OCR on scanned PDFs.

## Roadmap

Completed:

1. YAML rule loading
2. Phrase and regex matching
3. Document and paragraph scoring
4. Highlighted flagged text
5. TXT, DOCX, and PDF upload support
6. Markdown and JSON export
7. Unit tests for the core engine

Next:

1. Calibrate weights with more real samples
2. Add optional statistical writing features
3. Add a local report history
4. Add a rule editor
