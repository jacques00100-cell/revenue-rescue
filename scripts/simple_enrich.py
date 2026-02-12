#!/usr/bin/env python3
"""
Simple efficient enrichment - all leads
"""
import json
import re
import subprocess
import time
import sys

EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+', re.IGNORECASE)
FALSE_PATTERNS = ['bootstrap', 'jquery', 'email@email', 'your@email', 'example@', 'test@', 
                  'demo@', 'user@', 'admin@admin', 'info@info', 'contact@contact',
                  'wixpress', 'wix.com', 'gstatic', 'google', 'facebook', 'sentry.io',
                  'react@', 'vue@', 'lodash@', 'jquery@', 'core-js@', 'axios@', 'webpack@']

def fetch(url):
    if not url:
        return ""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    try:
        result = subprocess.run(
            ['curl', '-s', '-L', '-A', 'Mozilla/5.0', '--max-time', '6', '--connect-timeout', '3', url],
            capture_output=True, text=True, timeout=8
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

def process_lead(lead):
    website = lead.get('website')
    if not website:
        lead.update({"email": "", "contact_page": "", "has_online_booking": False, "has_live_chat": False, "best_contact_method": "phone" if lead.get('phone') else ""})
        return False
    
    main = fetch(website)
    if not main:
        lead.update({"email": "", "contact_page": "", "has_online_booking": False, "has_live_chat": False, "best_contact_method": "phone" if lead.get('phone') else ""})
        return False
    
    # Look for contact page
    contact_match = re.search(r'href=["\']([^"\']*contact[^"\']*)["\']', main, re.I)
    contact_url = None
    if contact_match:
        m = contact_match.group(1)
        if m.startswith('http'):
            contact_url = m
        elif m.startswith('/'):
            contact_url = website.rstrip('/') + m
    
    contact = fetch(contact_url) if contact_url and contact_url != website else ""
    all_content = main + "\n" + contact
    
    emails = extract_emails(all_content)
    lead['email'] = get_best_email(emails)
    lead['contact_page'] = contact_url if contact_url else ""
    lead['has_online_booking'] = 'book now' in all_content.lower() or 'schedule' in all_content.lower()
    lead['has_live_chat'] = 'live chat' in all_content.lower() or 'chat now' in all_content.lower()
    
    if lead['email']:
        lead['best_contact_method'] = "email"
    elif lead['has_live_chat']:
        lead['best_contact_method'] = "chat"
    elif contact_url:
        lead['best_contact_method'] = "form"
    else:
        lead['best_contact_method'] = "phone" if lead.get('phone') else ""
    
    return bool(lead['email'])

def process_file(filepath, filetype, max_leads=200):
    print(f"\n{'='*60}")
    print(f"Processing: {filetype}")
    print('='*60)
    
    with open(filepath) as f:
        data = json.load(f)
    
    if filetype in ('salon', 'hvac_gmaps'):
        leads = data.get('leads', [])
    else:
        leads = data
    
    to_process = [l for l in leads if not l.get('email') or l.get('email') == ''][:max_leads]
    print(f"Total: {len(leads)} | To process: {len(to_process)}")
    
    emails_found = 0
    for i, lead in enumerate(to_process):
        name = lead.get('company_name', 'Unknown')[:40]
        has_email = process_lead(lead)
        if has_email:
            emails_found += 1
            email_display = lead['email'][:35] if len(lead['email']) <= 35 else lead['email'][:32] + '...'
        else:
            email_display = '-'
        
        print(f"[{i+1:3d}/{len(to_process):3d}] {name:<40s} {email_display}")
        
        # Save every 10
        if (i + 1) % 10 == 0:
            if filetype in ('salon', 'hvac_gmaps'):
                data['leads'] = leads
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
            else:
                with open(filepath, 'w') as f:
                    json.dump(leads, f, indent=2)
        
        time.sleep(0.1)
    
    # Final save
    if filetype in ('salon', 'hvac_gmaps'):
        data['leads'] = leads
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    else:
        with open(filepath, 'w') as f:
            json.dump(leads, f, indent=2)
    
    print(f"\n✅ {filetype}: {emails_found} new emails")
    return emails_found

if __name__ == "__main__":
    base = "/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research"
    
    total = 0
    
    # Process all files
    total += process_file(f"{base}/dental-leads-dfw.json", "dental", max_leads=250)
    total += process_file(f"{base}/salon-leads-dfw.json", "salon", max_leads=213)
    total += process_file(f"{base}/auto-leads-dfw.json", "auto", max_leads=125)
    total += process_file(f"{base}/hvac-leads-dfw-BATCH2.json", "hvac_batch2", max_leads=175)
    total += process_file(f"{base}/hvac-leads-GMAPS.json", "hvac_gmaps", max_leads=19)
    
    print(f"\n{'='*60}")
    print(f"🎯 TOTAL NEW EMAILS: {total}")
    print('='*60)
