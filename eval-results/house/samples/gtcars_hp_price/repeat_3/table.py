import pandas as pd
from great_tables import GT, md, style, loc
import sys
sys.path.insert(0, '.claude/skills/great-tables-house/scripts')
from house_table import PALETTE, frame, finalize, band, stripe, stub_tint, humanize_labels, heatmap

df = pd.read_csv('gtcars.csv')

# Select only GT cars and keep model, hp, and msrp
gt_cars = df[df['model'] == 'GT'].copy()
gt_cars = gt_cars[['mfr', 'model', 'hp', 'msrp']].reset_index(drop=True)
gt_cars.columns = ['manufacturer', 'model', 'horsepower', 'price']

# Create GT table with manufacturer as stub (row identifier)
gt = (
    GT(gt_cars, rowname_col='manufacturer')
    .tab_header(
        title="GT Performance Cars",
        subtitle=md("Horsepower and price specifications"),
    )
    .tab_stubhead(label="Manufacturer")
    .fmt_integer(columns='horsepower')
    .fmt_currency(columns='price', decimals=0)
    .sub_missing(columns=['horsepower', 'price'], missing_text="—")
)

gt = humanize_labels(gt, gt_cars)

# Apply color to price (sequential/neutral — just showing the magnitude)
gt = heatmap(gt, 'price', kind='sequential', hue='neutral')

# Heading band with light tint
gt = gt.tab_options(
    column_labels_background_color=PALETTE['accent_tint']['navy'],
    column_labels_border_bottom_color=PALETTE['neutral']['column_label_rule'],
    column_labels_border_bottom_width='2px',
    column_labels_border_bottom_style='solid',
)

# Polish: stub tint, row hairlines
gt = stub_tint(gt, hue='navy')
gt = gt.tab_options(
    table_body_hlines_style='solid',
    table_body_hlines_color=PALETTE['neutral']['hairline'],
    table_body_hlines_width='1px',
)
gt = frame(gt)

# Add source note
gt = gt.tab_source_note(source_note="Source: provided dataset.")

finalize(gt, path="table.png", zoom=2.0, expand=15)
