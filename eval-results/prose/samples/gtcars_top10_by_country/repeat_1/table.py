import pandas as pd
from great_tables import GT, style, loc

df = pd.read_csv("gtcars.csv")

top10 = df.nlargest(10, "msrp")[["model", "ctry_origin", "msrp", "drivetrain", "trsmn"]].copy()
top10 = top10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

top10["msrp"] = top10["msrp"].astype(float)
top10.columns = ["Model", "Country", "Price", "Drivetrain", "Transmission"]

top10_rows = df.nlargest(10, "msrp").index.tolist()

gt = (
    GT(top10, rowname_col="Model", groupname_col="Country")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    .cols_width(cases={
        "Price": "120px",
        "Drivetrain": "110px",
        "Transmission": "110px"
    })
    .tab_style(
        style=[
            style.fill(color="#9A7B33"),
            style.text(color="#ffffff", weight="bold")
        ],
        locations=loc.body(rows=list(range(len(top10))))
    )
    .fmt_currency(columns="Price", currency="USD", decimals=0)
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        table_border_top_style="solid",
        table_border_top_color="#CCCCCC",
        table_border_top_width="1px",
        table_border_bottom_style="solid",
        table_border_bottom_color="#CCCCCC",
        table_border_bottom_width="1px",
        table_border_left_style="solid",
        table_border_left_color="#CCCCCC",
        table_border_left_width="1px",
        table_border_right_style="solid",
        table_border_right_color="#CCCCCC",
        table_border_right_width="1px",
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
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub()
    )
    .opt_row_striping()
    .tab_source_note(source_note="Data includes top 10 vehicles by MSRP, sorted by country and price within each country.")
    .tab_source_note(source_note="Source: gtcars.csv")
)

gt.gtsave("table.png", expand=15)
