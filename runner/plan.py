#!/usr/bin/env python3
"""Dry-run a RunSpec into the directory tree it WILL create.

Backs ``POST /api/plan`` and the Run tab's live preview (07-frontend-runner.md
§5.1): a read-only description of the run dir, reflecting the *real* skill mount
for the chosen skill (which SKILL.md / references / scripts get copied in) and
the baseline/repeat/convergence layout — so you see exactly what a launch
produces, and its invocation count, before spending any API budget.

Also owns the run-dir / prompt-dir naming, shared with ``runner.orchestrate`` so
the plan and the actual run agree byte-for-byte on paths.
"""

from __future__ import annotations

from pathlib import Path

from runner.engine import BASELINE_VARIANT, _VARIANT_SOURCES
from runner.convergence import slugify
from runner.spec import MODELS, PromptRef, RunSpec

# Files the harness always produces inside each invocation dir.
_PRODUCES = ["table.py", "table.png", "transcript.json"]


# --------------------------------------------------------------------------- #
# naming (shared with orchestrate)
# --------------------------------------------------------------------------- #
def prompt_dir_name(pref: PromptRef) -> str:
    """Per-prompt directory name: the corpus name, else a slug of the text."""
    return pref.name or slugify(pref.prompt)


def run_slug(spec: RunSpec) -> str:
    """The ``<skill>_<slug-or-multi>`` tail of the run dir name."""
    names = [prompt_dir_name(p) for p in spec.prompts]
    if len(names) == 1:
        tail = names[0]
    elif len(names) == 0:
        tail = "empty"
    else:
        tail = f"{len(names)}prompts"
    return f"{spec.skill}_{tail}"


def run_dir_name(spec: RunSpec, ts: str) -> str:
    """Full run dir name ``<ts>_<skill>_<slug-or-multi>``."""
    return f"{ts}_{run_slug(spec)}"


# The three run types, matching the historical runner kinds. Every run is filed
# under runs/<type>/ so all runs live under one ``runs/`` root, organized by
# what kind of run they are.
RUN_TYPES = ("single", "convergence", "sweep")


def run_type(spec: RunSpec) -> str:
    """Classify a run by shape: sweep (many prompts) > convergence (repeats>1) > single.

    Multiple prompts read as a ``sweep`` (the old test_runner shape) even with
    repeats; a single prompt run N>1 times is a ``convergence`` run (the old
    consistency_runner shape); one prompt once is a ``single`` run.
    """
    if len(spec.prompts) > 1:
        return "sweep"
    if spec.repeats > 1:
        return "convergence"
    return "single"


def run_dir_relpath(spec: RunSpec, ts: str) -> str:
    """Run dir path relative to the repo root: ``runs/<type>/<ts>_<skill>_<slug>``."""
    return f"runs/{run_type(spec)}/{run_dir_name(spec, ts)}"


# --------------------------------------------------------------------------- #
# plan
# --------------------------------------------------------------------------- #
def _mount_entries(variant: str) -> list[str]:
    """Top-level entries of the skill that ``variant`` mounts (SKILL.md, dirs...).

    Reflects the real source dir so the preview shows scripts/ only for the
    scripts skill, etc. Empty for the baseline (no skill root).
    """
    if variant == BASELINE_VARIANT:
        return []
    src, _mounted = _VARIANT_SOURCES[variant]
    if not src.is_dir():
        return []
    names = [c.name for c in src.iterdir() if c.name != "__pycache__" and not c.name.startswith(".")]
    return sorted(names)


def build_plan(spec: RunSpec, ts: str = "<ts>") -> dict:
    """Describe the run dir a launch of ``spec`` would create.

    ``ts`` defaults to a literal placeholder so the preview is stable as config
    changes; orchestrate substitutes a real timestamp at launch. Tolerant of an
    empty prompt set (the Launch button is disabled until ≥1 prompt) so the
    preview can render mid-configuration.
    """
    variant = spec.variant()
    baseline = spec.baseline_enabled()
    mounted = None if variant == BASELINE_VARIANT else _VARIANT_SOURCES[variant][1]
    entries = _mount_entries(variant)

    prompts_plan: list[dict] = []
    for p in spec.prompts:
        dirs: list[dict] = []
        if baseline:
            dirs.append(
                {
                    "label": "baseline",
                    "mounts_skill": False,
                    "skill": None,
                    "entries": [],
                    "data": Path(p.data).name,
                    "produces": _PRODUCES,
                }
            )
        for r in range(1, spec.repeats + 1):
            dirs.append(
                {
                    "label": f"repeat_{r}",
                    "mounts_skill": True,
                    "skill": mounted,
                    "entries": entries,
                    "data": Path(p.data).name,
                    "produces": _PRODUCES,
                }
            )
        prompts_plan.append(
            {
                "name": prompt_dir_name(p),
                "data": Path(p.data).name,
                "dirs": dirs,
                # convergence.json + contact_sheet.png only when repeats > 1
                "convergence": spec.repeats > 1,
            }
        )

    return {
        "run_dir": run_dir_relpath(spec, ts),
        "run_type": run_type(spec),
        "skill": spec.skill,
        "mounted_skill": mounted,
        "variant": variant,
        "model": {"label": spec.model, "id": MODELS.get(spec.model)},
        "repeats": spec.repeats,
        "baseline": baseline,
        "invocation_count": spec.invocation_count(),
        "prompts": prompts_plan,
    }
