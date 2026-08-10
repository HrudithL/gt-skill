import pandas as pd
from great_tables import GT, loc, style

# Read the data
df = pd.read_csv('towny.csv')

# Calculate overall growth rate from 1996 to 2021
df['overall_growth_pct'] = ((df['population_2021'] - df['population_1996']) / df['population_1996'] * 100).round(2)

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'overall_growth_pct')[['name', 'population_1996', 'population_2001', 'population_2006', 'population_2011', 'population_2016', 'population_2021',
                                                  'density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021',
                                                  'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct', 'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct']]

# Reset index for cleaner display
top_15 = top_15.reset_index(drop=True)

# Create density change columns
top_15['density_change_96_01_pct'] = ((top_15['density_2001'] - top_15['density_1996']) / top_15['density_1996'] * 100).round(2)
top_15['density_change_01_06_pct'] = ((top_15['density_2006'] - top_15['density_2001']) / top_15['density_2001'] * 100).round(2)
top_15['density_change_06_11_pct'] = ((top_15['density_2011'] - top_15['density_2006']) / top_15['density_2006'] * 100).round(2)
top_15['density_change_11_16_pct'] = ((top_15['density_2016'] - top_15['density_2011']) / top_15['density_2011'] * 100).round(2)
top_15['density_change_16_21_pct'] = ((top_15['density_2021'] - top_15['density_2016']) / top_15['density_2016'] * 100).round(2)

# Select columns for the final table
final_df = top_15[['name',
                    'population_1996', 'population_2001', 'population_2006', 'population_2011', 'population_2016', 'population_2021',
                    'density_1996', 'density_2001', 'density_2006', 'density_2011', 'density_2016', 'density_2021',
                    'pop_change_1996_2001_pct', 'pop_change_2001_2006_pct', 'pop_change_2006_2011_pct', 'pop_change_2011_2016_pct', 'pop_change_2016_2021_pct',
                    'density_change_96_01_pct', 'density_change_01_06_pct', 'density_change_06_11_pct', 'density_change_11_16_pct', 'density_change_16_21_pct']]

# Rename columns for clarity
final_df.columns = ['Town Name',
                     'Pop 1996', 'Pop 2001', 'Pop 2006', 'Pop 2011', 'Pop 2016', 'Pop 2021',
                     'Dens 1996', 'Dens 2001', 'Dens 2006', 'Dens 2011', 'Dens 2016', 'Dens 2021',
                     'Pop Δ 96-01 %', 'Pop Δ 01-06 %', 'Pop Δ 06-11 %', 'Pop Δ 11-16 %', 'Pop Δ 16-21 %',
                     'Dens Δ 96-01 %', 'Dens Δ 01-06 %', 'Dens Δ 06-11 %', 'Dens Δ 11-16 %', 'Dens Δ 16-21 %']

# Create the GT table
gt = (GT(final_df)
      .tab_header(
          title="Top 15 Fastest-Growing Ontario Towns",
          subtitle="Population & Density Trends Across Census Years (1996-2021)")
      .tab_spanner(
          label="Population",
          columns=['Pop 1996', 'Pop 2001', 'Pop 2006', 'Pop 2011', 'Pop 2016', 'Pop 2021'])
      .tab_spanner(
          label="Population % Change",
          columns=['Pop Δ 96-01 %', 'Pop Δ 01-06 %', 'Pop Δ 06-11 %', 'Pop Δ 11-16 %', 'Pop Δ 16-21 %'])
      .tab_spanner(
          label="Density (persons/km²)",
          columns=['Dens 1996', 'Dens 2001', 'Dens 2006', 'Dens 2011', 'Dens 2016', 'Dens 2021'])
      .tab_spanner(
          label="Density % Change",
          columns=['Dens Δ 96-01 %', 'Dens Δ 01-06 %', 'Dens Δ 06-11 %', 'Dens Δ 11-16 %', 'Dens Δ 16-21 %'])
      .fmt_integer(columns=['Pop 1996', 'Pop 2001', 'Pop 2006', 'Pop 2011', 'Pop 2016', 'Pop 2021'])
      .fmt_number(columns=['Dens 1996', 'Dens 2001', 'Dens 2006', 'Dens 2011', 'Dens 2016', 'Dens 2021'], decimals=1)
      .fmt_number(columns=['Pop Δ 96-01 %', 'Pop Δ 01-06 %', 'Pop Δ 06-11 %', 'Pop Δ 11-16 %', 'Pop Δ 16-21 %',
                           'Dens Δ 96-01 %', 'Dens Δ 01-06 %', 'Dens Δ 06-11 %', 'Dens Δ 11-16 %', 'Dens Δ 16-21 %'],
               decimals=1)
      .tab_style(
          style=style.fill(color='#f0f0f0'),
          locations=loc.body(columns=['Town Name']))
      .cols_width(
          {
              'Town Name': '150px',
              'Pop 1996': '80px',
              'Pop 2001': '80px',
              'Pop 2006': '80px',
              'Pop 2011': '80px',
              'Pop 2016': '80px',
              'Pop 2021': '80px',
              'Dens 1996': '85px',
              'Dens 2001': '85px',
              'Dens 2006': '85px',
              'Dens 2011': '85px',
              'Dens 2016': '85px',
              'Dens 2021': '85px',
          })
      )

gt.gtsave("table.png")
