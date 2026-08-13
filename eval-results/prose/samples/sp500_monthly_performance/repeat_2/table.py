import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Clean data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Extract year-month for grouping
df["year_month"] = df["date"].dt.to_period("M")

# Calculate daily gain/loss for each day
df["daily_gain"] = df["high"] - df["open"]
df["daily_loss"] = df["open"] - df["low"]

# Group by month and aggregate
monthly = df.groupby("year_month").agg(
    opening_price=("open", "first"),
    closing_price=("close", "last"),
    highest_daily_gain=("daily_gain", "max"),
    highest_daily_loss=("daily_loss", "max"),
    avg_daily_volume=("volume", "mean"),
).reset_index()

# Filter for 2010-2015
monthly["year"] = monthly["year_month"].dt.year
monthly = monthly[(monthly["year"] >= 2010) & (monthly["year"] <= 2015)].copy()

# Calculate percent change
monthly["pct_change"] = (monthly["closing_price"] - monthly["opening_price"]) / monthly["opening_price"]

# Format month label for display
monthly["month_label"] = monthly["year_month"].dt.strftime("%b %Y")

# Select and order columns for the table
display_df = monthly[[
    "month_label",
    "opening_price",
    "closing_price",
    "pct_change",
    "avg_daily_volume",
    "highest_daily_gain",
    "highest_daily_loss"
]].copy()

display_df.columns = [
    "Month",
    "Opening Price",
    "Closing Price",
    "% Change",
    "Avg Daily Volume",
    "Best Day Gain",
    "Worst Day Loss"
]

# Build the table
gt = (
    GT(display_df, rowname_col="Month")
    # Step 2: Organize columns - percent change and volumes merit color as distinct dimensions of performance
    # Step 4: Heading band
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Column labels border
    .tab_options(
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px"
    )
    # Step 5: Small Color polish
    # (a) Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # (c) Row striping
    .opt_row_striping()
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Frame
    .tab_options(
        table_border_top_style="solid",
        table_border_top_color="#CCCCCC",
        table_border_top_width="1px",
        table_border_bottom_style="solid",
        table_border_bottom_color="#CCCCCC",
        table_border_bottom_width="1px",
        table_border_left_style="solid",
        table_border_left_color="#CCCCCC",
        table_border_left_width="1px",
        table_border_right_style="solid",
        table_border_right_color="#CCCCCC",
        table_border_right_width="1px",
    )
)

# Column formatting
gt = (
    gt.fmt_currency(columns=["Opening Price", "Closing Price", "Best Day Gain", "Worst Day Loss"], decimals=2, use_seps=True)
      .fmt_percent(columns=["% Change"], decimals=1, scale_values=False, force_sign=True)
      .fmt_number(columns=["Avg Daily Volume"], decimals=0, use_seps=True)
)

# Step 3: Big Color - add color fills for key metrics
# Percent change: diverging fill (signed measure, positive=good)
lo_pct = float(np.nanmin(display_df["% Change"].to_numpy()))
hi_pct = float(np.nanmax(display_df["% Change"].to_numpy()))
M_pct = max(abs(lo_pct), abs(hi_pct))

gt = gt.data_color(
    columns=["% Change"],
    palette="RdYlGn",
    domain=[-M_pct, M_pct],
    truncate=False,
)

# Average Daily Volume: sequential fill (neutral magnitude → Blues)
lo_vol = float(np.nanmin(display_df["Avg Daily Volume"].to_numpy()))
hi_vol = float(np.nanmax(display_df["Avg Daily Volume"].to_numpy()))

gt = gt.data_color(
    columns=["Avg Daily Volume"],
    palette="Blues",
    domain=[lo_vol, hi_vol],
    truncate=False,
)

# Best Day Gain: sequential fill (positive magnitude → Greens, next in neutral tie-breaker ladder)
lo_gain = float(np.nanmin(display_df["Best Day Gain"].to_numpy()))
hi_gain = float(np.nanmax(display_df["Best Day Gain"].to_numpy()))

gt = gt.data_color(
    columns=["Best Day Gain"],
    palette="Greens",
    domain=[lo_gain, hi_gain],
    truncate=False,
)

# Worst Day Loss: sequential fill (loss/risk → Reds)
lo_loss = float(np.nanmin(display_df["Worst Day Loss"].to_numpy()))
hi_loss = float(np.nanmax(display_df["Worst Day Loss"].to_numpy()))

gt = gt.data_color(
    columns=["Worst Day Loss"],
    palette="Reds",
    domain=[lo_loss, hi_loss],
    truncate=False,
)

# Set heading band colors and column label styling
gt = gt.tab_options(
    heading_background_color="#08306B",
    column_labels_font_weight="bold",
)

# Column header text color
gt = gt.tab_style(
    style=style.text(color="white"),
    locations=loc.column_labels(),
)

# Step 6: Titles and annotations
gt = (
    gt.tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="2010–2015: Opening/Closing Prices, Monthly % Change, Volume & Daily Extremes"
    )
    .tab_source_note(
        source_note="Percent change computed as (closing price − opening price) ÷ opening price. Best day gain = highest intraday gain (high − open); worst day loss = largest intraday loss (open − low). Average daily volume is the mean trading volume across all market days in the month."
    )
    .tab_source_note(
        source_note="Source: S&P 500 daily price data, sp500.csv"
    )
)

# Column width sizing
gt = gt.cols_width(cases={
    "Opening Price": "120px",
    "Closing Price": "120px",
    "% Change": "100px",
    "Avg Daily Volume": "140px",
    "Best Day Gain": "120px",
    "Worst Day Loss": "120px",
})

# Step 7: Render
gt.gtsave("table.png", expand=15)
print("Table rendered to table.png")
