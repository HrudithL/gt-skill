# `airquality_monthly_summary/repeat_2` — why this repeat is an outlier

This invocation scored 21.1% (19/90) vs. 91.8%/96.9% for its two siblings on the
same prompt — the widest single-prompt spread (75.8pp) in the round-5 sweep. Its
`table.py` is 35 lines of bare `pandas`/`great_tables` code. All three repeats
(including the successful 91.8% and 96.9% siblings) import zero `gt_consistency.py`
helpers, so import count alone does not distinguish this failure from success —
a misleading signal. The real discriminator is documented below in the tool-call
evidence and verifiable in the committed metrics.

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
rather than a doc or comparator gap. The committed `metrics.json` captures the
real evidence: `repeat_2` used only 5 turns and 109K cache-read tokens, versus
`repeat_1` (16 turns, 576K tokens) and `repeat_3` (20 turns, 711K tokens) — a
stark reduction in work volume consistent with skipping the Skill invocation and
reference reading entirely.
