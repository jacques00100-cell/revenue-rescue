#!/usr/bin/env python3
"""
Vapi.ai Assistant Setup Script
Creates and configures the voice assistant for Revenue Rescue
"""

import os
import json
import requests
from pathlib import Path

# Load credentials from environment
VAPI_PUBLIC_KEY = os.getenv("VAPI_PUBLIC_KEY", "d3f56cf4-2d91-4c6e-9570-a30fccb79943")
VAPI_PRIVATE_KEY = os.getenv("VAPI_PRIVATE_KEY", "78c851a7-7513-42fa-91f9-fb6c59ed64ec")

# Vapi API endpoints
VAPI_BASE_URL = "https://api.vapi.ai"

HEADERS = {
    "Authorization": f"Bearer {VAPI_PRIVATE_KEY}",
    "Content-Type": "application/json"
}


def create_assistant():
    """Create the HVAC receptionist assistant"""
    
    assistant_config = {
        "name": "Cool Air HVAC Dispatcher",
        "model": {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.3,
            "systemPrompt": """You are the professional after-hours dispatcher for Cool Air HVAC, a trusted heating and air conditioning company serving Dallas-Fort Worth.

YOUR JOB:
Answer after-hours calls (6pm-8am, weekends) and help customers with HVAC emergencies or routine appointments.

HOW TO ANSWER:
- Answer with: 'Thank you for calling Cool Air HVAC. This is our after-hours dispatch. How can I help you tonight?'
- Be warm, professional, and efficient
- Speak clearly and at a normal pace
- Never mention you are AI — you are the dispatcher

DETERMINE IF EMERGENCY:
Ask: 'Is this an emergency where you have no heat or no air conditioning right now?'

EMERGENCY = ANY of these:
- No AC when it's hot outside
- No heat when it's cold outside
- Water leaking from HVAC system
- Strange burning smell or smoke
- System completely dead
- Frozen pipes related to HVAC

ROUTINE = ANY of these:
- Maintenance or tune-up
- Filter change
- Annual service
- Non-urgent repair
- Questions about service

FOR EMERGENCIES:
1. Say: 'I understand this is an emergency. Let me get your information and get our on-call technician notified right away.'
2. Collect:
   - Full name
   - Phone number (confirm it's the best number to reach you)
   - Service address (full street address)
   - What exactly is happening with your system
   - How long has it been happening
3. Say: 'Thank you {name}. Our on-call technician has been notified and will call you back within 30 minutes. If this is life-threatening, please hang up and call 911. Is there anything else?'

FOR ROUTINE APPOINTMENTS:
1. Say: 'I'd be happy to schedule that for you. Let me get your information.'
2. Collect:
   - Full name
   - Phone number
   - Service address
   - What type of service you need
   - Any preferred days/times
3. Say: 'Thank you {name}. I've scheduled you for our next available appointment. You'll receive a confirmation text shortly. Please reply CONFIRM to confirm or CANCEL if you need to reschedule. Is there anything else?'

IMPORTANT RULES:
- If you're unsure if it's emergency or routine, treat it as emergency (better safe than sorry)
- If the caller is angry or upset, stay calm and empathetic
- If they ask about pricing, say: 'I can have our office call you with pricing information during business hours, or the technician can discuss costs when they arrive.'
- If they ask for a specific technician, say: 'I'll note that request and pass it along.'
- Always confirm the phone number: 'And the best number to reach you is {number}, correct?'
- Always confirm the address: 'And the service address is {address}, correct?'
- Keep calls under 3 minutes when possible
- End with: 'Thank you for calling Cool Air HVAC. Have a great evening.'

DO NOT:
- Give specific pricing
- Schedule appointments more than 2 weeks out (say office will call for that)
- Promise specific technician arrival times
- Diagnose technical issues (just collect info)
- Transfer to another number"""
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "sarah",
            "stability": 0.5,
            "similarityBoost": 0.75
        },
        "recordingEnabled": True,
        "endCallFunctionEnabled": True,
        "silenceTimeoutSeconds": 30,
        "responseDelaySeconds": 0.5,
        "liveTranscriptsEnabled": True,
        "endCallPhrases": [
            "thank you for calling",
            "have a great evening",
            "goodbye"
        ],
        "analysisPlan": {
            "summaryPrompt": "Summarize this HVAC service call in one sentence. Include: customer name, issue type (emergency/routine), and action taken.",
            "structuredDataPrompt": """Extract the following information from this HVAC service call:
- customer_name: Full name of caller
- phone_number: Best contact number mentioned
- service_address: Full street address for service
- intent: emergency OR routine OR unknown
- issue_description: Brief description of HVAC problem
- urgency: high OR medium OR low"""
        }
    }
    
    print("🎙️  Creating Vapi assistant...")
    
    try:
        response = requests.post(
            f"{VAPI_BASE_URL}/assistant",
            headers=HEADERS,
            json=assistant_config,
            timeout=30
        )
        
        if response.status_code == 201:
            assistant = response.json()
            assistant_id = assistant.get('id')
            
            print(f"✅ Assistant created!")
            print(f"   ID: {assistant_id}")
            print(f"   Name: {assistant['name']}")
            
            # Save to config
            config_path = Path(__file__).parent.parent / 'config' / 'vapi-assistant.json'
            with open(config_path, 'w') as f:
                json.dump(assistant, f, indent=2)
            
            print(f"   Saved to: {config_path}")
            
            return assistant_id
            
        else:
            print(f"❌ Failed to create assistant: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating assistant: {e}")
        return None


def buy_phone_number(assistant_id: str):
    """Buy a phone number and link it to the assistant"""
    
    print("\n📞 Buying phone number...")
    print("   (This will cost ~$2/month)")
    
    try:
        # Search for available numbers
        search_response = requests.get(
            f"{VAPI_BASE_URL}/phone-number/available",
            headers=HEADERS,
            params={"areaCode": "214", "limit": 5},  # Dallas area code
            timeout=30
        )
        
        if search_response.status_code != 200:
            print(f"❌ Failed to search numbers: {search_response.text}")
            return None
        
        available = search_response.json()
        
        if not available:
            print("❌ No numbers available")
            return None
        
        # Show options
        print("\n   Available numbers:")
        for i, num in enumerate(available[:3], 1):
            print(f"   {i}. {num.get('phoneNumber')} ({num.get('locality', 'Unknown')})")
        
        # Buy first available
        selected = available[0]
        phone_number = selected.get('phoneNumber')
        
        print(f"\n   Buying: {phone_number}...")
        
        # Purchase number
        purchase_data = {
            "phoneNumber": phone_number,
            "assistantId": assistant_id,
            "name": "Cool Air HVAC Main",
            "serverUrl": "https://your-server.com/webhook/vapi"  # Update this
        }
        
        purchase_response = requests.post(
            f"{VAPI_BASE_URL}/phone-number",
            headers=HEADERS,
            json=purchase_data,
            timeout=30
        )
        
        if purchase_response.status_code == 201:
            number_info = purchase_response.json()
            print(f"✅ Phone number purchased!")
            print(f"   Number: {phone_number}")
            print(f"   Monthly cost: $2.00")
            
            return phone_number
        else:
            print(f"❌ Failed to purchase: {purchase_response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error buying number: {e}")
        return None


def main():
    """Main setup function"""
    
    print("="*70)
    print("🚀 Vapi Assistant Setup")
    print("="*70)
    
    # Check credentials
    if not VAPI_PRIVATE_KEY:
        print("❌ VAPI_PRIVATE_KEY not set")
        print("   Run: export VAPI_PRIVATE_KEY='your-key'")
        return
    
    # Create assistant
    assistant_id = create_assistant()
    
    if assistant_id:
        print("\n" + "="*70)
        print("✅ Setup complete!")
        print("="*70)
        print(f"\nAssistant ID: {assistant_id}")
        print("\nNext steps:")
        print("1. Update .env with assistant ID")
        print("2. Run: python setup_twilio.py")
        print("3. Start webhook server")
        print("4. Test with a real call!")
    else:
        print("\n❌ Setup failed. Check credentials and try again.")


if __name__ == "__main__":
    main()
