"""Ground truth for prompts/hard/films_by_decade.json.

Data: data/films.csv  (1,851 films from an international cinema
      corpus; one row per film, with `year`, `title`, `director`,
      `countries_of_origin`, and a text `run_time`).
Story: A decade-by-decade portrait of the corpus -- for the seven
       decades from the 1950s through the 2010s, total film count,
       dominant country of origin, average runtime, and the single
       longest film of the decade with its title and runtime.

Design decisions:

- Row scope: 7 decades (1950s-2010s inclusive) = exactly 7 rows.
  REQUIRED_INSTRUCTIONS pins row_count=7.
- Decade derivation: `decade = (year // 10) * 10`. Films from 2020+ are
  excluded (the prompt names the range explicitly).
- Runtime parsing: `run_time` is a string ("2h 8m"); parse to integer
  minutes before averaging.
- Dominant country: the modal value of `countries_of_origin` per decade
  (the raw field is a comma-separated ISO-2 code list; treat the raw
  string itself as the category, matching how the field is stored --
  "FR" and "FR,IT" are different countries-of-origin credit lines,
  even though they share France).
- Longest film: the single row with the maximum runtime within each
  decade -- both title and its runtime displayed as two adjacent
  columns.
- Stub: `decade_label` ("1950s", "1960s", etc.).
- Colored measures (two, distinct families):
  * `n_films`: sequential Blues -- how "full" each decade's slice of
    the corpus is.
  * `avg_runtime`: sequential Greens -- decades' average runtime has
    inched up steadily (from ~102 min in the 1950s to ~119 min in the
    2010s), so a heatmap makes that trend visible.
  `longest_runtime` (an integer) stays plain -- it's paired with
  `longest_title` as a two-column description of a single film, not a
  cross-decade magnitude to color. `dominant_country` stays plain text.
- Sort: chronological (1950s -> 2010s), the natural reading for a
  time-series digest.
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub.

`autocolor_text=True` on both `data_color()` calls is spelled out
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
    "n_films": ["films", "n films", "count", "film count", "number of films"],
    "dominant_country": [
        "dominant country", "country", "top country", "most common country",
        "modal country", "primary country", "country of origin",
    ],
    "avg_runtime": [
        "avg runtime", "average runtime", "mean runtime", "avg. runtime",
        "avg length", "avg. length",
    ],
    "longest_title": ["longest", "longest film", "longest title", "title", "longest film title"],
    "longest_runtime": [
        "longest runtime", "runtime (longest)", "length of longest",
        "longest (min)", "longest length",
    ],
}

REQUIRED_INSTRUCTIONS = {
    "row_count": 7,
}

CANONICAL_MEASURES = {
    "colored": ["n_films", "avg_runtime"],
    "hero_uncolored": [],
}

SEMANTIC_TYPES = {
    "n_films": "integer",
    "avg_runtime": "number",
    "longest_runtime": "integer",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "films.csv")


def _parse_runtime(s):
    if not isinstance(s, str):
        return None
    h = re.search(r"(\d+)\s*h", s)
    m = re.search(r"(\d+)\s*m", s)
    if not h and not m:
        return None
    return (int(h.group(1)) if h else 0) * 60 + (int(m.group(1)) if m else 0)


df["runtime_min"] = df["run_time"].map(_parse_runtime)
df["decade"] = (df["year"] // 10) * 10

sub = df[(df["decade"] >= 1950) & (df["decade"] <= 2010)].copy()


def _mode_str(s):
    m = s.mode()
    return m.iat[0] if not m.empty else None


agg = (
    sub.groupby("decade")
       .agg(
           n_films=("title", "count"),
           dominant_country=("countries_of_origin", _mode_str),
           avg_runtime=("runtime_min", "mean"),
       )
       .reset_index()
)

# Longest film per decade
longest_idx = sub.dropna(subset=["runtime_min"]).groupby("decade")["runtime_min"].idxmax()
longest = sub.loc[longest_idx, ["decade", "title", "runtime_min"]].rename(
    columns={"title": "longest_title", "runtime_min": "longest_runtime"}
)

by_decade = agg.merge(longest, on="decade")
by_decade["decade_label"] = by_decade["decade"].astype(int).astype(str) + "s"
by_decade["longest_runtime"] = by_decade["longest_runtime"].astype(int)
by_decade = by_decade[[
    "decade_label", "n_films", "dominant_country", "avg_runtime",
    "longest_title", "longest_runtime",
]].reset_index(drop=True)

# ---- Color domains ---------------------------------------------------------
n_lo = float(by_decade["n_films"].min())
n_hi = float(by_decade["n_films"].max())
r_lo = float(by_decade["avg_runtime"].min())
r_hi = float(by_decade["avg_runtime"].max())

# ---- Table -----------------------------------------------------------------
gt = (
    GT(by_decade, rowname_col="decade_label")
    .tab_header(
        title="A Decade-by-Decade Portrait of the Films Corpus",
        subtitle="For each decade from the 1950s through the 2010s: total film count, dominant country of origin, average runtime, and the single longest film of the decade",
    )
    .tab_stubhead(label="Decade")
    .tab_spanner(label="Longest film of the decade", columns=["longest_title", "longest_runtime"])
    .cols_label(
        n_films="Films",
        dominant_country="Top Country",
        avg_runtime="Avg. Runtime (min)",
        longest_title="Title",
        longest_runtime="Runtime (min)",
    )
    .fmt_integer(columns=["n_films", "longest_runtime"], use_seps=True)
    .fmt_number(columns=["avg_runtime"], decimals=1)
    .sub_missing(
        columns=["n_films", "avg_runtime", "longest_runtime"], missing_text="—",
    )
    # Big Color 1/2: n_films -- sequential Blues.
    .data_color(
        columns=["n_films"],
        palette="Blues",
        domain=[n_lo, n_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Big Color 2/2: avg_runtime -- sequential Greens (avoids collision
    # with n_films Blues; a "runtimes creeping up over decades" story).
    .data_color(
        columns=["avg_runtime"],
        palette="Greens",
        domain=[r_lo, r_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_width(cases={
        "decade_label": "90px", "n_films": "80px",
        "dominant_country": "110px", "avg_runtime": "150px",
        "longest_title": "240px", "longest_runtime": "120px",
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
        column_labels_padding_horizontal="6px",
        data_row_padding="5px",
        data_row_padding_horizontal="6px",
        source_notes_padding="6px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    .cols_align(align="right", columns=["n_films", "avg_runtime", "longest_runtime"])
    .cols_align(align="left", columns=["dominant_country", "longest_title"])
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Spanner-boundary divider: leading (before "Longest film" spanner).
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="avg_runtime"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="avg_runtime"),
    )
    .tab_source_note(
        source_note=html(
            "The 1950s dominate on volume (306 films) while runtimes have crept up steadily -- "
            "average runtime rose from 102 to 119 minutes across the seven decades. "
            "Konchalovskiy's <em>Siberiade</em> holds the outright longest at 275 minutes (1979)."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: <code>films</code> dataset -- international cinema selection "
            "(Posit / great_tables sample data). Runtime parsed from the human-formatted "
            "<code>run_time</code> field; dominant country is the modal <code>countries_of_origin</code> "
            "credit line per decade."
        )
    )
)

gt.gtsave(str(_HERE / "films_by_decade.png"), zoom=2.0, expand=8)
