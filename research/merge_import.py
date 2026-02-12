#!/usr/bin/env python3
"""
Lead Import Script - Merges all lead sources and prepares for Airtable/Notion import
"""
import csv
import json
import re
from datetime import datetime
from collections import defaultdict

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
    if not priority:
        return 5
    mapping = {
        'high': 8,
        'medium': 5,
        'low': 3
    }
    return mapping.get(priority.lower(), 5)

def make_key(company, phone):
    """Create unique key for deduplication"""
    company_clean = re.sub(r'[^\w]', '', company.lower()) if company else ''
    phone_clean = re.sub(r'\D', '', phone) if phone else ''
    return f"{company_clean}_{phone_clean}"

def load_json_file(filepath, industry_override=None):
    """Load leads from JSON file"""
    leads = []
    try:
        with open(filepath) as f:
            data = json.load(f)
            
        # Handle different structures
        if isinstance(data, dict):
            if 'leads' in data:
                items = data['leads']
            else:
                items = [data]
        elif isinstance(data, list):
            items = data
        else:
            items = []
        
        for item in items:
            if not isinstance(item, dict):
                continue
                
            company = item.get('company_name', item.get('name', ''))
            phone = normalize_phone(item.get('phone', ''))
            website = item.get('website', '') or ''
            address = item.get('address', '')
            rating = item.get('rating', '')
            priority_str = item.get('priority', 'medium')
            
            # Determine industry
            industry = industry_override or item.get('industry', 'Unknown')
            if not industry_override:
                # Try to infer from filename or data
                if 'hvac' in filepath.lower():
                    industry = 'HVAC'
                elif 'dental' in filepath.lower():
                    industry = 'Dental'
                elif 'salon' in filepath.lower():
                    industry = 'Salon'
                elif 'auto' in filepath.lower():
                    industry = 'Auto'
            
            city, zip_code = parse_address(address)
            priority_score = priority_to_score(priority_str)
            
            lead = {
                'Business Name': company,
                'Phone Number': phone,
                'Website': website,
                'Industry': industry,
                'City': city,
                'ZIP': zip_code,
                'Status': 'New',
                'Notes': f"Rating: {rating}" if rating else '',
                'Priority Score': priority_score,
                'Date Added': datetime.now().strftime('%Y-%m-%d'),
                '_key': make_key(company, phone),
                '_raw_priority': priority_str
            }
            leads.append(lead)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    
    return leads

def load_csv_file(filepath):
    """Load leads from CSV file"""
    leads = []
    industry_map = {
        'dental': 'Dental',
        'salon': 'Salon',
        'auto': 'Auto',
        'hvac_batch2': 'HVAC',
        'hvac_gmaps': 'HVAC',
        'hvac': 'HVAC'
    }
    
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            company = row.get('Company', '').strip()
            industry_raw = row.get('Industry', '').strip().lower()
            phone = normalize_phone(row.get('Phone', ''))
            website = row.get('Website', '').strip()
            address = row.get('Address', '')
            priority_str = row.get('Priority', 'medium')
            rating = row.get('Rating', '')
            
            industry = industry_map.get(industry_raw, industry_raw.capitalize())
            city, zip_code = parse_address(address)
            priority_score = priority_to_score(priority_str)
            
            lead = {
                'Business Name': company,
                'Phone Number': phone,
                'Website': website,
                'Industry': industry,
                'City': city,
                'ZIP': zip_code,
                'Status': 'New',
                'Notes': f"Rating: {rating}" if rating else '',
                'Priority Score': priority_score,
                'Date Added': datetime.now().strftime('%Y-%m-%d'),
                '_key': make_key(company, phone),
                '_raw_priority': priority_str
            }
            leads.append(lead)
    
    return leads

def merge_all_leads():
    """Load and merge all lead sources, removing duplicates"""
    all_leads = []
    seen_keys = set()
    
    # Files to process with their industry
    files = [
        ('all-leads-enriched.csv', 'csv'),
        ('hvac-leads-dfw-BATCH2.json', 'json'),
        ('hvac-leads-dfw-NEW.json', 'json'),
        ('hvac-leads-GMAPS.json', 'json'),
        ('hvac-leads-dfw-2026-02-11.json', 'json'),
        ('dental-leads-dfw.json', 'json'),
        ('salon-leads-dfw.json', 'json'),
        ('auto-leads-dfw.json', 'json'),
    ]
    
    for filepath, ftype in files:
        print(f"Loading {filepath}...")
        if ftype == 'csv':
            leads = load_csv_file(filepath)
        else:
            leads = load_json_file(filepath)
        
        for lead in leads:
            key = lead['_key']
            if key and key not in seen_keys:
                seen_keys.add(key)
                all_leads.append(lead)
            elif not key:
                all_leads.append(lead)
    
    return all_leads

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
            # Remove internal fields
            lead_export = {k: v for k, v in lead.items() if not k.startswith('_')}
            writer.writerow(lead_export)
    
    print(f"\n✅ Exported {len(leads)} leads to {filename}")

def get_industry_counts(leads):
    """Get counts per industry"""
    counts = defaultdict(int)
    for lead in leads:
        counts[lead['Industry']] += 1
    return dict(counts)

if __name__ == '__main__':
    print("🔄 Merging all lead sources...")
    leads = merge_all_leads()
    
    print(f"\n📊 Total unique leads: {len(leads)}")
    
    # Sort by priority score (high to low)
    leads.sort(key=lambda x: (x['Priority Score'], x['Notes']), reverse=True)
    
    # Flag top 50 as high priority
    for i, lead in enumerate(leads):
        if i < 50:
            lead['Notes'] = f"[PRIORITY HIGH] {lead['Notes']}".strip()
            lead['Status'] = 'New - Priority'
    
    print("\n📈 Industry breakdown:")
    counts = get_industry_counts(leads)
    for industry, count in sorted(counts.items()):
        print(f"  {industry}: {count}")
    
    export_to_csv(leads)
    
    print("\n🎯 Top 50 priority leads flagged")
    print("📁 Data normalized and ready for import")
