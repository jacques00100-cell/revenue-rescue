#!/usr/bin/env python3
"""
Revenue Rescue Receptionist - Simple Dashboard
View call logs, metrics, and company status
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

class Dashboard:
    """Simple CLI dashboard for Revenue Rescue"""
    
    def __init__(self):
        self.calls_db = Path('/tmp/revenue-rescue-calls.jsonl')
        self.companies_config = Path(__file__).parent.parent / 'config' / 'companies.json'
    
    def load_calls(self, days: int = 7) -> List[Dict[str, Any]]:
        """Load calls from database"""
        
        calls = []
        cutoff = datetime.now() - timedelta(days=days)
        
        if not self.calls_db.exists():
            return calls
        
        with open(self.calls_db, 'r') as f:
            for line in f:
                try:
                    call = json.loads(line.strip())
                    call_time = datetime.fromisoformat(call['timestamp'].replace('Z', '+00:00'))
                    if call_time > cutoff:
                        calls.append(call)
                except:
                    continue
        
        return calls
    
    def show_dashboard(self):
        """Display dashboard"""
        
        print("\n" + "="*70)
        print("💰 REVENUE RESCUE RECEPTIONIST — Dashboard")
        print("="*70)
        
        # Load data
        calls = self.load_calls(days=7)
        
        # Summary stats
        print("\n📊 LAST 7 DAYS")
        print("-"*70)
        
        total_calls = len(calls)
        emergencies = len([c for c in calls if c.get('intent') == 'emergency'])
        routines = len([c for c in calls if c.get('intent') == 'routine'])
        appointments = len([c for c in calls if 'appointment_booked' in c.get('status', '')])
        
        print(f"Total Calls:        {total_calls:>5}")
        print(f"Emergencies:        {emergencies:>5}")
        print(f"Routine Calls:      {routines:>5}")
        print(f"Appointments Booked: {appointments:>5}")
        
        if total_calls > 0:
            conversion_rate = (appointments / total_calls) * 100
            print(f"Conversion Rate:    {conversion_rate:>5.1f}%")
        
        # Recent calls
        print("\n📞 RECENT CALLS")
        print("-"*70)
        
        recent = sorted(calls, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
        
        if not recent:
            print("No calls yet. System ready.")
        else:
            for call in recent:
                time = call.get('timestamp', 'Unknown')[:16]
                name = call.get('caller_name', 'Unknown')[:15]
                intent = call.get('intent', 'unknown')[:10]
                status = call.get('status', 'unknown')[:20]
                
                emoji = "🚨" if intent == "emergency" else "📅" if intent == "routine" else "❓"
                print(f"{emoji} {time} | {name:<15} | {intent:<10} | {status}")
        
        # Company status
        print("\n🏢 COMPANY STATUS")
        print("-"*70)
        print("🟢 Cool Air HVAC — Active ($199/month)")
        print("   Status: Ready to receive calls")
        print("   On-call: +1-555-TECH-01")
        
        print("\n" + "="*70)
    
    def show_call_detail(self, call_id: str):
        """Show detailed info for a specific call"""
        
        calls = self.load_calls(days=30)
        
        for call in calls:
            if call.get('call_id') == call_id:
                print("\n" + "="*70)
                print(f"📞 CALL DETAIL: {call_id}")
                print("="*70)
                print(json.dumps(call, indent=2))
                print("="*70)
                return
        
        print(f"❌ Call not found: {call_id}")


def main():
    """Run dashboard"""
    import sys
    
    dashboard = Dashboard()
    
    if len(sys.argv) > 1:
        # Show specific call
        dashboard.show_call_detail(sys.argv[1])
    else:
        # Show main dashboard
        dashboard.show_dashboard()


if __name__ == "__main__":
    main()
