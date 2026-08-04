"""Ground truth for prompts/hard/sp500_monthly_performance.json.

Data: data/sp500.csv  (~16,607 DAILY OHLCV rows, 1950-01-03 through
      2015-12-31, descending by date in the raw file).
Story: 2010 through 2015, one row per calendar month (6 years x 12 months =
      72 rows), with that month's opening price, closing price, overall
      percent change, average daily volume, and the best/worst single
      trading day within that month.

Two colored measures (the ceiling): `pct_change` (the month's own overall
performance) is the diverging RdYlGn hero measure -- positive=good (green)
is the natural orientation for a stock table, no `reverse` needed. The
{best_day_gain, worst_day_loss} PAIR is colored TOGETHER as ONE measure via
a single `data_color(...)` call (deliberately no leading dot in this
docstring -- the comparator's source-text scan looks for the literal
substring "dot data_color open-paren" anywhere in the file, including
inside a comment, so writing that exact substring here would be misread
as a third color call) spanning both columns (mirrors towny's
"one call, one measure" pattern for its six density columns) -- this keeps
the colored-measure COUNT at exactly 2, not 3, even though six named values
are in play (open, close, pct_change, avg_volume, best day, worst day).
`PuOr` (not `RdYlGn` again) is used for that second measure specifically so
the two colored measures don't collide on the same palette family. open /
close / avg_volume stay plain, uncolored text (not bold) -- with 72 rows and
only 3 of the 6 measure columns "accounted for" (colored) the body is nowhere
near "essentially fully filled," so striping is the correct call, and a
third bold hero would only dilute the two real Big-Color measures without
changing that math.

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
    "colored": ["pct_change", "best_day_gain", "worst_day_loss"],
    "hero_uncolored": ["monthly_open", "monthly_close", "avg_volume"],
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
# pct_change: signed monthly performance -> diverging, symmetric about 0.
pct_m = float(max(abs(final["pct_change"].min()), abs(final["pct_change"].max())))

# best_day_gain / worst_day_loss: one SHARED symmetric domain across both
# columns (they are one measure, colored via one call) so a month's best day
# and worst day render at comparable saturation for comparable magnitude,
# regardless of which column happens to hold the larger absolute value.
day_m = float(max(
    abs(final["best_day_gain"].min()), abs(final["best_day_gain"].max()),
    abs(final["worst_day_loss"].min()), abs(final["worst_day_loss"].max()),
))

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
    # Big Color 1/2: this month's own overall performance, diverging RdYlGn;
    # positive = good (rising close), so no reverse. Symmetric domain keeps
    # 0% at the palette midpoint regardless of which sign is larger here.
    .data_color(
        columns=["pct_change"],
        palette="RdYlGn",
        domain=[-pct_m, pct_m],
        na_color="#808080",
        truncate=False,
    )
    # Big Color 2/2: the best-day/worst-day PAIR, one call, one shared
    # symmetric domain -> ONE colored measure, not two. PuOr (not RdYlGn
    # again) so the two Big-Color measures don't collide on the same
    # palette family.
    .data_color(
        columns=["best_day_gain", "worst_day_loss"],
        palette="PuOr",
        domain=[-day_m, day_m],
        na_color="#808080",
        truncate=False,
    )
    # Heading band: house DEFAULT shade="light" (Big Color present) ->
    # accent_tint. Hue = forest (money/finance, growth), the more visible of
    # the band/stub pairing.
    .tab_options(
        column_labels_background_color="#CFEAD9",
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
    )
    # 72 rows, and only 3 of 6 measure columns are colored (open/close/
    # avg_volume stay plain) -- nowhere near "essentially fully filled," so
    # row striping is the correct call. No stub tint on top of striping: an
    # already-striped body plus a tinted stub would double up on the same
    # visual job (breaking up the grey monotony), so only one of the two is
    # applied here.
    .opt_row_striping()
    # Column-group divider at the one spanner boundary only.
    .tab_style(style=style.borders(sides="right", color="#D0D0D0", weight="1px"), locations=loc.body(columns="avg_volume"))
    .tab_style(style=style.borders(sides="right", color="#D0D0D0", weight="1px"), locations=loc.column_labels(columns="avg_volume"))
    .cols_align(
        align="right",
        columns=["monthly_open", "monthly_close", "pct_change", "avg_volume", "best_day_gain", "worst_day_loss"],
    )
    .tab_source_note(
        source_note=html(
            "Best/worst days use a <b>continuous</b> day-over-day percent change in the closing "
            "price across the full historical series, <b>not reset</b> to zero at each month's "
            "start -- so a month's first trading day still carries its true change from the prior "
            "month's last close."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: daily S&amp;P 500 OHLCV data, 2010–2015, from <code>data/sp500.csv</code>."
        )
    )
)

gt.gtsave(str(_HERE / "sp500_monthly_performance.png"), zoom=2.0, expand=15)
