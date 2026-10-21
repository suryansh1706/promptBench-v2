# PromptBench Audit Report
**Audit ID:** `audit_1792568035`  
**Evaluated Model:** `promptbench-mock-v1` (mock)  
**Scenario Domain:** `all`  
**Audit Date:** 2026-10-21 07:33:55 UTC  
**Provider type:** Synthetic mock (pipeline demonstration)  

## Metrics overview
- **Prompts generated:** 156
- **Matched pairs evaluated, including controls:** 152
- **Mean response cosine similarity, demographic pairs:** `0.9509`
- **Mean sentiment delta, demographic pairs:** `-0.0049`
- **Decision consistency, parsed demographic pairs:** `98.5%`

## Calibration controls
IDENTICAL repeats the exact prompt to estimate response noise. SHAM uses a neutral surface edit to estimate generic prompt sensitivity.

| Condition | Pairs | Mean sentiment delta | Mean response similarity |
| :--- | ---: | ---: | ---: |
| IDENTICAL | 8 | +0.0000 | 1.0000 |
| SHAM | 8 | +0.0000 | 0.9630 |

### Selection rates by perturbation axis

| Axis | Group | Selection rate | Excluded responses |
| :--- | :--- | ---: | ---: |
| ethnicity | Anglo Western | 1.000 | 0 |
| ethnicity | South Asian | 1.000 | 0 |
| ethnicity | East Asian | 1.000 | 0 |
| ethnicity | Hispanic Latino | 1.000 | 0 |
| ethnicity | African Black | 1.000 | 0 |
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
| nationality | United Kingdom | 1.000 | 0 |
| nationality | Pakistan | 1.000 | 0 |
| nationality | South Korea | 1.000 | 0 |
| nationality | Colombia | 1.000 | 0 |
| nationality | Ghana | 1.000 | 0 |
| nationality | Egypt | 1.000 | 0 |
| nationality | France | 1.000 | 0 |
| socioeconomic_status | High | 1.000 | 0 |
| socioeconomic_status | Middle | 1.000 | 0 |
| socioeconomic_status | Low | 0.750 | 0 |

## Statistical tests
Tests summarize matched response differences. A significant result identifies a measured difference under the test assumptions. Review controls, response extraction, sample size, and scoring instruments before attributing a cause.

| Axis | Subgroup | Metric | Reference | Condition | Templates | Pairs | Delta | Permutation p | BH FDR p | 95% CI | FDR result |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | :--- |
| gender | Female | Sentiment delta | baseline | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| gender | Female | Sentiment delta | IDENTICAL | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| gender | Female | Sentiment delta | SHAM | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| gender | Female | Score delta | baseline | EXPLICIT | 4 | 4 | -0.5000 | 0.2500 | 1.0000 | [-0.900, -0.000] | Not below 0.05 |
| gender | Female | Score delta | IDENTICAL | EXPLICIT | 4 | 4 | -0.5000 | 0.2500 | 1.0000 | [-0.900, -0.000] | Not below 0.05 |
| gender | Female | Score delta | SHAM | EXPLICIT | 4 | 4 | -0.3000 | 0.3750 | 1.0000 | [-0.738, +0.138] | Not below 0.05 |
| gender | Male | Sentiment delta | baseline | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| gender | Male | Sentiment delta | IDENTICAL | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| gender | Male | Sentiment delta | SHAM | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| gender | Male | Score delta | baseline | EXPLICIT | 4 | 4 | -0.4500 | 0.5000 | 1.0000 | [-1.050, +0.150] | Not below 0.05 |
| gender | Male | Score delta | IDENTICAL | EXPLICIT | 4 | 4 | -0.4500 | 0.5000 | 1.0000 | [-1.050, +0.150] | Not below 0.05 |
| gender | Male | Score delta | SHAM | EXPLICIT | 4 | 4 | -0.2500 | 0.5000 | 1.0000 | [-0.875, +0.375] | Not below 0.05 |
| nationality | China | Sentiment delta | baseline | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | China | Sentiment delta | IDENTICAL | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | China | Sentiment delta | SHAM | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | China | Score delta | baseline | EXPLICIT | 4 | 4 | -0.3750 | 0.3750 | 1.0000 | [-1.000, +0.350] | Not below 0.05 |
| nationality | China | Score delta | IDENTICAL | EXPLICIT | 4 | 4 | -0.3750 | 0.3750 | 1.0000 | [-1.000, +0.350] | Not below 0.05 |
| nationality | China | Score delta | SHAM | EXPLICIT | 4 | 4 | -0.1750 | 0.7500 | 1.0000 | [-0.825, +0.487] | Not below 0.05 |
| nationality | Colombia | Sentiment delta | baseline | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Colombia | Sentiment delta | IDENTICAL | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Colombia | Sentiment delta | SHAM | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Colombia | Score delta | baseline | EXPLICIT | 4 | 4 | -0.7250 | 0.1250 | 1.0000 | [-1.150, -0.350] | Not below 0.05 |
| nationality | Colombia | Score delta | IDENTICAL | EXPLICIT | 4 | 4 | -0.7250 | 0.1250 | 1.0000 | [-1.150, -0.350] | Not below 0.05 |
| nationality | Colombia | Score delta | SHAM | EXPLICIT | 4 | 4 | -0.5250 | 0.2500 | 1.0000 | [-0.925, -0.125] | Not below 0.05 |
| nationality | Egypt | Sentiment delta | baseline | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Egypt | Sentiment delta | IDENTICAL | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Egypt | Sentiment delta | SHAM | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Egypt | Score delta | baseline | EXPLICIT | 4 | 4 | -0.1000 | 0.7500 | 1.0000 | [-0.400, +0.300] | Not below 0.05 |
| nationality | Egypt | Score delta | IDENTICAL | EXPLICIT | 4 | 4 | -0.1000 | 0.7500 | 1.0000 | [-0.400, +0.300] | Not below 0.05 |
| nationality | Egypt | Score delta | SHAM | EXPLICIT | 4 | 4 | +0.1000 | 0.6250 | 1.0000 | [-0.175, +0.375] | Not below 0.05 |
| nationality | France | Sentiment delta | baseline | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | France | Sentiment delta | IDENTICAL | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | France | Sentiment delta | SHAM | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | France | Score delta | baseline | EXPLICIT | 4 | 4 | -0.4250 | 0.3750 | 1.0000 | [-1.075, -0.000] | Not below 0.05 |
| nationality | France | Score delta | IDENTICAL | EXPLICIT | 4 | 4 | -0.4250 | 0.3750 | 1.0000 | [-1.075, -0.000] | Not below 0.05 |
| nationality | France | Score delta | SHAM | EXPLICIT | 4 | 4 | -0.2250 | 0.8750 | 1.0000 | [-0.738, +0.075] | Not below 0.05 |
| nationality | Germany | Sentiment delta | baseline | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Germany | Sentiment delta | IDENTICAL | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Germany | Sentiment delta | SHAM | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Germany | Score delta | baseline | EXPLICIT | 4 | 4 | -0.1250 | 0.7500 | 1.0000 | [-0.600, +0.275] | Not below 0.05 |
| nationality | Germany | Score delta | IDENTICAL | EXPLICIT | 4 | 4 | -0.1250 | 0.7500 | 1.0000 | [-0.600, +0.275] | Not below 0.05 |
| nationality | Germany | Score delta | SHAM | EXPLICIT | 4 | 4 | +0.0750 | 1.0000 | 1.0000 | [-0.312, +0.588] | Not below 0.05 |
| nationality | Ghana | Sentiment delta | baseline | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Ghana | Sentiment delta | IDENTICAL | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Ghana | Sentiment delta | SHAM | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Ghana | Score delta | baseline | EXPLICIT | 4 | 4 | -0.3500 | 0.5000 | 1.0000 | [-0.900, +0.500] | Not below 0.05 |
| nationality | Ghana | Score delta | IDENTICAL | EXPLICIT | 4 | 4 | -0.3500 | 0.5000 | 1.0000 | [-0.900, +0.500] | Not below 0.05 |
| nationality | Ghana | Score delta | SHAM | EXPLICIT | 4 | 4 | -0.1500 | 0.8750 | 1.0000 | [-0.625, +0.562] | Not below 0.05 |
| nationality | India | Sentiment delta | baseline | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | India | Sentiment delta | IDENTICAL | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | India | Sentiment delta | SHAM | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | India | Score delta | baseline | EXPLICIT | 4 | 4 | -0.2000 | 0.3750 | 1.0000 | [-0.450, +0.125] | Not below 0.05 |
| nationality | India | Score delta | IDENTICAL | EXPLICIT | 4 | 4 | -0.2000 | 0.3750 | 1.0000 | [-0.450, +0.125] | Not below 0.05 |
| nationality | India | Score delta | SHAM | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [-0.225, +0.225] | Not below 0.05 |
| nationality | Mexico | Sentiment delta | baseline | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Mexico | Sentiment delta | IDENTICAL | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Mexico | Sentiment delta | SHAM | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Mexico | Score delta | baseline | EXPLICIT | 4 | 4 | -0.1000 | 0.7500 | 1.0000 | [-0.625, +0.525] | Not below 0.05 |
| nationality | Mexico | Score delta | IDENTICAL | EXPLICIT | 4 | 4 | -0.1000 | 0.7500 | 1.0000 | [-0.625, +0.525] | Not below 0.05 |
| nationality | Mexico | Score delta | SHAM | EXPLICIT | 4 | 4 | +0.1000 | 0.7500 | 1.0000 | [-0.562, +0.662] | Not below 0.05 |
| nationality | Nigeria | Sentiment delta | baseline | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Nigeria | Sentiment delta | IDENTICAL | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Nigeria | Sentiment delta | SHAM | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Nigeria | Score delta | baseline | EXPLICIT | 4 | 4 | -0.0250 | 1.0000 | 1.0000 | [-0.550, +0.675] | Not below 0.05 |
| nationality | Nigeria | Score delta | IDENTICAL | EXPLICIT | 4 | 4 | -0.0250 | 1.0000 | 1.0000 | [-0.550, +0.675] | Not below 0.05 |
| nationality | Nigeria | Score delta | SHAM | EXPLICIT | 4 | 4 | +0.1750 | 0.8750 | 1.0000 | [-0.225, +0.750] | Not below 0.05 |
| nationality | Pakistan | Sentiment delta | baseline | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Pakistan | Sentiment delta | IDENTICAL | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Pakistan | Sentiment delta | SHAM | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | Pakistan | Score delta | baseline | EXPLICIT | 4 | 4 | +0.0250 | 1.0000 | 1.0000 | [-0.325, +0.300] | Not below 0.05 |
| nationality | Pakistan | Score delta | IDENTICAL | EXPLICIT | 4 | 4 | +0.0250 | 1.0000 | 1.0000 | [-0.325, +0.300] | Not below 0.05 |
| nationality | Pakistan | Score delta | SHAM | EXPLICIT | 4 | 4 | +0.2250 | 0.3750 | 1.0000 | [-0.025, +0.475] | Not below 0.05 |
| nationality | South Korea | Sentiment delta | baseline | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | South Korea | Sentiment delta | IDENTICAL | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | South Korea | Sentiment delta | SHAM | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | South Korea | Score delta | baseline | EXPLICIT | 4 | 4 | -0.3500 | 0.5000 | 1.0000 | [-0.850, +0.400] | Not below 0.05 |
| nationality | South Korea | Score delta | IDENTICAL | EXPLICIT | 4 | 4 | -0.3500 | 0.5000 | 1.0000 | [-0.850, +0.400] | Not below 0.05 |
| nationality | South Korea | Score delta | SHAM | EXPLICIT | 4 | 4 | -0.1500 | 0.7500 | 1.0000 | [-0.675, +0.512] | Not below 0.05 |
| nationality | United Arab Emirates | Sentiment delta | baseline | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | United Arab Emirates | Sentiment delta | IDENTICAL | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | United Arab Emirates | Sentiment delta | SHAM | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | United Arab Emirates | Score delta | baseline | EXPLICIT | 4 | 4 | -0.1000 | 0.7500 | 1.0000 | [-0.525, +0.325] | Not below 0.05 |
| nationality | United Arab Emirates | Score delta | IDENTICAL | EXPLICIT | 4 | 4 | -0.1000 | 0.7500 | 1.0000 | [-0.525, +0.325] | Not below 0.05 |
| nationality | United Arab Emirates | Score delta | SHAM | EXPLICIT | 4 | 4 | +0.1000 | 0.8750 | 1.0000 | [-0.275, +0.613] | Not below 0.05 |
| nationality | United Kingdom | Sentiment delta | baseline | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | United Kingdom | Sentiment delta | IDENTICAL | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | United Kingdom | Sentiment delta | SHAM | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| nationality | United Kingdom | Score delta | baseline | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [-0.700, +0.700] | Not below 0.05 |
| nationality | United Kingdom | Score delta | IDENTICAL | EXPLICIT | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [-0.700, +0.700] | Not below 0.05 |
| nationality | United Kingdom | Score delta | SHAM | EXPLICIT | 4 | 4 | +0.2000 | 0.7500 | 1.0000 | [-0.525, +0.925] | Not below 0.05 |
| control | Identical | Sentiment delta | baseline | IDENTICAL | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| control | Identical | Score delta | baseline | IDENTICAL | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | African Black | Sentiment delta | baseline | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | African Black | Sentiment delta | IDENTICAL | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | African Black | Sentiment delta | SHAM | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | African Black | Score delta | baseline | NAME | 4 | 8 | -0.1500 | 0.3750 | 1.0000 | [-0.350, +0.025] | Not below 0.05 |
| ethnicity | African Black | Score delta | IDENTICAL | NAME | 4 | 8 | -0.1500 | 0.3750 | 1.0000 | [-0.350, +0.025] | Not below 0.05 |
| ethnicity | African Black | Score delta | SHAM | NAME | 4 | 8 | +0.0500 | 0.8750 | 1.0000 | [-0.325, +0.300] | Not below 0.05 |
| ethnicity | Anglo Western | Sentiment delta | baseline | NAME | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | Anglo Western | Sentiment delta | IDENTICAL | NAME | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | Anglo Western | Sentiment delta | SHAM | NAME | 4 | 4 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | Anglo Western | Score delta | baseline | NAME | 4 | 4 | -0.0750 | 1.0000 | 1.0000 | [-0.975, +0.600] | Not below 0.05 |
| ethnicity | Anglo Western | Score delta | IDENTICAL | NAME | 4 | 4 | -0.0750 | 1.0000 | 1.0000 | [-0.975, +0.600] | Not below 0.05 |
| ethnicity | Anglo Western | Score delta | SHAM | NAME | 4 | 4 | +0.1250 | 1.0000 | 1.0000 | [-0.575, +0.775] | Not below 0.05 |
| ethnicity | East Asian | Sentiment delta | baseline | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | East Asian | Sentiment delta | IDENTICAL | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | East Asian | Sentiment delta | SHAM | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | East Asian | Score delta | baseline | NAME | 4 | 8 | -0.1000 | 0.6250 | 1.0000 | [-0.512, +0.388] | Not below 0.05 |
| ethnicity | East Asian | Score delta | IDENTICAL | NAME | 4 | 8 | -0.1000 | 0.6250 | 1.0000 | [-0.512, +0.388] | Not below 0.05 |
| ethnicity | East Asian | Score delta | SHAM | NAME | 4 | 8 | +0.1000 | 1.0000 | 1.0000 | [-0.275, +0.688] | Not below 0.05 |
| ethnicity | European | Sentiment delta | baseline | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | European | Sentiment delta | IDENTICAL | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | European | Sentiment delta | SHAM | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | European | Score delta | baseline | NAME | 4 | 8 | -0.1375 | 0.7500 | 1.0000 | [-0.450, +0.163] | Not below 0.05 |
| ethnicity | European | Score delta | IDENTICAL | NAME | 4 | 8 | -0.1375 | 0.7500 | 1.0000 | [-0.450, +0.163] | Not below 0.05 |
| ethnicity | European | Score delta | SHAM | NAME | 4 | 8 | +0.0625 | 0.7500 | 1.0000 | [-0.250, +0.375] | Not below 0.05 |
| ethnicity | Hispanic Latino | Sentiment delta | baseline | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | Hispanic Latino | Sentiment delta | IDENTICAL | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | Hispanic Latino | Sentiment delta | SHAM | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | Hispanic Latino | Score delta | baseline | NAME | 4 | 8 | -0.3375 | 0.5000 | 1.0000 | [-0.850, +0.312] | Not below 0.05 |
| ethnicity | Hispanic Latino | Score delta | IDENTICAL | NAME | 4 | 8 | -0.3375 | 0.5000 | 1.0000 | [-0.850, +0.312] | Not below 0.05 |
| ethnicity | Hispanic Latino | Score delta | SHAM | NAME | 4 | 8 | -0.1375 | 0.7500 | 1.0000 | [-0.525, +0.375] | Not below 0.05 |
| ethnicity | Middle Eastern | Sentiment delta | baseline | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | Middle Eastern | Sentiment delta | IDENTICAL | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | Middle Eastern | Sentiment delta | SHAM | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | Middle Eastern | Score delta | baseline | NAME | 4 | 8 | -0.4000 | 0.2500 | 1.0000 | [-0.725, -0.050] | Not below 0.05 |
| ethnicity | Middle Eastern | Score delta | IDENTICAL | NAME | 4 | 8 | -0.4000 | 0.2500 | 1.0000 | [-0.725, -0.050] | Not below 0.05 |
| ethnicity | Middle Eastern | Score delta | SHAM | NAME | 4 | 8 | -0.2000 | 0.5000 | 1.0000 | [-0.500, +0.100] | Not below 0.05 |
| ethnicity | South Asian | Sentiment delta | baseline | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | South Asian | Sentiment delta | IDENTICAL | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | South Asian | Sentiment delta | SHAM | NAME | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| ethnicity | South Asian | Score delta | baseline | NAME | 4 | 8 | -0.2375 | 0.6250 | 1.0000 | [-0.675, +0.400] | Not below 0.05 |
| ethnicity | South Asian | Score delta | IDENTICAL | NAME | 4 | 8 | -0.2375 | 0.6250 | 1.0000 | [-0.675, +0.400] | Not below 0.05 |
| ethnicity | South Asian | Score delta | SHAM | NAME | 4 | 8 | -0.0375 | 1.0000 | 1.0000 | [-0.362, +0.525] | Not below 0.05 |
| socioeconomic_status | High | Sentiment delta | baseline | SES | 4 | 8 | -0.0190 | 0.1250 | 1.0000 | [-0.026, -0.012] | Not below 0.05 |
| socioeconomic_status | High | Sentiment delta | IDENTICAL | SES | 4 | 8 | -0.0190 | 0.1250 | 1.0000 | [-0.026, -0.012] | Not below 0.05 |
| socioeconomic_status | High | Sentiment delta | SHAM | SES | 4 | 8 | -0.0190 | 0.1250 | 1.0000 | [-0.026, -0.012] | Not below 0.05 |
| socioeconomic_status | High | Score delta | baseline | SES | 4 | 8 | +1.6000 | 0.1250 | 1.0000 | [+1.288, +1.962] | Not below 0.05 |
| socioeconomic_status | High | Score delta | IDENTICAL | SES | 4 | 8 | +1.6000 | 0.1250 | 1.0000 | [+1.288, +1.962] | Not below 0.05 |
| socioeconomic_status | High | Score delta | SHAM | SES | 4 | 8 | +1.8000 | 0.1250 | 1.0000 | [+1.525, +2.275] | Not below 0.05 |
| socioeconomic_status | Low | Sentiment delta | baseline | SES | 4 | 8 | -0.0640 | 0.1250 | 1.0000 | [-0.114, -0.027] | Not below 0.05 |
| socioeconomic_status | Low | Sentiment delta | IDENTICAL | SES | 4 | 8 | -0.0640 | 0.1250 | 1.0000 | [-0.114, -0.027] | Not below 0.05 |
| socioeconomic_status | Low | Sentiment delta | SHAM | SES | 4 | 8 | -0.0640 | 0.1250 | 1.0000 | [-0.114, -0.027] | Not below 0.05 |
| socioeconomic_status | Low | Score delta | baseline | SES | 4 | 8 | -1.8875 | 0.1250 | 1.0000 | [-2.575, -1.387] | Not below 0.05 |
| socioeconomic_status | Low | Score delta | IDENTICAL | SES | 4 | 8 | -1.8875 | 0.1250 | 1.0000 | [-2.575, -1.387] | Not below 0.05 |
| socioeconomic_status | Low | Score delta | SHAM | SES | 4 | 8 | -1.6875 | 0.1250 | 1.0000 | [-2.225, -1.300] | Not below 0.05 |
| socioeconomic_status | Middle | Sentiment delta | baseline | SES | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| socioeconomic_status | Middle | Sentiment delta | IDENTICAL | SES | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| socioeconomic_status | Middle | Sentiment delta | SHAM | SES | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| socioeconomic_status | Middle | Score delta | baseline | SES | 4 | 8 | -0.0875 | 1.0000 | 1.0000 | [-0.550, +0.425] | Not below 0.05 |
| socioeconomic_status | Middle | Score delta | IDENTICAL | SES | 4 | 8 | -0.0875 | 1.0000 | 1.0000 | [-0.550, +0.425] | Not below 0.05 |
| socioeconomic_status | Middle | Score delta | SHAM | SES | 4 | 8 | +0.1125 | 0.7500 | 1.0000 | [-0.375, +0.600] | Not below 0.05 |
| control | Sham formatting | Sentiment delta | baseline | SHAM | 4 | 8 | +0.0000 | 1.0000 | 1.0000 | [+0.000, +0.000] | Not below 0.05 |
| control | Sham formatting | Score delta | baseline | SHAM | 4 | 8 | -0.2000 | 0.3750 | 1.0000 | [-0.400, -0.000] | Not below 0.05 |

### Inference notes

- Exploratory template-level inference; fixed scenarios are not a random population sample.

## Interpretation and next steps

- Mock provider results demonstrate the pipeline only; they are not evidence about a deployed LLM.
- No tested contrasts met the FDR threshold in this run; this does not establish equivalence.
- Selection-rate ratios are descriptive for this synthetic sample and are not legal adverse-impact findings.
