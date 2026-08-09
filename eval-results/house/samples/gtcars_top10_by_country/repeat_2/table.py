import pandas as pd
from great_tables import GT, md, loc, style
from house_table import (
    PALETTE,
    frame,
    finalize,
    band,
    group_emphasis,
    humanize_labels,
    heatmap,
)

# Load and prepare data
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
top10 = df.nlargest(10, "msrp")[["mfr", "model", "msrp", "ctry_origin", "drivetrain", "trsmn"]].reset_index(drop=True)

# Sort by country then by price (descending)
top10 = top10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Build the table
gt = (
    GT(top10, rowname_col="model", groupname_col="ctry_origin")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("Ranked by MSRP, grouped by country of origin — includes drivetrain and transmission details"),
    )
    .tab_stubhead(label="Model")
    .fmt_currency(columns="msrp", decimals=0)
    .sub_missing(columns=["msrp", "drivetrain", "trsmn"], missing_text="—")
)

gt = humanize_labels(gt, top10, overrides={"msrp": "MSRP", "ctry_origin": "Country", "drivetrain": "Drivetrain", "trsmn": "Transmission"})

# Apply color to MSRP (sequential heatmap)
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Band and emphasis
gt = band(gt, hue="navy")
gt = group_emphasis(gt)

# Frame and finalize
gt = frame(gt)
finalize(gt)
