"""Air quality monthly summary — average temperature, wind speed, and ozone levels.

Data: airquality.csv (NYC daily air quality, May-Sep 1973)
Story: Monthly aggregation of three key air quality measures across the summer.
"""
import pandas as pd
import numpy as np
from great_tables import GT, html, loc, style

df = pd.read_csv("airquality.csv")

# Map numeric Month codes to human-readable labels
month_name = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}

# Aggregate by month: mean temperature, wind speed, and ozone
monthly = df.groupby("Month").agg(
    temp_mean=("Temp", "mean"),
    wind_mean=("Wind", "mean"),
    ozone_mean=("Ozone", "mean"),
).reset_index()

monthly["month_label"] = monthly["Month"].map(month_name)
monthly = monthly[["month_label", "temp_mean", "wind_mean", "ozone_mean"]]

# Compute domains for heatmapped measures
# Temperature and ozone are distinct physical measurements, both earn fills
# Wind speed is mentioned but carries no narrative emphasis — stays plain
temp_lo = float(np.nanmin(monthly["temp_mean"].to_numpy()))
temp_hi = float(np.nanmax(monthly["temp_mean"].to_numpy()))
ozone_lo = float(np.nanmin(monthly["ozone_mean"].to_numpy()))
ozone_hi = float(np.nanmax(monthly["ozone_mean"].to_numpy()))

gt = (
    GT(monthly, rowname_col="month_label")
    .tab_header(
        title="NYC Air Quality — Summer 1973",
        subtitle="Monthly average temperature, wind speed, and ozone levels",
    )
    .cols_label(
        temp_mean=html("Temperature (&deg;F)"),
        wind_mean="Wind (mph)",
        ozone_mean="Ozone (ppb)",
    )
    # Format all numeric columns to 1 decimal place
    .fmt_number(columns=["temp_mean", "wind_mean", "ozone_mean"], decimals=1)
    .sub_missing(columns=["temp_mean", "wind_mean", "ozone_mean"], missing_text="—")
    # Temperature: neutral magnitude → Blues
    .data_color(
        columns=["temp_mean"],
        palette="Blues",
        domain=[temp_lo, temp_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Ozone: "more is worse" (health risk) → Reds
    .data_color(
        columns=["ozone_mean"],
        palette="Reds",
        domain=[ozone_lo, ozone_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Right-align numeric columns
    .cols_align(align="right", columns=["temp_mean", "wind_mean", "ozone_mean"])
    # Heading band — fixed branding navy, bold labels, white text
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    # Stub tint — fixed branding hex
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    # Row striping
    .opt_row_striping()
    .tab_options(
        row_striping_background_color="#F6F6F6",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        table_border_top_style="solid", table_border_top_color="#CCCCCC", table_border_top_width="1px",
        table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
        table_border_left_style="solid", table_border_left_color="#CCCCCC", table_border_left_width="1px",
        table_border_right_style="solid", table_border_right_color="#CCCCCC", table_border_right_width="1px",
    )
    # Column widths
    .cols_width(cases={
        "month_label": "90px",
        "temp_mean": "100px",
        "wind_mean": "90px",
        "ozone_mean": "90px",
    })
    # Compact layout padding
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Footer: analytical caption + source note (two separate calls)
    .tab_source_note(
        source_note=html(
            f"Temperature ranged from {temp_lo:.1f}–{temp_hi:.1f}°F; ozone from {ozone_lo:.1f}–{ozone_hi:.1f} ppb."
        )
    )
    .tab_source_note(
        source_note="Source: New York State Department of Conservation, daily measurements May–September 1973."
    )
)

gt.gtsave("table.png", zoom=2.0, expand=15)
