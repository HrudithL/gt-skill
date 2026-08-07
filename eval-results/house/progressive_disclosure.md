# Progressive disclosure in action — `house` skill

Real excerpt from `runs/sweep/20260807_080527_house_6prompts/prompts/airquality_monthly_summary/repeat_3/transcript.json`
(prompt: *"Create a table comparing the average temperature, wind speed, and
ozone levels for each month in the air quality data."*). Nothing here is
staged — this is the agent's actual tool-call sequence, showing it pull in
the `great-tables-house` skill's material one layer at a time instead of
having everything dumped into context up front: invoke the skill -> read the
data -> read the one worked reference script -> read the rules file -> only
then write code.

1. **Invoke the skill** (loads `SKILL.md`, nothing else yet):
   ```
   Skill({"skill": "great-tables-house"})
   ```
2. **Read the data** — "I'll create a monthly summary table of air quality
   metrics. Let me first read the data file to understand its structure."
   ```
   Read({"file_path": ".../repeat_3/airquality.csv", "limit": 20})
   ```
3. **Read the one worked reference script** — "Now let me read the reference
   script to understand the house format pattern."
   ```
   Read({"file_path": ".../repeat_3/.claude/skills/great-tables-house/scripts/house_table.py"})
   ```
4. **Read the rules file** — "Now I understand the house format. Let me read
   the rules file to understand the column patterns:"
   ```
   Read({"file_path": ".../repeat_3/.claude/skills/great-tables-house/references/RULES.md", "limit": 100})
   ```
5. **Only now writes code** — "Now I have enough context. Let me create the
   table script." — `Write(table.py)` importing `PALETTE, frame, finalize,
   band, stripe, stub_tint, heatmap, humanize_labels` from `house_table`,
   the exact module it read in step 3.

Each step's own text narrates *why* it's reaching for the next file — the
model is deciding what it still needs to know, not following a fixed script.
