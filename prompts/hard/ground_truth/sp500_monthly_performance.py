"""Ground truth for prompts/hard/sp500_monthly_performance.json.

Data: data/sp500.csv  (~16,607 DAILY OHLCV rows, 1950-01-03 through
      2015-12-31, descending by date in the raw file).
Story: 2010 through 2015, one row per calendar month (6 years x 12 months =
      72 rows), with that month's opening price, closing price, overall
      percent change, average daily volume, and the best/worst single
      trading day within that month.

Color treatment, by author direction (an explicit exception to the house
skill's usual <=2-heatmap-call ceiling -- that ceiling is a rule the
COMPARATOR enforces against CANDIDATE submissions, via CANONICAL_MEASURES
below; it isn't self-applied to this answer key's own rendering):
- `pct_change` (the month's own overall performance): a STRETCH-GOAL
  treatment, NOT a cell heatmap. Only the 5 highest and 5 lowest months
  (of all 72, by signed value) get bold colored TEXT -- green for the top
  5, red for the bottom 5 -- and the other 62 stay plain, unstyled. This
  is explicitly NOT the expectation for an average candidate (picking out
  the top/bottom 5 by value and styling only those cells is a much harder,
  more surgical pattern than a column-wide heatmap); it's the deliberate
  IDEAL this ground truth targets, understanding most candidates will fall
  back to either a full heatmap or no color at all on this column.
- `avg_volume`: a plain sequential Blues heatmap, full [min, max] -- the
  same "simply heatmapped" treatment as any other neutral magnitude
  column in this project (e.g. islands_sizes's `size`).
- `best_day_gain`: its OWN sequential Greens heatmap (darker green =
  bigger single-day gain). Always positive in this 2010-2015 window.
- `worst_day_loss`: its OWN sequential Reds heatmap, `reverse=True` so the
  LARGEST-magnitude loss (the most negative value) lands on the darkest
  red, not the lightest. Always negative in this window.
Gain=green / loss=red keeps the thematic read intuitive while staying
visually distinct from `pct_change`'s red/green TEXT treatment -- a filled
heatmap cell and bold colored text are different enough visual languages
that they don't read as the same signal repeated.

open / close stay plain, uncolored text (not bold, matching the same plain
treatment used for gtcars_hp_price's horsepower) -- with 72 rows and most
of the 6 measure columns now colored in some form, striping still helps on
the two fully-plain columns (open, close) and the 62 unstyled pct_change
rows.

CANONICAL "daily gain/loss" definition (the real derived-computation call
this prompt needs, same spirit as towny's own "canonical fastest-growing"
note): a day's gain/loss is `close.pct_change()` computed CONTINUOUSLY
across the FULL multi-year, date-sorted series -- NOT reset to NaN at the
start of each month. A stock does not stop existing between months, so the
first trading day of e.g. March still has a real percent change relative to
February's last close, and that value is exactly as eligible to be that
month's "highest single-day gain/loss" as any other day in March. Per month,
the "highest single-day gain" is the MAX of that daily-change series among
days whose date falls in the month; "highest single-day loss" is the MIN of
the same series over the same days. This is computed on the full sorted
series BEFORE filtering to 2010-2015 (so the January-2010 boundary day still
has a valid change relative to December 2009), then the resulting per-day
column is filtered down to the 2010-2015 window before grouping.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from great_tables import GT, html, loc, style

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent.parent

# ---- Ground-truth comparator metadata --------------------------------------
# Read directly by scripts/gt_compare.py via module import. Keep these as
# literal dict/list assignments (no computation) so they're both a plain-text
# answer key a human can review and something a script can load without exec
# risk beyond what already happens to render the table.

# Acceptable label synonyms per underlying derived column. Wording is free;
# the label just has to name the right concept. `month_label` (the stub) is
# intentionally omitted, the same way towny's stub column ("name") is never
# a `cols_label` key -- the stub's header comes from `tab_stubhead`, not
# `cols_label`, so it never appears in the parsed label signature anyway.
LABEL_SYNONYMS = {
    "monthly_open": ["open", "opening price"],
    "monthly_close": ["close", "closing price"],
    "pct_change": ["% change", "percent change", "monthly change", "monthly performance"],
    "avg_volume": ["avg daily volume", "average daily volume", "volume"],
    "best_day_gain": ["best day", "highest gain", "single-day gain"],
    "worst_day_loss": ["worst day", "highest loss", "single-day loss"],
}

# Only present when the PROMPT TEXT explicitly demands something structural.
# "2010 through 2015" + "monthly" is a direct mathematical consequence (6
# years x 12 months = 72 rows), not a subjective pick, so row_count is set.
# No "sort" key: rows are grouped by year (groupname_col), and a strict
# global monotonicity check can interact badly with grouped display (same
# reasoning the gtcars_top10_by_country ground truth uses) -- chronological
# order falls out of the groupby itself, but isn't asserted here. No
# "grouping" key either: the prompt never explicitly demands grouping by
# year, so it stays a pure style choice, not a graded requirement.
REQUIRED_INSTRUCTIONS = {
    "row_count": 72,
}

# Keyword-presence check for the caption/subtitle overlap rule. The caption
# states the daily-gain/loss methodology (the thing that makes this table's
# numbers reproducible); the subtitle only describes organization/scope, so
# it must never quote the methodology phrases the caption owns.
CAPTION_KEYWORDS = {
    "caption_should_mention": ["continuous", "day-over-day", "not reset"],
    "subtitle_should_not_duplicate": ["continuous day-over-day", "not reset"],
}

# Underlying derived column(s) that are the canonical colored measure(s),
# used for value-based matching -- NOT the rendered column name/label.
CANONICAL_MEASURES = {
    "colored": ["pct_change", "avg_volume", "best_day_gain", "worst_day_loss"],
    "hero_uncolored": ["monthly_open", "monthly_close"],
}

# Semantic type per rendered column, for the fmt_* correctness check.
SEMANTIC_TYPES = {
    "monthly_open": "currency",
    "monthly_close": "currency",
    "pct_change": "percent",
    "avg_volume": "number",
    "best_day_gain": "percent",
    "worst_day_loss": "percent",
}

# ---- Data prep -----------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "sp500.csv", parse_dates=["date"])

# Raw file is DESCENDING by date -- sort ascending first so "first"/"last"
# per month and the continuous day-over-day change below are both correct.
df = df.sort_values("date", kind="mergesort").reset_index(drop=True)

# Canonical daily gain/loss (see module docstring): continuous day-over-day
# percent change of the close, computed on the FULL sorted series -- before
# any filtering, so a month's first trading day still carries its true
# change relative to the prior month's last close, not an artificial NaN.
df["daily_change_pct"] = df["close"].pct_change()

df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

# Filter to 2010 through 2015 inclusive -- AFTER the continuous daily-change
# column is computed, and EARLY (before any expensive grouping) so the
# ~16,607-row full history is never re-touched again below.
sub = df[df["year"].between(2010, 2015)]

monthly = (
    sub.groupby(["year", "month"], sort=True)
    .agg(
        monthly_open=("open", "first"),
        monthly_close=("close", "last"),
        avg_volume=("volume", "mean"),
        best_day_gain=("daily_change_pct", "max"),
        worst_day_loss=("daily_change_pct", "min"),
    )
    .reset_index()
)
monthly["pct_change"] = (monthly["monthly_close"] - monthly["monthly_open"]) / monthly["monthly_open"]
# Billions of shares -- far more legible than a raw 10-digit share count.
monthly["avg_volume"] = monthly["avg_volume"] / 1e9
monthly["month_label"] = pd.to_datetime(
    monthly["year"].astype(str) + "-" + monthly["month"].astype(str) + "-01"
).dt.strftime("%b %Y")

final = monthly[
    [
        "month_label", "year",
        "monthly_open", "monthly_close", "pct_change", "avg_volume",
        "best_day_gain", "worst_day_loss",
    ]
].reset_index(drop=True)

# ---- Color domains ---------------------------------------------------------
# pct_change: NOT a full-column heatmap -- see module docstring. Only the
# top-5 highest and bottom-5 lowest months (by signed value, across all 72
# rows) get bold colored TEXT; the other 62 stay plain. Row positions are
# `final`'s own 0..71 index (reset_index(drop=True) above), directly usable
# with `loc.body(rows=...)`.
pct_change_top5_rows = final.nlargest(5, "pct_change").index.tolist()
pct_change_bottom5_rows = final.nsmallest(5, "pct_change").index.tolist()

# avg_volume: plain sequential magnitude -> Blues, full [min, max].
vol_lo = float(final["avg_volume"].min())
vol_hi = float(final["avg_volume"].max())

# best_day_gain / worst_day_loss: by author direction, each gets its OWN
# sequential domain (not a shared symmetric one) -- see module docstring.
# Both are one-directional in this 2010-2015 window (gain always positive,
# loss always negative), so a plain [min, max] per column is the honest read.
gain_lo = float(final["best_day_gain"].min())
gain_hi = float(final["best_day_gain"].max())
loss_lo = float(final["worst_day_loss"].min())
loss_hi = float(final["worst_day_loss"].max())

# ---- Table -----------------------------------------------------------------
gt = (
    GT(final, rowname_col="month_label", groupname_col="year")
    .tab_header(
        title="S&P 500 Monthly Performance, 2010–2015",
        subtitle="Six full years of trading, grouped by year, with each month's open, close, "
                  "overall percent change, average daily volume, and the best and worst single "
                  "trading day within that month",
    )
    .tab_stubhead(label="Month")
    .tab_spanner(label="Single-day extremes within the month", columns=["best_day_gain", "worst_day_loss"])
    .cols_label(
        monthly_open="Open",
        monthly_close="Close",
        pct_change="Monthly % Change",
        avg_volume="Avg Daily Volume (B sh)",
        best_day_gain=html("Best Day<br>(gain)"),
        worst_day_loss=html("Worst Day<br>(loss)"),
    )
    .fmt_currency(columns=["monthly_open", "monthly_close"], decimals=2)
    .fmt_percent(columns=["pct_change"], decimals=1, force_sign=True)
    .fmt_number(columns=["avg_volume"], decimals=2)
    .fmt_percent(columns=["best_day_gain", "worst_day_loss"], decimals=1, force_sign=True)
    .sub_missing(
        columns=["monthly_open", "monthly_close", "pct_change", "avg_volume", "best_day_gain", "worst_day_loss"],
        missing_text="—",
    )
    # Monthly % Change: STRETCH-GOAL treatment, by author direction (see
    # module docstring) -- no cell heatmap at all. Only the single most
    # extreme 5 up-months and 5 down-months (of all 72) get bold colored
    # text; the other 62 stay plain, unstyled numbers.
    .tab_style(
        style=style.text(color="#1A7A34", weight="bold"),
        locations=loc.body(columns="pct_change", rows=pct_change_top5_rows),
    )
    .tab_style(
        style=style.text(color="#C0392B", weight="bold"),
        locations=loc.body(columns="pct_change", rows=pct_change_bottom5_rows),
    )
    # Avg Daily Volume: plain sequential Blues heatmap, full [min, max].
    .data_color(
        columns=["avg_volume"],
        palette="Blues",
        domain=[vol_lo, vol_hi],
        na_color="#808080",
        truncate=False,
    )
    # Best day: its own sequential Greens heatmap -- darker = bigger gain.
    .data_color(
        columns=["best_day_gain"],
        palette="Greens",
        domain=[gain_lo, gain_hi],
        na_color="#808080",
        truncate=False,
    )
    # Worst day: its own sequential Reds heatmap, reverse=True so the
    # LARGEST-magnitude loss (most negative) lands on the darkest red.
    .data_color(
        columns=["worst_day_loss"],
        palette="Reds",
        domain=[loss_lo, loss_hi],
        na_color="#808080",
        truncate=False,
        reverse=True,
    )
    # Columns sized to their own content (+ a small buffer), not left to
    # auto-stretch -- author-directed.
    .cols_width(cases={
        "month_label": "90px", "monthly_open": "90px", "monthly_close": "90px",
        "pct_change": "110px", "avg_volume": "130px",
        "best_day_gain": "100px", "worst_day_loss": "100px",
    })
    # Heading band -- DEEP navy (#08306B), bold, white text: the same
    # header/stub branding used across every table in this project, by
    # author direction, decoupled from this table's own RdYlGn/Greens/Reds
    # heatmap hues.
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
        # Group-header emphasis (house group_emphasis()): bold weight + the
        # structural rule above/below each year's header row, deliberately
        # NO background fill -- a section break, not a result worth its own
        # highlight (that's the summary/total row's job, which this table
        # doesn't have).
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
        # Tighter padding throughout -- less whitespace per cell, by author
        # direction.
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    # Stub tint -- washed navy, matching every other table's stub treatment,
    # applied TOGETHER with row striping (same combined treatment used on
    # gtcars_top10_by_country, by author direction).
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    # 72 rows, and only 3 of 6 measure columns are colored (open/close/
    # avg_volume stay plain) -- nowhere near "essentially fully filled," so
    # row striping is the correct call.
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Column-group divider at the one spanner boundary only.
    .tab_style(style=style.borders(sides="right", color="#D0D0D0", weight="1px"), locations=loc.body(columns="avg_volume"))
    .tab_style(style=style.borders(sides="right", color="#D0D0D0", weight="1px"), locations=loc.column_labels(columns="avg_volume"))
    .cols_align(
        align="right",
        columns=["monthly_open", "monthly_close", "pct_change", "avg_volume", "best_day_gain", "worst_day_loss"],
    )
    .tab_source_note(
        source_note=html(
            "Best/worst-day figures use a <b>continuous</b> <b>day-over-day</b> price change, "
            "<b>not reset</b> at each month's start."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: daily S&amp;P 500 OHLCV data, 2010–2015, from <code>data/sp500.csv</code>."
        )
    )
)

gt.gtsave(str(_HERE / "sp500_monthly_performance.png"), zoom=2.0, expand=8)
