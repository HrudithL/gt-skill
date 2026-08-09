import pandas as pd
from great_tables import GT, md, loc, style
from house_table import PALETTE, frame, finalize, heatmap, humanize_labels


def build_islands_table():
    """Build and render the islands and their sizes table."""
    islands = pd.read_csv("islands.csv")

    gt = (
        GT(islands, rowname_col="name")
        .tab_header(
            title="Island Sizes",
            subtitle=md("Area of major islands and continents by size"),
        )
        .tab_stubhead(label="Island")
        .fmt_number(columns="size", decimals=0, use_seps=True)
    )

    gt = humanize_labels(gt, islands)

    # Sequential heatmap: magnitude column colored with Blues (neutral)
    gt = heatmap(gt, "size", kind="sequential", hue="neutral")

    # Heading band: light tint with navy accent
    gt = gt.tab_options(
        column_labels_background_color="#C9E0F0",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        column_labels_border_bottom_style="solid",
    )

    # Row striping for readability (48 rows is well above the >=10 gate)
    gt = gt.opt_row_striping().tab_options(
        row_striping_background_color=PALETTE["neutral"]["row_stripe"],
    )

    # Row hairlines between body rows
    gt = gt.tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )

    # Boxed frame
    gt = frame(gt)

    # Source note
    gt = gt.tab_source_note(source_note="Source: provided dataset.")

    # Finalize and render
    finalize(gt, path="table.png", zoom=2.0, expand=15)
    return gt


if __name__ == "__main__":
    build_islands_table()
