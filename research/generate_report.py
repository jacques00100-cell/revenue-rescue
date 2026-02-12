#!/usr/bin/env python3
"""
Create import summary and statistics
"""
import csv
from collections import Counter, defaultdict
from datetime import datetime

def analyze_leads():
    with open('leads-for-import.csv') as f:
        reader = csv.DictReader(f)
        leads = list(reader)
    
    total = len(leads)
    
    # Industry breakdown
    industries = Counter(l['Industry'] for l in leads)
    
    # Priority breakdown
    priorities = Counter(l['Status'] for l in leads)
    
    # City breakdown (top 10)
    cities = Counter(l['City'] for l in leads if l['City'])
    
    # Priority score distribution
    scores = Counter(int(l['Priority Score']) for l in leads)
    
    # Website availability
    with_website = sum(1 for l in leads if l['Website'])
    without_website = total - with_website
    
    # Phone availability
    with_phone = sum(1 for l in leads if l['Phone Number'])
    
    report = f"""
# Lead Import Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Summary Statistics

**Total Leads:** {total}

## Industry Breakdown
| Industry | Count | Percentage |
|----------|-------|------------|
"""
    for ind, count in sorted(industries.items(), key=lambda x: -x[1]):
        pct = (count / total) * 100
        report += f"| {ind} | {count} | {pct:.1f}% |\n"
    
    report += f"""
## Priority Status
| Status | Count |
|--------|-------|
"""
    for status, count in priorities.most_common():
        report += f"| {status} | {count} |\n"
    
    report += f"""
## Top Cities
| City | Count |
|------|-------|
"""
    for city, count in cities.most_common(10):
        report += f"| {city} | {count} |\n"
    
    report += f"""
## Data Quality
- Leads with website: {with_website} ({(with_website/total)*100:.1f}%)
- Leads without website: {without_website} ({(without_website/total)*100:.1f}%)
- Leads with phone: {with_phone} ({(with_phone/total)*100:.1f}%)

## Priority Score Distribution
| Score | Count |
|-------|-------|
"""
    for score in sorted(scores.keys(), reverse=True):
        report += f"| {score} | {scores[score]} |\n"
    
    report += """
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
"""
    
    return report

if __name__ == '__main__':
    report = analyze_leads()
    with open('IMPORT_REPORT.md', 'w') as f:
        f.write(report)
    print(report)
    print("\n✅ Report saved to IMPORT_REPORT.md")
