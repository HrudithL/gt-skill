import pandas as pd
from great_tables import GT, md, style, loc
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, heatmap, humanize_labels

# Load the islands data
islands = pd.read_csv("islands.csv")

# Create the GT table
gt = (
    GT(islands, rowname_col="name")
    .tab_header(
        title="World Islands by Size",
        subtitle="Land area in thousands of square kilometers"
    )
    .fmt_number(columns="size", decimals=0, use_seps=True)
)

# Humanize labels
gt = humanize_labels(gt, islands)

# Apply column width and padding
gt = gt.cols_width(cases={
    "name": "150px",
    "size": "120px",
})
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply heatmap coloring to size (sequential, neutral = Blues)
gt = heatmap(gt, "size", kind="sequential", hue="neutral")

# Apply heading band styling
gt = band(gt, hue="navy")

# Apply striping since not all cells are heatmap-covered
gt = stripe(gt)

# Add analytical and provenance notes
gt = (
    gt.tab_source_note(
        source_note="Size represents land area in thousands of square kilometers."
    )
    .tab_source_note(
        source_note="Source: provided dataset."
    )
)

# Apply hairlines and frame
gt = hairlines(gt)
gt = frame(gt)

# Finalize and save
finalize(gt, path="table.png")
