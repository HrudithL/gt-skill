"""Ground truth for prompts/hard/sp500_yearly_summary.json.

Data: data/sp500.csv  (~16,607 daily OHLCV rows, 1950-01-03 through
      2015-12-31, descending in the raw file).
Story: 15 full calendar years of S&P 500 trading (2000-2014), with each
       year's opening and closing price, overall percent change, average
       daily volume, and the best and worst single-day return within
       that year.

Design decisions:

- Row scope: 2000 through 2014 inclusive = 15 rows. REQUIRED_INSTRUCTIONS
  pins row_count=15.
- Canonical daily gain/loss: continuous day-over-day percent change of
  close, computed on the FULL sorted series BEFORE filtering (same
  convention sp500_monthly_performance.py's canonical definition uses).
  A year's first trading day carries its true change relative to the
  prior year's last close, not an artificial NaN.
- Stub: `year_label` -- the year as a string ("2000", ...).
- Colored measures (three, with distinct hue families to avoid
  collision):
  * `yr_pct_change`: DIVERGING RdYlGn -- the yearly performance is
    genuinely signed (2000-2002 lost, 2003 gained, 2008 lost heavily,
    ...); the check would flag a sequential palette here as a shape
    mismatch. Symmetric domain, positive=good (no reverse), force_sign
    on the fmt_percent call per the house rule for a signed percent.
  * `avg_vol`: sequential BLUES -- plain positive magnitude (billions of
    shares).
  * `best_day` and `worst_day`: their OWN sequential palettes, gain
    green / loss red, matching sp500_monthly_performance.py's
    convention exactly. Both are one-directional within the display
    slice (best_day always positive, worst_day always negative), so
    each gets its own [min, max] domain rather than a shared symmetric
    one.
    - `best_day`: sequential Greens (darker = bigger gain).
    - `worst_day`: sequential Reds with reverse=True (darkest red on
      the LARGEST-magnitude loss / most-negative value).
  yr_open and yr_close stay plain -- endpoints, not the color story
  (per sp500_monthly_performance.py's own treatment of open/close).
- Sort: chronological (2000 -> 2014).
- Column layout: a spanner "Single-day extremes within the year" over
  best_day + worst_day, matching sp500_monthly_performance.py's
  identical spanner. Spanner-boundary divider on avg_vol (before the
  spanned block starts).
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub --
  decoupled from the several heatmap hues.

`autocolor_text=True` on every `data_color()` call is spelled out
explicitly even though it's great_tables' own default, for the same
self-documenting-intent reason `na_color`/`truncate` are always spelled
out here.
"""
from pathlib import Path

import pandas as pd
from great_tables import GT, html, loc, style

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent.parent

# ---- Ground-truth comparator metadata --------------------------------------
LABEL_SYNONYMS = {
    "yr_open": ["open", "opening price", "year open"],
    "yr_close": ["close", "closing price", "year close"],
    "yr_pct_change": ["% change", "percent change", "yearly change", "annual change", "year change"],
    "avg_vol": ["avg daily volume", "average daily volume", "avg volume", "volume"],
    "best_day": ["best day", "highest gain", "best gain", "peak gain", "single-day gain"],
    "worst_day": ["worst day", "worst loss", "biggest loss", "single-day loss"],
}

REQUIRED_INSTRUCTIONS = {
    "row_count": 15,
}

CANONICAL_MEASURES = {
    "colored": ["yr_pct_change", "avg_vol", "best_day", "worst_day"],
    "hero_uncolored": ["yr_open", "yr_close"],
}

SEMANTIC_TYPES = {
    "yr_open": "currency",
    "yr_close": "currency",
    "yr_pct_change": "percent",
    "avg_vol": "number",
    "best_day": "percent",
    "worst_day": "percent",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "sp500.csv", parse_dates=["date"])
df = df.sort_values("date", kind="mergesort").reset_index(drop=True)

# Continuous day-over-day change, computed on the FULL sorted series --
# not reset at each year's start, so the first trading day of e.g. 2010
# still carries its true change relative to Dec 2009's last close.
df["daily_change_pct"] = df["close"].pct_change()
df["year"] = df["date"].dt.year

sub = df[df["year"].between(2000, 2014)]

yearly = (
    sub.groupby("year", sort=True)
       .agg(
           yr_open=("open", "first"),
           yr_close=("close", "last"),
           avg_vol=("volume", "mean"),
           best_day=("daily_change_pct", "max"),
           worst_day=("daily_change_pct", "min"),
       )
       .reset_index()
)
yearly["yr_pct_change"] = (yearly["yr_close"] - yearly["yr_open"]) / yearly["yr_open"]
yearly["avg_vol"] = yearly["avg_vol"] / 1e9  # billions of shares
yearly["year_label"] = yearly["year"].astype(int).astype(str)

final = yearly[[
    "year_label", "yr_open", "yr_close", "yr_pct_change",
    "avg_vol", "best_day", "worst_day",
]].reset_index(drop=True)

# ---- Color domains ---------------------------------------------------------
pct_lo = float(final["yr_pct_change"].min())
pct_hi = float(final["yr_pct_change"].max())
pct_m = max(abs(pct_lo), abs(pct_hi))

vol_lo = float(final["avg_vol"].min())
vol_hi = float(final["avg_vol"].max())

best_lo = float(final["best_day"].min())
best_hi = float(final["best_day"].max())

worst_lo = float(final["worst_day"].min())
worst_hi = float(final["worst_day"].max())

# ---- Table -----------------------------------------------------------------
gt = (
    GT(final, rowname_col="year_label")
    .tab_header(
        title="S&P 500 Yearly Performance, 2000-2014",
        subtitle="Fifteen years of trading with each year's open, close, overall percent change, average daily volume, and the best and worst single trading day within that year",
    )
    .tab_stubhead(label="Year")
    .tab_spanner(label="Single-day extremes within the year", columns=["best_day", "worst_day"])
    .cols_label(
        yr_open="Open",
        yr_close="Close",
        yr_pct_change="Yearly % Change",
        avg_vol="Avg Daily Volume (B sh)",
        best_day=html("Best Day<br>(gain)"),
        worst_day=html("Worst Day<br>(loss)"),
    )
    .fmt_currency(columns=["yr_open", "yr_close"], decimals=2)
    .fmt_percent(columns=["yr_pct_change"], decimals=1, force_sign=True)
    .fmt_number(columns=["avg_vol"], decimals=2)
    .fmt_percent(columns=["best_day", "worst_day"], decimals=1, force_sign=True)
    .sub_missing(
        columns=["yr_open", "yr_close", "yr_pct_change", "avg_vol", "best_day", "worst_day"],
        missing_text="—",
    )
    # Big Color 1/4: yearly % change -- DIVERGING RdYlGn, symmetric.
    .data_color(
        columns=["yr_pct_change"],
        palette="RdYlGn",
        domain=[-pct_m, pct_m],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Big Color 2/4: avg daily volume -- sequential Blues.
    .data_color(
        columns=["avg_vol"],
        palette="Blues",
        domain=[vol_lo, vol_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Big Color 3/4: best day -- own sequential Greens, darker = bigger gain.
    .data_color(
        columns=["best_day"],
        palette="Greens",
        domain=[best_lo, best_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Big Color 4/4: worst day -- own sequential Reds, reverse=True so the
    # LARGEST-magnitude loss (most negative) lands on the darkest red.
    .data_color(
        columns=["worst_day"],
        palette="Reds",
        domain=[worst_lo, worst_hi],
        na_color="#808080",
        truncate=False,
        reverse=True,
        autocolor_text=True,
    )
    .cols_width(cases={
        "year_label": "70px", "yr_open": "90px", "yr_close": "90px",
        "yr_pct_change": "120px", "avg_vol": "140px",
        "best_day": "100px", "worst_day": "100px",
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
    .cols_align(
        align="right",
        columns=["yr_open", "yr_close", "yr_pct_change", "avg_vol", "best_day", "worst_day"],
    )
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Spanner-boundary divider: leading (before the "Single-day extremes" spanner).
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="avg_vol"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="avg_vol"),
    )
    .tab_source_note(
        source_note=html(
            "Best/worst-day figures use a <b>continuous</b> day-over-day price change, "
            "<b>not reset</b> at each year's start. The 2008 crisis lands hardest: -38.5% for the "
            "year, with the biggest single-day gain (+11.6%) and the biggest single-day loss "
            "(-9.0%) of the entire 15-year window both landing in that one year."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: daily S&amp;P 500 OHLCV data, 2000-2014, from <code>data/sp500.csv</code>."
        )
    )
)

gt.gtsave(str(_HERE / "sp500_yearly_summary.png"), zoom=2.0, expand=8)
