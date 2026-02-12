#!/usr/bin/env python3
"""
Targeted enrichment - Dental and Salon (lower email rates)
Plus any remaining HVAC
"""
import json
import re
import subprocess
import time

EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+', re.IGNORECASE)
FALSE_PATTERNS = ['bootstrap', 'jquery', 'email@email', 'your@email', 'example@', 'test@', 
                  'demo@', 'user@', 'admin@admin', 'info@info', 'contact@contact',
                  'wixpress', 'gstatic', 'google', 'facebook', 'sentry.io',
                  'react@', 'vue@', 'lodash@', 'jquery@', 'core-js@', 'axios@', 'webpack@',
                  'intl-segmenter@', 'fancybox', 'popper@', 'wp-content']

def fetch(url):
    if not url:
        return ""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    try:
        result = subprocess.run(
            ['curl', '-s', '-L', '-A', 'Mozilla/5.0', '--max-time', '5', '--connect-timeout', '3', url],
            capture_output=True, text=True, timeout=7
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
                if len(domain) > 3 and '.' in domain[-5:] and not domain.endswith(('.png', '.jpg', '.gif', '.svg')):
                    valid.append(e.lower())
    return list(set(valid))

def get_best_email(emails):
    if not emails:
        return ""
    priority = ['contact@', 'info@', 'hello@', 'support@', 'admin@', 'office@', 'service@', 'help@']
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
    
    # Find contact page
    contact_match = re.search(r'href=["\']([^"\']*contact[^"\']*)["\']', main, re.I)
    contact_url = None
    if contact_match:
        m = contact_match.group(1)
        if m.startswith('http'):
            contact_url = m
        elif m.startswith('/'):
            contact_url = website.rstrip('/') + m
    
    if contact_url and contact_url != website:
        contact = fetch(contact_url)
    else:
        contact = ""
    
    all_content = main + "\n" + contact
    
    emails = extract_emails(all_content)
    lead['email'] = get_best_email(emails)
    lead['contact_page'] = contact_url if contact_url else ""
    lead['has_online_booking'] = any(x in all_content.lower() for x in ['book now', 'schedule', 'appointment', 'booking'])
    lead['has_live_chat'] = any(x in all_content.lower() for x in ['live chat', 'chat now', 'chat with us'])
    
    if lead['email']:
        lead['best_contact_method'] = "email"
    elif lead['has_live_chat']:
        lead['best_contact_method'] = "chat"
    elif contact_url:
        lead['best_contact_method'] = "form"
    else:
        lead['best_contact_method'] = "phone" if lead.get('phone') else ""
    
    return bool(lead['email'])

def process_dental():
    print("="*60)
    print("PROCESSING DENTAL LEADS")
    print("="*60)
    
    with open('/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/dental-leads-dfw.json') as f:
        leads = json.load(f)
    
    to_process = [l for l in leads if not l.get('email') or l.get('email') == '']
    print(f"To process: {len(to_process)}")
    
    found = 0
    for i, lead in enumerate(to_process):
        name = lead.get('company_name', 'Unknown')[:40]
        rating = lead.get('rating', 'N/A')
        
        has_email = process_lead(lead)
        if has_email:
            found += 1
            email = lead['email'][:35]
        else:
            email = '-'
        
        print(f"[{i+1:3d}] {name:<40s} [R:{rating}] {email}")
        
        if (i + 1) % 10 == 0:
            with open('/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/dental-leads-dfw.json', 'w') as f:
                json.dump(leads, f, indent=2)
        
        time.sleep(0.1)
    
    with open('/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/dental-leads-dfw.json', 'w') as f:
        json.dump(leads, f, indent=2)
    
    print(f"✅ Dental: {found} new emails")
    return found

def process_salon():
    print("\n" + "="*60)
    print("PROCESSING SALON LEADS")
    print("="*60)
    
    with open('/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/salon-leads-dfw.json') as f:
        data = json.load(f)
        leads = data.get('leads', [])
    
    to_process = [l for l in leads if not l.get('email') or l.get('email') == '']
    print(f"To process: {len(to_process)}")
    
    found = 0
    for i, lead in enumerate(to_process):
        name = lead.get('company_name', 'Unknown')[:40]
        rating = lead.get('rating', 'N/A')
        
        has_email = process_lead(lead)
        if has_email:
            found += 1
            email = lead['email'][:35]
        else:
            email = '-'
        
        print(f"[{i+1:3d}] {name:<40s} [R:{rating}] {email}")
        
        if (i + 1) % 10 == 0:
            data['leads'] = leads
            with open('/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/salon-leads-dfw.json', 'w') as f:
                json.dump(data, f, indent=2)
        
        time.sleep(0.1)
    
    data['leads'] = leads
    with open('/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/salon-leads-dfw.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Salon: {found} new emails")
    return found

def process_hvac_gmaps():
    print("\n" + "="*60)
    print("PROCESSING HVAC GMAPS LEADS")
    print("="*60)
    
    with open('/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/hvac-leads-GMAPS.json') as f:
        data = json.load(f)
        leads = data.get('leads', [])
    
    to_process = [l for l in leads if not l.get('email') or l.get('email') == '']
    print(f"To process: {len(to_process)}")
    
    found = 0
    for i, lead in enumerate(to_process):
        name = lead.get('company_name', 'Unknown')[:40]
        
        has_email = process_lead(lead)
        if has_email:
            found += 1
            email = lead['email'][:35]
        else:
            email = '-'
        
        print(f"[{i+1:2d}] {name:<40s} {email}")
        
        data['leads'] = leads
        with open('/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/hvac-leads-GMAPS.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        time.sleep(0.1)
    
    print(f"✅ HVAC GMaps: {found} new emails")
    return found

if __name__ == "__main__":
    total = 0
    total += process_dental()
    total += process_salon()
    total += process_hvac_gmaps()
    
    print(f"\n{'='*60}")
    print(f"🎯 TOTAL NEW EMAILS: {total}")
    print('='*60)
