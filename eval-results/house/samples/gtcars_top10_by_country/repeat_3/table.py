import pandas as pd
from great_tables import GT, md, style, loc
from house_table import PALETTE, frame, finalize, humanize_labels, heatmap, band, group_emphasis

# Read the data and filter to top 10 most expensive cars
df = pd.read_csv("gtcars.csv")
df_sorted = df.nlargest(10, "msrp")[["mfr", "model", "year", "drivetrain", "trsmn", "ctry_origin", "msrp"]].copy()

# Map drivetrain and transmission to readable labels
drivetrain_map = {
    "rwd": "RWD",
    "awd": "AWD",
    "fwd": "FWD",
}
trsmn_map = {
    "6m": "6-Speed Manual",
    "6a": "6-Speed Auto",
    "7a": "7-Speed Auto",
    "7m": "7-Speed Manual",
    "8a": "8-Speed Auto",
    "8am": "8-Speed Auto/Manual",
    "9a": "9-Speed Auto",
    "1dd": "1-Speed Direct Drive",
}

df_sorted["drivetrain"] = df_sorted["drivetrain"].map(drivetrain_map)
df_sorted["transmission"] = df_sorted["trsmn"].map(trsmn_map)
df_sorted["car"] = df_sorted["mfr"] + " " + df_sorted["model"]

# Create a display dataframe with the columns we want
display_df = df_sorted[["car", "year", "drivetrain", "transmission", "ctry_origin", "msrp"]].copy()
display_df.columns = ["car", "year", "drivetrain", "transmission", "country", "msrp"]
display_df = display_df.sort_values(["country", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Create the GT table with country grouping
gt = (
    GT(display_df, rowname_col="car", groupname_col="country")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("Grouped by country of origin — showing drivetrain, transmission, and MSRP")
    )
    .tab_stubhead(label="Car")
    .fmt_integer(columns="year")
    .fmt_currency(columns="msrp", decimals=0)
    .sub_missing(columns=["year", "drivetrain", "transmission"], missing_text="—")
)

# Apply humanize_labels for column headers
gt = humanize_labels(
    gt,
    display_df,
    overrides={"msrp": "MSRP"}
)

# Apply the sequential heatmap to MSRP (the hero measure)
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral")

# Apply the heading band with navy accent tint
gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color=PALETTE["neutral"]["column_label_rule"],
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

# Apply stub tint to harmonize with the navy heatmap
gt = gt.tab_style(style=style.fill(color=PALETTE["washed"]["navy"]), locations=loc.stub())

# Apply group emphasis for country headers
gt = group_emphasis(gt)

# Apply row hairlines
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color=PALETTE["neutral"]["hairline"],
    table_body_hlines_width="1px",
)

# Apply the frame
gt = frame(gt)

# Add source note
gt = gt.tab_source_note(source_note="Source: provided gtcars dataset.")

# Finalize and render
finalize(gt, path="table.png", zoom=2.0, expand=15)
