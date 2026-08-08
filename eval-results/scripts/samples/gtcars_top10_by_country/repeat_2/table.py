import pandas as pd
from great_tables import GT, md
from gt_consistency import PALETTE, frame, finalize, band, stripe, stub_tint

df = pd.read_csv("gtcars.csv")

df = df.dropna(subset=["msrp"])
df = df[df["msrp"] > 0]
df = df.sort_values("msrp", ascending=False)

df_top = df.nlargest(10, "msrp").copy()
df_top = df_top.sort_values("ctry_origin")

df_display = df_top[["ctry_origin", "mfr", "model", "year", "msrp", "drivetrain", "trsmn"]].copy()
df_display.columns = ["Country", "Manufacturer", "Model", "Year", "Price", "Drivetrain", "Transmission"]

df_display["Price"] = df_display["Price"].astype(float)
df_display["Year"] = df_display["Year"].astype(int)

gt = (
    GT(df_display, groupname_col="Country")
    .fmt_currency(columns="Price", currency="USD", decimals=0)
    .fmt_integer(columns="Year")
    .tab_options(
        row_group_background_color="#F0F0F0",
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin with Drivetrain and Transmission Details"
    )
    .tab_source_note(source_note="Source: gtcars.csv dataset")
)

gt = frame(gt)
gt = band(gt, shade="dark", hue="navy")
gt = stripe(gt)

gt.gtsave("table.png", expand=15, zoom=2.0)
