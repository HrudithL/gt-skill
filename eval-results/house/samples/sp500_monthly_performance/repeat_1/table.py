import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, finalize, band, stripe, stub_tint, heatmap, humanize_labels

# Load data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Extract year and month
df["year_month"] = df["date"].dt.to_period("M")
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

# Filter to 2010-2015
df = df[(df["year"] >= 2010) & (df["year"] <= 2015)].copy()

# Group by year-month and compute monthly metrics
monthly_data = []
for period, group in df.groupby("year_month"):
    year, month = period.year, period.month

    # Opening price (first day of month)
    opening = group.iloc[0]["open"]

    # Closing price (last day of month)
    closing = group.iloc[-1]["close"]

    # Percent change
    pct_change = (closing - opening) / opening

    # Average daily volume
    avg_volume = group["volume"].mean()

    # Daily changes within the month
    group_copy = group.copy()
    group_copy["daily_change"] = group_copy["close"] - group_copy["open"]

    # Highest single-day gain
    max_gain = group_copy["daily_change"].max()

    # Highest single-day loss (most negative)
    min_loss = group_copy["daily_change"].min()

    monthly_data.append({
        "year": year,
        "month": month,
        "date": period.to_timestamp(),
        "opening_price": opening,
        "closing_price": closing,
        "percent_change": pct_change,
        "avg_daily_volume": avg_volume,
        "highest_gain": max_gain,
        "highest_loss": min_loss,
    })

monthly_df = pd.DataFrame(monthly_data)

# Create display column for month name
month_names = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
}
monthly_df["month_label"] = monthly_df["year"].astype(str) + "-" + monthly_df["month"].map(month_names)

# Reorder and select columns
display_df = monthly_df[
    ["month_label", "opening_price", "closing_price", "percent_change", "avg_daily_volume", "highest_gain", "highest_loss"]
].copy()

gt = GT(display_df, rowname_col="month_label")
gt = gt.tab_header(
    title="S&P 500 Monthly Performance Summary",
    subtitle=md("Opening price, closing price, percent change, average daily volume, and highest single-day gains/losses, 2010–2015"),
)
gt = gt.tab_stubhead(label="Month")

# Format columns
gt = gt.fmt_currency(columns=["opening_price", "closing_price", "highest_gain", "highest_loss"], decimals=2)
gt = gt.fmt_percent(columns="percent_change", decimals=2)
gt = gt.fmt_number(columns="avg_daily_volume", decimals=0, use_seps=True)

# Humanize labels with overrides
gt = humanize_labels(
    gt,
    display_df,
    overrides={
        "opening_price": "Opening Price",
        "closing_price": "Closing Price",
        "percent_change": "Percent Change",
        "avg_daily_volume": "Avg Daily Volume",
        "highest_gain": "Highest Daily Gain",
        "highest_loss": "Highest Daily Loss",
    },
)

# Apply color formatting
# Percent change: diverging (green = good/positive, red = bad/negative)
gt = heatmap(gt, "percent_change", kind="diverging", hue="default")

# Add band and stub tint
gt = band(gt, hue="forest")
gt = stub_tint(gt, hue="forest")

# Add striping if there are enough rows (72 months = well over 10 rows)
gt = stripe(gt)

# Add frame and finalize
gt = frame(gt)
gt = gt.tab_source_note(source_note="Source: provided S&P 500 dataset.")

finalize(gt, path="table.png")
