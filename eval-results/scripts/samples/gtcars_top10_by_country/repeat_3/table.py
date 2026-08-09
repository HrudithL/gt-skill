import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from gt_consistency import frame, finalize, band, stripe, stub_tint

df = pd.read_csv("./gtcars.csv")

df = df.dropna(subset=["msrp"])
df = df[df["msrp"] > 0].copy()
df = df.sort_values("msrp", ascending=False).head(10)

df = df[["mfr", "model", "year", "drivetrain", "trsmn", "ctry_origin", "msrp"]].copy()
df = df.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

df.columns = ["Manufacturer", "Model", "Year", "Drivetrain", "Transmission", "Country", "MSRP"]

gt = (
    GT(df, rowname_col=None, groupname_col="Country")
    .cols_hide(columns=["Country"])
    .fmt_integer(columns=["Year"])
    .fmt_currency(columns=["MSRP"], currency="USD")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by country of origin with drivetrain and transmission"
    )
)

gt = band(gt, shade="dark", hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

gt = gt.tab_options(
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_color="#CCCCCC",
    table_border_top_width="1px",
    table_border_top_color="#E8E8E8",
    table_border_bottom_width="1px",
    table_border_bottom_color="#E8E8E8",
    table_border_left_width="1px",
    table_border_left_color="#E8E8E8",
    table_border_right_width="1px",
    table_border_right_color="#E8E8E8",
)

gt = frame(gt)
finalize(gt)
