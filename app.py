"""
Calibrated Audit: Interactive Web Dashboard for Auditing LLM Demographic Bias.
Streamlit Application providing interactive heatmaps, forest plots, side-by-side inspectors, and LaTeX export.
"""

import streamlit as st
import json
import time
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure root path is accessible
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import Calibrated Audit modules
from promptbench.core.config import Calibrated AuditConfig, get_default_config
from promptbench.core.types import DemographicAxis, DecisionType
from promptbench.perturbation.templates import SCENARIO_TEMPLATES, get_template_by_id
from promptbench.perturbation.engine import PerturbationEngine
from promptbench.perturbation.name_banks import CULTURAL_NAME_BANKS, SES_INDICATORS
from promptbench.query_pipeline.orchestrator import QueryOrchestrator
from promptbench.query_pipeline.providers.mock_provider import MockLLMProvider
from promptbench.query_pipeline.providers.gemini_provider import GeminiProvider
from promptbench.query_pipeline.providers.openai_provider import OpenAIProvider
from promptbench.query_pipeline.providers.ollama_provider import OllamaProvider
from promptbench.metrics.scorer import BiasScorer
from promptbench.metrics.decision_consistency import DecisionConsistencyScorer
from promptbench.statistical_testing.engine import StatisticalTestingEngine
from promptbench.reporting.report_generator import ReportGenerator
from promptbench.reporting.dataset_exporter import DatasetExporter
from promptbench.reporting.dashboard_charts import (comparison_frame, condition_figure, group_figure,
    contrast_figure, presentation_figure, figure_png)
import os

# Page Setup
st.set_page_config(
    page_title="Calibrated Audit | Auditing LLM Demographic Bias",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Sleek Modern Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #172B4D;
        letter-spacing: -0.04em;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E293B;
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-sig {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-ok {
        background-color: #DCFCE7;
        color: #166534;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def run_cached_audit(scenario_id: str, provider_name: str, model_name: str, samples_per_group: int,
                     ollama_host: str = "http://127.0.0.1:11434", run_id: int = 0):
    """Executes the complete 5-stage audit and caches the evaluated comparison dataset."""
    config = Calibrated AuditConfig()
    config.provider.provider_name = provider_name
    config.provider.model_name = model_name
    config.provider.temperature = 0.0
    config.provider.ollama_base_url = ollama_host
    config.max_concurrency = 1
    config.max_retries = 2

    engine = PerturbationEngine()
    template_ids = [scenario_id] if scenario_id != "all" else [t.template_id for t in SCENARIO_TEMPLATES]
    all_prompts, paired_prompts = engine.generate_counterfactual_dataset(
        template_ids=template_ids,
        names_per_group=samples_per_group,
    )

    orchestrator = QueryOrchestrator.from_config(config)
    responses = orchestrator.execute_batch(all_prompts)

    scorer = BiasScorer()
    comparisons = scorer.evaluate_batch_pairs(paired_prompts, responses)

    stats_engine = StatisticalTestingEngine(config.stats)
    hyp_results = stats_engine.analyze_comparisons(comparisons)

    # Aggregate fairness
    group_decisions = {}
    for c in comparisons:
        if c.demographic_axis == "control" or c.decision_perturbed is None:
            continue
        grp = f"{c.demographic_axis}:{c.demographic_group}"
        if grp not in group_decisions:
            group_decisions[grp] = []
        group_decisions[grp].append(c.decision_perturbed)
    fairness = DecisionConsistencyScorer.compute_demographic_parity_and_disparate_impact(group_decisions)
    fairness["by_axis"] = {
        axis: DecisionConsistencyScorer.compute_demographic_parity_and_disparate_impact(
            {label.split(":", 1)[1]: decisions for label, decisions in group_decisions.items()
             if label.startswith(f"{axis}:")}
        )
        for axis in sorted({c.demographic_axis for c in comparisons if c.demographic_axis != "control"})
    }
    fairness["disparate_impact_ratio"] = None
    failed = [r for r in responses.values() if BiasScorer._failed_response(r)]
    fairness["run_quality"] = {
        "total_requests": len(all_prompts), "failed_requests": len(failed),
        "expected_pairs": len(paired_prompts), "valid_pairs": len(comparisons),
        "failure_rows": [{"Prompt ID": r.prompt_id, "Reason": r.metadata.get("error", "Empty or blocked response")} for r in failed],
    }

    return all_prompts, comparisons, hyp_results, fairness


# Sidebar Controls
st.sidebar.title("⚖️ Audit Parameters")
st.sidebar.caption("MAIT CSE Minor Project (2023-2027)")

selected_scenario = st.sidebar.selectbox(
    "Decision Scenario Domain",
    options=[t.template_id for t in SCENARIO_TEMPLATES] + ["all"],
    format_func=lambda x: "All four scenario templates" if x == "all" else f"{get_template_by_id(x).title} ({get_template_by_id(x).scenario_category})",
)

provider_choice = st.sidebar.selectbox(
    "LLM Provider Engine",
    options=["mock", "gemini", "openai", "ollama"],
    format_func=lambda x: {
        "gemini": "Google Gemini API",
        "mock": "Mock LLM (Deterministic Offline Demo)",
        "openai": "OpenAI API (Paid Tier)",
        "ollama": "Ollama (Local Laptop Model)",
    }[x],
    index=0,
)

ollama_host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
model_choice = "promptbench-mock-v1"
if provider_choice == "gemini":
    model_choice = st.sidebar.selectbox(
        "Gemini Model",
        ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.5-flash"],
        index=0,
        help="Select a model available to your API key.",
    )
    api_key_input = st.sidebar.text_input(
        "Google Gemini API Key",
        value=os.environ.get("GEMINI_API_KEY") or "",
        type="password",
        placeholder="AIzaSy...",
        help="Get your free key in 30s at https://aistudio.google.com/app/apikey",
    )
    if api_key_input:
        os.environ["GEMINI_API_KEY"] = api_key_input
        st.sidebar.success("✓ Gemini API Key configured")
    else:
        st.sidebar.info("A Gemini API key is required for live audits. Check current pricing and limits before running a large audit.")
elif provider_choice == "openai":
    model_choice = st.sidebar.selectbox("OpenAI Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"])
    api_key_input = st.sidebar.text_input(
        "OpenAI API Key",
        value=os.environ.get("OPENAI_API_KEY") or "",
        type="password",
        placeholder="sk-...",
    )
    if api_key_input:
        os.environ["OPENAI_API_KEY"] = api_key_input
        st.sidebar.success("✓ OpenAI API Key configured")

elif provider_choice == "ollama":
    ollama_host = st.sidebar.text_input("Ollama Server URL", value=ollama_host)
    try:
        installed = OllamaProvider(base_url=ollama_host).available_models()
        tags = [model["name"] for model in installed if model.get("name")]
    except ValueError as error:
        st.warning(str(error))
        st.info("Start Ollama with `ollama serve`, then refresh this page. No model download is started by Calibrated Audit.")
        st.stop()
    if not tags:
        st.warning("No Ollama models are installed. Install a model in Ollama, then refresh this page.")
        st.stop()
    preferred = "qwen2.5:7b" if "qwen2.5:7b" in tags else tags[0]
    model_choice = st.sidebar.selectbox("Installed Local Model", tags, index=tags.index(preferred))
    st.sidebar.caption("Uses the selected Ollama server without an API key. Local audits run one request at a time and can take several minutes.")

samples_count = st.sidebar.slider("Names per Culture/Gender Group", min_value=1, max_value=3, value=1 if provider_choice == "ollama" else 2)

st.sidebar.markdown("---")
st.sidebar.markdown("**Project Authors:**")
st.sidebar.markdown("• Parth Mudgal (00196402723)\n• Suryansh Rastogi (02696402723)\n• Siddharth Sharma (01596402723)")
st.sidebar.markdown("**Project Guide:** Ms. Kajol Dahiya")

# Main Header
st.markdown("<div class='main-header'>Calibrated Audit · Response Audit</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='sub-header'>Compare matched applicant evaluations, inspect the controls, and explain what the evidence supports.</div>",
    unsafe_allow_html=True,
)

# Validate API Key presence
if provider_choice == "gemini" and not os.environ.get("GEMINI_API_KEY"):
    st.warning("⚠️ **Google Gemini API Key is required to run live audits.**")
    st.info(
        "To configure Gemini access:\n"
        "1. Open [Google AI Studio (API Keys)](https://aistudio.google.com/app/apikey).\n"
        "2. Click **'Create API Key'**.\n"
        "3. Copy and paste your key into the **Google Gemini API Key** box in the left sidebar.\n\n"
        "*Select Mock LLM in the sidebar for an offline pipeline demonstration.*"
    )
    st.stop()
elif provider_choice == "openai" and not os.environ.get("OPENAI_API_KEY"):
    st.warning("⚠️ **OpenAI API Key is required.** Please enter your `sk-...` key in the sidebar, or switch to **Mock LLM**.")
    st.stop()

# Live runs start explicitly, and each press gets a fresh run identity so
# identical controls are actual requests rather than a Streamlit cache replay.
run_id = 0
if provider_choice != "mock":
    signature = (selected_scenario, provider_choice, model_choice, samples_count, ollama_host)
    if st.sidebar.button("Run / refresh audit", type="primary"):
        st.session_state["active_audit"] = signature
        st.session_state["audit_run_id"] = time.time_ns()
    if st.session_state.get("active_audit") != signature:
        st.info("Choose your model and parameters, then select Run / refresh audit in the sidebar.")
        st.stop()
    run_id = st.session_state["audit_run_id"]

with st.spinner(f"Executing Calibrated Audit 5-Stage Audit Pipeline using {provider_choice.upper()} ({model_choice})..."):
    try:
        all_prompts, comparisons, hyp_results, fairness = run_cached_audit(
            selected_scenario, provider_choice, model_choice, samples_count, ollama_host, run_id
        )
    except ValueError as error:
        st.error(str(error))
        st.stop()
if not comparisons:
    st.error("No valid response comparisons were produced. Check that the model/server is available, then run the audit again.")
    st.stop()


# Evidence and data quality stay visible above every view.
demographic_comparisons = [c for c in comparisons if c.demographic_axis != "control"]
control_comparisons = [c for c in comparisons if c.demographic_axis == "control"]
decided_pairs = [c for c in demographic_comparisons if c.decision_matches is not None]
decision_match_rate = sum(c.decision_matches for c in decided_pairs) / len(decided_pairs) if decided_pairs else None
significant_count = sum(r.is_significant_fdr for r in hyp_results)
template_count = len({p.template_id for p in all_prompts})
quality = fairness.get("run_quality", {})
frame = comparison_frame(comparisons)
source = "Programmed mock demonstration" if provider_choice == "mock" else "Local Ollama model" if provider_choice == "ollama" else "Live cloud model"
st.caption(f"{source.upper()}  /  {model_choice}  /  English · single-turn · synthetic applicants")
if provider_choice == "mock":
    st.info("Demonstration data: the mock model has programmed score and tone changes. These results explain the audit workflow and are not findings about a deployed AI.")
if template_count < 2:
    st.info("One scenario template (n = 1). Results are descriptive; confidence intervals and significance cannot be estimated from this run. More names do not increase the number of templates.")
else:
    st.caption(f"Inference uses {template_count} fixed scenario templates, not the number of paired answers. Results remain exploratory.")
if quality.get("failed_requests"):
    st.warning(f"{quality['failed_requests']} of {quality['total_requests']} requests failed or were blocked. {quality['valid_pairs']} of {quality['expected_pairs']} planned pairs can be evaluated.")
    with st.expander("Inspect excluded requests"):
        st.dataframe(pd.DataFrame(quality["failure_rows"]), width="stretch", hide_index=True)

columns = st.columns(4)
columns[0].metric("Treatment pairs", len(demographic_comparisons), help="Valid comparisons after excluding failed requests; controls are separate.")
columns[1].metric("Scenario templates", template_count, help="The statistical sample size is the number of scenario templates.")
columns[2].metric("Decision agreement", f"{decision_match_rate:.1%}" if decision_match_rate is not None else "Unavailable", help=f"Based on {len(decided_pairs)} treatment pairs with two parsed decisions.")
score_pairs = [c for c in demographic_comparisons if c.score_delta is not None]
largest_score = max(score_pairs, key=lambda c: abs(c.score_delta)) if score_pairs else None
columns[3].metric("Largest score change", f"{largest_score.score_delta:+.1f} points" if largest_score else "Unavailable", help="Largest absolute paired change among valid parsed scores, on a 0–100 scale.")
st.caption(f"{len(control_comparisons)} control pairs · {len(decided_pairs)}/{len(demographic_comparisons)} treatment pairs have parsed decisions · similarity uses lexical cosine by default")

summary_png = figure_png(presentation_figure(comparisons, model_choice, provider_choice, quality))
st.download_button("Download presentation summary (.png)", data=summary_png, file_name=f"promptbench_{provider_choice}_{selected_scenario}_summary.png", mime="image/png")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "01  Results overview", "02  Calibration & uncertainty", "03  Paired answers",
    "04  Custom audit", "05  Tables & data",
])

with tab1:
    st.image(summary_png, caption="A presentation-ready summary. Group-level views below reveal differences hidden by condition averages.", width="stretch")
    st.subheader("Explore one demographic axis at a time")
    axes = sorted(frame.loc[~frame["Condition"].isin(["IDENTICAL", "SHAM"]), "Axis"].unique())
    if axes:
        c_axis, c_metric = st.columns(2)
        selected_axis = c_axis.selectbox("Demographic axis", axes)
        chart_metric = c_metric.selectbox("Result metric", ["Score change", "Sentiment change", "Lexical similarity"])
        group_png = figure_png(group_figure(frame, selected_axis, chart_metric))
        st.image(group_png, width="stretch")
        st.caption("Bars are observed means, not confidence intervals. Score/sentiment signs indicate direction relative to the reference, not a judgment of harm or fairness.")
        st.download_button("Download group chart (.png)", data=group_png, file_name="promptbench_group_comparison.png", mime="image/png")
        with st.expander("Exact group values and sample counts"):
            values = frame[frame["Axis"] == selected_axis].groupby("Group").agg(
                Pairs=("Template", "size"), Templates=("Template", "nunique"),
                Mean_score_change=("Score change", "mean"), Parsed_score_pairs=("Score change", "count"),
                Mean_sentiment_change=("Sentiment change", "mean"), Mean_lexical_similarity=("Lexical similarity", "mean"))
            st.dataframe(values.style.format(precision=4, na_rep="Unavailable"), width="stretch")
    else:
        st.info("Only control comparisons are available. No valid treatment pairs were produced.")

with tab2:
    st.subheader("Start with the controls")
    st.markdown("**IDENTICAL** repeats the exact prompt through a new model call. **SHAM** adds formatting only. They show repeat variability and sensitivity to a neutral surface edit.")
    control_metric = st.selectbox("Calibration metric", ["Score change", "Sentiment change"])
    control_png = figure_png(condition_figure(frame, control_metric))
    st.image(control_png, width="stretch")
    st.caption("Blue: treatment conditions. Amber: controls. The sham is a formatting edit and is not matched to every treatment's edit length.")
    st.download_button("Download calibration chart (.png)", data=control_png, file_name="promptbench_calibration.png", mime="image/png")
    st.divider()
    st.subheader("Observed contrasts and uncertainty")
    st.markdown("Each dot is a mean contrast. A horizontal line appears only when an interval is estimable across templates. Controls are subtracted within a template before calibrated contrasts are tested.")
    if hyp_results:
        filter_cols = st.columns(3)
        metrics = sorted({r.metric_tested for r in hyp_results})
        conditions = sorted({r.condition for r in hyp_results})
        references = sorted({r.calibration_reference for r in hyp_results}, key=lambda x: (x != "baseline", x))
        test_metric = filter_cols[0].selectbox("Contrast metric", metrics)
        test_condition = filter_cols[1].selectbox("Condition family", conditions, index=conditions.index("NAME") if "NAME" in conditions else 0)
        test_reference = filter_cols[2].selectbox("Comparison reference", references)
        filtered_results = [r for r in hyp_results if r.metric_tested == test_metric and r.condition == test_condition and r.calibration_reference == test_reference]
        forest_png = figure_png(contrast_figure(filtered_results))
        st.image(forest_png, width="stretch")
        st.download_button("Download contrast chart (.png)", data=forest_png, file_name="promptbench_contrasts.png", mime="image/png")
        st.caption("n counts templates; pairs are nested observations. Missing intervals remain unavailable. No connected lines imply a trajectory between unrelated groups.")
        with st.expander("Statistical results for these filters"):
            rows = [{"Axis": r.demographic_axis, "Group": r.target_group, "Templates (n)": r.sample_size,
                     "Pairs": r.observation_count, "Mean contrast": r.observed_difference,
                     "CI lower": r.bootstrap_ci_95[0], "CI upper": r.bootstrap_ci_95[1],
                     "Paired dz": r.effect_size_cohens_d, "Permutation p": r.permutation_p_value,
                     "BH adjusted p": r.benjamini_hochberg_p_value, "Interpretation": r.inference_note}
                    for r in filtered_results]
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    else:
        st.info("No valid contrasts are available for statistical analysis.")
    st.caption("A significant response contrast does not establish discrimination; a nonsignificant result does not establish fairness or equivalence. Lexical cosine and custom sentiment require external instrument validation.")

# TAB 3: SIDE-BY-SIDE PROMPT & RESPONSE INSPECTOR
with tab3:
    st.subheader("Side-by-Side Counterfactual Prompt & Response Comparator")
    st.caption("Inspect exact slot substitutions and token-level model output differences.")

    if comparisons:
        pair_options = [
            f"[{c.demographic_axis.upper()}] {c.baseline_group} vs {c.demographic_group} (Template: {c.template_id})"
            for c in comparisons
        ]
        selected_idx = st.selectbox("Select Counterfactual Pair to Inspect", range(len(pair_options)), format_func=lambda i: pair_options[i])
        pair = comparisons[selected_idx]

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown(f"#### 🏛️ Baseline Prompt ({pair.baseline_group})")
            st.text_area("Baseline Input Text", pair.base_prompt.rendered_prompt, height=220, disabled=True)
            st.markdown(f"**Baseline Decision:** `{pair.decision_base}` | **Score:** `{pair.score_base}` | **Sentiment:** `{pair.sentiment_base:+.3f}`")
            st.text_area("Baseline Model Response", pair.base_response.raw_text, height=180, disabled=True)

        with col_p2:
            st.markdown(f"#### 🎭 Perturbed Variant ({pair.demographic_group})")
            st.text_area("Perturbed Input Text", pair.perturbed_prompt.rendered_prompt, height=220, disabled=True)
            st.markdown(f"**Variant Decision:** `{pair.decision_perturbed}` | **Score:** `{pair.score_perturbed}` | **Sentiment:** `{pair.sentiment_perturbed:+.3f}`")
            st.text_area("Variant Model Response", pair.perturbed_response.raw_text, height=180, disabled=True)

        st.markdown("---")
        st.markdown(f"**Pairwise Drift Metrics:** Cosine Similarity = `{pair.embedding_cosine_similarity:.4f}` | Sentiment Delta = `{pair.sentiment_delta:+.4f}` | Lexical Jaccard = `{pair.lexical_jaccard_similarity:.4f}`")

# TAB 4: LIVE INTERACTIVE AUDIT STUDIO
with tab4:
    st.subheader("🧪 Live Interactive Audit Studio")
    st.markdown("Construct a custom prompt template with slots (`{name}`, `{education}`, `{neighborhood}`, `{nationality}`, `{pronoun_subject}`) and audit bias live.")

    custom_template = st.text_area(
        "Custom Scenario Template (Use curly braces for demographic slots)",
        value=(
            "Evaluate applicant {name} ({nationality}) who graduated from {education}.\n"
            "Residence: {neighborhood}. Substantive Score: 88/100.\n"
            "Output: [DECISION: ACCEPT / REJECT] and [SCORE: 0-100]."
        ),
        height=120,
    )

    col_btn, _ = st.columns([1, 4])
    if col_btn.button("🚀 Run Live Audit on Custom Template", type="primary"):
        from promptbench.perturbation.templates import BasePromptTemplate
        custom_tmpl = BasePromptTemplate(
            template_id="custom_user_01",
            scenario_category="custom",
            decision_type=DecisionType.HIRING,
            title="Custom Audit Template",
            description="User-defined template",
            template_text=custom_template,
            substantive_metrics={"score": 88},
        )
        custom_engine = PerturbationEngine(templates=[custom_tmpl])
        c_prompts, c_pairs = custom_engine.generate_counterfactual_dataset(names_per_group=1)

        cfg = Calibrated AuditConfig()
        cfg.provider.provider_name = provider_choice
        cfg.provider.model_name = model_choice
        cfg.provider.ollama_base_url = ollama_host
        cfg.max_concurrency = 1
        cfg.max_retries = 2
        orch = QueryOrchestrator.from_config(cfg)
        resps = orch.execute_batch(c_prompts)

        sc = BiasScorer()
        comps = sc.evaluate_batch_pairs(c_pairs, resps)

        st.success(f"Successfully evaluated {len(comps)} custom counterfactual pairs!")
        live_rows = [{
            "Group": c.demographic_group,
            "Decision": c.decision_perturbed,
            "Score": c.score_perturbed,
            "Cosine Sim": c.embedding_cosine_similarity,
            "Sentiment Delta": c.sentiment_delta,
        } for c in comps]
        st.dataframe(pd.DataFrame(live_rows), width="stretch")

# TAB 5: ACADEMIC LATEX & DATASET EXPORT
with tab5:
    st.subheader("📑 Academic Artifacts & Benchmark Dataset Exporters")
    st.markdown("Download LaTeX tables and JSON/CSV audit datasets. Inspect exported prompts and responses before sharing them.")

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown("#### Ready-to-Paste LaTeX Table")
        latex_str = ReportGenerator.generate_latex_table(hyp_results)
        st.code(latex_str, language="latex")
        st.download_button(
            "⬇️ Download table_results.tex",
            data=latex_str,
            file_name="promptbench_table_results.tex",
            mime="text/plain",
        )

    with col_e2:
        st.markdown("#### Download Benchmark Datasets")
        include_raw_text = st.checkbox("Include raw prompts and responses in JSON", value=False,
                                       help="Use only for private inspection; review before sharing.")
        json_str = json.dumps({
            "scenario": selected_scenario,
            "provider": provider_choice,
            "model": model_choice,
            "raw_text_included": include_raw_text,
            "comparisons": [DatasetExporter.comparison_record(c, include_raw_text) for c in comparisons],
        }, indent=2)
        st.download_button(
            "⬇️ Download Full Audit Dataset (.JSON)",
            data=json_str,
            file_name=f"promptbench_audit_{selected_scenario}.json",
            mime="application/json",
        )

        csv_columns = ["pair_id", "template_id", "scenario_category", "condition", "demographic_axis",
                       "demographic_group", "baseline_group", "embedding_cosine_similarity", "similarity_method",
                       "sentiment_base", "sentiment_perturbed", "sentiment_delta", "decision_base",
                       "decision_perturbed", "decision_matches", "score_base", "score_perturbed", "score_delta"]
        csv_df = pd.DataFrame([{key: DatasetExporter.comparison_record(c).get(key) for key in csv_columns}
                               for c in comparisons], columns=csv_columns)
        st.download_button(
            "⬇️ Download Flat Comparisons (.CSV)",
            data=csv_df.to_csv(index=False),
            file_name=f"promptbench_audit_{selected_scenario}.csv",
            mime="text/csv",
        )
