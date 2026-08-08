import pandas as pd
from great_tables import GT, md, style, loc
from house_table import PALETTE, frame, finalize, band, stripe, stub_tint, group_emphasis, humanize_labels

# Load the data
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
top_10 = df.nlargest(10, "msrp")[["mfr", "model", "year", "drivetrain", "trsmn", "ctry_origin", "msrp"]].copy()
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Create a display name combining manufacturer and model
top_10["car_name"] = top_10["mfr"] + " " + top_10["model"]
top_10["year"] = top_10["year"].astype(int)

# Format drivetrain and transmission for display
top_10["drivetrain"] = top_10["drivetrain"].str.upper()
top_10["transmission"] = top_10["trsmn"].str.upper()

# Keep only the columns we need
display_df = top_10[["car_name", "year", "drivetrain", "transmission", "ctry_origin", "msrp"]].copy()
display_df.columns = ["car_name", "year", "drivetrain", "transmission", "ctry_origin", "msrp"]

gt = (
    GT(display_df, rowname_col="car_name", groupname_col="ctry_origin")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("By country of origin, with drivetrain and transmission details"),
    )
    .tab_stubhead(label="Car")
    .fmt_integer(columns="year")
    .fmt_currency(columns="msrp", currency="USD", decimals=0)
)

gt = humanize_labels(
    gt,
    display_df,
    overrides={
        "ctry_origin": "Country",
        "msrp": "MSRP",
    },
)

# Color the MSRP column (sequential, neutral/Blues for price)
gt = gt.data_color(
    columns="msrp",
    palette="Blues",
    domain=[display_df["msrp"].min(), display_df["msrp"].max()],
    na_color=PALETTE["neutral"]["na_cell"],
    truncate=False,
    autocolor_text=True,
)

# Heading band with navy accent tint (matching the Blues heatmap)
gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color=PALETTE["neutral"]["column_label_rule"],
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

# Small-Color polish: stripe and stub tint
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)

# Row hairlines
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color=PALETTE["neutral"]["hairline"],
    table_body_hlines_width="1px",
)

gt = frame(gt)
gt = gt.tab_source_note(source_note="Source: provided dataset. MSRP in USD.")

finalize(gt, path="table.png", zoom=2.0, expand=15)
