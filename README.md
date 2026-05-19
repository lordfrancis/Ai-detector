# AWARE Local

AI Writing Academic Review Engine - Local Edition

AWARE Local is a personal, offline AI-writing pattern checker for academic English text. It is designed as a review aid, not as a conclusive AI authorship detector.

## Disclaimer

This tool identifies writing patterns that may be associated with AI-generated or AI-assisted academic text. The result is not conclusive proof of AI use. Use this report as a review aid together with drafts, version history, oral explanation, and human judgment.

## Current Status

This repository is at Milestone 1 of the development plan:

- Streamlit project scaffold
- Minimal local app
- Pasted-text input
- Placeholder analysis flow
- Initial folders for the future analysis engine

The rule checker, scoring engine, highlighting, file uploads, and report exports are planned next.

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

## Supported Input Types

Current:

- Pasted text

Planned:

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

1. YAML rule loading
2. Phrase and regex matching
3. Document and paragraph scoring
4. Highlighted flagged text
5. TXT, DOCX, and PDF upload support
6. Markdown and JSON export
7. Unit tests and scoring calibration
