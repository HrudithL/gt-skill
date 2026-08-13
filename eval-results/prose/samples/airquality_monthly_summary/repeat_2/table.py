import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Read and clean data
df = pd.read_csv("airquality.csv")

# Aggregate by month: compute mean for each measure
monthly = df.groupby("Month")[["Ozone", "Wind", "Temp"]].mean().reset_index()
monthly.columns = ["Month", "Ozone", "Wind", "Temperature"]

# Create month labels for the stub
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
monthly["Month_Label"] = monthly["Month"].map(month_names)

# Reorder columns for better narrative flow
monthly = monthly[["Month_Label", "Temperature", "Wind", "Ozone"]]
monthly = monthly.rename(columns={"Month_Label": "Month"})

# Step 2: Organize columns (Month is stub, three numeric measures)
# Step 3: Compute domains for Big Color heatmaps
# Both Temperature and Ozone qualify (5 rows, ordered magnitudes)
# Temperature first in natural flow (input/context), Ozone second (outcome)
# Both are distinct dimensions, so both earn a full fill

ozone_cols = ["Ozone"]
lo_ozone = float(np.nanmin(monthly[ozone_cols].to_numpy()))
hi_ozone = float(np.nanmax(monthly[ozone_cols].to_numpy()))

temp_cols = ["Temperature"]
lo_temp = float(np.nanmin(monthly[temp_cols].to_numpy()))
hi_temp = float(np.nanmax(monthly[temp_cols].to_numpy()))

# Step 4: Build the table with heading band
gt = (
    GT(monthly, rowname_col="Month")
    # Step 5a: Format all numeric columns
    .fmt_number(columns=["Temperature", "Wind", "Ozone"], decimals=1, use_seps=False)
    .sub_missing(columns=["Temperature", "Wind", "Ozone"], missing_text="—")

    # Step 3: Big Color - heatmap fills for Temperature (Greens) and Ozone (Oranges)
    # Temperature: "more is better" context for air quality
    .data_color(
        columns=["Temperature"],
        palette="Greens",
        domain=[lo_temp, hi_temp],
        truncate=False,
        na_color="#808080",
    )
    # Ozone: "more is worse" (higher ozone = worse air quality)
    .data_color(
        columns=["Ozone"],
        palette="Reds",
        domain=[lo_ozone, hi_ozone],
        truncate=False,
        na_color="#808080",
    )

    # Step 4: Heading band (fixed branding)
    .tab_header(
        title="Monthly Air Quality Summary",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels by Month",
    )
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )

    # Step 5: Small Color polish
    # (a) Cell borders / hairlines
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # (c) Row striping (both measures colored, but Wind is plain, so stripe applies)
    .opt_row_striping()
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )

    # (e) Column label bottom rule (already set in tab_options above)

    # Frame borders (all four sides) and row stripe color
    .tab_options(
        row_striping_background_color="#F6F6F6",
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

    # Compact layout padding
    .cols_width(cases={
        "Month": "100px",
        "Temperature": "130px",
        "Wind": "110px",
        "Ozone": "110px",
    })
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )

    # Step 6: Titles & annotations (two footer calls)
    # Analytical caption: explain the measure definitions
    .tab_source_note(
        source_note="Ozone levels follow EPA convention (lower is better); Temperature and Wind Speed are unaggregated daily averages."
    )
    # Source note
    .tab_source_note(
        source_note="Source: New York air quality dataset (1973)."
    )
)

# Step 7: Render with gtsave
gt.gtsave("table.png", expand=15)
