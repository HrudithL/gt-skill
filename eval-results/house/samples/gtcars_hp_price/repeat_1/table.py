import pandas as pd
from great_tables import GT, loc, style
from house_table import PALETTE, frame, finalize, humanize_labels, heatmap, stripe, stub_tint


def build_table():
    """Build a table of GT cars with horsepower and price."""
    df = pd.read_csv("gtcars.csv")

    # Select only GT cars and relevant columns
    gt_cars = df[df["model"].str.contains("GT", case=False, na=False)][
        ["mfr", "model", "hp", "msrp"]
    ].reset_index(drop=True)
    gt_cars = gt_cars.rename(columns={"mfr": "manufacturer", "model": "model", "hp": "horsepower", "msrp": "price"})

    gt = (
        GT(gt_cars)
        .tab_header(
            title="GT Performance Cars",
            subtitle="Horsepower and price for sports cars with GT in the model name",
        )
        .fmt_number(columns="horsepower", decimals=0)
        .fmt_currency(columns="price", decimals=0)
    )

    gt = humanize_labels(gt, gt_cars)

    # Color the price column with a sequential heatmap (neutral blues)
    gt = heatmap(gt, "price", kind="sequential", hue="neutral")

    # Heading band with light navy tint
    gt = gt.tab_options(
        column_labels_background_color=PALETTE["accent_tint"]["navy"],
        column_labels_border_bottom_color=PALETTE["neutral"]["column_label_rule"],
        column_labels_border_bottom_width="2px",
        column_labels_border_bottom_style="solid",
    )

    # Row hairlines between body rows
    gt = gt.tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color=PALETTE["neutral"]["hairline"],
        table_body_hlines_width="1px",
    )

    # Source note
    gt = gt.tab_source_note(source_note="Source: provided dataset.")

    # Frame and finalize
    gt = frame(gt)
    finalize(gt, path="table.png", zoom=2.0, expand=15)
    return gt


if __name__ == "__main__":
    build_table()
