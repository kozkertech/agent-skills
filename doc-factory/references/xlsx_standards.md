# XLSX Generation Standards

These rules apply whenever doc-factory generates a spreadsheet (price lists, financial summaries, project budgets, or any XLSX output). They are drawn from the Anthropic xlsx skill's production standards.

---

## Non-Negotiable Rules

### 1. Zero Formula Errors
Every delivered XLSX must have zero formula errors: no `#REF!`, `#DIV/0!`, `#VALUE!`, `#N/A`, `#NAME?`. After generating, always run:

```bash
python /path/to/xlsx-skill/scripts/recalc.py output.xlsx
```

Check the JSON output — if `status` is `"errors_found"`, fix before delivering.

### 2. Formulas Over Hardcoded Values
**Never** compute a total in Python and put the number in a cell. Always write an Excel formula so the sheet recalculates when source data changes.

```python
# ❌ Wrong
sheet['B10'] = df['Price'].sum()  # hardcoded number

# ✅ Right
sheet['B10'] = '=SUM(B2:B9)'     # Excel formula
```

This applies to: totals, subtotals, averages, percentages, growth rates, tax calculations, and any derived value.

### 3. Cell References, Not Magic Numbers
Put assumptions (rates, multipliers, dates) in named cells or a dedicated Assumptions row/section. Reference those cells in formulas rather than embedding numbers directly.

```python
# ❌ Wrong
sheet['C5'] = '=C4*1.2'     # Where does 1.2 come from?

# ✅ Right
sheet['B2'] = 0.20           # Named row: "VAT Rate"
sheet['C5'] = '=C4*(1+$B$2)' # Formula references assumption
```

---

## Financial Color Coding (for financial models and budgets)

Use industry-standard color coding when building financial tables:

| Color | Hex | Meaning |
|---|---|---|
| Blue text | `#0000FF` | Hardcoded inputs — numbers users may change |
| Black text | `#000000` | All formulas and calculations |
| Green text | `#008000` | Links pulling from other worksheets in the same file |
| Red text | `#FF0000` | External links to other files |
| Yellow background | `#FFFF00` | Key assumptions requiring attention |

For non-financial documents (price lists, project trackers), use the brand's primary color for header rows instead.

---

## Number Formatting Standards

Apply these formats consistently:

| Data type | Format string | Example |
|---|---|---|
| Currency (no decimals) | `$#,##0` | $12,500 |
| Currency (with decimals) | `$#,##0.00` | $12,500.00 |
| Percentage | `0.0%` | 15.3% |
| Multiples | `0.0x` | 3.2x |
| Negative numbers | `($#,##0)` — parentheses, not minus | (500) |
| Zeros | Use `"$#,##0;($#,##0);-"` format to display `-` for zero | – |
| Years | Store as text strings `"2026"`, not numbers | 2026 |

Always include units in headers: `Revenue ($k)`, `Growth Rate (%)`, not just `Revenue` or `Growth`.

---

## Code Patterns (openpyxl)

### Creating a new workbook with brand styling

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

wb = Workbook()
ws = wb.active
ws.title = "Sheet Name"

BRAND_PRIMARY = "#1F3A70"   # from brand_config.json
BRAND_HEX     = "1F3A70"    # openpyxl uses no-# hex

# Header row
header_fill = PatternFill("solid", start_color=BRAND_HEX, end_color=BRAND_HEX)
header_font = Font(bold=True, color="FFFFFF", name="Arial", size=11)

for col, value in enumerate(headers, start=1):
    cell = ws.cell(row=1, column=col, value=value)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="left", vertical="center")

ws.row_dimensions[1].height = 20

# Data rows
for r_idx, row_data in enumerate(data, start=2):
    bg = "F9FAFB" if r_idx % 2 == 0 else "FFFFFF"
    row_fill = PatternFill("solid", start_color=bg, end_color=bg)
    for c_idx, val in enumerate(row_data, start=1):
        cell = ws.cell(row=r_idx, column=c_idx, value=val)
        cell.fill = row_fill
        cell.font = Font(name="Arial", size=10)

# Total row (last row)
total_row = len(data) + 2
total_fill = PatternFill("solid", start_color="EFF6FF", end_color="EFF6FF")
ws.cell(row=total_row, column=1, value="TOTAL").font = Font(bold=True, name="Arial", size=10)
ws.cell(row=total_row, column=2).fill = total_fill

# Column widths
ws.column_dimensions['A'].width = 30
ws.column_dimensions['B'].width = 18

wb.save("output.xlsx")
```

### Editing an existing file (preserve formulas)

```python
from openpyxl import load_workbook

wb = load_workbook("existing.xlsx")   # Do NOT use data_only=True — it strips formulas
ws = wb.active

ws['C5'] = '=SUM(C2:C4)'   # Add formula
ws['A1'] = 'Updated Value'  # Edit cell

wb.save("existing.xlsx")
```

**Warning**: `load_workbook(..., data_only=True)` reads calculated values but permanently discards all formulas if you save after loading this way.

### Reading data for analysis

```python
import pandas as pd

df = pd.read_excel("file.xlsx")           # First sheet
all_sheets = pd.read_excel("file.xlsx", sheet_name=None)  # All sheets as dict
```

---

## Validation Checklist

Before delivering any XLSX:

- [ ] All totals are formulas (SUM, not hardcoded)
- [ ] Assumptions are in separate named cells, not embedded in formulas
- [ ] Run recalc.py — status is `"success"` with zero errors
- [ ] Brand primary color applied to header rows
- [ ] Alternating row shading applied
- [ ] Column widths set (not default 8.43)
- [ ] Currency/percentage formatting applied to numeric columns
- [ ] Units specified in column headers
- [ ] No `#REF!`, `#DIV/0!`, `#VALUE!`, `#N/A`, or `#NAME?` errors
