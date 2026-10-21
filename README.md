# Calibrated Audit

Calibrated Audit checks whether an AI gives different answers when only a person's background changes. It keeps the person's skills and scores the same, swaps details such as names, pronouns, culture, education, or neighborhood, then compares the AI's answers.

It is a research tool for exploring possible differences. Its results do not prove that a model is fair or unfair in every real-world situation.

The distribution and dashboard are named **Calibrated Audit**. The existing Python import path (`promptbench`) and `promptbench` command remain available for compatibility; the package adds the `calibrated-audit` command.

## What it does

- Builds matching prompts from built-in scenarios or a prompt you write.
- Runs them with a demo model, Google Gemini, or OpenAI.
- Compares answers for meaning, tone, decisions, and scores.
- Uses statistical checks to help tell steady patterns from random changes.
- Varies gender, ethnicity, nationality, and socioeconomic cues one axis at a time.
- Includes identical-prompt repeats and neutral-name sham controls for calibration.
- Shows charts and comparisons in a web dashboard.
- Saves results as JSON, CSV, Markdown, and LaTeX files.
- Caches repeated model requests and retries some temporary API errors.

## How an audit works

1. Choose a scenario, such as hiring, a loan, or housing.
2. Calibrated Audit makes versions that keep the important qualifications the same while changing background details.
3. The selected model answers each version.
4. Calibrated Audit compares the answers and checks for patterns across groups.
5. You review the results and export files for further study.

The checks include answer similarity, sentiment changes, decision consistency, selection rates, confidence intervals, effect sizes, permutation tests, and a multiple-test correction. These measures are clues for review, not legal findings or a substitute for careful human evaluation.

## Run the dashboard

You need Python 3.11 or newer.

```bash
python -m pip install -e .
streamlit run app.py
```

Choose **Mock LLM** in the dashboard for an offline demo that needs no API key. For live requests, choose Gemini or OpenAI and provide the matching API key in the sidebar or as an environment variable:

- `GEMINI_API_KEY`
- `OPENAI_API_KEY`

Live model use may incur costs and is subject to the provider's limits. Keep API keys private; do not commit them.

## Run an audit in the terminal

After installing the project, run an offline demo:

```bash
calibrated-audit audit --scenario job_swe_001 --provider mock --output-dir results
```

Or use a live provider:

```bash
calibrated-audit audit --scenario job_swe_001 --provider gemini --model gemini-3.8-flash
calibrated-audit audit --scenario job_swe_001 --provider openai --model gpt-4o-mini
```

Use `--reps 5` (default) for repeated queries per prompt, `--embedding-model` to select a sentence-transformer, or `--models mock:promptbench-mock-v1,openai:gpt-4o-mini` to run multiple providers/models into separate output folders. Reports include run metadata, response exclusions, calibration summaries, and exploratory tests across decision flips, numeric score deltas, embedding similarity, and secondary sentiment deltas. Audits stop if over 10% of responses fail, are empty, or are refusals.

The first sentence-transformer run may need to download model weights. If the model cannot load, the scorer records the failure and uses its TF-IDF fallback. Use `--reps 1` for a small smoke run; repeated live provider calls may incur cost.

Set the matching API key first. Use `--scenario all` to run every built-in scenario. The command also accepts `--samples-per-group`, `--temperature`, `--seed`, and `--output-dir` options. Run `calibrated-audit audit --help` to see them.

Each audit writes these files to its output folder:

- `audit_report.md`: a short results summary
- `audit_dataset.json`: audit details in JSON
- `audit_comparisons.csv`: comparison rows in CSV
- `table_results.tex`: a LaTeX results table

## What is in the dashboard?

- **Summary and heatmaps:** view key measures and compare results by group.
- **Statistical results:** inspect tests, effect sizes, and confidence intervals.
- **Answer inspector:** read each paired prompt and response side by side.
- **Custom audit:** try a prompt template with demographic slots such as `{name}` or `{nationality}`.
- **Downloads:** save the audit data and a LaTeX table.

## Project files

- `app.py` — Streamlit dashboard
- `promptbench/perturbation/` — scenario templates and prompt variations
- `promptbench/query_pipeline/` — model providers, request handling, and caching
- `promptbench/metrics/` — answer and fairness measures
- `promptbench/statistical_testing/` — statistical checks
- `promptbench/reporting/` — reports and data exports
- `promptbench/cli.py` — terminal command
- `ALGORITHMS_GUIDE.md` — more detail about the methods
- `tests/` — project tests
