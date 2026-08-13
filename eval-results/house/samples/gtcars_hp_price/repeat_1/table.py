import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, humanize_labels

# Load the data
df = pd.read_csv("./gtcars.csv")

# Create a composite car identifier (manufacturer + model)
df["car"] = df["mfr"] + " " + df["model"]

# Select relevant columns
df_display = df[["car", "hp", "msrp"]].copy()
df_display.columns = ["car", "hp", "price"]

# Sort by horsepower descending for visual interest
df_display = df_display.sort_values("hp", ascending=False).reset_index(drop=True)

# Create the GT table
gt = GT(df_display, rowname_col="car")

# Title and subtitle
gt = gt.tab_header(
    title="GT Cars Performance",
    subtitle=md("Horsepower and price for high-performance vehicles")
)

# Stub head
gt = gt.tab_stubhead(label="Car Model")

# Format columns
gt = gt.fmt_integer(columns="hp")
gt = gt.fmt_currency(columns="price", decimals=0)

# Humanize labels
gt = humanize_labels(gt, df_display)

# Set column widths
gt = gt.cols_width(
    cases={
        "car": "200px",
        "hp": "100px",
        "price": "130px",
    }
)

# Apply heatmap to horsepower (the hero measure)
gt = heatmap(gt, "hp", kind="sequential", hue="neutral")

# Branding elements
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Source notes - analytical caption first, then provenance
gt = gt.tab_source_note(
    source_note="Horsepower displayed at maximum RPM rating. Price represents manufacturer's suggested retail price (MSRP)."
)
gt = gt.tab_source_note(
    source_note="Source: provided GT cars dataset."
)

# Polish
gt = hairlines(gt)
gt = frame(gt)

# Render and save
finalize(gt)
