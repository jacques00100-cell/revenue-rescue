
# Lead Import Report
Generated: 2026-02-12 10:18

## Summary Statistics

**Total Leads:** 1021

## Industry Breakdown
| Industry | Count | Percentage |
|----------|-------|------------|
| Dental | 291 | 28.5% |
| HVAC | 290 | 28.4% |
| Salon | 240 | 23.5% |
| Auto | 200 | 19.6% |

## Priority Status
| Status | Count |
|--------|-------|
| New | 971 |
| New - Priority | 50 |

## Top Cities
| City | Count |
|------|-------|
| Dallas | 222 |
| Plano | 188 |
| Fort Worth | 187 |
| Arlington | 139 |
| Frisco | 39 |
| Richardson | 21 |
| Garland | 21 |
| Irving | 21 |
| Mesquite | 19 |
| Carrollton | 18 |

## Data Quality
- Leads with website: 884 (86.6%)
- Leads without website: 137 (13.4%)
- Leads with phone: 1016 (99.5%)

## Priority Score Distribution
| Score | Count |
|-------|-------|
| 8 | 676 |
| 5 | 249 |
| 3 | 96 |

## Import Instructions

### Airtable (Recommended)
1. Go to https://airtable.com and create a free account
2. Create a new base from scratch
3. Click "Add or Import" → "CSV file"
4. Upload `leads-for-import.csv`
5. Airtable will auto-detect field types
6. The first 50 rows are already flagged as "New - Priority"

### Notion
1. Go to https://notion.so and create a free account
2. Create a new database (Table view)
3. Click "..." → "Merge with CSV"
4. Upload `leads-for-import.csv`
5. Map the columns to properties

## Files Generated
- `leads-for-import.csv` - Main import file with 1,021 leads
- `IMPORT_REPORT.md` - This report

## Schema Used
- Business Name
- Phone Number (normalized)
- Website
- Industry (HVAC/Dental/Salon/Auto)
- City
- ZIP
- Status (New/New - Priority)
- Notes (includes rating and priority flag)
- Priority Score (1-10)
- Date Added
