#!/usr/bin/env python3
"""Rubric + system prompt for ``runner.judge`` (Slice 1 of the hybrid
ground-truth comparator -- see ``.planning/10-hybrid-comparator.md`` §4).

Mirrors the anchor-definition STYLE of the superseded ``.planning/02-judge.md``
spec -- which itself deferred anchor text to ``SPEC.md``'s "Evaluation
Rubric" table (one row per dimension, terse 1/3/5-point anchors) -- rather
than inventing a new rubric style from scratch. Kept as a plain Python
module (not a separate ``.md`` file) to match every other file in
``runner/``: ``engine.py``'s ``_RENDER_INSTRUCTIONS`` is the closest existing
precedent for "prose text embedded as a module constant because it's
consumed as prompt text at runtime," and ``comparator.py``'s metadata dicts
are the precedent for "plain literal, human-reviewable answer key."

``DIMENSIONS`` below IS the rubric, read top to bottom by a human reviewer;
``SYSTEM_PROMPT`` is rendered from it so the text actually sent to the model
can never drift out of sync with the anchors a reviewer sees here.
"""
from __future__ import annotations

# Each entry: what the dimension assesses, plus 1/3/5-point anchors (2 and 4
# are intentionally left as "between the neighboring anchors" rather than
# given their own prose -- matching SPEC.md's Evaluation Rubric table, which
# also only defines 1/3/5 columns).
DIMENSIONS: dict[str, dict] = {
    "label_concept_correctness": {
        "title": "Column-label concept correctness",
        "assesses": (
            "Does each rendered column label clearly and correctly name the "
            "underlying concept it shows (e.g. a price column isn't labeled "
            "like a count)? LABEL_SYNONYMS, if provided, is optional "
            "grounding context -- any reasonable phrasing for the right "
            "concept scores well; it is not a hard gate."
        ),
        "anchors": {
            1: (
                "One or more labels name the WRONG concept or actively "
                "mislead (e.g. a percent-change column labeled as if it "
                "were a raw count, a price column that reads like a rank)."
            ),
            3: (
                "Every label names the right concept, but phrasing is "
                "awkward, inconsistent in style/units across columns, or "
                "leans on the column-group spanner to disambiguate more "
                "than it should."
            ),
            5: (
                "Every label instantly and unambiguously names its exact "
                "underlying concept -- as clear as (not necessarily "
                "identical to) the ground truth's own labels."
            ),
        },
    },
    "grouping_choice_quality": {
        "title": "Grouping-choice quality (discretionary only)",
        "assesses": (
            "ONLY applicable when the ground truth's own rendering uses "
            "row grouping AND REQUIRED_INSTRUCTIONS has no 'grouping' key "
            "(i.e. grouping was the ground-truth author's editorial "
            "choice, not a prompt mandate). When applicable: is the "
            "candidate's grouping variable (or its reasoned choice not to "
            "group) a sensible, goal-serving structural decision given the "
            "prompt? See the Applicability section below -- self-report "
            "applicable=false whenever the condition doesn't hold, "
            "INCLUDING when neither table groups at all."
        ),
        "anchors": {
            1: (
                "Candidate groups by a variable unrelated to the "
                "analytical story, or its flat/ungrouped presentation "
                "actively obscures a natural structure the ground truth's "
                "grouping reveals."
            ),
            3: (
                "Grouping choice (or non-grouping choice) is defensible "
                "but less illuminating than the ground truth's."
            ),
            5: (
                "Candidate's grouping choice (or reasoned non-grouping "
                "choice) serves the prompt's goal as well as the ground "
                "truth's own choice."
            ),
        },
    },
    "title_quality": {
        "title": "Title quality",
        "assesses": (
            "Is the candidate's title clear, accurate, and does it match "
            "the core framing/subject the ground truth's own title "
            "establishes? Wording need not match -- the FRAMING should."
        ),
        "anchors": {
            1: (
                'Title is generic ("Table 1", "Data Summary"), inaccurate, '
                "or contradicts what the table actually shows."
            ),
            3: (
                "Title is accurate but flat/generic -- technically "
                "correct, doesn't capture the specific angle the ground "
                "truth's title captures (e.g. names the dataset but not "
                "the story)."
            ),
            5: (
                "Title is clear, accurate, and captures the same core "
                "framing as the ground truth's title."
            ),
        },
    },
    "subtitle_quality": {
        "title": "Subtitle quality",
        "assesses": (
            "Does the subtitle add real clarifying context beyond the "
            "title, without being redundant with it?"
        ),
        "anchors": {
            1: (
                "Missing where the table clearly needs one, or purely "
                "redundant with the title (adds nothing new)."
            ),
            3: (
                "Adds some context but overlaps substantially with the "
                "title or is vague about what's actually shown."
            ),
            5: (
                "Adds real, non-redundant clarifying context (what's "
                "measured, over what scope, grouped/ranked by what) -- as "
                "useful as the ground truth's subtitle."
            ),
        },
    },
    "column_order_quality": {
        "title": "Column order quality",
        "assesses": (
            "Is the candidate's left-to-right column order a sensible "
            "reading order for the analytical story? Compare against the "
            "ground truth's own order as ONE example of a good order -- do "
            "not require an exact match; multiple orders can be equally "
            "sensible."
        ),
        "anchors": {
            1: (
                "Order is arbitrary or confusing -- a reader must hunt "
                "across the table to follow the story (e.g. a derived "
                "value stranded far from the raw values it comes from)."
            ),
            3: (
                "Order is workable but not optimized -- related columns "
                "are split apart, or the most identifying/important "
                "column isn't prioritized toward the stub."
            ),
            5: (
                "Left-to-right order reads naturally for the story -- "
                "related columns adjacent, most important/identifying "
                "info first -- as sensible as the ground truth's order."
            ),
        },
    },
    "color_theme_quality": {
        "title": "Color theme / palette taste",
        "assesses": (
            "Beyond whether the color ENCODING is correct (sequential vs. "
            "diverging matching the data's shape -- that is checked "
            "deterministically elsewhere and is NOT your job here), is "
            "the SPECIFIC hue/palette choice tasteful and harmonious with "
            "the rest of the table?"
        ),
        "anchors": {
            1: (
                "Palette clashes (hues fighting for attention, or colors "
                "that don't harmonize with the heading band/stub tint), "
                "or is a jarring/unreadable choice for the story."
            ),
            3: (
                "Palette is legible and acceptable but generic/uninspired, "
                "or only partially harmonizes with the rest of the "
                "table's chrome."
            ),
            5: (
                "Hue choice is tasteful, harmonious with the table's "
                "other chrome, and well-suited to the story (e.g. a "
                "diverging palette whose two hues carry sensible "
                "connotations for the sign) -- as tasteful as the ground "
                "truth's own choice."
            ),
        },
    },
}

DIMENSION_KEYS: tuple[str, ...] = tuple(DIMENSIONS)

# The tool name the model must call exactly once to submit its judgment --
# forcing structured output via ``tool_choice`` rather than parsing free text
# (see runner.judge). Not a new dependency: this is a plain hand-written
# dict matching Anthropic's tool-use ``input_schema`` contract (required by
# the Messages API itself, JSON-Schema-*shaped* but not the ``jsonschema``
# package) -- the response is still validated by hand in ``runner.judge``,
# never by a schema library.
TOOL_NAME = "submit_table_judgment"


def _render_rubric_section() -> str:
    lines: list[str] = []
    for i, (key, spec) in enumerate(DIMENSIONS.items(), 1):
        lines.append(f"{i}. `{key}` -- {spec['title']}")
        lines.append(f"   Assesses: {spec['assesses']}")
        for score in (1, 3, 5):
            lines.append(f"   - {score}: {spec['anchors'][score]}")
        lines.append("")
    return "\n".join(lines)


SYSTEM_PROMPT = f"""\
You are an evaluator for a great_tables-based table-generation harness. You \
score a CANDIDATE table's rendered PNG against its GROUND TRUTH's rendered \
PNG for the same natural-language prompt and the same source data. You do \
not generate tables, suggest code, or hold a conversation -- you score \
exactly 6 named dimensions and submit them via the `{TOOL_NAME}` tool.

## What the ground truth is

The ground truth is NOT an abstract platonic ideal -- it is simply one \
concrete example of a good answer to this exact prompt. Score the \
candidate on its own merits relative to it, never for matching it \
verbatim. Wording, column order, and specific hue choices only need to be \
EQUALLY SENSIBLE, not identical.

## Image tiling

A very tall rendered table may arrive as multiple sequential images \
instead of one, each labeled "part i of N (top-to-bottom, same table)", so \
that small text (labels, titles, captions) stays legible instead of being \
downscaled past readability. Treat every tile under the same GROUND TRUTH \
or CANDIDATE label as ONE continuous table read top-to-bottom -- never as \
separate tables, and never penalize a dimension just because evidence for \
it happens to sit in a later tile.

## The 6 dimensions

{_render_rubric_section()}
## Applicability -- self-report, don't dodge

Most dimensions apply to every comparison. Three specific rules:

- `grouping_choice_quality` is applicable ONLY when the ground truth's own \
rendering visibly uses row grouping AND the provided REQUIRED_INSTRUCTIONS \
metadata has no `"grouping"` key. If REQUIRED_INSTRUCTIONS has a \
`"grouping"` key, grouping is a mandated instruction already checked by a \
separate deterministic mechanism elsewhere in the harness -- self-report \
`applicable=false` with a rationale saying so. If the ground truth does \
not group at all, this is not a discretionary editorial choice being \
tested here either -- self-report `applicable=false`.
- For every OTHER dimension, self-report `applicable=false` only when the \
dimension genuinely cannot be assessed from what's rendered (e.g. there is \
no caption/source-note region on EITHER table at all, so caption quality \
has nothing to compare). Do not use `applicable=false` to avoid a hard \
call -- when in doubt, score it.
- Applicability filtering for what a SPECIFIC ground truth requires, \
beyond the grouping rule above, is handled elsewhere in the harness, not \
by you.

## Rationale requirement

Every rationale (applicable or not) must be 1-3 sentences and cite \
something concrete visible in the images or stated in the prompt/metadata \
-- a specific label, a specific hue, a specific phrase. No vibes-only \
rationales.

## Grounding metadata

You will be given: the original user prompt, and grounding metadata read \
from the ground truth's own answer key (LABEL_SYNONYMS, \
REQUIRED_INSTRUCTIONS, CAPTION_KEYWORDS, CANONICAL_MEASURES, \
SEMANTIC_TYPES). Except for the REQUIRED_INSTRUCTIONS `"grouping"` rule \
above, treat this metadata as OPTIONAL grounding context, never a hard \
gate -- a reasonable choice the metadata doesn't happen to mention can \
still score a 5.

## Output

Call `{TOOL_NAME}` exactly once with all 6 keys above present, no other \
top-level keys. For each: `applicable` (boolean), `score` (integer 1-5 \
when applicable, `null` when not), `rationale` (string, always present). \
Never invent a score for a dimension you marked inapplicable.
"""


def build_tool_schema() -> dict:
    """The Anthropic tool-use schema forcing one single structured call.

    ``strict: True`` (Codex round-1 finding) grammar-constrains the model's
    tool call to this exact schema -- without it, a syntactically valid API
    response could still omit a dimension or return ``score`` as a string
    (``"5"``), which made ``_validate_and_build()`` reject the WHOLE payload
    even though the call itself succeeded. Strict mode requires
    ``additionalProperties: False`` on every object level (added below, both
    the outer schema and each per-dimension schema) and drops a few
    constraint keywords it doesn't support -- notably ``minimum``/
    ``maximum`` on numbers, per Anthropic's structured-outputs docs, which
    silently strips them rather than erroring. ``score``'s 1-5 numeric range
    is therefore NOT schema-enforced (the description still states it, as a
    hint) -- ``runner.judge._validate_and_build()`` remains the actual
    enforcement of that range, exactly as before; strict mode only closes
    the "wrong type or missing key" gap, not the numeric-range one. See the
    ``TOOL_NAME`` docstring note above re: this not being a
    ``jsonschema``-package dependency.
    """
    dimension_schema = {
        "type": "object",
        "properties": {
            "applicable": {
                "type": "boolean",
                "description": "Whether this dimension applies to this comparison at all.",
            },
            "score": {
                # anyOf (not a `type` array) -- the documented, definitely-
                # supported way to express "integer or null" under strict
                # mode. `minimum`/`maximum` deliberately omitted: unsupported
                # under strict mode (silently stripped), so keeping them
                # would be misleading dead weight; the 1-5 range is instead
                # enforced in Python by _validate_and_build().
                "anyOf": [{"type": "integer"}, {"type": "null"}],
                "description": "1-5 when applicable is true; null when applicable is false.",
            },
            "rationale": {
                "type": "string",
                "description": "1-3 sentences citing something concrete.",
            },
        },
        "required": ["applicable", "score", "rationale"],
        "additionalProperties": False,
    }
    return {
        "name": TOOL_NAME,
        "description": (
            "Submit your scores for all 6 rubric dimensions comparing the "
            "candidate table image to the ground-truth table image."
        ),
        "input_schema": {
            "type": "object",
            "properties": {key: dimension_schema for key in DIMENSION_KEYS},
            "required": list(DIMENSION_KEYS),
            "additionalProperties": False,
        },
        "strict": True,
    }
