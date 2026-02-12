#!/usr/bin/env python3
"""
Twilio Phone Number Setup
Purchase a phone number for the HVAC business
"""

import os
from twilio.rest import Client
from pathlib import Path

# Load credentials
TWILIO_SID = os.getenv("TWILIO_SID", "")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN", "e14bda475d21dcfa27dc4d2a50bb1828")


def setup_twilio():
    """Set up Twilio phone number"""
    
    print("="*70)
    print("📞 Twilio Phone Number Setup")
    print("="*70)
    
    if not TWILIO_SID or not TWILIO_TOKEN:
        print("\n❌ Missing Twilio credentials")
        print("   Need:")
        print("   - TWILIO_SID (Account SID from console.twilio.com)")
        print("   - TWILIO_TOKEN (already have)")
        print("\n   Get your Account SID from:")
        print("   https://console.twilio.com")
        print("   → Account → API keys & tokens")
        return None
    
    try:
        # Initialize client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        
        # Get account info
        account = client.api.accounts(TWILIO_SID).fetch()
        print(f"\n✅ Connected to Twilio")
        print(f"   Account: {account.friendly_name}")
        print(f"   Status: {account.status}")
        
        # Check existing numbers
        print("\n📱 Checking existing phone numbers...")
        numbers = client.incoming_phone_numbers.list()
        
        if numbers:
            print(f"   Found {len(numbers)} number(s):")
            for num in numbers:
                print(f"   • {num.phone_number} → {num.friendly_name}")
            
            use_existing = input("\nUse existing number? (y/n): ").lower() == 'y'
            
            if use_existing:
                selected = numbers[0]
                print(f"\n✅ Using: {selected.phone_number}")
                return selected.phone_number
        
        # Search for new number
        print("\n🔍 Searching for available numbers...")
        print("   Area code: 214 (Dallas)")
        
        available = client.available_phone_numbers("US").local.list(
            area_code="214",
            limit=5
        )
        
        if not available:
            print("❌ No numbers available in 214")
            print("   Trying toll-free...")
            
            available = client.available_phone_numbers("US").toll_free.list(limit=5)
        
        if not available:
            print("❌ No numbers available")
            return None
        
        # Show options
        print("\n   Available numbers:")
        for i, num in enumerate(available[:3], 1):
            print(f"   {i}. {num.phone_number}")
        
        # Buy number
        print(f"\n   Purchasing: {available[0].phone_number}...")
        
        new_number = client.incoming_phone_numbers.create(
            phone_number=available[0].phone_number,
            friendly_name="Cool Air HVAC Main"
        )
        
        print(f"✅ Number purchased!")
        print(f"   Phone: {new_number.phone_number}")
        print(f"   Monthly: $1.00")
        print(f"   Per minute: $0.0085")
        
        # Save to env file
        env_path = Path(__file__).parent.parent / '.env'
        with open(env_path, 'r') as f:
            content = f.read()
        
        content = content.replace(
            'export TWILIO_PHONE="your_twilio_phone_number"',
            f'export TWILIO_PHONE="{new_number.phone_number}"'
        )
        
        with open(env_path, 'w') as f:
            f.write(content)
        
        print(f"   Updated .env with new number")
        
        return new_number.phone_number
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nCommon issues:")
        print("- Invalid Account SID")
        print("- Insufficient account balance")
        print("- API key permissions")
        return None


def configure_sms_webhook(phone_number: str):
    """Configure SMS webhook for replies"""
    
    print("\n📲 Configuring SMS webhook...")
    
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        
        # Find the number
        numbers = client.incoming_phone_numbers.list(phone_number=phone_number)
        
        if not numbers:
            print("❌ Number not found")
            return
        
        number_sid = numbers[0].sid
        
        # Update webhook URL (you'll need to update this with your actual URL)
        webhook_url = "https://your-server.com/webhook/twilio"
        
        client.incoming_phone_numbers(number_sid).update(
            sms_url=webhook_url,
            sms_method="POST"
        )
        
        print(f"✅ SMS webhook configured")
        print(f"   URL: {webhook_url}")
        print("   (Update this when server is deployed)")
        
    except Exception as e:
        print(f"❌ Error configuring webhook: {e}")


if __name__ == "__main__":
    phone = setup_twilio()
    
    if phone:
        configure_sms_webhook(phone)
        
        print("\n" + "="*70)
        print("✅ Twilio setup complete!")
        print("="*70)
        print(f"\nPhone number: {phone}")
        print("\nTest it:")
        print(f"1. Call: {phone}")
        print("2. Text: Send 'CONFIRM' to {phone}")
        print("3. Check: python src/dashboard.py")
    else:
        print("\n❌ Setup incomplete")
        print("Need: Twilio Account SID")
