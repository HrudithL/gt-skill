# Progressive disclosure in action — `prose` skill

Real excerpt from `runs/sweep/20260807_080533_prose_6prompts/prompts/gtcars_hp_price/repeat_1/transcript.json`
(prompt: *"Show me a table of the gt cars with their horsepower and
price."*). The `great-tables` skill is the full 7-step-flowchart variant,
routed through `references/REFERENCE.md` — this excerpt shows the agent
pulling in exactly the reference files the flowchart tells it to, layer by
layer, rather than reading the whole `references/` tree up front.

1. **Invoke the skill**:
   ```
   Skill({"skill": "great-tables"})
   ```
2. **Read the router first, as instructed** — "I'll build a table of gt cars
   with horsepower and price. Let me start by reading the REFERENCE.md file
   as instructed by the skill."
   ```
   Read({"file_path": ".../repeat_1/.claude/skills/great-tables/references/REFERENCE.md"})
   ```
3. **Read the data** — "Now let me read the data file to understand the
   structure":
   ```
   Read({"file_path": ".../repeat_1/gtcars.csv", "limit": ...})
   ```
4. **Follow REFERENCE.md's routing to the specific rules this data needs** —
   "Good! Now let me check the reference files for data cleaning and the
   appropriate big color strategy. Since we have two numeric measures
   (horsepower and price), I need to read the relevant references" — 4
   separate `Read` calls into `references/` for the data-cleaning and
   Big-Color archetype rules that apply to *this* prompt's two numeric
   measures specifically (not every archetype file that exists).
5. **One more targeted read** — "Now I'll read the
   big_color/column_label_emphasis.md to understand the heading band
   decision":
   ```
   Read({"file_path": ".../references/big_color/column_label_emphasis.md"})
   ```
6. **Only now writes code** — "Perfect! Now I understand the data and the
   design rules. Let me write the table.py script" — and the design rationale
   in its own commentary (two neutral-magnitude measures, which Big-Color
   rule applies) traces directly back to the specific files read in steps
   4-5, not the full skill dump.

Six reads, each narrower than the last, each justified by what the previous
one revealed — the router (`REFERENCE.md`) plus the data's own shape is what
decided which archetype file got pulled in, not a fixed reading order.
