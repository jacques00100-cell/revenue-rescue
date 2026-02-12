#!/usr/bin/env python3
"""
Vapi Assistant Flow Test Script
Tests the AI phone assistant conversation flow to ensure proper responsiveness
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
WEBHOOK_URL = "http://localhost:8080/webhook/vapi"
TIMEOUT = 10

class VapiFlowTester:
    def __init__(self):
        self.results = []
        self.call_id = f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def log(self, test_name, passed, details=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"      {details}")
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    def test_webhook_response(self):
        """Test that webhook returns proper JSON response"""
        print("\n🧪 Testing webhook response...")
        
        test_payload = {
            "call": {"id": self.call_id},
            "message": {
                "type": "transcript",
                "transcript": "Hello, my name is John"
            }
        }
        
        try:
            response = requests.post(
                WEBHOOK_URL,
                json=test_payload,
                timeout=TIMEOUT
            )
            
            # Check status code
            if response.status_code != 200:
                self.log("Webhook Status Code", False, f"Expected 200, got {response.status_code}")
                return
            
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' not in content_type:
                self.log("Webhook Content-Type", False, f"Expected JSON, got {content_type}")
                return
            
            # Check response body is valid JSON
            try:
                data = response.json()
                if 'status' in data and data.get('action') == 'continue':
                    self.log("Webhook Response Format", True, "Proper JSON with continue action")
                else:
                    self.log("Webhook Response Format", False, f"Missing required fields: {data}")
            except json.JSONDecodeError:
                self.log("Webhook Response Format", False, "Response is not valid JSON")
                
        except requests.exceptions.ConnectionError:
            self.log("Webhook Connection", False, f"Cannot connect to {WEBHOOK_URL}. Is the server running?")
        except Exception as e:
            self.log("Webhook Test", False, str(e))
    
    def test_end_of_call_logging(self):
        """Test that end-of-call reports are handled"""
        print("\n🧪 Testing end-of-call report handling...")
        
        test_payload = {
            "call": {
                "id": self.call_id,
                "duration": 120
            },
            "message": {
                "type": "end-of-call-report",
                "duration": 120,
                "summary": "Test call completed"
            }
        }
        
        try:
            response = requests.post(
                WEBHOOK_URL,
                json=test_payload,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'logged':
                    self.log("End-of-Call Logging", True, "Call report logged successfully")
                else:
                    self.log("End-of-Call Logging", False, "Unexpected response format")
            else:
                self.log("End-of-Call Logging", False, f"Status {response.status_code}")
                
        except Exception as e:
            self.log("End-of-Call Test", False, str(e))
    
    def test_config_validity(self):
        """Test that config files are valid JSON with required fields"""
        print("\n🧪 Testing configuration files...")
        
        configs = [
            ("config/vapi-assistant.json", "Original Config"),
            ("config/vapi-assistant-fixed.json", "Fixed Config")
        ]
        
        for path, name in configs:
            try:
                with open(path, 'r') as f:
                    config = json.load(f)
                
                # Check required fields
                required = ['name', 'model', 'voice', 'silenceTimeoutSeconds']
                missing = [f for f in required if f not in config]
                
                if missing:
                    self.log(f"{name} Structure", False, f"Missing fields: {missing}")
                else:
                    timeout = config.get('silenceTimeoutSeconds')
                    end_call_enabled = config.get('endCallFunctionEnabled')
                    phrases = config.get('endCallPhrases', [])
                    
                    details = f"timeout={timeout}s, endCall={end_call_enabled}, phrases={len(phrases)}"
                    self.log(f"{name} Structure", True, details)
                    
            except FileNotFoundError:
                self.log(f"{name} File", False, f"File not found: {path}")
            except json.JSONDecodeError as e:
                self.log(f"{name} JSON", False, f"Invalid JSON: {e}")
    
    def test_conversation_flow(self):
        """Test simulated conversation flow"""
        print("\n🧪 Testing conversation flow simulation...")
        
        # Read the fixed config
        try:
            with open("config/vapi-assistant-fixed.json", 'r') as f:
                config = json.load(f)
            
            system_prompt = config['model']['systemPrompt']
            
            # Check for key flow elements
            checks = [
                ("Name collection first", "May I have your name" in system_prompt),
                ("Wait for response instruction", "WAIT" in system_prompt or "wait" in system_prompt.lower()),
                ("Confirm phone number", "confirm" in system_prompt.lower() and "phone" in system_prompt.lower()),
                ("Confirm address", "confirm" in system_prompt.lower() and "address" in system_prompt.lower()),
                ("Emergency detection", "emergency" in system_prompt.lower()),
                ("Graceful ending", "anything else" in system_prompt.lower()),
            ]
            
            for check_name, passed in checks:
                self.log(f"Flow: {check_name}", passed)
            
            # Check silence timeout is reasonable
            timeout = config.get('silenceTimeoutSeconds', 0)
            if timeout >= 45:
                self.log("Silence Timeout", True, f"{timeout}s (good for hesitant callers)")
            else:
                self.log("Silence Timeout", False, f"{timeout}s (too short, should be 45s+)")
            
            # Check end call is disabled
            if not config.get('endCallFunctionEnabled'):
                self.log("End Call Function", True, "Disabled (prevents abrupt hangup)")
            else:
                self.log("End Call Function", False, "Enabled (may cause abrupt hangup)")
            
            # Check response delay
            delay = config.get('responseDelaySeconds', 0)
            if delay >= 1.0:
                self.log("Response Delay", True, f"{delay}s (gives caller time)")
            else:
                self.log("Response Delay", False, f"{delay}s (too fast, should be 1.0s+)")
                
        except Exception as e:
            self.log("Conversation Flow Test", False, str(e))
    
    def generate_report(self):
        """Generate final test report"""
        print("\n" + "="*60)
        print("📊 VAPI ASSISTANT TEST REPORT")
        print("="*60)
        
        passed = sum(1 for r in self.results if r['passed'])
        total = len(self.results)
        
        print(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed! The assistant should be responsive.")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Review issues above.")
            print("\nCommon fixes:")
            print("  - Make sure Flask server is running: python app.py")
            print("  - Check that vapi-assistant-fixed.json is uploaded to Vapi dashboard")
            print("  - Verify webhook URL is set in Vapi assistant settings")
        
        print("\n" + "="*60)
        
        return passed == total

def main():
    print("🚀 Vapi Assistant Flow Tester")
    print("Testing AI phone assistant responsiveness...")
    
    tester = VapiFlowTester()
    
    # Run all tests
    tester.test_config_validity()
    tester.test_conversation_flow()
    tester.test_webhook_response()
    tester.test_end_of_call_logging()
    
    # Generate report
    success = tester.generate_report()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
