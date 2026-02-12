#!/usr/bin/env python3
"""
Lead Import Script - Normalizes and prepares leads for Airtable/Notion import
"""
import csv
import json
import re
from datetime import datetime

def normalize_phone(phone):
    """Normalize phone to (XXX) XXX-XXXX format"""
    if not phone:
        return ""
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return phone

def parse_address(address):
    """Extract City and ZIP from address"""
    if not address:
        return "", ""
    
    # Match pattern: City, TX ZIP or City, TX
    match = re.search(r'([A-Za-z\s]+),\s*TX\s*(\d{5})?', address)
    if match:
        city = match.group(1).strip()
        zip_code = match.group(2) if match.group(2) else ""
        return city, zip_code
    
    # Try just ZIP
    zip_match = re.search(r'(\d{5})', address)
    zip_code = zip_match.group(1) if zip_match else ""
    
    return "", zip_code

def priority_to_score(priority):
    """Convert priority to 1-10 score"""
    mapping = {
        'high': 8,
        'medium': 5,
        'low': 3
    }
    return mapping.get(priority.lower(), 5)

def process_leads():
    leads = []
    
    # Read the enriched CSV
    with open('all-leads-enriched.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            company = row.get('Company', '').strip()
            industry_raw = row.get('Industry', '').strip().lower()
            phone = normalize_phone(row.get('Phone', ''))
            website = row.get('Website', '').strip()
            address = row.get('Address', '')
            priority_str = row.get('Priority', 'medium')
            rating = row.get('Rating', '')
            
            # Map industry to clean values
            industry_map = {
                'dental': 'Dental',
                'salon': 'Salon',
                'auto': 'Auto',
                'hvac_batch2': 'HVAC',
                'hvac_gmaps': 'HVAC',
                'hvac': 'HVAC'
            }
            industry = industry_map.get(industry_raw, industry_raw.capitalize())
            
            city, zip_code = parse_address(address)
            priority_score = priority_to_score(priority_str)
            
            # Determine if this is top 50
            is_top_50 = False
            
            lead = {
                'Business Name': company,
                'Phone Number': phone,
                'Website': website,
                'Industry': industry.capitalize() if industry else 'Unknown',
                'City': city,
                'ZIP': zip_code,
                'Status': 'New',
                'Notes': f"Rating: {rating}" if rating else '',
                'Priority Score': priority_score,
                'Date Added': datetime.now().strftime('%Y-%m-%d'),
                'Raw Priority': priority_str
            }
            leads.append(lead)
    
    # Sort by priority score (high to low), then by rating
    leads.sort(key=lambda x: (x['Priority Score'], x['Notes']), reverse=True)
    
    # Flag top 50 as high priority in notes
    for i, lead in enumerate(leads):
        if i < 50:
            lead['Notes'] = f"[PRIORITY HIGH] {lead['Notes']}".strip()
            lead['Status'] = 'New - Priority'
    
    return leads

def export_to_csv(leads, filename='leads-for-import.csv'):
    """Export normalized leads to CSV"""
    if not leads:
        return
    
    fieldnames = ['Business Name', 'Phone Number', 'Website', 'Industry', 
                  'City', 'ZIP', 'Status', 'Notes', 'Priority Score', 'Date Added']
    
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for lead in leads:
            # Remove internal field
            lead_export = {k: v for k, v in lead.items() if k != 'Raw Priority'}
            writer.writerow(lead_export)
    
    print(f"Exported {len(leads)} leads to {filename}")

def get_industry_counts(leads):
    """Get counts per industry"""
    counts = {}
    for lead in leads:
        industry = lead['Industry']
        counts[industry] = counts.get(industry, 0) + 1
    return counts

if __name__ == '__main__':
    print("Processing leads...")
    leads = process_leads()
    
    print(f"\nTotal leads: {len(leads)}")
    
    print("\nIndustry breakdown:")
    counts = get_industry_counts(leads)
    for industry, count in sorted(counts.items()):
        print(f"  {industry}: {count}")
    
    export_to_csv(leads)
    
    print("\n✅ Top 50 priority leads flagged")
    print("✅ Data normalized and ready for import")
