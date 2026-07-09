#!/usr/bin/env python3
"""Drift-guard + execution-helper tests for ``gt_consistency``.

Two families of tests live here:

  1. **Palette parity** (the original tests) — ``gt_consistency.PALETTE`` must
     mirror ``references/palettes.md`` exactly, in both directions:
       * script  subset of  doc  — every hex in ``PALETTE`` appears in the doc.
       * doc-core subset of script — the 19 CORE hexes (6 solids + 6 washed
         tints + 7 neutrals) parsed from the doc all appear in ``PALETTE``.

  2. **Execution helpers (R8)** — the thin ``heatmap`` / ``band`` / ``stripe`` /
     ``stub_tint`` helpers:
       * must not inline any stray hex or palette NAME (every color they emit
         comes from ``PALETTE`` or the caller) — the "zero decisions" doctrine.
       * must execute their (model-supplied) decision identically: symmetric
         diverging domain, full-range sequential domain, and the pinned
         background hexes in the rendered HTML.

Runnable two ways (no hard dependency on pytest):

    pytest test_palette_parity.py
    python test_palette_parity.py     # prints OK / exits 1 on failure

Path resolution: ``gt_consistency`` is imported from the test file's own
directory first (so a colocated copy wins), else from the skill's
``scripts/``. ``palettes.md`` is located under the skill dir, which defaults to
the repo layout (``<repo>/.claude/skills/great-tables``) but can be overridden
with the ``GT_SKILL_DIR`` environment variable.
"""
import inspect
import os
import re
import sys

# Matches a #RRGGBB hex; fullmatch is used when filtering PALETTE leaves so
# that palette NAMES ("Blues", "RdYlGn", ...) are ignored.
HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _skill_dir():
    """Locate the great-tables skill dir (env override, else repo layout)."""
    env = os.environ.get("GT_SKILL_DIR")
    if env:
        return env
    return os.path.join(REPO_ROOT, ".claude", "skills", "great-tables")


SKILL_DIR = _skill_dir()
PALETTES_MD = os.path.join(SKILL_DIR, "references", "palettes.md")
# The helper library lives in the scripted (CI) skill's scripts/ — R2 moved it
# out of the prose skill (which now ships no scripts/). palettes.md stays the
# source of truth in the prose skill's references/. A colocated copy beside this
# test still wins (see _import_module), so this is only the repo-layout fallback.
SCRIPTS_DIR = os.path.join(REPO_ROOT, ".claude", "skills", "great-tables-ci", "scripts")


def _doc_hexes():
    """Return the set of #RRGGBB hexes parsed from palettes.md (uppercased)."""
    with open(PALETTES_MD, encoding="utf-8") as fh:
        text = fh.read()
    return {h.upper() for h in HEX_RE.findall(text)}


def _import_module():
    """Import gt_consistency without importing great_tables at module top.

    The test file's own directory is tried first (a colocated copy wins), then
    the skill's ``scripts/`` directory. ``HERE`` is forced to the front of
    ``sys.path`` (even when it is already present at a lower priority) so a
    colocated copy always shadows the skill's installed one; ``SCRIPTS_DIR`` is
    appended at lowest priority as the repo-layout fallback.
    """
    if SCRIPTS_DIR not in sys.path:
        sys.path.append(SCRIPTS_DIR)
    if HERE in sys.path:
        sys.path.remove(HERE)
    sys.path.insert(0, HERE)
    import gt_consistency

    return gt_consistency


def _load_palette():
    """Import PALETTE from gt_consistency.py without importing great_tables."""
    return _import_module().PALETTE


def _flatten_hexes(obj):
    """Yield every hex-looking string leaf (uppercased); ignore palette names."""
    if isinstance(obj, str):
        if HEX_RE.fullmatch(obj):
            yield obj.upper()
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from _flatten_hexes(value)
    elif isinstance(obj, (list, tuple, set)):
        for value in obj:
            yield from _flatten_hexes(value)


# ---------------------------------------------------------------------------
# Family 1 — palette parity (original tests, unchanged behavior).
# ---------------------------------------------------------------------------

def test_script_hexes_are_subset_of_doc():
    """Every hex in PALETTE must exist in palettes.md (script subset of doc)."""
    doc = _doc_hexes()
    script = set(_flatten_hexes(_load_palette()))
    extra = script - doc
    assert not extra, (
        "gt_consistency.PALETTE has hex(es) absent from references/palettes.md "
        "(script is not a subset of doc): " + ", ".join(sorted(extra))
    )


def test_core_doc_hexes_are_in_script():
    """The 19 core doc hexes must all appear in PALETTE (doc-core subset of script)."""
    doc = _doc_hexes()
    script = set(_flatten_hexes(_load_palette()))
    assert len(doc) == 19, (
        "expected exactly 19 core hexes (6 solids + 6 washed + 7 neutrals) in "
        "references/palettes.md, found %d: %s" % (len(doc), ", ".join(sorted(doc)))
    )
    missing = doc - script
    assert not missing, (
        "references/palettes.md hex(es) missing from gt_consistency.PALETTE "
        "(doc-core is not a subset of script): " + ", ".join(sorted(missing))
    )


# ---------------------------------------------------------------------------
# Family 2a — the helpers encode ZERO literal colors.
# ---------------------------------------------------------------------------

# The names of the execution helpers (public + private) whose bodies must be
# free of inlined hexes / palette NAMES.
_HELPER_NAMES = (
    "heatmap",
    "band",
    "stripe",
    "stub_tint",
    "_as_columns",
    "_column_min_max",
    "_heatmap_domain",
    "_resolve_palette",
)


def _palette_names(palette):
    """Every palette NAME literal that PALETTE resolves to (brewer names)."""
    names = set()
    for value in palette["sequential"].values():
        names.add(value)
    for value in palette["diverging"].values():
        if isinstance(value, (list, tuple)):
            names.update(value)
        else:
            names.add(value)
    return names


def test_helpers_contain_no_stray_color_literals():
    """Helper bodies must draw every hex / palette NAME from PALETTE or args.

    Fails if any helper's source inlines a ``#RRGGBB`` hex or a brewer palette
    NAME (e.g. ``RdYlGn``, ``Blues``) — those must live only in ``PALETTE``.
    """
    module = _import_module()
    names = _palette_names(module.PALETTE)

    for fn_name in _HELPER_NAMES:
        fn = getattr(module, fn_name)
        src = inspect.getsource(fn)

        stray_hex = HEX_RE.findall(src)
        assert not stray_hex, (
            "helper %s() inlines hex literal(s) %s — read them from PALETTE "
            "instead" % (fn_name, ", ".join(sorted(set(stray_hex))))
        )

        stray_names = sorted(n for n in names if n in src)
        assert not stray_names, (
            "helper %s() inlines palette NAME literal(s) %s — resolve them "
            "through PALETTE instead" % (fn_name, ", ".join(stray_names))
        )


# ---------------------------------------------------------------------------
# Family 2b — the helpers execute the model's decision identically (behavior).
# Guarded: skipped (no-op) if great_tables / pandas are unavailable. They ARE
# installed in the skill's venv, so these run there.
# ---------------------------------------------------------------------------

try:  # optional deps for the behavior tests only
    import pandas as _pd
    from great_tables import GT as _GT

    _HAS_GT = True
except Exception:  # pragma: no cover - venv has both
    _HAS_GT = False


def _capture_data_color(call):
    """Run ``call`` with GT.data_color spied; return the captured kwargs.

    Wraps ``great_tables.GT.data_color`` so the arguments ``heatmap`` passes
    (domain / palette / na_color / truncate / autocolor_text) can be asserted
    directly, then restores the original method.
    """
    import great_tables as gt_mod

    captured = {}
    original = gt_mod.GT.data_color

    def _spy(self, *args, **kwargs):
        captured.update(kwargs)
        return original(self, *args, **kwargs)

    gt_mod.GT.data_color = _spy
    try:
        call()
    finally:
        gt_mod.GT.data_color = original
    return captured


def test_heatmap_diverging_domain_is_symmetric():
    """Diverging heatmap over data [-3, 10] must build a symmetric [-10, 10]."""
    if not _HAS_GT:
        return
    module = _import_module()
    df = _pd.DataFrame({"delta": [-3, 10]})

    captured = _capture_data_color(
        lambda: module.heatmap(_GT(df), "delta", kind="diverging", hue="default")
    )

    assert captured["domain"] == [-10.0, 10.0], captured["domain"]
    assert captured["palette"] == module.PALETTE["diverging"]["default"]
    assert captured["na_color"] == module.PALETTE["neutral"]["na_cell"]
    assert captured["truncate"] is False
    assert captured["autocolor_text"] is True


def test_heatmap_sequential_domain_is_full_range():
    """Sequential heatmap must span the full [min, max] across all columns."""
    if not _HAS_GT:
        return
    module = _import_module()
    # Two facet columns share ONE domain: min across both = 2, max across both = 20.
    df = _pd.DataFrame({"q1": [2, 8, 5], "q2": [11, 20, 4]})

    captured = _capture_data_color(
        lambda: module.heatmap(
            _GT(df), ["q1", "q2"], kind="sequential", hue="neutral"
        )
    )

    assert captured["domain"] == [2.0, 20.0], captured["domain"]
    assert captured["palette"] == module.PALETTE["sequential"]["neutral"]


def test_heatmap_domain_override_is_verbatim():
    """An explicit domain= (model override) must be passed through unchanged."""
    if not _HAS_GT:
        return
    module = _import_module()
    df = _pd.DataFrame({"score": [1, 2, 3]})

    captured = _capture_data_color(
        lambda: module.heatmap(
            _GT(df), "score", kind="sequential", hue="neutral", domain=[0, 100]
        )
    )
    assert captured["domain"] == [0, 100]


def test_heatmap_literal_palette_name_passes_through():
    """A literal palette NAME (not a semantic key) is used verbatim."""
    if not _HAS_GT:
        return
    module = _import_module()
    df = _pd.DataFrame({"delta": [-2, 5]})

    captured = _capture_data_color(
        lambda: module.heatmap(_GT(df), "delta", kind="diverging", hue="RdBu")
    )
    assert captured["palette"] == "RdBu"


def test_helpers_render_expected_backgrounds():
    """band/stripe/stub_tint must emit their pinned hexes into the HTML."""
    if not _HAS_GT:
        return
    module = _import_module()
    df = _pd.DataFrame(
        {
            "name": ["a", "b", "c", "d"],
            "delta": [-3, 10, 2, -1],
        }
    )

    gt = _GT(df, rowname_col="name")
    gt = module.heatmap(gt, "delta", kind="diverging", hue="default")
    gt = module.band(gt, shade="light", hue="navy")
    gt = module.stripe(gt)
    gt = module.stub_tint(gt, hue="grey")

    html = gt.as_raw_html().lower()

    band_hex = module.PALETTE["washed"]["navy"].lower()       # #EAF0F6
    stripe_hex = module.PALETTE["neutral"]["row_stripe"].lower()  # #F6F6F6
    stub_hex = module.PALETTE["neutral"]["label_band"].lower()    # #F0F0F0
    rule_hex = module.PALETTE["neutral"]["column_label_rule"].lower()  # #CCCCCC

    assert band_hex in html, "washed-navy band hex missing from HTML"
    assert stripe_hex in html, "row-stripe hex missing from HTML"
    assert stub_hex in html, "stub-tint hex missing from HTML"
    assert rule_hex in html, "column-label bottom-rule hex missing from HTML"


def test_dark_band_uses_solid_and_white_text():
    """A dark band paints the DA solid and turns column-label text white."""
    if not _HAS_GT:
        return
    module = _import_module()
    df = _pd.DataFrame({"x": [1, 2], "y": [3, 4]})

    gt = module.band(_GT(df), shade="dark", hue="navy")
    html = gt.as_raw_html().lower()

    assert module.PALETTE["solid"]["navy"].lower() in html, "dark-band solid missing"
    assert "white" in html, "white column-label text missing from HTML"


# ---------------------------------------------------------------------------
# Script-mode runner (no pytest required).
# ---------------------------------------------------------------------------

_TESTS = [
    test_script_hexes_are_subset_of_doc,
    test_core_doc_hexes_are_in_script,
    test_helpers_contain_no_stray_color_literals,
    test_heatmap_diverging_domain_is_symmetric,
    test_heatmap_sequential_domain_is_full_range,
    test_heatmap_domain_override_is_verbatim,
    test_heatmap_literal_palette_name_passes_through,
    test_helpers_render_expected_backgrounds,
    test_dark_band_uses_solid_and_white_text,
]


def _run():
    passed = 0
    for test in _TESTS:
        test()
        passed += 1
        print("PASS:", test.__name__)
    print("OK (%d passed)" % passed)
    if not _HAS_GT:
        print("NOTE: great_tables/pandas unavailable — behavior tests were no-ops.")


if __name__ == "__main__":
    try:
        _run()
    except AssertionError as exc:
        print("FAIL:", exc)
        sys.exit(1)
    print("OK")
