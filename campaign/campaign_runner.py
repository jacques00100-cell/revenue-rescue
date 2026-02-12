#!/usr/bin/env python3
"""
Revenue Rescue Campaign Runner
Automated email campaign system with engagement tracking
"""

import sqlite3
import csv
import json
import yaml
import smtplib
import imaplib
import email
import re
import time
import hashlib
import uuid
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Optional
import requests
from jinja2 import Template

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config.yaml"
with open(CONFIG_PATH) as f:
    CONFIG = yaml.safe_load(f)

DB_PATH = Path(__file__).parent / CONFIG['database']['path']


def init_database():
    """Initialize SQLite database with campaign tracking schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id TEXT PRIMARY KEY,
            lead_email TEXT NOT NULL,
            lead_name TEXT,
            business_name TEXT,
            industry TEXT,
            city TEXT,
            state TEXT,
            phone TEXT,
            website TEXT,
            priority_score INTEGER,
            email_1_sent_at TIMESTAMP,
            email_1_opened BOOLEAN DEFAULT 0,
            email_1_opened_at TIMESTAMP,
            email_1_clicked BOOLEAN DEFAULT 0,
            email_1_clicked_at TIMESTAMP,
            email_1_replied BOOLEAN DEFAULT 0,
            email_1_replied_at TIMESTAMP,
            email_2_sent_at TIMESTAMP,
            email_2_opened BOOLEAN DEFAULT 0,
            email_2_opened_at TIMESTAMP,
            email_2_clicked BOOLEAN DEFAULT 0,
            email_2_clicked_at TIMESTAMP,
            email_2_replied BOOLEAN DEFAULT 0,
            email_2_replied_at TIMESTAMP,
            email_3_sent_at TIMESTAMP,
            email_3_opened BOOLEAN DEFAULT 0,
            email_3_opened_at TIMESTAMP,
            email_3_clicked BOOLEAN DEFAULT 0,
            email_3_clicked_at TIMESTAMP,
            email_3_replied BOOLEAN DEFAULT 0,
            email_3_replied_at TIMESTAMP,
            sentiment_score REAL,
            sentiment_label TEXT,
            reply_content TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracking_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id TEXT,
            event_type TEXT,
            email_number INTEGER,
            ip_address TEXT,
            user_agent TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            date TEXT PRIMARY KEY,
            emails_sent INTEGER DEFAULT 0,
            emails_opened INTEGER DEFAULT 0,
            emails_clicked INTEGER DEFAULT 0,
            emails_replied INTEGER DEFAULT 0,
            sentiment_positive INTEGER DEFAULT 0,
            sentiment_neutral INTEGER DEFAULT 0,
            sentiment_negative INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized")


def generate_campaign_id(lead_email: str) -> str:
    """Generate unique campaign ID"""
    return hashlib.md5(f"{lead_email}:{uuid.uuid4()}".encode()).hexdigest()[:16]


def load_leads(csv_path: str, limit: int = 50) -> List[Dict]:
    """Load top priority leads from CSV"""
    leads = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip if no email address
            if 'Email' in row and row['Email']:
                leads.append({
                    'email': row['Email'],
                    'name': row.get('Contact Name', row.get('Business Name', '')),
                    'business_name': row.get('Business Name', ''),
                    'phone': row.get('Phone Number', ''),
                    'website': row.get('Website', ''),
                    'industry': row.get('Industry', ''),
                    'city': row.get('City', ''),
                    'state': row.get('State', 'TX'),
                    'priority_score': int(row.get('Priority Score', 0) or 0)
                })
    
    # Sort by priority score (descending)
    leads.sort(key=lambda x: x['priority_score'], reverse=True)
    return leads[:limit]


def get_first_name(full_name: str) -> str:
    """Extract first name from full name"""
    if not full_name:
        return "there"
    return full_name.split()[0]


def render_email(template_path: str, lead: Dict, campaign_id: str, email_num: int) -> str:
    """Render email template with lead data"""
    with open(template_path) as f:
        template = Template(f.read())
    
    tracking_pixel = f"{CONFIG['tracking']['base_url']}/track/open/{campaign_id}/{email_num}"
    unsubscribe_url = f"{CONFIG['tracking']['base_url']}/unsubscribe/{campaign_id}"
    calendly_url = CONFIG['demo']['calendly_url']
    
    return template.render(
        first_name=get_first_name(lead['name']),
        business_name=lead['business_name'],
        city=lead['city'],
        state=lead['state'],
        tracking_pixel=tracking_pixel,
        unsubscribe_url=unsubscribe_url,
        calendly_url=calendly_url,
        view_in_browser=f"{CONFIG['tracking']['base_url']}/view/{campaign_id}/{email_num}"
    )


def send_email_resend(to_email: str, subject: str, html_content: str) -> bool:
    """Send email via Resend API"""
    if CONFIG['campaign'].get('dry_run', True):
        print(f"  [DRY RUN] Would send to: {to_email}")
        print(f"  Subject: {subject}")
        return True
    
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {CONFIG['email']['resend_api_key']}"},
            json={
                "from": f"{CONFIG['sender']['name']} <{CONFIG['sender']['email']}",
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }
        )
        return response.status_code == 200
    except Exception as e:
        print(f"  ✗ Failed to send: {e}")
        return False


def send_email_sendgrid(to_email: str, subject: str, html_content: str) -> bool:
    """Send email via SendGrid API"""
    if CONFIG['campaign'].get('dry_run', True):
        print(f"  [DRY RUN] Would send to: {to_email}")
        print(f"  Subject: {subject}")
        return True
    
    try:
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {CONFIG['email']['sendgrid_api_key']}"},
            json={
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": CONFIG['sender']['email'], "name": CONFIG['sender']['name']},
                "subject": subject,
                "content": [{"type": "text/html", "value": html_content}]
            }
        )
        return response.status_code in [200, 202]
    except Exception as e:
        print(f"  ✗ Failed to send: {e}")
        return False


def send_campaign_email(lead: Dict, campaign_id: str, email_num: int) -> bool:
    """Send a specific email in the sequence"""
    templates = {
        1: ("email_templates/email_1_cold_intro.html", "{first_name}, quick question about after-hours calls"),
        2: ("email_templates/email_2_followup.html", "Re: {first_name} - the $500 question"),
        3: ("email_templates/email_3_final.html", "{first_name}, last try")
    }
    
    if email_num not in templates:
        return False
    
    template_path, subject_template = templates[email_num]
    template_path = Path(__file__).parent / template_path
    
    first_name = get_first_name(lead['name'])
    subject = subject_template.format(first_name=first_name)
    html_content = render_email(template_path, lead, campaign_id, email_num)
    
    # Choose provider
    provider = CONFIG['email']['provider']
    if provider == 'resend':
        success = send_email_resend(lead['email'], subject, html_content)
    else:
        success = send_email_sendgrid(lead['email'], subject, html_content)
    
    if success and not CONFIG['campaign'].get('dry_run', True):
        # Update database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        column = f"email_{email_num}_sent_at"
        cursor.execute(f"UPDATE campaigns SET {column} = ? WHERE id = ?", 
                      (datetime.now(), campaign_id))
        conn.commit()
        conn.close()
    
    return success


def import_leads(csv_path: str, limit: int = 50):
    """Import leads into campaign database"""
    leads = load_leads(csv_path, limit)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    imported = 0
    for lead in leads:
        campaign_id = generate_campaign_id(lead['email'])
        
        cursor.execute('''
            INSERT OR IGNORE INTO campaigns 
            (id, lead_email, lead_name, business_name, industry, city, state, phone, website, priority_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (campaign_id, lead['email'], lead['name'], lead['business_name'],
              lead['industry'], lead['city'], lead['state'], lead['phone'],
              lead['website'], lead['priority_score']))
        
        if cursor.rowcount > 0:
            imported += 1
    
    conn.commit()
    conn.close()
    print(f"✓ Imported {imported} leads into campaign database")
    return imported


def run_campaign(csv_path: str, dry_run: bool = True):
    """Main campaign execution"""
    print("=" * 60)
    print("REVENUE RESCUE EMAIL CAMPAIGN")
    print("=" * 60)
    
    # Initialize
    init_database()
    
    # Import leads
    imported = import_leads(csv_path)
    if imported == 0:
        print("No new leads to import. Checking for pending sends...")
    
    # Get leads ready for each email
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Email 1: Not yet sent
    cursor.execute('''
        SELECT id, lead_email, lead_name, business_name, city, state 
        FROM campaigns 
        WHERE email_1_sent_at IS NULL AND status = 'active'
        LIMIT ?
    ''', (CONFIG['campaign']['rate_limit_per_hour'],))
    
    email_1_ready = cursor.fetchall()
    
    # Email 2: Sent 3+ days ago, not opened/replied, not sent yet
    cursor.execute('''
        SELECT id, lead_email, lead_name, business_name, city, state 
        FROM campaigns 
        WHERE email_1_sent_at IS NOT NULL 
        AND email_1_sent_at < datetime('now', '-3 days')
        AND email_2_sent_at IS NULL
        AND status = 'active'
        LIMIT ?
    ''', (CONFIG['campaign']['rate_limit_per_hour'],))
    
    email_2_ready = cursor.fetchall()
    
    # Email 3: Sent 7+ days after email 2, not sent yet
    cursor.execute('''
        SELECT id, lead_email, lead_name, business_name, city, state 
        FROM campaigns 
        WHERE email_2_sent_at IS NOT NULL 
        AND email_2_sent_at < datetime('now', '-7 days')
        AND email_3_sent_at IS NULL
        AND status = 'active'
        LIMIT ?
    ''', (CONFIG['campaign']['rate_limit_per_hour'],))
    
    email_3_ready = cursor.fetchall()
    
    conn.close()
    
    print(f"\n📧 Ready to send:")
    print(f"   Email 1 (Cold Intro): {len(email_1_ready)} leads")
    print(f"   Email 2 (Follow-up):  {len(email_2_ready)} leads")
    print(f"   Email 3 (Final):      {len(email_3_ready)} leads")
    
    if dry_run:
        print("\n🧪 DRY RUN MODE - No emails will be sent")
        print("Set dry_run: false in config.yaml to enable live sending")
    
    # Send emails with rate limiting
    rate_limit = CONFIG['campaign']['rate_limit_per_hour']
    delay_seconds = 3600 / rate_limit
    
    total_sent = 0
    
    for email_num, leads in [(1, email_1_ready), (2, email_2_ready), (3, email_3_ready)]:
        if not leads:
            continue
        
        print(f"\n📤 Sending Email {email_num} to {len(leads)} leads...")
        
        for i, (campaign_id, email, name, biz, city, state) in enumerate(leads):
            lead = {
                'email': email, 'name': name, 'business_name': biz,
                'city': city, 'state': state
            }
            
            print(f"  [{i+1}/{len(leads)}] {name} ({email})...", end=" ")
            
            success = send_campaign_email(lead, campaign_id, email_num)
            if success:
                print("✓")
                total_sent += 1
            else:
                print("✗")
            
            if not dry_run and i < len(leads) - 1:
                time.sleep(delay_seconds)
    
    print(f"\n✅ Campaign run complete. {total_sent} emails processed.")
    print(f"\n📊 Generate report: python campaign_runner.py --report")


def generate_report():
    """Generate campaign performance report"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Overall stats
    cursor.execute('''
        SELECT 
            COUNT(*) as total_leads,
            SUM(CASE WHEN email_1_sent_at IS NOT NULL THEN 1 ELSE 0 END) as email_1_sent,
            SUM(CASE WHEN email_1_opened = 1 THEN 1 ELSE 0 END) as email_1_opened,
            SUM(CASE WHEN email_1_clicked = 1 THEN 1 ELSE 0 END) as email_1_clicked,
            SUM(CASE WHEN email_2_sent_at IS NOT NULL THEN 1 ELSE 0 END) as email_2_sent,
            SUM(CASE WHEN email_2_opened = 1 THEN 1 ELSE 0 END) as email_2_opened,
            SUM(CASE WHEN email_2_clicked = 1 THEN 1 ELSE 0 END) as email_2_clicked,
            SUM(CASE WHEN email_3_sent_at IS NOT NULL THEN 1 ELSE 0 END) as email_3_sent,
            SUM(CASE WHEN email_3_opened = 1 THEN 1 ELSE 0 END) as email_3_opened,
            SUM(CASE WHEN email_3_clicked = 1 THEN 1 ELSE 0 END) as email_3_clicked,
            SUM(CASE WHEN sentiment_label = 'interested' THEN 1 ELSE 0 END) as interested,
            SUM(CASE WHEN sentiment_label = 'not_now' THEN 1 ELSE 0 END) as not_now
        FROM campaigns
    ''')
    
    stats = cursor.fetchone()
    conn.close()
    
    print("\n" + "=" * 60)
    print("CAMPAIGN PERFORMANCE REPORT")
    print("=" * 60)
    
    if stats[0] == 0:
        print("No campaign data yet.")
        return
    
    total = stats[0]
    print(f"\n📊 Total Leads: {total}")
    
    print("\n📧 Email 1 (Cold Intro):")
    print(f"   Sent: {stats[1]} | Opened: {stats[2]} ({stats[2]/stats[1]*100:.1f}%) | Clicked: {stats[3]} ({stats[3]/stats[1]*100:.1f}%)")
    
    if stats[4]:
        print("\n📧 Email 2 (Follow-up):")
        print(f"   Sent: {stats[4]} | Opened: {stats[5]} ({stats[5]/stats[4]*100:.1f}%) | Clicked: {stats[6]} ({stats[6]/stats[4]*100:.1f}%)")
    
    if stats[7]:
        print("\n📧 Email 3 (Final):")
        print(f"   Sent: {stats[7]} | Opened: {stats[8]} ({stats[8]/stats[7]*100:.1f}%) | Clicked: {stats[9]} ({stats[9]/stats[7]*100:.1f}%)")
    
    print(f"\n🎯 Interested Leads: {stats[10] or 0}")
    print(f"⏰ 'Not Now' Responses: {stats[11] or 0}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--report":
        generate_report()
    else:
        csv_path = sys.argv[1] if len(sys.argv) > 1 else "../../leads-for-import.csv"
        run_campaign(csv_path, dry_run=CONFIG['campaign'].get('dry_run', True))
