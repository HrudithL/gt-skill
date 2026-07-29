#!/usr/bin/env python3
"""Aggregates every historical convergence run into the "is the skill worth it"
data the Metrics tab charts: does the skill converge on well-formatted tables
the no-skill baseline misses, is that consistency real (repeat agreement vs.
how often a single baseline sample would have landed on the skill's own
consensus), and what does that cost in tokens and price per iteration — each
broken out per (skill, prompt) so the comparison isn't hidden inside a
global average.

Reads both convergence-report layouts (the unified
``prompts/<name>/convergence.json`` and the legacy ``consistency_report.json``)
since they share one field schema — the only difference is where the per-repeat
transcripts live for deriving cost/tokens. Every per-sample number is kept as
raw, poolable counts (matches/total, true/n, or a list of per-invocation token
+ cost items) rather than a pre-divided ratio, so grouping several historical
runs of the same (skill, prompt) together sums numerators and denominators
once instead of averaging averages.
"""

from __future__ import annotations

from pathlib import Path

from runner import discover
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

# Legacy consistency_report.json predates the "skill" field and only recorded
# "variant": "scripted" for what every current run/CLI flag calls "scripts" —
# without this, the same skill would split into two groups by (skill, prompt).
_VARIANT_TO_SKILL = {"scripted": "scripts"}


def _prompt_slug(text: str | None) -> str:
    text = (text or "").strip()
    return (text[:48] + "…") if len(text) > 48 else (text or "prompt")


def _corpus_name_lookup() -> dict[str, str]:
    """Full prompt text -> corpus slug (e.g. "sp500_monthly_performance").

    The unified layout already keys samples by that slug (the prompt's
    directory name); the legacy consistency-report layout only stores the
    full prompt text. Without this lookup the same corpus prompt would form
    two separate groups — one per layout — when averaging by (skill, prompt).
    """
    lookup: dict[str, str] = {}
    for prompts in discover.prompts_grouped().values():
        for p in prompts:
            lookup[p["prompt"]] = p["name"]
    return lookup


def _baseline_match_counts(conv: dict) -> tuple[int, int]:
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


def _compliance_counts(conv: dict) -> tuple[int, int, int, int]:
    """(skill_true, skill_n, base_true, base_n) pooled over BOOL_FIELDS — the
    checklist of concrete table elements (frame/striping/captions/...), as
    opposed to the style choices (palette/heading hue) also folded into
    overall convergence. This collapses to one composite compliance ratio."""
    skill_true = skill_n = base_true = base_n = 0
    for field in BOOL_FIELDS:
        e = conv.get(field)
        if not isinstance(e, dict):
            continue
        cons, base = e.get("consensus"), e.get("baseline")
        if isinstance(cons, bool):
            skill_n += 1
            skill_true += int(cons)
        if isinstance(base, bool):
            base_n += 1
            base_true += int(base)
    return skill_true, skill_n, base_true, base_n


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
            "prompt": prompt_dir.name.replace("_", " "),
            "prompt_key": prompt_dir.name,
            "model": model.get("label") if isinstance(model, dict) else model,
            "convergence": d.get("overall_convergence"),
            "fields": conv,
            "baseline_match": _baseline_match_counts(conv),
            "compliance": _compliance_counts(conv),
            "base_items": base_items,
            "skill_items": skill_items,
        })
    return samples


# --------------------------------------------------------------------------- #
# legacy layout: runs/convergence/<run>/consistency_report.json (+ test-runs/)
# --------------------------------------------------------------------------- #
def _legacy_samples(corpus_names: dict[str, str]) -> list[dict]:
    samples = []
    paths = list(ROOT.glob("runs/*/*/consistency_report.json")) + list(ROOT.glob("test-runs/*/consistency_report.json"))
    for rep_path in sorted(paths):
        d = _read_json(rep_path)
        if not d or d.get("overall_convergence") is None:
            continue
        run_dir = rep_path.parent
        conv = d.get("convergence") or {}
        prompt_text = d.get("prompt")
        prompt_key = corpus_names.get(prompt_text) or _prompt_slug(prompt_text)

        base_tp = run_dir / "baseline" / "transcript.json"
        base_items = _token_cost_items([base_tp]) if base_tp.is_file() else []
        skill_items = _token_cost_items(sorted((run_dir / "with_skill").glob("repeat_*/transcript.json")))

        samples.append({
            "run_id": run_dir.name,
            "timestamp": _timestamp(run_dir.name, run_dir),
            "skill": d.get("skill") or _VARIANT_TO_SKILL.get(d.get("variant"), d.get("variant")),
            "prompt": prompt_key,
            "prompt_key": prompt_key,
            "model": d.get("model"),
            "convergence": d.get("overall_convergence"),
            "fields": conv,
            "baseline_match": _baseline_match_counts(conv),
            "compliance": _compliance_counts(conv),
            "base_items": base_items,
            "skill_items": skill_items,
        })
    return samples


def _ratio(numer: int, denom: int) -> float | None:
    return round(numer / denom, 3) if denom else None


def _formatting_checklist_global(samples: list[dict]) -> list[dict]:
    """Skill-consensus-true-rate vs baseline-true-rate per checklist field,
    pooled globally across every sample and every skill/prompt — which
    specific table elements the skill reliably adds that a no-skill attempt
    doesn't. (For a per-(skill, prompt) breakdown see `by_skill_prompt`'s
    compliance columns, a single composite rate across all these fields.)"""
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


def _by_skill_prompt(samples: list[dict]) -> list[dict]:
    """One row per (skill, prompt), pooling every historical sample of that
    combo — the "average per skill per prompt" view across all four metrics:
    formatting-checklist compliance, repeat-to-repeat consistency, tokens, and
    price. Every baseline_* value is the same no-skill benchmark reused across
    metrics; every skill_*_avg is the with-skill average for that combo."""
    groups: dict[tuple[str, str], dict] = {}
    for s in samples:
        key = (s["skill"] or "unknown", s["prompt_key"])
        g = groups.setdefault(key, {
            "skill": s["skill"] or "unknown", "prompt_key": s["prompt_key"],
            "run_ids": set(), "conv_vals": [],
            "match_m": 0, "match_t": 0,
            "comp_st": 0, "comp_sn": 0, "comp_bt": 0, "comp_bn": 0,
            "base_items": [], "skill_items": [],
        })
        g["run_ids"].add(s["run_id"])
        if s["convergence"] is not None:
            g["conv_vals"].append(s["convergence"])
        m, t = s["baseline_match"]
        g["match_m"] += m
        g["match_t"] += t
        st, sn, bt, bn = s["compliance"]
        g["comp_st"] += st
        g["comp_sn"] += sn
        g["comp_bt"] += bt
        g["comp_bn"] += bn
        g["base_items"].extend(s["base_items"])
        g["skill_items"].extend(s["skill_items"])

    rows = []
    for g in groups.values():
        rows.append({
            "skill": g["skill"], "prompt": g["prompt_key"].replace("_", " "), "prompt_key": g["prompt_key"],
            "n_runs": len(g["run_ids"]), "n_iterations": len(g["skill_items"]),
            "skill_consistency_avg": round(sum(g["conv_vals"]) / len(g["conv_vals"]), 3) if g["conv_vals"] else None,
            "baseline_consistency": _ratio(g["match_m"], g["match_t"]),
            "skill_compliance_avg": _ratio(g["comp_st"], g["comp_sn"]),
            "baseline_compliance": _ratio(g["comp_bt"], g["comp_bn"]),
            "baseline_tokens": _avg(g["base_items"], "tokens"),
            "skill_tokens_avg": _avg(g["skill_items"], "tokens"),
            "baseline_cost": _avg(g["base_items"], "cost"),
            "skill_cost_avg": _avg(g["skill_items"], "cost"),
        })
    rows.sort(key=lambda r: (r["skill"], r["prompt"]))
    return rows


def compute_metrics() -> dict:
    corpus_names = _corpus_name_lookup()
    samples = _unified_samples() + _legacy_samples(corpus_names)

    return {
        "by_skill_prompt": _by_skill_prompt(samples),
        "formatting": _formatting_checklist_global(samples),
    }
