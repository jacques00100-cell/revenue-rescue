#!/usr/bin/env python3
"""
Google Calendar Integration for Revenue Rescue
Uses service account to book appointments
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

# Google API imports
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("⚠️  Google API libraries not installed")
    print("   Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")


class GoogleCalendarClient:
    """Google Calendar API client for booking appointments"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, calendar_id: str = None):
        self.calendar_id = calendar_id or os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with service account"""
        
        if not GOOGLE_AVAILABLE:
            print("❌ Google API not available")
            return
        
        try:
            # Path to service account file
            service_account_file = Path(__file__).parent.parent / 'config' / 'google-service-account.json'
            
            if not service_account_file.exists():
                print(f"❌ Service account file not found: {service_account_file}")
                return
            
            # Load credentials
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file,
                scopes=self.SCOPES
            )
            
            # Build service
            self.service = build('calendar', 'v3', credentials=credentials)
            print("✅ Google Calendar authenticated")
            
        except Exception as e:
            print(f"❌ Google auth error: {e}")
            self.service = None
    
    def book_appointment(self, 
                         customer_name: str,
                         customer_phone: str,
                         service_address: str,
                         service_type: str,
                         is_emergency: bool = False,
                         notes: str = "") -> Optional[Dict[str, Any]]:
        """Book an appointment in Google Calendar"""
        
        if not self.service:
            print("❌ Calendar service not available")
            return None
        
        try:
            # Calculate appointment time
            if is_emergency:
                # Emergency = Next available slot (tomorrow morning priority)
                start_time = self._get_next_available(priority=True)
            else:
                # Routine = Standard next available
                start_time = self._get_next_available(priority=False)
            
            # Duration: 2 hours for emergency, 1 hour for routine
            duration_hours = 2 if is_emergency else 1
            end_time = start_time + timedelta(hours=duration_hours)
            
            # Build event
            event = {
                'summary': f"{'🚨 ' if is_emergency else ''}HVAC Service - {customer_name}",
                'location': service_address,
                'description': f"""Customer: {customer_name}
Phone: {customer_phone}
Address: {service_address}
Service: {service_type}
Type: {'Emergency' if is_emergency else 'Routine'}

{notes}

Booked by Revenue Rescue AI""",
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/Chicago',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/Chicago',
                },
                'attendees': [
                    {'email': 'dispatch@coolairhvac.com'}
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }
            
            # Create event
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            print(f"✅ Appointment booked: {event.get('htmlLink')}")
            
            return {
                'event_id': event.get('id'),
                'event_link': event.get('htmlLink'),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
            
        except HttpError as e:
            print(f"❌ Calendar API error: {e}")
            return None
        except Exception as e:
            print(f"❌ Booking error: {e}")
            return None
    
    def _get_next_available(self, priority: bool = False) -> datetime:
        """Get next available appointment slot"""
        
        now = datetime.now()
        
        if priority:
            # Emergency = Tomorrow at 8am
            tomorrow = now + timedelta(days=1)
            return tomorrow.replace(hour=8, minute=0, second=0, microsecond=0)
        else:
            # Routine = Day after tomorrow at 9am
            day_after = now + timedelta(days=2)
            return day_after.replace(hour=9, minute=0, second=0, microsecond=0)
    
    def list_upcoming(self, max_results: int = 10) -> list:
        """List upcoming appointments"""
        
        if not self.service:
            return []
        
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
            
        except Exception as e:
            print(f"❌ List error: {e}")
            return []


if __name__ == "__main__":
    # Test calendar integration
    print("="*70)
    print("📅 Testing Google Calendar Integration")
    print("="*70)
    
    client = GoogleCalendarClient()
    
    if client.service:
        # Test booking
        result = client.book_appointment(
            customer_name="Test Customer",
            customer_phone="+1-555-TEST",
            service_address="123 Test St, Dallas, TX",
            service_type="AC Maintenance",
            is_emergency=False,
            notes="Test booking from setup script"
        )
        
        if result:
            print(f"\n✅ Test booking successful!")
            print(f"   Link: {result['event_link']}")
        else:
            print("\n❌ Test booking failed")
            
        # List upcoming
        print("\n📋 Upcoming appointments:")
        events = client.list_upcoming(5)
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(f"   {start} - {event['summary']}")
    else:
        print("\n❌ Calendar not connected")
        print("   Check:")
        print("   1. google-service-account.json exists")
        print("   2. Service account has calendar access")
        print("   3. Calendar is shared with service account")
