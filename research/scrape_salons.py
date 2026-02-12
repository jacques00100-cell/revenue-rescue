#!/usr/bin/env python3
"""
Google Maps Places API (New) Salon Lead Generator for Dallas-Fort Worth
Targets 200 operational salon leads with contact info and ratings
Uses the new Places API endpoints
"""

import requests
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

API_KEY = "AIzaSyBxlFDdKEz0zOZuLrEZgBKHl6aH2XBerBk"

# Places API (New) endpoint
SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
DETAILS_URL = "https://places.googleapis.com/v1/places"

SEARCH_QUERIES = [
    "hair salon Dallas TX",
    "beauty salon Fort Worth TX",
    "nail salon Plano TX",
    "spa Arlington TX",
    "barber shop Frisco TX",
    "hair salon Plano TX",
    "nail salon Dallas TX",
    "beauty salon Plano TX",
    "spa Dallas TX",
    "barber shop Dallas TX",
    "hair salon Arlington TX",
    "nail salon Fort Worth TX",
    "beauty salon Frisco TX",
    "spa Plano TX",
    "barber shop Arlington TX",
    "hair salon Frisco TX",
    "nail salon Arlington TX",
    "beauty salon Arlington TX",
    "spa Fort Worth TX",
    "barber shop Plano TX",
    "hair salon Irving TX",
    "nail salon Frisco TX",
    "beauty salon Dallas TX",
    "spa Frisco TX",
    "barber shop Fort Worth TX",
]

@dataclass
class SalonLead:
    company_name: str
    phone: Optional[str]
    website: Optional[str]
    address: str
    rating: Optional[float]
    business_status: str
    priority: str
    place_id: str
    query_source: str

class SalonLeadScraper:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.leads: List[SalonLead] = []
        self.seen_place_ids = set()
        self.headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.rating,places.businessStatus,nextPageToken"
        }
    
    def search_places(self, query: str, page_token: Optional[str] = None) -> Dict:
        """Search for places using Places API (New)"""
        payload = {
            "textQuery": query,
            "pageSize": 20
        }
        if page_token:
            payload["pageToken"] = page_token
        
        try:
            response = requests.post(SEARCH_URL, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error searching for '{query}': {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text[:500]}")
            return {"places": []}
    
    def get_place_details(self, place_id: str) -> Dict:
        """Get detailed information about a place"""
        url = f"{DETAILS_URL}/{place_id}"
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "id,displayName,nationalPhoneNumber,websiteUri,formattedAddress,rating,businessStatus"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting details for {place_id}: {e}")
            return {}
    
    def determine_priority(self, rating: Optional[float]) -> str:
        """Determine priority based on rating"""
        if rating is None:
            return "low"
        if rating >= 4.8:
            return "high"
        elif rating >= 4.5:
            return "medium"
        else:
            return "low"
    
    def process_place(self, place: Dict, query: str) -> Optional[SalonLead]:
        """Process a place result into a SalonLead"""
        place_id = place.get("id")
        
        if not place_id or place_id in self.seen_place_ids:
            return None
        
        # Extract fields from the place data
        business_status = place.get("businessStatus", "OPERATIONAL")
        if business_status != "OPERATIONAL":
            return None
        
        # Handle displayName which can be a string or object
        name_data = place.get("displayName", {})
        if isinstance(name_data, dict):
            name = name_data.get("text", "Unknown")
        else:
            name = str(name_data) if name_data else "Unknown"
        
        phone = place.get("nationalPhoneNumber")
        website = place.get("websiteUri")
        address = place.get("formattedAddress", "Unknown")
        rating = place.get("rating")
        
        # Convert rating to float if it's a number
        if rating is not None:
            try:
                rating = float(rating)
            except (TypeError, ValueError):
                rating = None
        
        priority = self.determine_priority(rating)
        
        lead = SalonLead(
            company_name=name,
            phone=phone,
            website=website,
            address=address,
            rating=rating,
            business_status=business_status,
            priority=priority,
            place_id=place_id,
            query_source=query
        )
        
        self.seen_place_ids.add(place_id)
        return lead
    
    def search_all_pages(self, query: str) -> List[SalonLead]:
        """Search all pages for a query"""
        leads = []
        page_token = None
        pages = 0
        
        while pages < 3:  # Max 3 pages per query
            result = self.search_places(query, page_token)
            
            places = result.get("places", [])
            if not places:
                error_msg = result.get("error", {}).get("message", "")
                if error_msg:
                    print(f"   API Error: {error_msg[:100]}")
                break
            
            for place in places:
                lead = self.process_place(place, query)
                if lead:
                    leads.append(lead)
            
            page_token = result.get("nextPageToken")
            if not page_token:
                break
            
            # Delay between page requests
            time.sleep(2)
            pages += 1
        
        return leads
    
    def scrape(self, target: int = 200) -> List[SalonLead]:
        """Main scraping function"""
        print(f"🎯 Target: {target} salon leads")
        print(f"📍 Region: Dallas-Fort Worth")
        print(f"🔑 Using Places API (New)")
        print("=" * 60)
        
        for i, query in enumerate(SEARCH_QUERIES, 1):
            if len(self.leads) >= target:
                break
            
            print(f"\n🔍 [{i}/{len(SEARCH_QUERIES)}] Searching: '{query}'")
            new_leads = self.search_all_pages(query)
            self.leads.extend(new_leads)
            
            print(f"   ✓ Found {len(new_leads)} new leads (Total: {len(self.leads)})")
            
            # Progress report every 50 leads
            prev_count = len(self.leads) - len(new_leads)
            if len(self.leads) >= 50 and prev_count < 50:
                print(f"\n🎉 PROGRESS MILESTONE: 50+ leads collected!")
            if len(self.leads) >= 100 and prev_count < 100:
                print(f"\n🎉 PROGRESS MILESTONE: 100+ leads collected!")
            if len(self.leads) >= 150 and prev_count < 150:
                print(f"\n🎉 PROGRESS MILESTONE: 150+ leads collected!")
            if len(self.leads) >= 200 and prev_count < 200:
                print(f"\n🎉 PROGRESS MILESTONE: 200+ leads collected!")
            
            # Rate limiting between queries
            time.sleep(0.5)
        
        return self.leads
    
    def save_results(self, filepath: str):
        """Save results to JSON file"""
        data = {
            "total_leads": len(self.leads),
            "region": "Dallas-Fort Worth",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "leads": [asdict(lead) for lead in self.leads]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved {len(self.leads)} leads to: {filepath}")
    
    def print_stats(self):
        """Print statistics about collected leads"""
        if not self.leads:
            print("\n⚠️  No leads collected.")
            return
            
        high = sum(1 for l in self.leads if l.priority == "high")
        medium = sum(1 for l in self.leads if l.priority == "medium")
        low = sum(1 for l in self.leads if l.priority == "low")
        
        with_phone = sum(1 for l in self.leads if l.phone)
        with_website = sum(1 for l in self.leads if l.website)
        
        print("\n" + "=" * 60)
        print("📈 COLLECTION STATISTICS")
        print("=" * 60)
        print(f"Total Leads: {len(self.leads)}")
        print(f"\nPriority Breakdown:")
        print(f"  🔥 High (4.8+):   {high}")
        print(f"  ⚡ Medium (4.5+): {medium}")
        print(f"  📌 Low (<4.5):    {low}")
        print(f"\nContact Info:")
        print(f"  📞 With Phone:    {with_phone} ({with_phone/len(self.leads)*100:.1f}%)")
        print(f"  🌐 With Website:  {with_website} ({with_website/len(self.leads)*100:.1f}%)")

if __name__ == "__main__":
    scraper = SalonLeadScraper(API_KEY)
    scraper.scrape(target=200)
    scraper.save_results("/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/salon-leads-dfw.json")
    scraper.print_stats()
