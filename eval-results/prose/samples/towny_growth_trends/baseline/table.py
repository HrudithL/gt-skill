import pandas as pd
import numpy as np
from great_tables import GT

df = pd.read_csv("towny.csv")

# Calculate overall growth from 1996 to 2021
df['overall_growth_pct'] = ((df['population_2021'] - df['population_1996']) / df['population_1996'] * 100)

# Filter out rows with missing 1996 data
df = df[df['population_1996'].notna()]

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'overall_growth_pct')

# Create a clean display table with density and percentage changes
display_data = []

for _, row in top_15.iterrows():
    town_name = row['name']

    # Density values
    density_1996 = row['density_1996']
    density_2001 = row['density_2001']
    density_2006 = row['density_2006']
    density_2011 = row['density_2011']
    density_2016 = row['density_2016']
    density_2021 = row['density_2021']

    # Calculate percentage changes between periods
    change_96_01 = ((density_2001 - density_1996) / density_1996 * 100) if density_1996 > 0 else 0
    change_01_06 = ((density_2006 - density_2001) / density_2001 * 100) if density_2001 > 0 else 0
    change_06_11 = ((density_2011 - density_2006) / density_2006 * 100) if density_2006 > 0 else 0
    change_11_16 = ((density_2016 - density_2011) / density_2011 * 100) if density_2011 > 0 else 0
    change_16_21 = ((density_2021 - density_2016) / density_2016 * 100) if density_2016 > 0 else 0

    display_data.append({
        'Town': town_name,
        'Density 1996': round(density_1996, 1),
        '1996-2001 Δ%': round(change_96_01, 1),
        'Density 2001': round(density_2001, 1),
        '2001-2006 Δ%': round(change_01_06, 1),
        'Density 2006': round(density_2006, 1),
        '2006-2011 Δ%': round(change_06_11, 1),
        'Density 2011': round(density_2011, 1),
        '2011-2016 Δ%': round(change_11_16, 1),
        'Density 2016': round(density_2016, 1),
        '2016-2021 Δ%': round(change_16_21, 1),
        'Density 2021': round(density_2021, 1),
        'Overall Growth %': round(row['overall_growth_pct'], 1)
    })

display_df = pd.DataFrame(display_data)

# Create GT table
gt = (
    GT(display_df)
    .fmt_number(
        columns=[col for col in display_df.columns if col not in ['Town']],
        decimals=1
    )
    .tab_header(
        title="Population Growth Trends: Top 15 Fastest-Growing Ontario Towns",
        subtitle="Density Changes (persons/km²) Across Census Periods 1996-2021"
    )
    .tab_spanner(
        label="1996-2001",
        columns=["Density 1996", "1996-2001 Δ%", "Density 2001"]
    )
    .tab_spanner(
        label="2001-2006",
        columns=["2001-2006 Δ%", "Density 2006"]
    )
    .tab_spanner(
        label="2006-2011",
        columns=["2006-2011 Δ%", "Density 2011"]
    )
    .tab_spanner(
        label="2011-2016",
        columns=["2011-2016 Δ%", "Density 2016"]
    )
    .tab_spanner(
        label="2016-2021",
        columns=["2016-2021 Δ%", "Density 2021"]
    )
    .data_color(
        columns=["1996-2001 Δ%", "2001-2006 Δ%", "2006-2011 Δ%", "2011-2016 Δ%", "2016-2021 Δ%", "Overall Growth %"],
        palette=["#d73027", "#fee090", "#1a9850"],
        domain=[-100, 100],
        na_color="white"
    )
    .cols_label(
        **{
            'Town': 'Town',
            'Density 1996': '1996',
            '1996-2001 Δ%': 'Change %',
            'Density 2001': '2001',
            '2001-2006 Δ%': 'Change %',
            'Density 2006': '2006',
            '2006-2011 Δ%': 'Change %',
            'Density 2011': '2011',
            '2011-2016 Δ%': 'Change %',
            'Density 2016': '2016',
            '2016-2021 Δ%': 'Change %',
            'Density 2021': '2021',
            'Overall Growth %': '1996-2021 Growth %'
        }
    )
    .tab_source_note(
        source_note="Density measured in persons per square kilometer (persons/km²). Δ% represents percentage change from previous census period."
    )
)

gt.gtsave("table.png")
