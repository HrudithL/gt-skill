#!/usr/bin/env python3
"""RunSpec — the single spec that drives every run, from CLI or web alike.

`python run.py --flags` and `POST /api/runs` both build one of these and hand it
to `runner.orchestrate`, so the file runner and the web app can never diverge in
behavior. This module also owns the two small lookup tables the UI exposes — the
skill-label → engine-variant map and the model-label → concrete-id map — kept
here so there is exactly one place to bump a model id.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# UI skill label -> engine variant token (see runner.engine._VARIANT_SOURCES).
# The four self-contained skills the UI offers; "scripts" is historically the
# engine's "scripted" variant, so the label differs from the token by design.
SKILL_TO_VARIANT: dict[str, str] = {
    "prose": "prose",
    "scripts": "scripted",
    "creator": "creator",
    "house": "house",
}
SKILL_LABELS: tuple[str, ...] = tuple(SKILL_TO_VARIANT)

# The baseline (no-skill control) is realized by the ABSENCE of a skill root, not
# a variant; mirrors runner.engine.BASELINE_VARIANT. Kept here so orchestrate and
# the backend can name it without importing the engine.
BASELINE_VARIANT = "none"

# UI model label -> concrete model id. THE one place to bump an id. The Claude
# Agent SDK passes `model` straight through to Claude Code, which accepts these
# catalog ids; the selected id is threaded to the agent via GTSKILL_AGENT_MODEL.
# (Anthropic model catalog, current 2026-07: Haiku 4.5 / Sonnet 5 / Opus 4.8.)
MODELS: dict[str, str] = {
    "haiku": "claude-haiku-4-5",
    "sonnet": "claude-sonnet-5",
    "opus": "claude-opus-4-8",
}
MODEL_LABELS: tuple[str, ...] = tuple(MODELS)
DEFAULT_MODEL = "haiku"


@dataclass
class PromptRef:
    """One run target: a corpus prompt or an ad-hoc one.

    `prompt` is the text, `data` the CSV path (repo-relative like
    ``data/sp500.csv`` or absolute). `name`/`difficulty` are set for corpus
    prompts (used for the per-prompt directory name and grouping); `source`
    records where it came from for the UI.
    """

    prompt: str
    data: str
    name: str | None = None
    difficulty: str | None = None
    source: str = "adhoc"  # "corpus" | "adhoc" | "template"

    def to_dict(self) -> dict:
        return {
            "prompt": self.prompt,
            "data": self.data,
            "name": self.name,
            "difficulty": self.difficulty,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PromptRef":
        return cls(
            prompt=d["prompt"],
            data=d["data"],
            name=d.get("name"),
            difficulty=d.get("difficulty"),
            source=d.get("source", "adhoc"),
        )


@dataclass
class RunSpec:
    """The parameterized run: one skill, a set of prompts, N repeats, a model.

    Folds the four old runners into one shape:
      - single prompt (old run.py): one prompt, repeats=1, baseline off
      - convergence (old consistency_runner): repeats>1 -> per-prompt convergence
      - sweep (old test_runner): many prompts -> aggregate summary
      - creator (old skill_creator_runner): skill="creator"
    """

    skill: str  # "prose" | "scripts" | "creator" | "house" (UI label)
    prompts: list[PromptRef] = field(default_factory=list)
    repeats: int = 1  # per prompt
    model: str = DEFAULT_MODEL  # shortcut label (haiku/sonnet/opus) or raw Claude id
    # None = auto: baseline runs iff repeats > 1. The user can force it on (even
    # at repeats == 1) or off. See 07-frontend-runner.md §4.1 / §11-Q1.
    baseline: bool | None = None

    # ------------------------------------------------------------------ #
    # derived values
    # ------------------------------------------------------------------ #
    def variant(self) -> str:
        """Engine variant token for the selected skill label."""
        return SKILL_TO_VARIANT[self.skill]

    def model_id(self) -> str:
        """Concrete model id for the selected model.

        Shortcut labels in ``MODELS`` (haiku/sonnet/opus) resolve to their
        pinned Claude ids; any other string is passed through verbatim so
        callers can target arbitrary Claude models (e.g. a specific dated
        release like ``claude-haiku-4-5``) without editing this file.
        """
        return MODELS.get(self.model, self.model)

    def baseline_enabled(self) -> bool:
        """Resolve the auto baseline toggle: on iff repeats>1, unless overridden."""
        if self.baseline is None:
            return self.repeats > 1
        return self.baseline

    def invocation_count(self) -> int:
        """Total agent invocations this spec implies (for the cost warning)."""
        per_prompt = self.repeats + (1 if self.baseline_enabled() else 0)
        return per_prompt * len(self.prompts)

    # ------------------------------------------------------------------ #
    # validation + (de)serialization
    # ------------------------------------------------------------------ #
    def validate(self) -> None:
        """Raise ValueError if the spec is not runnable."""
        if self.skill not in SKILL_TO_VARIANT:
            raise ValueError(
                f"skill must be one of {SKILL_LABELS}, got {self.skill!r}"
            )
        # Model is either a shortcut label in MODELS or an arbitrary
        # Claude model id passed through verbatim. Only the empty string
        # is rejected -- the SDK will surface a clearer error for a bad id.
        if not self.model:
            raise ValueError("model must be a non-empty string")
        if self.repeats < 1:
            raise ValueError(f"repeats must be >= 1, got {self.repeats}")
        if not self.prompts:
            raise ValueError("at least one prompt is required")

    def to_dict(self) -> dict:
        return {
            "skill": self.skill,
            "prompts": [p.to_dict() for p in self.prompts],
            "repeats": self.repeats,
            "model": self.model,
            "baseline": self.baseline,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RunSpec":
        return cls(
            skill=d["skill"],
            prompts=[PromptRef.from_dict(p) for p in d.get("prompts", [])],
            repeats=int(d.get("repeats", 1)),
            model=d.get("model", DEFAULT_MODEL),
            baseline=d.get("baseline", None),
        )
