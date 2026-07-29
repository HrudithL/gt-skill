#!/usr/bin/env python3
"""Aggregates every historical convergence run into the "is the skill worth it"
data the Metrics tab charts (07-frontend-runner follow-up): does the skill
converge on well-formatted tables the no-skill baseline misses, is that
consistency real (repeat agreement vs. how often a single baseline sample would
have landed on the skill's own consensus), and what does that cost in tokens
and price per iteration.

Reads both convergence-report layouts (07-frontend-runner.md §4.2's ``unified``
``prompts/<name>/convergence.json`` and the legacy ``consistency_report.json``)
since they share one field schema — the only difference is where the per-repeat
transcripts live for deriving cost/tokens.
"""

from __future__ import annotations

from pathlib import Path

from runner.engine import ROOT
from web.history import _read_json, _result_entry, _timestamp

# Fields whose "good table" reading is a plain present/absent boolean, so a
# skill-consensus-true-rate vs baseline-true-rate comparison is meaningful.
# (heading_band_*/palettes are style choices with no single "correct" value,
# so they're part of the convergence score but not the formatting checklist.)
BOOL_FIELDS = [
    "frame_present", "striping_present", "dividers_present",
    "caption_present", "source_present", "grouping_present", "stub_present",
]
ALL_FIELDS = ["heading_band_shade", "heading_band_hue", "palettes"] + BOOL_FIELDS


def _prompt_slug(text: str | None) -> str:
    text = (text or "").strip()
    return (text[:48] + "…") if len(text) > 48 else (text or "prompt")


def _baseline_match_rate(conv: dict) -> tuple[int, int]:
    """(matches, total) fields where this run's single baseline sample equals
    the skill's own repeat-consensus — i.e. how a no-skill attempt would have
    scored against the bar the skill reliably clears."""
    matches = total = 0
    for field in ALL_FIELDS:
        e = conv.get(field)
        # A run launched with no baseline still writes this field with
        # "baseline": null (present, not absent) — count it as a real
        # disagreement and every field would read as "baseline never matches",
        # fabricating evidence the no-skill run did worse than it ever ran.
        if not isinstance(e, dict) or "consensus" not in e or e.get("baseline") is None:
            continue
        total += 1
        if e["consensus"] == e["baseline"]:
            matches += 1
    return matches, total


def _usage_tokens(usage: dict) -> int:
    """Total tokens actually processed for one iteration: fresh input, prompt-cache
    writes AND reads, plus output. Omitting cache-read tokens would undercount
    skill runs far more than baseline ones (skill runs carry more turns, so a much
    larger share of their input rides the cache), skewing the token comparison."""
    return (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0) \
        + (usage.get("cache_creation_input_tokens") or 0) + (usage.get("cache_read_input_tokens") or 0)


def _token_cost_items(transcripts: list[Path]) -> list[dict]:
    items = []
    for t in transcripts:
        res = _result_entry(t)
        if not res:
            continue
        cost = res.get("total_cost_usd")
        if cost is None:
            continue
        items.append({"tokens": _usage_tokens(res.get("usage") or {}), "cost": cost})
    return items


def _avg(items: list[dict], key: str) -> float | None:
    vals = [i[key] for i in items if i.get(key) is not None]
    return round(sum(vals) / len(vals), 4) if vals else None


# --------------------------------------------------------------------------- #
# unified layout: runs/sweep|convergence/<run>/prompts/<name>/convergence.json
# --------------------------------------------------------------------------- #
def _unified_samples() -> list[dict]:
    samples = []
    for conv_path in sorted(ROOT.glob("runs/*/*/prompts/*/convergence.json")):
        d = _read_json(conv_path)
        if not d or d.get("overall_convergence") is None:
            continue
        prompt_dir = conv_path.parent
        run_dir = prompt_dir.parent.parent
        run_json = _read_json(run_dir / "run.json") or {}
        summ = _read_json(run_dir / "summary.json") or {}
        cfg = run_json.get("config") or summ.get("config") or {}
        model = cfg.get("model") or {}
        conv = d.get("convergence") or {}
        matches, total = _baseline_match_rate(conv)

        base_items, skill_items = [], []
        for r in summ.get("results", []):
            if r.get("name") != prompt_dir.name:
                continue
            cost = r.get("total_cost_usd")
            if cost is None:
                continue
            item = {"tokens": _usage_tokens(r.get("usage") or {}), "cost": cost}
            (base_items if r.get("kind") == "baseline" else skill_items).append(item)

        samples.append({
            "run_id": run_dir.name,
            "timestamp": _timestamp(run_dir.name, run_dir),
            "skill": cfg.get("skill") or d.get("variant"),
            "prompt": _prompt_slug(prompt_dir.name.replace("_", " ")),
            "prompt_key": prompt_dir.name,
            "model": model.get("label") if isinstance(model, dict) else model,
            "convergence": d.get("overall_convergence"),
            "baseline_match_rate": round(matches / total, 3) if total else None,
            "fields": conv,
            "baseline_tokens": _avg(base_items, "tokens"),
            "baseline_cost": _avg(base_items, "cost"),
            "skill_tokens_avg": _avg(skill_items, "tokens"),
            "skill_cost_avg": _avg(skill_items, "cost"),
            "skill_n": len(skill_items),
        })
    return samples


# --------------------------------------------------------------------------- #
# legacy layout: runs/convergence/<run>/consistency_report.json (+ test-runs/)
# --------------------------------------------------------------------------- #
def _legacy_samples() -> list[dict]:
    samples = []
    paths = list(ROOT.glob("runs/*/*/consistency_report.json")) + list(ROOT.glob("test-runs/*/consistency_report.json"))
    for rep_path in sorted(paths):
        d = _read_json(rep_path)
        if not d or d.get("overall_convergence") is None:
            continue
        run_dir = rep_path.parent
        conv = d.get("convergence") or {}
        matches, total = _baseline_match_rate(conv)

        base_tp = run_dir / "baseline" / "transcript.json"
        base_items = _token_cost_items([base_tp]) if base_tp.is_file() else []
        skill_items = _token_cost_items(sorted((run_dir / "with_skill").glob("repeat_*/transcript.json")))

        samples.append({
            "run_id": run_dir.name,
            "timestamp": _timestamp(run_dir.name, run_dir),
            "skill": d.get("skill") or d.get("variant"),
            "prompt": _prompt_slug(d.get("prompt")),
            "prompt_key": _prompt_slug(d.get("prompt")),
            "model": d.get("model"),
            "convergence": d.get("overall_convergence"),
            "baseline_match_rate": round(matches / total, 3) if total else None,
            "fields": conv,
            "baseline_tokens": _avg(base_items, "tokens"),
            "baseline_cost": _avg(base_items, "cost"),
            "skill_tokens_avg": _avg(skill_items, "tokens"),
            "skill_cost_avg": _avg(skill_items, "cost"),
            "skill_n": len(skill_items),
        })
    return samples


def _formatting_checklist(samples: list[dict]) -> list[dict]:
    """Skill-consensus-true-rate vs baseline-true-rate, pooled across every
    sample that has this field — the "does the skill format tables better than
    no skill at all" evidence."""
    out = []
    for field in BOOL_FIELDS:
        skill_true = skill_n = base_true = base_n = 0
        for s in samples:
            e = s["fields"].get(field)
            if not isinstance(e, dict):
                continue
            cons, base = e.get("consensus"), e.get("baseline")
            if isinstance(cons, bool):
                skill_n += 1
                skill_true += int(cons)
            if isinstance(base, bool):
                base_n += 1
                base_true += int(base)
        if skill_n and base_n:
            out.append({
                "field": field,
                "skill_rate": round(skill_true / skill_n, 3),
                "baseline_rate": round(base_true / base_n, 3),
                "n": skill_n,
            })
    return out


def compute_metrics() -> dict:
    samples = _unified_samples() + _legacy_samples()
    samples.sort(key=lambda s: s["timestamp"])

    trend = [{
        "run_id": s["run_id"], "timestamp": s["timestamp"], "skill": s["skill"],
        "prompt": s["prompt"], "model": s["model"],
        "convergence": s["convergence"], "baseline_match_rate": s["baseline_match_rate"],
    } for s in samples]

    cost = [{
        "run_id": s["run_id"], "timestamp": s["timestamp"], "skill": s["skill"],
        "prompt": s["prompt"], "prompt_key": s["prompt_key"],
        "baseline_tokens": s["baseline_tokens"], "baseline_cost": s["baseline_cost"],
        "skill_tokens_avg": s["skill_tokens_avg"], "skill_cost_avg": s["skill_cost_avg"],
        "skill_n": s["skill_n"],
    } for s in samples if s["baseline_tokens"] is not None and s["skill_tokens_avg"] is not None]

    return {
        "trend": trend,
        "formatting": _formatting_checklist(samples),
        "cost": cost,
    }
