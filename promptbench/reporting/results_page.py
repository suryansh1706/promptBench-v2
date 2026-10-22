"""Create a portable results report from an audit export, without raw model text.

Usage: python -m promptbench.reporting.results_page audit_dataset.json results.html
"""
import argparse
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape
import json
import math
from pathlib import Path


def _number(value, percent=False):
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        return "Unavailable"
    return f"{value * 100:.1f}%" if percent else f"{value:,.3f}".rstrip("0").rstrip(".")


def _mean(rows, key):
    values = [r.get(key) for r in rows]
    values = [v for v in values if isinstance(v, (int, float)) and math.isfinite(v)]
    return sum(values) / len(values) if values else None


def write_results_page(source, output):
    """Write a self-contained HTML report; only explicitly selected fields appear."""
    source = Path(source)
    payload = json.loads(source.read_text())
    quality_path = source.parent / "run_quality.json"
    generation_quality = json.loads(quality_path.read_text()) if quality_path.exists() else {}
    summary, rows = payload.get("summary", {}), payload.get("comparisons", [])
    axes = summary.get("axis_summaries", {})
    quality = axes.get("response_quality", {})
    templates = {r.get("template_id") for r in rows if r.get("template_id")}
    treatment = [r for r in rows if r.get("condition") not in {"IDENTICAL", "SHAM"}]
    groups = defaultdict(list)
    for row in treatment:
        groups[(row.get("condition", "Unknown"), row.get("demographic_axis", "Unknown"), row.get("demographic_group", "Unknown"))].append(row)
    def count_values(items, key):
        return sum(isinstance(r.get(key), (int, float)) and math.isfinite(r[key]) for r in items)
    def safe(value):
        return escape(str(value))
    def table(headers, data):
        return '<div class="scroll"><table><thead><tr>' + ''.join(f'<th>{safe(h)}</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{safe(v)}</td>' for v in line) + '</tr>' for line in data) + '</tbody></table></div>'
    axis_labels = {"ethnicity": "Name cues", "gender": "Pronoun cues", "nationality": "Nationality cues", "socioeconomic_status": "Socioeconomic background cues"}
    group_table = ""
    for axis in sorted({key[1] for key in groups}):
        group_table += f'<h3>{safe(axis_labels.get(axis, axis.replace("_", " ").title()))}</h3>'
        group_table += table(["Group", "Pairs", "Parsed scores", "Mean score change", "Mean sentiment change", "Decision match"], [
            (group, len(items), count_values(items, "score_delta"), _number(_mean(items, "score_delta")), _number(_mean(items, "sentiment_delta")), _number(_mean(items, "decision_matches"), True))
            for (condition, group_axis, group), items in sorted(groups.items()) if group_axis == axis])
    parsed_decisions = [r for r in treatment if isinstance(r.get("decision_matches"), bool)]
    changed = [r for r in parsed_decisions if r["decision_matches"] is False]
    findings = [f'{len(changed)} of {len(parsed_decisions)} parsed treatment pairs changed the decision.' if parsed_decisions else 'No parsed treatment decisions are available to compare.']
    for (condition, axis, group), items in sorted(groups.items()):
        changed_items = [r for r in items if r.get("decision_matches") is False]
        if changed_items:
            transitions = sorted({f'{r.get("decision_base", "Unavailable")} → {r.get("decision_perturbed", "Unavailable")}' for r in changed_items})
            findings.append(f'{group} ({axis_labels.get(axis, axis)}): {", ".join(transitions)} in {len(changed_items)} pair(s); mean score change {_number(_mean(items, "score_delta"))} points.')
    for axis in ("ethnicity", "gender", "nationality"):
        axis_rows = [r for r in treatment if r.get("demographic_axis") == axis]
        if axis_rows and count_values(axis_rows, "score_delta") == len(axis_rows) and all(r["score_delta"] == 0 for r in axis_rows):
            findings.append(f'{axis_labels[axis]}: scores were unchanged in all {len(axis_rows)} observed pairs.')
    changed_scores = [(group, _mean(items, "score_delta")) for (condition, axis, group), items in sorted(groups.items()) if _mean(items, "score_delta") not in (None, 0)]
    if changed_scores:
        findings.append('Nonzero mean score changes: ' + '; '.join(f'{group} {value:+g} points' for group, value in changed_scores) + '.')
    control_readout = []
    for condition, description in (("IDENTICAL", "Repeating the exact prompt"), ("SHAM", "Changing formatting only")):
        items = [r for r in rows if r.get("condition") == condition]
        delta = _mean(items, "score_delta")
        values = [r["score_delta"] for r in items if isinstance(r.get("score_delta"), (int, float)) and math.isfinite(r["score_delta"])]
        score_range = f' Range: {_number(min(values))} to {_number(max(values))} points.' if values else ''
        parsed_controls = [r for r in items if isinstance(r.get("decision_matches"), bool)]
        decision_changes = sum(not r["decision_matches"] for r in parsed_controls)
        control_readout.append(f'{description}: mean score change {_number(delta)} points across {len(items)} valid pair(s).{score_range} Decisions changed in {decision_changes} of {len(parsed_controls)} parsed control pairs.')
    sham_rows = [r for r in rows if r.get("condition") == "SHAM"]
    sham_mean = _mean(sham_rows, "score_delta")
    sham_magnitudes = [abs(r["score_delta"]) for r in sham_rows if isinstance(r.get("score_delta"), (int, float)) and math.isfinite(r["score_delta"])]
    if sham_magnitudes and max(sham_magnitudes) > 0 and any(abs(value) <= max(sham_magnitudes) for _, value in changed_scores):
        control_readout.append('At least one formatting-only change is as large as or larger than an observed treatment mean score change. This run cannot cleanly attribute those changes to demographic cues; repeat runs and more scenario templates are needed.')
    findings_html = ''.join(f'<li>{safe(finding)}</li>' for finding in findings)
    controls_html = ''.join(f'<p>{safe(finding)}</p>' for finding in control_readout)
    changed_rows = [r for r in treatment if r.get("decision_matches") is False or (isinstance(r.get("score_delta"), (int, float)) and r["score_delta"] != 0)]
    before_after = table(["Cue / group", "Baseline score → variant score", "Score change", "Baseline decision → variant decision"], [
        (f'{axis_labels.get(r.get("demographic_axis"), r.get("demographic_axis", "Unknown"))} / {r.get("demographic_group", "Unknown")}',
         f'{_number(r.get("score_base"))} → {_number(r.get("score_perturbed"))}',
         _number(r.get("score_delta")),
         f'{r.get("decision_base") or "Unavailable"} → {r.get("decision_perturbed") or "Unavailable"}') for r in changed_rows])
    control_table = table(["Control", "Valid pairs", "Score Δ", "Sentiment Δ", "Decision match"], [
        (condition, len(items), _number(_mean(items, "score_delta")), _number(_mean(items, "sentiment_delta")), _number(_mean(items, "decision_matches"), True))
        for condition in ("IDENTICAL", "SHAM")
        for items in [[r for r in rows if r.get("condition") == condition]]])
    # A centered scale makes zero and direction visible without implying inference.
    chart_rows = [(f"{condition} · {group}", _mean(items, "score_delta")) for (condition, axis, group), items in sorted(groups.items())]
    plotted = [(label, value) for label, value in chart_rows if value is not None]
    extent = max([abs(value) for _, value in plotted] + [1.0])
    height = 60 + 32 * len(plotted)
    chart = f'<svg viewBox="0 0 880 {height}" role="img" aria-label="Observed mean score change by treatment group; zero is centered" style="width:100%;height:auto">'
    chart += f'<line x1="540" x2="540" y1="24" y2="{height - 20}" stroke="#9cadb3"/><text x="540" y="15" text-anchor="middle" font-size="12" fill="#62747d">0</text>'
    for index, (label, value) in enumerate(plotted):
        y = 38 + 32 * index
        width = abs(value) / extent * 220
        x = 540 if value >= 0 else 540 - width
        chart += f'<text x="0" y="{y + 13}" font-size="12" fill="#172d38">{safe(label)}</text><rect x="{x}" y="{y}" width="{max(width, 1)}" height="18" rx="3" fill="{("#187d78" if value >= 0 else "#bd7132")}"/><text x="800" y="{y + 13}" font-size="12">{_number(value)}</text>'
    chart += '</svg>' if plotted else '<text x="10" y="35">No parsed score changes available</text></svg>'
    settings = set()
    for row in rows:
        for key in ("base_provenance", "perturbed_provenance"):
            provenance = row.get(key) or {}
            settings.add((str(provenance.get("model_version") or "Unavailable"), str(provenance.get("temperature", "Unavailable")), str(provenance.get("seed", "Unavailable"))))
    provenance_table = table(["Model version / digest", "Temperature", "Seed"], sorted(settings))
    tests = summary.get("hypothesis_test_results", [])
    contrast_table = table(["Condition / group", "Metric", "Reference", "Templates", "Contrast", "95% interval", "FDR p"], [
        (f"{r.get('condition', '')} / {r.get('target_group', '')}", r.get("metric_tested", ""), r.get("calibration_reference", "baseline"), r.get("sample_size", "Unavailable"), _number(r.get("observed_difference")), " to ".join(_number(v) for v in (r.get("bootstrap_ci_95") or [None, None])), _number(r.get("benjamini_hochberg_p_value")))
        for r in tests])
    coverage = table(["Coverage", "Count"], [(label, quality.get(key, "Unavailable")) for label, key in [
        ("Requests", "requests"), ("Usable responses", "usable_responses"), ("Failed or blocked", "failed_or_blocked_responses"), ("Planned pairs", "matched_pairs_generated"), ("Valid pairs", "valid_pairs"), ("Excluded pairs", "excluded_pairs"), ("Responses with parsed decisions", "parsed_decision_responses"), ("Responses with parsed scores", "parsed_score_responses")]])
    execution = axes.get("run_execution", {})
    run_settings = execution.get("settings", {})
    setting_rows = [(label, run_settings.get(key, "Unavailable")) for label, key in (
        ("Response profile", "response_profile"), ("Output token cap", "max_tokens"),
        ("Samples per group", "samples_per_group"), ("Temperature", "temperature"), ("Seed", "seed"))]
    settings_table = table(["Run setting", "Recorded value"], setting_rows)
    provider = summary.get("provider", "Unknown")
    run_label = "PROGRAMMED MOCK DEMONSTRATION" if provider == "mock" else "OBSERVED MODEL RUN"
    timestamp = summary.get("timestamp")
    try:
        date = datetime.fromtimestamp(timestamp, ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y · %H:%M IST")
    except (TypeError, ValueError, OSError):
        date = "Timestamp unavailable"
    incomplete = quality.get("excluded_pairs", 0) or quality.get("failed_or_blocked_responses", 0)
    notice = "Incomplete run: failed responses and excluded pairs limit interpretation." if incomplete else "Coverage counts are reported below; unavailable values remain missing."
    pair_coverage = f'{quality.get("valid_pairs", "?")} / {quality.get("matched_pairs_generated", "?")}'
    cards = [("Decision changes", f"{len(changed)} / {len(parsed_decisions)}" if parsed_decisions else "Unavailable"), ("Valid / planned comparisons", pair_coverage), ("Scenario templates", len(templates)), ("Decisions unchanged¹", _number(_mean(treatment, "decision_matches"), True))]
    html = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Calibrated Audit · Results</title><style>
    :root{font-family:Inter,system-ui,sans-serif;color:#172d38;background:#f0f3f2}*{box-sizing:border-box}body{margin:0}main{max-width:1180px;margin:auto;padding:48px 24px}header{background:#123e40;color:white;border-radius:24px;padding:38px}h1{font-size:clamp(32px,5vw,54px);letter-spacing:-2px;margin:16px 0}h2{font-size:24px;letter-spacing:-.5px}p{line-height:1.65}.eyebrow{font-size:12px;letter-spacing:2px;color:#b3e4cf}.muted{color:#62747d;font-size:14px}.notice{padding:18px 22px;background:#fff1d7;border-left:4px solid #ba7719;border-radius:8px;margin:22px 0}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:24px 0}.card,section{background:white;border:1px solid #dce5e2;border-radius:16px;padding:24px}.card strong{display:block;font-size:30px;margin-top:12px}.card span{font-size:13px;color:#62747d}section{margin:20px 0}.scroll{overflow:auto}table{width:100%;border-collapse:collapse;font-size:13px}th{text-align:left;color:#62747d;font-size:11px;text-transform:uppercase;letter-spacing:.7px}td,th{padding:13px 12px;overflow-wrap:anywhere;border-bottom:1px solid #e7edeb}tbody tr:hover{background:#f5f9f7}.findings{padding-left:22px;line-height:1.7}.findings li{margin:10px 0}h3{font-size:17px;margin-top:28px}details summary{cursor:pointer;padding:12px 0;font-weight:600}footer{font-size:12px;color:#62747d;margin-top:28px}@media(max-width:700px){.cards{grid-template-columns:repeat(2,1fr)}main{padding:20px 12px}header{padding:26px}section{padding:18px}td,th{padding:10px 7px}table{font-size:12px}header small{overflow-wrap:anywhere}}@media print{body{background:white}main{padding:0}details>*{display:block}header{color:#172d38;background:#eee}}
    </style><main>'''
    html += f'<header><div class="eyebrow">CALIBRATED AUDIT / {run_label}</div><h1>Audit results</h1><p>{safe(summary.get("model_name", "Unknown model"))} · {safe(provider)} · {safe(summary.get("scenario_category", "Unknown scenario"))}</p><small>{safe(date)} · {safe(summary.get("audit_id", ""))}</small></header>'
    html += '<section><h2>What happened in this run</h2><ul class="findings">' + findings_html + '</ul><p class="muted">These are observed responses to this scenario, not a conclusion about overall model fairness.</p></section>'
    html += f'<div class="notice">{safe(notice)}</div><div class="cards">' + ''.join(f'<div class="card"><span>{safe(label)}</span><strong>{safe(value)}</strong></div>' for label, value in cards) + '</div>'
    html += f'<p class="muted">Decision match denominator: {count_values(treatment, "decision_matches")} parsed treatment pairs out of {len(treatment)} valid treatment pairs.</p>'
    html += '<p class="muted">¹ Treatment pairs with parsed decisions only; controls excluded. Score changes are variant minus baseline on a 0–100 scale: positive means a higher score, negative means a lower score, and zero means unchanged. Missing parsed scores are excluded from means.</p>'
    html += '<section><h2>What changed: scores and decisions</h2><p class="muted">Only treatment pairs with a changed score or decision are listed. Each arrow runs from the baseline response to the cue variant.</p>' + (before_after if changed_rows else '<p>No changed scores or decisions were recorded in the available treatment pairs.</p>') + '</section>'
    html += '<section><h2>Controls: could a neutral edit also change the answer?</h2>' + controls_html + '<p class="muted">Treatment comparisons change a demographic cue. Controls repeat the same prompt or change only formatting. Compare both before interpreting a treatment difference.</p>' + control_table + '</section>'
    html += '<section><details><summary>Coverage & reliability: request and pair counts</summary>' + coverage + '</details></section>'
    html += '<section><h2>Observed score changes</h2><p class="muted">Perturbed minus baseline; bars are descriptive means on a shared centered scale, without confidence intervals.</p><div class="scroll">' + chart + '</div></section>'
    html += '<section><h2>Group comparisons</h2><p class="muted">Descriptive pair averages. Groups share baselines; these rows are not independent population samples. NAME labels describe perceived name cues, not a person’s ethnicity.</p>' + group_table + '</section>'

    html += '<section><h2>How to read this run</h2><p>' + ('This is one observed scenario template. Results are descriptive; confidence intervals and significance cannot be estimated. More names do not increase the template count.' if len(templates) == 1 else 'Two original scenario templates were observed. Treat this small fixed sample descriptively; exploratory intervals do not establish population fairness. Repeated names remain nested observations, not additional templates.' if len(templates) == 2 else 'No valid template comparisons were exported; interpretation is unavailable.' if not templates else 'Inference uses fixed scenario templates as the analysis unit. These exploratory scenarios are not a random population sample.') + '</p><p>Differences alone do not establish discrimination or legal fairness. SES combines several background cues. Lexical similarity measures wording overlap unless a loaded sentence transformer is explicitly recorded. Sentiment uses a custom English lexicon.</p>' + ('<p>Mock score and tone effects are deliberately programmed and are not observations about a live model.</p>' if provider == 'mock' else '') + '</section>'
    html += '<section><details><summary>Detailed metric / reference contrasts</summary><p class="muted">For a single template these are descriptive contrasts. Reported p-values do not provide evidence of fairness or discrimination; uncertainty requires multiple templates.</p>' + contrast_table + '</details></section>'
    if generation_quality:
        quality_table = table(["Generation check", "Recorded value"], [
            (label, generation_quality.get(key, "Unavailable")) for label, key in (
                ("Returned responses", "responses"), ("Errors", "errors"),
                ("Parsed decisions", "parsed_decisions"), ("Parsed scores", "parsed_scores"),
                ("Duplicate prompt IDs", "duplicate_prompt_ids"), ("Duplicate response IDs", "duplicate_response_ids"),
                ("Cache hits", "cache_hits"), ("Total output tokens", "completion_tokens_total"),
                ("Smallest output (tokens)", "completion_tokens_min"), ("Largest output (tokens)", "completion_tokens_max"),
                ("Justifications measured", "justifications_measurable"), ("Justifications over 25 words", "justifications_over_25_words"),
                ("Justifications unmeasurable", "justifications_unmeasurable"),
                ("Shortest justification (words)", "justification_words_min"),
                ("Longest justification (words)", "justification_words_max"))])
        quality_table += table(["Completion reason", "Responses"], sorted((generation_quality.get("finish_reasons") or {}).items()))
        html += '<section><details><summary>Generation quality & brief-output compliance</summary>' + quality_table + '<p class="muted">Justification words are counted after bracketed decision/score fields and an optional Justification/Rationale label are removed. Length violations are reported, not excluded. Repeated answer text may be legitimate; duplicate IDs check duplicated observations.</p></details></section>'
    html += '<section><details><summary>Recorded model provenance & settings</summary>' + settings_table + provenance_table + '<p class="muted">Only recorded settings are shown. A brief response profile differs from unrestricted earlier answers and should not be pooled with them. Unavailable values were not retained in this export.</p></details></section>'
    html += '<footer>Generated from an audit export. This page includes selected aggregate metrics only; raw prompts, responses, and credentials are not embedded.</footer></main></html>'
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(write_results_page(args.source, args.output))


if __name__ == "__main__":
    main()
