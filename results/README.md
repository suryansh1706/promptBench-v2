# Results provenance

`verified_mock_all/` is a fresh, reproducible offline demonstration generated with the current code:

```bash
python3 -m promptbench.cli audit --scenario all --provider mock --model promptbench-mock-v1 --samples-per-group 2 --temperature 0 --seed 42 --output-dir results/verified_mock_all
```

It uses synthetic model responses. Its numbers test the pipeline and are **not findings about Gemini, OpenAI, or demographic fairness**. The report includes IDENTICAL and SHAM controls and records the number of independent templates used for inference.

The four files directly in `results/` predate the controlled design. Their model response provenance and analysis cannot be reproduced here because no live API key was available. The old report's claims about statistically confirmed bias and a legal four-fifths-rule violation are unsupported; do not use those claims in a submission. The files are retained only as historical artifacts. Run a fresh live audit with a configured API key and inspect its control responses before presenting live-model conclusions.

## Fresh live runs, October 21, 2026

- `live_ollama_qwen25_swe/`: local `qwen2.5:7b`, one hiring scenario, 21 requests and 20/20 valid pairs. Includes a presentation PNG. This is a complete scenario-level run but has only one independent template, so it is descriptive.
- `live_gemini35_all_512/`: cloud `gemini-3.5-flash-lite`, four scenarios, 84 requests but only 43 usable responses and 28/80 valid pairs. Its presentation PNG prominently labels the run incomplete. Treat the available metrics as a partial diagnostic, not a complete model finding.

These exported JSON/CSV files omit raw prompts and responses. They retain synthetic labels and request provenance but no API key. The `live_*` directories are ignored by default to avoid accidentally publishing unreviewed future runs; the vetted evidence for this submission is explicitly added to Git.
