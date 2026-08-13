import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Data cleaning
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
df_top = df.nlargest(10, "msrp").copy()

# Ensure msrp is numeric
df_top["msrp"] = pd.to_numeric(df_top["msrp"], errors="coerce")

# Create display label combining manufacturer and model
df_top["car_label"] = df_top["mfr"] + " " + df_top["model"]

# Create transmission display (decode trsmn codes: "7a" = "7-speed Auto", "6m" = "6-speed Manual", etc.)
def decode_transmission(code):
    if pd.isna(code):
        return "—"
    code_str = str(code).lower()
    if "dd" in code_str:
        return "Direct Drive"
    if "a" in code_str:
        return f"{code_str[0]}-speed Automatic"
    if "m" in code_str:
        return f"{code_str[0]}-speed Manual"
    return code_str

df_top["transmission"] = df_top["trsmn"].apply(decode_transmission)

# Capitalize drivetrain
df_top["drivetrain_display"] = df_top["drivetrain"].str.upper()

# Select and order columns for display
df_display = df_top[["ctry_origin", "car_label", "drivetrain_display", "transmission", "msrp"]].reset_index(drop=True)
df_display.columns = ["country", "car", "drivetrain", "transmission", "msrp"]

# Sort by country, then by price descending for better grouping readability
df_display = df_display.sort_values(["country", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Step 2: Organize columns with grouping
gt = (
    GT(df_display, rowname_col="car", groupname_col="country")

    # Step 3: Big Color - msrp is the hero measure (ordered magnitude, neutral = Blues)
    .data_color(
        columns="msrp",
        palette="Blues",
        domain=[
            float(np.nanmin(df_display[["msrp"]].to_numpy())),
            float(np.nanmax(df_display[["msrp"]].to_numpy()))
        ],
        truncate=False,
        na_color="#808080",
    )

    # Formatting per column
    .fmt_currency(columns="msrp", currency="USD", decimals=0)
    .sub_missing(columns=["drivetrain", "transmission"], missing_text="—")

    # Step 4: Heading band - dark navy with white text
    .tab_header(
        title="Top 10 Most Expensive GT Cars by Country",
        subtitle="Price, drivetrain, and transmission details"
    )

    # Step 5: Small Color polish
    # (a) Cell borders - hairlines between rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )

    # Row group styling - bold + structural rule, no fill
    .tab_options(
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
    )

    # (c) Row striping
    .opt_row_striping()

    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )

    # Frame - boxed border on all sides
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

    # Compact layout - sizing and padding
    .cols_width(cases={
        "drivetrain": "120px",
        "transmission": "150px",
        "msrp": "130px",
    })
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )

    # Step 6: Titles & annotations (footer with two notes)
    .tab_source_note(source_note="Price shows MSRP in USD. Top 10 based on highest listed price.")
    .tab_source_note(source_note="Source: gtcars.csv")
)

# Render
gt.gtsave("table.png", expand=15)
