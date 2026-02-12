#!/usr/bin/env python3
"""
Night Shift Lead Enrichment - Batch Processor
Uses web_fetch via function calls to scrape websites
"""
import json
import re
import subprocess
import time
from pathlib import Path

# Regex patterns
EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+', re.IGNORECASE)
BOOKING_RE = re.compile(r'book|schedule|appointment|booking|mindbody|squareup|acuity|calendly|vagaro', re.IGNORECASE)
CHAT_RE = re.compile(r'live.chat|chat.now|intercom|drift|tawk|zendesk|crisp|livechat', re.IGNORECASE)

def fetch_with_curl(url):
    """Fetch URL content using curl (faster than python requests)"""
    if not url:
        return ""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        result = subprocess.run(
            ['curl', '-s', '-L', '-A', 'Mozilla/5.0 (compatible; LeadBot/1.0)', 
             '--max-time', '10', '--connect-timeout', '5', url],
            capture_output=True,
            text=True,
            timeout=12
        )
        return result.stdout if result.returncode == 0 else ""
    except:
        return ""

def extract_info(content):
    """Extract all relevant info from HTML content"""
    if not content:
        return {"emails": [], "has_booking": False, "has_chat": False}
    
    c_lower = content.lower()
    
    # Extract emails
    emails = EMAIL_RE.findall(content)
    emails = [e.lower().strip() for e in emails if '@' in e and '.' in e.split('@')[-1]]
    # Filter out junk
    emails = [e for e in emails if not any(x in e for x in ['example.', 'test.', 'demo.', '.png', '.jpg', '.gif', 'wixpress', 'wix.com', 'squarespace'])]
    emails = list(set(emails))
    
    # Check for booking
    has_booking = bool(BOOKING_RE.search(c_lower))
    # More specific booking indicators
    booking_indicators = ['book now', 'schedule now', 'online booking', 'request appointment', 'book online']
    has_booking = has_booking or any(ind in c_lower for ind in booking_indicators)
    
    # Check for live chat
    has_chat = bool(CHAT_RE.search(c_lower))
    
    return {"emails": emails, "has_booking": has_booking, "has_chat": has_chat}

def get_best_email(emails):
    """Select best email from list, filtering out false positives"""
    if not emails:
        return ""
    
    # Filter out false positives
    false_patterns = ['bootstrap', 'jquery', 'email@email', 'your@email', 'example@', 'test@', 
                      'demo@', 'user@', 'admin@admin', 'info@info', 'contact@contact',
                      'wixpress', 'wix.com', 'squarespace', 'gstatic', 'google', 'facebook',
                      'splide@', 'popper.js', 'webreporting@gargle', 'wp-content', 'fonts@']
    
    valid_emails = []
    for e in emails:
        e_lower = e.lower()
        if not any(fp in e_lower for fp in false_patterns):
            # Check for valid domain
            if '@' in e and '.' in e.split('@')[-1]:
                domain = e.split('@')[1]
                if len(domain) > 3 and '.' in domain:
                    valid_emails.append(e)
    
    if not valid_emails:
        return ""
    
    priority = ['contact@', 'info@', 'hello@', 'support@', 'admin@', 'office@', 'reception@', 'dr@', 'dentistry@']
    for p in priority:
        for e in valid_emails:
            if p in e.lower() and 'noreply' not in e.lower():
                return e
    
    # Return first non-noreply
    for e in valid_emails:
        if 'noreply' not in e.lower() and 'no-reply' not in e.lower():
            return e
    return valid_emails[0]

def find_contact_url(base_url, content):
    """Find contact page URL from content"""
    if not content or not base_url:
        return None
    
    # Look for contact links
    patterns = [
        r'href=["\']([^"\']*contact[^"\']*)["\']',
        r'href=["\']([^"\']*about[^"\']*)["\']',
        r'href=["\']([^"\']*reach-us[^"\']*)["\']',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if match.startswith('http'):
                return match
            elif match.startswith('/'):
                return base_url.rstrip('/') + match
    
    # Default guesses
    return base_url.rstrip('/') + '/contact'

def process_lead(lead):
    """Process a single lead"""
    website = lead.get('website')
    
    if not website:
        lead['email'] = ""
        lead['contact_page'] = ""
        lead['has_online_booking'] = False
        lead['has_live_chat'] = False
        lead['best_contact_method'] = "phone" if lead.get('phone') else ""
        return lead, "no_website"
    
    # Fetch main page
    main_content = fetch_with_curl(website)
    
    if not main_content:
        lead['email'] = ""
        lead['contact_page'] = ""
        lead['has_online_booking'] = False
        lead['has_live_chat'] = False
        lead['best_contact_method'] = "phone" if lead.get('phone') else ""
        return lead, "fetch_failed"
    
    # Find contact page
    contact_url = find_contact_url(website, main_content)
    
    # Fetch contact page
    contact_content = ""
    if contact_url and contact_url != website:
        contact_content = fetch_with_curl(contact_url)
    
    # Combine content
    all_content = main_content + "\n" + contact_content
    
    # Extract info
    info = extract_info(all_content)
    
    # Update lead
    lead['email'] = get_best_email(info['emails'])
    lead['contact_page'] = contact_url if contact_url else ""
    lead['has_online_booking'] = info['has_booking']
    lead['has_live_chat'] = info['has_chat']
    
    # Determine best contact method
    if lead['email']:
        lead['best_contact_method'] = "email"
    elif info['has_chat']:
        lead['best_contact_method'] = "chat"
    elif contact_url:
        lead['best_contact_method'] = "form"
    else:
        lead['best_contact_method'] = "phone" if lead.get('phone') else ""
    
    return lead, "success"

def process_file(file_type, file_path, limit=None, high_priority_only=False):
    """Process leads from a file"""
    print(f"\n{'='*70}")
    print(f"PROCESSING: {file_type.upper()}")
    print(f"{'='*70}")
    
    # Load leads
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if file_type == 'salon':
        leads = data.get('leads', [])
    elif file_type == 'hvac_gmaps':
        leads = data.get('leads', [])
    else:
        leads = data
    
    total = len(leads)
    print(f"Total leads: {total}")
    
    # Filter for high priority
    if high_priority_only:
        def is_hp(l):
            r = l.get('rating')
            return (r is not None and r >= 4.8) or l.get('priority') == 'high'
        to_process = [l for l in leads if is_hp(l) and not l.get('email')]
    else:
        to_process = [l for l in leads if not l.get('email')]
    
    if limit:
        to_process = to_process[:limit]
    
    print(f"To process: {len(to_process)}")
    print()
    
    stats = {"success": 0, "no_website": 0, "fetch_failed": 0}
    
    for i, lead in enumerate(to_process):
        name = lead.get('company_name', 'Unknown')[:50]
        website = lead.get('website', '')
        print(f"[{i+1:3d}/{len(to_process):3d}] {name:<50s} ", end='', flush=True)
        
        try:
            lead, status = process_lead(lead)
            stats[status] = stats.get(status, 0) + 1
            
            email_short = lead['email'][:30] if lead['email'] else "None"
            print(f"✓ {email_short:<30s} Booking:{str(lead['has_online_booking']):5s} Chat:{str(lead['has_live_chat']):5s}")
            
            # Rate limiting
            time.sleep(0.2)
            
            # Save progress every 10 leads
            if (i + 1) % 10 == 0:
                if file_type == 'salon':
                    data['leads'] = leads
                    with open(file_path, 'w') as f:
                        json.dump(data, f, indent=2)
                elif file_type == 'hvac_gmaps':
                    data['leads'] = leads
                    with open(file_path, 'w') as f:
                        json.dump(data, f, indent=2)
                else:
                    with open(file_path, 'w') as f:
                        json.dump(leads, f, indent=2)
                print(f"  [SAVED]")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            stats['error'] = stats.get('error', 0) + 1
    
    # Final save
    print("\nFinal save...")
    # Save updated data
    if file_type == 'salon':
        data['leads'] = leads
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    elif file_type == 'hvac_gmaps':
        data['leads'] = leads
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    else:
        with open(file_path, 'w') as f:
            json.dump(leads, f, indent=2)
    
    print()
    print(f"💾 Saved!")
    print(f"   Success: {stats.get('success', 0)}")
    print(f"   No website: {stats.get('no_website', 0)}")
    print(f"   Fetch failed: {stats.get('fetch_failed', 0)}")
    
    return stats

if __name__ == "__main__":
    import sys
    
    FILES = {
        'dental': '/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/dental-leads-dfw.json',
        'salon': '/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/salon-leads-dfw.json',
        'auto': '/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/auto-leads-dfw.json',
        'hvac_batch2': '/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/hvac-leads-dfw-BATCH2.json',
        'hvac_gmaps': '/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/hvac-leads-GMAPS.json',
    }
    
    high_priority_only = '--high-priority' in sys.argv
    
    all_stats = {}
    for ft, fp in FILES.items():
        if Path(fp).exists():
            all_stats[ft] = process_file(ft, fp, high_priority_only=high_priority_only)
        else:
            print(f"⚠ File not found: {fp}")
    
    print("\n" + "="*70)
    print("ENRICHMENT COMPLETE!")
    print("="*70)
    for ft, stats in all_stats.items():
        print(f"{ft}: {stats}")
