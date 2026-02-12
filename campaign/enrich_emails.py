#!/usr/bin/env python3
"""
Email Enrichment Helper
Generate likely email patterns for leads based on common conventions
"""

import csv
import re
from pathlib import Path
from urllib.parse import urlparse

def clean_name(name: str) -> str:
    """Clean business name for email generation"""
    # Remove common suffixes
    name = re.sub(r'\s+(LLC|Inc|Corp|Ltd|Co\.?|Company)\.?\s*$', '', name, flags=re.IGNORECASE)
    # Remove special characters
    name = re.sub(r'[^\w\s]', '', name)
    return name.strip().lower()


def generate_email_patterns(business_name: str, domain: str, contact_name: str = ""):
    """Generate likely email patterns"""
    patterns = []
    
    # Clean domain
    if not domain or domain in ['', 'N/A']:
        return []
    
    # Extract domain from URL
    if '://' in domain:
        parsed = urlparse(domain)
        domain = parsed.netloc
    domain = domain.replace('www.', '').lower()
    
    # Business-based patterns
    clean = clean_name(business_name)
    words = clean.split()
    
    # Pattern: info@domain.com
    patterns.append(f"info@{domain}")
    
    # Pattern: hello@domain.com
    patterns.append(f"hello@{domain}")
    
    # Pattern: contact@domain.com
    patterns.append(f"contact@{domain}")
    
    # Pattern: bookings@domain.com (for salons)
    patterns.append(f"bookings@{domain}")
    
    # Pattern: firstword@domain.com
    if words:
        patterns.append(f"{words[0]}@{domain}")
    
    # Pattern: firstword+booking@domain.com
    if words:
        patterns.append(f"{words[0]}salon@{domain}")
    
    # Contact name patterns
    if contact_name and contact_name != 'N/A':
        first = contact_name.split()[0].lower()
        patterns.append(f"{first}@{domain}")
        patterns.append(f"{first}@{domain.replace('www.', '')}")
    
    return list(set(patterns))


def enrich_csv(input_path: str, output_path: str):
    """Add email pattern suggestions to CSV"""
    
    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames + ['Suggested Emails', 'Email Enrichment Status']
        rows = list(reader)
    
    enriched = []
    for row in rows:
        business = row.get('Business Name', '')
        website = row.get('Website', '')
        contact = row.get('Contact Name', '')
        
        patterns = generate_email_patterns(business, website, contact)
        
        row['Suggested Emails'] = '; '.join(patterns[:4])
        row['Email Enrichment Status'] = 'pattern_guessed' if patterns else 'no_domain'
        enriched.append(row)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched)
    
    print(f"✓ Enriched {len(enriched)} leads")
    print(f"✓ Saved to: {output_path}")
    print(f"\n⚠️  WARNING: These are PATTERN GUESSES only!")
    print("   You MUST verify these emails before sending!")
    print("\nRecommended verification tools:")
    print("  • Hunter.io (hunter.io)")
    print("  • NeverBounce (neverbounce.com)")
    print("  • ZeroBounce (zerobounce.net)")


if __name__ == "__main__":
    import sys
    
    input_path = sys.argv[1] if len(sys.argv) > 1 else "../../leads-for-import.csv"
    output_path = input_path.replace('.csv', '-enriched.csv')
    
    print("=" * 60)
    print("📧 EMAIL ENRICHMENT HELPER")
    print("=" * 60)
    print(f"\nInput:  {input_path}")
    print(f"Output: {output_path}\n")
    
    enrich_csv(input_path, output_path)
    
    # Show sample
    print("\n📋 Sample output:")
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 3:
                break
            print(f"\n  {row['Business Name']}")
            print(f"    Suggested: {row['Suggested Emails'][:60]}...")
