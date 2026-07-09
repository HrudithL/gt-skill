#!/usr/bin/env python3
"""Drift-guard: ``gt_consistency.PALETTE`` must mirror ``references/palettes.md``.

``palettes.md`` is the single source of truth for every color hex; the scripted
variant's ``PALETTE`` must not drift from it. This test asserts both directions:

  1. script  subset of  doc  — every hex in ``PALETTE`` appears in the doc.
  2. doc-core subset of script — the 19 CORE hexes (6 solids + 6 washed tints +
     7 neutrals) parsed from the doc all appear in ``PALETTE``.

Together those mean the two hex sets are identical.

Runnable two ways (no hard dependency on pytest):

    pytest tests/test_palette_parity.py
    python tests/test_palette_parity.py     # prints OK / exits 1 on failure
"""
import os
import re
import sys

# Matches a #RRGGBB hex; fullmatch is used when filtering PALETTE leaves so
# that palette NAMES ("Blues", "RdYlGn", ...) are ignored.
HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(REPO_ROOT, ".claude", "skills", "great-tables")
# palettes.md is the source of truth in the prose skill's references/; the
# helper library now lives in the scripted (CI) skill's scripts/ (R2 moved it).
PALETTES_MD = os.path.join(SKILL_DIR, "references", "palettes.md")
SCRIPTS_DIR = os.path.join(REPO_ROOT, ".claude", "skills", "great-tables-ci", "scripts")


def _doc_hexes():
    """Return the set of #RRGGBB hexes parsed from palettes.md (uppercased)."""
    with open(PALETTES_MD, encoding="utf-8") as fh:
        text = fh.read()
    return {h.upper() for h in HEX_RE.findall(text)}


def _load_palette():
    """Import PALETTE from gt_consistency.py without importing great_tables."""
    if SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, SCRIPTS_DIR)
    import gt_consistency

    return gt_consistency.PALETTE


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


def _run():
    test_script_hexes_are_subset_of_doc()
    test_core_doc_hexes_are_in_script()


if __name__ == "__main__":
    try:
        _run()
    except AssertionError as exc:
        print("FAIL:", exc)
        sys.exit(1)
    print("OK")
