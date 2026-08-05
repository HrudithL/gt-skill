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
import io
import json
import math
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

# Model ids (by prefix) known to support `thinking={"type": "adaptive"}`
# (Codex round-1 finding: this was previously sent unconditionally, which
# 400s on GTSKILL_JUDGE_MODEL overrides like "claude-haiku-4-5" -- a real,
# documented MODELS["haiku"] entry -- since older/smaller models only
# support `{"type": "enabled", "budget_tokens": N}` or no `thinking` at all,
# never "adaptive"). Deliberately an ALLOWLIST, not a denylist: omitting
# `thinking` entirely is accepted by every model tier without erroring, so
# that's the safe default for anything not explicitly known to support
# adaptive thinking -- unlike guessing "adaptive" is fine and risking a 400
# on a model that doesn't support it.
_ADAPTIVE_THINKING_MODEL_PREFIXES = (
    "claude-sonnet-5",
    "claude-sonnet-4-6",
    "claude-opus-5",
    "claude-opus-4-8",
    "claude-opus-4-7",
    "claude-opus-4-6",
    "claude-fable-5",
    "claude-mythos-5",
)

# Long-edge pixel cap a single image is kept under before this module starts
# splitting it into vertical tiles (Codex round-1 finding: real ground
# truths in this corpus can be very tall -- e.g. sp500_monthly_performance.png
# at 2012x5936 -- and Claude's vision pipeline downscales anything over its
# own resolution cap before the model ever "sees" it, which for an image
# this tall shrinks title/caption/column-label text past legibility).
# Matches claude-sonnet-5's (the pinned default model) own documented
# high-resolution cap, so an ordinary table -- even a moderately tall one
# like towny_growth_trends.png at 2014x1782 -- is sent untouched as a single
# image; only genuinely extreme heights get split.
_MAX_TILE_DIMENSION = 2576
# Defensive ceiling on tile count so a pathologically tall image can't
# balloon one request into dozens of images -- no ground truth in this
# corpus needs more than ~3.
_MAX_TILES = 12


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


def _supports_adaptive_thinking(model: str) -> bool:
    """Whether ``model`` is known to accept ``thinking={"type": "adaptive"}``.

    See ``_ADAPTIVE_THINKING_MODEL_PREFIXES`` -- an allowlist, so an
    unrecognized model id (a future model this list hasn't been updated
    for, or a typo) defaults to False, i.e. no ``thinking`` parameter at
    all, which every model tier accepts.
    """
    return model.startswith(_ADAPTIVE_THINKING_MODEL_PREFIXES)


def _load_png_b64(path: Path) -> str:
    return base64.standard_b64encode(path.read_bytes()).decode("ascii")


def _load_image_tiles_b64(path: Path) -> list[str]:
    """Base64 PNG tile(s) for ``path``, top-to-bottom, each within a safe
    long-edge dimension for Claude's vision pipeline.

    The common case (a table whose rendered height is already within
    ``_MAX_TILE_DIMENSION`` -- true for every ground truth in this corpus
    except ``sp500_monthly_performance.png``) returns the file's own bytes
    completely untouched, via ``_load_png_b64`` -- no PIL re-encoding, no
    behavior change from before this fix. Only when the image is genuinely
    too tall does this crop it into vertical bands (full width, bounded
    height each) and PNG-re-encode each band; only height is ever split --
    width isn't part of the reported problem and every table in this corpus
    stays comfortably under the cap on that axis.

    Splitting trades a small increase in image tokens and asking the model
    to mentally stitch bands back into one table (mitigated by the explicit
    "part i of N" labels ``_image_blocks`` attaches, and by the system
    prompt's "Image tiling" section) for keeping small text legible -- an
    acceptable tradeoff here since this judge's 7 dimensions are about
    labels/captions/titles/column-order/color, not the kind of precise
    cross-row numeric reading the deterministic comparator's own value-diff
    checks already own.
    """
    from PIL import Image

    with Image.open(path) as img:
        width, height = img.size
        if height <= _MAX_TILE_DIMENSION:
            return [_load_png_b64(path)]

        tile_height = max(_MAX_TILE_DIMENSION, math.ceil(height / _MAX_TILES))
        n_tiles = math.ceil(height / tile_height)
        tiles: list[str] = []
        for i in range(n_tiles):
            top = i * tile_height
            bottom = min(top + tile_height, height)
            crop = img.crop((0, top, width, bottom))
            buf = io.BytesIO()
            crop.save(buf, format="PNG")
            tiles.append(base64.standard_b64encode(buf.getvalue()).decode("ascii"))
        return tiles


def _format_metadata_context(metadata: dict) -> str:
    """Render the ground-truth metadata block as readable JSON.

    ``metadata``'s values are always plain dict/list/str/int/bool literals
    per ``comparator.load_ground_truth_metadata()``'s own AST-literal-eval
    contract, so this never has anything non-JSON-serializable to choke on;
    ``default=str`` is just a defensive backstop, not load-bearing.
    """
    return json.dumps(metadata or {}, indent=2, ensure_ascii=False, default=str)


def _image_blocks(tiles_b64: list[str], label: str) -> list[dict]:
    """Text-labeled image content block(s) for one rendering's tile(s).

    A single tile (the common case) gets one plain ``=== {label} ===``
    caption. Multiple tiles (a table too tall for one image -- see
    ``_load_image_tiles_b64``) each get an explicit "part i of N" caption so
    the model treats them as sequential vertical slices of ONE table, not
    separate tables -- reinforcing the system prompt's "Image tiling"
    section rather than relying on it alone.
    """
    blocks: list[dict] = []
    n = len(tiles_b64)
    for i, tile_b64 in enumerate(tiles_b64, 1):
        caption = label if n == 1 else f"{label}, part {i} of {n} (top-to-bottom, same table)"
        blocks.append({"type": "text", "text": f"=== {caption} ==="})
        blocks.append({"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": tile_b64}})
    return blocks


def _build_user_content(
    prompt_text: str, metadata: dict, truth_tiles: list[str], candidate_tiles: list[str]
) -> list[dict]:
    """One user message: intro + grounding metadata, then the two renderings
    (each 1+ tiles, see ``_load_image_tiles_b64``), each preceded by an
    explicit text label -- the standard, reliable way to disambiguate
    multiple images to the model (there is no separate per-image "role" in
    the Messages API).
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
        "Score the CANDIDATE rendering against the GROUND TRUTH rendering "
        "now, following the rubric and output contract in your system "
        "instructions."
    )
    content: list[dict] = [{"type": "text", "text": intro}]
    content += _image_blocks(truth_tiles, "GROUND TRUTH (reference) rendering")
    content += _image_blocks(candidate_tiles, "CANDIDATE rendering (the one you are scoring)")
    content.append({"type": "text", "text": closing})
    return content


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
            truth_tiles = _load_image_tiles_b64(truth_path)
            candidate_tiles = _load_image_tiles_b64(candidate_path)
        except Exception as e:
            return _unavailable(f"could not read/tile PNG bytes: {type(e).__name__}: {e}")

        model = _resolve_model()
        user_content = _build_user_content(str(prompt_text), metadata, truth_tiles, candidate_tiles)
        tool_schema = judge_rubric.build_tool_schema()

        # No temperature/top_p/top_k: removed for claude-sonnet-5 (any
        # non-default value 400s) -- see module docstring's "Consistency
        # mechanics" section. `thinking` is model-gated (Codex round-1
        # finding): sent only for models known to support the "adaptive"
        # mode (see _supports_adaptive_thinking) -- sending it unconditionally
        # 400s on a GTSKILL_JUDGE_MODEL override to an older/smaller model
        # (e.g. "claude-haiku-4-5", a real MODELS["haiku"] entry) that only
        # supports `{"type": "enabled", "budget_tokens": N}` or no thinking
        # at all. When sent, adaptive is preferred over disabling thinking
        # -- disabling it is the documented trigger for a forced tool call
        # silently arriving as plain text instead of a `tool_use` block,
        # which would break this call's contract.
        create_kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": _MAX_TOKENS,
            "system": judge_rubric.SYSTEM_PROMPT,
            "tools": [tool_schema],
            "tool_choice": {"type": "tool", "name": judge_rubric.TOOL_NAME},
            "messages": [{"role": "user", "content": user_content}],
            "timeout": _TIMEOUT_S,
        }
        if _supports_adaptive_thinking(model):
            create_kwargs["thinking"] = {"type": "adaptive"}

        try:
            client = anthropic.Anthropic()
            response = client.messages.create(**create_kwargs)
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
