"""Link separate domain results without pooling fairness or statistical conclusions.

Usage: python -m promptbench.reporting.experiment_report RESULTS_DIRECTORY
"""
import argparse
from html import escape
import json
from pathlib import Path
from .results_page import write_results_page
from .run_quality import summarize_response_journal


def write_experiment_overview(directory):
    directory = Path(directory)
    totals = {"requests": 0, "usable_responses": 0, "matched_pairs_generated": 0, "valid_pairs": 0}
    sections = []
    all_templates = set()
    completed_domains = 0
    profiles = set()
    for domain, title in (("hiring", "Hiring"), ("loan", "Small-business loan"), ("tenant", "Tenant screening")):
        path = directory / domain / "audit_dataset.json"
        if not path.exists():
            manifest_path = directory / domain / "run_manifest.json"
            journal_path = directory / domain / "responses.private.jsonl"
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text())
                saved = 0
                if journal_path.exists():
                    with journal_path.open("rb") as journal:
                        saved = sum(line.endswith(b"\n") for line in journal)
                state = f'Running / checkpointed: {saved} of {manifest["planned_requests"]} returned responses saved.'
            else:
                state = "Pending — this domain has not started."
            sections.append(f'<article><div class="tag">AWAITING COMPLETION</div><h2>{title}</h2><p>{escape(state)}</p><p class="muted">Results will be linked after scoring and export complete.</p></article>')
            continue
        completed_domains += 1
        payload = json.loads(path.read_text())
        summary, rows = payload["summary"], payload["comparisons"]
        axes = summary.get("axis_summaries", {})
        quality = axes.get("response_quality", {})
        settings = axes.get("run_execution", {}).get("settings", {})
        profiles.add(f'{summary.get("model_name", "Unavailable")} · {settings.get("response_profile", "Unavailable")} · {settings.get("samples_per_group", "Unavailable")} samples per group')
        for key in totals:
            if not isinstance(quality.get(key), int):
                raise ValueError(f"Missing coverage count in {domain}: {key}")
            totals[key] += quality[key]
        templates = {r["template_id"] for r in rows}
        all_templates |= templates
        treatment = [r for r in rows if r.get("condition") not in {"IDENTICAL", "SHAM"}]
        parsed = [r for r in treatment if isinstance(r.get("decision_matches"), bool)]
        changed = sum(not r["decision_matches"] for r in parsed)
        journal = directory / domain / "responses.private.jsonl"
        if journal.exists():
            quality_path = directory / domain / "run_quality.json"
            quality_path.write_text(json.dumps(summarize_response_journal(journal), indent=2), encoding="utf-8")
        write_results_page(path, directory / domain / "results.html")
        def safe(value):
            return escape(str(value))
        sections.append(f'''<article><div class="tag">{safe(len(templates))} original scenario template(s)</div><h2>{title}</h2><p class="stat">{changed} / {len(parsed)} <span>parsed treatment decisions changed</span></p><p>{quality['usable_responses']} / {quality['requests']} usable responses<br>{quality['valid_pairs']} / {quality['matched_pairs_generated']} valid comparisons</p><p class="muted">Model: {safe(summary.get('model_name', 'Unavailable'))}<br>Profile: {safe(settings.get('response_profile', 'Unavailable'))} · token cap {safe(settings.get('max_tokens', 'Unavailable'))}<br>{safe(settings.get('samples_per_group', 'Unavailable'))} samples per group</p><a href="{domain}/results.html">Read {title.lower()} results →</a></article>''')
    profile_text = escape("; ".join(sorted(profiles))) or "Separate local model batches; results pending"
    html = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Calibrated Audit · Larger local experiment</title><style>
    *{{box-sizing:border-box}}body{{margin:0;background:#f0f3f2;color:#172d38;font-family:Inter,system-ui,sans-serif}}main{{max-width:1180px;margin:auto;padding:48px 24px}}header{{background:#123e40;color:white;border-radius:24px;padding:38px}}h1{{font-size:clamp(30px,5vw,52px);letter-spacing:-1.5px}}p{{line-height:1.7}}.tag{{font-size:12px;letter-spacing:1px;text-transform:uppercase}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:24px 0}}article,.note{{background:white;border:1px solid #dce5e2;border-radius:16px;padding:26px}}.stat{{font-size:30px;font-weight:700}}.stat span{{display:block;font-size:14px;font-weight:400;color:#62747d}}.muted{{font-size:13px;color:#62747d}}a{{color:#12635f;font-weight:600}}.notice{{background:#fff1d7;border-left:4px solid #ba7719;padding:20px;margin-top:24px;line-height:1.7}}@media(max-width:800px){{.grid{{grid-template-columns:1fr}}main{{padding:20px 12px}}header{{padding:26px}}}}@media print{{body{{background:white}}}}
    </style><main><header><div class="tag">CALIBRATED AUDIT / LOCAL OLLAMA EXPERIMENT</div><h1>Three domains. Separate results.</h1><p>Completed domains: {completed_domains} / 3<br>Coverage in completed domains: {totals['usable_responses']} / {totals['requests']} usable local responses · {totals['valid_pairs']} / {totals['matched_pairs_generated']} valid comparisons · {len(all_templates)} original scenario templates</p><p>{profile_text}</p></header><div class="notice">Coverage counts are summed for progress only. Decisions, scores, selection rates, and statistical tests are interpreted within each domain; they are not pooled into a fairness score.</div><div class="grid">{''.join(sections)}</div><section class="note"><h2>What this larger experiment can tell you</h2><p>More names and cue substitutions provide more observed comparisons. They do not increase the number of independent scenario templates: hiring has two original cases, loan and tenant screening each have one. Treat these small fixed sets descriptively.</p><p>Review each domain’s changed decisions, before-and-after scores, and IDENTICAL / formatting-only SHAM controls. A response difference alone does not establish discrimination; an unchanged answer does not establish fairness.</p><p class="muted">This brief response profile is distinct from earlier unrestricted answers. Local private checkpoints preserve original observations during resume; final pages contain aggregate metrics without raw prompts, responses, or credentials.</p></section></main></html>'''
    output = directory / "index.html"
    directory.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(write_experiment_overview(parser.parse_args().directory))


if __name__ == "__main__":
    main()
