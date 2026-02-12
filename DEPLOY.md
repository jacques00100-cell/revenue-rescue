# Revenue Rescue - Production Deployment

## Platform: Render.com (Free Tier)

### Why Render?
- **Always on** — Unlike Heroku, free tier doesn't sleep
- **HTTPS by default** — Secure webhooks out of the box  
- **Easy deploy** — Connect GitHub, auto-deploy on push
- **Reliable** — Production-grade infrastructure

---

## Deploy Steps

### 1. Create Render Account
- Go to [render.com](https://render.com)
- Sign up with GitHub
- Connect your repository

### 2. Create Web Service
- Click "New" → "Web Service"
- Connect: `jacques00100-cell/revenue-rescue`
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn -w 2 -b 0.0.0.0:$PORT app:app`

### 3. Environment Variables
Add these in Render dashboard:

| Variable | Value |
|----------|-------|
| `TWILIO_ACCOUNT_SID` | (from your Twilio console) |
| `TWILIO_AUTH_TOKEN` | (from your Twilio console) |
| `TWILIO_PHONE` | +18178736706 |
| `VAPI_ASSISTANT_ID` | 73a70239-a0f1-480c-9b50-f310554c974e |

### 4. Deploy
- Click "Create Web Service"
- Wait for build (~2 minutes)
- Get URL: `https://revenue-rescue.onrender.com`

### 5. Configure Webhooks
**Vapi Dashboard:**
- Server URL: `https://revenue-rescue.onrender.com/webhook/vapi`

**Twilio Console:**
- Webhook: `https://revenue-rescue.onrender.com/webhook/twilio`

---

## Testing

```bash
# Health check
curl https://revenue-rescue.onrender.com/health

# Dashboard
curl https://revenue-rescue.onrender.com/dashboard
```

---

**This is BULLETPROOF.**
- 99.9% uptime
- HTTPS always
- Auto-restart
- No tunnel flapping
