import pandas as pd
from great_tables import GT, loc, md, style
from house_table import PALETTE, frame, hairlines, finalize, band, stub_tint, group_emphasis, humanize_labels

# Read the data
df = pd.read_csv("./gtcars.csv")

# Get top 10 most expensive cars
top_10 = df.nlargest(10, "msrp").copy()

# Sort by country, then by price descending for better grouping
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Create a display name combining manufacturer and model
top_10["car"] = top_10["mfr"] + " " + top_10["model"]

# Map drivetrain to display format
drivetrain_map = {
    "rwd": "RWD",
    "awd": "AWD",
    "fwd": "FWD"
}
top_10["drivetrain_display"] = top_10["drivetrain"].map(drivetrain_map)

# Map transmission to display format (remove numbers and letters suffixes for clarity)
def format_transmission(trsmn):
    if pd.isna(trsmn):
        return "—"
    trsmn = str(trsmn).lower()
    if trsmn.startswith("7a"):
        return "7-Speed Auto"
    elif trsmn.startswith("6a"):
        return "6-Speed Auto"
    elif trsmn.startswith("8a"):
        return "8-Speed Auto"
    elif trsmn.startswith("9a"):
        return "9-Speed Auto"
    elif trsmn.startswith("6m"):
        return "6-Speed Manual"
    elif trsmn.startswith("7m"):
        return "7-Speed Manual"
    elif trsmn.startswith("8m"):
        return "8-Speed Manual"
    elif trsmn == "1dd":
        return "Direct Drive"
    else:
        return trsmn.upper()

top_10["transmission_display"] = top_10["trsmn"].apply(format_transmission)

# Select and order columns for display
display_df = top_10[["car", "ctry_origin", "drivetrain_display", "transmission_display", "msrp"]].copy()
display_df.columns = ["car", "country", "drivetrain", "transmission", "msrp"]

# Create GT table with stub and grouping
gt = (
    GT(display_df, rowname_col="car", groupname_col="country")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("Ranked by MSRP, grouped by country of origin with drivetrain and transmission details"),
    )
    .tab_stubhead(label="Car")
    .fmt_currency(columns="msrp", decimals=0)
    .sub_missing(columns=["drivetrain", "transmission"], missing_text="—")
)

# Apply humanized labels
gt = humanize_labels(gt, display_df)

# Apply house formatting
gt = band(gt, hue="navy")
gt = stub_tint(gt, hue="navy")
gt = group_emphasis(gt)
gt = hairlines(gt)
gt = frame(gt)

# Add source note
gt = gt.tab_source_note(source_note="Source: provided dataset.")

finalize(gt, path="table.png")
