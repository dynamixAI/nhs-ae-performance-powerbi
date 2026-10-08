# NHS A&E Performance Dashboard

> **Status: In progress** — data pipeline complete and validated; Power BI report under construction.

An end-to-end analytics project tracking A&E performance in England against the 4-hour standard. It combines a Python data pipeline (download, clean, reconcile, validate) with a Power BI KPI dashboard.

## Business brief

**Stakeholder (simulated):** Regional Urgent & Emergency Care Performance Lead.

**Questions the dashboard answers:**

1. What share of patients are seen within 4 hours, and how far is each trust from the target?
2. Which trusts are consistently underperforming, and which have improved?
3. How large is winter pressure, and when does it start?
4. How many patients wait over 4 and 12 hours from decision to admit?

## Data

- **Source:** NHS England, *Monthly A&E Attendances and Emergency Admissions* — trust-level CSVs
- **Coverage:** January 2021 to September 2026 (69 months), 233 organisations, 7 NHS regions
- **Licence:** Contains public sector information licensed under the Open Government Licence v3.0

## Pipeline

| Step | Script | What it does |
|---|---|---|
| 1. Download | `scripts/download_nhs_ae.py` | Scrapes every NHS financial-year page from the start date and downloads each monthly CSV with a consistent, sortable filename. Skips files already downloaded. |
| 2. Clean & model | `scripts/clean_nhs_ae.py` | Combines all files, fixes data issues, reconciles to NHS totals, and outputs a star schema (`fact_ae`, `dim_org`, `dim_date`) for Power BI. |

### Data quality issues found and handled

| Issue | How it was handled |
|---|---|
| July 2021 link text missing "A&E" on the source page, so it was silently skipped | Matching rule changed from exact wording to reliable signals (monthly + CSV + month/year) |
| September 2024 file had 6 extra empty columns (one named "a") | Investigated (all empty), then excluded by keeping only the 22 known columns |
| National TOTAL rows in every file, spelled inconsistently ("TOTAL", "Total", "TOTAl") | Separated from detail rows to prevent double counting, then used for reconciliation |
| February 2026 TOTAL row stored in the organisation columns instead of Period | Detection extended to all label columns; caught by a dimension-value check |
| Trailing spaces in region names; typo in a source header | Trimmed and renamed to clean, consistent column names |

## Validation

| Check | Result |
|---|---|
| Completeness | 69 of 69 months downloaded |
| Reconciliation | Sum of organisations matches NHS England's TOTAL rows for all 69 months — attendances and over-4-hour counts, zero variance |
| KPI accuracy | September 2026 4-hour performance calculated at **74.4%**, matching NHS England's published statistical commentary exactly (`docs/commentary_2026-09.pdf`) |

## Reproduce it

```bash
python3 scripts/download_nhs_ae.py
python3 scripts/clean_nhs_ae.py
```

Requires Python 3 with `requests`, `beautifulsoup4`, `pandas` and `openpyxl`.

## Repository structure




## Coming next

- [ ] Power BI semantic model: relationships and DAX measures (4-hour %, variance to target, RAG status, YoY)
- [ ] Report pages: National overview, Trust league table, Trust drill-through, Seasonality
- [ ] Key findings and recommendations
- [ ] Video walkthrough

---
*Independent portfolio project by [DynamixAI](https://github.com/dynamixAI).*
