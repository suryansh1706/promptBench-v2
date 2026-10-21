"""Aggregate local checkpoint diagnostics without exposing raw model responses."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


def summarize_response_journal(path):
    with Path(path).open(encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream if line.endswith("\n")]
    word_counts, unmeasurable = [], 0
    for row in rows:
        text = row["raw_text"]
        decision = re.search(r"\[DECISION:\s*[A-Za-z]+\s*\]", text, re.I)
        score = re.search(r"\[SCORE:\s*[+-]?\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?\s*\]", text, re.I)
        if not decision or not score:
            unmeasurable += 1
            continue
        remainder = re.sub(r"\[(?:DECISION|SCORE):[^\]]*\]", "", text, flags=re.I).strip()
        remainder = re.sub(r"^(?:justification|rationale)\s*:\s*", "", remainder, flags=re.I)
        word_counts.append(len(re.findall(r"\b[\w'-]+\b", remainder)))
    completion_tokens = [(row["metadata"].get("usage") or {}).get("completion_tokens") for row in rows]
    completion_tokens = [n for n in completion_tokens if isinstance(n, int)]
    return {
        "responses": len(rows),
        "finish_reasons": dict(Counter(str(row["metadata"].get("finish_reason")) for row in rows)),
        "errors": sum(row.get("status", "ok") != "ok" or bool(row["metadata"].get("error")) for row in rows),
        "parsed_decisions": sum(row["extracted_decision"] not in {None, "ERROR", "BLOCKED"} for row in rows),
        "parsed_scores": sum(row["extracted_score"] is not None for row in rows),
        "duplicate_prompt_ids": len(rows) - len({row["prompt_id"] for row in rows}),
        "duplicate_response_ids": len(rows) - len({row["response_id"] for row in rows}),
        "cache_hits": sum(bool(row["cache_hit"]) for row in rows),
        "distinct_response_texts": len({hashlib.sha256(row["raw_text"].encode()).hexdigest() for row in rows}),
        "completion_tokens_total": sum(completion_tokens),
        "completion_tokens_min": min(completion_tokens, default=None),
        "completion_tokens_max": max(completion_tokens, default=None),
        "justification_word_count_method": "Words after removing bracketed DECISION/SCORE fields and an optional Justification/Rationale label; regex word boundaries. No raw text exported.",
        "justifications_measurable": len(word_counts), "justifications_unmeasurable": unmeasurable,
        "justifications_over_25_words": sum(n > 25 for n in word_counts),
        "justification_words_min": min(word_counts, default=None), "justification_words_max": max(word_counts, default=None),
        "compliance_note": "Length violations are disclosed, not removed from results. Identical answer text can legitimately recur; unique prompt/response IDs check observation duplication.",
    }
