#!/bin/bash
# Start Revenue Rescue — LIVE MODE

cd /Users/connorsisk/.openclaw/workspace/builds/revenue-rescue

echo "🚀 STARTING REVENUE RESCUE — LIVE MODE"
echo "=========================================="

# Load environment
export $(grep -v '^#' .env | xargs)

echo ""
echo "📞 Phone Number: $TWILIO_PHONE"
echo "🎙️  Assistant ID: $VAPI_ASSISTANT_ID"
echo ""

# Check if ngrok is needed for webhooks
echo "🔍 Checking webhook configuration..."

# For now, run locally with ngrok
# In production, this would be a real server URL

echo ""
echo "📋 To complete setup:"
echo "1. Install ngrok: brew install ngrok"
echo "2. Run: ngrok http 8080"
echo "3. Copy https URL"
echo "4. Update Vapi webhook: dashboard.vapi.ai"
echo "5. Update Twilio webhook: console.twilio.com"
echo ""
echo "Starting server on port 8080..."
echo ""

python3 src/webhook_server.py 8080
