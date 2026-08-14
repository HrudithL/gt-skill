import pandas as pd
from great_tables import GT
from great_tables.data import exibble

# Read the data
df = pd.read_csv('towny.csv')

# Calculate overall population growth from 1996 to 2021
df['total_growth_pct'] = ((df['population_2021'] - df['population_1996']) / df['population_1996']) * 100

# Sort by total growth and get top 15
top_15 = df.nlargest(15, 'total_growth_pct').copy()

# Prepare the table data with town names and density/change information
result_data = []
for _, row in top_15.iterrows():
    result_data.append({
        'Town': row['name'],
        'Density 1996': f"{row['density_1996']:.1f}",
        '% Change 1996-2001': f"{row['pop_change_1996_2001_pct']*100:.1f}%",
        'Density 2001': f"{row['density_2001']:.1f}",
        '% Change 2001-2006': f"{row['pop_change_2001_2006_pct']*100:.1f}%",
        'Density 2006': f"{row['density_2006']:.1f}",
        '% Change 2006-2011': f"{row['pop_change_2006_2011_pct']*100:.1f}%",
        'Density 2011': f"{row['density_2011']:.1f}",
        '% Change 2011-2016': f"{row['pop_change_2011_2016_pct']*100:.1f}%",
        'Density 2016': f"{row['density_2016']:.1f}",
        '% Change 2016-2021': f"{row['pop_change_2016_2021_pct']*100:.1f}%",
        'Density 2021': f"{row['density_2021']:.1f}",
        'Overall Growth %': f"{row['total_growth_pct']:.1f}%",
    })

result_df = pd.DataFrame(result_data)

# Create the table
gt = GT(result_df)
gt = gt.tab_header(
    title="Population Growth Trends: Top 15 Fastest-Growing Ontario Towns",
    subtitle="Population Density Changes Across Census Years (1996-2021) with Percentage Changes Between Periods"
)

# Render and save
gt.gtsave('table.png')
print("Table created and saved to table.png")
