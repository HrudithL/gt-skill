import pandas as pd
import numpy as np
from great_tables import GT, style, loc

df = pd.read_csv("gtcars.csv")

# Step 1: Data cleaning
df = df[["mfr", "model", "hp", "msrp"]].copy()
df["model_display"] = df["mfr"] + " " + df["model"]
df = df.drop(columns=["mfr", "model"])
df = df[["model_display", "hp", "msrp"]]
df.columns = ["car", "hp", "msrp"]

# Step 2: Organize columns
gt = GT(df, rowname_col="car")

# Step 3: Big Color — only msrp (price) is colored; hp stays plain
# msrp is a neutral magnitude → Blues
cols_measure = ["msrp"]
lo = float(np.nanmin(df[cols_measure].to_numpy()))
hi = float(np.nanmax(df[cols_measure].to_numpy()))

# Step 4: Heading band (navy branding constant)
gt = (
    gt.tab_header(
        title="GT Cars by Horsepower and Price",
        subtitle="Performance metrics for high-end vehicles",
    )
)

# Step 5a: Formatting
gt = (
    gt.fmt_integer(columns=["hp"], use_seps=True)
      .fmt_currency(columns=["msrp"], currency="USD", decimals=0)
      .sub_missing(columns=["hp", "msrp"], missing_text="—")
)

# Step 5b: Column width and labels
gt = (
    gt.cols_label(hp="Horsepower", msrp="Price (USD)")
      .cols_width(cases={"hp": "120px", "msrp": "140px"})
)

# Step 3 continued: Apply data_color to msrp only
gt = (
    gt.data_color(
        columns=["msrp"],
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
)

# Step 5c: Frame borders
gt = (
    gt.tab_options(
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
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
)

# Step 5d: Stub tint (fixed pale-blue)
gt = (
    gt.tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
)

# Step 5e: Row striping
gt = gt.opt_row_striping()

# Step 5f: Padding (compact layout)
gt = (
    gt.tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

# Step 6: Titles & annotations (footer notes)
gt = (
    gt.tab_source_note(source_note="Price is the primary measure of vehicle value in this context; horsepower is shown as supporting context.")
      .tab_source_note(source_note="Source: gtcars.csv")
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
