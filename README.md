# Calibrated Audit

Calibrated Audit is an exploratory, reproducible framework for auditing whether
an LLM's response changes when the substantive qualifications of a synthetic
applicant remain fixed but demographic or background cues change. The primary
design is an English, text-only, single-turn hiring evaluation. Loan-eligibility
and tenant-screening scenarios are included as extensions.

This repository is a research prototype, not a validated fairness instrument.
A measured response difference does not establish discrimination, legal
non-compliance, or fairness in a real deployment. Results should be reported
with the model identifier, prompt conditions, valid-pair coverage, controls,
independent-template count, missing-response policy, and statistical limitations.

## Research question and estimand

The central question is:

> Holding substantive qualifications and evaluation instructions constant, does
> changing a synthetic applicant's name, pronouns, nationality, or bundled
> socioeconomic cues change the model's decision, numerical score, wording, or
> sentiment?

For a metric \(m\), each treatment pair has a within-pair difference:

`d_i = m(treatment_i) - m(reference_i)`

The reference is shared within each scenario template. Because multiple names
or cue examples can share one template-level reference, observations are nested.
The statistical engine therefore averages valid pair differences within each
template before inferential testing:

`D_t = mean(d_i for observations i in template t)`

The inferential sample size is the number of independent scenario templates,
not the number of names, requests, or paired answers. The repository currently
contains four fixed templates, so conclusions are exploratory and do not
represent a random sample of hiring, lending, or housing decisions.

## Contributions and research workflow

The implementation provides:

1. Controlled counterfactual prompt generation with explicit metadata.
2. Two calibration controls: fresh identical calls and a formatting-only sham.
3. Provider adapters for a deterministic mock model, Gemini, OpenAI, and Ollama.
4. Structured parsing of decisions and 0--100 scores.
5. Lexical similarity, optional sentence-transformer similarity, sentiment,
   decision consistency, and disparity summaries.
6. Failure-aware comparison and export logic.
7. Template-level sign-flip tests, bootstrap intervals, effect sizes, and
   multiple-testing correction.
8. A Streamlit dashboard, CLI, JSON/CSV/Markdown/LaTeX exports, and tests.

The complete implementation notes and assumptions are in
[ALGORITHMS_GUIDE.md](ALGORITHMS_GUIDE.md). The presentation and submission
guidance is in [PRESENTATION_NOTES.md](PRESENTATION_NOTES.md) and
[SUBMISSION_GUIDE.md](SUBMISSION_GUIDE.md).

## Repository layout

- [`app.py`](app.py): Streamlit dashboard.
- [`promptbench/perturbation/`](promptbench/perturbation): scenario templates,
  demographic profiles, name banks, and counterfactual generation.
- [`promptbench/query_pipeline/`](promptbench/query_pipeline): orchestration,
  retries, caching, and provider adapters.
- [`promptbench/metrics/`](promptbench/metrics): response scoring instruments.
- [`promptbench/statistical_testing/`](promptbench/statistical_testing): paired
  inference, bootstrap intervals, and multiple-testing corrections.
- [`promptbench/reporting/`](promptbench/reporting): reports, exports, and
  presentation charts.
- [`tests/`](tests): unit, integration, provider-wire-format, and dashboard
  tests.
- [`results/verified_mock_all/`](results/verified_mock_all): vetted offline
  demonstration output.
- [`results/`](results): historical and live-run provenance notes.

## Installation

Python 3.12 or newer is required. Use the same Python environment for
installation, tests, CLI commands, and Streamlit.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

If PowerShell execution policy prevents activation, invoke the environment
directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

### macOS/Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

The pinned runtime dependencies are listed in
[requirements.txt](requirements.txt). The optional sentence-transformer
backend is installed with:

```bash
python -m pip install -e '.[embeddings]'
```

The optional backend may download a model on first use. The default CLI and
dashboard scorer is lexical; installing the extra alone does not enable the
transformer scorer.

## Run the dashboard locally

```bash
python -m streamlit run app.py
```

On Windows, [`run_dashboard.bat`](run_dashboard.bat) launches the dashboard
using `.venv` when it exists.

The dashboard starts with the offline **Mock demo**. Choose a live provider
only when its credentials or local service are available. Mock output contains
deliberately programmed score and tone changes; it is a pipeline demonstration,
not evidence about a deployed model.

Live cloud requests start only after **Run / refresh audit**. Streamlit may
retain a completed run while the settings and run key are unchanged; refreshing
the browser is not automatically a new experiment.

## Reproduce the verified offline run

From the repository root:

```bash
python -m unittest discover -s tests -v
python -m promptbench.cli audit `
  --scenario all `
  --provider mock `
  --model promptbench-mock-v1 `
  --samples-per-group 2 `
  --temperature 0 `
  --seed 42 `
  --output-dir results/verified_mock_all
```

For macOS/Linux, replace PowerShell backticks with backslashes or place the
command on one line.

The test suite covers controlled-field changes, unique prompt IDs, uncached
identical calls, sham controls, cache rebinding, response parsing, failed and
missing responses, calibrated contrasts, template-level inference, reports,
exports, provider wire formats, and dashboard behavior. The mock provider and
metrics are deterministic for fixed settings, although timestamps, response
IDs, latency, and audit IDs are runtime provenance.

A focused single-scenario run is useful for inspecting paired answers:

```bash
python -m promptbench.cli audit --scenario job_swe_001 `
  --provider mock --model promptbench-mock-v1 `
  --samples-per-group 1 --output-dir results/local_hiring_demo
```

Run `python -m promptbench.cli audit --help` for all CLI options.

## Experimental design

Each template contains one neutral reference profile. The engine renders
counterfactual variants while preserving substantive numerical qualifications
and the evaluator system prompt.

| Condition | Manipulation | Fields intended to remain fixed |
| --- | --- | --- |
| `NAME` | Replace the name using an experimental name bank | Pronouns, nationality, education, neighborhood, activities, qualifications |
| `EXPLICIT` | Change pronouns alone or nationality alone | Other profile fields and qualifications |
| `SES` | Change education, residence, and activity cues as a bundle | Name, pronouns, nationality, qualifications |
| `IDENTICAL` | Re-submit the exact reference prompt independently | Prompt text and request settings |
| `SHAM` | Add trailing newline formatting | Profile fields and substantive text |

The engine omits a demographic variant if its rendered text is identical to
the reference, but intentionally retains `IDENTICAL` controls as fresh
provider calls. Generated audit requests bypass the persistent SQLite cache:
otherwise a cache hit could manufacture a zero noise floor. The general Python
query API still supports caching for explicitly cacheable requests.

The built-in scenarios include at least ten templates each for job application,
loan eligibility, and tenant screening. The exact template identifiers and
rendered prompts are available in
[promptbench/perturbation/templates.py](promptbench/perturbation/templates.py).

### Interpretation of cues

Name-bank origin labels are experimental linguistic cues; they do not identify a
person's actual ethnicity. Pronoun conditions are linguistic conditions and do
not establish gender identity. The SES manipulation is a bundled proxy: school
prestige, neighborhood, and activities may change perceived qualifications, so
it cannot isolate income or a protected attribute. The sham is a simple
formatting control and is not edit-length matched to every treatment.

## Provider protocol and provenance

Every provider request records, where available, the selected model ID, system
prompt, user prompt, temperature, seed, maximum token setting, provider, model
version or fingerprint, latency, and usage metadata. API keys are sent through
provider-specific authentication and are excluded from exported provenance.

### Mock provider

The mock provider is deterministic and offline. It is intended for tests,
demonstrations, and checking the complete reporting path. Its programmed
behavior must never be presented as a measured property of Gemini, OpenAI,
Ollama, or any demographic group.

### Gemini and OpenAI

Set the relevant key in an untracked `.env` file or enter it in the dashboard:

```text
GEMINI_API_KEY=your-key
OPENAI_API_KEY=your-key
```

Do not commit `.env`, keys, raw provider responses, or private applicant data.
Select the exact model ID available to the account. Hosted outputs can change
despite fixed temperature and seed because provider infrastructure, model
versions, rate limits, and seed support can change.

Examples:

```bash
promptbench audit --scenario job_swe_001 \
  --provider gemini --model gemini-3.5-flash-lite
promptbench audit --scenario job_swe_001 \
  --provider openai --model gpt-4o-mini
```

Transient errors use full-jitter exponential backoff:

`delay_i ~ Uniform(0, min(max_delay, base_delay * 2**i))`

Known authentication and invalid-request errors stop retries. Exhausted,
empty, blocked, or failed completions become error responses and are excluded
from valid response comparisons. Cloud runs default to one concurrent request
and two attempts per prompt unless CLI options override them.

### Ollama

Ollama runs a downloaded model locally without a cloud API key:

```bash
ollama serve
ollama list
python -m promptbench.cli audit --scenario job_swe_001 \
  --provider ollama --model qwen2.5:7b \
  --samples-per-group 1 --max-tokens 256 \
  --output-dir results/local_ollama
```

The default server is `http://127.0.0.1:11434`; use `--ollama-host` or
`OLLAMA_HOST` to change it. The adapter checks installed tags and never
downloads a model automatically. It sends `stream=false`, `think=false`,
temperature, seed, and a token cap to the Ollama chat API. Ollama queries run
sequentially to limit local memory pressure. A one-template, one-sample
scenario creates 21 requests, including controls.

## Scoring instruments

### Response parsing

The evaluator is instructed to emit:

`[DECISION: ACCEPT / REJECT / INTERVIEW / APPROVED / DENIED]`

and:

`[SCORE: 0-100]`

The parser accepts recognized structured decision tokens and valid scores.
Fractions such as `8/10` normalize to `80/100`. Scores outside the stated
range, malformed structured fields, arbitrary prose, empty responses, and
provider errors are not silently converted into valid answers. A decision
match exists only when both responses have parsed decisions.

### Lexical response similarity

The default similarity is weighted unigram/bigram term-frequency cosine:

1. Tokenize ASCII words and numbers.
2. Add adjacent word bigrams.
3. Weight bigram counts by 1.5.
4. Transform nonzero weighted counts using `1 + ln(count)`.
5. Calculate cosine similarity:

`sim(u,v) = dot(u,v) / (norm(u) * norm(v))`

This is a lexical overlap proxy, not TF-IDF and not a semantic embedding.
Identical nonempty text scores 1; missing text scores 0. A high similarity does
not prove semantic equivalence.

The optional `all-MiniLM-L6-v2` sentence-transformer backend can be enabled in
the Python scorer API:

```python
from promptbench.metrics.scorer import BiasScorer
scorer = BiasScorer(use_transformer_embeddings=True)
```

Exports record the method actually used. If the optional dependency/model is
unavailable, the implementation uses its documented fallback behavior.

### Sentiment

Sentiment uses a custom English evaluation lexicon with positive and negative
weights, booster handling, and simple three-token negation. The normalized
score is:

`sentiment(text) = v / sqrt(v*v + 15)`

The paired sentiment delta is the treatment score minus the reference score.
This is not VADER and has no external human-labeled validation. It is an
instrument output, not a direct measure of harm, intent, or fairness.

### Decisions, scores, and lexical drift

For decision outcomes, the dashboard reports agreement and group selection
summaries. Known positive, negative, and intermediate decision categories are
retained; errors and unknown decisions are excluded. When valid group rates
exist, the descriptive disparity ratio is:

`min(selection_rate) / max(selection_rate)`

The ratio is unavailable when there are fewer than two valid groups or no
positive selections. It is not a legal four-fifths-rule determination.

Secondary descriptive measures include token-set Jaccard similarity and
response-length changes. Score deltas are `score_treatment - score_reference`.

## Statistical analysis

The engine analyzes score, sentiment, similarity, decision consistency, and
calibration controls separately. Treatment results are reported as:

1. Reference contrast: `D_treatment,t`
2. Identical-adjusted contrast: `D_treatment,t - D_IDENTICAL,t`
3. Sham-adjusted contrast: `D_treatment,t - D_SHAM,t`

Only templates represented in both treatment and requested control enter a
calibrated contrast. Underlying valid pairs are averaged by template before
resampling or testing. `sample_size` is template count; `observation_count` is
the number of valid underlying pairs.

### Sign-flip test

For template contrasts `D_1 ... D_n`, the mean is the test statistic. Signs are
enumerated when feasible (`2**n`, with the configured resampling budget);
otherwise random signs are drawn with seed 42. The two-sided Monte Carlo
estimate uses a +1 numerator and denominator correction. With one template,
the result is explicitly descriptive with `p=1`; with four templates, the
smallest exact two-sided p-value is 0.125.

### Bootstrap and effect size

For at least two templates, percentile bootstrap intervals resample template
contrasts with replacement. The default is 2,000 resamples at 95% confidence,
with seed 42. Paired Cohen's dz is:

`dz = mean(D) / sample_std(D)`

It is unavailable with fewer than two templates or zero variance. The schema
retains the field name `effect_size_cohens_d`; the tested metric is never
substituted with another metric.

Wilcoxon signed-rank is secondary. For fewer than five nonzero template
contrasts, the implementation reports a conservative `p=1`; otherwise SciPy
is used when available.

### Multiple comparisons

Benjamini--Hochberg and Bonferroni corrections cover the reported
metric/group/reference tests in a run. Shared templates and controls induce
dependence, and correction guarantees depend on assumptions that are not
fully established for this exploratory design. Report raw p-values, adjusted
p-values, effect sizes, intervals, and denominators together.

## Missing data and quality reporting

A response is excluded from a valid comparison when it is failed, blocked,
empty, or otherwise lacks a usable structured response. Missing decisions are
not treated as agreement or disagreement. Reports retain total requests,
failed requests, expected pairs, valid pairs, failure reasons, and decision
denominators.

Never describe a partial run as a complete model finding. The presentation
figure labels incomplete coverage and the dashboard keeps quality information
above the result views.

## Reproducibility checklist

For every paper, report:

- Git commit and repository version.
- Date and environment/Python version.
- Provider, exact model ID, model fingerprint/version when available.
- Scenario IDs and template count.
- Samples per group and total requests.
- System prompt and user-prompt construction.
- Temperature, seed, maximum tokens, concurrency, retries, and timeout.
- Whether lexical or transformer similarity was used.
- Valid, failed, blocked, and excluded response counts.
- Control results for `IDENTICAL` and `SHAM`.
- Template-level sample size and underlying observation count.
- Raw and corrected p-values, confidence intervals, and effect sizes.
- Any manual exclusions or prompt-equivalence decisions.
- Whether results are mock, local, or hosted-model results.

For a defensible study, add more independently authored templates, preregister
the analysis, sample names and cue alternatives systematically, audit prompt
equivalence, validate instruments with human labels, test multiple decoding
settings, repeat hosted models across dates, and consider hierarchical models
with template and cue-level effects. The current implementation does not
support broad population claims or causal claims about protected groups.

## Existing result artifacts

[results/verified_mock_all/](results/verified_mock_all/) is a reproducible
offline demonstration generated with the current code. Its synthetic outputs
test the pipeline and are not findings about Gemini, OpenAI, Ollama, or
demographic fairness.

The historical files directly under [`results/`](results/) predate the
controlled design and should not be used for statistical or legal claims.
See [results/README.md](results/README.md) for provenance.

The repository also contains example live-run directories:

- `live_ollama_qwen25_swe`: one local hiring scenario, 21 requests and 20/20
  valid pairs; one template means descriptive evidence only.
- `live_gemini35_all_512`: four scenarios, 84 requests, 43 usable responses,
  and 28/80 valid pairs; it is an incomplete diagnostic, not a complete
  four-scenario finding.

Exports omit raw prompts and responses by default. They retain synthetic labels,
scorer method, hashes, model settings, timestamps, and provenance. Review any
raw-response export before sharing.

## Deploy to Streamlit Community Cloud

The app can be hosted from the GitHub repository at
`https://share.streamlit.io`.

1. Sign in with GitHub.
2. Choose **Create app** or **New app**.
3. Select repository `suryansh1706/promptBench-v2`.
4. Select branch `main`.
5. Set the main file path to `app.py`.
6. Deploy and wait for dependency installation.
7. Start with **Mock demo (offline)** to verify the deployment.

For cloud providers, open the deployed app's settings and add secrets without
committing them:

```toml
GEMINI_API_KEY = "your-key"
OPENAI_API_KEY = "your-key"
```

Ollama at `127.0.0.1` means the hosted container itself, not a laptop, so the
local Ollama workflow is not available through Community Cloud unless a
reachable remote Ollama service is deliberately configured. Public deployments
should not receive private applicant data or raw confidential responses.

## Citation and responsible reporting

This repository supplies an implementation and an exploratory audit protocol,
not a validated benchmark. A paper should cite the exact commit, preserve the
exported provenance, distinguish mock/local/hosted evidence, and avoid wording
such as “the model is discriminatory” based only on response contrasts.
Prefer precise claims such as “under this prompt, model, cue set, and
calibration design, the observed response metric differed.”

The project is intended for research, education, and model-audit development.
It should not be used as the sole basis for employment, lending, housing, or
other high-impact decisions.
