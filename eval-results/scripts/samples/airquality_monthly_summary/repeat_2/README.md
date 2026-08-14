# `airquality_monthly_summary/repeat_2` — why this repeat is an outlier

This invocation scored 21.1% (19/90) vs. 91.8%/96.9% for its two siblings on the
same prompt — the widest single-prompt spread (75.8pp) in the round-5 sweep. Its
`table.py` is 35 lines of bare `pandas`/`great_tables` code with none of
`gt_consistency.py`'s helpers imported at all, which is consistent with the model
never having read the skill's reference material before writing code.

The evidence for that in the original run is `runs/sweep/20260813_161442_scripts_6prompts/
prompts/airquality_monthly_summary/repeat_2/transcript.json`, which is gitignored
and not part of this repo's history, so a future reader of `SUMMARY.md` can't
re-derive this from committed artifacts alone. This file records the specific,
already-observed comparison as a plain fact instead:

| Repeat | Tool calls | Opens with `Skill`? |
|---|---|---|
| `repeat_1` | 14 | yes |
| `repeat_2` (this one) | 4 | **no** — `Read` (CSV) -> `Write` (`table.py`) -> `Bash` (run) -> `Read` (view PNG) |
| `repeat_3` | 18 | yes |

`repeat_2`'s tool sequence never includes a `Skill` call at all, unlike both
siblings, which open with one before reading any reference files or writing code.
Read together with the near-total comparator miss above (no stub, no colored
measures, no frame, no hairlines, no header branding, no caption), this points to
the model electing not to invoke the available skill on this particular run,
rather than a doc or comparator gap — the skill materials (including a copy of
`gt_consistency.py` in the working directory) were present and used correctly by
both siblings on the identical prompt.
