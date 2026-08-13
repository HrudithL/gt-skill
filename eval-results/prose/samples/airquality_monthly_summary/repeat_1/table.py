import pandas as pd
import numpy as np
from great_tables import GT, html, loc, style

# Step 1: Load and clean the data
df = pd.read_csv("airquality.csv")

# Create monthly summary
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}

monthly = df.groupby("Month").agg(
    temp_mean=("Temp", "mean"),
    wind_mean=("Wind", "mean"),
    ozone_mean=("Ozone", "mean"),
).reset_index()

monthly["month_label"] = monthly["Month"].map(month_names)
monthly = monthly[["month_label", "temp_mean", "wind_mean", "ozone_mean"]]

# Step 3: Determine which measures get color fills
# All three are numeric and have ≥5 rows, so all qualify.
# Per the prompt, all three measures are named and distinct.
# Temperature and Ozone should be colored as primary measures (both neutral magnitudes).
# Wind speed is less central to the core ask, so keep it plain.

temp_lo = float(np.nanmin(monthly[["temp_mean"]].to_numpy()))
temp_hi = float(np.nanmax(monthly[["temp_mean"]].to_numpy()))

ozone_lo = float(np.nanmin(monthly[["ozone_mean"]].to_numpy()))
ozone_hi = float(np.nanmax(monthly[["ozone_mean"]].to_numpy()))

# Step 4 & 5: Build the table with header band and polish
gt = (
    GT(monthly, rowname_col="month_label")
    .tab_header(
        title="Air Quality Metrics by Month",
        subtitle="Average temperature, wind speed, and ozone levels"
    )
    .cols_label(
        temp_mean=html("Temp (&deg;F)"),
        wind_mean="Wind (mph)",
        ozone_mean=html("Ozone (ppb)"),
    )
    # Format numbers (Step 5e)
    .fmt_number(columns=["temp_mean", "wind_mean", "ozone_mean"], decimals=1)
    .sub_missing(columns=["temp_mean", "wind_mean", "ozone_mean"], missing_text="—")
    # Color fills for temperature (neutral magnitude → Blues) and ozone (neutral magnitude, secondary → Greens)
    .data_color(
        columns=["temp_mean"],
        palette="Blues",
        domain=[temp_lo, temp_hi],
        truncate=False,
        na_color="#808080",
        autocolor_text=True,
    )
    .data_color(
        columns=["ozone_mean"],
        palette="Greens",
        domain=[ozone_lo, ozone_hi],
        truncate=False,
        na_color="#808080",
        autocolor_text=True,
    )
    # Column widths
    .cols_width(cases={
        "month_label": "100px",
        "temp_mean": "110px",
        "wind_mean": "110px",
        "ozone_mean": "110px",
    })
    # Heading band (Step 4) — fixed navy, bold labels, white text
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    # Stub tint (Step 5d) — fixed pale blue
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub()
    )
    # Row striping (Step 5c) and body hairlines (Step 5a)
    .opt_row_striping()
    .tab_options(
        row_striping_background_color="#F6F6F6",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        # Frame border (Step 5)
        table_border_top_style="solid", table_border_top_color="#CCCCCC", table_border_top_width="1px",
        table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
        table_border_left_style="solid", table_border_left_color="#CCCCCC", table_border_left_width="1px",
        table_border_right_style="solid", table_border_right_color="#CCCCCC", table_border_right_width="1px",
    )
    # Padding (Step 5) — compact layout
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Titles and annotations (Step 6) — two separate source notes
    .tab_source_note(
        source_note="Temperature and ozone are color-encoded as distinct physical measurements of summer conditions."
    )
    .tab_source_note(
        source_note="Source: Air quality measurements (May–September 1973)"
    )
)

# Step 7: Render and verify
gt.gtsave("table.png", zoom=2.0, expand=15)
