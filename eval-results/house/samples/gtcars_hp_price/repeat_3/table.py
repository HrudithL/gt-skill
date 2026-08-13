import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, heatmap

# Read the data
df = pd.read_csv("gtcars.csv")

# Create a display-ready dataframe with the columns we need
# Compose the car identifier from manufacturer and model
df["car"] = df["mfr"] + " " + df["model"]
display_df = df[["car", "hp", "msrp"]].copy()
display_df.columns = ["car", "hp", "msrp"]
display_df = display_df.sort_values("hp", ascending=False).reset_index(drop=True)

# Build the table
gt = (
    GT(display_df, rowname_col="car")
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle=md("Performance specifications sorted by horsepower")
    )
    .fmt_number(columns="hp", decimals=0)
    .fmt_currency(columns="msrp", decimals=0)
)

# Apply humanized labels
gt = gt.cols_label(hp="Horsepower", msrp="Price (MSRP)")

# Set column widths
gt = gt.cols_width(
    cases={
        "car": "180px",
        "hp": "120px",
        "msrp": "120px",
    }
)

# Apply house formatting
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Big Color: highlight price with sequential Blues (neutral magnitude)
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Heading band with navy (house default)
gt = band(gt, hue="navy")

# Small-color polish
gt = stripe(gt)

# Source notes
gt = gt.tab_source_note(
    source_note="Data includes vehicles from multiple manufacturers across various model years."
)
gt = gt.tab_source_note(source_note="Source: gtcars dataset.")

# Final touches
gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
