#!/usr/bin/env python3
"""
Preview Campaign Emails (Dry Run)
Shows sample of first 5 emails without sending - no dependencies required
"""

import csv
import sys
from pathlib import Path

def get_first_name(full_name: str) -> str:
    if not full_name:
        return "there"
    return full_name.split()[0]


def load_leads(csv_path: str, limit: int = 5):
    leads = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append({
                'business_name': row.get('Business Name', ''),
                'name': row.get('Contact Name', ''),
                'city': row.get('City', ''),
                'state': row.get('State', 'TX'),
                'industry': row.get('Industry', ''),
                'phone': row.get('Phone Number', ''),
                'priority': row.get('Priority Score', 'N/A')
            })
    return leads[:limit]


def show_email_preview(lead, email_num: int):
    first_name = get_first_name(lead['name'])
    
    subjects = {
        1: f"{first_name}, quick question about after-hours calls",
        2: f"Re: {first_name} - the $500 question",
        3: f"{first_name}, last try"
    }
    
    previews = {
        1: f"""Hi {first_name},

I was looking at {lead['business_name']}'s website and noticed you book appointments by phone. 
Quick question: What happens when someone calls after hours?

I ask because we work with salons across {lead['city']} who were shocked when 
they discovered this stat:

→ 80% of callers hang up when they reach voicemail

That means 4 out of 5 potential new clients are going to your competitors instead.

We built Revenue Rescue to answer those calls 24/7...

[Demo line: (817) 873-6706]""",
        
        2: f"""Hi {first_name},

Quick follow-up to my email about after-hours calls.

Here's the $500 question: If just ONE after-hours caller became a regular client, 
how much revenue would that be worth to {lead['business_name']}?

Let's do some quick math:
  Average salon visit: $85
  Visits per year: × 6
  ─────────────────────────
  Total client value: = $510

One missed call = potentially $500+ in lost lifetime value.

[Demo line: (817) 873-6706]""",
        
        3: f"""Hi {first_name},

I'll be direct — this is my last email about Revenue Rescue.

I know you're busy running {lead['business_name']}, and I don't want to clutter 
your inbox if this isn't a priority right now.

⚡ 3 BETA SPOTS REMAINING AT 50% OFF

Exclusive Beta Pricing:
  ~~$199/mo~~ → $99/mo
  
  ✓ AI answers calls 24/7
  ✓ Books directly into your calendar  
  ✓ Captures leads even when fully booked
  ✓ Set up in under 1 hour

[Book Your 15-Min Setup Call]

Not interested? Just reply "stop" and I'll remove you immediately.

Cheers,
Connor"""
    }
    
    return subjects[email_num], previews[email_num]


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "../../leads-for-import.csv"
    
    print("=" * 70)
    print("📧 REVENUE RESCUE EMAIL CAMPAIGN - DRY RUN PREVIEW")
    print("=" * 70)
    print(f"\nLoading first 5 priority leads from: {csv_path}\n")
    
    leads = load_leads(csv_path)
    
    for i, lead in enumerate(leads, 1):
        print(f"\n{'═' * 70}")
        print(f"🎯 LEAD #{i}: {lead['business_name']}")
        print(f"   📍 {lead['city']}, {lead['state']} | 🏢 {lead['industry']}")
        print(f"   ⭐ Priority Score: {lead['priority']}")
        print('═' * 70)
        
        for email_num in range(1, 4):
            subject, preview = show_email_preview(lead, email_num)
            
            print(f"\n   📨 EMAIL {email_num}")
            print(f"   ┌{'─' * 66}┐")
            print(f"   │ Subject: {subject[:58]:<58}│")
            print(f"   ├{'─' * 66}┤")
            for line in preview.split('\n'):
                while line:
                    chunk = line[:58]
                    line = line[58:]
                    print(f"   │ {chunk:<58} │")
            print(f"   └{'─' * 66}┘")
    
    print(f"\n{'=' * 70}")
    print("✅ PREVIEW COMPLETE")
    print("=" * 70)
    print("\n⚠️  IMPORTANT: Your leads CSV needs email addresses!")
    print("   Current CSV has: Business Name, Phone, Website, Industry, City, ZIP")
    print("   Missing: Email addresses")
    print("\n📝 NEXT STEPS:")
    print("   1. Run: python3 enrich_emails.py")
    print("      → Generates likely email patterns based on domain")
    print("   2. Verify emails with a service like Hunter.io")
    print("   3. Update config.yaml with your Resend API key")
    print("   4. Start tracking server: python3 tracking_server.py")
    print("   5. Run campaign: python3 campaign_runner.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
