import pandas as pd
from great_tables import GT, loc, md, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, group_emphasis, humanize_labels

# Load data and prepare
df = pd.read_csv("gtcars.csv")

# Build row identifier from mfr + model
df["car"] = df["mfr"] + " " + df["model"]

# Select top 10 by MSRP
top10 = df.nlargest(10, "msrp").copy()

# Create display columns for drivetrain and transmission
drivetrain_map = {
    "rwd": "Rear-wheel drive",
    "awd": "All-wheel drive",
    "fwd": "Front-wheel drive",
}
top10["drivetrain_display"] = top10["drivetrain"].map(drivetrain_map)

# Transmission display
transmission_map = {
    "6a": "6-speed automatic",
    "7a": "7-speed automatic",
    "8a": "8-speed automatic",
    "8am": "8-speed automatic/manual",
    "6am": "6-speed automatic/manual",
    "9a": "9-speed automatic",
}
top10["transmission_display"] = top10["trsmn"].map(transmission_map)

# Prepare final DataFrame
table_data = top10[["car", "ctry_origin", "drivetrain_display", "transmission_display", "msrp"]].copy()
table_data.columns = ["car", "country", "drivetrain", "transmission", "price"]

# Sort by country, then by price descending
table_data = table_data.sort_values(["country", "price"], ascending=[True, False]).reset_index(drop=True)

# Create the GT table
gt = (
    GT(table_data, rowname_col="car", groupname_col="country")
    .tab_header(
        title="Top 10 Most Expensive GT Cars by Country",
        subtitle=md("Grouped by country of origin with drivetrain and transmission specifications"),
    )
    .tab_stubhead(label="Vehicle")
    .fmt_currency(columns="price", decimals=0)
    .sub_missing(columns=["drivetrain", "transmission", "price"], missing_text="—")
)

gt = humanize_labels(
    gt,
    table_data,
    overrides={"price": "MSRP (USD)"},
)

# Apply formatting
gt = band(gt, hue="navy")
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)
gt = stripe(gt)
gt = hairlines(gt)
gt = frame(gt)

gt.tab_source_note(source_note="Source: GT Cars dataset. MSRP shown is manufacturer's suggested retail price.")

finalize(gt, path="table.png")
