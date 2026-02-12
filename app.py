from flask import Flask, request, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

# In-memory storage (use Redis/DB in production)
calls = []
sms_log = []

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "revenue-rescue", "time": datetime.now().isoformat()})

@app.route('/webhook/vapi', methods=['POST'])
def vapi_webhook():
    """Handle Vapi voice calls - pass through to assistant"""
    data = request.json or {}
    
    # Log the call
    call_record = {
        "id": data.get('id', 'unknown'),
        "timestamp": datetime.now().isoformat(),
        "type": "voice",
        "data": data
    }
    calls.append(call_record)
    
    print(f"📞 Vapi call: {data.get('id')}")
    
    # Return 200 OK - Vapi will handle with configured assistant
    return jsonify({"status": "ok"}), 200

@app.route('/webhook/twilio', methods=['POST'])
def twilio_webhook():
    """Handle Twilio SMS"""
    data = request.form.to_dict()
    
    sms_record = {
        "timestamp": datetime.now().isoformat(),
        "type": "sms",
        "from": data.get('From'),
        "body": data.get('Body'),
        "data": data
    }
    sms_log.append(sms_record)
    
    print(f"💬 SMS from {data.get('From')}: {data.get('Body')}")
    
    # Twilio expects TwiML response
    return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Received. Our team will respond shortly.</Message>
</Response>""", 200, {'Content-Type': 'application/xml'}

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Simple dashboard view"""
    return jsonify({
        "total_calls": len(calls),
        "total_sms": len(sms_log),
        "recent_calls": calls[-10:],
        "recent_sms": sms_log[-10:]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
