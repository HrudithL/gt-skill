import pandas as pd
import numpy as np
from great_tables import GT, style, loc, md
from gt_consistency import frame, hairlines, finalize, heatmap, band, stripe, stub_tint

# Step 1: Load and clean data
df_raw = pd.read_csv("sp500.csv")
df_raw["date"] = pd.to_datetime(df_raw["date"])
df_raw = df_raw.sort_values("date").reset_index(drop=True)

# Filter to 2010-2015
start_date = pd.Timestamp("2010-01-01")
end_date = pd.Timestamp("2015-12-31")
df_raw = df_raw[(df_raw["date"] >= start_date) & (df_raw["date"] <= end_date)].copy()

# Step 2: Aggregate to monthly summary
df_raw["year_month"] = df_raw["date"].dt.to_period("M")

monthly_data = []
for period, group in df_raw.groupby("year_month", sort=True):
    group = group.sort_values("date")
    opening_price = group.iloc[0]["open"]
    closing_price = group.iloc[-1]["close"]
    pct_change = ((closing_price - opening_price) / opening_price) * 100 if opening_price > 0 else np.nan
    avg_volume = group["volume"].mean()

    # Single-day gains/losses within the month
    daily_gains = group["close"] - group["open"]
    highest_gain = daily_gains.max()
    largest_loss = daily_gains.min()

    monthly_data.append({
        "Period": period.strftime("%b %Y"),
        "Opening Price": opening_price,
        "Closing Price": closing_price,
        "Percent Change": pct_change,
        "Avg Daily Volume": avg_volume,
        "Highest Single-Day Gain": highest_gain,
        "Largest Single-Day Loss": largest_loss,
    })

df = pd.DataFrame(monthly_data)

# Convert volume to millions for readability
df["Avg Daily Volume"] = df["Avg Daily Volume"] / 1e6

# Step 3: Create GT table
gt = GT(df, rowname_col="Period")

# Format columns
gt = (
    gt.fmt_currency(
        columns=["Opening Price", "Closing Price"],
        currency="USD",
        decimals=2
    )
    .fmt_number(
        columns=["Avg Daily Volume"],
        decimals=1,
        use_seps=True
    )
    .fmt_currency(
        columns=["Highest Single-Day Gain", "Largest Single-Day Loss"],
        currency="USD",
        decimals=2
    )
    .fmt_percent(
        columns=["Percent Change"],
        decimals=1,
        scale_values=False,
        force_sign=True
    )
)

# Step 3b: Add column groups (spanners)
gt = (
    gt.tab_spanner(label="Daily", columns=["Opening Price", "Closing Price", "Percent Change"])
    .tab_spanner(label="Volume & Daily Range", columns=["Avg Daily Volume", "Highest Single-Day Gain", "Largest Single-Day Loss"])
)

# Step 3: Big Color — heatmap colored measures
# Percent Change: diverging (signed)
gt = heatmap(gt, "Percent Change", kind="diverging", hue="default")

# Avg Daily Volume: sequential (magnitude)
gt = heatmap(gt, "Avg Daily Volume", kind="sequential", hue="neutral")

# Highest Single-Day Gain & Largest Single-Day Loss: sequential (magnitudes)
gt = heatmap(gt, "Highest Single-Day Gain", kind="sequential", hue="positive")
gt = heatmap(gt, "Largest Single-Day Loss", kind="sequential", hue="warning_alt")

# Step 4: Heading band
gt = band(gt)

# Step 5: Small Color polish
gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)
gt = hairlines(gt)

# Column dividers at spanner seams
gt = (
    gt.tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="Percent Change"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="Percent Change"),
    )
)

# Compact layout with col widths
gt = gt.cols_width(cases={
    "Opening Price": "110px",
    "Closing Price": "110px",
    "Percent Change": "100px",
    "Avg Daily Volume": "120px",
    "Highest Single-Day Gain": "130px",
    "Largest Single-Day Loss": "130px",
})

gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Step 6: Titles & annotations
gt = (
    gt.tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="2010–2015"
    )
    .tab_source_note(
        source_note="Percent Change = (Closing Price − Opening Price) / Opening Price. Highest/Lowest = intraday close − open difference."
    )
    .tab_source_note(
        source_note="Source: Historical S&P 500 data."
    )
)

# Finalize and render
finalize(gt, "table.png")
