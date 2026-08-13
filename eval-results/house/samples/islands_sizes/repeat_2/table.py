import pandas as pd
from great_tables import GT, md
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe,
    stub_tint, heatmap, humanize_labels
)

def build_islands_table():
    """Build and render the islands and their sizes table."""
    islands = pd.read_csv("islands.csv")

    gt = (
        GT(islands, rowname_col="name")
        .tab_header(
            title="Island Sizes",
            subtitle=md("Geographic area in thousands of square kilometers")
        )
        .tab_stubhead(label="Island")
        .fmt_number(columns="size", decimals=0, use_seps=True)
        .sub_missing(columns=["size"], missing_text="—")
    )

    gt = humanize_labels(gt, islands)

    gt = gt.cols_width(cases={"name": "150px", "size": "120px"})
    gt = gt.tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )

    # Sequential heatmap for island size (the hero measure)
    gt = heatmap(gt, "size", kind="sequential", hue="neutral")

    # Heading band with the house default dark shade
    gt = band(gt, hue="navy")

    # Small-color polish: striping and stub tint
    gt = stripe(gt)
    gt = stub_tint(gt, hue="navy")

    # Source notes and frame
    gt = (
        gt.tab_source_note(
            source_note="Island sizes are expressed in thousands of square kilometers."
        )
        .tab_source_note(source_note="Source: provided dataset.")
    )

    gt = hairlines(gt)
    gt = frame(gt)
    finalize(gt, path="table.png")
    return gt

if __name__ == "__main__":
    build_islands_table()
