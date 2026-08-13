import pandas as pd
from great_tables import GT, md, loc, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, group_emphasis, humanize_labels
)

# Load the data
df = pd.read_csv("gtcars.csv")

# Create a car identifier (composite stub)
df["car"] = df["mfr"] + " " + df["model"]

# Select top 10 most expensive cars
top_10 = df.nlargest(10, "msrp")[["car", "ctry_origin", "drivetrain", "trsmn", "msrp"]].copy()

# Rename transmission codes to human-readable format
transmission_map = {
    "7a": "7-Speed Automatic",
    "6a": "6-Speed Automatic",
    "8a": "8-Speed Automatic",
    "8am": "8-Speed Automatic",
    "7am": "7-Speed Automatic",
    "6am": "6-Speed Automatic",
    "9a": "9-Speed Automatic",
    "1dd": "Direct Drive",
    "6m": "6-Speed Manual",
    "7m": "7-Speed Manual",
}
top_10["trsmn"] = top_10["trsmn"].map(transmission_map)

# Rename columns for display
top_10 = top_10.rename(columns={
    "car": "model",
    "ctry_origin": "country",
    "drivetrain": "drivetrain",
    "trsmn": "transmission",
    "msrp": "msrp"
})

# Sort by country, then by price descending
top_10 = top_10.sort_values(["country", "msrp"], ascending=[True, False])

# Build the table
gt = (
    GT(top_10, rowname_col="model", groupname_col="country")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("By country of origin, with drivetrain and transmission specifications"),
    )
    .tab_stubhead(label="Model")
    .fmt_currency(columns="msrp", decimals=0)
    .sub_missing(columns=["drivetrain", "transmission"], missing_text="—")
)

gt = humanize_labels(
    gt,
    top_10,
    overrides={"msrp": "MSRP"},
)

# Column widths and padding
gt = gt.cols_width(
    cases={
        "model": "180px",
        "country": "140px",
        "drivetrain": "120px",
        "transmission": "180px",
        "msrp": "140px",
    }
)
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply styling: heatmap for MSRP (the hero measure)
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Heading band, striping, stub tint, and group emphasis
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)

# Add source notes
gt = gt.tab_source_note(
    source_note="Top 10 vehicles ranked by MSRP, grouped by country of origin."
)
gt = gt.tab_source_note(
    source_note="Source: gtcars.csv dataset."
)

# Apply frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Finalize and save
finalize(gt)
