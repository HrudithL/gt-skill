"""Ground truth for prompts/medium/films_prolific_directors.json.

Data: data/films.csv  (1,851 films from a curated international cinema
      corpus; one row per film, with `year`, `title`, `director`,
      `countries_of_origin`, and a text `run_time` like "1h 30m").
Story: The 10 directors with the most films in the dataset, with each
       director's average runtime and the years spanning their earliest
       and latest film — a "career volume" leaderboard.

Design decisions:

- Row scope: the prompt names "the 10 most prolific" explicitly, so
  REQUIRED_INSTRUCTIONS pins row_count=10.
- Prolific = film count in the dataset. Ranking metric is the number of
  distinct titles credited to that director.
- Runtime parsing: `run_time` is a string ("2h 8m", "21m"). Parse to
  integer minutes per film, then average per director.
- Director aggregation: the raw `director` field sometimes credits a
  directing DUO as a joint value ("Jean-Pierre Dardenne, Luc Dardenne");
  such joint credits are treated as a single directing entity, which
  matches how the field's own data models the credit.
- Stub: `director`.
- Colored measure: `films` — the "prolific" ranking criterion, plain
  positive count -> sequential Greens (the house sequential.positive
  palette; "more films = more prolific" is directly "more is more").
- `avg_runtime` / `first_year` / `last_year` stay plain (secondary
  details the prompt names but not the color hero).
- Sort: descending by films.
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub —
  decoupled from the Greens heatmap hue.

`autocolor_text=True` on the `data_color()` call is spelled out
explicitly even though it's great_tables' own default, for the same
self-documenting-intent reason `na_color`/`truncate` are always spelled
out here.
"""
from pathlib import Path
import re

import pandas as pd
from great_tables import GT, html, loc, style

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent.parent

# ---- Ground-truth comparator metadata --------------------------------------
LABEL_SYNONYMS = {
    "films": ["films", "film count", "number of films", "count", "films directed"],
    "avg_runtime": [
        "avg runtime", "average runtime", "avg. runtime", "mean runtime",
        "avg length", "avg. length", "runtime",
    ],
    "first_year": ["first year", "earliest", "earliest year", "debut year", "debut", "from"],
    "last_year": ["last year", "latest", "latest year", "most recent", "to"],
}

REQUIRED_INSTRUCTIONS = {
    "row_count": 10,
}

CANONICAL_MEASURES = {
    "colored": ["films"],
    "hero_uncolored": [],
}

SEMANTIC_TYPES = {
    "films": "integer",
    "avg_runtime": "number",
    "first_year": "integer",
    "last_year": "integer",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "films.csv")


def _parse_runtime(s):
    """Human "1h 30m" -> integer minutes, or None on anything else."""
    if not isinstance(s, str):
        return None
    h = re.search(r"(\d+)\s*h", s)
    m = re.search(r"(\d+)\s*m", s)
    if not h and not m:
        return None
    return (int(h.group(1)) if h else 0) * 60 + (int(m.group(1)) if m else 0)


df["runtime_min"] = df["run_time"].map(_parse_runtime)

top = (
    df.groupby("director")
      .agg(
          films=("title", "count"),
          avg_runtime=("runtime_min", "mean"),
          first_year=("year", "min"),
          last_year=("year", "max"),
      )
      .sort_values("films", ascending=False)
      .head(10)
      .reset_index()
)
top["first_year"] = top["first_year"].astype(int)
top["last_year"] = top["last_year"].astype(int)

# ---- Color domain ----------------------------------------------------------
f_lo = float(top["films"].min())
f_hi = float(top["films"].max())

# ---- Table -----------------------------------------------------------------
gt = (
    GT(top, rowname_col="director")
    .tab_header(
        title="The 10 Most Prolific Directors in the Films Corpus",
        subtitle="Total film count, average runtime, and the years spanning each director's earliest and latest work in the dataset",
    )
    .tab_stubhead(label="Director")
    .cols_label(
        films="Films",
        avg_runtime="Avg. Runtime (min)",
        first_year="Earliest",
        last_year="Latest",
    )
    .fmt_integer(columns=["films", "first_year", "last_year"])
    .fmt_number(columns=["avg_runtime"], decimals=1)
    .sub_missing(columns=["films", "avg_runtime", "first_year", "last_year"], missing_text="—")
    # Big Color 1/1: films -- "prolific" ranking hero, plain positive
    # count, sequential Greens (house sequential.positive palette).
    .data_color(
        columns=["films"],
        palette="Greens",
        domain=[f_lo, f_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_width(cases={
        "director": "280px", "films": "90px",
        "avg_runtime": "160px", "first_year": "100px", "last_year": "100px",
    })
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        column_labels_border_bottom_style="solid",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        table_border_top_style="solid", table_border_top_color="#CCCCCC", table_border_top_width="1px",
        table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
        table_border_left_style="solid", table_border_left_color="#CCCCCC", table_border_left_width="1px",
        table_border_right_style="solid", table_border_right_color="#CCCCCC", table_border_right_width="1px",
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    .cols_align(align="right", columns=["films", "avg_runtime", "first_year", "last_year"])
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    .tab_source_note(
        source_note=html(
            "Ken Loach tops the list with 15 credited films spanning 42 years (1981-2023) — "
            "the longest active career on the leaderboard. The Dardenne brothers appear as a "
            "single directing duo, matching the source data's own credit format."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: <code>films</code> dataset — international cinema selection "
            "(Posit / great_tables sample data). Runtime parsed from the human-formatted "
            "<code>run_time</code> field."
        )
    )
)

gt.gtsave(str(_HERE / "films_prolific_directors.png"), zoom=2.0, expand=8)
