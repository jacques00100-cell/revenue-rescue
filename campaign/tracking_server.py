#!/usr/bin/env python3
"""
Tracking Server for Email Campaign
Handles open pixels, click tracking, and webhook endpoints
"""

from flask import Flask, request, redirect, send_file, Response
import sqlite3
import yaml
import base64
from pathlib import Path
from datetime import datetime
from urllib.parse import unquote

app = Flask(__name__)

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config.yaml"
with open(CONFIG_PATH) as f:
    CONFIG = yaml.safe_load(f)

DB_PATH = Path(__file__).parent / CONFIG['database']['path']

# 1x1 transparent GIF for tracking pixel
PIXEL_GIF = base64.b64decode(
    'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
)


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def log_event(campaign_id: str, event_type: str, email_number: int = None):
    """Log tracking event to database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Log event
        cursor.execute('''
            INSERT INTO tracking_events (campaign_id, event_type, email_number, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            campaign_id,
            event_type,
            email_number,
            request.remote_addr,
            request.headers.get('User-Agent', '')[:500]
        ))
        
        # Update campaign stats
        if event_type == 'open' and email_number:
            column = f"email_{email_number}_opened"
            time_col = f"email_{email_number}_opened_at"
            cursor.execute(f'''
                UPDATE campaigns 
                SET {column} = 1, {time_col} = datetime('now')
                WHERE id = ? AND {column} = 0
            ''', (campaign_id,))
            
        elif event_type == 'click' and email_number:
            column = f"email_{email_number}_clicked"
            time_col = f"email_{email_number}_clicked_at"
            cursor.execute(f'''
                UPDATE campaigns 
                SET {column} = 1, {time_col} = datetime('now')
                WHERE id = ?
            ''', (campaign_id,))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error logging event: {e}")


@app.route('/track/open/<campaign_id>/<int:email_number>')
def track_open(campaign_id, email_number):
    """Track email open via 1x1 pixel"""
    log_event(campaign_id, 'open', email_number)
    
    # Return transparent GIF
    response = Response(PIXEL_GIF, mimetype='image/gif')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/track/click/<campaign_id>/<int:email_number>')
def track_click(campaign_id, email_number):
    """Track link click and redirect to destination"""
    destination = request.args.get('url', 'https://pac-holding.com')
    
    log_event(campaign_id, 'click', email_number)
    
    return redirect(unquote(destination))


@app.route('/unsubscribe/<campaign_id>')
def unsubscribe(campaign_id):
    """Handle unsubscribe requests"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE campaigns 
            SET status = 'unsubscribed', updated_at = datetime('now')
            WHERE id = ?
        ''', (campaign_id,))
        
        conn.commit()
        conn.close()
        
        log_event(campaign_id, 'unsubscribe')
        
        return """
        <html>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1>✓ Unsubscribed</h1>
            <p>You've been successfully unsubscribed from our emails.</p>
            <p>Sorry to see you go!</p>
        </body>
        </html>
        """
        
    except Exception as e:
        return f"Error: {e}", 500


@app.route('/view/<campaign_id>/<int:email_number>')
def view_in_browser(campaign_id, email_number):
    """Show email in browser"""
    template_map = {
        1: 'email_templates/email_1_cold_intro.html',
        2: 'email_templates/email_2_followup.html',
        3: 'email_templates/email_3_final.html'
    }
    
    template_path = Path(__file__).parent / template_map.get(email_number, template_map[1])
    
    try:
        with open(template_path) as f:
            content = f.read()
        return content
    except:
        return "Email not found", 404


@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard stats"""
    try:
        conn = get_db_connection()
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
                SUM(CASE WHEN sentiment_label = 'not_now' THEN 1 ELSE 0 END) as not_now,
                SUM(CASE WHEN sentiment_label = 'not_interested' THEN 1 ELSE 0 END) as not_interested,
                SUM(CASE WHEN status = 'unsubscribed' THEN 1 ELSE 0 END) as unsubscribed,
                SUM(CASE WHEN status = 'converted' THEN 1 ELSE 0 END) as converted
            FROM campaigns
        ''')
        
        row = cursor.fetchone()
        stats = {
            'total_leads': row[0] or 0,
            'email_1': {'sent': row[1] or 0, 'opened': row[2] or 0, 'clicked': row[3] or 0},
            'email_2': {'sent': row[4] or 0, 'opened': row[5] or 0, 'clicked': row[6] or 0},
            'email_3': {'sent': row[7] or 0, 'opened': row[8] or 0, 'clicked': row[9] or 0},
            'sentiment': {
                'interested': row[10] or 0,
                'not_now': row[11] or 0,
                'not_interested': row[12] or 0
            },
            'status': {
                'unsubscribed': row[13] or 0,
                'converted': row[14] or 0
            }
        }
        
        # Top performing leads
        cursor.execute('''
            SELECT lead_name, business_name, sentiment_score, sentiment_label
            FROM campaigns
            WHERE sentiment_score > 0.5
            ORDER BY sentiment_score DESC
            LIMIT 10
        ''')
        
        top_leads = []
        for row in cursor.fetchall():
            top_leads.append({
                'name': row[0],
                'business': row[1],
                'score': row[2],
                'label': row[3]
            })
        
        stats['top_leads'] = top_leads
        
        conn.close()
        
        return stats
        
    except Exception as e:
        return {'error': str(e)}, 500


@app.route('/api/leads')
def api_leads():
    """API endpoint for lead data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, lead_name, business_name, city, industry,
                   email_1_sent_at, email_1_opened, email_1_clicked,
                   sentiment_label, sentiment_score, status
            FROM campaigns
            ORDER BY priority_score DESC, created_at DESC
            LIMIT 100
        ''')
        
        leads = []
        for row in cursor.fetchall():
            leads.append({
                'id': row[0],
                'name': row[1],
                'business': row[2],
                'city': row[3],
                'industry': row[4],
                'email_1_sent': bool(row[5]),
                'email_1_opened': bool(row[6]),
                'email_1_clicked': bool(row[7]),
                'sentiment': row[8],
                'score': row[9],
                'status': row[10]
            })
        
        conn.close()
        return {'leads': leads}
        
    except Exception as e:
        return {'error': str(e)}, 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'ok', 'timestamp': datetime.now().isoformat()}


if __name__ == '__main__':
    port = CONFIG['tracking']['server_port']
    print(f"Starting tracking server on port {port}...")
    print(f"Tracking URL: {CONFIG['tracking']['base_url']}")
    app.run(host='0.0.0.0', port=port, debug=False)
