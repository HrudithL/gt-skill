import pandas as pd
from great_tables import GT, md, loc, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, group_emphasis, humanize_labels

df = pd.read_csv("gtcars.csv")

# Select top 10 most expensive cars and sort by country, then price
top_10 = df.nlargest(10, "msrp").copy()
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False])

# Create readable car identifier (mfr + model)
top_10["car"] = top_10["mfr"] + " " + top_10["model"]

# Map transmission codes to readable format
transmission_map = {
    "7a": "7-Speed Auto",
    "7m": "7-Speed Manual",
    "6a": "6-Speed Auto",
    "6m": "6-Speed Manual",
    "8a": "8-Speed Auto",
    "8am": "8-Speed Auto/Manual",
    "9a": "9-Speed Auto",
    "1dd": "Direct Drive",
}
top_10["transmission"] = top_10["trsmn"].map(transmission_map)

# Map drivetrain codes to readable format
drivetrain_map = {
    "rwd": "Rear Wheel Drive",
    "awd": "All Wheel Drive",
    "fwd": "Front Wheel Drive",
}
top_10["drivetrain_display"] = top_10["drivetrain"].map(drivetrain_map)

# Select and reorder columns
display_df = top_10[["car", "ctry_origin", "drivetrain_display", "transmission", "msrp"]].copy()
display_df.columns = ["car", "country_origin", "drivetrain", "transmission", "msrp"]

# Build the GT table
gt = (
    GT(display_df, rowname_col="car", groupname_col="country_origin")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("Performance vehicles ranked by MSRP, grouped by country of origin"),
    )
    .tab_stubhead(label="Vehicle")
    .fmt_currency(columns="msrp", decimals=0)
)

gt = humanize_labels(
    gt,
    display_df,
    overrides={"country_origin": "Country", "drivetrain": "Drivetrain", "transmission": "Transmission", "msrp": "MSRP"},
)

# Set column widths
gt = gt.cols_width(
    cases={
        "car": "180px",
        "country_origin": "130px",
        "drivetrain": "150px",
        "transmission": "140px",
        "msrp": "120px",
    }
)

# Set padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply branding and styling
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)

# Add source notes
gt = (
    gt.tab_source_note(
        source_note="Ranking based on manufacturer suggested retail price (MSRP) at time of model year."
    )
    .tab_source_note(source_note="Source: gtcars dataset.")
)

# Apply frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Render
finalize(gt)
