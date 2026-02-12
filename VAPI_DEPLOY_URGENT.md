# URGENT: VAPI DEPLOY NEEDED

## Status
Phone AI still running OLD config. Fix created but NOT deployed.

## Action Required (5 minutes)

### 1. Upload Fixed Assistant
1. Go to https://dashboard.vapi.ai
2. Find your assistant (Cool Air HVAC Dispatcher)
3. Click "Import JSON"
4. Upload: `/builds/revenue-rescue/config/vapi-assistant-fixed.json`

### 2. Update Webhook URL
1. In Vapi dashboard, go to "Server" tab
2. Set Webhook URL: `https://revenue-rescue.onrender.com/webhook/vapi`
3. Save changes

### 3. Verify Deployment
1. Call (817) 873-6706
2. AI should now ask: "Thank you for calling. May I have your name please?"
3. Should NOT hang up abruptly

## What Changed
- Name collection is FIRST step
- Auto hangup DISABLED
- Silence timeout: 30s → 45s
- Response delay: 0.5s → 1.0s

## Test Checklist
- [ ] AI asks for name immediately
- [ ] Waits for your response
- [ ] Collects name before asking how to help
- [ ] Does NOT hang up mid-conversation
- [ ] Ends with "Thank you for calling..." not silence

If still broken after deploy, check Render logs.