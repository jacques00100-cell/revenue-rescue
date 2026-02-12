#!/usr/bin/env python3
"""
Quick enrichment for remaining leads - smaller batches
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+', re.IGNORECASE)
FALSE_PATTERNS = ['bootstrap', 'jquery', 'email@email', 'your@email', 'example@', 'test@', 
                  'demo@', 'user@', 'admin@admin', 'info@info', 'contact@contact',
                  'wixpress', 'wix.com', 'squarespace', 'gstatic', 'google', 'facebook',
                  'splide@', 'popper.js', 'webreporting@gargle', 'wp-content', 'fonts@',
                  'wght@', 'pixel@', 'analytics@', 'gtag@']

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
                if len(domain) > 3 and '.' in domain:
                    valid.append(e.lower())
    return list(set(valid))

def get_best_email(emails):
    if not emails:
        return ""
    priority = ['contact@', 'info@', 'hello@', 'support@', 'admin@', 'office@', 'reception@', 'dr@']
    for p in priority:
        for e in emails:
            if p in e and 'noreply' not in e:
                return e
    for e in emails:
        if 'noreply' not in e.lower():
            return e
    return emails[0]

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
    return any(x in c for x in ['book now', 'schedule now', 'online booking', 'appointment', 'calendly', 'acuity', 'vagaro'])

def has_chat(content):
    if not content:
        return False
    c = content.lower()
    return any(x in c for x in ['live chat', 'chat now', 'intercom', 'drift', 'tawk', 'zendesk'])

def process_lead(lead):
    website = lead.get('website')
    if not website:
        lead.update({"email": "", "contact_page": "", "has_online_booking": False, "has_live_chat": False, "best_contact_method": "phone" if lead.get('phone') else ""})
        return "no_website"
    
    main = fetch(website)
    if not main:
        lead.update({"email": "", "contact_page": "", "has_online_booking": False, "has_live_chat": False, "best_contact_method": "phone" if lead.get('phone') else ""})
        return "fail"
    
    contact_url = find_contact_url(website, main)
    contact = fetch(contact_url) if contact_url and contact_url != website else ""
    all_content = main + "\n" + contact
    
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
    
    return "ok"

def process_file(filepath, filetype, limit=100):
    print(f"\n{'='*60}")
    print(f"Processing: {filepath}")
    
    with open(filepath) as f:
        data = json.load(f)
    
    if filetype in ('salon', 'hvac_gmaps'):
        leads = data.get('leads', [])
    else:
        leads = data
    
    to_process = [l for l in leads if not l.get('email') or l.get('email') == ''][:limit]
    print(f"Leads: {len(leads)} | To process: {len(to_process)}")
    
    for i, lead in enumerate(to_process):
        name = lead.get('company_name', 'Unknown')[:45]
        print(f"[{i+1:3d}/{len(to_process):3d}] {name:<45s} ", end='', flush=True)
        
        try:
            status = process_lead(lead)
            email_short = lead['email'][:35] if lead['email'] else "None"
            print(f"{email_short}")
            
            # Save after each lead
            if filetype in ('salon', 'hvac_gmaps'):
                data['leads'] = leads
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
            else:
                with open(filepath, 'w') as f:
                    json.dump(leads, f, indent=2)
            
            time.sleep(0.15)
        except Exception as e:
            print(f"Error: {e}")
    
    # Final save
    if filetype in ('salon', 'hvac_gmaps'):
        data['leads'] = leads
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    else:
        with open(filepath, 'w') as f:
            json.dump(leads, f, indent=2)
    
    print(f"Saved {len(leads)} leads")

if __name__ == "__main__":
    base = "/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research"
    
    files = [
        (f"{base}/salon-leads-dfw.json", "salon"),
        (f"{base}/auto-leads-dfw.json", "auto"),
        (f"{base}/hvac-leads-dfw-BATCH2.json", "hvac_batch2"),
        (f"{base}/hvac-leads-GMAPS.json", "hvac_gmaps"),
        (f"{base}/dental-leads-dfw.json", "dental"),
    ]
    
    for fp, ft in files:
        if Path(fp).exists():
            process_file(fp, ft, limit=150)
        else:
            print(f"Not found: {fp}")
    
    print("\n✅ Complete!")
