# Revenue Rescue Receptionist — HVAC Edition

AI-powered after-hours call answering for HVAC companies. Captures emergency calls, books appointments, notifies technicians.

## Value Proposition

**For HVAC Companies:**
- Never miss another emergency call = never lose high-value jobs ($200-800 each)
- Capture after-hours leads when competitors go to voicemail
- Professional 24/7 dispatch without hiring overnight staff
- ROI: 1 saved emergency call per month pays for the service

**Pricing:** $199/month flat rate

## How It Works

```
Customer Calls After Hours
         ↓
    [Vapi AI Voice Agent]
         ↓
   Intent Classification
         ↓
   ┌─────┴─────┐
   ▼           ▼
Emergency    Routine
   ↓           ↓
SMS to      Calendar
On-Call     Booking
Tech        ↓
   ↓       SMS
Customer    Confirmation
Confirm     ↓
ation      Office
           Notified
```

## Quick Start

### 1. Configure Environment

```bash
export VAPI_API_KEY="your_vapi_key"
export TWILIO_SID="your_twilio_sid"
export TWILIO_TOKEN="your_twilio_token"
export TWILIO_PHONE="+15551234567"
export GOOGLE_CALENDAR_ID="your_calendar_id"
```

### 2. Test the Handler

```bash
cd builds/revenue-rescue/tests
python test_handler.py
```

### 3. Start Webhook Server

```bash
cd builds/revenue-rescue/src
python webhook_server.py 8080
```

### 4. View Dashboard

```bash
cd builds/revenue-rescue/src
python dashboard.py
```

## Architecture

### Core Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Voice AI | Vapi.ai | Answer calls, collect info |
| SMS | Twilio | Notifications |
| Email | SendGrid | Office notifications |
| Calendar | Google Calendar API | Booking |
| Database | JSONL (MVP) → PostgreSQL | Call records |
| Server | Python HTTP | Webhooks |

### File Structure

```
builds/revenue-rescue/
├── src/
│   ├── call_handler.py      # Main business logic
│   ├── webhook_server.py    # HTTP server for webhooks
│   └── dashboard.py         # CLI dashboard
├── config/
│   ├── vapi-assistant.json  # Voice AI configuration
│   └── companies.json       # Company configs
├── tests/
│   └── test_handler.py      # Test suite
└── docs/
    └── README.md            # This file
```

## API Endpoints

### Vapi Webhook
```
POST /webhook/vapi
Content-Type: application/json

{
  "id": "call-id",
  "customer": {"number": "+15551234567"},
  "transcript": "...",
  "analysis": {
    "extractedInformation": {
      "name": "John Smith",
      "intent": "emergency",
      "issue": "AC not working"
    }
  }
}
```

### Twilio Webhook
```
POST /webhook/twilio
From: +15551234567
Body: CONFIRM
```

### Health Check
```
GET /health
→ {"status": "healthy"}
```

## Testing

### Run All Tests
```bash
cd tests
python test_handler.py
```

### Manual Test
```bash
# Start server
python src/webhook_server.py &

# Send test webhook
curl -X POST http://localhost:8080/webhook/vapi \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-001",
    "customer": {"number": "+15551234567"},
    "transcript": "Test call",
    "analysis": {
      "extractedInformation": {
        "name": "Test User",
        "intent": "emergency",
        "issue": "No AC"
      }
    }
  }'
```

## Deployment

### Local (Development)
```bash
python src/webhook_server.py 8080
```

### Production (VPS)
```bash
# Using systemd
sudo cp config/revenue-rescue.service /etc/systemd/system/
sudo systemctl enable revenue-rescue
sudo systemctl start revenue-rescue
```

### Ngrok (For Vapi Webhooks)
```bash
ngrok http 8080
# Use https URL for Vapi webhook configuration
```

## Configuration

### Company Config (companies.json)

```json
{
  "company_id": "cool-air-hvac",
  "name": "Cool Air HVAC",
  "phone": "+1-555-HVAC",
  "on_call_phone": "+1-555-TECH-01",
  "owner_email": "owner@coolairhvac.com",
  "timezone": "America/Chicago",
  "monthly_fee": 199
}
```

### Vapi Assistant Config

Edit `config/vapi-assistant.json`:
- Update company name
- Adjust system prompt for your brand voice
- Set webhook URL to your server

## Monitoring

### View Logs
```bash
tail -f /tmp/revenue-rescue.log
tail -f /tmp/revenue-rescue-server.log
```

### View Call Records
```bash
python src/dashboard.py
```

### View Specific Call
```bash
python src/dashboard.py <call-id>
```

## Next Steps (Post-MVP)

- [ ] Google Calendar API integration (real booking)
- [ ] SendGrid email integration
- [ ] ServiceTitan/Housecall Pro integration
- [ ] Web dashboard (not CLI)
- [ ] Multi-company support
- [ ] Call analytics
- [ ] On-call rotation management

## Support

Questions? Check:
1. Logs in `/tmp/revenue-rescue*.log`
2. Call records in `/tmp/revenue-rescue-calls.jsonl`
3. Company config in `config/companies.json`

## License

Internal use only — PAC Automation
