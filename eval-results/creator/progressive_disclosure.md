# Progressive disclosure in action — `creator` skill

Real excerpt from `runs/sweep/20260807_080537_creator_6prompts/prompts/gtcars_hp_price/repeat_1/transcript.json`
(prompt: *"Show me a table of the gt cars with their horsepower and
price."*). `creator` mounts a skill-creator-produced *candidate* skill
(verbatim as `great-tables`) for A/B evaluation against the promoted one — so
this excerpt also shows the weaker side of progressive disclosure: the model
invokes the skill and reads reference material, but less systematically than
`prose`/`scripts` (a pattern that shows up again in this skill's lower,
noisier comparator scores — see `comparator_score.png`).

1. **Reads the data first, skill second** — "I'll create a polished table of
   gt cars showing horsepower and price. Let me start by reading the data
   file to understand its structure."
   ```
   Read({"file_path": ".../repeat_1/gtcars.csv"})
   ```
2. **Then invokes the skill** — "Now I'll invoke the great-tables skill to
   create a polished table with horsepower and price data."
   ```
   Skill({"skill": "great-tables"})
   ```
3. **Reads two reference files** — "I'll read the reference files to
   understand the house style, then create a polished table."
   ```
   Read({"file_path": ".../.claude/skills/great-tables/references/formatting_decisions.md"})
   Read({"file_path": ".../.claude/skills/great-tables/references/REFERENCE.md"})
   ```
   (Read in that order — `REFERENCE.md`, the router other variants read
   *first*, comes second here.)
4. **Falls back to exploring the directory rather than following a router** —
   "Let me check what's in the great-tables skill directory:"
   ```
   Glob({"pattern": ".claude/skills/great-tables/**/*.md"})
   ```
5. **Writes code** without reading any of the archetype-specific rule files
   `prose`/`scripts` pulled in for this same prompt (Big-Color, column-label
   emphasis) — the disclosure happened, but stopped one layer shallower.

Disclosure still occurs (skill -> 2 reference reads -> a directory probe),
just less targeted than the router-driven reads in `prose`/`scripts` — a
concrete, mechanical difference this excerpt makes visible, not just an
impression from the score gap.
