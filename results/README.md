# Results provenance

`verified_mock_all/` is a fresh, reproducible offline demonstration generated with the current code:

```bash
python3 -m promptbench.cli audit --scenario all --provider mock --model promptbench-mock-v1 --samples-per-group 2 --temperature 0 --seed 42 --output-dir results/verified_mock_all
```

It uses synthetic model responses. Its numbers test the pipeline and are **not findings about Gemini, OpenAI, or demographic fairness**. The report includes IDENTICAL and SHAM controls and records the number of independent templates used for inference.

The four files directly in `results/` predate the controlled design. Their model response provenance and analysis cannot be reproduced here because no live API key was available. The old report's claims about statistically confirmed bias and a legal four-fifths-rule violation are unsupported; do not use those claims in a submission. The files are retained only as historical artifacts. Run a fresh live audit with a configured API key and inspect its control responses before presenting live-model conclusions.
