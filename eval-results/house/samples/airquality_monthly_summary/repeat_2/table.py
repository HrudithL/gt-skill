import pandas as pd
from great_tables import GT, md, style, loc
import sys
import os

# Add the skill helpers to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.claude/skills/great-tables-house/scripts'))
from house_table import PALETTE, frame, finalize, band, stripe, stub_tint, heatmap, humanize_labels


def build_air_quality_table():
    """Build a table comparing average temperature, wind speed, and ozone by month."""

    # Read the air quality data
    df = pd.read_csv("airquality.csv")

    # Group by month and compute averages
    monthly = df.groupby("Month").agg({
        "Temp": "mean",
        "Wind": "mean",
        "Ozone": "mean"
    }).reset_index()

    # Create a month name mapping
    month_names = {
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September"
    }
    monthly["Month_Name"] = monthly["Month"].map(month_names)
    monthly = monthly[["Month_Name", "Temp", "Wind", "Ozone"]]
    monthly.columns = ["month", "temperature", "wind_speed", "ozone"]

    # Create the GT table
    gt = GT(monthly, rowname_col="month")

    # Add title and subtitle
    gt = gt.tab_header(
        title="Air Quality Summary by Month",
        subtitle=md("Average temperature, wind speed, and ozone levels from May to September")
    )

    # Format columns
    gt = gt.fmt_number(columns="temperature", decimals=1)
    gt = gt.fmt_number(columns="wind_speed", decimals=2)
    gt = gt.fmt_number(columns="ozone", decimals=2)

    # Humanize labels (snake_case to Title Case)
    gt = humanize_labels(gt, monthly)

    # Add two heatmaps: temperature (sequential) and ozone (sequential)
    gt = heatmap(gt, "temperature", kind="sequential", hue="positive")
    gt = heatmap(gt, "ozone", kind="sequential", hue="warning")

    # Apply band styling with forest hue (environment/air quality theme)
    gt = gt.tab_options(
        column_labels_background_color=PALETTE["accent_tint"]["forest"],
        column_labels_border_bottom_color=PALETTE["neutral"]["column_label_rule"],
        column_labels_border_bottom_width="2px",
        column_labels_border_bottom_style="solid",
    )

    # Apply stub tint to harmonize with forest heatmap
    gt = stub_tint(gt, hue="forest")

    # Row hairlines between body rows
    gt = gt.tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color=PALETTE["neutral"]["hairline"],
        table_body_hlines_width="1px",
    )

    # Apply frame
    gt = frame(gt)

    # Add source note
    gt = gt.tab_source_note("Source: air quality dataset (May-September observations)")

    # Finalize and save
    finalize(gt, path="table.png", zoom=2.0, expand=15)

    return gt


if __name__ == "__main__":
    build_air_quality_table()
