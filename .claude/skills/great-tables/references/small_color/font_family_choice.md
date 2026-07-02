# Small Color — Font Family Choice

Swap the table's font family to one of the `system_fonts()` stacks so the tone of the table matches its content. Font choice is *color-adjacent*: it changes the perceived weight, warmth, and formality of every value.

## When to use

- The default system font feels generic and the table has an editorial or brand context (report, dashboard, publication).
- The content warrants a specific tone: humanist for warmer/narrative, neo-grotesque for clean/technical, monospace for code or aligned digits.
- You are not overriding font in every other CSS layer (the table lives in a container that will pass its font through).

## Recipe

```python
from great_tables import GT, system_fonts

gt = (
    GT(df)
    .opt_table_font(font=system_fonts("humanist"))       # warmer, editorial
)
```

Other useful stacks:

```python
system_fonts("neo-grotesque")        # clean, modern (Helvetica-family)
system_fonts("transitional")         # classic serif alternative
system_fonts("monospace-code")       # for code samples, aligned digits
system_fonts("rounded-sans")         # friendly, soft
```

## Rules

- **Pick one stack for the whole table.** Do not mix stacks per column or per row.
- **Don't ship an untested named font** (`font="Comic Sans MS"`). Use `system_fonts(...)` stacks so the table renders consistently across machines.
- **Match the tone to the content**: financial/scientific → neo-grotesque or transitional; narrative/editorial → humanist; code/API tables → monospace-code.
- **Do not** change the font just because the default looks fine — an unmotivated font change reads as inconsistency, not polish.

## Counts as

One Small Color treatment.
