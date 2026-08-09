import pandas as pd
from great_tables import GT, md, style, loc
from house_table import PALETTE, frame, finalize, band, stripe, stub_tint, group_emphasis, humanize_labels

# Load data
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
top_10 = df.nlargest(10, "msrp").copy()

# Sort by country then by price descending within each country
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False])

# Create a display column combining drivetrain and transmission
top_10["drivetrain_transmission"] = top_10["drivetrain"].str.upper() + " / " + top_10["trsmn"]

# Select relevant columns for display
display_df = top_10[["mfr", "model", "year", "ctry_origin", "drivetrain_transmission", "msrp"]].copy()
display_df.columns = ["Manufacturer", "Model", "Year", "Country", "Drivetrain / Trans", "MSRP"]

# Create GT table with country as groupname
gt = (
    GT(display_df, rowname_col="Model", groupname_col="Country")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("Grouped by country of origin, with drivetrain and transmission details"),
    )
    .tab_stubhead(label="Model")
    .fmt_integer(columns="Year")
    .fmt_currency(columns="MSRP", decimals=0)
)

gt = humanize_labels(gt, display_df)

# Heading band — navy accent_tint for the Blues sequential theme
gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

# Small-Color polish
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)

# Row hairlines between body rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

gt = frame(gt)
gt.tab_source_note(source_note="Source: gtcars.csv dataset.")

finalize(gt, path="table.png", zoom=2.0, expand=15)
