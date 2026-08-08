import pandas as pd
import numpy as np
from great_tables import GT

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")
df_display = df[["mfr", "model", "hp", "msrp"]].copy()
df_display.columns = ["Manufacturer", "Model", "Horsepower", "Price"]

# Step 2: Create GT table with stub
gt = (
    GT(df_display, rowname_col="Manufacturer")
    .cols_hide(columns=["Manufacturer"])
    .fmt_number(columns="Horsepower", decimals=0, use_seps=True)
    .fmt_currency(columns="Price", decimals=0, currency="USD")
    .opt_row_striping()
    # Step 3: Big Color - price is the hero measure (neutral magnitude → Blues)
    .data_color(
        columns="Price",
        palette="Blues",
        domain=[float(np.nanmin(df_display["Price"].to_numpy())),
                float(np.nanmax(df_display["Price"].to_numpy()))],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band - light band since we have Big Color
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5: Small Color - borders and frame
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
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
    # Step 6: Titles and annotations
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="A selection of performance vehicles with their specifications and MSRP"
    )
    .tab_source_note(source_note="Source: gtcars dataset")
)

gt.gtsave("table.png", expand=15, zoom=2.0)
