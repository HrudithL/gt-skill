# Progressive disclosure in action — `scripts` skill

Real excerpt from `runs/sweep/20260807_080530_scripts_6prompts/prompts/gtcars_hp_price/repeat_1/transcript.json`
(prompt: *"Show me a table of the gt cars with their horsepower and
price."*). `great-tables-ci` is the same flowchart skill as `prose` plus a
checker loop (`scripts/gt_check.py`) — this excerpt shows both halves:
progressive reference reads before writing code, then a mechanical
check-and-fix loop after.

1. **Invoke the skill**:
   ```
   Skill({"skill": "great-tables-ci"})
   ```
2. **State the plan before reading anything** — "Now I'll follow the 7-step
   flowchart. First, let me examine the data and the reference files." — then
   2 `Read` calls (the data file + the flowchart's entry-point reference).
3. **Follow the flowchart's routing to the specific rules this data needs** —
   "Now let me read the key reference files needed for this table:" — 4 more
   `Read` calls into `references/`, narrowed to this prompt's two
   neutral-magnitude numeric measures (horsepower, price) rather than the
   whole directory.
4. **Only now writes code** — `Write(table.py)`, with its own commentary
   walking through the flowchart steps it just read (data cleaning, column
   organization, row identifier) in the same order it read them.
5. **Runs the checker it was told to run** — "Now let me run the checker to
   verify the table against the CI rules:"
   ```
   Bash({"command": "<the skill's own gt_check.py invocation>"})
   ```
6. **Reads the checker's specific complaint, then reads exactly the file
   needed to fix it** — "I need to fix three issues. Let me check the API for
   currency formatting and review the band setting" — a targeted `Read` of
   the API reference and a `Bash` probe of the real function signature,
   scoped to the 3 things the checker flagged, not a general re-read.

The reference reads in steps 2-3 are the same progressive pattern as `prose`;
step 5-6 is `scripts`' own addition — disclosure continues *after* the first
draft, pulled in on demand by what the checker actually failed on.
