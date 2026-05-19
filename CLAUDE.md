# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AWARE Local — an offline Streamlit app that flags AI-writing patterns in academic English text. It is a **review aid**, not a conclusive AI-authorship detector. Rules surface signals; humans interpret them.

## Commands

```bash
# Setup (Windows)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Run the app
streamlit run app.py
# or, using the bundled venv directly:
.\.venv\Scripts\streamlit.exe run app.py

# Tests
pytest                              # full suite
pytest tests/test_scorer.py         # single file
pytest tests/test_scorer.py::test_name   # single test
pytest -k "scorer and not document" # filtered
```

There is no linter or formatter configured in this repo.

## Architecture

The pipeline is a one-way data flow orchestrated by `engine/analyzer.py::analyze_text`. Every stage is a pure function over plain `dict`s/`list`s — there are no classes for the domain model (see `models/data_models.py`, which only defines `TypeAlias`es).

```
input text / uploaded file
    └─► engine.extractor.extract_text          (TXT / DOCX / PDF via PyMuPDF + python-docx)
        └─► engine.preprocessor.clean_text     (quote + whitespace normalization; preserves em dashes and paragraph breaks)
            └─► engine.segmenter               (split_paragraphs on blank lines, split_sentences by .!? )
            └─► engine.rule_checker            (load YAML rules; phrase + regex matchers; produces offsets per match)
                └─► engine.scorer              (per-paragraph + document risk, normalized to 0–100 via get_risk_level)
                    └─► app.py / engine.report_generator / engine.highlighter
```

Key invariants when modifying the engine:

- **Offsets are absolute into the cleaned text.** `rule_checker.check_text` runs per-paragraph but adds `base_offset` so `start_offset`/`end_offset` are valid indices into the full cleaned document. `highlighter.highlight_matches` and the Markdown/JSON exporters all rely on this. If you change segmentation or matching, preserve this contract.
- **`paragraph_index` / `sentence_index` are zero-based in the engine** and converted to one-based only at the UI/report boundary (see `app.py::_one_based`).
- **Rules are data, not code.** New patterns go in `rules/ai_patterns.yaml`. Each rule must have `id`, `category`, `severity`, `weight`, `pattern_type` (`phrase` or `regex`), `patterns` (list of strings), `explanation`; `reviewer_note` and `case_sensitive` are optional. `rule_checker._validate_rule` is the source of truth — it compiles every regex at load time, so invalid patterns fail fast.
- **Phrase rules are matched with `(?<!\w)…(?!\w)` word boundaries and `IGNORECASE`** by default. Regex rules respect `case_sensitive: true` to opt out.
- **Risk score formula** lives in `scorer._normalized_risk_score`: `min(100, (total_weight / word_count) * 1000 * 5)`. The `* 5` is a calibration knob — changes will shift every "Low/Moderate/High/Very high" band defined in `get_risk_level` (thresholds 20 / 50 / 80). `config/scoring_config.yaml` documents these bands but is **not** currently read at runtime; the values are hardcoded in `scorer.py`.
- **PDF extraction is text-layer only.** Scanned PDFs raise `ValueError` — there is no OCR.

## Tests

Tests live in `tests/` and mirror engine modules one-to-one (`test_scorer.py` ↔ `engine/scorer.py`, etc.). `test_samples.py` exercises end-to-end runs on fixtures in `samples/`. When adding a rule category or changing scoring, update both the targeted unit test and `test_samples.py`.
