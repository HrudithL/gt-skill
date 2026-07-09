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

# The complete allowed hex set for a heading band (case-insensitive membership).
ALL_PALETTE_HEXES: set[str] = {
    h.upper() for h in (*SOLID.values(), *WASHED.values(), *NEUTRAL.values())
}
# Solid (dark) hexes — a legitimate no-Big-Color anchor band comes from here.
SOLID_HEXES: set[str] = {h.upper() for h in SOLID.values()}

# --------------------------------------------------------------------------- #
# Rule id -> the reference file that documents its fix (drives the output line).
# --------------------------------------------------------------------------- #
RULE_REFS: dict[str, str] = {
    "too-many-measures": "palettes.md",
    "palette-signedness": "big_color/diverging_fill.md",
    "domain-symmetry": "big_color/diverging_fill.md",
    "domain-present": "big_color/column_gradient_fill.md",
    "frame-missing": "small_color.md",
    "heading-band": "palettes.md",
    "render-params": "small_color.md",
    "striping-gate": "small_color.md",
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
            f"— expected: {self.expected} — read references/{self.ref}"
        )

    def as_dict(self) -> dict[str, str]:
        return {
            "rule_id": self.rule_id,
            "level": self.level,
            "missed": self.missed,
            "expected": self.expected,
            "reference": f"references/{self.ref}",
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


def _hex_in_palette(hexstr: Optional[str]) -> bool:
    """True if ``hexstr`` is one of the allowed palette hexes (case-insensitive)."""
    return bool(hexstr) and hexstr.strip().upper() in ALL_PALETTE_HEXES


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
    # Standalone numeric literals only — a token inside df['x'] or .min() is skipped.
    nums = re.findall(r"(?<![\w.'\"])-?\d+(?:\.\d+)?(?![\w'\"])", content)
    if len(nums) == 2:
        return ("literal", (float(nums[0]), float(nums[1])))
    return ("unknown", None)


@dataclass
class ColorCall:
    """One parsed ``data_color(...)`` call."""

    columns: str
    palette: str
    domain_status: str
    domain: Optional[tuple[float, float]]

    @property
    def is_diverging(self) -> bool:
        return self.palette in DIVERGING_NAMES


def _parse_color_calls(source: str) -> list[ColorCall]:
    """Every ``data_color(...)`` call parsed into a ``ColorCall``."""
    calls: list[ColorCall] = []
    for block in _call_arg_blocks(source, "data_color"):
        status, bounds = _extract_domain(block)
        calls.append(
            ColorCall(
                columns=_columns_arg(block),
                palette=_palette_name(block),
                domain_status=status,
                domain=bounds,
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
def check_too_many_measures(source: str, calls: list[ColorCall]) -> list[Finding]:
    """PP-2/PP-3: at most 2 colored measures (distinct data_color targets)."""
    distinct = {c.columns for c in calls}
    n = len(distinct)
    if n > 2:
        return [
            Finding(
                "too-many-measures",
                FAIL,
                f"{n} colored measures ({n} distinct data_color targets)",
                "at most 2 colored measures; drop color from all but the 1-2 hero measures",
            )
        ]
    return []


def check_palettes_and_domains(source: str, calls: list[ColorCall]) -> list[Finding]:
    """PP-4 (signedness), PP-6 (symmetry), PP-7 (domain present) across all
    ``data_color`` calls."""
    findings: list[Finding] = []
    for call in calls:
        # PP-7 — every data_color needs an explicit domain.
        if call.domain_status == "missing":
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


def check_frame(source: str) -> list[Finding]:
    """PP-10: the mandatory enclosing boxed frame."""
    has_outline = bool(re.search(r"opt_table_outline\s*\(", source))
    has_side_borders = bool(
        re.search(r"table_border_left_(?:style|width|color)\s*=", source)
    ) and bool(re.search(r"table_border_right_(?:style|width|color)\s*=", source))
    has_frame_helper = bool(re.search(r"\b(?:frame|finalize)\s*\(", source))
    if has_outline or has_side_borders or has_frame_helper:
        return []
    return [
        Finding(
            "frame-missing",
            FAIL,
            "no enclosing boxed frame",
            "add opt_table_outline(), or set table_border_left/right_* on all four sides",
        )
    ]


def check_heading_band(source: str, band_hex: Optional[str], big_color: bool) -> list[Finding]:
    """PP-8/PP-9: heading band present and correct for the Big-Color state."""
    if band_hex is None:
        expected = (
            "a LIGHT washed-tint/grey band (Big Color present)"
            if big_color
            else "a DARK saturated Dark-Academia band (no Big Color)"
        )
        return [
            Finding(
                "heading-band",
                FAIL,
                "no column_labels_background_color set",
                f"set a column-label band: {expected}",
            )
        ]

    shade = _band_shade(band_hex)
    if not _hex_in_palette(band_hex):
        return [
            Finding(
                "heading-band",
                FAIL,
                f"band hex {band_hex} is not in the allowed palette",
                "use a hex from palettes.md (washed tint / neutral grey for light, DA solid for dark)",
            )
        ]

    if big_color and shade != "light":
        return [
            Finding(
                "heading-band",
                FAIL,
                f"Big Color present but band {band_hex} is not light",
                "use a LIGHT washed-DA tint (or grey) band when the table has Big Color",
            )
        ]
    if (not big_color) and shade != "dark":
        return [
            Finding(
                "heading-band",
                FAIL,
                f"no Big Color but band {band_hex} is not a dark saturated anchor",
                "use a DARK saturated Dark-Academia solid band (white text) when there is no Big Color",
            )
        ]
    return []


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
    # expand may be an int or a 4-tuple; take the max when it is a tuple.
    expand_val: Optional[float] = None
    if isinstance(expand, (list, tuple)) and expand:
        try:
            expand_val = max(float(x) for x in expand)
        except (TypeError, ValueError):
            expand_val = None
    else:
        try:
            expand_val = float(expand)
        except (TypeError, ValueError):
            expand_val = None
    if expand_val is not None and expand_val <= 5:
        findings.append(
            Finding(
                "render-params",
                FAIL,
                f"gtsave expand={expand_val:g} is not raised above the 5px default",
                "raise expand to ~15-20 so the boxed frame has an outer margin",
            )
        )
    return findings


def check_striping_gate(
    source: str, exec_res: ExecResult, big_color: bool
) -> list[Finding]:
    """PP-12: >=10 body rows and body not fully filled ⇒ striping expected."""
    if exec_res.dom is None:
        # No DOM — cannot count rows reliably; skip (dom-error is reported separately).
        return []
    rows = _dom_body_rows(exec_res.dom)
    if rows < 10:
        return []  # under 10 rows: striping optional either way.

    has_striping = bool(
        re.search(r"opt_row_striping\s*\(", source)
        or re.search(r"row_striping_background_color\s*=", source)
        or re.search(r"row_striping_include_table_body\s*=\s*True", source)
    )
    if has_striping:
        return []

    fill_fraction = _dom_fill_fraction(exec_res.dom)
    if fill_fraction >= 0.9:
        return []  # body essentially fully filled by color; stripes would fight it.

    return [
        Finding(
            "striping-gate",
            FAIL,
            f"{rows} body rows, body not fully color-filled, but no row striping",
            "add opt_row_striping() for a >=10-row table whose body is not fully filled",
        )
    ]


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
    band_hex = _find_band_color(source)
    big_color = _has_big_color(source, band_hex)
    meta.update(
        {
            "n_color_measures": len({c.columns for c in calls}),
            "palettes": sorted(c.palette for c in calls),
            "band_hex": band_hex,
            "band_shade": _band_shade(band_hex) if band_hex else "none",
            "big_color": big_color,
        }
    )

    # --- Exec + DOM (degrade gracefully). ---
    exec_res = run_table(path)
    meta["exec_ok"] = exec_res.exec_error is None and exec_res.gt is not None
    meta["dom_ok"] = exec_res.dom is not None
    meta["gtsave_kwargs"] = exec_res.gtsave_kwargs
    if exec_res.dom is not None:
        meta["body_rows"] = _dom_body_rows(exec_res.dom)

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
    findings += _run_safe("too-many-measures", lambda: check_too_many_measures(source, calls))
    findings += _run_safe("palettes-domains", lambda: check_palettes_and_domains(source, calls))
    findings += _run_safe("frame-missing", lambda: check_frame(source))
    findings += _run_safe("heading-band", lambda: check_heading_band(source, band_hex, big_color))
    findings += _run_safe("render-params", lambda: check_render_params(source, exec_res.gtsave_kwargs))
    findings += _run_safe("striping-gate", lambda: check_striping_gate(source, exec_res, big_color))
    findings += _run_safe("orphan-stub", lambda: check_orphan_stub(source))
    findings += _run_safe("opt-stylize-banned", lambda: check_opt_stylize(source))
    findings += _run_safe("formatting", lambda: check_formatting(source, calls))

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
            f"— expected: a path to an existing table.py — read references/small_color.md"
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
