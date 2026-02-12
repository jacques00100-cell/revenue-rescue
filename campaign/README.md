# Revenue Rescue Email Campaign System

## ✅ Complete System Delivered

All files saved to: `/builds/revenue-rescue/campaign/`

### 📁 File Structure

```
/builds/revenue-rescue/campaign/
├── README.md                    # This file
├── config.yaml                  # API keys & settings
├── requirements.txt             # Python dependencies
├── setup.md                     # Detailed setup instructions
│
├── campaign_runner.py           # Main automation script
├── sentiment_analyzer.py        # AI reply analysis
├── tracking_server.py           # Webhook/tracking server
├── preview.py                   # Dry-run email preview
├── enrich_emails.py             # Email pattern generator
│
├── dashboard.html               # Visual analytics dashboard
│
└── email_templates/
    ├── email_1_cold_intro.html  # Day 0: Cold intro
    ├── email_2_followup.html    # Day 3: Revenue math
    └── email_3_final.html       # Day 7: Scarcity/offer
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd /builds/revenue-rescue/campaign/
pip3 install flask pyyaml jinja2 requests
```

### 2. Preview Campaign (Dry Run)
```bash
python3 preview.py /path/to/leads-for-import.csv
```

### 3. Set Up Services

**Resend (Email)**
- Sign up: resend.com
- Verify domain: pac-holding.com
- Get API key → update `config.yaml`

**OpenAI (Sentiment)**
- Get API key: platform.openai.com
- Update `config.yaml`

### 4. Run Campaign
```bash
# Start tracking server (terminal 1)
python3 tracking_server.py

# Run campaign (terminal 2)  
python3 campaign_runner.py /path/to/leads-for-import.csv
```

### 5. View Dashboard
Open `dashboard.html` in browser

## 📧 Email Sequence

| Day | Subject | Key Element |
|-----|---------|-------------|
| 0 | `[First Name], quick question about after-hours calls` | 80% hang-up stat |
| 3 | `Re: [First Name] - the $500 question` | Revenue math |
| 7 | `[First Name], last try` | Beta offer ($99/mo) |

## 📊 Features

- ✅ SQLite database for tracking
- ✅ Open/click tracking pixels
- ✅ Rate limiting (20/hour max)
- ✅ AI sentiment analysis
- ✅ Unsubscribe handling
- ✅ Real-time dashboard
- ✅ Conversion funnel visualization
- ✅ Top leads ranking

## ⚠️ Critical: Email Addresses Needed

Your `leads-for-import.csv` currently lacks email addresses. Use `enrich_emails.py` to generate patterns, then verify with Hunter.io or similar before sending.

## 📊 Sample Preview Output

First 5 leads would receive personalized emails for:
1. Ritual Hair Co. (Dallas)
2. Elévate Hair Parlour (Dallas)
3. La Maison Salon (Dallas)
4. Mane Collective (Dallas)
5. One Studio Salon (Dallas)

All 3 emails in sequence previewed in `preview.py` output.

## 🔐 API Keys Needed

Update these in `config.yaml`:
- `email.resend_api_key` - From resend.com
- `openai.api_key` - From platform.openai.com

## 💡 Pro Tips

1. Start with dry_run: true in config.yaml
2. Send test to your own email first
3. Monitor dashboard after each batch
4. Follow up with "interested" sentiment leads immediately
5. Respect unsubscribe requests instantly

## 📞 Demo Contact

- Phone: (817) 873-6706
- Calendly: Set in config.yaml

---

Built for Revenue Rescue by OpenClaw
