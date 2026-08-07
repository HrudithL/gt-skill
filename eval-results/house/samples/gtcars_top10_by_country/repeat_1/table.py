import pandas as pd
from great_tables import GT, loc, style, md
from house_table import PALETTE, frame, finalize, band, stub_tint, heatmap, group_emphasis, humanize_labels

# Load and process data
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
top10 = df.nlargest(10, "msrp")[["mfr", "model", "ctry_origin", "msrp", "drivetrain", "trsmn"]].reset_index(drop=True)

# Sort by country first, then by price descending within each country
top10 = top10.sort_values(by=["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Create a display column combining manufacturer and model
top10["car"] = top10["mfr"] + " " + top10["model"]

# Rename transmission codes to readable format
transmission_map = {
    "6a": "6-Spd Auto",
    "6am": "6-Spd Auto w/ Manual",
    "7a": "7-Spd Auto",
    "8a": "8-Spd Auto",
    "8am": "8-Spd Auto w/ Manual",
    "9a": "9-Spd Auto",
}
top10["transmission"] = top10["trsmn"].map(lambda x: transmission_map.get(x, x))

# Format price for display
top10["price"] = top10["msrp"]

# Create the display dataframe with relevant columns
display_df = top10[["car", "ctry_origin", "price", "drivetrain", "transmission"]].copy()
display_df.columns = ["car", "country", "price", "drivetrain", "transmission"]

# Build the GT table
gt = (
    GT(display_df, rowname_col="car", groupname_col="country")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("Grouped by country of origin with drivetrain and transmission details"),
    )
    .tab_stubhead(label="Car")
    .fmt_currency(columns="price", decimals=0)
    .sub_missing(columns=["drivetrain", "transmission"], missing_text="—")
)

gt = humanize_labels(
    gt,
    display_df,
    overrides={"price": "MSRP"},
)

# Apply heatmap to price (sequential, neutral = Blues)
gt = heatmap(gt, "price", kind="sequential", hue="neutral")

# Apply heading band with navy hue (matching the Blues heatmap)
gt = band(gt, hue="navy")

# Apply stub tint and group emphasis
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)

# Add source note and frame
gt = (
    gt.tab_source_note(source_note="Source: GT cars dataset. Prices in USD.")
)

gt = frame(gt)
finalize(gt, path="table.png")
