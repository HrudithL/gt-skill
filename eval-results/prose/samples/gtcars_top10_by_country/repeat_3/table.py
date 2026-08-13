import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: UNDERSTAND & CLEAN DATA
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
df_top10 = df.nlargest(10, "msrp").copy()

# Sort by country, then by MSRP descending within each country
df_top10 = df_top10.sort_values(["ctry_origin", "msrp"], ascending=[True, False])

# Create a display name combining manufacturer and model
df_top10["car_name"] = df_top10["mfr"] + " " + df_top10["model"]

# Step 2: ORGANIZE COLUMNS
# Select and order columns: stub (car name), country (group), then detail columns, then price
cols_to_show = ["car_name", "ctry_origin", "drivetrain", "trsmn", "msrp"]
df_display = df_top10[cols_to_show].copy()

# Rename columns for display
df_display = df_display.rename(columns={
    "car_name": "Car",
    "ctry_origin": "Country",
    "drivetrain": "Drivetrain",
    "trsmn": "Transmission",
    "msrp": "MSRP"
})

# Step 3: BIG COLOR - MSRP is an ordered magnitude (price), qualifies for gradient fill
# Compute domain across the MSRP column
cols_color = ["MSRP"]
lo = float(np.nanmin(df_display[cols_color].to_numpy()))
hi = float(np.nanmax(df_display[cols_color].to_numpy()))

# Step 4: HEADING BAND - dark navy band with white text (fixed, unconditional)
# Step 5: SMALL COLOR - apply the checklist

gt = (
    GT(df_display, rowname_col="Car", groupname_col="Country")
    # Step 4: Heading band (fixed branding)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    # Step 2: Column widths (compact layout)
    .cols_width(cases={
        "Car": "200px",
        "Country": "150px",
        "Drivetrain": "120px",
        "Transmission": "100px",
        "MSRP": "140px"
    })
    # Step 2: Column labels
    .cols_label(
        Drivetrain="Drivetrain",
        Transmission="Transmission",
        MSRP="MSRP ($)"
    )
    # Step 5(e): Format MSRP as currency
    .fmt_currency(columns="MSRP", decimals=0)
    # Step 3: Big Color - gradient fill on MSRP
    .data_color(
        columns="MSRP",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080"
    )
    # Step 4: Heading band styling (dark navy background with white text)
    .tab_options(
        column_labels_background_color="#08306B",
        table_font_size="12px",
        heading_background_color="#FFFFFF"
    )
    # Step 5(a): Cell hairlines between rows and (c) Row striping
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        row_striping_background_color="#F6F6F6"
    )
    # Step 5(c): Row striping (apply by default)
    .opt_row_striping()
    # Step 5(d): Stub tint (pale blue background on stub)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub()
    )
    # Step 5: Row group emphasis (bold + structural rule)
    .tab_options(
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px"
    )
    # Step 5: Padding for compact layout
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px"
    )
    # Step 5: Frame border (all four sides)
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
        table_border_right_width="1px"
    )
    # Step 6: Titles & annotations (footer notes)
    .tab_source_note(source_note="Table shows the top 10 most expensive GT cars, ranked by MSRP in descending order within each country.")
    .tab_source_note(source_note="Source: gtcars.csv")
)

# Step 7: RENDER & VERIFY
gt.gtsave("table.png", expand=15)
print("Table rendered successfully to table.png")
