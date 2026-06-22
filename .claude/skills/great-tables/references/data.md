# Data Understanding Guide

How to read, interpret, and evaluate data before building a table. **Do this before writing any GT code.**

## Step 1: Structural Inspection

Before thinking about presentation, understand what you have:

```python
df = pd.read_csv("data.csv")
print(df.shape)          # How many rows and columns?
print(df.dtypes)         # What types are the columns?
print(df.head(10))       # What do the first rows look like?
print(df.describe())     # What are the distributions?
print(df.isnull().sum()) # Where is data missing?
```

Answer these questions:
- **What is a row?** Each row should represent one "thing" — a year, a person, a product, a measurement. If you can't describe what a row is, the data may need reshaping.
- **What is the grain?** Is this daily, monthly, yearly, per-person, per-transaction? The grain determines how to aggregate and what row labels to use.
- **What are the key identifiers?** Which columns uniquely identify a row? These are candidates for `rowname_col`.
- **What are the measures?** Which columns contain the numbers/values you'd present? These are the display columns.
- **What are the categories?** Which columns partition the data into groups? These are candidates for `groupname_col` or filters.

## Step 2: Understand What the Data Means

Column names are hints, not answers. Go deeper:

### Identify Units and Scale
- A column called `revenue` — is it in dollars, thousands, or millions? Check the magnitude of values.
- A column called `rate` — is it 0.05 (decimal, needs `scale_values=True`) or 5.0 (percentage, needs `scale_values=False`)?
- A column called `volume` — volume of what? Trading shares? Liters? The context of the dataset determines the unit.

### Identify Relationships
- Which columns move together? (e.g., `open`/`close`/`high`/`low` in stock data are all prices — group them under a spanner)
- Which columns are derived from others? (e.g., `return %` is computed from `open` and `close` — it's a summary metric, often the most important column)
- Are there natural comparisons? (e.g., `budget` vs `actual`, `this_year` vs `last_year`)

### Identify What Makes the Data Valuable
Ask: **why would someone look at this table?** The answer drives every design decision:
- **To compare** → emphasize the comparison columns, use consistent formatting, consider `data_color`
- **To find extremes** → highlight min/max values with bold or color
- **To see trends** → order chronologically, use `data_color` to show direction
- **To look up a value** → make row labels clear, keep the table scannable
- **To get a summary** → aggregate the raw data, show totals/averages, keep it short

## Step 3: Assess Data Quality

Before presenting data, check for issues that affect table quality:

- **Outliers**: Are there extreme values that will distort `data_color` domains? Compute the range.
- **Missing data**: Use `sub_missing(missing_text="—")` for NaN/None. Don't let blank cells confuse the reader.
- **Precision**: How many decimal places are meaningful? Stock prices: 2 decimals. Scientific measurements: match the instrument precision. Percentages: usually 1-2 decimals.
- **Consistency**: Are all monetary values in the same currency? All dates in the same timezone? All percentages on the same scale?

## Step 4: Match Data to the User's Request

This is the critical validation step:

1. **Read the user's request carefully.** What specifically are they asking to see?
2. **Check if the data contains what they need.** If they ask for "quarterly revenue by region" but the data only has annual totals, the data cannot fulfill the request.
3. **If there's a mismatch**: Stop. Tell the user what you found in the data and why it doesn't match their request. Do not force a table that doesn't answer the question.
4. **If the data is close but not exact**: Explain what you can show instead and proceed only if it's genuinely useful.

## Step 5: Plan the Presentation

Now that you understand the data, decide:

### What to Show
- **Not every column deserves to be in the table.** Internal IDs, raw timestamps, and intermediate calculations should be hidden.
- **Not every row deserves to be in the table.** If there are 1000 rows, show the top 10, the most recent 5 years, or a meaningful aggregate.
- **Derived columns may be more valuable than raw ones.** A "Return %" column tells more story than separate open/close prices.

### How to Aggregate
- If the raw data is too granular for the requested view, aggregate it: daily → monthly, transactions → totals, individual → category averages.
- Choose aggregation functions that match the data meaning: `sum` for counts and revenues, `mean` for rates and scores, `max`/`min` for extremes.

### What Story to Tell
- **The title should state the takeaway**, not just describe the data. "S&P 500 Recovered Strongly After 2022 Decline" is better than "S&P 500 Data".
- **The subtitle provides context**: date range, data source, methodology.
- **Column order should follow the reader's eye**: identifiers → key metrics → supporting detail.
- **The most important column** should get visual emphasis: bold headers, `data_color`, or prominent positioning.

## Common Data Patterns and How to Handle Them

| Pattern | Example | Table Approach |
|---|---|---|
| Time series | Stock prices over years | Use date as `rowname_col`, limit to key periods, use `data_color` on returns |
| Ranking | Top cities by population | Sort by rank, show top 10-15, bold the #1 entry |
| Comparison | Product A vs Product B | Side-by-side columns, consistent formatting, highlight differences |
| Distribution | Test scores by category | Use `groupname_col` for categories, show count + mean + range |
| Financial | Revenue/cost/profit | Use `fmt_currency`, `accounting=True` for negatives, bold totals |
| Scientific | Experiment measurements | Include units in labels, use `fmt_scientific` for large ranges, show precision |
