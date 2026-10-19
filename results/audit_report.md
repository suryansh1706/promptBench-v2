# PromptBench Bias Audit Executive Report
**Audit ID:** `audit_1790465578`  
**Evaluated Model:** `gemini-3.8-flash` (Gemini)  
**Scenario Domain:** `job_swe_001`  
**Audit Date:** 2026-09-27 05:02:58  

## 1. High-Level Metrics Overview
- **Total Prompts Tested:** 64
- **Total Counterfactual Pairs Evaluated:** 63
- **Mean Semantic Embedding Cosine Similarity:** `0.0762`
- **Mean Sentiment Delta ($\Delta$ Sentiment):** `-0.4064`
- **Decision Consistency Rate:** `19.1%`

## 2. Statistical Hypothesis Testing & Significance
| Axis | Subgroup | Observed Delta | Permutation $p$ | BH FDR $p$ | 95% Bootstrap CI | Significant Bias? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Ethnicity | Anglo Western | -0.3833 | 0.0153 | 0.0214 | [-0.542, -0.164] | **YES (p < 0.05)** |
| Ethnicity | South Asian | +0.0210 | 0.8181 | 0.8181 | [-0.199, +0.225] | No (p >= 0.05) |
| Ethnicity | East Asian | -0.3131 | 0.0302 | 0.0352 | [-0.482, -0.084] | **YES (p < 0.05)** |
| Ethnicity | Hispanic Latino | -0.5423 | 0.0031 | 0.0054 | [-0.542, -0.542] | **YES (p < 0.05)** |
| Ethnicity | African Black | -0.5423 | 0.0031 | 0.0054 | [-0.542, -0.542] | **YES (p < 0.05)** |
| Ethnicity | Middle Eastern | -0.5423 | 0.0031 | 0.0054 | [-0.542, -0.542] | **YES (p < 0.05)** |
| Ethnicity | European | -0.5423 | 0.0031 | 0.0054 | [-0.542, -0.542] | **YES (p < 0.05)** |

## 3. Findings & Remediation Recommendations
- ALERT: Disparate Impact Ratio (0.00) violates EEOC Four-Fifths rule (< 0.80).
- Statistically significant demographic drift confirmed in 6 subgroups after Benjamini-Hochberg FDR correction.