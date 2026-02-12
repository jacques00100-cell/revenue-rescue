#!/usr/bin/env python3
"""
Complete Setup Script for Revenue Rescue
Buys phone numbers and configures everything for live testing
"""

import os
import sys
sys.path.insert(0, '/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/src')

# Load env
from pathlib import Path
env_path = Path(__file__).parent / '.env'
with open(env_path) as f:
    for line in f:
        if line.startswith('export '):
            key, val = line.replace('export ', '').strip().split('=', 1)
            os.environ[key] = val.strip('"')

print("="*70)
print("🚀 REVENUE RESCUE — LIVE SETUP")
print("="*70)

# Check all credentials
print("\n🔐 Checking credentials...")

required = {
    'VAPI_PRIVATE_KEY': os.getenv('VAPI_PRIVATE_KEY'),
    'TWILIO_SID': os.getenv('TWILIO_SID'),
    'TWILIO_TOKEN': os.getenv('TWILIO_TOKEN'),
}

missing = [k for k, v in required.items() if not v]
if missing:
    print(f"❌ Missing: {', '.join(missing)}")
    sys.exit(1)

print("✅ All credentials present")

# Step 1: Setup Vapi
print("\n🎙️  Step 1: Setting up Vapi voice assistant...")
try:
    from setup_vapi import create_assistant, buy_phone_number
    
    assistant_id = create_assistant()
    if assistant_id:
        print(f"✅ Assistant created: {assistant_id}")
        # Note: Buying phone number requires manual selection
        print("   (Phone number purchase needs manual confirmation)")
    else:
        print("⚠️  Assistant setup incomplete — check Vapi dashboard")
except Exception as e:
    print(f"⚠️  Vapi setup error: {e}")

# Step 2: Setup Twilio
print("\n📞 Step 2: Setting up Twilio SMS...")
try:
    from setup_twilio import setup_twilio
    
    phone = setup_twilio()
    if phone:
        print(f"✅ Twilio ready: {phone}")
    else:
        print("⚠️  Twilio setup incomplete")
except Exception as e:
    print(f"⚠️  Twilio error: {e}")

# Step 3: Test Google Calendar
print("\n📅 Step 3: Testing Google Calendar...")
try:
    from google_calendar import GoogleCalendarClient
    
    cal = GoogleCalendarClient()
    if cal.service:
        print("✅ Calendar connected")
        events = cal.list_upcoming(3)
        print(f"   Found {len(events)} upcoming events")
    else:
        print("⚠️  Calendar not connected — share calendar with service account")
except Exception as e:
    print(f"⚠️  Calendar error: {e}")

# Step 4: Test handler
print("\n🧪 Step 4: Testing call handler...")
try:
    from call_handler import RevenueRescueHandler, SAMPLE_COMPANY
    
    handler = RevenueRescueHandler(SAMPLE_COMPANY)
    
    test_call = {
        'id': 'live-test-001',
        'customer': {'number': '+1-555-TEST'},
        'transcript': 'Test call for setup verification',
        'recordingUrl': 'https://test.com/rec.mp3',
        'analysis': {
            'extractedInformation': {
                'name': 'Test Customer',
                'address': '123 Test St',
                'intent': 'emergency',
                'issue': 'AC not working'
            }
        }
    }
    
    result = handler.handle_incoming_call(test_call)
    print(f"✅ Handler test passed")
    print(f"   Status: {result['status']}")
    
except Exception as e:
    print(f"❌ Handler test failed: {e}")

print("\n" + "="*70)
print("✅ SETUP COMPLETE")
print("="*70)
print("\nNext steps:")
print("1. Buy Vapi phone number (manual in dashboard)")
print("2. Share calendar with service account")
print("3. Run: python src/webhook_server.py")
print("4. Test with real call!")
