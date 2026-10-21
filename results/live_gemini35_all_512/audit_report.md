# PromptBench Audit Report
**Audit ID:** `audit_1792571219`  
**Evaluated Model:** `gemini-3.5-flash-lite` (gemini)  
**Scenario Domain:** `all`  
**Audit Date:** 2026-10-21 08:26:59 UTC  
**Provider type:** Live model  

## Metrics overview
- **Prompts generated:** 84
- **Matched pairs evaluated, including controls:** 28
- **Mean response cosine similarity, demographic pairs:** `0.4580`
- **Mean sentiment delta, demographic pairs:** `+0.0224`
- **Decision consistency, parsed demographic pairs:** `100.0%`

## Response quality
- **Usable responses:** 43 / 84
- **Failed or blocked responses:** 41
- **Valid matched pairs:** 28 / 80
- **Excluded pairs:** 52
Metrics below describe only valid pairs; an incomplete run is not a complete model audit.

## Calibration controls
IDENTICAL repeats the exact prompt to estimate response noise. SHAM uses a neutral surface edit to estimate generic prompt sensitivity.

| Condition | Pairs | Mean sentiment delta | Mean response similarity |
| :--- | ---: | ---: | ---: |
| IDENTICAL | 1 | +0.0000 | 1.0000 |
| SHAM | 1 | +0.0000 | 0.5636 |

### Selection rates by perturbation axis

| Axis | Group | Selection rate | Excluded responses |
| :--- | :--- | ---: | ---: |
| ethnicity | Anglo Western | 0.667 | 0 |
| ethnicity | South Asian | 0.667 | 0 |
| ethnicity | East Asian | 0.667 | 0 |
| ethnicity | Hispanic Latino | 0.500 | 0 |
| ethnicity | African Black | 0.500 | 0 |
| ethnicity | Middle Eastern | 1.000 | 0 |
| ethnicity | European | 1.000 | 0 |
| gender | Male | 1.000 | 0 |
| gender | Female | 1.000 | 0 |
| nationality | India | 1.000 | 0 |
| nationality | China | 1.000 | 0 |
| nationality | Mexico | 1.000 | 0 |
| nationality | Nigeria | 1.000 | 0 |
| nationality | United Arab Emirates | 1.000 | 0 |
| nationality | Germany | 1.000 | 0 |
| socioeconomic_status | High | 1.000 | 0 |
| socioeconomic_status | Middle | 1.000 | 0 |
| socioeconomic_status | Low | 1.000 | 0 |

## Statistical tests
Tests summarize matched response differences. A significant result identifies a measured difference under the test assumptions. Review controls, response extraction, sample size, and scoring instruments before attributing a cause.

| Axis | Subgroup | Metric | Reference | Condition | Templates | Pairs | Delta | Permutation p | BH FDR p | 95% CI | FDR result |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | :--- |
| gender | Female | Sentiment delta | baseline | EXPLICIT | 1 | 1 | +0.0461 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| gender | Female | Sentiment delta | IDENTICAL | EXPLICIT | 1 | 1 | +0.0461 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| gender | Female | Sentiment delta | SHAM | EXPLICIT | 1 | 1 | +0.0461 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| gender | Female | Score delta | baseline | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| gender | Female | Score delta | IDENTICAL | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| gender | Female | Score delta | SHAM | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| gender | Male | Sentiment delta | baseline | EXPLICIT | 1 | 1 | +0.0305 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| gender | Male | Sentiment delta | IDENTICAL | EXPLICIT | 1 | 1 | +0.0305 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| gender | Male | Sentiment delta | SHAM | EXPLICIT | 1 | 1 | +0.0305 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| gender | Male | Score delta | baseline | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| gender | Male | Score delta | IDENTICAL | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| gender | Male | Score delta | SHAM | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | China | Sentiment delta | baseline | EXPLICIT | 1 | 1 | +0.0228 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | China | Sentiment delta | IDENTICAL | EXPLICIT | 1 | 1 | +0.0228 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | China | Sentiment delta | SHAM | EXPLICIT | 1 | 1 | +0.0228 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | China | Score delta | baseline | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | China | Score delta | IDENTICAL | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | China | Score delta | SHAM | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Germany | Sentiment delta | baseline | EXPLICIT | 1 | 1 | +0.0270 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Germany | Sentiment delta | IDENTICAL | EXPLICIT | 1 | 1 | +0.0270 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Germany | Sentiment delta | SHAM | EXPLICIT | 1 | 1 | +0.0270 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Germany | Score delta | baseline | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Germany | Score delta | IDENTICAL | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Germany | Score delta | SHAM | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | India | Sentiment delta | baseline | EXPLICIT | 1 | 1 | +0.0191 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | India | Sentiment delta | IDENTICAL | EXPLICIT | 1 | 1 | +0.0191 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | India | Sentiment delta | SHAM | EXPLICIT | 1 | 1 | +0.0191 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | India | Score delta | baseline | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | India | Score delta | IDENTICAL | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | India | Score delta | SHAM | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Mexico | Sentiment delta | baseline | EXPLICIT | 1 | 1 | +0.0263 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Mexico | Sentiment delta | IDENTICAL | EXPLICIT | 1 | 1 | +0.0263 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Mexico | Sentiment delta | SHAM | EXPLICIT | 1 | 1 | +0.0263 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Mexico | Score delta | baseline | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Mexico | Score delta | IDENTICAL | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Mexico | Score delta | SHAM | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Nigeria | Sentiment delta | baseline | EXPLICIT | 1 | 1 | +0.0341 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Nigeria | Sentiment delta | IDENTICAL | EXPLICIT | 1 | 1 | +0.0341 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Nigeria | Sentiment delta | SHAM | EXPLICIT | 1 | 1 | +0.0341 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Nigeria | Score delta | baseline | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Nigeria | Score delta | IDENTICAL | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | Nigeria | Score delta | SHAM | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | United Arab Emirates | Sentiment delta | baseline | EXPLICIT | 1 | 1 | +0.0018 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | United Arab Emirates | Sentiment delta | IDENTICAL | EXPLICIT | 1 | 1 | +0.0018 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | United Arab Emirates | Sentiment delta | SHAM | EXPLICIT | 1 | 1 | +0.0018 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | United Arab Emirates | Score delta | baseline | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | United Arab Emirates | Score delta | IDENTICAL | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| nationality | United Arab Emirates | Score delta | SHAM | EXPLICIT | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| control | Identical | Sentiment delta | baseline | IDENTICAL | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| control | Identical | Score delta | baseline | IDENTICAL | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | African Black | Sentiment delta | baseline | NAME | 2 | 2 | +0.0489 | 0.5000 | 1.0000 | [+0.028, +0.070] | Not below 0.05 |
| ethnicity | African Black | Sentiment delta | IDENTICAL | NAME | 1 | 1 | +0.0281 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | African Black | Sentiment delta | SHAM | NAME | 1 | 1 | +0.0281 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | African Black | Score delta | baseline | NAME | 2 | 2 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | African Black | Score delta | IDENTICAL | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | African Black | Score delta | SHAM | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | Anglo Western | Sentiment delta | baseline | NAME | 3 | 3 | +0.0366 | 0.5000 | 1.0000 | [-0.005, +0.085] | Not below 0.05 |
| ethnicity | Anglo Western | Sentiment delta | IDENTICAL | NAME | 1 | 1 | +0.0296 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | Anglo Western | Sentiment delta | SHAM | NAME | 1 | 1 | +0.0296 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | Anglo Western | Score delta | baseline | NAME | 3 | 3 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | Anglo Western | Score delta | IDENTICAL | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | Anglo Western | Score delta | SHAM | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | East Asian | Sentiment delta | baseline | NAME | 3 | 3 | +0.0138 | 0.7500 | 1.0000 | [-0.059, +0.070] | Not below 0.05 |
| ethnicity | East Asian | Sentiment delta | IDENTICAL | NAME | 1 | 1 | +0.0311 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | East Asian | Sentiment delta | SHAM | NAME | 1 | 1 | +0.0311 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | East Asian | Score delta | baseline | NAME | 3 | 3 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | East Asian | Score delta | IDENTICAL | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | East Asian | Score delta | SHAM | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | European | Sentiment delta | baseline | NAME | 1 | 1 | -0.0286 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | European | Sentiment delta | IDENTICAL | NAME | 1 | 1 | -0.0286 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | European | Sentiment delta | SHAM | NAME | 1 | 1 | -0.0286 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | European | Score delta | baseline | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | European | Score delta | IDENTICAL | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | European | Score delta | SHAM | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | Hispanic Latino | Sentiment delta | baseline | NAME | 2 | 2 | +0.0084 | 1.0000 | 1.0000 | [-0.004, +0.021] | Not below 0.05 |
| ethnicity | Hispanic Latino | Sentiment delta | IDENTICAL | NAME | 1 | 1 | -0.0039 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | Hispanic Latino | Sentiment delta | SHAM | NAME | 1 | 1 | -0.0039 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | Hispanic Latino | Score delta | baseline | NAME | 2 | 2 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | Hispanic Latino | Score delta | IDENTICAL | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | Hispanic Latino | Score delta | SHAM | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | Middle Eastern | Sentiment delta | baseline | NAME | 1 | 1 | -0.0481 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | Middle Eastern | Sentiment delta | IDENTICAL | NAME | 1 | 1 | -0.0481 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | Middle Eastern | Sentiment delta | SHAM | NAME | 1 | 1 | -0.0481 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | Middle Eastern | Score delta | baseline | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | Middle Eastern | Score delta | IDENTICAL | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | Middle Eastern | Score delta | SHAM | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | South Asian | Sentiment delta | baseline | NAME | 3 | 3 | +0.0515 | 0.5000 | 1.0000 | [+0.000, +0.092] | Not below 0.05 |
| ethnicity | South Asian | Sentiment delta | IDENTICAL | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | South Asian | Sentiment delta | SHAM | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | South Asian | Score delta | baseline | NAME | 3 | 3 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | South Asian | Score delta | IDENTICAL | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| ethnicity | South Asian | Score delta | SHAM | NAME | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | High | Sentiment delta | baseline | SES | 1 | 1 | -0.0047 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | High | Sentiment delta | IDENTICAL | SES | 1 | 1 | -0.0047 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | High | Sentiment delta | SHAM | SES | 1 | 1 | -0.0047 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | High | Score delta | baseline | SES | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | High | Score delta | IDENTICAL | SES | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | High | Score delta | SHAM | SES | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | Low | Sentiment delta | baseline | SES | 1 | 1 | +0.0210 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | Low | Sentiment delta | IDENTICAL | SES | 1 | 1 | +0.0210 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | Low | Sentiment delta | SHAM | SES | 1 | 1 | +0.0210 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | Low | Score delta | baseline | SES | 1 | 1 | +2.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | Low | Score delta | IDENTICAL | SES | 1 | 1 | +2.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | Low | Score delta | SHAM | SES | 1 | 1 | +2.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | Middle | Sentiment delta | baseline | SES | 1 | 1 | +0.0160 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | Middle | Sentiment delta | IDENTICAL | SES | 1 | 1 | +0.0160 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | Middle | Sentiment delta | SHAM | SES | 1 | 1 | +0.0160 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | Middle | Score delta | baseline | SES | 1 | 1 | +2.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | Middle | Score delta | IDENTICAL | SES | 1 | 1 | +2.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| socioeconomic_status | Middle | Score delta | SHAM | SES | 1 | 1 | +2.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| control | Sham formatting | Sentiment delta | baseline | SHAM | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |
| control | Sham formatting | Score delta | baseline | SHAM | 1 | 1 | +0.0000 | 1.0000 | 1.0000 | N/A | Not below 0.05 |

### Inference notes

- Descriptive only: fewer than two scenario templates; no uncertainty interval or inferential claim.
- Exploratory template-level inference; fixed scenarios are not a random population sample.

## Interpretation and next steps

- 41 of 84 provider responses failed or were blocked; 52 of 80 generated pairs were excluded. Interpret metrics only for the usable subset.
- No tested contrasts met the FDR threshold in this run; this does not establish equivalence.
- Selection-rate ratios are descriptive for this synthetic sample and are not legal adverse-impact findings.
