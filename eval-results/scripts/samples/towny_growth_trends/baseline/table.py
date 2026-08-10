import pandas as pd
from great_tables import GT, loc, style

# Read the data
df = pd.read_csv('towny.csv')

# Calculate overall population growth (1996-2021)
df['overall_growth_pct'] = ((df['population_2021'] - df['population_1996']) / df['population_1996'] * 100).round(2)

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'overall_growth_pct')[['name', 'density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021']].copy()

# Calculate percentage changes between census periods
top_15['change_1996_2001'] = (((top_15['density_2001'] - top_15['density_1996']) / top_15['density_1996'] * 100)).round(2)
top_15['change_2001_2006'] = (((top_15['density_2006'] - top_15['density_2001']) / top_15['density_2001'] * 100)).round(2)
top_15['change_2006_2011'] = (((top_15['density_2011'] - top_15['density_2006']) / top_15['density_2006'] * 100)).round(2)
top_15['change_2011_2016'] = (((top_15['density_2016'] - top_15['density_2011']) / top_15['density_2011'] * 100)).round(2)
top_15['change_2016_2021'] = (((top_15['density_2021'] - top_15['density_2016']) / top_15['density_2016'] * 100)).round(2)

# Round density values to 1 decimal place
top_15['density_1996'] = top_15['density_1996'].round(1)
top_15['density_2001'] = top_15['density_2001'].round(1)
top_15['density_2006'] = top_15['density_2006'].round(1)
top_15['density_2011'] = top_15['density_2011'].round(1)
top_15['density_2016'] = top_15['density_2016'].round(1)
top_15['density_2021'] = top_15['density_2021'].round(1)

# Reset index for cleaner display
top_15 = top_15.reset_index(drop=True)

# Create the GT table
gt = (
    GT(top_15)
    .tab_header(
        title="Population Density Growth Trends",
        subtitle="Top 15 Fastest-Growing Ontario Towns (1996-2021)"
    )
    .cols_label(
        name="Town",
        density_1996="1996\nDensity",
        density_2001="2001\nDensity",
        density_2006="2006\nDensity",
        density_2011="2011\nDensity",
        density_2016="2016\nDensity",
        density_2021="2021\nDensity",
        change_1996_2001="1996-2001\n% Change",
        change_2001_2006="2001-2006\n% Change",
        change_2006_2011="2006-2011\n% Change",
        change_2011_2016="2011-2016\n% Change",
        change_2016_2021="2016-2021\n% Change"
    )
    .fmt_number(
        columns=['density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021'],
        decimals=1
    )
    .fmt_number(
        columns=['change_1996_2001', 'change_2001_2006', 'change_2006_2011', 'change_2011_2016', 'change_2016_2021'],
        decimals=2
    )
    .tab_style(
        style=style.fill(color="#f0f0f0"),
        locations=loc.column_labels()
    )
)

# Save as PNG
gt.gtsave("table.png")
print("Table saved to table.png")
