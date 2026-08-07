#!/usr/bin/env python3
"""CLI: score a candidate `table.py` against its prompt's ground truth.

    python scripts/gt_compare.py <candidate_table.py> <prompt_id>

`<prompt_id>` is a corpus prompt's file stem (e.g. `towny_growth_trends`) --
its ground truth is resolved by searching `prompts/<difficulty>/ground_truth/
<prompt_id>.py`, and its original prompt text by searching
`prompts/<difficulty>/<prompt_id>.json`'s `"prompt"` field, across the three
difficulty tiers. Most checks are deterministic (regex/AST/execution); a
handful are a single grounded LLM judge call -- see `runner/comparator.py`
and `runner/judge.py`. If the judge is unavailable (no credentials, no
network), the run still completes -- judge-backed checks read N/A and
mechanical checks are unaffected.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runner import comparator  # noqa: E402

_DIFFICULTIES = ("easy", "medium", "hard")


def _resolve_ground_truth(prompt_id: str) -> Path:
    for difficulty in _DIFFICULTIES:
        candidate = ROOT / "prompts" / difficulty / "ground_truth" / f"{prompt_id}.py"
        if candidate.is_file():
            return candidate
    searched = ", ".join(str(ROOT / "prompts" / d / "ground_truth" / f"{prompt_id}.py") for d in _DIFFICULTIES)
    raise SystemExit(f"no ground truth found for prompt_id={prompt_id!r}; searched: {searched}")


def _resolve_prompt_text(prompt_id: str) -> str:
    """The original natural-language prompt's own `"prompt"` field, read
    from `prompts/<difficulty>/<prompt_id>.json` (same three-tier search
    `_resolve_ground_truth` already does, one directory level up -- the
    prompt JSON is a sibling of `ground_truth/`, not inside it). Returns
    `""` (not a hard error) if no matching prompt JSON is found -- the judge
    still runs with less grounding rather than the whole comparison failing
    over a missing prompt file, matching every other judge-unavailable
    degrade path in this system.
    """
    for difficulty in _DIFFICULTIES:
        candidate = ROOT / "prompts" / difficulty / f"{prompt_id}.json"
        if candidate.is_file():
            try:
                return json.loads(candidate.read_text()).get("prompt", "") or ""
            except (json.JSONDecodeError, OSError):
                return ""
    return ""


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    candidate_path = Path(argv[1]).resolve()
    prompt_id = argv[2]
    if not candidate_path.is_file():
        print(f"error: candidate file not found: {candidate_path}", file=sys.stderr)
        return 2
    ground_truth_path = _resolve_ground_truth(prompt_id)
    prompt_text = _resolve_prompt_text(prompt_id)
    report = comparator.compare(candidate_path, ground_truth_path, prompt_text)
    print(comparator.format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
