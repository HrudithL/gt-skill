import pandas as pd
from great_tables import GT, loc, style

df = pd.read_csv('towny.csv')

# Calculate total population growth from 1996 to 2021
df['total_growth_pct'] = ((df['population_2021'] - df['population_1996']) / df['population_1996'] * 100)

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, 'total_growth_pct')[['name',
                                                'population_1996', 'density_1996',
                                                'population_2001', 'density_2001', 'pop_change_1996_2001_pct',
                                                'population_2006', 'density_2006', 'pop_change_2001_2006_pct',
                                                'population_2011', 'density_2011', 'pop_change_2006_2011_pct',
                                                'population_2016', 'density_2016', 'pop_change_2011_2016_pct',
                                                'population_2021', 'density_2021', 'pop_change_2016_2021_pct',
                                                'total_growth_pct']].reset_index(drop=True)

# Rename columns for clarity
top_15.columns = ['Town',
                  'Pop 1996', 'Dens 1996',
                  'Pop 2001', 'Dens 2001', '% Chg 96-01',
                  'Pop 2006', 'Dens 2006', '% Chg 01-06',
                  'Pop 2011', 'Dens 2011', '% Chg 06-11',
                  'Pop 2016', 'Dens 2016', '% Chg 11-16',
                  'Pop 2021', 'Dens 2021', '% Chg 16-21',
                  'Total % Chg 96-21']

# Format numeric columns
numeric_cols = {
    'Pop 1996': 0, 'Pop 2001': 0, 'Pop 2006': 0, 'Pop 2011': 0, 'Pop 2016': 0, 'Pop 2021': 0,
    'Dens 1996': 2, 'Dens 2001': 2, 'Dens 2006': 2, 'Dens 2011': 2, 'Dens 2016': 2, 'Dens 2021': 2,
    '% Chg 96-01': 1, '% Chg 01-06': 1, '% Chg 06-11': 1, '% Chg 11-16': 1, '% Chg 16-21': 1,
    'Total % Chg 96-21': 1
}

for col in numeric_cols:
    top_15[col] = top_15[col].apply(lambda x: f"{x:.{numeric_cols[col]}f}")

# Create GT table
gt = (GT(top_15)
      .tab_header(
          title="Ontario Towns: Population Growth Trends (1996-2021)",
          subtitle="Top 15 Fastest-Growing Towns - Population, Density & Change Rates"
      )
      .cols_label(Town="Town")
)

# Combine columns into groups for better readability
gt = (gt
      .tab_spanner(label="1996", columns=["Pop 1996", "Dens 1996"])
      .tab_spanner(label="2001", columns=["Pop 2001", "Dens 2001", "% Chg 96-01"])
      .tab_spanner(label="2006", columns=["Pop 2006", "Dens 2006", "% Chg 01-06"])
      .tab_spanner(label="2011", columns=["Pop 2011", "Dens 2011", "% Chg 06-11"])
      .tab_spanner(label="2016", columns=["Pop 2016", "Dens 2016", "% Chg 11-16"])
      .tab_spanner(label="2021", columns=["Pop 2021", "Dens 2021", "% Chg 16-21"])
      .tab_spanner(label="Overall Growth", columns=["Total % Chg 96-21"])
      .opt_row_striping()
)

gt.gtsave("table.png")
