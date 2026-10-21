"""Presentation figures for descriptive audit results; no significance implied."""
from io import BytesIO
import json
from pathlib import Path
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BLUE = "#2563EB"
TEAL = "#0891B2"
AMBER = "#B45309"
INK = "#172B4D"
MUTED = "#5E6C84"
CONDITIONS = ["NAME", "EXPLICIT", "SES", "IDENTICAL", "SHAM"]


def comparison_frame(comparisons):
    """Keep numeric missing data as missing rather than implying zero changes."""
    rows = []
    for comparison in comparisons:
        get = comparison.get if isinstance(comparison, dict) else lambda key, default=None: getattr(comparison, key, default)
        rows.append({
            "Condition": get("condition", "DEMOGRAPHIC"), "Axis": get("demographic_axis", "unknown").replace("_", " ").title(),
            "Group": get("demographic_group", "Unknown"), "Template": get("template_id", "unknown"),
            "Score change": get("score_delta"), "Sentiment change": get("sentiment_delta"),
            "Lexical similarity": get("embedding_cosine_similarity"), "Decision match": get("decision_matches"),
        })
    return pd.DataFrame(rows, columns=["Condition", "Axis", "Group", "Template", "Score change", "Sentiment change", "Lexical similarity", "Decision match"])



def _style(ax):
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#DDE3EC")
    ax.tick_params(axis="both", labelsize=10, colors=MUTED, length=0)
    ax.grid(axis="x", color="#E8EDF4", linewidth=.8)
    ax.set_axisbelow(True)
    ax.set_facecolor("white")


def figure_png(figure):
    output = BytesIO()
    figure.savefig(output, format="png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output.getvalue()


def condition_figure(frame, metric="Score change"):
    fig, ax = plt.subplots(figsize=(9, 4.1), constrained_layout=True)
    _style(ax)
    rows = frame.dropna(subset=[metric]).groupby("Condition")[metric].agg(["mean", "count"]).reindex(CONDITIONS).dropna()
    if rows.empty:
        ax.text(.5, .5, "No parsed values for this metric", ha="center", transform=ax.transAxes)
        ax.set_axis_off()
        return fig
    y = np.arange(len(rows))
    colors = [AMBER if name in {"IDENTICAL", "SHAM"} else BLUE for name in rows.index]
    ax.barh(y, rows["mean"], color=colors, height=.55)
    ax.set_yticks(y, [f"{name}  ·  {int(row['count'])} pairs" for name, row in rows.iterrows()])
    ax.invert_yaxis()
    ax.axvline(0, color=INK, linewidth=.9)
    extent = max(abs(rows["mean"]).max(), .1 if metric == "Score change" else .002)
    ax.set_xlim(-extent * 1.35, extent * 1.35)
    for index, value in enumerate(rows["mean"]):
        ax.annotate(f"{value:+.2f}" if metric == "Score change" else f"{value:+.4f}",
                    (value, index), xytext=(5 if value >= 0 else -5, 0), textcoords="offset points",
                    va="center", ha="left" if value >= 0 else "right", fontsize=10, color=INK)
    ax.set_xlabel(f"Mean {metric.lower()} relative to reference", color=MUTED, labelpad=12)
    ax.set_title("Treatment changes alongside the controls", loc="left", color=INK, fontsize=14, weight="bold", pad=15)
    return fig


def group_figure(frame, axis, metric):
    selected = frame[(frame["Axis"] == axis) & (~frame["Condition"].isin(["IDENTICAL", "SHAM"]))]
    rows = selected.dropna(subset=[metric]).groupby("Group")[metric].agg(["mean", "count"]).sort_values("mean")
    fig, ax = plt.subplots(figsize=(9, max(3.5, .43 * len(rows) + 1.2)), constrained_layout=True)
    _style(ax)
    if rows.empty:
        ax.text(.5, .5, "No parsed values for this selection", ha="center", transform=ax.transAxes)
        ax.set_axis_off()
        return fig
    positions = np.arange(len(rows))
    ax.barh(positions, rows["mean"], color=TEAL, height=.6)
    ax.set_yticks(positions, [f"{name}  (pairs={int(row['count'])})" for name, row in rows.iterrows()])
    ax.axvline(0, color=INK, linewidth=.9)
    if metric == "Lexical similarity":
        ax.set_xlim(0, 1.06)
    else:
        extent = max(abs(rows["mean"]).max(), .1 if metric == "Score change" else .002)
        ax.set_xlim(-extent * 1.25, extent * 1.25)
    ax.set_xlabel(metric + (" (0 to 1)" if metric == "Lexical similarity" else " relative to reference"), color=MUTED, labelpad=12)
    ax.set_title(f"{axis}: descriptive group means", loc="left", color=INK, fontsize=14, weight="bold", pad=15)
    return fig


def contrast_figure(results):
    fig, ax = plt.subplots(figsize=(10, max(3.6, len(results) * .38 + 1.4)), constrained_layout=True)
    _style(ax)
    for index, result in enumerate(results):
        low, high = result.bootstrap_ci_95
        if low is not None and high is not None:
            ax.hlines(index, low, high, color=BLUE, linewidth=2)
            ax.plot([low, high], [index, index], "|", color=BLUE, markersize=7)
        ax.scatter(result.observed_difference, index, color=BLUE, s=45, zorder=3)
    ax.axvline(0, color=INK, linewidth=1, linestyle="--")
    ax.set_yticks(range(len(results)), [f"{r.demographic_axis.replace('_', ' ')}: {r.target_group}  (n={r.sample_size})" for r in results])
    ax.invert_yaxis()
    ax.set_xlabel("Mean contrast; horizontal lines show bootstrap intervals when estimable", color=MUTED, labelpad=12)
    ax.set_title("Observed contrasts and uncertainty", loc="left", color=INK, fontsize=14, weight="bold", pad=15)
    if not results:
        ax.text(.5, .5, "No contrasts for these filters", ha="center", transform=ax.transAxes)
    return fig


def presentation_figure(comparisons, model, provider, quality):
    """One slide export: disclose data source, denominator and limits on the figure."""
    frame = comparison_frame(comparisons)
    treatments = frame[~frame["Condition"].isin(["IDENTICAL", "SHAM"])]
    parsed = treatments["Decision match"].dropna()
    templates = frame["Template"].nunique()
    fig = plt.figure(figsize=(15, 8.5), facecolor="white")
    fig.text(.055, .94, "CALIBRATED AUDIT  /  RESPONSE AUDIT", fontsize=12, color=TEAL, weight="bold")
    fig.text(.055, .885, "How much did the model's response change?", fontsize=24, color=INK, weight="bold")
    source = "PROGRAMMED MOCK DEMO" if provider == "mock" else "LOCAL MODEL RUN" if provider == "ollama" else "LIVE API RUN"
    fig.text(.055, .84, f"{source}  ·  {model}  ·  {templates} template(s) with valid pairs", fontsize=12, color=MUTED)
    expected = quality.get("expected_pairs")
    valid = quality.get("valid_pairs", len(frame))
    incomplete = expected is not None and valid < expected
    if incomplete:
        fig.text(.055, .795, f"INCOMPLETE RUN  ·  {valid}/{expected} planned pairs available; excluded pairs may change the findings",
                 fontsize=12, color=AMBER, weight="bold")
    consistency = f"{parsed.astype(bool).mean():.1%}" if len(parsed) else "Unavailable"
    kpis = [("Valid treatment pairs", str(len(treatments))), ("Parsed-decision agreement", consistency), ("Pair coverage (including controls)", f"{valid}/{expected}" if expected is not None else "Not recorded")]
    for x, (label, value) in zip([.055, .38, .705], kpis):
        fig.text(x, .745, value, color=INK, fontsize=27, weight="bold")
        fig.text(x, .705, label, color=MUTED, fontsize=11)
    ax1 = fig.add_axes([.16, .24, .37, .37])
    _style(ax1)
    rows = frame.dropna(subset=["Score change"]).groupby("Condition")["Score change"].mean().reindex(CONDITIONS).dropna()
    if len(rows):
        ax1.barh(range(len(rows)), rows.values, color=[AMBER if i in {"IDENTICAL", "SHAM"} else BLUE for i in rows.index])
        ax1.set_yticks(range(len(rows)), rows.index)
        ax1.invert_yaxis()
        extent = max(abs(rows).max(), .1)
        ax1.set_xlim(-extent * 1.35, extent * 1.35)
        for i, value in enumerate(rows):
            ax1.annotate(f"{value:+.2f}", (value, i), xytext=(4 if value >= 0 else -4, 0), textcoords="offset points", ha="left" if value >= 0 else "right", va="center", fontsize=10)
        ax1.axvline(0, color=INK, linewidth=.8)
    else:
        ax1.text(.5, .5, "No paired scores parsed", ha="center", transform=ax1.transAxes)
    ax1.set_title("Mean score change vs reference", loc="left", color=INK, weight="bold", pad=16)
    ax1.set_xlabel("Score points on a 0–100 scale", color=MUTED, labelpad=10)
    ax2 = fig.add_axes([.67, .24, .26, .37])
    _style(ax2)
    values = [int((parsed == True).sum()), int((parsed == False).sum()), len(treatments) - len(parsed)]
    ax2.barh([0, 1, 2], values, color=[BLUE, AMBER, "#94A3B8"], height=.6)
    ax2.set_yticks([0, 1, 2], ["Same", "Changed", "Unparsed"])
    ax2.invert_yaxis()
    ax2.set_xlim(0, max(values + [1]) * 1.2)
    for i, value in enumerate(values):
        ax2.text(value + max(values + [1]) * .025, i, str(value), va="center", fontsize=11, color=INK)
    ax2.set_title("Decision outcomes", loc="left", color=INK, weight="bold", pad=16)
    ax2.set_xlabel("Treatment pairs", color=MUTED, labelpad=10)
    note = ("One template: descriptive results only; confidence intervals and significance are not estimable. " if templates < 2 else "Fixed illustrative templates: exploratory comparisons, not population fairness estimates. ")
    if quality.get("failed_requests") is not None:
        note += f"Excluded request failures: {quality['failed_requests']}. "
    note += "Blue = treatments; amber = calibration controls. NAME/EXPLICIT/SES means can conceal group differences. Lexical similarity and custom-lexicon sentiment are proxies."
    fig.text(.055, .12, textwrap.fill(note, 145), fontsize=10, color=MUTED, va="top", linespacing=1.5)
    fig.text(.055, .035, "Synthetic applicants · fixed substantive numerical qualifications · inspect paired answers before drawing conclusions", fontsize=10, color=TEAL)
    return fig


def presentation_from_dataset(dataset_path, output_path, quality_override=None):
    """Render a minimized CLI JSON export without using any prompt/response text."""
    data = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    axes = summary.get("axis_summaries", {})
    quality = axes.get("run_quality", axes.get("response_quality", summary.get("response_quality", {})))
    quality = dict(quality)
    if "expected_pairs" not in quality and "matched_pairs_generated" in quality:
        quality["expected_pairs"] = quality["matched_pairs_generated"]
    if "failed_requests" not in quality and "failed_or_blocked_responses" in quality:
        quality["failed_requests"] = quality["failed_or_blocked_responses"]
    if quality_override:
        quality = {**quality, **quality_override}
    figure = presentation_figure(data.get("comparisons", []), summary.get("model_name") or data.get("model", "Unspecified model"),
                                 summary.get("provider") or data.get("provider", "unknown"), quality)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(figure_png(figure))
    return target
