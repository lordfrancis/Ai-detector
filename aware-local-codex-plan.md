# AWARE Local: Development Plan for Codex

## 1. Project name

**AWARE Local**

Meaning:

**AI Writing Academic Review Engine - Local Edition**

This is a personal/offline AI-writing pattern checker that runs on the user's own laptop or desktop. It is intended as a self-use tool first, not a deployed institutional system.

## 2. Project goal

Build a local application that can analyze academic English text and identify writing patterns commonly associated with AI-generated or AI-assisted writing.

The system should not claim to prove that a text was written by AI. It should provide an explainable AI-writing risk report based on rule-based pattern detection and later statistical writing analysis.

## 3. Product positioning

AWARE Local is not a final AI detector.

It is an **AI-writing pattern checker** that:

1. Accepts pasted text or uploaded documents.
2. Extracts and cleans the text.
3. Detects AI-associated academic writing patterns.
4. Highlights flagged phrases.
5. Gives paragraph-level and document-level risk scores.
6. Explains why each phrase or sentence was flagged.
7. Exports a local report for review.

## 4. Initial scope

The first version will be local-only and single-user.

### Included

- Local Streamlit interface
- Paste text input
- TXT upload
- DOCX upload
- PDF upload
- Rule-based pattern detection
- Paragraph-level scoring
- Overall AI-writing risk level
- Flagged phrase table
- Basic highlighted text view
- Markdown report export
- JSON result export

### Excluded for now

- Login system
- Laravel
- PostgreSQL
- pgvector
- Mobile app
- Cloud deployment
- Multi-user support
- Plagiarism checking
- LLM-based rewriting
- Automatic student misconduct decision
- Paid SaaS features

## 5. Recommended tech stack

### Main stack

```text
Python
Streamlit
Regex
pandas
PyMuPDF
python-docx
Markdown export
JSON export
```

### Optional later

```text
spaCy
textstat
scikit-learn
sentence-transformers
SQLite
PostgreSQL + pgvector
FastAPI
```

## 6. Why Streamlit

Streamlit is ideal for this first local version because:

1. It runs locally in a browser.
2. It is fast to develop.
3. It supports file upload widgets.
4. It can display tables and reports easily.
5. It avoids the overhead of Laravel, database setup, and authentication.
6. It allows the project to focus first on the AI-writing analysis engine.

## 7. Basic app command

The project should run using:

```bash
streamlit run app.py
```

## 8. Proposed folder structure

```text
aware-local/
│
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── config/
│   ├── app_config.yaml
│   └── scoring_config.yaml
│
├── rules/
│   ├── ai_patterns.yaml
│   └── rule_categories.md
│
├── engine/
│   ├── __init__.py
│   ├── extractor.py
│   ├── preprocessor.py
│   ├── segmenter.py
│   ├── rule_checker.py
│   ├── scorer.py
│   ├── highlighter.py
│   └── report_generator.py
│
├── models/
│   ├── __init__.py
│   └── data_models.py
│
├── reports/
│   └── .gitkeep
│
├── samples/
│   ├── sample_human_like.txt
│   └── sample_ai_like.txt
│
└── tests/
    ├── test_rule_checker.py
    ├── test_scorer.py
    └── test_extractor.py
```

## 9. Main modules

### 9.1 app.py

Purpose:

- Main Streamlit user interface
- Handles text input and file upload
- Calls the analysis engine
- Displays the output

Main UI sections:

1. App title and disclaimer
2. Input method selector
3. Paste text area
4. File uploader
5. Analyze button
6. Overall result summary
7. Paragraph-level results
8. Flagged phrases table
9. Highlighted text view
10. Export buttons

### 9.2 extractor.py

Purpose:

Extract raw text from supported file types.

Supported formats:

- TXT
- DOCX
- PDF

Functions:

```python
extract_text_from_txt(file) -> str
extract_text_from_docx(file) -> str
extract_text_from_pdf(file) -> str
extract_text(uploaded_file) -> str
```

Notes:

- Use `python-docx` for DOCX.
- Use `PyMuPDF` for PDF.
- Do not implement OCR in Version 1.
- If a PDF is scanned and has no extractable text, return a clear error message.

### 9.3 preprocessor.py

Purpose:

Clean raw text before analysis.

Functions:

```python
normalize_whitespace(text: str) -> str
normalize_quotes(text: str) -> str
remove_extra_blank_lines(text: str) -> str
clean_text(text: str) -> str
```

Rules:

- Preserve paragraph breaks.
- Do not rewrite the text.
- Do not remove punctuation needed for detection.
- Preserve em dashes because they are part of the detection rules.

### 9.4 segmenter.py

Purpose:

Split text into paragraphs and sentences.

Functions:

```python
split_paragraphs(text: str) -> list[str]
split_sentences(paragraph: str) -> list[str]
```

Version 1 may use simple regex sentence splitting.

Later, this may be replaced with spaCy.

### 9.5 rule_checker.py

Purpose:

Apply AI-writing pattern rules to the text.

Functions:

```python
load_rules(path: str) -> list[dict]
check_text(text: str, rules: list[dict]) -> list[dict]
check_paragraph(paragraph: str, paragraph_index: int, rules: list[dict]) -> list[dict]
```

Each match should include:

```text
rule_id
category
severity
weight
matched_text
explanation
paragraph_index
sentence_index
start_offset
end_offset
```

### 9.6 scorer.py

Purpose:

Convert rule matches into risk scores.

Functions:

```python
score_paragraph(paragraph: str, matches: list[dict]) -> dict
score_document(text: str, paragraph_scores: list[dict]) -> dict
get_risk_level(score: float) -> str
```

Initial risk levels:

```text
0-20: Low
21-50: Moderate
51-80: High
81-100: Very high
```

### 9.7 highlighter.py

Purpose:

Create a highlighted display version of the text.

Functions:

```python
highlight_matches(text: str, matches: list[dict]) -> str
```

For Streamlit, the output may use simple HTML with background highlights.

### 9.8 report_generator.py

Purpose:

Generate Markdown and JSON reports.

Functions:

```python
generate_markdown_report(analysis_result: dict) -> str
generate_json_report(analysis_result: dict) -> dict
save_report(content: str, filename: str) -> str
```

## 10. Rule file design

Rules should be stored in:

```text
rules/ai_patterns.yaml
```

Example rule format:

```yaml
- id: inflated_001
  category: Inflated significance
  severity: high
  weight: 4
  pattern_type: phrase
  patterns:
    - "underscores the importance"
    - "underscores the critical importance"
    - "plays a crucial role"
    - "pivotal role"
    - "evolving landscape"
  explanation: "This phrase may indicate inflated academic significance commonly associated with AI-generated academic writing."
  reviewer_note: "Check whether the claim is specific, supported by evidence, and necessary."

- id: emdash_001
  category: Em dash usage
  severity: medium
  weight: 3
  pattern_type: regex
  patterns:
    - "—"
  explanation: "Frequent em dash usage may be associated with AI-generated or AI-polished writing."
  reviewer_note: "Review whether the punctuation style is natural for the writer and document type."
```

## 11. Initial rule categories

The first rule set should include:

1. Inflated significance claims
2. Promotional or exaggerated academic language
3. Vague attribution
4. Overused AI-associated vocabulary
5. Superficial "-ing" academic add-ons
6. Copula avoidance
7. Excessive hedging
8. Overly assertive causal claims
9. Generic positive conclusions
10. Formulaic challenges/future outlook phrasing
11. Em dash usage
12. Negative parallelisms
13. Rule-of-three overuse
14. Artificially condensed phrases
15. Non-locative use of "where"
16. Overuse of "via"
17. Overuse of "beyond"
18. Overuse of "yield"
19. Title-case academic headings
20. Unsupported vague claims

## 12. Initial scoring design

Each rule match contributes points.

Suggested weights:

```text
low severity: +1
medium severity: +2 or +3
high severity: +4 or +5
critical severity: +6
```

The raw score should be normalized by word count.

Suggested initial formula:

```text
normalized_score = (total_weight / total_words) * 1000
```

Then convert to 0-100 scale using a cap.

Suggested Version 1 formula:

```text
risk_score = min(100, normalized_score * 5)
```

This should be adjusted after testing on real samples.

## 13. Paragraph-level scoring

Each paragraph should have:

```text
paragraph_number
word_count
match_count
total_weight
risk_score
risk_level
top_categories
```

Paragraph-level scoring is important because AI-assisted writing may appear only in selected parts of a document.

## 14. Document-level scoring

The document report should show:

```text
overall_risk_score
overall_risk_level
total_word_count
total_matches
top_5_rule_categories
highest_risk_paragraphs
```

## 15. Disclaimer text

The app should display this disclaimer:

```text
This tool identifies writing patterns that may be associated with AI-generated or AI-assisted academic text. The result is not conclusive proof of AI use. Use this report as a review aid together with drafts, version history, oral explanation, and human judgment.
```

## 16. Streamlit UI layout

Recommended UI:

```text
Title: AWARE Local
Subtitle: AI Writing Academic Review Engine

Sidebar:
- Input method
- Rule sensitivity
- Show/hide low severity flags
- Export options

Main page:
1. Disclaimer
2. Text input or file upload
3. Analyze button
4. Overall score card
5. Score breakdown
6. Paragraph risk table
7. Flagged matches table
8. Highlighted document
9. Export report
```

## 17. Minimum viable version

The first working version should only do the following:

1. Accept pasted text.
2. Load rules from YAML.
3. Detect phrase and regex matches.
4. Score the document.
5. Display flagged matches in a table.
6. Display overall risk score.
7. Export Markdown report.

Do not start with DOCX/PDF extraction until the pasted-text version works.

## 18. Development milestones

### Milestone 1: Project setup

Tasks:

- Create folder structure.
- Create virtual environment.
- Create `requirements.txt`.
- Create `README.md`.
- Create `app.py`.
- Create sample rule file.

Expected result:

The app runs with:

```bash
streamlit run app.py
```

### Milestone 2: Rule engine

Tasks:

- Load YAML rules.
- Support phrase matching.
- Support regex matching.
- Return structured matches.
- Add unit tests.

Expected result:

Given a sample text, the engine returns all detected AI-writing patterns.

### Milestone 3: Scoring engine

Tasks:

- Count total matches.
- Apply rule weights.
- Normalize by word count.
- Assign risk level.
- Compute paragraph scores.

Expected result:

The app displays document-level and paragraph-level risk.

### Milestone 4: Streamlit interface

Tasks:

- Add text area.
- Add analyze button.
- Show summary score.
- Show matches table.
- Show paragraph table.
- Add basic highlighted text.

Expected result:

The app becomes usable for pasted academic text.

### Milestone 5: File upload

Tasks:

- Add TXT extraction.
- Add DOCX extraction.
- Add PDF extraction.
- Handle unreadable PDFs.

Expected result:

The app can analyze uploaded documents.

### Milestone 6: Report export

Tasks:

- Generate Markdown report.
- Generate JSON result.
- Add Streamlit download buttons.

Expected result:

The user can save analysis results locally.

### Milestone 7: Testing and calibration

Tasks:

- Test with human-written samples.
- Test with AI-generated samples.
- Adjust rule weights.
- Reduce false positives.
- Add missing patterns.

Expected result:

The checker becomes more useful and less noisy.

## 19. Suggested requirements.txt

```text
streamlit
pandas
PyYAML
pymupdf
python-docx
regex
```

Optional later:

```text
spacy
textstat
scikit-learn
sentence-transformers
```

## 20. Suggested README.md content

The README should include:

1. Project description
2. Disclaimer
3. Installation steps
4. How to run
5. Supported input types
6. Current limitations
7. Roadmap
8. Example usage

## 21. Suggested Codex task sequence

Use Codex in small steps. Do not ask Codex to build the whole project in one prompt.

### Codex Task 1

```text
Create a Python Streamlit project named AWARE Local. Set up the folder structure, requirements.txt, README.md, and a minimal app.py that displays the app title, disclaimer, text area, and Analyze button. Do not implement the analysis engine yet.
```

### Codex Task 2

```text
Implement a YAML-based rule loading system in engine/rule_checker.py. Rules should support phrase and regex pattern types. Create rules/ai_patterns.yaml with sample rules for em dash usage, inflated significance phrases, vague attribution, and AI-associated vocabulary.
```

### Codex Task 3

```text
Implement check_text and check_paragraph functions. They should return structured matches with rule_id, category, severity, weight, matched_text, paragraph_index, start_offset, end_offset, explanation, and reviewer_note.
```

### Codex Task 4

```text
Implement engine/scorer.py. Create functions to compute paragraph-level scores and document-level scores. Normalize scores by word count and assign risk levels: Low, Moderate, High, and Very high.
```

### Codex Task 5

```text
Connect the rule checker and scorer to app.py. When the user pastes text and clicks Analyze, show the overall risk score, total matches, paragraph risk table, and flagged matches table.
```

### Codex Task 6

```text
Implement engine/highlighter.py. Create a function that returns HTML-highlighted text for matched phrases. Show the highlighted text in Streamlit using st.markdown with unsafe_allow_html=True.
```

### Codex Task 7

```text
Implement file upload support for TXT, DOCX, and PDF. Use python-docx for DOCX and PyMuPDF for PDF. Add clear error messages for unsupported files and scanned PDFs with no extractable text.
```

### Codex Task 8

```text
Implement report export. Create a Markdown report and JSON result export. Add Streamlit download buttons for both formats.
```

### Codex Task 9

```text
Add unit tests for rule_checker.py and scorer.py using pytest. Include tests for phrase rules, regex rules, scoring, and risk level assignment.
```

### Codex Task 10

```text
Refactor the project for readability. Add type hints, docstrings, and comments where helpful. Ensure the app still runs with streamlit run app.py.
```

## 22. Testing samples

Create two sample files:

### sample_human_like.txt

A short academic paragraph with direct, specific claims and minimal inflated phrasing.

### sample_ai_like.txt

A paragraph containing:

```text
evolving landscape
underscores the importance
plays a crucial role
highlighting the need
not only ... but also
—
```

Use these to verify whether the checker flags the expected patterns.

## 23. Version 1 limitations

The first version will have limitations:

1. It cannot prove AI authorship.
2. It may flag formal human academic writing.
3. It may miss heavily edited AI text.
4. It does not understand the author's writing history.
5. It does not detect plagiarism.
6. It does not verify citations.
7. It does not perform OCR on scanned PDFs.
8. It depends on the quality of the rule file.

These limitations should be clearly stated in the README and app interface.

## 24. Future improvements

After Version 1 works, consider:

1. Add spaCy sentence segmentation.
2. Add statistical writing features.
3. Add local SQLite storage for past reports.
4. Add baseline comparison using pre-2022 academic writing.
5. Add machine learning classifier.
6. Add embedding support.
7. Add PDF report export.
8. Add batch document analysis.
9. Add rule editor inside the app.
10. Add calibration mode for adjusting rule weights.

## 25. Development priority

Build in this order:

```text
1. Paste text analysis
2. Rule loading
3. Pattern matching
4. Scoring
5. Results display
6. Highlighting
7. File upload
8. Report export
9. Testing
10. Calibration
```

## 26. Important design rule

Keep the analysis engine separate from the Streamlit UI.

The Streamlit app should only handle input and output.

The `engine/` modules should contain the actual analysis logic.

This will make it easier to later convert the project into:

- a FastAPI service
- a Laravel-integrated backend
- a desktop app
- a SaaS product

## 27. Final MVP definition

The MVP is complete when:

1. The app runs locally.
2. The user can paste academic text.
3. The app detects AI-writing patterns from YAML rules.
4. The app shows an overall risk score.
5. The app shows paragraph-level scores.
6. The app lists flagged phrases with explanations.
7. The app can export a Markdown report.
8. The README explains setup, usage, and limitations.

## 28. Recommended next action

Start with Codex Task 1.

Do not add PDF, DOCX, machine learning, or database features until the pasted-text rule checker works correctly.
