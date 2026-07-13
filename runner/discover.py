#!/usr/bin/env python3
"""Catalogs: prompts, data files, skills, models.

Read-only discovery over the repo layout, shared by the CLI (to resolve
``--prompt <name>`` / ``--difficulty``) and the web backend (the
``/api/{prompts,data,skills,models}`` endpoints). Prompt discovery is the old
``test_runner.discover_prompts`` logic; the rest is new surface the UI needs.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from runner.engine import (
    CREATOR_SKILL_SRC,
    ROOT,
    SKILL_CI_DIR,
    SKILL_DIR,
)
from runner.spec import MODELS, SKILL_LABELS

PROMPTS_DIR = ROOT / "prompts"
DATA_DIR = ROOT / "data"
DIFFICULTIES = ["easy", "medium", "hard"]

# UI skill label -> (source directory, one-line summary fallback). The source
# dirs come from the engine so there is one source of truth for where each skill
# lives; descriptions are read live from each SKILL.md's frontmatter.
SKILL_DIRS: dict[str, Path] = {
    "prose": SKILL_DIR,
    "scripts": SKILL_CI_DIR,
    "creator": CREATOR_SKILL_SRC,
}


# --------------------------------------------------------------------------- #
# prompts
# --------------------------------------------------------------------------- #
def discover_prompts(difficulty: str | None = None) -> list[dict]:
    """Return {name, difficulty, path, prompt, data} for matching corpus prompts.

    ``data`` is the resolved absolute path (a prompt whose data file is missing
    is skipped with a warning), matching the old test_runner behavior so the
    sweep flow is unchanged.
    """
    if difficulty and difficulty != "all":
        dirs = [PROMPTS_DIR / difficulty]
    else:
        dirs = [PROMPTS_DIR / d for d in DIFFICULTIES]

    prompts: list[dict] = []
    for d in dirs:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.json")):
            content = json.loads(f.read_text())
            data_path = ROOT / content["data"]
            if not data_path.is_file():
                print(
                    f"warning: data file not found for {f.name}: {data_path}",
                    file=sys.stderr,
                )
                continue
            prompts.append(
                {
                    "name": f.stem,
                    "difficulty": d.name,
                    "path": str(f),
                    "prompt": content["prompt"],
                    "data": str(data_path.resolve()),
                }
            )
    return prompts


def prompts_grouped() -> dict[str, list[dict]]:
    """Corpus prompts grouped by difficulty (easy/medium/hard) for the picker."""
    grouped: dict[str, list[dict]] = {d: [] for d in DIFFICULTIES}
    for p in discover_prompts(None):
        grouped.setdefault(p["difficulty"], []).append(p)
    return grouped


def find_prompt(name: str) -> dict | None:
    """Look up one corpus prompt by its file stem (the ``--prompt`` argument)."""
    for p in discover_prompts(None):
        if p["name"] == name:
            return p
    return None


# --------------------------------------------------------------------------- #
# data
# --------------------------------------------------------------------------- #
def list_data() -> list[dict]:
    """Every ``data/*.csv`` as {name, path, size_bytes} (sorted by name)."""
    if not DATA_DIR.is_dir():
        return []
    out: list[dict] = []
    for f in sorted(DATA_DIR.glob("*.csv")):
        try:
            size = f.stat().st_size
        except OSError:
            size = None
        out.append({"name": f.name, "path": f"data/{f.name}", "size_bytes": size})
    return out


# --------------------------------------------------------------------------- #
# models
# --------------------------------------------------------------------------- #
def list_models() -> list[dict]:
    """The model dropdown: [{label, id}] in UI order (haiku default first)."""
    return [{"label": label, "id": model_id} for label, model_id in MODELS.items()]


# --------------------------------------------------------------------------- #
# skills
# --------------------------------------------------------------------------- #
_FRONTMATTER_DESC = re.compile(r"^description:\s*(.+?)\s*$", re.MULTILINE)


def _skill_description(skill_dir: Path) -> str | None:
    """First-line ``description:`` from the skill's SKILL.md frontmatter, if any."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return None
    try:
        text = skill_md.read_text()
    except OSError:
        return None
    m = _FRONTMATTER_DESC.search(text)
    return m.group(1) if m else None


def _file_tree(root: Path, rel: Path | None = None) -> list[dict]:
    """Nested [{name, type, path, children?}] listing of ``root``.

    ``path`` is relative to the skill root (POSIX separators) so the backend can
    round-trip it through ``/api/skills/{name}/file?path=``. Symlinks are
    followed (the CI skill's references/assets are symlinks today); ``__pycache__``
    and dotfiles are skipped.
    """
    base = root if rel is None else root / rel
    entries: list[dict] = []
    try:
        children = sorted(base.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except OSError:
        return entries
    for child in children:
        if child.name == "__pycache__" or child.name.startswith("."):
            continue
        child_rel = child.name if rel is None else f"{rel.as_posix()}/{child.name}"
        if child.is_dir():
            entries.append(
                {
                    "name": child.name,
                    "type": "dir",
                    "path": child_rel,
                    "children": _file_tree(root, Path(child_rel)),
                }
            )
        else:
            entries.append({"name": child.name, "type": "file", "path": child_rel})
    return entries


def list_skills() -> list[dict]:
    """The three skills as {label, dir, description, tree} for the picker + viewer."""
    out: list[dict] = []
    for label in SKILL_LABELS:
        skill_dir = SKILL_DIRS[label]
        if not skill_dir.is_dir():
            continue
        out.append(
            {
                "label": label,
                "dir": str(skill_dir.relative_to(ROOT)),
                "description": _skill_description(skill_dir),
                "tree": _file_tree(skill_dir),
            }
        )
    return out


def skill_dir(label: str) -> Path | None:
    """The source directory for a UI skill label (None if unknown)."""
    return SKILL_DIRS.get(label)
