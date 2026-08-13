import pandas as pd
from great_tables import GT, loc, md, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, group_emphasis, humanize_labels

# Load data
df = pd.read_csv("gtcars.csv")

# Create composite car identifier and select top 10 most expensive
df["car"] = df["mfr"] + " " + df["model"]
top_10 = df.nlargest(10, "msrp")[["car", "ctry_origin", "drivetrain", "trsmn", "msrp"]].copy()

# Sort by country and price within country for better grouping
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Format transmission codes to be more readable
trsmn_map = {
    "6a": "6-speed automatic",
    "6m": "6-speed manual",
    "7a": "7-speed automatic",
    "7m": "7-speed manual",
    "8a": "8-speed automatic",
    "8am": "8-speed automatic/manual",
    "9a": "9-speed automatic",
    "1dd": "Direct drive"
}
top_10["trsmn"] = top_10["trsmn"].map(lambda x: trsmn_map.get(x, x))

# Format drivetrain to be more readable
drivetrain_map = {
    "rwd": "Rear-wheel",
    "awd": "All-wheel",
    "fwd": "Front-wheel"
}
top_10["drivetrain"] = top_10["drivetrain"].map(lambda x: drivetrain_map.get(x, x))

# Create GT object with grouping by country
gt = GT(top_10, rowname_col="car", groupname_col="ctry_origin")

# Apply humanized labels with overrides
gt = humanize_labels(gt, top_10, overrides={
    "car": "Car Model",
    "ctry_origin": "Country",
    "drivetrain": "Drivetrain",
    "trsmn": "Transmission",
    "msrp": "MSRP"
})

# Format MSRP as currency
gt = gt.fmt_currency(columns="msrp", decimals=0, currency="USD")

# Apply styling
gt = band(gt, hue="navy")
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)
gt = stripe(gt)
gt = frame(gt)
gt = hairlines(gt)

# Apply sequential heatmap to MSRP (the hero measure)
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Add header and source notes
gt = gt.tab_header(
    title="Top 10 Most Expensive GT Cars",
    subtitle="Grouped by country of origin with drivetrain and transmission details"
)

gt = gt.tab_source_note(
    source_note="Ranked by MSRP (manufacturer's suggested retail price), sorted by country and price within each country."
)

gt = gt.tab_source_note(
    source_note=md("Source: gtcars.csv")
)

# Missing values
gt = gt.sub_missing(columns=["drivetrain", "trsmn"], missing_text="—")

# Column widths and padding
gt = gt.cols_width(cases={
    "car": "200px",
    "ctry_origin": "120px",
    "drivetrain": "120px",
    "trsmn": "170px",
    "msrp": "120px"
})

gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px"
)

# Finalize and save
finalize(gt, path="table.png")
