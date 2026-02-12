#!/usr/bin/env python3
"""
Lead Enrichment Script v2 - Using direct HTTP requests
"""
import json
import re
import time
import requests
from urllib.parse import urljoin, urlparse
from pathlib import Path

# File paths
FILES = {
    'dental': '/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/dental-leads-dfw.json',
    'salon': '/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/salon-leads-dfw.json',
    'auto': '/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/auto-leads-dfw.json',
    'hvac_batch2': '/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/hvac-leads-dfw-BATCH2.json',
    'hvac_gmaps': '/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/hvac-leads-GMAPS.json',
}

# Email regex
EMAIL_PATTERN = r'[\w.+-]+@[\w-]+\.[\w.-]+'

def fetch_url(url, timeout=10):
    """Fetch content from URL"""
    if not url:
        return None
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; LeadScout/1.0)'}
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        return resp.text if resp.status_code == 200 else None
    except Exception as e:
        return None

def extract_emails(content):
    """Extract email addresses from content"""
    if not content:
        return []
    emails = re.findall(EMAIL_PATTERN, content, re.IGNORECASE)
    valid = []
    for email in emails:
        email = email.lower().strip()
        if '@' in email and '.' in email.split('@')[-1]:
            if not any(x in email for x in ['example.', 'test.', 'demo.', '.png', '.jpg', '.gif', 'wixpress']):
                valid.append(email)
    return list(set(valid))

def find_contact_page(base_url, content):
    """Find contact page URL"""
    if not content or not base_url:
        return None
    
    patterns = [
        r'href=["\']([^"\']*contact[^"\']*)["\']',
        r'href=["\']([^"\']*about[^"\']*)["\']',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if match.startswith('http'):
                return match
            elif match.startswith('/'):
                return urljoin(base_url, match)
    
    # Guess common paths
    return urljoin(base_url, '/contact')

def has_booking(content):
    """Check for online booking"""
    if not content:
        return False
    c = content.lower()
    keywords = ['book now', 'schedule now', 'online booking', 'appointment', 'mindbody', 'squareup', 'acuity', 'calendly', 'vagaro']
    return any(k in c for k in keywords)

def has_chat(content):
    """Check for live chat"""
    if not content:
        return False
    c = content.lower()
    keywords = ['live chat', 'chat now', 'intercom', 'drift', 'tawk', 'zendesk', 'crisp', 'livechat']
    return any(k in c for k in keywords)

def get_best_email(emails):
    """Get priority email"""
    if not emails:
        return ""
    priority = ['contact@', 'info@', 'hello@', 'support@', 'admin@', 'office@']
    for p in priority:
        for e in emails:
            if p in e.lower():
                return e
    for e in emails:
        if 'noreply' not in e.lower():
            return e
    return emails[0]

def load_leads(fp, ft):
    with open(fp, 'r') as f:
        data = json.load(f)
    if ft in ('salon', 'hvac_gmaps'):
        return data.get('leads', [])
    return data

def save_leads(fp, ft, leads):
    if ft in ('salon', 'hvac_gmaps'):
        with open(fp, 'r') as f:
            data = json.load(f)
        data['leads'] = leads
        with open(fp, 'w') as f:
            json.dump(data, f, indent=2)
    else:
        with open(fp, 'w') as f:
            json.dump(leads, f, indent=2)

def process_lead(lead):
    """Process a single lead"""
    website = lead.get('website')
    if not website:
        lead['email'] = ""
        lead['contact_page'] = ""
        lead['has_online_booking'] = False
        lead['has_live_chat'] = False
        lead['best_contact_method'] = "phone" if lead.get('phone') else ""
        return lead
    
    main_content = fetch_url(website)
    if not main_content:
        lead['email'] = ""
        lead['contact_page'] = ""
        lead['has_online_booking'] = False
        lead['has_live_chat'] = False
        lead['best_contact_method'] = "phone" if lead.get('phone') else ""
        return lead
    
    contact_url = find_contact_page(website, main_content)
    all_content = main_content
    
    if contact_url and contact_url != website:
        contact_content = fetch_url(contact_url)
        if contact_content:
            all_content += "\n" + contact_content
    
    emails = extract_emails(all_content)
    booking = has_booking(all_content)
    chat = has_chat(all_content)
    
    lead['email'] = get_best_email(emails)
    lead['contact_page'] = contact_url if contact_url else ""
    lead['has_online_booking'] = booking
    lead['has_live_chat'] = chat
    
    if lead['email']:
        lead['best_contact_method'] = "email"
    elif chat:
        lead['best_contact_method'] = "chat"
    elif contact_url:
        lead['best_contact_method'] = "form"
    else:
        lead['best_contact_method'] = "phone" if lead.get('phone') else ""
    
    return lead

def process_batch(file_type, file_path, limit=50, high_priority_only=False):
    """Process a batch of leads"""
    print(f"\n{'='*60}")
    print(f"Processing: {file_type.upper()}")
    print(f"{'='*60}")
    
    leads = load_leads(file_path, file_type)
    
    # Filter high priority
    if high_priority_only:
        def is_hp(l):
            r = l.get('rating')
            return (r is not None and r >= 4.8) or l.get('priority') == 'high'
        leads_to_process = [l for l in leads if is_hp(l) and not l.get('email')]
    else:
        leads_to_process = [l for l in leads if not l.get('email')]
    
    batch = leads_to_process[:limit]
    print(f"Total leads: {len(leads)} | To process: {len(leads_to_process)} | This batch: {len(batch)}")
    
    processed = 0
    for i, lead in enumerate(batch):
        name = lead.get('company_name', 'Unknown')
        print(f"\n[{i+1}/{len(batch)}] {name}")
        
        if not lead.get('website'):
            print(f"  ⚠ No website")
            lead['email'] = ""
            lead['contact_page'] = ""
            lead['has_online_booking'] = False
            lead['has_live_chat'] = False
            lead['best_contact_method'] = "phone" if lead.get('phone') else ""
        else:
            try:
                process_lead(lead)
                print(f"  ✓ Email: {lead['email'][:40] if lead['email'] else 'None'}")
                processed += 1
                time.sleep(0.3)
            except Exception as e:
                print(f"  ✗ Error: {e}")
                lead['email'] = ""
                lead['contact_page'] = ""
                lead['has_online_booking'] = False
                lead['has_live_chat'] = False
                lead['best_contact_method'] = "phone" if lead.get('phone') else ""
    
    save_leads(file_path, file_type, leads)
    print(f"\n💾 Saved! Processed {processed} leads")
    return len(leads_to_process) - len(batch)  # Return remaining

if __name__ == "__main__":
    import sys
    
    high_priority = '--high-priority' in sys.argv
    batch_size = 50
    
    for ft, fp in FILES.items():
        if Path(fp).exists():
            remaining = process_batch(ft, fp, batch_size, high_priority)
            print(f"  Remaining: {remaining}")
        else:
            print(f"⚠ Not found: {fp}")
    
    print("\n" + "="*60)
    print("BATCH COMPLETE!")
    print("="*60)
