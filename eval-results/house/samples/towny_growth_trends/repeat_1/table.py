import pandas as pd
from great_tables import GT, md, html, style, loc
import sys
sys.path.insert(0, '/Users/hrudithl/Documents/posit-dev/gtskill/runs/sweep/20260813_080322_house_6prompts/prompts/towny_growth_trends/repeat_1/.claude/skills/great-tables-house')
from scripts.house_table import PALETTE, frame, finalize, heatmap, hairlines

# Read data
df = pd.read_csv('./towny.csv')

# Calculate overall population growth (1996-2021)
df['overall_growth'] = ((df['population_2021'] - df['population_1996']) / df['population_1996']).fillna(-1)

# Filter towns with data for all census years and rank by growth
df_with_1996 = df[(df['population_1996'].notna()) & (df['population_2021'].notna())].copy()
df_ranked = df_with_1996.sort_values('overall_growth', ascending=False)

# Get top 15 fastest-growing towns
top_15 = df_ranked.head(15).copy()

# Sort by name for display
top_15 = top_15.sort_values('name').reset_index(drop=True)

# Build display data with proper columns
# Organize as: Town | Density (6 years) | Pop Change (5 periods)
display_data = []
for _, row in top_15.iterrows():
    row_dict = {
        'Town': row['name'],
        'Density 1996': row['density_1996'],
        'Density 2001': row['density_2001'],
        'Density 2006': row['density_2006'],
        'Density 2011': row['density_2011'],
        'Density 2016': row['density_2016'],
        'Density 2021': row['density_2021'],
        'Δ 1996–2001': f"{row['pop_change_1996_2001_pct']*100:.1f}%" if pd.notna(row['pop_change_1996_2001_pct']) else "—",
        'Δ 2001–2006': f"{row['pop_change_2001_2006_pct']*100:.1f}%" if pd.notna(row['pop_change_2001_2006_pct']) else "—",
        'Δ 2006–2011': f"{row['pop_change_2006_2011_pct']*100:.1f}%" if pd.notna(row['pop_change_2006_2011_pct']) else "—",
        'Δ 2011–2016': f"{row['pop_change_2011_2016_pct']*100:.1f}%" if pd.notna(row['pop_change_2011_2016_pct']) else "—",
        'Δ 2016–2021': f"{row['pop_change_2016_2021_pct']*100:.1f}%" if pd.notna(row['pop_change_2016_2021_pct']) else "—",
    }
    display_data.append(row_dict)

gt_data = pd.DataFrame(display_data)

# Create GT object
gt = GT(gt_data.set_index('Town'))

# Apply frame
gt = frame(gt)

# Format density columns (numeric, 1 decimal place)
density_cols = ['Density 1996', 'Density 2001', 'Density 2006', 'Density 2011', 'Density 2016', 'Density 2021']
for col in density_cols:
    gt = gt.fmt_number(
        columns=col,
        decimals=1
    )

# Add title and subtitle
gt = gt.tab_header(
    title="Population Growth Trends: Top 15 Fastest-Growing Ontario Towns",
    subtitle="Census years 1996–2021"
)

# Add source notes
gt = gt.tab_source_note(
    source_note=md(
        "**Top 15 towns ranked by overall population growth (1996–2021).** "
        "Density measured in persons per square kilometer. "
        "Percentage changes show population growth between consecutive census periods."
    )
)

gt = gt.tab_source_note(
    source_note="Source: Provided dataset."
)

# Apply heatmap to density columns
gt = heatmap(
    gt,
    columns=density_cols,
    kind='sequential',
    hue='neutral'
)

# Apply hairlines
gt = hairlines(gt)

# Finalize and save
finalize(gt, path="table.png")
