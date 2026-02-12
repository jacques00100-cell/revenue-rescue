from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import json
import os
import sqlite3
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# Database setup
DB_PATH = '/tmp/revenue_rescue.db'

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Calls table
    c.execute('''
        CREATE TABLE IF NOT EXISTS calls (
            id TEXT PRIMARY KEY,
            timestamp TEXT,
            business_id TEXT DEFAULT 'demo',
            customer_phone TEXT,
            customer_name TEXT,
            transcript TEXT,
            issue_type TEXT,
            is_emergency BOOLEAN,
            booking_requested BOOLEAN,
            booking_confirmed BOOLEAN,
            technician_notified BOOLEAN,
            call_duration INTEGER,
            status TEXT DEFAULT 'open',
            raw_data TEXT
        )
    ''')
    
    # Appointments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id TEXT PRIMARY KEY,
            call_id TEXT,
            customer_name TEXT,
            customer_phone TEXT,
            service_address TEXT,
            issue_description TEXT,
            scheduled_date TEXT,
            scheduled_time TEXT,
            service_type TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            FOREIGN KEY (call_id) REFERENCES calls(id)
        )
    ''')
    
    # SMS log table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sms_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            from_number TEXT,
            to_number TEXT,
            body TEXT,
            direction TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

init_db()

def classify_issue(transcript):
    """Classify if emergency based on transcript keywords"""
    if not transcript:
        return 'routine', False
    
    emergency_keywords = [
        'no heat', 'no ac', 'no air', 'not working', 'completely dead',
        'leaking', 'water', 'burning smell', 'smoke', 'fire',
        'frozen', 'ice', 'urgent', 'emergency', 'dangerous',
        'unsafe', 'gas smell', 'carbon monoxide', 'pregnant', 'baby', 'elderly'
    ]
    
    transcript_lower = transcript.lower()
    
    for keyword in emergency_keywords:
        if keyword in transcript_lower:
            return 'emergency', True
    
    return 'routine', False

def extract_customer_name(transcript):
    """Extract customer name from transcript"""
    if not transcript:
        return None
    
    # Simple extraction - look for "my name is" or similar patterns
    import re
    patterns = [
        r'my name is (\w+)',
        r'this is (\w+)',
        r'name is (\w+)',
        r'(?:hello|hi) (?:i\'m|this is) (\w+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, transcript, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def send_emergency_alert(call_data):
    """Send email alert for emergency calls"""
    try:
        # For demo, just print. In production, use SMTP
        print(f"🚨 EMERGENCY ALERT - Would send email:")
        print(f"   Customer: {call_data.get('customer_name', 'Unknown')}")
        print(f"   Phone: {call_data.get('customer_phone', 'Unknown')}")
        print(f"   Issue: {call_data.get('issue_type', 'Unknown')}")
        print(f"   Time: {datetime.now().isoformat()}")
        
        # TODO: Implement SMTP email sending
        # smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        # smtp_port = int(os.environ.get('SMTP_PORT', 587))
        # sender_email = os.environ.get('SENDER_EMAIL', 'Connor@pac-holding.com')
        # sender_password = os.environ.get('SENDER_PASSWORD')
        # recipient = os.environ.get('ALERT_EMAIL', 'connorsisk14@gmail.com')
        
    except Exception as e:
        print(f"❌ Failed to send alert: {e}")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    # Get counts from database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM calls')
    total_calls = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM calls WHERE is_emergency = 1')
    emergency_calls = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM appointments')
    total_appointments = c.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        "status": "healthy",
        "service": "revenue-rescue",
        "time": datetime.now().isoformat(),
        "metrics": {
            "total_calls": total_calls,
            "emergency_calls": emergency_calls,
            "total_appointments": total_appointments
        }
    })

@app.route('/webhook/vapi', methods=['POST'])
def vapi_webhook():
    """Handle Vapi voice calls - process conversation and log everything"""
    data = request.get_json() or {}
    
    message_type = data.get('message', {}).get('type', 'unknown')
    call_id = data.get('call', {}).get('id', 'unknown')
    
    print(f"📞 Vapi webhook: {message_type} | Call: {call_id}")
    
    # Handle end-of-call report
    if message_type == 'end-of-call-report':
        message = data.get('message', {})
        
        # Extract conversation data
        transcript = message.get('transcript', '')
        customer_name = extract_customer_name(transcript)
        issue_type, is_emergency = classify_issue(transcript)
        
        # Check if booking was requested
        booking_keywords = ['schedule', 'appointment', 'book', 'come out', 'send someone']
        booking_requested = any(kw in transcript.lower() for kw in booking_keywords)
        
        # Build call record
        call_record = {
            'id': call_id,
            'timestamp': datetime.now().isoformat(),
            'business_id': 'demo',  # Will be dynamic per client
            'customer_phone': data.get('call', {}).get('customer', {}).get('number'),
            'customer_name': customer_name,
            'transcript': transcript,
            'issue_type': issue_type,
            'is_emergency': is_emergency,
            'booking_requested': booking_requested,
            'booking_confirmed': False,  # Will be updated when actually booked
            'technician_notified': False,
            'call_duration': message.get('duration'),
            'status': 'open',
            'raw_data': json.dumps(data)
        }
        
        # Save to database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO calls 
            (id, timestamp, business_id, customer_phone, customer_name, transcript,
             issue_type, is_emergency, booking_requested, booking_confirmed,
             technician_notified, call_duration, status, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            call_record['id'], call_record['timestamp'], call_record['business_id'],
            call_record['customer_phone'], call_record['customer_name'],
            call_record['transcript'], call_record['issue_type'],
            call_record['is_emergency'], call_record['booking_requested'],
            call_record['booking_confirmed'], call_record['technician_notified'],
            call_record['call_duration'], call_record['status'], call_record['raw_data']
        ))
        conn.commit()
        conn.close()
        
        print(f"✅ Call logged: {call_id}")
        print(f"   Customer: {customer_name or 'Unknown'}")
        print(f"   Emergency: {is_emergency}")
        print(f"   Booking requested: {booking_requested}")
        
        # Send alert for emergencies
        if is_emergency:
            send_emergency_alert(call_record)
            print(f"🚨 Emergency alert sent for {call_id}")
        
        return jsonify({"status": "logged", "call_id": call_id}), 200
    
    # Handle real-time transcript updates
    elif message_type == 'transcript':
        transcript = data.get('message', {}).get('transcript', '')
        print(f"📝 Live transcript: {transcript[:80]}...")
        return jsonify({"status": "received"}), 200
    
    # Default: tell Vapi to continue
    return jsonify({"status": "ok", "action": "continue"}), 200

@app.route('/webhook/twilio', methods=['POST'])
def twilio_webhook():
    """Handle Twilio SMS"""
    data = request.form.to_dict()
    
    sms_record = {
        'timestamp': datetime.now().isoformat(),
        'from_number': data.get('From'),
        'to_number': data.get('To'),
        'body': data.get('Body'),
        'direction': 'inbound'
    }
    
    # Save to database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO sms_log (timestamp, from_number, to_number, body, direction)
        VALUES (?, ?, ?, ?, ?)
    ''', (sms_record['timestamp'], sms_record['from_number'], 
          sms_record['to_number'], sms_record['body'], sms_record['direction']))
    conn.commit()
    conn.close()
    
    print(f"💬 SMS from {data.get('From')}: {data.get('Body')}")
    
    return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Thanks for your message. Our team will follow up shortly.</Message>
</Response>""", 200, {'Content-Type': 'application/xml'}

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Dashboard view - today's calls and appointments"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Today's calls
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('''
        SELECT * FROM calls 
        WHERE date(timestamp) = date('now')
        ORDER BY timestamp DESC
        LIMIT 20
    ''')
    today_calls = c.fetchall()
    
    # Pending appointments
    c.execute('''
        SELECT * FROM appointments 
        WHERE status = 'pending'
        ORDER BY created_at DESC
        LIMIT 10
    ''')
    pending_appointments = c.fetchall()
    
    # Stats
    c.execute('SELECT COUNT(*) FROM calls WHERE date(timestamp) = date("now")')
    calls_today = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM calls WHERE is_emergency = 1 AND date(timestamp) = date("now")')
    emergencies_today = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM appointments WHERE status = "pending"')
    pending_count = c.fetchone()[0]
    
    conn.close()
    
    # Simple HTML dashboard
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Revenue Rescue Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #0a0a0a; color: #e5e5e5; }
            .stats { display: flex; gap: 20px; margin-bottom: 30px; }
            .stat-box { background: #1a1a1a; padding: 20px; border-radius: 8px; flex: 1; border: 1px solid #2a2a2a; }
            .stat-number { font-size: 2em; color: #00d4ff; }
            h2 { color: #00d4ff; border-bottom: 1px solid #2a2a2a; padding-bottom: 10px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th { text-align: left; padding: 10px; background: #1a1a1a; color: #00d4ff; }
            td { padding: 10px; border-bottom: 1px solid #2a2a2a; }
            .emergency { color: #ff6b35; font-weight: bold; }
            .routine { color: #10b981; }
            .refresh { float: right; background: #00d4ff; color: #0a0a0a; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>📞 Revenue Rescue Dashboard</h1>
        <button class="refresh" onclick="location.reload()">Refresh</button>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">''' + str(calls_today) + '''</div>
                <div>Calls Today</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" style="color: #ff6b35;">''' + str(emergencies_today) + '''</div>
                <div>Emergencies</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" style="color: #f7931e;">''' + str(pending_count) + '''</div>
                <div>Pending Appointments</div>
            </div>
        </div>
        
        <h2>🚨 Recent Calls (Today)</h2>
        <table>
            <tr>
                <th>Time</th>
                <th>Customer</th>
                <th>Phone</th>
                <th>Type</th>
                <th>Booking</th>
                <th>Status</th>
            </tr>
    '''
    
    for call in today_calls:
        call_id, timestamp, business_id, phone, name, transcript, issue_type, is_emergency, booking_req, booking_conf, tech_notified, duration, status, raw = call
        time_str = timestamp.split('T')[1][:5] if 'T' in timestamp else timestamp
        type_class = 'emergency' if is_emergency else 'routine'
        type_label = '🔴 EMERGENCY' if is_emergency else '🟢 Routine'
        booking_status = '✅ Yes' if booking_req else '❌ No'
        
        html += f'''
            <tr>
                <td>{time_str}</td>
                <td>{name or 'Unknown'}</td>
                <td>{phone or 'N/A'}</td>
                <td class="{type_class}">{type_label}</td>
                <td>{booking_status}</td>
                <td>{status}</td>
            </tr>
        '''
    
    if not today_calls:
        html += '<tr><td colspan="6" style="text-align: center; padding: 20px;">No calls today yet</td></tr>'
    
    html += '''
        </table>
        
        <h2 style="margin-top: 40px;">📅 Pending Appointments</h2>
    '''
    
    if pending_appointments:
        html += '''
        <table>
            <tr>
                <th>Customer</th>
                <th>Phone</th>
                <th>Address</th>
                <th>Issue</th>
                <th>Date/Time</th>
            </tr>
        '''
        for appt in pending_appointments:
            html += f'''
                <tr>
                    <td>{appt[2] or 'Unknown'}</td>
                    <td>{appt[3] or 'N/A'}</td>
                    <td>{appt[4] or 'N/A'}</td>
                    <td>{appt[5] or 'N/A'}</td>
                    <td>{appt[6] or 'TBD'} {appt[7] or ''}</td>
                </tr>
            '''
        html += '</table>'
    else:
        html += '<p style="text-align: center; padding: 20px;">No pending appointments</p>'
    
    html += '''
    </body>
    </html>
    '''
    
    return html

@app.route('/api/calls', methods=['GET'])
def api_calls():
    """API endpoint to get all calls"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM calls ORDER BY timestamp DESC LIMIT 100')
    calls = c.fetchall()
    conn.close()
    
    return jsonify([{
        'id': c[0],
        'timestamp': c[1],
        'customer_name': c[4],
        'customer_phone': c[3],
        'issue_type': c[6],
        'is_emergency': c[7],
        'booking_requested': c[8],
        'status': c[12]
    } for c in calls])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)