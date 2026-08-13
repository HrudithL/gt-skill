import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, heatmap, humanize_labels

# Read the islands data
islands = pd.read_csv("islands.csv")

gt = (
    GT(islands, rowname_col="name")
    .tab_header(
        title="Island Sizes",
        subtitle=md("Land area by island, in thousands of square kilometers"),
    )
    .fmt_number(columns="size", decimals=0)
)

# Humanize the column label
gt = humanize_labels(gt, islands)

# Set column widths
gt = gt.cols_width(
    cases={
        "name": "180px",
        "size": "110px",
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

# Apply heatmap to the size column
gt = heatmap(gt, "size", kind="sequential", hue="neutral")

# Apply heading band
gt = band(gt, hue="navy")

# Apply striping and tinting
gt = stripe(gt)

# Apply the frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Add source notes
gt = gt.tab_source_note(
    source_note="Size represents land area in thousands of square kilometers."
)
gt = gt.tab_source_note(
    source_note="Source: provided dataset."
)

# Finalize and render
finalize(gt, path="table.png")
