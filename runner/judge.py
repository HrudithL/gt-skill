#!/usr/bin/env python3
"""The grounded LLM judge -- Slice 1 of the hybrid ground-truth comparator.

Per ``.planning/10-hybrid-comparator.md`` §4: two of ``runner.comparator``'s
~25 checks were faking semantic judgment with hardcoded keyword/synonym
lists, and several real quality dimensions (title/subtitle wording, column
order, palette taste) were left entirely unscored because they don't fit a
regex. This module is the fix for those 7 dimensions specifically -- a
one-shot, vision-capable call that scores a candidate table's rendered PNG
against its ground truth's rendered PNG, returning strict structured output.
Nothing else in the repo calls this yet (that wiring is Slice 2, on
``runner.comparator``); this module is usable standalone.

This module NEVER renders, execs, or regenerates a PNG -- it only ever reads
bytes from two already-existing paths (mirrors ``runner.execution_tier``'s
"stub ``gtsave``, never launch a browser" discipline, just one level up: by
the time a PNG reaches this module, it was already produced by a real
render). If a path doesn't exist, ``judge()`` degrades to the same
"unavailable" result every other failure mode produces -- see its docstring.

Model-calling path -- why ``anthropic``, not ``claude_agent_sdk``
------------------------------------------------------------------
``runner.engine`` owns this repo's only other model-calling code, via
``claude_agent_sdk.query()`` -- but that is a full multi-turn AGENTIC
session wrapping the ``claude`` CLI as a subprocess (its own module
docstring says as much), which is the wrong shape for "one single-turn
structured-JSON vision call." Before reaching for the raw ``anthropic``
package, this was investigated directly against the installed
``claude-agent-sdk==0.2.103`` and the ``claude`` CLI it wraps
(``claude --help``, full flag list read end to end):

- **No sampling-temperature control exists anywhere in that path.** Neither
  ``claude_agent_sdk.types.ClaudeAgentOptions`` (every field enumerated) nor
  the ``claude`` CLI's own ``--help`` (every flag read) expose
  ``temperature``/``top_p``/``top_k``/``seed`` in any form -- Claude Code is
  a coding-agent product, not a raw completions API, and this is a
  structural gap, not a missing flag combination.
- **No supported path to attach a caller-supplied image to an outgoing
  user message either.** The SDK's only ``ImageContent`` handling
  (``claude_agent_sdk/__init__.py``, ``_internal/query.py``) is for MCP
  TOOL-CALL RESULTS flowing back to the agent (a custom tool returning an
  image), never for images supplied by the caller in the initial prompt;
  ``query()``'s own docstring examples only ever show plain-string
  ``content``, and the subprocess transport never references a
  ``content``-block shape when building the CLI's stdin.

Both gaps were independently confirmed by direct source inspection (not
guessed), and either alone would be disqualifying. ``anthropic`` (the raw
Messages API) is required. Per this repo's dependency-escalation rule, this
was flagged back rather than decided unilaterally -- see the PR description
for the full writeup; ``anthropic==0.109.2`` happens to already be
pip-installed in the shared ``.venv`` (unused elsewhere in the codebase, not
yet in ``README.md``'s ``pip install`` line), so no new *install* step was
needed to verify this end to end, only the dependency *decision*.

Consistency mechanics -- why there's no ``temperature=0`` in this file
------------------------------------------------------------------------
The spec for this module asked for temperature 0 explicitly ("consistency
matters"). That turned out to be unavailable at the API level too, not just
via ``claude_agent_sdk`` -- confirmed empirically (a live call with
``temperature=0`` against ``claude-sonnet-5`` returned
``400 invalid_request_error: 'temperature' is deprecated for this model``)
and then against Anthropic's own current migration guidance: ``temperature``/
``top_p``/``top_k`` are REMOVED for this model generation -- passing any
non-default value 400s; there is no ``seed`` parameter or other
determinism knob to substitute. Per that same guidance, ``temperature=0``
never actually guaranteed identical outputs even on older models where it
was accepted -- so this is a real capability loss only in the narrow sense
of losing a heuristic that was already inexact, not a hard determinism
guarantee that existed and now doesn't. The recommended (and only available)
substitute is what this module does instead: omit sampling parameters
entirely and lean on a closed, precisely-anchored rubric (``judge_rubric``)
for run-to-run consistency. Thinking is left at its default (adaptive, on)
rather than explicitly disabled -- beyond matching current guidance, a
documented Claude Sonnet 5 failure mode is that a FORCED tool call (this
module's ``tool_choice``) can occasionally arrive as plain text instead of a
proper ``tool_use`` block when thinking is off, which would silently break
the structured-output contract this module depends on.
"""
from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runner import judge_rubric
from runner.spec import MODELS

# engine.py lives at <repo>/runner/engine.py and resolves ROOT the same way;
# mirrored here so `load_dotenv` finds the repo-root `.env` regardless of
# the caller's own cwd (run.py / web/server.py each load it too, but a
# standalone caller -- e.g. Slice 2's CLI, or this module's own smoke test
# -- may not have done so yet).
ROOT = Path(__file__).resolve().parent.parent

# The 7 keys `judge()` always returns, in the exact fixed order Slice 2 will
# look them up by name. Sourced from judge_rubric so the contract and the
# rubric text can never drift apart.
DIMENSION_KEYS: tuple[str, ...] = judge_rubric.DIMENSION_KEYS

_DEFAULT_MODEL = MODELS["sonnet"]  # "claude-sonnet-5" as of runner/spec.py
_MODEL_ENV_VAR = "GTSKILL_JUDGE_MODEL"
# No `temperature` (or `top_p`/`top_k`) is passed -- see the module docstring's
# "Consistency mechanics" section for why: the parameter is REMOVED for this
# model generation, not merely defaulted, so passing ANY value (including 0)
# is a hard 400, not a no-op.
_MAX_TOKENS = 8192  # thinking (on by default, see below) shares this budget with the response
_TIMEOUT_S = 120.0
_UNAVAILABLE_PREFIX = "judge unavailable: "


@dataclass
class JudgeDimension:
    """One scored dimension. ``score`` is 1-5 iff ``applicable``, else
    ``None`` -- never fabricated, never present alongside ``applicable=False``.
    """

    applicable: bool
    score: int | None
    rationale: str

    def to_dict(self) -> dict:
        return {"applicable": self.applicable, "score": self.score, "rationale": self.rationale}


def _unavailable(reason: str) -> dict[str, JudgeDimension]:
    """The shared degrade path: all 7 keys, all ``applicable=False``, every
    ``rationale`` prefixed with ``_UNAVAILABLE_PREFIX`` -- see `judge()`'s
    docstring for why that prefix is the thing callers should key off of to
    distinguish "the judge broke" from "genuinely not applicable."
    """
    rationale = f"{_UNAVAILABLE_PREFIX}{reason}"
    return {key: JudgeDimension(applicable=False, score=None, rationale=rationale) for key in DIMENSION_KEYS}


def _resolve_model() -> str:
    return os.environ.get(_MODEL_ENV_VAR) or _DEFAULT_MODEL


def _load_png_b64(path: Path) -> str:
    return base64.standard_b64encode(path.read_bytes()).decode("ascii")


def _format_metadata_context(metadata: dict) -> str:
    """Render the ground-truth metadata block as readable JSON.

    ``metadata``'s values are always plain dict/list/str/int/bool literals
    per ``comparator.load_ground_truth_metadata()``'s own AST-literal-eval
    contract, so this never has anything non-JSON-serializable to choke on;
    ``default=str`` is just a defensive backstop, not load-bearing.
    """
    return json.dumps(metadata or {}, indent=2, ensure_ascii=False, default=str)


def _build_user_content(prompt_text: str, metadata: dict, truth_b64: str, candidate_b64: str) -> list[dict]:
    """One user message: intro + grounding metadata, then the two images,
    each preceded by an explicit text label -- the standard, reliable way
    to disambiguate multiple images to the model (there is no separate
    per-image "role" in the Messages API).
    """
    intro = (
        "## Original user prompt\n"
        f"{prompt_text}\n\n"
        "## Grounding metadata from the ground truth's own answer key\n"
        "(optional context, not a hard gate, except the grouping rule in "
        "your system instructions)\n"
        f"```json\n{_format_metadata_context(metadata)}\n```"
    )
    closing = (
        "Score the CANDIDATE (second image above) against the GROUND "
        "TRUTH (first image above) now, following the rubric and output "
        "contract in your system instructions."
    )
    return [
        {"type": "text", "text": intro},
        {"type": "text", "text": "=== GROUND TRUTH (reference) rendering ==="},
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": truth_b64}},
        {"type": "text", "text": "=== CANDIDATE rendering (the one you are scoring) ==="},
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": candidate_b64}},
        {"type": "text", "text": closing},
    ]


def _extract_tool_input(response: Any) -> Any:
    """Pull the forced tool call's ``input`` (already a parsed dict, per the
    Anthropic SDK) out of a Messages response. Raises on anything
    unexpected -- the caller (`judge()`) turns that into the standard
    unavailable result; this function itself never needs to degrade
    gracefully since it's always called inside that outer guard.
    """
    for block in getattr(response, "content", []) or []:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == judge_rubric.TOOL_NAME:
            return block.input
    raise ValueError(f"no `{judge_rubric.TOOL_NAME}` tool_use block in model response")


def _validate_and_build(payload: Any) -> dict[str, JudgeDimension] | None:
    """Hand-rolled shape/type validation (no ``jsonschema`` dependency, per
    this repo's constraint) of the model's claimed judgment. All-or-nothing:
    if ANY of the 7 entries fails validation, the whole response is
    considered unparseable (returns ``None``) rather than partially
    salvaging some dimensions and silently patching others -- simpler, and
    it never risks quietly fabricating a value the model didn't actually
    provide in valid form.
    """
    if not isinstance(payload, dict):
        return None
    result: dict[str, JudgeDimension] = {}
    for key in DIMENSION_KEYS:
        entry = payload.get(key)
        if not isinstance(entry, dict):
            return None
        applicable = entry.get("applicable")
        if not isinstance(applicable, bool):
            return None
        rationale = entry.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            return None
        score = entry.get("score")
        if applicable:
            # bool is a subclass of int in Python -- exclude it explicitly
            # so a stray `true`/`false` can't slip through as 1/0.
            if not isinstance(score, int) or isinstance(score, bool) or not (1 <= score <= 5):
                return None
        else:
            score = None  # never trust/propagate a score paired with inapplicable
        result[key] = JudgeDimension(applicable=applicable, score=score, rationale=rationale.strip())
    return result


def judge(
    candidate_png: Path,
    truth_png: Path,
    prompt_text: str,
    metadata: dict,
) -> dict[str, JudgeDimension]:
    """Score 7 quality dimensions of ``candidate_png`` against ``truth_png``.

    One batched, single-turn, vision-capable call to ``$GTSKILL_JUDGE_MODEL``
    (default: ``runner.spec.MODELS["sonnet"]``, i.e. ``claude-sonnet-5``) via
    the raw ``anthropic`` package -- see the module docstring for why
    ``claude_agent_sdk`` (this repo's only other model-calling path, in
    ``runner.engine``) could not be used instead, and for why no
    ``temperature`` is passed (the parameter is removed for this model
    generation, not merely defaulted -- see "Consistency mechanics" above).

    ``metadata`` mirrors ``runner.comparator.load_ground_truth_metadata()``'s
    return shape exactly (keys: ``LABEL_SYNONYMS``, ``REQUIRED_INSTRUCTIONS``,
    ``CAPTION_KEYWORDS``, ``CANONICAL_MEASURES``, ``SEMANTIC_TYPES``) -- this
    module never imports from ``comparator.py``, it just matches the shape
    so a caller can pass that function's return value straight through.

    Returns
    -------
    Always exactly the 7 keys in ``DIMENSION_KEYS`` (``label_concept_correctness``,
    ``caption_quality``, ``grouping_choice_quality``, ``title_quality``,
    ``subtitle_quality``, ``column_order_quality``, ``color_theme_quality``),
    each a ``JudgeDimension(applicable, score, rationale)``. Never raises and
    never fabricates a score -- ``score`` is only ever an int 1-5 when
    ``applicable`` is True, else ``None``.

    Two distinct reasons a dimension can come back ``applicable=False``, and
    how to tell them apart (there is no separate top-level "ok"/"available"
    flag -- the return shape is pinned to exactly the 7 ``JudgeDimension``
    values Slice 2 looks up by name, so the signal lives in ``rationale``
    instead, by explicit convention):

    - **Genuinely not applicable** to this specific comparison (e.g. the
      ground truth doesn't group at all, so ``grouping_choice_quality``
      isn't a discretionary choice being tested here). ``rationale``
      explains the specific reason in prose, and does NOT start with the
      prefix below.
    - **The judge itself is unavailable** -- either PNG path doesn't exist,
      the model call failed or timed out, or its output couldn't be
      validated as well-formed JSON matching the 7-key contract. In this
      case ALL 7 dimensions come back ``applicable=False`` and EVERY
      ``rationale`` starts with the literal prefix ``"judge unavailable: "``
      followed by the reason. Callers that need to distinguish "not
      applicable" from "judge broke" should check for this prefix
      (``rationale.startswith("judge unavailable: ")``) rather than
      treating every ``applicable=False`` the same way.
    """
    try:
        try:
            from dotenv import load_dotenv

            load_dotenv(ROOT / ".env")
        except Exception:
            pass  # best effort; an already-exported env var still works

        candidate_path = Path(candidate_png)
        truth_path = Path(truth_png)

        if not truth_path.is_file():
            return _unavailable(f"ground-truth PNG not found: {truth_path}")
        if not candidate_path.is_file():
            return _unavailable(f"candidate PNG not found: {candidate_path}")

        try:
            import anthropic
        except Exception as e:
            return _unavailable(f"anthropic package not importable: {type(e).__name__}: {e}")

        try:
            truth_b64 = _load_png_b64(truth_path)
            candidate_b64 = _load_png_b64(candidate_path)
        except Exception as e:
            return _unavailable(f"could not read PNG bytes: {type(e).__name__}: {e}")

        model = _resolve_model()
        user_content = _build_user_content(str(prompt_text), metadata, truth_b64, candidate_b64)
        tool_schema = judge_rubric.build_tool_schema()

        try:
            client = anthropic.Anthropic()
            response = client.messages.create(
                model=model,
                max_tokens=_MAX_TOKENS,
                # No temperature/top_p/top_k: removed for this model generation
                # (any non-default value 400s) -- see module docstring's
                # "Consistency mechanics" section. Thinking is left at its
                # adaptive default (explicit here for clarity) rather than
                # disabled -- disabling it is the documented trigger for a
                # forced tool call silently arriving as plain text instead of
                # a `tool_use` block, which would break this call's contract.
                thinking={"type": "adaptive"},
                system=judge_rubric.SYSTEM_PROMPT,
                tools=[tool_schema],
                tool_choice={"type": "tool", "name": judge_rubric.TOOL_NAME},
                messages=[{"role": "user", "content": user_content}],
                timeout=_TIMEOUT_S,
            )
        except Exception as e:
            return _unavailable(f"model call failed (model={model}): {type(e).__name__}: {e}")

        try:
            payload = _extract_tool_input(response)
        except Exception as e:
            return _unavailable(f"could not extract structured output: {type(e).__name__}: {e}")

        result = _validate_and_build(payload)
        if result is None:
            return _unavailable("model returned malformed or incomplete judgment JSON")
        return result
    except Exception as e:  # final safety net -- judge() must never raise
        return _unavailable(f"unexpected error: {type(e).__name__}: {e}")
