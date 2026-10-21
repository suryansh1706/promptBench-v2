# Calibrated Audit: short teacher presentation

## One-minute opening

"Calibrated Audit checks whether an LLM changes its evaluation when a synthetic applicant's demographic cue changes. The main use case is hiring. We hold numerical qualifications fixed, change one cue family at a time, and compare each answer with a shared neutral reference. The tool also tests exact repeats and harmless formatting changes, so ordinary model variation is visible."

## Demo order

1. Open `streamlit run app.py`. Show **Results overview**, including the source label, valid-pair coverage, number of scenario templates, and downloadable PNG.
2. Show the [complete local-model example](results/live_ollama_qwen25_swe/presentation_summary.png). It has 20/20 valid pairs from 21 requests, including two controls. The 94.4% decision agreement means 17 of 18 treatment pairs with parsed decisions matched the reference; one differed. These are descriptive results for one template.
3. In **Calibration & uncertainty**, explain IDENTICAL (same prompt, fresh call) and SHAM (newline edit). A treatment change must be judged against that response variation. Open **Paired answers** for an individual comparison before interpreting a mean.
4. Switch the sidebar to **All four scenario templates** with **Mock LLM** for a fast full-pipeline demonstration. State that mock outputs are programmed examples, not findings about a deployed model.
5. Show the [Gemini graphic](results/live_gemini35_all_512/presentation_summary.png) only as a data-quality example: 28 of 80 planned pairs were usable. The incomplete-run banner is why that aggregate cannot support a four-scenario conclusion.

## Methods to explain if asked

| Question | Short answer |
| --- | --- |
| What changes? | NAME changes only a culturally associated name cue; EXPLICIT changes pronouns or nationality; SES changes a background bundle. |
| What stays fixed? | Numerical experience and other substantive qualifications in each paired scenario. |
| Why two controls? | IDENTICAL estimates response variation from repeated calls; SHAM measures sensitivity to an innocuous edit. |
| What is the independent sample size? | Scenario templates, not the number of names or pairs sharing one reference. |
| What do the charts show? | Response similarity, tone change, score change, parsed decisions, and calibrated statistical contrasts. |
| Is this proof of bias? | No. The name banks, four fixed templates, lexical similarity, and custom sentiment scorer limit causal and population claims. |

## Closing sentence

"The deliverable is a reproducible audit workflow with explicit quality checks and honest uncertainty. The complete local-model run shows it works end to end; the partial cloud run shows why failed calls must be reported rather than silently counted as evidence."
