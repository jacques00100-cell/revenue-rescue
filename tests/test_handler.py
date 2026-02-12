#!/usr/bin/env python3
"""
Test Revenue Rescue Receptionist
"""

import sys
sys.path.insert(0, '/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/src')

from call_handler import RevenueRescueHandler, SAMPLE_COMPANY
import json

def test_emergency_call():
    """Test emergency call handling"""
    
    print("\n" + "="*70)
    print("🚨 TEST: Emergency Call")
    print("="*70)
    
    handler = RevenueRescueHandler(SAMPLE_COMPANY)
    
    test_call = {
        'id': 'test-emergency-001',
        'customer': {'number': '+1-555-123-4567'},
        'transcript': 'Hi, my AC just stopped working and it is 95 degrees outside. I have a baby in the house. I need someone to come fix it tonight.',
        'recordingUrl': 'https://example.com/recording1.mp3',
        'analysis': {
            'extractedInformation': {
                'name': 'Sarah Johnson',
                'address': '456 Oak Ave, Dallas, TX',
                'intent': 'emergency',
                'issue': 'AC stopped working, 95 degrees, baby in house'
            }
        }
    }
    
    result = handler.handle_incoming_call(test_call)
    
    print(f"\n✅ Call processed successfully")
    print(f"   Intent: {result['intent']}")
    print(f"   Status: {result['status']}")
    print(f"   Action: {result['action_taken']}")
    print(f"   On-call tech notified: {result.get('tech_notified', False)}")
    
    return result


def test_routine_call():
    """Test routine call handling"""
    
    print("\n" + "="*70)
    print("📅 TEST: Routine Call")
    print("="*70)
    
    handler = RevenueRescueHandler(SAMPLE_COMPANY)
    
    test_call = {
        'id': 'test-routine-001',
        'customer': {'number': '+1-555-987-6543'},
        'transcript': 'Hi, I would like to schedule my annual AC maintenance check. I am flexible on timing, maybe next week?',
        'recordingUrl': 'https://example.com/recording2.mp3',
        'analysis': {
            'extractedInformation': {
                'name': 'Mike Chen',
                'address': '789 Pine St, Dallas, TX',
                'intent': 'routine',
                'issue': 'Annual AC maintenance'
            }
        }
    }
    
    result = handler.handle_incoming_call(test_call)
    
    print(f"\n✅ Call processed successfully")
    print(f"   Intent: {result['intent']}")
    print(f"   Status: {result['status']}")
    print(f"   Action: {result['action_taken']}")
    
    return result


def test_unknown_call():
    """Test unclear intent handling"""
    
    print("\n" + "="*70)
    print("❓ TEST: Unknown Intent")
    print("="*70)
    
    handler = RevenueRescueHandler(SAMPLE_COMPANY)
    
    test_call = {
        'id': 'test-unknown-001',
        'customer': {'number': '+1-555-555-5555'},
        'transcript': 'I am not sure, my system is making a weird noise but it still works. Should I be worried?',
        'recordingUrl': 'https://example.com/recording3.mp3',
        'analysis': {
            'extractedInformation': {
                'name': 'Unknown Caller',
                'address': '321 Elm St, Dallas, TX',
                'intent': 'unknown',
                'issue': 'Weird noise from system'
            }
        }
    }
    
    result = handler.handle_incoming_call(test_call)
    
    print(f"\n✅ Call processed successfully")
    print(f"   Intent: {result['intent']}")
    print(f"   Status: {result['status']}")
    print(f"   Action: {result['action_taken']}")
    
    return result


def run_all_tests():
    """Run all tests"""
    
    print("\n" + "="*70)
    print("🧪 REVENUE RESCUE — TEST SUITE")
    print("="*70)
    
    results = []
    
    try:
        results.append(test_emergency_call())
        results.append(test_routine_call())
        results.append(test_unknown_call())
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print(f"\nTotal calls processed: {len(results)}")
        print(f"Emergencies: {len([r for r in results if r['intent'] == 'emergency'])}")
        print(f"Routines: {len([r for r in results if r['intent'] == 'routine'])}")
        print(f"Escalated: {len([r for r in results if 'escalated' in r['status']])}")
        
        print("\n📊 Call records saved to: /tmp/revenue-rescue-calls.jsonl")
        print("📊 Server logs: /tmp/revenue-rescue.log")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
