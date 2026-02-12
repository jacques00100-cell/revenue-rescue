#!/usr/bin/env python3
"""
Fast batch enrichment - Get as many emails as possible
"""
import json
import re
import subprocess
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+', re.IGNORECASE)
FALSE_PATTERNS = ['bootstrap', 'jquery', 'email@email', 'your@email', 'example@', 'test@', 
                  'demo@', 'user@', 'admin@admin', 'info@info', 'contact@contact',
                  'wixpress', 'wix.com', 'gstatic', 'google', 'facebook', 'sentry.io',
                  'react@', 'vue@', 'lodash@', 'jquery@', 'core-js@', 'axios@']

def fetch(url):
    if not url:
        return ""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    try:
        result = subprocess.run(
            ['curl', '-s', '-L', '-A', 'Mozilla/5.0', '--max-time', '8', '--connect-timeout', '4', url],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout if result.returncode == 0 else ""
    except:
        return ""

def extract_emails(content):
    if not content:
        return []
    emails = EMAIL_RE.findall(content)
    valid = []
    for e in emails:
        e_lower = e.lower()
        if not any(fp in e_lower for fp in FALSE_PATTERNS):
            if '@' in e and '.' in e.split('@')[-1]:
                domain = e.split('@')[1]
                if len(domain) > 3 and '.' in domain[-5:]:
                    valid.append(e.lower())
    return list(set(valid))

def get_best_email(emails):
    if not emails:
        return ""
    priority = ['contact@', 'info@', 'hello@', 'support@', 'admin@', 'office@', 'service@']
    for p in priority:
        for e in emails:
            if p in e and 'noreply' not in e:
                return e
    for e in emails:
        if 'noreply' not in e.lower():
            return e
    return ""

def find_contact_url(base, content):
    if not content or not base:
        return None
    patterns = [r'href=["\']([^"\']*contact[^"\']*)["\']', r'href=["\']([^"\']*about[^"\']*)["\']']
    for pat in patterns:
        matches = re.findall(pat, content, re.I)
        for m in matches:
            if m.startswith('http'):
                return m
            elif m.startswith('/'):
                return base.rstrip('/') + m
    return base.rstrip('/') + '/contact'

def has_booking(content):
    if not content:
        return False
    c = content.lower()
    return any(x in c for x in ['book now', 'schedule', 'appointment', 'calendly', 'acuity'])

def has_chat(content):
    if not content:
        return False
    c = content.lower()
    return any(x in c for x in ['live chat', 'chat now', 'intercom', 'tawk', 'zendesk'])

def process_single_lead(lead):
    """Process a single lead and return updated lead"""
    website = lead.get('website')
    if not website:
        lead.update({"email": "", "contact_page": "", "has_online_booking": False, "has_live_chat": False, "best_contact_method": "phone" if lead.get('phone') else ""})
        return lead, False
    
    main = fetch(website)
    if not main:
        lead.update({"email": "", "contact_page": "", "has_online_booking": False, "has_live_chat": False, "best_contact_method": "phone" if lead.get('phone') else ""})
        return lead, False
    
    contact_url = find_contact_url(website, main)
    contact = fetch(contact_url) if contact_url and contact_url != website else ""
    all_content = main + "\n" + contact
    
    emails = extract_emails(all_content)
    lead['email'] = get_best_email(emails)
    lead['contact_page'] = contact_url if contact_url else ""
    lead['has_online_booking'] = has_booking(all_content)
    lead['has_live_chat'] = has_chat(all_content)
    
    if lead['email']:
        lead['best_contact_method'] = "email"
    elif lead['has_live_chat']:
        lead['best_contact_method'] = "chat"
    elif contact_url:
        lead['best_contact_method'] = "form"
    else:
        lead['best_contact_method'] = "phone" if lead.get('phone') else ""
    
    return lead, bool(lead['email'])

def process_batch(leads, batch_size=20):
    """Process leads in parallel batches"""
    results = []
    emails_found = 0
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_lead = {executor.submit(process_single_lead, lead): lead for lead in leads[:batch_size]}
        for future in as_completed(future_to_lead):
            lead, has_email = future.result()
            results.append(lead)
            if has_email:
                emails_found += 1
    
    return results, emails_found

def process_file(filepath, filetype, max_leads=100):
    print(f"\nProcessing: {filetype}")
    
    with open(filepath) as f:
        data = json.load(f)
    
    if filetype in ('salon', 'hvac_gmaps'):
        leads = data.get('leads', [])
    else:
        leads = data
    
    # Get leads without emails
    to_process = [l for l in leads if not l.get('email') or l.get('email') == ''][:max_leads]
    print(f"Processing {len(to_process)} leads...")
    
    # Process in batches
    batch_size = 20
    total_emails = 0
    
    for i in range(0, len(to_process), batch_size):
        batch = to_process[i:i+batch_size]
        print(f"  Batch {i//batch_size + 1}/{(len(to_process)-1)//batch_size + 1}: ", end='', flush=True)
        
        processed, emails = process_batch(batch, batch_size)
        total_emails += emails
        print(f"{emails} emails found")
        
        # Small delay between batches
        time.sleep(0.5)
    
    # Save
    if filetype in ('salon', 'hvac_gmaps'):
        data['leads'] = leads
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    else:
        with open(filepath, 'w') as f:
            json.dump(leads, f, indent=2)
    
    print(f"✅ {filetype}: {total_emails} new emails")
    return total_emails

if __name__ == "__main__":
    base = "/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research"
    
    files = [
        (f"{base}/dental-leads-dfw.json", "dental"),
        (f"{base}/salon-leads-dfw.json", "salon"),
        (f"{base}/auto-leads-dfw.json", "auto"),
        (f"{base}/hvac-leads-dfw-BATCH2.json", "hvac_batch2"),
        (f"{base}/hvac-leads-GMAPS.json", "hvac_gmaps"),
    ]
    
    total = 0
    for fp, ft in files:
        if Path(fp).exists():
            total += process_file(fp, ft, max_leads=150)
        else:
            print(f"⚠ Not found: {fp}")
    
    print(f"\n🎯 TOTAL NEW EMAILS: {total}")
