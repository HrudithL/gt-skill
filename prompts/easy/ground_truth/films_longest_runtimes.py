"""Ground truth for prompts/easy/films_longest_runtimes.json.

Data: data/films.csv  (1,851 films from the last several decades of
      international cinema; one row per film, with year, director,
      country codes, and `run_time` as a human-formatted string like
      "1h 30m" or "21m" or "2h 8m").
Story: The 10 longest films in the dataset with each film's director and
       country of origin — an "endurance test" leaderboard.

Design decisions:

- Row scope: the prompt names "the 10 longest" explicitly, so
  REQUIRED_INSTRUCTIONS pins row_count=10.
- `run_time` is a STRING in the raw data ("2h 18m", "21m"). Parse it to
  an integer minute count first — great_tables formats numbers, not
  natural-language duration strings — and display the parsed minute
  count as the hero column.
- Stub: `title`. Confirmed unique across the top 10.
- Colored measure: `runtime_min` only — plain positive magnitude and the
  literal ranking criterion -> sequential Blues.
- `director` and `countries_of_origin` stay plain text (descriptive
  attributes, no magnitude).
- Sort: descending by runtime_min.
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub.

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
    "director": ["director", "directed by"],
    "countries_of_origin": [
        "country", "countries", "country of origin", "countries of origin",
        "origin", "country/countries",
    ],
    "runtime_min": [
        "runtime", "run time", "length", "duration", "minutes", "runtime (min)",
        "runtime (minutes)", "runtime in minutes",
    ],
}

REQUIRED_INSTRUCTIONS = {
    "row_count": 10,
}

CANONICAL_MEASURES = {
    "colored": ["runtime_min"],
    "hero_uncolored": [],
}

SEMANTIC_TYPES = {
    "runtime_min": "integer",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "films.csv")


def _parse_runtime(s):
    """Parse a human-formatted runtime string like "2h 18m", "1h 30m", or
    "21m" to an integer minute count. Returns None on anything else.
    """
    if not isinstance(s, str):
        return None
    h = re.search(r"(\d+)\s*h", s)
    m = re.search(r"(\d+)\s*m", s)
    if not h and not m:
        return None
    return (int(h.group(1)) if h else 0) * 60 + (int(m.group(1)) if m else 0)


df["runtime_min"] = df["run_time"].map(_parse_runtime)

top = (
    df.dropna(subset=["runtime_min"])
    .nlargest(10, "runtime_min")
    .loc[:, ["title", "director", "countries_of_origin", "runtime_min"]]
    .reset_index(drop=True)
)
top["runtime_min"] = top["runtime_min"].astype(int)

# ---- Color domain ----------------------------------------------------------
rt_lo = float(top["runtime_min"].min())
rt_hi = float(top["runtime_min"].max())

# ---- Table -----------------------------------------------------------------
gt = (
    GT(top, rowname_col="title")
    .tab_header(
        title="The 10 Longest Films in the Corpus",
        subtitle="Runtime in minutes for the longest films in the dataset, with each film's director and country of origin",
    )
    .tab_stubhead(label="Film")
    .cols_label(
        director="Director",
        countries_of_origin="Country",
        runtime_min="Runtime (minutes)",
    )
    .fmt_integer(columns=["runtime_min"], use_seps=True)
    .sub_missing(columns=["runtime_min"], missing_text="—")
    .data_color(
        columns=["runtime_min"],
        palette="Blues",
        domain=[rt_lo, rt_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_width(cases={
        "title": "260px", "director": "180px",
        "countries_of_origin": "110px", "runtime_min": "140px",
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
    .cols_align(align="right", columns=["runtime_min"])
    .cols_align(align="left", columns=["director", "countries_of_origin"])
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    .tab_source_note(
        source_note=html(
            "Konchalovskiy's <em>Siberiade</em> tops the list at 4 hours 35 minutes — nearly "
            "an hour longer than the average feature. European auteurs dominate the top 10; "
            "seven of the ten were made outside the United States."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: <code>films</code> dataset — international cinema selection "
            "(Posit / great_tables sample data)."
        )
    )
)

gt.gtsave(str(_HERE / "films_longest_runtimes.png"), zoom=2.0, expand=8)
