#!/usr/bin/env python3
"""
Revenue Rescue Receptionist - Webhook Server
Receives calls from Vapi.ai and routes to handler
"""

import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from call_handler import RevenueRescueHandler

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('/tmp/revenue-rescue-server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Company configs (load from file in production)
COMPANIES = {
    'cool-air-hvac': {
        'company_id': 'cool-air-hvac',
        'name': 'Cool Air HVAC',
        'phone': '+1-555-HVAC',
        'on_call_phone': '+1-555-TECH-01',
        'owner_email': 'owner@coolairhvac.com',
        'office_manager_email': 'dispatch@coolairhvac.com',
        'timezone': 'America/Chicago'
    }
}


class WebhookHandler(BaseHTTPRequestHandler):
    """Handle incoming webhooks from Vapi.ai"""
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")
    
    def do_POST(self):
        """Handle POST requests"""
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Get request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request")
            self._send_error(400, "Invalid JSON")
            return
        
        # Route based on path
        if path == '/webhook/vapi':
            self._handle_vapi_webhook(data)
        elif path == '/webhook/twilio':
            self._handle_twilio_webhook(data)
        else:
            self._send_error(404, "Unknown endpoint")
    
    def do_GET(self):
        """Handle GET requests (health check)"""
        
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/health':
            self._send_json({'status': 'healthy', 'service': 'revenue-rescue'})
        else:
            self._send_error(404, "Not found")
    
    def _handle_vapi_webhook(self, data: dict):
        """Process Vapi.ai call webhook"""
        
        logger.info("📞 Received Vapi webhook")
        
        # Determine which company this is for
        # (In production, use phone number to route)
        company_id = 'cool-air-hvac'  # Default for MVP
        
        if company_id not in COMPANIES:
            logger.error(f"Unknown company: {company_id}")
            self._send_error(404, "Company not found")
            return
        
        company_config = COMPANIES[company_id]
        
        # Process the call
        handler = RevenueRescueHandler(company_config)
        result = handler.handle_incoming_call(data)
        
        # Send success response
        self._send_json({
            'status': 'success',
            'call_id': result.get('call_id'),
            'action': result.get('action_taken')
        })
        
        logger.info(f"✅ Call processed: {result.get('call_id')}")
    
    def _handle_twilio_webhook(self, data: dict):
        """Process Twilio SMS webhook"""
        
        logger.info("📱 Received Twilio webhook")
        
        # Handle SMS replies (CONFIRM, CANCEL, etc.)
        from_number = data.get('From', '')
        body = data.get('Body', '').upper().strip()
        
        if 'CONFIRM' in body:
            logger.info(f"✅ Appointment confirmed by {from_number}")
            # TODO: Update appointment status
            
        elif 'CANCEL' in body:
            logger.info(f"❌ Cancellation requested by {from_number}")
            # TODO: Handle cancellation
            
        else:
            logger.info(f"💬 SMS reply from {from_number}: {body}")
        
        self._send_json({'status': 'received'})
    
    def _send_json(self, data: dict, status_code: int = 200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def _send_error(self, status_code: int, message: str):
        """Send error response"""
        self._send_json({'error': message}, status_code)


def run_server(port: int = 8080):
    """Start the webhook server"""
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, WebhookHandler)
    
    logger.info(f"🚀 Revenue Rescue Server starting on port {port}")
    logger.info(f"📞 Vapi webhook: http://localhost:{port}/webhook/vapi")
    logger.info(f"📱 Twilio webhook: http://localhost:{port}/webhook/twilio")
    logger.info(f"🏥 Health check: http://localhost:{port}/health")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n👋 Server shutting down")
        httpd.shutdown()


if __name__ == "__main__":
    import sys
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
