#!/usr/bin/env python3
"""gt_check.py — a standalone CI style-checker for great-tables ``table.py`` files.

USAGE
-----
    python gt_check.py table.py [--json]

This is a **CI checker, not a helper library.** It is never imported by
``table.py``; the model runs it as a subcommand after writing a table and
iterates on ``table.py`` until every check passes (the "demonstrated-need"
enforcement loop described in ``.planning/CONSISTENCY_FAILURES.md`` R3).

It enforces only the **prompt-independent** style rules the flowchart pins
down (it never sees the user's prompt, so it cannot judge instruction-following
choices such as which columns to show or how to group rows). Each rule maps to
the one focused reference file that documents the fix, so a failing check tells
the model exactly which reference to open.

HOW IT INSPECTS A TABLE
-----------------------
Two independent views, so a failure in one never blinds the other:

1. **Rendered DOM.** It ``exec``s ``table.py`` in a fresh namespace and reads the
   final table from a module-level ``gt`` variable (a convention the scripted
   SKILL.md states). ``table.py`` normally ends with ``gt.gtsave("table.png")``,
   which renders via Chrome; before exec we monkeypatch ``great_tables.GT.gtsave``
   to a no-op that *records* its kwargs (so render-param checks still work) and
   stub ``gtskill_chrome`` so an ``import gtskill_chrome`` line cannot fail. From
   ``gt`` we call ``gt.as_raw_html()`` for the DOM.
2. **Raw source.** It reads ``table.py`` as text and parses it with regex
   (balanced-paren argument scans, mirroring ``consistency_runner.py``).

Every source-level check runs unconditionally. DOM-level checks degrade
gracefully: if exec or ``as_raw_html`` fails, the failure is reported as its own
finding and the source-only checks still run.

OUTPUT CONTRACT
---------------
A loud single-line banner (``===== gt_check: PASS =====`` /
``===== gt_check: FAIL (<n> issue(s)) =====``), then one line per violation:

    [rule-id] <what you missed> — expected: <what's expected> — read references/<file>

Exit code is 0 when there are no FAIL-level findings, 1 otherwise. INFO-level
notes print but never change the exit code. ``--json`` additionally dumps a
machine-readable summary to stdout.

No dependencies beyond the standard library plus (optionally) ``great_tables``,
which is only needed to exec the target file for the DOM checks.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
import traceback
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

# --------------------------------------------------------------------------- #
# Palette constants — mirror references/palettes.md (via scripts/gt_consistency.py)
# --------------------------------------------------------------------------- #
# §1 Dark Academia SOLID Big-Color palette (dark saturated bands, fills, etc.).
SOLID: dict[str, str] = {
    "navy": "#22384F",
    "forest": "#2F4A38",
    "oxblood": "#5C2E2E",
    "espresso": "#4A3A2C",
    "ochre": "#9A7B33",
    "tan": "#8A7452",
}
# §1 washed light tints paired with each solid (light heading bands, stub tints).
WASHED: dict[str, str] = {
    "navy": "#EAF0F6",
    "forest": "#EAF1EC",
    "oxblood": "#F5EBEB",
    "espresso": "#F1EADD",
    "ochre": "#F5EFDC",
    "tan": "#EFE7D6",
}
# §2 neutral structural greys.
NEUTRAL: dict[str, str] = {
    "label_band": "#F0F0F0",
    "row_stripe": "#F6F6F6",
    "hairline": "#E8E8E8",
    "column_label_rule": "#CCCCCC",
    "structural_rule": "#BDBDBD",
    "vertical_divider": "#D0D0D0",
    "na_cell": "#808080",
}
# §3 palette NAMES (matplotlib/brewer) passed to data_color(palette=...).
DIVERGING_NAMES: set[str] = {
    "RdYlGn", "RdBu", "PuOr", "RdGy", "BrBG", "PiYG", "PRGn", "Spectral",
    "coolwarm", "bwr", "seismic",
}
SEQUENTIAL_NAMES: set[str] = {
    "Greens", "Reds", "Oranges", "Blues", "Purples", "Greys",
    "YlGnBu", "YlOrRd", "viridis", "magma", "plasma", "inferno", "cividis",
}
# §0 Branding tier — the FIXED, universal header/stub/stripe surface every
# table now uses (2026-08-12 ground-truth redesign), independent of any
# per-measure heatmap hue. ``stub_tint`` already equals ``WASHED["navy"]``
# and ``stripe`` already equals ``NEUTRAL["row_stripe"]`` — both are listed
# again here under their branding role for clarity; ``header`` (#08306B) is
# a value no other tier carries.
BRANDING: dict[str, str] = {
    "header": "#08306B",
    "stub_tint": WASHED["navy"],
    "stripe": NEUTRAL["row_stripe"],
}

# The complete allowed hex set for a heading band (case-insensitive membership).
ALL_PALETTE_HEXES: set[str] = {
    h.upper()
    for h in (*SOLID.values(), *WASHED.values(), *NEUTRAL.values(), *BRANDING.values())
}
# Solid (dark) hexes — a legitimate no-Big-Color anchor band comes from here.
SOLID_HEXES: set[str] = {h.upper() for h in SOLID.values()}

# --------------------------------------------------------------------------- #
# Rule id -> the reference file that documents its fix (drives the output line).
# --------------------------------------------------------------------------- #
RULE_REFS: dict[str, str] = {
    "palette-signedness": "big_color/diverging_fill.md",
    "domain-symmetry": "big_color/diverging_fill.md",
    "domain-present": "big_color/column_gradient_fill.md",
    "frame-missing": "small_color.md",
    "hairlines-missing": "small_color.md",
    "heading-band": "palettes.md",
    "render-params": "small_color.md",
    "striping-gate": "small_color.md",
    "stub-tint": "small_color.md",
    "stripe-color": "small_color.md",
    "force-sign": "small_color.md",
    "hero-not-bold": "small_color.md",
    "layout-advisory": "small_color.md",
    "orphan-stub": "small_color.md",
    "opt-stylize-banned": "small_color.md",
    "formatting": "small_color.md",
    # Meta findings (exec / dom / internal-error).
    "gt-missing": "small_color.md",
    "exec-error": "small_color.md",
    "dom-error": "small_color.md",
    "check-error": "small_color.md",
}

FAIL = "FAIL"
INFO = "INFO"

# --------------------------------------------------------------------------- #
# Readable reference paths. ``gt_check.py`` is invoked from the run cwd via
# its full path under ``.claude/skills/great-tables-ci/scripts/`` (no symlink
# into the run cwd anymore), so a bare ``references/<file>`` would not
# resolve. Resolve the checker's real location (``Path(__file__).resolve()``)
# and use its sibling ``../references/`` as the printable reference root.
# --------------------------------------------------------------------------- #
_REFERENCES_DIR = Path(__file__).resolve().parent.parent / "references"


def _reference_display(ref: str) -> str:
    """Return an openable path for reference file ``ref``.

    Prefers the absolute path next to the (symlink-resolved) checker if it
    exists on disk; falls back to the plain ``references/<file>`` token so the
    output is never empty even if the layout changes."""
    candidate = _REFERENCES_DIR / ref
    try:
        if candidate.exists():
            return str(candidate)
    except OSError:  # pragma: no cover - defensive
        pass
    return f"references/{ref}"


@dataclass
class Finding:
    """One check result. ``level`` is ``FAIL`` (fails the run) or ``INFO`` (note)."""

    rule_id: str
    level: str
    missed: str        # what you missed
    expected: str      # what's expected
    ref: str = field(default="")

    def __post_init__(self) -> None:
        if not self.ref:
            self.ref = RULE_REFS.get(self.rule_id, "palettes.md")

    def line(self) -> str:
        """The human-readable one-line form for the report."""
        tag = "" if self.level == FAIL else " (info)"
        return (
            f"  [{self.rule_id}]{tag} {self.missed} "
            f"— expected: {self.expected} — read {_reference_display(self.ref)}"
        )

    def as_dict(self) -> dict[str, str]:
        return {
            "rule_id": self.rule_id,
            "level": self.level,
            "missed": self.missed,
            "expected": self.expected,
            "reference": f"references/{self.ref}",
            "reference_path": _reference_display(self.ref),
        }


# --------------------------------------------------------------------------- #
# Small pure helpers (colour maths + source parsing) — parsing ideas mirror
# consistency_runner.py's _call_arg_blocks / _find_band_color / _band_shade /
# _classify_hue / _extract_palettes.
# --------------------------------------------------------------------------- #
def _clean_source(source: str) -> str:
    """Return ``source`` with comments and docstrings removed.

    All source-level regex checks run on this cleaned text so that prose in a
    ``# comment`` or a module/function docstring cannot masquerade as code (e.g.
    the word "frame(" in a docstring must not satisfy the frame check, and a hex
    named in a docstring must not inflate the Big-Color heuristic). The actual
    *string values* used in calls (hexes, palette names, domain literals) are
    preserved, since they are not docstrings. Falls back to the raw source if the
    file cannot be parsed (a syntactically broken file still gets regex checks)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            continue
        body = getattr(node, "body", [])
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            remaining = body[1:]
            # A function/class body cannot be empty — keep it valid.
            if not remaining and not isinstance(node, ast.Module):
                remaining = [ast.Pass()]
            node.body = remaining
    try:
        return ast.unparse(tree)
    except Exception:  # pragma: no cover - defensive
        return source


def _hex_to_rgb(hexstr: str) -> Optional[tuple[int, int, int]]:
    """Parse ``#rgb`` / ``#rrggbb`` to an (r, g, b) tuple, else ``None``."""
    if not hexstr:
        return None
    h = hexstr.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return None
    try:
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
    except ValueError:
        return None


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    """Perceptual luminance on 0..1 (Rec. 709 coefficients)."""
    r, g, b = rgb
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def _band_shade(hexstr: str) -> str:
    """Classify a band hex as ``'light'`` / ``'dark'`` / ``'unknown'`` by luminance."""
    rgb = _hex_to_rgb(hexstr)
    if rgb is None:
        return "unknown"
    return "dark" if _relative_luminance(rgb) < 0.5 else "light"


def _call_arg_blocks(source: str, func: str, *, dotted: bool = True) -> list[str]:
    """Return the argument text of every ``func(...)`` call in ``source``.

    A balanced-paren scan, so nested calls / list literals inside the args
    (e.g. ``domain=[df[...].min(), ...]``) are handled. ``dotted=True`` matches
    method calls (``.func(``); ``dotted=False`` matches bare calls (``func(``),
    used for the ``GT(...)`` constructor.
    """
    blocks: list[str] = []
    pattern = rf"\.{re.escape(func)}\s*\(" if dotted else rf"\b{re.escape(func)}\s*\("
    for m in re.finditer(pattern, source):
        open_idx = m.end() - 1
        depth = 0
        for j in range(open_idx, len(source)):
            c = source[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    blocks.append(source[open_idx + 1 : j])
                    break
    return blocks


def _find_band_color(source: str) -> Optional[str]:
    """The heading-band background hex, if the script sets one.

    Prefers the column-labels band (Step-4's "heading band"); falls back to the
    title/subtitle heading band. Only explicit ``tab_options(...)`` hexes are
    detected (the mechanism the skill prescribes)."""
    for key in ("column_labels_background_color", "heading_background_color"):
        m = re.search(rf"{key}\s*=\s*['\"]([^'\"]+)['\"]", source)
        if m:
            return m.group(1)
    return None


def _band_hex_from_helper(source: str) -> Optional[str]:
    """The band background hex a ``band(...)`` helper call would apply.

    2026-08-12 redesign: ``gt_consistency.band()`` now always paints the
    fixed branding hex regardless of any ``shade``/``hue`` it's called with
    (the header no longer follows a per-measure heatmap hue — see
    ``check_heading_band``), so any recognised ``band(...)`` call resolves to
    that one constant."""
    if _call_arg_blocks(source, "band", dotted=False):
        return BRANDING["header"]
    return None


def _palette_name(block: str) -> str:
    """The palette of one ``data_color`` arg block: a name, ``'custom'`` (list
    literal) or ``'default'`` (no palette arg)."""
    m = re.search(r"palette\s*=\s*(\[[^\]]*\]|['\"]([^'\"]+)['\"])", block)
    if not m:
        return "default"
    if m.group(2):
        return m.group(2)
    return "custom"


def _columns_arg(block: str) -> str:
    """A normalised string of the ``columns=`` argument of a call block.

    Used only to de-duplicate ``data_color`` calls that target the same columns
    (so two calls on the same columns count as one measure). Falls back to the
    whole block when no explicit ``columns=`` is present."""
    m = re.search(r"columns\s*=\s*(\[[^\]]*\]|\([^)]*\)|['\"][^'\"]+['\"])", block)
    raw = m.group(1) if m else block
    return re.sub(r"\s+", "", raw)


def _extract_domain(block: str) -> tuple[str, Optional[tuple[float, float]]]:
    """Parse ``domain=`` from a ``data_color`` arg block.

    Returns ``(status, bounds)`` where status is one of:
      * ``"missing"`` — no ``domain=`` (or ``domain=None``),
      * ``"literal"`` — two numeric literals parsed → ``bounds`` is ``(a, b)``,
      * ``"unknown"`` — a ``domain=`` that is a data expression (e.g.
        ``[df['x'].min(), df['x'].max()]``) we cannot evaluate statically.
    """
    m = re.search(r"domain\s*=\s*", block)
    if not m:
        return ("missing", None)
    i = m.end()
    if i >= len(block):
        return ("missing", None)
    open_ch = block[i]
    close_ch = {"[": "]", "(": ")"}.get(open_ch)
    if close_ch is None:
        # Scalar form, e.g. domain=None or domain=some_var.
        tok_match = re.match(r"[^,)]+", block[i:])
        tok = tok_match.group(0).strip() if tok_match else ""
        if tok.lower() in ("", "none"):
            return ("missing", None)
        return ("unknown", None)
    # Balanced scan for the matching close bracket.
    depth = 0
    j = i
    while j < len(block):
        c = block[j]
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                break
        j += 1
    content = block[i + 1 : j]
    # Standalone numeric literals only — a token inside df['x'] or .min() is
    # skipped. Accepts scientific/exponent notation (e.g. -1e3, 1.5E-3) so a
    # domain=[-1e3, 2e3] is parsed instead of falling through to "unknown".
    nums = re.findall(
        r"(?<![\w.'\"])[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?(?![\w'\"])", content
    )
    if len(nums) == 2:
        return ("literal", (float(nums[0]), float(nums[1])))
    return ("unknown", None)


@dataclass
class ColorCall:
    """One parsed value-coloring call — a literal ``data_color(...)`` or a
    ``heatmap(...)`` helper call (both apply per-value fills)."""

    columns: str
    palette: str
    domain_status: str
    domain: Optional[tuple[float, float]]
    source_kind: str = "data_color"        # "data_color" | "heatmap"
    diverging: Optional[bool] = None        # set for heatmap (kind=); None => infer

    @property
    def is_diverging(self) -> bool:
        if self.diverging is not None:
            return self.diverging
        return self.palette in DIVERGING_NAMES


def _split_top_args(block: str) -> list[str]:
    """Split a call's argument text on top-level commas (depth- and quote-aware)."""
    args: list[str] = []
    cur: list[str] = []
    depth = 0
    quote: Optional[str] = None
    for ch in block:
        if quote is not None:
            cur.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            cur.append(ch)
        elif ch in "([{":
            depth += 1
            cur.append(ch)
        elif ch in ")]}":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            args.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    tail = "".join(cur)
    if tail.strip():
        args.append(tail)
    return [a.strip() for a in args]


def _heatmap_columns(block: str) -> str:
    """The normalised ``columns`` argument of a ``heatmap(gt, columns, ...)`` call.

    Accepts either the keyword form (``columns=...``) or the second positional
    argument (the first positional is the ``gt`` object)."""
    args = _split_top_args(block)
    for a in args:
        if re.match(r"columns\s*=", a):
            return re.sub(r"\s+", "", a.split("=", 1)[1])
    positional = [a for a in args if not re.match(r"[A-Za-z_]\w*\s*=", a)]
    if len(positional) >= 2:
        return re.sub(r"\s+", "", positional[1])
    return re.sub(r"\s+", "", block)


def _parse_color_calls(source: str) -> list[ColorCall]:
    """Every value-coloring call — ``data_color(...)`` and ``heatmap(...)`` — as
    a ``ColorCall``.

    Recognising ``heatmap(...)`` at source level is what lets the argument-driven
    checks (signedness / domain) read intent on the helper path, where no literal
    ``data_color(`` token exists."""
    calls: list[ColorCall] = []
    for block in _call_arg_blocks(source, "data_color"):
        status, bounds = _extract_domain(block)
        calls.append(
            ColorCall(
                columns=_columns_arg(block),
                palette=_palette_name(block),
                domain_status=status,
                domain=bounds,
                source_kind="data_color",
            )
        )
    # heatmap(gt, columns, *, kind, hue, domain=None) — a diverging/sequential
    # fill applied at runtime. A computed (absent/None) domain is NOT the
    # data_color "missing domain" problem: the helper derives a full/symmetric
    # domain from the data, so only an EXPLICIT literal domain is check-worthy.
    for block in _call_arg_blocks(source, "heatmap", dotted=False):
        status, bounds = _extract_domain(block)
        kind_m = re.search(r"kind\s*=\s*['\"]([^'\"]+)['\"]", block)
        hue_m = re.search(r"hue\s*=\s*['\"]([^'\"]+)['\"]", block)
        kind = kind_m.group(1) if kind_m else ""
        hue = hue_m.group(1) if hue_m else ""
        diverging = kind == "diverging"
        palette_label = f"{kind or 'heatmap'} palette (hue={hue or '?'})"
        calls.append(
            ColorCall(
                columns=_heatmap_columns(block),
                palette=palette_label,
                domain_status=status,
                domain=bounds,
                source_kind="heatmap",
                diverging=diverging,
            )
        )
    return calls


def _has_big_color(source: str, band_hex: Optional[str]) -> bool:
    """Heuristic: does the table use any Big Color (fills / colored text)?

    True if there is any ``data_color`` call, or a Dark-Academia *solid* hex is
    used somewhere other than (only) the dark heading band. The dark band itself
    is the no-Big-Color anchor, so a solid that appears solely as the band value
    does not count as Big Color."""
    if _call_arg_blocks(source, "data_color"):
        return True
    band_upper = band_hex.upper() if band_hex else None
    for hexv in SOLID_HEXES:
        occurrences = len(re.findall(re.escape(hexv), source, re.IGNORECASE))
        if occurrences == 0:
            continue
        # If the only occurrence is the band value, it is the dark anchor band.
        if band_upper == hexv and occurrences <= 1:
            continue
        return True
    return False


# --------------------------------------------------------------------------- #
# DOM helpers
# --------------------------------------------------------------------------- #
def _dom_tbody(dom: str) -> str:
    """The ``<tbody>...</tbody>`` slice of the DOM, or ``''`` if absent."""
    m = re.search(r"<tbody\b.*?</tbody>", dom, re.DOTALL | re.IGNORECASE)
    return m.group(0) if m else ""


def _dom_body_rows(dom: str) -> int:
    """Count data body rows (``<tr>`` carrying the ``gt_row`` class), excluding
    group-heading / summary rows."""
    body = _dom_tbody(dom)
    if not body:
        return 0
    rows = re.findall(r"<tr\b.*?</tr>", body, re.DOTALL | re.IGNORECASE)
    return sum(1 for r in rows if "gt_row" in r)


def _dom_fill_fraction(dom: str) -> float:
    """Fraction of body ``<td>`` data cells carrying an inline ``background-color``.

    A proxy for "the body is essentially fully filled by data_color". Stub cells
    are ``<th>`` and are ignored. Returns 0.0 when there are no ``<td>`` cells."""
    body = _dom_tbody(dom)
    if not body:
        return 0.0
    cells = re.findall(r"<td\b[^>]*>", body, re.IGNORECASE)
    if not cells:
        return 0.0
    filled = sum(1 for c in cells if "background-color" in c.lower())
    return filled / len(cells)


def _dom_colored_columns(dom: Optional[str]) -> int:
    """Number of distinct body columns whose ``<td>`` cells carry an inline
    ``background-color`` (a helper-agnostic count of colored measures).

    Position within a row identifies the column (stub cells are ``<th>`` and do
    not shift the ``<td>`` index). Row striping paints via the ``gt_striped``
    CSS *class*, not an inline style, so stripes are never miscounted as fills."""
    body = _dom_tbody(dom or "")
    if not body:
        return 0
    colored: set[int] = set()
    for row in re.findall(r"<tr\b.*?</tr>", body, re.DOTALL | re.IGNORECASE):
        if "gt_row" not in row:
            continue
        for idx, cell in enumerate(re.findall(r"<td\b[^>]*>", row, re.IGNORECASE)):
            if "background-color" in cell.lower():
                colored.add(idx)
    return len(colored)


def _dom_has_colored_body(dom: Optional[str]) -> bool:
    """True if any body data cell carries an inline ``background-color`` (a
    DOM-level Big-Color signal, independent of how the fill was applied)."""
    return _dom_colored_columns(dom) > 0


def _dom_col_heading_bg(dom: Optional[str]) -> Optional[str]:
    """The rendered column-label band background hex, or ``None`` for the default.

    ``tab_options(column_labels_background_color=...)`` — whether typed directly
    or applied by ``band()`` — compiles to the ``.gt_col_heading`` CSS rule. A
    default (unbanded) heading is white, which is reported as no band."""
    if not dom:
        return None
    m = re.search(r"\.gt_col_heading\s*\{([^}]*)\}", dom)
    if not m:
        return None
    bg = re.search(r"background-color:\s*([^;]+);", m.group(1))
    if not bg:
        return None
    hexv = bg.group(1).strip()
    if hexv.upper() in ("#FFFFFF", "#FFF", "WHITE", "TRANSPARENT"):
        return None
    return hexv


def _dom_col_heading_text_white(dom: Optional[str]) -> bool:
    """True if the column labels render with white text.

    ``band(shade='dark')`` applies this via ``tab_style(style.text(color='white'),
    loc.column_labels())``; Great Tables also auto-contrasts label text to white
    on a dark band. An inline ``color`` on the heading ``<th>`` cells overrides
    the ``.gt_col_heading`` CSS rule, so inline colors are authoritative when
    present (this catches a band that forces DARK text over the auto-white CSS);
    only when no heading cell sets an inline color do we read the CSS rule."""
    if not dom:
        return False
    color_re = re.compile(r"(?<!background-)color:\s*([^;]+)", re.I)

    def _is_white(val: str) -> bool:
        return val.strip().lower() in ("white", "#fff", "#ffffff")

    thead = re.search(r"<thead\b.*?</thead>", dom, re.DOTALL | re.IGNORECASE)
    inline_colors: list[str] = []
    if thead:
        for th in re.findall(r"<th\b[^>]*>", thead.group(0), re.IGNORECASE):
            if "gt_col_heading" not in th.lower():
                continue
            style_m = re.search(r"style\s*=\s*\"([^\"]*)\"", th, re.IGNORECASE)
            if not style_m:
                continue
            cm = color_re.search(style_m.group(1))
            if cm:
                inline_colors.append(cm.group(1))
    if inline_colors:
        # Inline overrides the class rule for the label cells that carry
        # one. A single label explicitly forced to a non-white color is a
        # FAIL regardless of how many other labels are correctly white
        # (whether via their own inline override or via the default
        # dark-band CSS) — so every EXPLICITLY-STYLED label must be white,
        # not merely at-least-one of them.
        return all(_is_white(c) for c in inline_colors)
    css = re.search(r"\.gt_col_heading\s*\{([^}]*)\}", dom)
    if css:
        cm = color_re.search(css.group(1))
        return bool(cm) and _is_white(cm.group(1))
    return False


def _dom_has_stripes(dom: Optional[str]) -> bool:
    """True if striping is actually rendered (body rows carry ``gt_striped``).

    The ``.gt_striped`` CSS rule is always emitted, so only its use as a *class*
    on ``<tbody>`` rows proves striping was enabled (via ``opt_row_striping()``
    or ``row_striping_include_table_body=True``)."""
    body = _dom_tbody(dom or "")
    return bool(body) and "gt_striped" in body


def _dom_stripe_color(dom: Optional[str]) -> Optional[str]:
    """The rendered row-stripe background hex, or ``None`` if unavailable.

    Unlike the heading band / stub (which default to a CSS rule that a
    literal option then overrides inline), ``row_striping_background_color``
    compiles straight into the ``.gt_striped`` CSS rule, so that rule is
    authoritative whether or not striping was ever explicitly colored."""
    if not dom:
        return None
    m = re.search(r"\.gt_striped\s*\{([^}]*)\}", dom, re.IGNORECASE)
    if not m:
        return None
    bg = re.search(r"background-color:\s*([^;]+);", m.group(1), re.IGNORECASE)
    return bg.group(1).strip() if bg else None


def _dom_col_heading_bold(dom: Optional[str]) -> bool:
    """True if the rendered column-label band renders bold text.

    Reads the compiled ``.gt_col_heading`` CSS rule's ``font-weight`` (the
    only mechanism ``column_labels_font_weight=`` compiles to — there is no
    inline per-cell override for this option, unlike the band background or
    text color)."""
    if not dom:
        return False
    m = re.search(r"\.gt_col_heading\s*\{([^}]*)\}", dom)
    if not m:
        return False
    fw = re.search(r"font-weight:\s*([^;]+);", m.group(1))
    if not fw:
        return False
    return fw.group(1).strip().lower() in ("bold", "bolder", "700", "800", "900")


def _dom_stub_present(dom: Optional[str]) -> bool:
    """True if the rendered DOM has a stub column (a ``<th ... gt_stub ...>``
    cell in the body)."""
    return bool(dom) and bool(re.search(r"<th\b[^>]*\bgt_stub\b[^>]*>", dom, re.IGNORECASE))


def _dom_stub_non_default_bg(css_text: str) -> Optional[str]:
    """Parse a ``background-color:`` declaration out of one CSS/inline-style
    block, treating white/transparent as "no fill" (the default)."""
    bg = re.search(r"background-color:\s*([^;]+);", css_text, re.IGNORECASE)
    if not bg:
        return None
    hexv = bg.group(1).strip()
    if hexv.upper() in ("#FFFFFF", "#FFF", "WHITE", "TRANSPARENT"):
        return None
    return hexv


def _dom_stub_fills(dom: Optional[str]) -> list[Optional[str]]:
    """The effective background fill of EVERY stub ``<th>`` cell in the
    document, in document order.

    Two distinct mechanisms tint the stub, and each compiles differently:
    ``tab_style(style.fill(...), locations=loc.stub())`` applies an INLINE
    ``background-color`` on the stub ``<th>`` (overriding the ``.gt_stub``
    CSS rule) — and, critically, can target a SUBSET of rows (e.g.
    ``loc.stub(rows=[0])``), so only some cells get the inline override;
    ``stub_background_color=`` (a ``tab_options`` global option — what
    ``gt_consistency.stub_tint()`` itself uses) compiles straight into the
    ``.gt_stub`` CSS rule instead, with NO inline style at all, and therefore
    applies uniformly to every stub cell. For each cell: inline wins when
    present (same inline-overrides-class pattern the column-label band
    uses); otherwise the CSS rule is read, ignoring its own white default.
    Every cell must be checked individually — reading only the first cell
    would let a partially-tinted stub (only some rows tinted) pass.

    Grand-summary-row and per-group-summary-row label cells also carry the
    ``gt_stub`` class (alongside ``gt_grand_summary_row`` / ``gt_summary_row``
    — great_tables emits variants like ``gt_first_grand_summary_row_bottom``
    too, always containing ``summary_row``), but ``loc.stub()`` can never
    target them — it only reaches regular body-row stub cells. Excluding
    them here keeps a correctly, uniformly tinted body stub from being
    flagged as non-uniform just because a totals row's deliberately-untinted
    label cell doesn't match."""
    if not dom:
        return []
    tags = re.findall(r"<th\b[^>]*\bgt_stub\b[^>]*>", dom, re.IGNORECASE)
    tags = [t for t in tags if "summary_row" not in t.lower()]
    if not tags:
        return []

    css_m = re.search(r"\.gt_stub\s*\{([^}]*)\}", dom)
    class_fill = _dom_stub_non_default_bg(css_m.group(1)) if css_m else None

    fills: list[Optional[str]] = []
    for tag in tags:
        style_m = re.search(r'style\s*=\s*"([^"]*)"', tag, re.IGNORECASE)
        inline = _dom_stub_non_default_bg(style_m.group(1)) if style_m else None
        fills.append(inline if inline is not None else class_fill)
    return fills


def _dom_frame_ok(dom: Optional[str]) -> Optional[bool]:
    """Whether the table renders visible LEFT and RIGHT side borders.

    Reads the compiled ``.gt_table`` CSS rule. Great Tables defaults the side
    border style to ``none``; ``frame()`` / ``opt_table_outline()`` / genuine
    per-side style options set it to a visible style. Returns ``None`` when the
    rule cannot be found so the caller can fall back to source parsing."""
    if not dom:
        return None
    m = re.search(r"\.gt_table\s*\{([^}]*)\}", dom)
    if not m:
        return None
    css = m.group(1)
    for side in ("left", "right"):
        s = re.search(rf"border-{side}-style:\s*([^;]+);", css)
        if s is None or s.group(1).strip().lower() in ("none", "hidden"):
            return False
    return True


# --------------------------------------------------------------------------- #
# exec the target table.py and capture (gt, dom, gtsave kwargs)
# --------------------------------------------------------------------------- #
@dataclass
class ExecResult:
    """Everything the DOM-side checks need, plus any exec/DOM failures."""

    gt: Any = None
    dom: Optional[str] = None
    gtsave_kwargs: Optional[dict[str, Any]] = None
    exec_error: Optional[str] = None
    dom_error: Optional[str] = None


def run_table(path: Path) -> ExecResult:
    """Exec ``table.py`` in a fresh namespace and capture the ``gt`` table.

    Rendering is neutralised: ``great_tables.GT.gtsave`` is monkeypatched to a
    no-op that records its kwargs, and ``gtskill_chrome`` is stubbed so an
    ``import gtskill_chrome`` line can never fail. Exec runs with the working
    directory set to the file's directory so relative data paths resolve the way
    they would when the model runs the script. Any exec failure is captured (not
    raised); ``gt`` is still read from the partial namespace when possible."""
    result = ExecResult()
    recorded: dict[str, Any] = {}

    # Resolve up front: we chdir into the file's directory below, after which a
    # relative path would no longer resolve.
    path = path.resolve()

    # Environment guard (available to table.py if it wants to branch on it).
    os.environ.setdefault("GT_CHECK", "1")

    try:
        import great_tables  # noqa: WPS433  (lazy — only needed for DOM checks)
    except Exception as exc:  # great_tables missing → DOM checks unavailable.
        result.exec_error = f"could not import great_tables ({exc})"
        return result

    original_gtsave = great_tables.GT.gtsave

    def _stub_gtsave(self: Any, *args: Any, **kwargs: Any) -> Any:
        """Record kwargs and skip rendering (no Chrome)."""
        recorded.clear()
        recorded.update(kwargs)
        result.gtsave_kwargs = dict(kwargs)
        return self

    # Stub gtskill_chrome so `import gtskill_chrome` is always harmless.
    stub_chrome = types.ModuleType("gtskill_chrome")
    saved_chrome = sys.modules.get("gtskill_chrome")

    src_dir = path.parent.resolve()
    saved_cwd = os.getcwd()
    saved_syspath0 = list(sys.path)

    ns: dict[str, Any] = {"__name__": "__main__", "__file__": str(path.resolve())}

    try:
        great_tables.GT.gtsave = _stub_gtsave  # type: ignore[assignment]
        sys.modules["gtskill_chrome"] = stub_chrome
        sys.path.insert(0, str(src_dir))
        try:
            os.chdir(src_dir)
        except OSError:
            pass
        code = path.read_text(encoding="utf-8")
        try:
            exec(compile(code, str(path), "exec"), ns)  # noqa: S102 (intended)
        except Exception:
            # Table crashed at runtime. Capture it and still try to read `gt`
            # from whatever was bound before the exception.
            result.exec_error = traceback.format_exc(limit=4).strip()
    finally:
        great_tables.GT.gtsave = original_gtsave  # type: ignore[assignment]
        if saved_chrome is not None:
            sys.modules["gtskill_chrome"] = saved_chrome
        else:
            sys.modules.pop("gtskill_chrome", None)
        os.chdir(saved_cwd)
        sys.path[:] = saved_syspath0

    result.gt = ns.get("gt")

    # Render the DOM if we captured a table.
    if result.gt is not None:
        try:
            result.dom = result.gt.as_raw_html()
        except Exception as exc:
            result.dom_error = str(exc)

    return result


# --------------------------------------------------------------------------- #
# render-param source fallback (used when exec never reached gtsave)
# --------------------------------------------------------------------------- #
def _num_kwarg(block: str, name: str) -> Optional[float]:
    """Parse a numeric ``name=<number>`` kwarg from a call arg block."""
    m = re.search(rf"{name}\s*=\s*(-?\d+(?:\.\d+)?)", block)
    return float(m.group(1)) if m else None


def _render_from_source(source: str) -> Optional[dict[str, float]]:
    """Best-effort render kwargs parsed from the source when exec did not run.

    ``gtsave`` defaults: expand=5, zoom=2.0. The (now-retired) ``finalize``
    helper defaulted to expand=15, zoom=2.0."""
    for func, exp_default in (("gtsave", 5.0), ("finalize", 15.0)):
        blocks = _call_arg_blocks(source, func, dotted=(func == "gtsave"))
        if not blocks:
            # `finalize(gt, ...)` is a bare call, not dotted — try that too.
            blocks = _call_arg_blocks(source, func, dotted=False)
        if blocks:
            block = blocks[0]
            zoom = _num_kwarg(block, "zoom")
            expand = _num_kwarg(block, "expand")
            return {
                "zoom": 2.0 if zoom is None else zoom,
                "expand": exp_default if expand is None else expand,
            }
    return None


# --------------------------------------------------------------------------- #
# The rule checks. Each takes the parsed context and returns a list[Finding].
# --------------------------------------------------------------------------- #
def _colored_column_names(calls: list[ColorCall]) -> set[str]:
    """Flat set of column names targeted by any ``data_color``/``heatmap`` call.

    ``ColorCall.columns`` is a normalised (whitespace-stripped) source
    fragment like ``['msrp']`` or ``"msrp"``; this pulls the quoted names out
    of it. Used by ``check_hero_not_bold`` to tell a genuinely-colored column
    apart from an uncolored one."""
    names: set[str] = set()
    for c in calls:
        names.update(re.findall(r"['\"]([^'\"]+)['\"]", c.columns))
    return names


def check_palettes_and_domains(source: str, calls: list[ColorCall]) -> list[Finding]:
    """PP-4 (signedness), PP-6 (symmetry), PP-7 (domain present) across all
    ``data_color`` calls."""
    findings: list[Finding] = []
    for call in calls:
        # PP-7 — every literal data_color needs an explicit domain. A heatmap()
        # with a computed (absent/None) domain is exempt: the helper derives a
        # proper full/symmetric domain from the data, so it is not the
        # arbitrary-default problem PP-7 targets.
        if call.domain_status == "missing" and call.source_kind == "data_color":
            findings.append(
                Finding(
                    "domain-present",
                    FAIL,
                    f"data_color on columns={call.columns} has no explicit domain=",
                    "pass domain=[min, max] covering the full data range (truncate=False)",
                )
            )

        if not call.is_diverging:
            continue

        # Sign / symmetry checks need parseable literal bounds.
        if call.domain_status != "literal" or call.domain is None:
            continue
        a, b = call.domain
        spans_zero = a < 0 < b
        if not spans_zero:
            # PP-4 — diverging palette on data that is not signed.
            findings.append(
                Finding(
                    "palette-signedness",
                    FAIL,
                    (
                        f"diverging palette {call.palette!r} on unsigned data "
                        f"(domain=[{a:g}, {b:g}] does not straddle 0)"
                    ),
                    "use a sequential palette for an unsigned magnitude; reserve diverging for signed measures",
                )
            )
        else:
            # PP-6 — a signed diverging domain must be symmetric about 0.
            scale = max(abs(a), abs(b)) or 1.0
            if abs(a + b) > 0.15 * scale:
                m = max(abs(a), abs(b))
                findings.append(
                    Finding(
                        "domain-symmetry",
                        FAIL,
                        (
                            f"diverging palette {call.palette!r} has asymmetric "
                            f"domain=[{a:g}, {b:g}]"
                        ),
                        f"make the domain symmetric about 0, e.g. domain=[-{m:g}, {m:g}]",
                    )
                )
    return findings


def _frame_style_set(source: str, side: str) -> bool:
    """True if ``table_border_<side>_style`` is set to a visible (non-none) value.

    Great Tables defaults the side border *style* to ``none``, so setting only
    the color/width leaves the border invisible; a real box needs the style."""
    m = re.search(rf"table_border_{side}_style\s*=\s*['\"]([^'\"]+)['\"]", source)
    return bool(m) and m.group(1).strip().lower() not in ("none", "hidden")


def check_frame(source: str, exec_res: "ExecResult") -> list[Finding]:
    """PP-10: the mandatory enclosing boxed frame.

    When the DOM is available it is authoritative — the ``.gt_table`` rule must
    carry visible LEFT and RIGHT border styles (defaults are ``none``). Source
    parsing is the fallback: ``frame(gt)`` (the helper that sets all four border
    *styles*), ``opt_table_outline(...)``, or explicit left/right border *style*
    options. ``finalize(...)`` is NOT accepted — it only calls ``gtsave`` and
    adds no border. Setting only ``*_color`` / ``*_width`` is NOT accepted —
    without the style the side borders never render."""
    dom_ok = _dom_frame_ok(exec_res.dom)
    if dom_ok is True:
        return []

    has_outline = bool(re.search(r"opt_table_outline\s*\(", source))
    has_frame_helper = bool(re.search(r"\bframe\s*\(", source))
    has_side_border_styles = _frame_style_set(source, "left") and _frame_style_set(
        source, "right"
    )
    source_ok = has_outline or has_frame_helper or has_side_border_styles

    # If the DOM says the frame is missing, trust it even if a source token
    # looked present (e.g. an overridden/none style); otherwise honour source.
    if dom_ok is False:
        if has_outline or has_frame_helper or has_side_border_styles:
            # A recognised frame mechanism is present but did not render a visible
            # box — report the visible-style requirement rather than "missing".
            return [
                Finding(
                    "frame-missing",
                    FAIL,
                    "side borders do not render (left/right border-style is none)",
                    "set the LEFT and RIGHT border STYLE (frame() does this), not just color/width",
                )
            ]
        return [
            Finding(
                "frame-missing",
                FAIL,
                "no enclosing boxed frame",
                "add frame(gt) or opt_table_outline(); set left/right border STYLE, not just color/width",
            )
        ]

    # DOM unavailable — decide from source alone.
    if source_ok:
        return []
    return [
        Finding(
            "frame-missing",
            FAIL,
            "no enclosing boxed frame",
            "add frame(gt) or opt_table_outline(); set left/right border STYLE, not just color/width",
        )
    ]


def _walk_no_nested_defs(tree: ast.AST):
    """Like ``ast.walk``, but does not descend into a `def`/`class`'s own
    body -- a call trapped inside a never-invoked helper function (or dead
    code) doesn't count. Mirrors `runner/comparator.py`'s `_walk_top_level`
    bound (round-2 review finding: the first version of this file's checks
    used unrestricted `ast.walk`, so `hairlines(gt)` sitting in a function
    that's never called, or behind an `if True:`, PASSed here while the real
    comparator -- scoped to the exported call chain -- would still fail it)."""
    stack = [tree]
    while stack:
        node = stack.pop()
        yield node
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            stack.append(child)


def _is_call_named(node: ast.AST, name: str) -> bool:
    """True if ``node`` is a genuine `ast.Call` to a function/method literally
    named ``name`` -- excludes a `def name(...):`, a comment, or a docstring
    mention (none of those parse as an `ast.Call`)."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (isinstance(func, ast.Name) and func.id == name) or (
        isinstance(func, ast.Attribute) and func.attr == name
    )


def _is_zero_length(v: str) -> bool:
    """A CSS-style zero length (`"0px"`, `"0"`, `"0.0em"`, ...). Mirrors
    `runner/convergence.py`'s `_is_zero_length` verbatim."""
    return re.fullmatch(r"0+(\.0+)?(px|pt|em|rem|%)?", v.strip()) is not None


def _is_effectively_transparent(color: str) -> bool:
    """True if a CSS color literal renders with effectively zero opacity --
    `transparent`/`none`/empty, a zero-alpha `rgba(...)`, or a zero-alpha
    8-digit `#RRGGBBAA`/4-digit `#RGBA` hex. Mirrors
    `runner/comparator.py`'s `_is_effectively_transparent` verbatim --
    deliberately does NOT treat `#ffffff`/white as transparent (round-2
    review finding: an earlier version of this check did, false-failing a
    genuinely visible white hairline)."""
    c = color.strip()
    if c.lower() in ("transparent", "none", ""):
        return True
    m = re.fullmatch(r"rgba?\(\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*([\d.]+)\s*\)", c, re.I)
    if m:
        try:
            return float(m.group(1)) == 0.0
        except ValueError:
            return False
    if re.fullmatch(r"#[0-9A-Fa-f]{8}", c):
        return c[-2:].lower() == "00"
    if re.fullmatch(r"#[0-9A-Fa-f]{4}", c):
        return c[-1].lower() == "0"
    return False


def _hairlines_tab_options_ok(tree: ast.AST) -> Optional[bool]:
    """True/False if `table_body_hlines_style`/`_width`/`_color` (whichever
    appear as a LITERAL string, taking the last occurrence of each in SOURCE
    order across every real `tab_options(...)` call) together indicate a
    genuinely visible hairline; `None` if none of the three appear as a
    literal at all.

    Mirrors `runner/comparator.py`'s `_option_line_present` (same tolerance:
    a non-literal color expression like `PALETTE["neutral"]["hairline"]`
    cannot be resolved here and is treated as unset, not as a failure --
    `style`/`width` alone, if visible, are enough). Round-2 review finding:
    the first version iterated `ast.walk` order (breadth-first, NOT source
    order) for "last occurrence wins," so a later-in-source override could
    lose to an earlier call visited later in the traversal. Calls are now
    explicitly sorted by source position first."""
    calls = [
        node
        for node in _walk_no_nested_defs(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "tab_options"
    ]
    calls.sort(key=lambda n: (n.lineno, n.col_offset))
    style = width = color = None
    for node in calls:
        for kw in node.keywords:
            if not (isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str)):
                continue
            if kw.arg == "table_body_hlines_style":
                style = kw.value.value
            elif kw.arg == "table_body_hlines_width":
                width = kw.value.value
            elif kw.arg == "table_body_hlines_color":
                color = kw.value.value
    if style is None and width is None and color is None:
        return None
    if style is not None and style.strip().lower() in ("none", "hidden", ""):
        return False
    if width is not None and _is_zero_length(width):
        return False
    if color is not None and _is_effectively_transparent(color):
        return False
    return True


def check_hairlines(source: str) -> list[Finding]:
    """Step 5a: the body-row hairline must be pinned to the palette's neutral
    tone, not left at Great Tables' own raw default gray -- unconditional,
    every table gets it, same as ``check_frame`` above, and a genuinely
    different option family from that check (the outer table border vs. the
    rule BETWEEN body rows).

    AST-based (no DOM signal wired up yet, unlike ``check_frame`` above,
    which uses a source regex for its own no-DOM fallback): accepts either a
    genuine ``hairlines(gt)`` CALL (``_is_call_named``, immune to a candidate
    merely defining its own same-named function, or a comment/docstring
    mention), or an explicit ``table_body_hlines_*`` tab_options call
    indicating a visible line (``_hairlines_tab_options_ok`` -- does not
    require the color to be a literal hex; ``PALETTE["neutral"]["hairline"]``
    is the taught, expected form and is accepted like the comparator accepts
    it, via style/width alone). Both checks are scoped via
    ``_walk_no_nested_defs`` to exclude dead/never-called code, matching how
    the real comparator scopes its own equivalent checks.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []  # a broken file already gets its own exec-error finding elsewhere
    if any(_is_call_named(node, "hairlines") for node in _walk_no_nested_defs(tree)):
        return []
    if _hairlines_tab_options_ok(tree):
        return []
    return [
        Finding(
            "hairlines-missing",
            FAIL,
            "no body-row hairline pinned to the palette neutral hairline color",
            'call hairlines(gt) or set table_body_hlines_style/_color/_width via tab_options(...)',
        )
    ]


def check_heading_band(
    source: str,
    band_hex: Optional[str],
    exec_res: "ExecResult",
) -> list[Finding]:
    """Header branding (2026-08-12 redesign): every table gets the SAME fixed
    deep-navy band (``BRANDING["header"]``), bold column labels, and white
    label text — unconditionally, regardless of whether (or which) measure is
    colored. The old light-vs-dark-by-Big-Color branch is gone: branding
    surfaces always resolve to the standard navy family rather than following
    a heatmapped measure's own hue (every one of the 6 project ground truths
    uses the identical hex no matter what each one's own body heatmaps)."""
    if band_hex is None:
        return [
            Finding(
                "heading-band",
                FAIL,
                "no column_labels_background_color set",
                f"set the header band to the fixed branding hex {BRANDING['header']} "
                "(every table uses the same navy band, regardless of Big Color)",
            )
        ]

    if band_hex.strip().upper() != BRANDING["header"]:
        return [
            Finding(
                "heading-band",
                FAIL,
                f"band hex {band_hex} is not {BRANDING['header']}",
                f"use the fixed branding hex {BRANDING['header']} for every table's header band — "
                "it no longer follows a heatmapped measure's own hue",
            )
        ]

    if not _column_labels_bold(source, exec_res):
        return [
            Finding(
                "heading-band",
                FAIL,
                "header band present but column labels are not bold",
                "set column_labels_font_weight='bold' so the header text renders bold",
            )
        ]

    # A dark branding band needs WHITE column-label text for contrast. The
    # rendered DOM is authoritative whenever it exists (real output beats a
    # source-text guess about what a same-named `band(...)` call probably
    # did); source-text inference (an explicit white tab_style, or a
    # recognised band() helper call) is used ONLY when there is no DOM at all.
    if exec_res.dom is not None:
        white_text = _dom_col_heading_text_white(exec_res.dom)
    else:
        white_text = _source_white_column_labels(source) or bool(
            _call_arg_blocks(source, "band", dotted=False)
        )
    if not white_text:
        return [
            Finding(
                "heading-band",
                FAIL,
                f"band {band_hex} but column-label text is not white",
                "set white column-label text (tab_style(style.text(color='white'), "
                "loc.column_labels()))",
            )
        ]
    return []


def _source_white_column_labels(source: str) -> bool:
    """True if a ``tab_style(...)`` sets white text on the column labels."""
    for block in _call_arg_blocks(source, "tab_style"):
        if "column_labels" not in block:
            continue
        if re.search(
            r"color\s*=\s*['\"](?:white|#fff(?:fff)?)['\"]", block, re.IGNORECASE
        ):
            return True
    return False


def _find_column_labels_font_weight(source: str) -> Optional[str]:
    """The literal ``column_labels_font_weight=`` value, if set in source."""
    m = re.search(r"column_labels_font_weight\s*=\s*['\"]([^'\"]+)['\"]", source)
    return m.group(1) if m else None


def _column_labels_bold(source: str, exec_res: "ExecResult") -> bool:
    """True if column labels render bold.

    The rendered DOM's ``.gt_col_heading`` CSS rule is authoritative whenever a
    DOM exists — it is the actual output, whereas a source-text token (an
    explicit ``column_labels_font_weight='bold'``, or a bare ``band(...)``
    call assumed to be ``gt_consistency.band()``) is only an inference about
    what the source probably does and can be fooled by an unrelated
    same-named helper. Source-text inference is used ONLY when there is no
    DOM to check at all (e.g. exec failed, or a purely static source-review
    mode)."""
    if exec_res.dom is not None:
        return _dom_col_heading_bold(exec_res.dom)
    weight = _find_column_labels_font_weight(source)
    if weight and weight.strip().lower() in ("bold", "bolder", "700", "800", "900"):
        return True
    if _call_arg_blocks(source, "band", dotted=False):
        return True
    return False


def check_render_params(
    source: str, gtsave_kwargs: Optional[dict[str, Any]]
) -> list[Finding]:
    """PP-11: recorded/parsed gtsave params — zoom >= 2.0 and expand > 5."""
    kwargs: Optional[dict[str, Any]] = gtsave_kwargs
    if kwargs is None:
        # Exec never reached gtsave — fall back to source parsing.
        parsed = _render_from_source(source)
        if parsed is None:
            return [
                Finding(
                    "render-params",
                    INFO,
                    "no gtsave() call detected (could not check render params)",
                    "end the script with gt.gtsave('table.png', expand=15, zoom=2.0)",
                )
            ]
        kwargs = parsed

    findings: list[Finding] = []
    zoom = kwargs.get("zoom", 2.0)
    expand = kwargs.get("expand", 5)
    try:
        zoom_val = float(zoom)
    except (TypeError, ValueError):
        zoom_val = 2.0
    if zoom_val < 2.0:
        findings.append(
            Finding(
                "render-params",
                FAIL,
                f"gtsave zoom={zoom_val:g} is below the 2.0 default",
                "keep zoom >= 2.0; give the table room with vwidth/vheight before lowering crispness",
            )
        )
    # expand may be an int or a per-side tuple. For a tuple, EVERY side must
    # exceed the 5px default — the weakest side gates, so use the minimum (this
    # rejects e.g. expand=(15, 0, 0, 0), where three sides keep the default).
    expand_val: Optional[float] = None
    if isinstance(expand, (list, tuple)) and expand:
        try:
            expand_val = min(float(x) for x in expand)
        except (TypeError, ValueError):
            expand_val = None
    else:
        try:
            expand_val = float(expand)
        except (TypeError, ValueError):
            expand_val = None
    if expand_val is not None and expand_val <= 5:
        smallest = (
            f"smallest side expand={expand_val:g}"
            if isinstance(expand, (list, tuple))
            else f"expand={expand_val:g}"
        )
        findings.append(
            Finding(
                "render-params",
                FAIL,
                f"gtsave {smallest} is not raised above the 5px default",
                "raise expand on EVERY side to ~15-20 so the boxed frame has an outer margin",
            )
        )
    return findings


def _has_striping_enabled(source: str, exec_res: "ExecResult") -> bool:
    """Striping must be ENABLED, not merely styled. A bare
    ``row_striping_background_color=`` (color only) does NOT turn striping on.
    Accept an actual ``opt_row_striping()`` / ``stripe()`` call, or stripes
    verified in the rendered DOM."""
    return bool(
        re.search(r"opt_row_striping\s*\(", source) or re.search(r"\bstripe\s*\(", source)
    ) or _dom_has_stripes(exec_res.dom)


def check_striping_gate(source: str, exec_res: ExecResult) -> list[Finding]:
    """Striping applies by DEFAULT, ALWAYS (2026-08-12 redesign — the old
    ``>=10 body rows`` floor is gone: ``airquality_monthly_summary`` stripes
    at just 5 rows, and ``towny_growth_trends`` stripes even though 11 of its
    13 body columns are already heatmapped, both by explicit author
    direction). The ONLY exemption is a body that is genuinely 100%
    color-filled (``islands_sizes``'s single, fully-heatmapped column) — a
    stripe has no plain cell left to ever show through on. This is a real
    100%-coverage test, not the old ~90% approximation (a 95%-covered body no
    longer gets a free pass)."""
    if exec_res.dom is None:
        # No DOM — cannot count rows/fill reliably; skip (dom-error is
        # reported separately).
        return []
    rows = _dom_body_rows(exec_res.dom)
    if rows == 0:
        return []  # no body rows to stripe (e.g. an empty/degenerate table).

    if _has_striping_enabled(source, exec_res):
        return []

    fill_fraction = _dom_fill_fraction(exec_res.dom)
    if fill_fraction >= 1.0 - 1e-9:
        return []  # body is genuinely 100% color-filled; nothing for a stripe to show through on.

    return [
        Finding(
            "striping-gate",
            FAIL,
            f"{rows} body rows, body not 100% color-filled, but striping is not enabled",
            "call opt_row_striping() (there is no row-count floor anymore — striping is the default; "
            "skip it only when the body is genuinely 100% color-filled)",
        )
    ]


def _fmt_percent_columns_force_sign(source: str) -> dict[str, bool]:
    """``{column -> force_sign bool}`` for every column an ``fmt_percent(...)``
    call targets. Absent ``force_sign=`` resolves to ``False`` (great_tables'
    own default); a non-literal value is treated as ``False`` too (cannot be
    proven ``True`` statically, so it does not satisfy the rule)."""
    result: dict[str, bool] = {}
    for block in _call_arg_blocks(source, "fmt_percent"):
        cols_m = re.search(r"columns\s*=\s*(\[[^\]]*\]|['\"][^'\"]+['\"])", block)
        if not cols_m:
            continue
        cols = re.findall(r"['\"]([^'\"]+)['\"]", cols_m.group(1))
        fs_m = re.search(r"force_sign\s*=\s*(True|False)\b", block)
        value = fs_m.group(1) == "True" if fs_m else False
        for c in cols:
            result[c] = value
    return result


def _column_crosses_zero(gt_obj: Any, column: str) -> Optional[bool]:
    """True/False if ``column``'s underlying data spans both signs (a real
    positive AND a real negative value present); ``None`` if it cannot be
    determined (no exec'd ``gt``, missing column, non-numeric, or all-NaN)."""
    if gt_obj is None:
        return None
    try:
        series = gt_obj._tbl_data[column]
        lo = float(series.min())
        hi = float(series.max())
    except Exception:
        return None
    if lo != lo or hi != hi:  # NaN != NaN
        return None
    return lo < 0 < hi


def check_force_sign(source: str, exec_res: "ExecResult") -> list[Finding]:
    """A percent column whose underlying TRUTH data genuinely crosses zero (a
    real gain-or-loss measure — pct_change, growth %, best/worst day) must
    format with ``force_sign=True`` so a reader can tell +3.8% from -3.8% at a
    glance. An always-positive or always-negative percent has nothing to
    force a sign onto, so this only fires when the column's own data is
    genuinely signed (checked against the executed ``gt``'s own data, not
    guessed from the column name)."""
    force_sign_map = _fmt_percent_columns_force_sign(source)
    if not force_sign_map:
        return []
    findings: list[Finding] = []
    for col, force_sign in sorted(force_sign_map.items()):
        if _column_crosses_zero(exec_res.gt, col) is not True:
            continue
        if not force_sign:
            findings.append(
                Finding(
                    "force-sign",
                    FAIL,
                    f"fmt_percent(columns=[{col!r}]) has zero-crossing data (both positive and "
                    "negative values present) without force_sign=True",
                    "pass force_sign=True on fmt_percent for a signed (crosses-zero) percent measure",
                )
            )
    return findings


def _bold_full_column_body_styles(source: str) -> set[str]:
    """Columns with a ``tab_style(style.text(weight='bold'), locations=loc.body(
    columns=...))`` call that has NO ``rows=`` restriction — i.e. bolds the
    ENTIRE column, not a row-scoped subset.

    A row-scoped bold highlight (e.g. only the top-5/bottom-5 rows of an
    otherwise-plain measure, as in ``sp500_monthly_performance``'s
    ``pct_change``) is a distinct, legitimate pattern and is deliberately NOT
    what ``check_hero_not_bold`` targets — only an unconditional, whole-column
    bold is the violation shape."""
    bold_cols: set[str] = set()
    for block in _call_arg_blocks(source, "tab_style"):
        if not re.search(r"weight\s*=\s*['\"]bold['\"]", block):
            continue
        loc_m = re.search(r"loc\.body\s*\(([^)]*)\)", block)
        if not loc_m:
            continue
        loc_args = loc_m.group(1)
        if re.search(r"\brows\s*=", loc_args):
            continue  # row-scoped — not a full-column bold.
        cols_m = re.search(r"columns\s*=\s*(\[[^\]]*\]|['\"][^'\"]+['\"])", loc_args)
        if not cols_m:
            continue
        bold_cols.update(re.findall(r"['\"]([^'\"]+)['\"]", cols_m.group(1)))
    return bold_cols


def check_hero_not_bold(source: str, calls: list[ColorCall]) -> list[Finding]:
    """A column with no ``data_color``/``heatmap`` fill must never get a
    column-wide bold treatment — an uncolored named measure renders fully
    plain (no bold, no fill), the same treatment every current ground truth's
    own uncolored measure gets (gtcars_hp_price's horsepower, airquality's
    wind speed, towny's rank/total growth, sp500's open/close). This is a
    previously-untaught rule: bolding an uncolored hero measure used to look
    like a reasonable substitute for a 3rd color fill; it no longer is."""
    colored = _colored_column_names(calls)
    offending = sorted(_bold_full_column_body_styles(source) - colored)
    if not offending:
        return []
    return [
        Finding(
            "hero-not-bold",
            FAIL,
            f"column(s) {offending} are bolded across the whole column but have no color fill",
            "an uncolored measure must render fully plain — no bold, no fill; drop the bold "
            "tab_style or give the column an actual data_color/heatmap fill instead",
        )
    ]


_STANDARD_PADDING_KEYS: tuple[str, ...] = (
    "heading_padding",
    "column_labels_padding",
    "column_labels_padding_horizontal",
    "data_row_padding",
    "data_row_padding_horizontal",
    "source_notes_padding",
)


def check_layout_advisory(source: str) -> list[Finding]:
    """INFO-only consistency nicety (never a hard gate): the standard
    ``cols_width(cases={...})`` call and the full standard padding block. Every
    ground truth in this project sets both, but neither is a scored
    correctness rule — a table that skips them isn't wrong, just less tightly
    laid out, so this stays advisory."""
    findings: list[Finding] = []
    if not _call_arg_blocks(source, "cols_width"):
        findings.append(
            Finding(
                "layout-advisory",
                INFO,
                "no cols_width(cases={...}) call found",
                "size columns to their own content with cols_width(cases={...}) for a tighter, "
                "less auto-stretched layout",
            )
        )
    missing_padding = [k for k in _STANDARD_PADDING_KEYS if not re.search(rf"{k}\s*=", source)]
    if missing_padding:
        findings.append(
            Finding(
                "layout-advisory",
                INFO,
                f"missing the standard padding block: {missing_padding}",
                "set the standard tab_options padding keys (heading_padding, column_labels_padding, "
                "column_labels_padding_horizontal, data_row_padding, data_row_padding_horizontal, "
                "source_notes_padding) for consistent, tightened cell padding",
            )
        )
    return findings


def _source_stub_present(source: str) -> bool:
    """True if the source declares a stub (``rowname_col=`` in ``GT(...)``)."""
    for block in _call_arg_blocks(source, "GT", dotted=False):
        if re.search(r"rowname_col\s*=\s*['\"][^'\"]+['\"]", block):
            return True
    return False


def _source_stub_fill(source: str) -> Optional[str]:
    """The stub fill hex from source: ``stub_background_color=`` or a
    ``tab_style(style.fill(...), locations=loc.stub())`` call."""
    m = re.search(r"stub_background_color\s*=\s*['\"]([^'\"]+)['\"]", source)
    if m:
        return m.group(1)
    for block in _call_arg_blocks(source, "tab_style"):
        if "stub" not in block:
            continue
        cm = re.search(r"fill\s*\(\s*color\s*=\s*['\"]([^'\"]+)['\"]", block)
        if cm:
            return cm.group(1)
    return None


def check_stub_tint(source: str, exec_res: "ExecResult") -> list[Finding]:
    """Whenever a stub exists, its fill must be the fixed branding tint
    (``BRANDING["stub_tint"]`` = #EAF0F6) — universal across every table
    (2026-08-12 redesign), not a per-hue washed tint chosen per table.

    Every stub cell in the document must carry this tint, not just the first
    one: a table that tints only some rows (e.g. ``loc.stub(rows=[0])``)
    still fails, since the fixed branding tint is a table-wide surface, not a
    per-row highlight."""
    if exec_res.dom is not None:
        if not _dom_stub_present(exec_res.dom):
            return []
        fills = _dom_stub_fills(exec_res.dom)
        # Normalize case before comparing: two mechanisms writing the same
        # color in different letter-case (e.g. #EAF0F6 vs #eaf0f6) are the
        # same fill, not a "not uniform" finding. Matches the case
        # normalization the color-match check below already applies.
        normalized_fills = [f.strip().upper() if f else f for f in fills]
        unique_fills = set(normalized_fills)
        if len(unique_fills) > 1:
            found = ", ".join(sorted(v or "none" for v in unique_fills))
            return [
                Finding(
                    "stub-tint",
                    FAIL,
                    f"stub tint is not applied uniformly across all stub cells (found: {found})",
                    f"tint EVERY stub cell to the fixed branding hex {BRANDING['stub_tint']} "
                    "(a global stub_background_color / stub_tint() applies uniformly; a "
                    "per-row tab_style(locations=loc.stub(rows=[...])) does not)",
                )
            ]
        fill = unique_fills.pop() if unique_fills else None
    else:
        if not _source_stub_present(source):
            return []
        fill = _source_stub_fill(source)
        if fill is None and _call_arg_blocks(source, "stub_tint", dotted=False):
            fill = BRANDING["stub_tint"]  # stub_tint() always emits the fixed tint now.

    if fill is None:
        return [
            Finding(
                "stub-tint",
                FAIL,
                "a stub exists but has no fill/background color set",
                f"tint the stub to the fixed branding hex {BRANDING['stub_tint']} "
                "(tab_style(style.fill(color=...), locations=loc.stub()))",
            )
        ]
    if fill.strip().upper() != BRANDING["stub_tint"]:
        return [
            Finding(
                "stub-tint",
                FAIL,
                f"stub fill {fill} is not the fixed branding hex {BRANDING['stub_tint']}",
                f"use {BRANDING['stub_tint']} for every table's stub tint — it no longer varies by hue",
            )
        ]
    return []


def _source_stripe_color(source: str) -> Optional[str]:
    m = re.search(r"row_striping_background_color\s*=\s*['\"]([^'\"]+)['\"]", source)
    return m.group(1) if m else None


def check_stripe_color(source: str, exec_res: "ExecResult") -> list[Finding]:
    """Whenever row striping is enabled, its background must be the fixed
    neutral grey (``BRANDING["stripe"]`` = #F6F6F6) — great_tables' own
    ``opt_row_striping()`` default (#F4F4F4) is a different, unpinned hex, so
    an enabled-but-uncolored stripe still fails this rule."""
    if not _has_striping_enabled(source, exec_res):
        return []
    color = _dom_stripe_color(exec_res.dom)
    if color is None:
        color = _source_stripe_color(source)
    if color is None:
        return [
            Finding(
                "stripe-color",
                FAIL,
                "row striping is enabled but no row_striping_background_color is set "
                f"(renders great_tables' own default, not {BRANDING['stripe']})",
                f"pin row_striping_background_color='{BRANDING['stripe']}' (stripe() does this)",
            )
        ]
    if color.strip().upper() != BRANDING["stripe"]:
        return [
            Finding(
                "stripe-color",
                FAIL,
                f"row-stripe background {color} is not the fixed neutral grey {BRANDING['stripe']}",
                f"use {BRANDING['stripe']} for row striping — it's a fixed neutral, not a per-table color",
            )
        ]
    return []


def check_orphan_stub(source: str) -> list[Finding]:
    """PP-25: tab_stubhead(...) requires a rowname_col= in the GT(...) constructor."""
    if not _call_arg_blocks(source, "tab_stubhead"):
        return []
    gt_blocks = _call_arg_blocks(source, "GT", dotted=False)
    has_rowname = any(
        re.search(r"rowname_col\s*=\s*['\"][^'\"]+['\"]", b) for b in gt_blocks
    )
    if has_rowname:
        return []
    return [
        Finding(
            "orphan-stub",
            FAIL,
            "tab_stubhead(...) set but no rowname_col= in GT(...)",
            "give GT(df, rowname_col='<id column>') a real stub, or drop tab_stubhead()",
        )
    ]


def check_opt_stylize(source: str) -> list[Finding]:
    """PP-17: opt_stylize as a whole-table styler is banned by the flowchart."""
    if re.search(r"\.opt_stylize\s*\(", source):
        return [
            Finding(
                "opt-stylize-banned",
                FAIL,
                "opt_stylize(...) used as a whole-table styler",
                "build the band/frame/polish from the flowchart steps; do not use opt_stylize as a styler",
            )
        ]
    return []


def check_formatting(source: str, calls: list[ColorCall]) -> list[Finding]:
    """PP-14/15/16 (soft): if a table color-encodes numbers but uses no fmt_*
    formatter at all, the numbers likely render raw. INFO-level only."""
    if not calls:
        return []
    has_fmt = bool(re.search(r"\.fmt_[a-z_]+\s*\(", source))
    if has_fmt:
        return []
    return [
        Finding(
            "formatting",
            INFO,
            "numeric data_color present but no fmt_* formatter called (numbers may render raw)",
            "format value columns per semantic type (fmt_currency / fmt_percent / fmt_number)",
        )
    ]


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _run_safe(name: str, fn: Callable[[], list[Finding]]) -> list[Finding]:
    """Run one check, converting any internal error into a check-error INFO note
    so a single buggy check never aborts the whole run."""
    try:
        return fn()
    except Exception as exc:  # pragma: no cover - defensive
        return [
            Finding(
                "check-error",
                INFO,
                f"internal error while running check {name!r}: {exc}",
                "this is a checker bug, not a table problem; the other checks still ran",
            )
        ]


def run_checks(path: Path) -> tuple[list[Finding], dict[str, Any]]:
    """Run every source- and DOM-level check against ``table.py``.

    Returns ``(findings, meta)``. Never raises — any unexpected internal error is
    turned into a ``check-error`` finding."""
    findings: list[Finding] = []
    meta: dict[str, Any] = {"table_py": str(path)}

    try:
        raw_source = path.read_text(encoding="utf-8")
    except Exception as exc:
        findings.append(
            Finding(
                "check-error",
                FAIL,
                f"could not read {path}: {exc}",
                "pass a readable path to a table.py file",
            )
        )
        return findings, meta

    # All regex checks run on a comment/docstring-stripped copy so prose can
    # never masquerade as code. Exec still uses the real file (see run_table).
    source = _clean_source(raw_source)

    # --- Source-level parse (always available). ---
    calls = _parse_color_calls(source)

    # --- Exec + DOM (degrade gracefully). Run first so the band / Big-Color /
    # measure detection below can judge the RENDERED output, not just tokens. ---
    exec_res = run_table(path)
    meta["exec_ok"] = exec_res.exec_error is None and exec_res.gt is not None
    meta["dom_ok"] = exec_res.dom is not None
    meta["gtsave_kwargs"] = exec_res.gtsave_kwargs
    if exec_res.dom is not None:
        meta["body_rows"] = _dom_body_rows(exec_res.dom)

    # --- Band + Big-Color detection (helper-agnostic). ---
    # Band hex: the actual RENDERED .gt_col_heading background is authoritative
    # whenever a DOM exists — real output beats any inference about what the
    # source probably does (a source-text token like a bare `band(...)` call
    # only proves a function of that name was invoked, not that it's actually
    # gt_consistency.band() or that it produced this color). Source-text
    # detection (explicit tab_options token, then the band() helper's assumed
    # intent) is used ONLY when there is no DOM at all (e.g. exec failed, or a
    # purely static source-review mode).
    if exec_res.dom is not None:
        band_hex = _dom_col_heading_bg(exec_res.dom)
    else:
        band_hex = _find_band_color(source) or _band_hex_from_helper(source)
    # Big Color: any data_color/heatmap call, a solid DA hex used off-band, or
    # any inline-filled body cell in the DOM (covers the helper path).
    big_color = (
        bool(calls)
        or _has_big_color(source, band_hex)
        or _dom_has_colored_body(exec_res.dom)
    )
    meta.update(
        {
            "n_color_measures": len({c.columns for c in calls}),
            "palettes": sorted(c.palette for c in calls),
            "band_hex": band_hex,
            "band_shade": _band_shade(band_hex) if band_hex else "none",
            "big_color": big_color,
        }
    )

    # Meta findings for exec / DOM problems.
    if exec_res.exec_error is not None:
        findings.append(
            Finding(
                "exec-error",
                FAIL,
                f"table.py raised while executing: {exec_res.exec_error.splitlines()[-1]}",
                "the script must run cleanly (rendering is stubbed); fix the runtime error",
            )
        )
    if exec_res.gt is None and exec_res.exec_error is None:
        # Ran clean but no `gt` — the convention was not followed.
        findings.append(
            Finding(
                "gt-missing",
                FAIL,
                "no module-level `gt` variable found after executing table.py",
                "bind the final table to a top-level `gt` (e.g. `gt = GT(df)...`) so the checker can inspect it",
            )
        )
    if exec_res.gt is not None and exec_res.dom is None:
        findings.append(
            Finding(
                "dom-error",
                INFO,
                f"gt.as_raw_html() failed ({exec_res.dom_error}); DOM checks skipped",
                "ensure the table renders to HTML; source-level checks still ran",
            )
        )

    # --- Rule checks (each isolated). ---
    findings += _run_safe("palettes-domains", lambda: check_palettes_and_domains(source, calls))
    findings += _run_safe("frame-missing", lambda: check_frame(source, exec_res))
    findings += _run_safe("hairlines-missing", lambda: check_hairlines(source))
    findings += _run_safe("heading-band", lambda: check_heading_band(source, band_hex, exec_res))
    findings += _run_safe("render-params", lambda: check_render_params(source, exec_res.gtsave_kwargs))
    findings += _run_safe("striping-gate", lambda: check_striping_gate(source, exec_res))
    findings += _run_safe("stub-tint", lambda: check_stub_tint(source, exec_res))
    findings += _run_safe("stripe-color", lambda: check_stripe_color(source, exec_res))
    findings += _run_safe("force-sign", lambda: check_force_sign(source, exec_res))
    findings += _run_safe("hero-not-bold", lambda: check_hero_not_bold(source, calls))
    findings += _run_safe("orphan-stub", lambda: check_orphan_stub(source))
    findings += _run_safe("opt-stylize-banned", lambda: check_opt_stylize(source))
    findings += _run_safe("formatting", lambda: check_formatting(source, calls))
    findings += _run_safe("layout-advisory", lambda: check_layout_advisory(source))

    return findings, meta


def _print_report(findings: list[Finding], meta: dict[str, Any]) -> int:
    """Print the banner + per-violation lines; return the exit code."""
    fails = [f for f in findings if f.level == FAIL]
    infos = [f for f in findings if f.level == INFO]

    if fails:
        print(f"===== gt_check: FAIL ({len(fails)} issue(s)) =====")
    else:
        print("===== gt_check: PASS =====")

    # FAIL lines first, then INFO notes.
    for finding in fails:
        print(finding.line())
    for finding in infos:
        print(finding.line())

    if not findings:
        print("  (no issues)")

    return 1 if fails else 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gt_check.py",
        description="CI style-checker for a great-tables table.py "
        "(reads a module-level `gt`).",
    )
    parser.add_argument("table_py", help="path to the table.py to check")
    parser.add_argument(
        "--json",
        action="store_true",
        help="also print a machine-readable JSON summary to stdout",
    )
    args = parser.parse_args(argv)

    path = Path(args.table_py)
    if not path.exists():
        print(f"===== gt_check: FAIL (1 issue(s)) =====")
        print(
            f"  [check-error] file not found: {path} "
            f"— expected: a path to an existing table.py "
            f"— read {_reference_display('small_color.md')}"
        )
        if args.json:
            print(
                json.dumps(
                    {
                        "table_py": str(path),
                        "passed": False,
                        "findings": [
                            {
                                "rule_id": "check-error",
                                "level": FAIL,
                                "missed": f"file not found: {path}",
                                "expected": "a path to an existing table.py",
                                "reference": "references/small_color.md",
                            }
                        ],
                    },
                    indent=2,
                )
            )
        return 1

    try:
        findings, meta = run_checks(path)
    except Exception as exc:  # last-resort guard — never traceback.
        findings = [
            Finding(
                "check-error",
                FAIL,
                f"unexpected internal error: {exc}",
                "this is a checker bug; please report it",
            )
        ]
        meta = {"table_py": str(path)}

    exit_code = _print_report(findings, meta)

    if args.json:
        summary = {
            "table_py": str(path),
            "passed": exit_code == 0,
            "n_fail": sum(1 for f in findings if f.level == FAIL),
            "n_info": sum(1 for f in findings if f.level == INFO),
            "meta": meta,
            "findings": [f.as_dict() for f in findings],
        }
        print(json.dumps(summary, indent=2, default=str))

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
