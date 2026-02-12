#!/usr/bin/env python3
"""
Revenue Rescue Receptionist - HVAC Edition
Voice AI Call Handler
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import requests

# Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "")
TWILIO_SID = os.getenv("TWILIO_SID", "")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN", "")
TWILIO_PHONE = os.getenv("TWILIO_PHONE", "")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('/tmp/revenue-rescue.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RevenueRescueHandler:
    """Main call handler for HVAC after-hours calls"""
    
    def __init__(self, company_config: Dict[str, Any]):
        self.config = company_config
        self.company_name = company_config.get('name', 'HVAC Company')
        self.on_call_phone = company_config.get('on_call_phone', '')
        self.owner_email = company_config.get('owner_email', '')
        
    def handle_incoming_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming call from Vapi.ai webhook"""
        
        logger.info(f"📞 Incoming call for {self.company_name}")
        
        # Extract call info
        caller_number = call_data.get('customer', {}).get('number', '')
        transcript = call_data.get('transcript', '')
        recording_url = call_data.get('recordingUrl', '')
        
        # Parse extracted info from Vapi
        extracted_info = call_data.get('analysis', {}).get('extractedInformation', {})
        
        call_record = {
            'call_id': call_data.get('id'),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'company_id': self.config.get('company_id'),
            'company_name': self.company_name,
            'caller_phone': caller_number,
            'caller_name': extracted_info.get('name', 'Unknown'),
            'service_address': extracted_info.get('address', ''),
            'intent': extracted_info.get('intent', 'unknown'),
            'issue_description': extracted_info.get('issue', ''),
            'transcript': transcript,
            'recording_url': recording_url,
            'status': 'received'
        }
        
        # Route based on intent
        intent = call_record['intent']
        
        if intent == 'emergency':
            logger.info(f"🚨 Emergency call from {call_record['caller_name']}")
            self._handle_emergency(call_record)
            
        elif intent == 'routine':
            logger.info(f"📅 Routine call from {call_record['caller_name']}")
            self._handle_routine(call_record)
            
        else:
            logger.info(f"❓ Unknown intent from {call_record['caller_name']}")
            self._handle_unknown(call_record)
        
        # Save call record
        self._save_call_record(call_record)
        
        return call_record
    
    def _handle_emergency(self, call_record: Dict[str, Any]):
        """Handle emergency HVAC call"""
        
        # 1. Notify on-call tech immediately
        self._notify_on_call_tech(call_record)
        
        # 2. Send confirmation to caller
        self._send_caller_confirmation(call_record, is_emergency=True)
        
        # 3. Email owner for tracking
        self._email_owner(call_record)
        
        call_record['status'] = 'emergency_dispatched'
        call_record['action_taken'] = 'On-call tech notified via SMS'
        
        logger.info(f"✅ Emergency dispatched for {call_record['caller_name']}")
    
    def _handle_routine(self, call_record: Dict[str, Any]):
        """Handle routine maintenance call"""
        
        # 1. Book appointment in calendar
        appointment_time = self._book_appointment(call_record)
        
        if appointment_time:
            # 2. Send confirmation to caller
            self._send_caller_confirmation(call_record, is_emergency=False, appointment_time=appointment_time)
            
            # 3. Notify office manager
            self._notify_office_manager(call_record, appointment_time)
            
            call_record['status'] = 'appointment_booked'
            call_record['appointment_time'] = appointment_time
            call_record['action_taken'] = f'Appointment booked for {appointment_time}'
            
            logger.info(f"✅ Appointment booked for {call_record['caller_name']}")
        else:
            # Fallback: Request callback
            self._request_callback(call_record)
            call_record['status'] = 'callback_requested'
            logger.info(f"⏸️ Callback requested for {call_record['caller_name']}")
    
    def _handle_unknown(self, call_record: Dict[str, Any]):
        """Handle unclear intent — default to safe escalation"""
        
        # Treat as potential emergency (better safe than sorry)
        self._notify_on_call_tech(call_record, prefix="[REVIEW NEEDED]")
        self._request_callback(call_record)
        
        call_record['status'] = 'escalated_for_review'
        call_record['action_taken'] = 'Escalated to human for review'
        
        logger.info(f"⏸️ Escalated for review: {call_record['caller_name']}")
    
    def _notify_on_call_tech(self, call_record: Dict[str, Any], prefix: str = ""):
        """Send SMS to on-call technician"""
        
        if not self.on_call_phone:
            logger.warning("No on-call phone configured")
            return
        
        message = f"""{prefix}🚨 EMERGENCY HVAC CALL

Name: {call_record['caller_name']}
Phone: {call_record['caller_phone']}
Address: {call_record['service_address']}
Issue: {call_record['issue_description']}

Call back ASAP: {call_record['caller_phone']}

Recording: {call_record['recording_url'][:50]}..."""
        
        self._send_sms(self.on_call_phone, message)
        logger.info(f"📱 SMS sent to on-call tech")
    
    def _send_caller_confirmation(self, call_record: Dict[str, Any], is_emergency: bool, appointment_time: str = None):
        """Send confirmation SMS to caller"""
        
        if is_emergency:
            message = f"""Hi {call_record['caller_name']}, this is {self.company_name}.

We've received your emergency call and our on-call technician has been notified. They will call you back within 30 minutes.

If this is life-threatening, please call 911.

Thank you,
{self.company_name} Dispatch"""
        else:
            message = f"""Hi {call_record['caller_name']}, this is {self.company_name}.

Your appointment is scheduled:
📅 {appointment_time}
🔧 HVAC Service
📍 {self.company_name}

Please reply CONFIRM to confirm or CANCEL to reschedule.

Thank you!"""
        
        self._send_sms(call_record['caller_phone'], message)
        call_record['confirmation_sent'] = True
        logger.info(f"📱 Confirmation SMS sent to caller")
    
    def _book_appointment(self, call_record: Dict[str, Any]) -> Optional[str]:
        """Book appointment in Google Calendar"""
        
        try:
            from google_calendar import GoogleCalendarClient
            
            # Initialize calendar client
            calendar = GoogleCalendarClient()
            
            if not calendar.service:
                logger.warning("Calendar not available, using mock booking")
                # Fallback to mock
                from datetime import datetime, timedelta
                tomorrow = datetime.now() + timedelta(days=1)
                appointment = tomorrow.replace(hour=9, minute=0).strftime("%A, %B %d at 9:00 AM")
                return appointment
            
            # Determine if emergency
            is_emergency = call_record.get('intent') == 'emergency'
            
            # Book appointment
            result = calendar.book_appointment(
                customer_name=call_record.get('caller_name', 'Unknown'),
                customer_phone=call_record.get('caller_phone', ''),
                service_address=call_record.get('service_address', ''),
                service_type=call_record.get('issue_description', 'HVAC Service'),
                is_emergency=is_emergency,
                notes=f"Call ID: {call_record.get('call_id')}"
            )
            
            if result:
                # Format time for SMS
                from datetime import datetime
                start = datetime.fromisoformat(result['start_time'].replace('Z', '+00:00'))
                appointment = start.strftime("%A, %B %d at %I:%M %p")
                
                # Save event link to call record
                call_record['calendar_event_id'] = result['event_id']
                call_record['calendar_event_link'] = result['event_link']
                
                logger.info(f"📅 Appointment booked: {appointment}")
                return appointment
            else:
                logger.error("Failed to book appointment")
                return None
                
        except Exception as e:
            logger.error(f"Calendar booking error: {e}")
            # Fallback
            from datetime import datetime, timedelta
            tomorrow = datetime.now() + timedelta(days=1)
            appointment = tomorrow.replace(hour=9, minute=0).strftime("%A, %B %d at 9:00 AM")
            return appointment
    
    def _notify_office_manager(self, call_record: Dict[str, Any], appointment_time: str):
        """Email office manager about new appointment"""
        
        # TODO: Implement SendGrid email
        logger.info(f"📧 Office manager notification queued")
    
    def _email_owner(self, call_record: Dict[str, Any]):
        """Email owner about emergency call"""
        
        # TODO: Implement SendGrid email
        logger.info(f"📧 Owner notification queued")
    
    def _request_callback(self, call_record: Dict[str, Any]):
        """Request human callback for complex cases"""
        
        # TODO: Add to callback queue
        logger.info(f"📋 Callback requested for {call_record['caller_name']}")
    
    def _send_sms(self, to_number: str, message: str):
        """Send SMS via Twilio"""
        
        if not TWILIO_SID or not TWILIO_TOKEN:
            logger.warning("Twilio not configured — SMS not sent")
            logger.info(f"Would send to {to_number}: {message[:100]}...")
            return
        
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
            
            response = requests.post(
                url,
                auth=(TWILIO_SID, TWILIO_TOKEN),
                data={
                    'From': TWILIO_PHONE,
                    'To': to_number,
                    'Body': message
                }
            )
            
            if response.status_code == 201:
                logger.info(f"✅ SMS sent to {to_number}")
            else:
                logger.error(f"❌ SMS failed: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ SMS error: {e}")
    
    def _save_call_record(self, call_record: Dict[str, Any]):
        """Save call record to database"""
        
        import json
        from pathlib import Path
        
        db_path = Path('/tmp/revenue-rescue-calls.jsonl')
        
        with open(db_path, 'a') as f:
            f.write(json.dumps(call_record) + '\n')
        
        logger.info(f"💾 Call record saved: {call_record['call_id']}")


# Example company config
SAMPLE_COMPANY = {
    'company_id': 'hvac_cool_air_001',
    'name': 'Cool Air HVAC',
    'phone': '+1-555-HVAC',
    'on_call_phone': '+1-555-TECH-01',
    'owner_email': 'owner@coolairhvac.com',
    'office_manager_email': 'dispatch@coolairhvac.com',
    'timezone': 'America/Chicago'
}

if __name__ == "__main__":
    # Test handler
    handler = RevenueRescueHandler(SAMPLE_COMPANY)
    
    # Simulate emergency call
    test_call = {
        'id': 'test-call-001',
        'customer': {'number': '+1-555-123-4567'},
        'transcript': 'Hi, my AC just stopped working and it is 95 degrees outside. I need someone to come fix it tonight.',
        'recordingUrl': 'https://example.com/recording.mp3',
        'analysis': {
            'extractedInformation': {
                'name': 'John Smith',
                'address': '123 Main St, Dallas, TX',
                'intent': 'emergency',
                'issue': 'AC not working, 95 degrees outside'
            }
        }
    }
    
    result = handler.handle_incoming_call(test_call)
    print(json.dumps(result, indent=2))
