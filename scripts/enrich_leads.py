#!/usr/bin/env python3
"""
Lead Enrichment Script - Extract emails and contact info from websites
"""
import json
import re
import time
import subprocess
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

# Email regex patterns
EMAIL_PATTERNS = [
    r'[\w.+-]+@[\w-]+\.[\w.-]+',  # Standard email
    r'mailto:([\w.+-]+@[\w-]+\.[\w.-]+)',  # mailto links
]

# Booking/Scheduling keywords
BOOKING_KEYWORDS = [
    'book', 'schedule', 'appointment', 'reservation', 'booking',
    'online booking', 'schedule online', 'book now', 'schedule now',
    'appointments', 'scheduling', 'book appointment'
]

# Live chat keywords
CHAT_KEYWORDS = [
    'live chat', 'chat now', 'chat with us', 'livechat', 'chatbot',
    'intercom', 'drift', 'tawk.to', 'zendesk', 'freshchat',
    'olark', 'crisp', 'liveagent'
]

def fetch_url(url):
    """Fetch content from URL using web_fetch via subprocess"""
    if not url:
        return None
    try:
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        result = subprocess.run(
            ['python3', '-c', f'''
import sys
sys.path.insert(0, "/Users/connorsisk/.openclaw/workspace")
from skills.web_fetch import fetch
print(fetch("{url}"))
'''],
            capture_output=True,
            text=True,
            timeout=15
        )
        return result.stdout if result.returncode == 0 else None
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None

def extract_emails(content):
    """Extract email addresses from content"""
    if not content:
        return []
    emails = []
    for pattern in EMAIL_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        emails.extend(matches)
    # Filter and dedupe
    valid_emails = []
    for email in emails:
        email = email.lower().strip()
        if email and '@' in email and '.' in email.split('@')[-1]:
            # Filter out common false positives
            if not any(x in email for x in ['example.', 'test.', 'demo.', '.png', '.jpg', '.gif']):
                valid_emails.append(email)
    return list(set(valid_emails))

def find_contact_page_url(base_url, content):
    """Find contact page URL from content"""
    if not content or not base_url:
        return None
    
    # Look for contact links
    contact_patterns = [
        r'href=["\']([^"\']*contact[^"\']*)["\']',
        r'href=["\']([^"\']*about[^"\']*)["\']',
        r'href=["\']([^"\']*reach-us[^"\']*)["\']',
    ]
    
    for pattern in contact_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            # Take first match, make absolute URL
            contact_path = matches[0]
            if contact_path.startswith('http'):
                return contact_path
            return urljoin(base_url, contact_path)
    
    # Try common contact URLs
    common_paths = ['/contact', '/contact-us', '/about', '/about-us', '/reach-us']
    for path in common_paths:
        guess = urljoin(base_url, path)
        # Return the most likely one (contact is preferred)
        if 'contact' in path:
            return guess
    
    return None

def has_online_booking(content):
    """Check if content indicates online booking capability"""
    if not content:
        return False
    content_lower = content.lower()
    # Check for booking keywords
    for keyword in BOOKING_KEYWORDS:
        if keyword in content_lower:
            # Additional validation - look for actual booking mechanisms
            if any(x in content_lower for x in ['book now', 'schedule now', 'online booking', 'appointment']):
                return True
    # Check for common booking platforms
    booking_platforms = ['mindbody', 'squareup', 'acuity', 'calendly', 'booker', 'genbook', 'vagaro', 'schedulicity']
    for platform in booking_platforms:
        if platform in content_lower:
            return True
    return False

def has_live_chat(content):
    """Check if content indicates live chat capability"""
    if not content:
        return False
    content_lower = content.lower()
    # Check for chat keywords
    for keyword in CHAT_KEYWORDS:
        if keyword in content_lower:
            return True
    # Check for chat widget scripts
    chat_scripts = ['livechat', 'intercom', 'drift', 'tawk', 'zendesk', 'crisp']
    for script in chat_scripts:
        if script in content_lower:
            return True
    return False

def determine_best_contact_method(lead, emails, has_booking, has_chat, contact_page):
    """Determine best contact method based on available info"""
    # Filter out noreply emails
    good_emails = [e for e in emails if not any(x in e for x in ['noreply', 'no-reply', 'donotreply'])]
    
    if good_emails:
        return "email"
    elif has_chat:
        return "chat"
    elif contact_page:
        return "form"
    elif lead.get('phone'):
        return "phone"
    return "phone"  # Default

def get_priority_email(emails):
    """Get the best email from list (prefer contact@, info@, etc.)"""
    if not emails:
        return ""
    
    # Priority order for common business emails
    priority_patterns = ['contact@', 'info@', 'hello@', 'support@', 'admin@', 'office@']
    
    for pattern in priority_patterns:
        for email in emails:
            if pattern in email.lower():
                return email
    
    # Return first non-noreply email
    for email in emails:
        if 'noreply' not in email.lower() and 'no-reply' not in email.lower():
            return email
    
    return emails[0] if emails else ""

def load_leads(file_path, file_type):
    """Load leads from JSON file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if file_type == 'salon':
        return data.get('leads', [])
    elif file_type == 'hvac_gmaps':
        return data.get('leads', [])
    else:
        return data

def save_leads(file_path, file_type, leads):
    """Save leads back to JSON file"""
    if file_type == 'salon':
        with open(file_path, 'r') as f:
            data = json.load(f)
        data['leads'] = leads
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    elif file_type == 'hvac_gmaps':
        with open(file_path, 'r') as f:
            data = json.load(f)
        data['leads'] = leads
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    else:
        with open(file_path, 'w') as f:
            json.dump(leads, f, indent=2)

def enrich_lead(lead):
    """Enrich a single lead with contact information"""
    website = lead.get('website')
    
    if not website:
        lead['email'] = ""
        lead['contact_page'] = ""
        lead['has_online_booking'] = False
        lead['has_live_chat'] = False
        lead['best_contact_method'] = "phone" if lead.get('phone') else ""
        return lead
    
    print(f"  Fetching: {website}")
    
    # Fetch main page
    main_content = fetch_url(website)
    
    if not main_content:
        lead['email'] = ""
        lead['contact_page'] = ""
        lead['has_online_booking'] = False
        lead['has_live_chat'] = False
        lead['best_contact_method'] = "phone" if lead.get('phone') else ""
        return lead
    
    # Find contact page
    contact_page_url = find_contact_page_url(website, main_content)
    
    # Fetch contact page if different from main
    all_content = main_content
    if contact_page_url and contact_page_url != website:
        print(f"  Fetching contact page: {contact_page_url}")
        contact_content = fetch_url(contact_page_url)
        if contact_content:
            all_content += "\n" + contact_content
    
    # Extract information
    emails = extract_emails(all_content)
    booking = has_online_booking(all_content)
    chat = has_live_chat(all_content)
    
    # Update lead
    lead['email'] = get_priority_email(emails)
    lead['contact_page'] = contact_page_url if contact_page_url else ""
    lead['has_online_booking'] = booking
    lead['has_live_chat'] = chat
    lead['best_contact_method'] = determine_best_contact_method(lead, emails, booking, chat, contact_page_url)
    
    print(f"  ✓ Email: {lead['email'][:40] if lead['email'] else 'None'}")
    print(f"  ✓ Booking: {booking}, Chat: {chat}, Method: {lead['best_contact_method']}")
    
    return lead

def process_file(file_type, file_path, high_priority_only=False):
    """Process all leads in a file"""
    print(f"\n{'='*60}")
    print(f"Processing: {file_type.upper()}")
    print(f"File: {file_path}")
    print(f"{'='*60}")
    
    leads = load_leads(file_path, file_type)
    total = len(leads)
    
    print(f"Total leads: {total}")
    
    # Filter high priority if requested
    if high_priority_only:
        def is_high_priority(l):
            rating = l.get('rating')
            return (rating is not None and rating >= 4.8) or l.get('priority') == 'high'
        leads_to_process = [l for l in leads if is_high_priority(l)]
        print(f"High priority leads (4.8+): {len(leads_to_process)}")
    else:
        leads_to_process = leads
    
    # Process leads
    processed = 0
    skipped_no_website = 0
    
    for i, lead in enumerate(leads):
        # Check if this lead should be processed
        if high_priority_only and lead not in leads_to_process:
            continue
        
        # Skip if already enriched (has email field)
        if 'email' in lead and lead['email']:
            print(f"[{i+1}/{total}] {lead.get('company_name', 'Unknown')} - Already enriched")
            continue
        
        print(f"\n[{i+1}/{total}] {lead.get('company_name', 'Unknown')}")
        print(f"  Rating: {lead.get('rating', 'N/A')} | Priority: {lead.get('priority', 'N/A')}")
        
        if not lead.get('website'):
            print(f"  ⚠ No website - skipping")
            skipped_no_website += 1
            lead['email'] = ""
            lead['contact_page'] = ""
            lead['has_online_booking'] = False
            lead['has_live_chat'] = False
            lead['best_contact_method'] = "phone" if lead.get('phone') else ""
            continue
        
        try:
            enrich_lead(lead)
            processed += 1
            
            # Save progress every 5 leads
            if processed % 5 == 0:
                save_leads(file_path, file_type, leads)
                print(f"  💾 Progress saved ({processed} processed)")
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            lead['email'] = ""
            lead['contact_page'] = ""
            lead['has_online_booking'] = False
            lead['has_live_chat'] = False
            lead['best_contact_method'] = "phone" if lead.get('phone') else ""
    
    # Final save
    save_leads(file_path, file_type, leads)
    print(f"\n✅ {file_type.upper()} complete!")
    print(f"   Processed: {processed} | Skipped (no website): {skipped_no_website}")
    
    return leads

if __name__ == "__main__":
    import sys
    
    # Check for command line args
    high_priority_only = '--high-priority' in sys.argv
    
    # Process each file
    for file_type, file_path in FILES.items():
        if Path(file_path).exists():
            process_file(file_type, file_path, high_priority_only)
        else:
            print(f"⚠ File not found: {file_path}")
    
    print("\n" + "="*60)
    print("ENRICHMENT COMPLETE!")
    print("="*60)
