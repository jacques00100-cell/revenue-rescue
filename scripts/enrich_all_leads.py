#!/usr/bin/env python3
"""
ENRICH ALL LEADS - Regardless of rating
Bad ratings = HOT leads for Revenue Rescue
"""
import json
import re
import subprocess
import time
from pathlib import Path

EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+', re.IGNORECASE)
FALSE_PATTERNS = ['bootstrap', 'jquery', 'email@email', 'your@email', 'example@', 'test@', 
                  'demo@', 'user@', 'admin@admin', 'info@info', 'contact@contact',
                  'wixpress', 'wix.com', 'squarespace', 'gstatic', 'google', 'facebook',
                  'splide@', 'popper.js', 'webreporting@gargle', 'wp-content', 'fonts@',
                  'wght@', 'pixel@', 'analytics@', 'gtag@', 'sentry.io', 'mailchimp',
                  'react@', 'vue@', 'angular@', 'lodash@', 'axios@', 'intl-segmenter',
                  'jquery@', 'core-js@', 'webpack@', 'babel@', 'typescript@']

def fetch(url):
    if not url:
        return ""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    try:
        result = subprocess.run(
            ['curl', '-s', '-L', '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 
             '--max-time', '10', '--connect-timeout', '5', url],
            capture_output=True, text=True, timeout=12
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
        e_lower = e.lower().strip()
        if not any(fp in e_lower for fp in FALSE_PATTERNS):
            if '@' in e and '.' in e.split('@')[-1]:
                domain = e.split('@')[1]
                if len(domain) > 3 and '.' in domain[-5:] and not domain.endswith(('.png', '.jpg', '.gif', '.svg', '.webp')):
                    valid.append(e_lower)
    return list(set(valid))

def get_best_email(emails):
    if not emails:
        return ""
    priority = ['contact@', 'info@', 'hello@', 'support@', 'admin@', 'office@', 'service@', 'sales@', 'repair@', 'help@']
    for p in priority:
        for e in emails:
            if p in e and 'noreply' not in e and 'no-reply' not in e:
                return e
    for e in emails:
        if 'noreply' not in e.lower() and 'no-reply' not in e.lower():
            return e
    return ""

def find_contact_url(base, content):
    if not content or not base:
        return None
    patterns = [
        r'href=["\']([^"\']*contact[^"\']*)["\']',
        r'href=["\']([^"\']*about[^"\']*)["\']',
        r'href=["\']([^"\']*reach-us[^"\']*)["\']'
    ]
    for pat in patterns:
        matches = re.findall(pat, content, re.I)
        for m in matches:
            if m.startswith('http'):
                return m
            elif m.startswith('/'):
                return base.rstrip('/') + m
            elif m.startswith('./'):
                return base.rstrip('/') + m[1:]
    return base.rstrip('/') + '/contact'

def has_booking(content):
    if not content:
        return False
    c = content.lower()
    keywords = ['book now', 'schedule now', 'online booking', 'appointment', 'calendly', 'acuity', 'vagaro', 'mindbody', 'square appointments']
    return any(k in c for k in keywords)

def has_chat(content):
    if not content:
        return False
    c = content.lower()
    keywords = ['live chat', 'chat now', 'chat with us', 'intercom', 'drift', 'tawk', 'zendesk', 'crisp', 'livechat']
    return any(k in c for k in keywords)

def process_lead(lead):
    website = lead.get('website')
    if not website:
        lead.update({
            "email": "", 
            "contact_page": "", 
            "has_online_booking": False, 
            "has_live_chat": False, 
            "best_contact_method": "phone" if lead.get('phone') else ""
        })
        return "no_website"
    
    main = fetch(website)
    if not main:
        lead.update({
            "email": "", 
            "contact_page": "", 
            "has_online_booking": False, 
            "has_live_chat": False, 
            "best_contact_method": "phone" if lead.get('phone') else ""
        })
        return "fetch_failed"
    
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
    
    return "success"

def process_file(filepath, filetype):
    print(f"\n{'='*70}")
    print(f"Processing: {filetype.upper()}")
    print(f"File: {filepath}")
    print('='*70)
    
    with open(filepath) as f:
        data = json.load(f)
    
    if filetype in ('salon', 'hvac_gmaps'):
        leads = data.get('leads', [])
    else:
        leads = data
    
    # Get leads without emails (regardless of priority)
    to_process = [l for l in leads if not l.get('email') or l.get('email') == '']
    already_done = len(leads) - len(to_process)
    
    print(f"Total leads: {len(leads)}")
    print(f"Already enriched: {already_done}")
    print(f"To process: {len(to_process)}")
    print()
    
    stats = {"success": 0, "no_website": 0, "fetch_failed": 0, "email_found": 0}
    
    for i, lead in enumerate(to_process):
        name = lead.get('company_name', 'Unknown')[:45]
        rating = lead.get('rating', 'N/A')
        priority = lead.get('priority', 'N/A')
        
        print(f"[{i+1:3d}/{len(to_process):3d}] {name:<45s} [R:{rating} P:{priority}] ", end='', flush=True)
        
        try:
            status = process_lead(lead)
            stats[status] = stats.get(status, 0) + 1
            if lead.get('email'):
                stats['email_found'] += 1
            
            email_short = (lead['email'][:30] + '...') if len(lead.get('email', '')) > 30 else lead.get('email', 'None')
            print(f"{email_short}")
            
            # Save every 5 leads
            if (i + 1) % 5 == 0:
                if filetype in ('salon', 'hvac_gmaps'):
                    data['leads'] = leads
                    with open(filepath, 'w') as f:
                        json.dump(data, f, indent=2)
                else:
                    with open(filepath, 'w') as f:
                        json.dump(leads, f, indent=2)
            
            time.sleep(0.15)
            
        except Exception as e:
            print(f"ERROR: {e}")
            stats['error'] = stats.get('error', 0) + 1
    
    # Final save
    if filetype in ('salon', 'hvac_gmaps'):
        data['leads'] = leads
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    else:
        with open(filepath, 'w') as f:
            json.dump(leads, f, indent=2)
    
    print()
    print(f"✅ {filetype.upper()} COMPLETE!")
    print(f"   Emails found this batch: {stats.get('email_found', 0)}")
    print(f"   Success: {stats.get('success', 0)} | No website: {stats.get('no_website', 0)} | Failed: {stats.get('fetch_failed', 0)}")
    
    return stats

if __name__ == "__main__":
    base = "/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research"
    
    files = [
        (f"{base}/dental-leads-dfw.json", "dental"),
        (f"{base}/auto-leads-dfw.json", "auto"),
        (f"{base}/hvac-leads-dfw-BATCH2.json", "hvac_batch2"),
        (f"{base}/hvac-leads-GMAPS.json", "hvac_gmaps"),
        (f"{base}/salon-leads-dfw.json", "salon"),
    ]
    
    all_stats = {}
    for fp, ft in files:
        if Path(fp).exists():
            all_stats[ft] = process_file(fp, ft)
        else:
            print(f"⚠ File not found: {fp}")
    
    print("\n" + "="*70)
    print("ALL FILES PROCESSED!")
    print("="*70)
    for ft, stats in all_stats.items():
        print(f"{ft}: {stats}")
