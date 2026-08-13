import pandas as pd
from great_tables import GT, loc, md, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, group_emphasis, humanize_labels

# Read data
df = pd.read_csv("gtcars.csv")

# Select top 10 most expensive cars by MSRP
df_top10 = df.nlargest(10, "msrp").copy()

# Create composite car identifier (mfr + model)
df_top10["car"] = df_top10["mfr"] + " " + df_top10["model"]

# Sort by country, then by price descending for display within groups
df_top10 = df_top10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Select and rename columns
display_df = df_top10[["car", "ctry_origin", "msrp", "drivetrain", "trsmn"]].copy()
display_df.columns = ["car", "country", "price", "drivetrain", "transmission"]

gt = (
    GT(display_df, rowname_col="car", groupname_col="country")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("By country of origin with drivetrain and transmission details"),
    )
    .tab_stubhead(label="Car Model")
    .fmt_currency(columns="price", decimals=0)
)

gt = humanize_labels(
    gt,
    display_df,
    overrides={
        "country": "Country",
        "price": "Price (USD)",
        "drivetrain": "Drivetrain",
        "transmission": "Transmission",
    },
)

gt = gt.cols_width(
    cases={
        "car": "200px",
        "country": "120px",
        "price": "130px",
        "drivetrain": "110px",
        "transmission": "110px",
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

# Color the price column with sequential heatmap (Blues/neutral)
gt = heatmap(gt, "price", kind="sequential", hue="neutral")

# Apply house formatting
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)

# Source notes
gt = (
    gt.tab_source_note(
        source_note="Ranked by MSRP (manufacturer's suggested retail price) and grouped by country of origin."
    )
    .tab_source_note(source_note="Source: gtcars.csv dataset.")
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
