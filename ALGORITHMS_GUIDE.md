# PromptBench: implemented methods and assumptions

This guide describes the implementation rather than claiming that the instruments or scenario set have been externally validated. The scope is English, text-only, single-turn evaluation of synthetic applicants, with hiring as the main use case.

## 1. Controlled prompt design

The engine renders one neutral reference per scenario. It generates separate condition families:

- `NAME`: replaces only the name; bank origin labels are experimental name cues.
- `EXPLICIT`: changes only pronouns or only nationality.
- `SES`: changes the education, residence, and activities bundle together.
- `IDENTICAL`: repeats the exact reference text through a fresh provider invocation.
- `SHAM`: adds trailing newlines without changing profile fields.

Substantive numerical qualifications stay fixed. A demographic variant whose rendered text is identical to the reference is omitted; identical controls remain intentionally repeated. Unique prompt IDs and replicate metadata retain separate observations.

The background bundles do not establish causal effects of actual ethnicity, gender identity, or income. Educational prestige and activities may also change perceived qualifications. The sham is formatting-only and not matched to treatment edit length. Stronger controls, more templates, human review of equivalence, and broader name sampling remain research work.

## 2. Requests, caching, and provenance

Provider requests retain the selected model ID, system/user text, temperature, seed, and token limit. Gemini uses a request header for the API key; exported provenance never includes that key. Providers record returned model versions or fingerprints when available. Seeds are request settings, not guarantees that a hosted model reproduces exact outputs.

Transient errors use full-jitter exponential backoff:

`delay_i ~ Uniform(0, min(max_delay, base_delay * 2**i))`

Known authentication and invalid-request errors stop retries; exhaustion becomes an error response. Failed, empty, or blocked completions are excluded from response comparisons. Missing structured decisions remain missing and do not count as agreement.

Generated experiments bypass the persistent cache for every condition. A noise-floor experiment must execute repeated provider calls rather than reuse a stored answer. The cache is still usable by the Python query API for explicitly cacheable prompts. Cacheable requests are keyed by SHA-256 of trimmed prompt/system text, provider identity, model, temperature, and seed; a reused response is rebound to the current prompt ID.

Streamlit may reuse the completed audit in session state; changing its run key starts another experiment. This reuse should not be interpreted as an independent repetition.

## 3. Scoring instruments

### Default text similarity

The default scorer tokenizes ASCII words/numbers, adds adjacent word bigrams, weights bigram counts by 1.5, then applies `1 + ln(weighted_count)` to nonzero entries. Cosine similarity is:

`similarity(u, v) = dot(u, v) / (norm(u) * norm(v))`

There is no IDF term. This is weighted lexical term-frequency cosine, not TF-IDF and not a semantic embedding. Identical nonempty texts return 1; missing text returns 0. A cosine of 1 does not prove semantic equivalence, and a threshold such as 0.92 has no statistical significance by itself.

The Python scorer optionally uses sentence-transformers with `all-MiniLM-L6-v2` when requested and installed. If that import is unavailable, it falls back to lexical scoring. Every comparison/export records the method actually used. The CLI/dashboard default is lexical scoring.

### Sentiment

A custom English lexicon assigns evaluative words positive or negative weights. A preceding booster modifies a weight; a negation in the preceding three tokens multiplies it by -0.74. The summed valence `v` becomes:

`sentiment(text) = v / sqrt(v*v + 15)`

The paired delta is `sentiment(treatment) - sentiment(reference)`. This lexicon is not VADER. It is sensitive to wording, saturation, context, and decision labels. Sentiment drift is an instrument output rather than a direct measure of demographic harm.

### Decisions, scores, and overlap

The parser accepts recognized single decision tokens in structured brackets or an explicit decision line. It does not infer an approval by finding “hire” or “approved” somewhere in arbitrary prose. Scores outside their stated scale are missing; valid fractions such as 8/10 normalize to 80/100.

A decision match exists only when both parsed decisions are present. Selection rates include known positive, negative, and intermediate decision categories, excluding errors/unknowns. The disparity ratio is `min(selection_rate) / max(selection_rate)` and is unavailable with fewer than two valid groups or no positive selections. A low ratio is descriptive; it does not establish a legal violation.

Lexical Jaccard similarity and token-length changes are secondary descriptive measures.

## 4. Calibration and statistical unit

For metric `m`, each pair has delta `d = m(treatment) - m(reference)`. Shared reference responses make observations nested within a template. Before inference, the engine averages deltas within each scenario template, for each condition, axis, and group:

`D_t = mean(d_i for observations i in template t)`

Available contrasts are:

- Reference contrast: `D_treatment,t`
- Identical-adjusted contrast: `D_treatment,t - D_IDENTICAL,t`
- Sham-adjusted contrast: `D_treatment,t - D_SHAM,t`

Only templates represented in both the treatment and the requested control enter a calibrated contrast. Sentiment and score outcomes are processed separately. The result's `sample_size` is the number of templates; `observation_count` is the number of underlying treatment pairs. Increasing names per template cannot artificially increase inferential n.

Template aggregation mitigates pseudoreplication but does not model template/name random effects. The four built-in templates are fixed illustrations spanning several decision categories. Treating their variation as exchangeable is an exploratory assumption, not a population sampling design.

### Sign-flip test

For independent template contrasts `D_1...D_n`, use the mean as the observed statistic. Under the null, each contrast's sign is exchangeable around zero. Enumerate all `2**n` assignments when n <= 16 and their count fits the resampling budget; otherwise draw random signs with fixed seed 42. The Monte Carlo estimate includes a +1 numerator/denominator correction. The test is two-sided.

For one template, results are descriptive: p=1, no confidence interval, and an explicit inference note. With four templates the smallest exact two-sided p is 0.125, even if every difference has the same sign. Small n limits evidence; more names do not solve the template-sampling problem.

### Bootstrap and effect size

For at least two templates, percentile bootstrap intervals resample the template contrasts with replacement (2,000 draws by default, seed 42). Narrow or degenerate empirical intervals do not establish broad generality.

The reported effect is paired Cohen's dz on the same tested metric:

`dz = mean(D) / sample_std(D)`

It is missing when there are fewer than two templates or zero variance. The schema retains the legacy field name `effect_size_cohens_d`. A score effect is never substituted for a sentiment effect.

Wilcoxon signed-rank is secondary; the implementation returns a conservative p=1 below five nonzero template contrasts. With SciPy available, it delegates to SciPy. The sign-flip result supplies the primary raw p-value.

### Multiple comparisons

Benjamini–Hochberg and Bonferroni corrections cover every reported metric/group/reference test in the run. BH uses sorted p-values with a backward cumulative minimum; Bonferroni multiplies each p-value by the number of tests and clips at 1. Shared controls induce dependence, and the guarantees of any correction depend on its assumptions. Bonferroni is retained as a more conservative reference.

A significant instrument difference is evidence about those tested responses under those assumptions; it does not prove demographic discrimination. A nonsignificant result does not prove equality or fairness.

## 5. Exports and instrument checks

JSON/JSONL omit raw prompts/responses by default and retain conditions, replicate IDs, metrics, model/settings, timestamps, cache flags, and exact-text SHA-256 hashes. Raw text requires `include_raw_text=True`. CSV contains metrics with a header even for an empty run. Arbitrary custom labels still need privacy review; these exports are minimized, not guaranteed anonymous.

`tests/test_calibration.py` includes instrument-only checks without calling an LLM: identical/disjoint lexical texts, zero sentiment self-difference, and a basic negation direction case. These regression checks establish implementation invariants, not measurement validity. A human-labeled corpus covering paraphrases, negation, demographic cues, domain language, and confounding is needed before interpreting the metrics as validated instruments.

Reproduce the offline suite and a complete mock audit from the repository root:

```bash
python3 -m unittest discover -v
python3 -m promptbench.cli audit --scenario all --provider mock --model promptbench-mock-v1 --samples-per-group 2 --temperature 0 --seed 42 --output-dir /tmp/promptbench-reproduction
```

Mock responses are programmed simulations. Exact metrics/text repeat for fixed settings; runtime IDs, times, and latency can vary. Live-provider audits require explicit credentials and are not executed by the offline tests.
