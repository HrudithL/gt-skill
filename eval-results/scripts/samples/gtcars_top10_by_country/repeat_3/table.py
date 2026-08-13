import pandas as pd
import numpy as np
from great_tables import GT, md
from gt_consistency import heatmap, band, stripe, stub_tint, frame, finalize

df = pd.read_csv("gtcars.csv")

# Step 1: Clean data and get top 10 most expensive
df = df.sort_values("msrp", ascending=False).head(10).reset_index(drop=True)
df = df[["mfr", "model", "ctry_origin", "msrp", "drivetrain", "trsmn"]].copy()

# Create display name: mfr + model for stub
df["car_name"] = df["mfr"] + " " + df["model"]
df = df.drop(columns=["mfr", "model"])

# Step 2: Organize columns - group by country
gt = (
    GT(df, rowname_col="car_name", groupname_col="ctry_origin")
    .cols_move_to_end(["msrp"])
    .cols_width(cases={
        "car_name": "200px",
        "drivetrain": "100px",
        "trsmn": "100px",
        "msrp": "120px"
    })
)

# Step 3: Big Color - msrp is neutral magnitude → Blues
cols = ["msrp"]
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))
gt = heatmap(gt, "msrp", kind="sequential", hue="neutral", domain=[lo, hi])

# Step 4: Heading band
gt = band(gt)

# Step 5: Small Color polish
gt = (
    gt
    .fmt_currency(columns=["msrp"], decimals=0, currency="USD")
    .sub_missing(columns=["msrp", "drivetrain", "trsmn"], missing_text="—")
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        row_striping_background_color="#F6F6F6",
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)

# Step 6: Titles & annotations
gt = (
    gt
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    .tab_source_note(source_note="Top 10 cars ranked by MSRP price, from highest to lowest.")
    .tab_source_note(source_note="Source: gtcars.csv")
)

# Step 7: Render
finalize(gt, "table.png")
