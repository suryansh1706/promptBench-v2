# PromptBench

PromptBench explores how an AI response changes when a synthetic applicant's name, pronouns, nationality, or socioeconomic background cues change. Its main example is English, text-only, single-turn hiring evaluation; loan and tenant scenarios provide extensions.

This is an exploratory research prototype. A significant response difference does not establish discrimination, legal noncompliance, or fairness across real-world uses.

## Run it

Python 3.9 or newer is required.

```bash
python3 -m pip install -e .
streamlit run app.py
```

Choose **Mock LLM** for an offline demonstration. Its score/tone differences are deliberately programmed examples, not empirical findings about a live model. Gemini and OpenAI require `GEMINI_API_KEY` or `OPENAI_API_KEY`, supplied through the environment or dashboard sidebar. Live calls may incur provider charges.

## Reproduce the offline checks

From the repository root:

```bash
python3 -m unittest discover -v
python3 -m promptbench.cli audit --scenario all --provider mock --model promptbench-mock-v1 --samples-per-group 2 --temperature 0 --seed 42 --output-dir /tmp/promptbench-reproduction
```

The test suite exercises controlled fields, uncached identical calls, sham controls, calibrated contrasts, template-level inference, missing decisions, failed requests, parsers, and instrument smoke checks without live model calls. Mock text and metrics are deterministic for the same settings; timestamps, response IDs, latency, and audit IDs are runtime provenance and can differ.

A single-scenario run is useful for inspecting answers:

```bash
python3 -m promptbench.cli audit --scenario job_swe_001 --provider mock --model promptbench-mock-v1 --output-dir /tmp/promptbench-hiring
```

For a live provider, select its model explicitly:

```bash
promptbench audit --scenario job_swe_001 --provider gemini --model gemini-2.5-flash
promptbench audit --scenario job_swe_001 --provider openai --model gpt-4o-mini
```

The Gemini model ID is documented in [Google's model reference](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash). Availability depends on the provider/account. PromptBench preserves a requested model ID rather than silently replacing it. `--samples-per-group` accepts 1–5 names/cue examples. Run `promptbench audit --help` for options.

## Experimental conditions

Each scenario has one shared neutral reference. Its substantive numerical qualifications stay fixed.

| Condition | Changes | Held fixed |
| --- | --- | --- |
| `NAME` | Name drawn from a culturally associated name bank | Pronouns, nationality, education, neighborhood, activities |
| `EXPLICIT` | Pronouns alone, or nationality alone | Other profile fields |
| `SES` | Education, neighborhood, and activity cue bundle | Name, pronouns, nationality, substantive numerical qualifications |
| `IDENTICAL` | No prompt change; independent repeated provider call | Exact prompt and request settings |
| `SHAM` | Trailing newline formatting | All profile fields and substantive text |

Name-bank labels describe experimental cues; they do not identify a person's actual ethnicity. Neutral pronouns are a linguistic condition and do not establish gender identity. SES changes are bundled background proxies: education prestige and activities can influence perceived qualifications, so these comparisons cannot isolate income or a protected attribute.

All generated audit requests bypass the persistent cache, including the reference and identical repeats. Otherwise a cache hit could manufacture a zero noise floor. The SQLite cache remains available for explicitly cacheable requests through the Python API. Streamlit retains a completed run until its settings or run key change; rerunning the page is not a new experiment.

The sham control is a simple formatting perturbation. It is not edit-magnitude matched to each treatment. The mock provider can react to changed text through its deterministic hash; its identical controls remain deterministic and do not estimate a live API's stochastic noise.

## Measures and inference

The default similarity measure is weighted unigram/bigram term-frequency cosine. It has no inverse-document-frequency weighting and is a lexical overlap proxy, not a validated semantic embedding. Optional sentence-transformer scoring is available through the Python scorer API when the dependency/model is installed (`python3 -m pip install -e '.[embeddings]'`, then `BiasScorer(use_transformer_embeddings=True)`). The synopsis sentence-embedding requirement is met only when this optional backend is enabled and loaded; the default lexical cosine does not meet it. Exports record the method actually used. Sentiment uses a custom English evaluation lexicon with simple negation and boosters, not VADER or a validated demographic instrument.

For sentiment and numerical scores, the statistical engine reports paired deltas against the reference, plus treatment-minus-`IDENTICAL` and treatment-minus-`SHAM` contrasts. Names and repetitions sharing one reference are averaged within each scenario template before testing or resampling. `sample_size` counts templates; `observation_count` counts underlying valid pairs.

A single template yields descriptive means, p=1, and unavailable confidence intervals. Small template sets have limited resolution and power. Tests use sign flips, percentile bootstrap intervals, paired Cohen's dz, Benjamini–Hochberg and Bonferroni adjustments. These checks are exploratory: the four built-in scenarios are fixed examples, not a random population sample, and aggregation does not replace a larger design or a fitted hierarchical model.

Decision consistency excludes missing decisions from its denominator. Failed/blocked API completions are excluded from comparisons rather than scored as model evaluations. Selection rates ignore unknown decisions; a ratio is unavailable without at least two groups and one positive selection. Threshold flags are descriptive screening signals, not legal conclusions.

The no-LLM instrument smoke checks verify known identical/disjoint texts and simple sentiment direction. They do not establish external validity; human-labeled evaluation and a larger scenario/name sample remain necessary for a research claim.

## Outputs and privacy

Each CLI audit writes:

- `audit_report.md`: descriptive findings and limits
- `audit_dataset.json`: summary, conditions, metrics, and request provenance
- `audit_comparisons.csv`: metrics table
- `table_results.tex`: LaTeX table

JSON/JSONL exports omit raw prompts and responses by default. They retain synthetic group labels, request/model settings, cache flags, timestamps, provider model version/fingerprint when supplied, and SHA-256 hashes of exact prompts, system prompts, and responses. CSV contains metrics only. These are minimized exports, not a guarantee that arbitrary custom labels are anonymous. Review them before sharing.

For a private, fully inspectable JSON/JSONL export, call `DatasetExporter.export_to_json(..., include_raw_text=True)` or `export_to_jsonl(..., include_raw_text=True)` in Python. That opt-in includes raw prompts, system prompts, and responses. Never enter real personal information into custom templates unless you intend to send it to the selected provider.

API keys are excluded from export provenance. Exact live-output reproduction is not guaranteed by fixed temperature/seed because hosted models, infrastructure, and provider support can change.

## Project files

- `app.py`: Streamlit dashboard and paired-answer inspector
- `promptbench/perturbation/`: scenario templates and controlled variations
- `promptbench/query_pipeline/`: providers, concurrency, retries, cache handling
- `promptbench/metrics/`: lexical similarity, sentiment, decisions, and scores
- `promptbench/statistical_testing/`: template-level tests and calibrated contrasts
- `promptbench/reporting/`: reports and export helpers
- `ALGORITHMS_GUIDE.md`: implemented methods and assumptions
- `tests/`: offline regression and instrument smoke checks
