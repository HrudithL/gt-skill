import pandas as pd
from great_tables import GT, loc, style

from pathlib import Path
skill_path = Path(__file__).parent / ".claude/skills/great-tables-house/scripts"
import sys
sys.path.insert(0, str(skill_path))
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap

df = pd.read_csv("islands.csv")

gt = (
    GT(df, rowname_col="name")
    .tab_header(
        title="Island Sizes",
        subtitle="Area in thousands of square kilometers"
    )
    .tab_stubhead(label="Island")
    .fmt_number(columns="size", decimals=0, use_seps=True)
    .cols_label(size="Area (1000 km²)")
)

gt = heatmap(gt, "size", kind="sequential", hue="neutral")
gt = band(gt, hue="navy")

if len(df) >= 10:
    gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

gt = gt.tab_source_note(source_note="Source: provided dataset.")
gt = hairlines(gt)
gt = frame(gt)
finalize(gt)
