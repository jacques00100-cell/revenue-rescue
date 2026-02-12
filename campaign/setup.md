# Revenue Rescue Email Campaign Setup Guide

## Overview
Complete automated email campaign system with engagement tracking and AI sentiment analysis for Revenue Rescue.

## 📁 Files Created

```
/builds/revenue-rescue/campaign/
├── config.yaml              # API keys and settings
├── campaign_runner.py       # Main automation script
├── sentiment_analyzer.py    # AI reply analysis
├── tracking_server.py       # Webhook/tracking server
├── dashboard.html           # Visual analytics dashboard
├── setup.md                 # This file
└── email_templates/
    ├── email_1_cold_intro.html
    ├── email_2_followup.html
    └── email_3_final.html
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /builds/revenue-rescue/campaign/
pip install flask pyyaml jinja2 requests
```

### 2. Set Up Resend (Recommended)

1. Go to [resend.com](https://resend.com) and create a free account
2. Verify your domain: `pac-holding.com`
   - Add DNS records as instructed by Resend
   - Wait for domain verification (usually instant)
3. Get your API key from the Resend dashboard
4. Update `config.yaml`:
   ```yaml
   email:
     provider: "resend"
     resend_api_key: "re_your_actual_api_key"
   ```

### 3. Set Up OpenAI for Sentiment Analysis

1. Go to [platform.openai.com](https://platform.openai.com)
2. Create an API key
3. Add billing (costs ~$0.001 per email reply analyzed)
4. Update `config.yaml`:
   ```yaml
   openai:
     api_key: "sk-your-openai-key"
     model: "gpt-4o-mini"
   ```

### 4. Configure Tracking Server

Update `config.yaml` with your tracking domain:
```yaml
tracking:
  base_url: "https://track.pac-holding.com"  # Or use localhost for testing
  server_port: 8000
```

For production, deploy the tracking server to a public URL so tracking pixels work.

### 5. Prepare Lead Data

Your `leads-for-import.csv` needs an **Email** column. Current columns:
- Business Name, Phone Number, Website, Industry, City, ZIP, Status, Notes, Priority Score, Date Added

You need to enrich this data with email addresses. Options:
1. Use a service like Hunter.io, Apollo.io, or ZoomInfo
2. Manual research
3. Skip leads without emails

## 📊 Running the Campaign

### Test Mode (Dry Run)

```bash
# Initialize database and preview first 5 emails
python campaign_runner.py ../../leads-for-import.csv
```

This will:
- Create the SQLite database
- Import top 50 priority leads
- Show what emails would be sent (without sending)

### Live Mode

1. Edit `config.yaml`:
   ```yaml
   campaign:
     dry_run: false
   ```

2. Start the tracking server:
   ```bash
   python tracking_server.py
   ```

3. In another terminal, run the campaign:
   ```bash
   python campaign_runner.py ../../leads-for-import.csv
   ```

## 📈 Viewing Analytics

### Dashboard
Open `dashboard.html` in a browser or serve it:
```bash
python -m http.server 8080
```
Then visit: http://localhost:8080/dashboard.html

### Command Line Report
```bash
python campaign_runner.py --report
```

## 🧪 Testing

### Test Sentiment Analysis
```bash
python sentiment_analyzer.py --test
```

### Test Email Templates
Open these files in a browser:
- `email_templates/email_1_cold_intro.html`
- `email_templates/email_2_followup.html`
- `email_templates/email_3_final.html`

## 📧 Email Sequence

| Day | Email | Subject | Purpose |
|-----|-------|---------|---------|
| 0 | 1 | `{First Name}, quick question about after-hours calls` | Cold intro with 80% hang-up stat |
| 3 | 2 | `Re: {First Name} - the $500 question` | Follow-up with revenue math |
| 7 | 3 | `{First Name}, last try` | Final with scarcity/offer |

## 🔧 Configuration Options

### Rate Limiting
```yaml
campaign:
  rate_limit_per_hour: 20  # Max emails per hour
```

### Sender Details
```yaml
sender:
  name: "Connor"
  email: "Connor@pac-holding.com"
  domain: "pac-holding.com"
```

### Demo Info
```yaml
demo:
  phone: "(817) 873-6706"
  calendly_url: "https://calendly.com/connor-pac-holding/revenue-rescue-demo"
```

## 📊 Database Schema

The system tracks:
- Email sends, opens, clicks per email in sequence
- Reply sentiment (interested/not_now/not_interested/unsubscribe/question)
- Sentiment score (-1 to +1)
- Campaign status (active/converted/unsubscribed/no_reply)

## 🔐 Security Notes

1. **Never commit `config.yaml`** with real API keys
2. Use environment variables for secrets in production
3. The unsubscribe endpoint is public (no auth needed)
4. Tracking pixels expose IP addresses (normal for email marketing)

## 🐛 Troubleshooting

### "No module named 'flask'"
```bash
pip install flask pyyaml jinja2 requests
```

### "Resend API key invalid"
- Check your API key in Resend dashboard
- Ensure domain is verified

### "No leads imported"
- Check CSV has an `Email` column
- Verify email addresses are present

### "Open tracking not working"
- Tracking server must be publicly accessible
- Gmail/images may block tracking pixels
- Check browser dev tools for 404s on pixel requests

## 📞 Support

For issues with:
- **Resend**: docs.resend.com
- **OpenAI**: platform.openai.com/docs
- **Campaign logic**: Check `campaign_runner.py` comments

---

## 📋 Pre-Launch Checklist

- [ ] Resend account created and domain verified
- [ ] OpenAI API key created and billing added
- [ ] `config.yaml` updated with real API keys
- [ ] Leads CSV has email addresses
- [ ] Demo phone number is working
- [ ] Calendly link is correct
- [ ] Tested in dry_run mode
- [ ] Tracking server accessible publicly (production)
- [ ] Dashboard loads and shows data

---

## 🎉 You're Ready!

Run the campaign with:
```bash
python campaign_runner.py ../../leads-for-import.csv
```

Monitor with:
```bash
python campaign_runner.py --report
```

Or open `dashboard.html` in your browser.
