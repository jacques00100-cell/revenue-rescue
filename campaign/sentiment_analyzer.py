#!/usr/bin/env python3
"""
Sentiment Analyzer for Email Replies
Uses OpenAI to classify reply sentiment and extract buying signals
"""

import sqlite3
import yaml
import json
from pathlib import Path
from typing import Dict, Optional
import requests

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config.yaml"
with open(CONFIG_PATH) as f:
    CONFIG = yaml.safe_load(f)

DB_PATH = Path(__file__).parent / CONFIG['database']['path']


def analyze_sentiment(reply_text: str, subject: str = "") -> Dict:
    """
    Analyze email reply sentiment using OpenAI
    Returns: {
        'sentiment_label': str,
        'sentiment_score': float,
        'buying_signal': int,
        'urgency': str,
        'summary': str
    }
    """
    
    system_prompt = """You are an expert sales assistant analyzing email replies from potential customers.
    
Classify the reply into exactly one of these categories:
- "interested": Wants demo, asks about pricing, ready to book, positive response
- "not_now": Good fit but bad timing, will consider later, busy currently
- "not_interested": Rejection, wrong fit, already have solution
- "unsubscribe": Wants to be removed, requests no contact
- "question": Has specific questions but not yet committed
- "neutral": Unclear, needs clarification, autoresponder

Also extract:
- buying_signal: 0-10 (10 = very likely to buy)
- urgency: "low", "medium", or "high"
- brief_summary: One sentence summary of reply

Respond ONLY in valid JSON format:
{
  "sentiment_label": "string",
  "sentiment_score": float (-1.0 to 1.0),
  "buying_signal": int (0-10),
  "urgency": "string",
  "summary": "string"
}"""

    user_prompt = f"Subject: {subject}\n\nReply:\n{reply_text}"
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {CONFIG['openai']['api_key']}",
                "Content-Type": "application/json"
            },
            json={
                "model": CONFIG['openai']['model'],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 300
            }
        )
        
        if response.status_code != 200:
            print(f"OpenAI API error: {response.text}")
            return {
                'sentiment_label': 'neutral',
                'sentiment_score': 0.0,
                'buying_signal': 5,
                'urgency': 'low',
                'summary': 'API error - manual review needed'
            }
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Parse JSON response
        analysis = json.loads(content)
        
        # Validate and normalize
        valid_labels = ['interested', 'not_now', 'not_interested', 'unsubscribe', 'question', 'neutral']
        if analysis.get('sentiment_label') not in valid_labels:
            analysis['sentiment_label'] = 'neutral'
        
        analysis['sentiment_score'] = max(-1.0, min(1.0, float(analysis.get('sentiment_score', 0))))
        analysis['buying_signal'] = max(0, min(10, int(analysis.get('buying_signal', 5))))
        
        valid_urgency = ['low', 'medium', 'high']
        if analysis.get('urgency') not in valid_urgency:
            analysis['urgency'] = 'low'
        
        return analysis
        
    except Exception as e:
        print(f"Analysis error: {e}")
        return {
            'sentiment_label': 'neutral',
            'sentiment_score': 0.0,
            'buying_signal': 5,
            'urgency': 'low',
            'summary': 'Analysis failed - manual review needed'
        }


def update_campaign_sentiment(campaign_id: str, reply_content: str, subject: str = ""):
    """Update database with sentiment analysis"""
    
    analysis = analyze_sentiment(reply_content, subject)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE campaigns 
        SET sentiment_label = ?,
            sentiment_score = ?,
            reply_content = ?,
            updated_at = datetime('now')
        WHERE id = ?
    ''', (
        analysis['sentiment_label'],
        analysis['sentiment_score'],
        reply_content,
        campaign_id
    ))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Updated sentiment for {campaign_id}: {analysis['sentiment_label']} (signal: {analysis['buying_signal']}/10)")
    
    return analysis


def get_high_priority_leads(min_signal: int = 7) -> list:
    """Get leads with high buying signals for immediate follow-up"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, lead_email, lead_name, business_name, sentiment_label, sentiment_score
        FROM campaigns
        WHERE sentiment_score >= ?
        OR sentiment_label IN ('interested', 'question')
        ORDER BY sentiment_score DESC
    ''', (min_signal / 10,))  # Convert 0-10 scale to -1 to 1 scale
    
    leads = cursor.fetchall()
    conn.close()
    
    return leads


def process_reply(campaign_id: str, from_email: str, subject: str, body: str):
    """Process an incoming email reply"""
    
    print(f"\n📨 Processing reply from: {from_email}")
    print(f"   Subject: {subject}")
    
    # Analyze sentiment
    analysis = update_campaign_sentiment(campaign_id, body, subject)
    
    # Check for unsubscribe
    if analysis['sentiment_label'] == 'unsubscribe':
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE campaigns SET status = 'unsubscribed' WHERE id = ?", (campaign_id,))
        conn.commit()
        conn.close()
        print(f"   ⚠️ Lead {campaign_id} marked as unsubscribed")
    
    # Check for conversion
    if analysis['sentiment_label'] == 'interested' and analysis['buying_signal'] >= 8:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE campaigns SET status = 'converted' WHERE id = ?", (campaign_id,))
        conn.commit()
        conn.close()
        print(f"   🎯 Lead {campaign_id} marked as converted!")
    
    return analysis


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test sentiment analysis
        test_replies = [
            "This sounds great! Can we schedule a demo next Tuesday?",
            "Not interested right now, maybe in a few months",
            "Please remove me from your list",
            "How much does this cost? I'm currently using Calendly",
            "We're all set with our current system, thanks"
        ]
        
        print("Testing sentiment analyzer...\n")
        for reply in test_replies:
            print(f"Reply: {reply}")
            result = analyze_sentiment(reply)
            print(f"  → Label: {result['sentiment_label']}, Signal: {result['buying_signal']}/10, Urgency: {result['urgency']}")
            print(f"  → Summary: {result['summary']}\n")
    
    else:
        print("Usage: python sentiment_analyzer.py --test")
