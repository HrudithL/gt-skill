import pandas as pd
import numpy as np
from great_tables import GT, style, loc

df = pd.read_csv("gtcars.csv")

# Step 1: Ensure numeric columns are properly typed
df["hp"] = pd.to_numeric(df["hp"], errors="coerce")
df["msrp"] = pd.to_numeric(df["msrp"], errors="coerce")

# Step 2: Organize columns — stub + measures, group by manufacturer
cols_to_show = ["mfr", "model", "hp", "msrp"]
df_display = df[cols_to_show].copy()

# Compute domains for Big Color (Step 3)
hp_col = ["hp"]
msrp_col = ["msrp"]
msrp_lo = float(np.nanmin(df_display[msrp_col].to_numpy()))
msrp_hi = float(np.nanmax(df_display[msrp_col].to_numpy()))

# Step 3 & 4: Build the table with Big Color and light heading band
gt = (
    GT(df_display, groupname_col="mfr", rowname_col="model")
    .cols_hide(columns="mfr")
    # Format columns (Step 5e)
    .fmt_number(columns="hp", decimals=0, use_seps=True)
    .fmt_currency(columns="msrp", decimals=0)
    .sub_missing(columns=["hp", "msrp"], missing_text="—")
    # Step 3: Big Color — msrp (price) colored with Blues, hp (horsepower) stays bold-uncolored
    .data_color(
        columns="msrp",
        palette="Blues",
        domain=[msrp_lo, msrp_hi],
        truncate=False,
        na_color="#808080",
    )
    # Bold hp (secondary measure, not colored)
    .tab_style(
        style=style.text(weight="bold"),
        locations=loc.body(columns="hp"),
    )
    # Step 4: Light heading band (washed-DA tint for Blues is #EAF0F6)
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5a: Cell borders — hairlines between rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Step 5c: Row striping (gate: ≥10 rows and not fully filled by Big Color)
    .opt_row_striping()
    # Step 5d: Stub tint (harmonized to washed-DA tint #EAF0F6 per grey-budget rule)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5: Row-group emphasis (bold + light background)
    .tab_options(
        row_group_background_color="#EAF0F6",
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
    )
    # Step 4 (global constant): Frame — boxed light border on all sides
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
    # Step 6: Titles & annotations
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="A collection of high-performance vehicles with their key specifications",
    )
    .tab_source_note(
        source_note="Horsepower is shown in bold; price is color-encoded from lowest (light) to highest (dark)."
    )
    .tab_source_note(
        source_note="Source: gtcars.csv"
    )
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
