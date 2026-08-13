import pandas as pd
from great_tables import GT, md, loc, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, group_emphasis, humanize_labels
)

# Load and prepare data
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
df_top10 = df.nlargest(10, "msrp").copy()

# Build composite car identifier
df_top10["car"] = df_top10["mfr"] + " " + df_top10["model"]

# Sort by country, then by price descending for each country
df_top10 = df_top10.sort_values(["ctry_origin", "msrp"], ascending=[True, False])

# Select and rename columns for display
df_display = df_top10[["car", "ctry_origin", "drivetrain", "trsmn", "msrp"]].copy()
df_display.columns = ["car", "country", "drivetrain", "transmission", "msrp"]

# Reset index for proper row ordering
df_display = df_display.reset_index(drop=True)

# Build the table
gt = (
    GT(df_display, rowname_col="car", groupname_col="country")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("Grouped by country of origin with drivetrain and transmission details"),
    )
    .tab_stubhead(label="Car Model")
    .fmt_currency(columns="msrp", decimals=0)
    .sub_missing(columns=["drivetrain", "transmission"], missing_text="—")
)

# Humanize labels
gt = humanize_labels(
    gt,
    df_display,
    overrides={"msrp": "MSRP"},
)

# Set column widths
gt = gt.cols_width(
    cases={
        "car": "180px",
        "country": "120px",
        "drivetrain": "100px",
        "transmission": "110px",
        "msrp": "130px",
    }
)

# Apply padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply heatmap to MSRP (sequential, neutral magnitude in currency -> Blues)
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Apply heading band with navy branding (the house default)
gt = band(gt, hue="navy")

# Apply striping, stub tint, and group emphasis
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)

# Add source notes: analytical caption first, then provenance
gt = (
    gt.tab_source_note(
        source_note="Showing the 10 most expensive models in the dataset, grouped by country of origin."
    )
    .tab_source_note(source_note="Source: gtcars dataset.")
)

# Apply hairlines and frame
gt = hairlines(gt)
gt = frame(gt)

# Finalize and render
finalize(gt, path="table.png")
