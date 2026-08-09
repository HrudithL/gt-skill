import pandas as pd
import numpy as np
from great_tables import GT, style, loc, html
from gt_consistency import band, heatmap, stripe, frame, finalize, PALETTE

df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)

# Filter to 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]

# Group by year-month
df["period"] = df["date"].dt.to_period("M")
monthly = df.groupby("period", sort=True).agg({
    "open": "first",
    "close": "last",
    "volume": "mean",
    "high": "max",
    "low": "min",
}).reset_index()

# Calculate percent change (first close / first open)
monthly["percent_change"] = (monthly["close"] - monthly["open"]) / monthly["open"]

# Find highest single-day gain and loss within each month
daily_change = df.groupby("period").apply(
    lambda g: pd.Series({
        "highest_gain": ((g["close"] - g["open"]) / g["open"]).max(),
        "worst_loss": ((g["close"] - g["open"]) / g["open"]).min(),
    })
).reset_index()

monthly = monthly.merge(daily_change, on="period")

# Format period as "Mon YYYY" for stub display
monthly["period_label"] = monthly["period"].dt.strftime("%b %Y")

# Rename columns for display
display_df = monthly[[
    "period_label",
    "open",
    "close",
    "percent_change",
    "volume",
    "highest_gain",
    "worst_loss",
]].copy()
display_df.columns = [
    "period",
    "open_price",
    "close_price",
    "percent_change",
    "avg_daily_volume",
    "highest_day_gain",
    "worst_day_loss",
]

# Compute symmetric domain for diverging fill (highest_gain and worst_loss together)
all_pct = np.concatenate([
    display_df["percent_change"].dropna().values,
    display_df["highest_day_gain"].dropna().values,
    display_df["worst_day_loss"].dropna().values,
])
M = float(np.max(np.abs(all_pct)))

gt = GT(display_df, rowname_col="period")

# Step 3: Big Color — diverging for percent changes (signed measures)
# Color all three signed percent columns together under one domain
gt = heatmap(
    gt,
    columns=["percent_change", "highest_day_gain", "worst_day_loss"],
    kind="diverging",
    hue="default",
    domain=[-M, M],
)

# Step 4: Heading band — light with Navy hue (Big Color present)
gt = band(gt, shade="light", hue="navy")

# Step 5: Small Color polish
# (a) Cell borders
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# (b) Striping for readability (≥10 rows)
gt = stripe(gt)

# Step 5: Formatting
gt = (
    gt
    .fmt_currency(columns=["open_price", "close_price"], currency="USD", decimals=2)
    .fmt_currency(columns=["avg_daily_volume"], currency="USD", decimals=0)
    .fmt_percent(
        columns=["percent_change", "highest_day_gain", "worst_day_loss"],
        decimals=2,
        force_sign=True,
    )
)

# Step 6: Titles and annotations
gt = (
    gt
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="2010–2015: Opening & closing prices, percent change, and daily extremes",
    )
    .tab_source_note(
        html(
            "Percent change calculated from monthly opening to closing price. "
            "Highest day gain and worst day loss reflect single-day intraday movement (close − open) "
            "as a percent of opening price within each month."
        )
    )
    .tab_stubhead(label="Month")
)

# Global constants: frame and render parameters
gt = frame(gt)

# Step 7: Render
finalize(gt, "table.png")
