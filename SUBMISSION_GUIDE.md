# Calibrated Audit minor project submission guide

For a concise speaking outline, use [PRESENTATION_NOTES.md](PRESENTATION_NOTES.md).

## What to demonstrate

1. Start the dashboard: `streamlit run app.py` after installing the project with `python3 -m pip install -e .`.
2. Keep **Mock LLM** selected for the offline demo. Open the presentation summary, group explorer, calibration controls, paired response inspector, statistical table, and export tab. Download the presentation PNG from the dashboard.
3. Run the reproducible command in [README.md](README.md#reproduce-the-offline-checks) to regenerate `results/verified_mock_all/`.
4. Show that an exact repeat (IDENTICAL) and a neutral surface edit (SHAM) are included alongside NAME, EXPLICIT, and SES variations. Explain that a single scenario has one independent template and therefore produces descriptive results only.

## Verified offline evidence

- `python3 -m unittest discover -v`: **32 tests passed** on October 21, 2026.
- Full mock audit: **156 prompts**, **152 matched pairs**, **154 metric/reference contrasts** across four built-in templates.
- The verified report is [results/verified_mock_all/audit_report.md](results/verified_mock_all/audit_report.md). Its results come from a synthetic deterministic provider and do not describe Gemini or OpenAI behavior.
- Default JSON/CSV exports omit raw prompts and responses. JSON includes condition labels, scorer method, hashes, model settings, timestamps, and provenance.

## Research interpretation

The contribution is a controlled, repeatable audit workflow with two calibration controls and explicit handling of failed responses. Its default cosine measure is lexical. A sentence transformer backend is optional and must be installed and enabled separately. The sentiment lexicon and embedding measure have smoke tests, but no external human-labeled validation. Four fixed templates do not support broad population claims or a fitted hierarchical model. The SHAM newline is a simple neutral edit, not edit-magnitude matched to each treatment.

The old files directly under `results/` are historical and unverified; see [results/README.md](results/README.md). Do not cite the old report's statistical or legal conclusions.

## Live-model evidence and presentation

- A complete **local Ollama** hiring-scenario run with `qwen2.5:7b` evaluated **21 requests and 20/20 matched pairs**, including IDENTICAL and SHAM controls. Its presentation graphic is [results/live_ollama_qwen25_swe/presentation_summary.png](results/live_ollama_qwen25_swe/presentation_summary.png). The template count is one, so those numbers are descriptive only.
- A live **Gemini** all-scenario run with `gemini-3.5-flash-lite` generated 84 requests, but only **43 responses and 28/80 matched pairs** were usable. Its [presentation graphic](results/live_gemini35_all_512/presentation_summary.png) marks the run **INCOMPLETE**. Do not use its aggregate figures as a complete four-scenario finding.
- Each graphic labels its source, pair coverage, decision denominator, and inference limit. For a teacher presentation, show the complete local-model graphic first, then the Gemini graphic as an example of why failed requests must be excluded and disclosed.

## Repeating a cloud audit

Add a provider API key to an untracked `.env` file, run a fresh audit with a named model, and inspect provider errors, paired responses, control behavior, and export provenance. Record the model ID, run settings, date, and number of valid pairs. Hosted-model output may change despite the same settings. Keep live results separate from the verified mock directory.
