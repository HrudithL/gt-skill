# Data cleaning — get to ONE clean, correctly-typed DataFrame (Step 1)

Before Step 2, turn whatever you were handed (CSV, Excel, SQL result, messy DataFrame)
into **one tidy DataFrame with the right dtype in every column** — `great_tables`
formats numbers, it does not parse strings, and a currency string or `object`-dtype
column silently breaks `fmt_*`/`data_color` downstream.

## The checklist — run it before you organize columns

1. **Strip number-like strings to real numbers.** Currency symbols, thousands
   separators, percent signs, or unit suffixes (`"$1,200"`, `"1,116.56"`, `"12%"`,
   `"5 kg"`) must become plain floats/ints before reaching gt — `fmt_currency`/
   `fmt_percent` format *numbers*, not strings.

   **Normalize accounting-negative parentheses first.** A value wrapped in parentheses
   is a **negative** (`"($1,200)"` = −1200). The naïve strip `r"[^0-9.\-]"` deletes the
   parentheses and keeps only the digits, silently turning a loss into a positive —
   **data corruption**. Convert wrapping parens to a leading `-` *before* stripping
   symbols:
   ```python
   s = df["price"].astype(str).str.strip()
   s = s.str.replace(r"^\((.*)\)$", r"-\1", regex=True)  # (1,200) -> -1,200  BEFORE stripping
   s = s.str.replace(r"[^0-9.\-]", "", regex=True)       # now drop $ , % and unit text; keep leading -
   df["price"] = pd.to_numeric(s, errors="coerce")
   ```
   **Magnitude suffixes need an explicit multiplier — never the generic strip.** For
   `"$1.2M"`, `"3K"`, `"4bn"` the generic strip leaves `1.2`, `3`, `4` — dropping the
   ×1e6/×1e3/×1e9 multiplier, an order-of-magnitude corruption. Parse the suffix
   explicitly against a fixed multiplier table (deterministic):
   ```python
   import re
   _MULT = {"k": 1e3, "m": 1e6, "b": 1e9, "bn": 1e9, "t": 1e12}   # fixed, case-insensitive
   def parse_scaled(x):
       s = str(x).strip().lower().replace(",", "")
       s = re.sub(r"^\((.*)\)$", r"-\1", s)                       # accounting negative first
       m = re.match(r"^[^\d\-.]*(-?\d+(?:\.\d+)?)\s*(bn|k|m|b|t)?", s)  # bn before b
       if not m:
           return float("nan")
       return float(m.group(1)) * _MULT.get(m.group(2), 1.0)
   df["amount"] = df["amount"].map(parse_scaled)
   ```

2. **Coerce `object`-dtype numeric columns deliberately.** A column with numbers plus a
   stray `"N/A"`/`"-"` stays `object` and breaks `fmt_number`/`data_color`. Coerce it:
   `df["x"] = pd.to_numeric(df["x"], errors="coerce")` (bad values → `NaN`, rendered
   later with `sub_missing`).

3. **Percent scale — decide fraction vs. already-scaled.** `fmt_percent` expects the
   **fractional** form (`0.12` → `12%`). If the column is already `12` meaning "12%",
   divide by 100 first or pass `scale_values=False` — otherwise it renders `1200%`.
   Pick one and be consistent across every percent column.

4. **Fix the header row.** If row 0 is a title/blank/merged cell rather than the real
   header (common in Excel exports), reload with the correct `header=`/`skiprows=` so
   column names are real, not `Unnamed: 0`.

5. **SQL / Decimal results → float.** Cast `decimal.Decimal` columns to `float`
   (`df["amt"] = df["amt"].astype(float)`) so gt's formatters accept them, and confirm
   NULL handling matches your missing-value convention (below). **Caution — exact money /
   large integers:** `float` has only ~15–16 significant digits (integers exact only up
   to 2^53). For values that must stay exact — cents-precise money, IDs, or magnitudes
   beyond 2^53 — do **not** cast to `float`: keep the `Decimal`, or `quantize` it to the
   display precision (`df["amt"] = df["amt"].map(lambda d: d.quantize(Decimal("0.01")))`),
   then format. gt can format `Decimal` values directly.

6. **Trim whitespace in string keys.** Leading/trailing spaces break exact matching for
   `groupname_col` labels and joins: `df["region"] = df["region"].str.strip()`.

7. **Name the missing-value meaning, then make it uniform.** "No data", "true zero", and
   "not applicable" are different claims — don't let them all collapse to a blank cell.
   Standardize to `NaN` where you mean missing, and render with
   `sub_missing(missing_text="—")` (an em dash reads as *intentionally blank*, not
   *broken*). Pairs with the NA-cell neutral in `small_color.md`.

## Grain & identifiers — does every row have a distinct stub label?

Before Step 2 turns a column into the stub, confirm the DataFrame's **grain** — what
one row actually represents — has an identifier that is genuinely unique at that
grain, not just present.

- **Single-column identifier.** A single existing column (name, ID, date) is enough
  when it alone is unique at the row's grain — use it directly as the stub.
- **Composite identifier — two distinct motivations, not one.** A composite (joining
  two or more columns into one stub label) can be built for either reason, and it's
  worth being clear about which one actually applies:
  - **Uniqueness** — a single column has duplicate values across rows, so a
    composite is *required* to disambiguate at all.
  - **Readability** — a single column is already unique on its own, but pairing it
    with another column produces a more self-describing label, so the reader isn't
    forced to cross-reference a second column to understand what the stub names.
    A column can pass the uniqueness test below and still be worth combining for
    this reason alone.

  A hypothetical product-catalog dataset illustrates the readability case: suppose
  `sku_name` (e.g. "Trail Runner 3") is already unique across every row on its own
  (verified directly against the data), so uniqueness alone would not require a
  composite. A stub can still combine `brand + " " + sku_name` into one label
  anyway, because "Trail Runner 3" read alone doesn't say which brand makes it,
  while "Summit Trail Runner 3" is self-describing without a separate brand column:
  ```python
  df["display_name"] = df["brand"] + " " + df["sku_name"]
  ```
- **Constructed identifier.** When the grain is itself a combination of columns with
  no natural label (e.g. one row per region-quarter), build a display label from them
  rather than showing the raw parts side by side:
  ```python
  df["period_label"] = df["yr"].astype(str) + " Q" + df["qtr"].astype(str)  # -> "2010 Q1"
  ```

**The decidable test (uniqueness only):** would two different rows render an
**identical** stub label? If so, the identifier is incomplete for uniqueness —
extend it (add another column to the composite, or construct a finer label) until
every row's label is unique. This test only checks uniqueness, not readability — a
column can pass it (be unique on its own) and still benefit from a composite for the
readability reason above. Check the test against the actual data, the same way the
product-catalog case above is verified against every row before it's trusted, rather
than assuming a column "looks like" an identifier.

## Do NOT fabricate

If cleaning reveals the data cannot answer the request (a needed column is absent or
unusable), stop — tell the user what is missing and emit a blank table (Step 1's
validate-request rule). Never invent values to fill a gap.
