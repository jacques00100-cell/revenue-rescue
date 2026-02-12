# VAPI Assistant Fix - Deployment Instructions

## 🎯 Summary of Changes

Fixed issues causing abrupt hangups and unresponsiveness in the Cool Air HVAC AI phone assistant.

### Changes Made:

1. **Extended Silence Timeout**: 30s → 45s (gives hesitant callers more time)
2. **Fixed Webhook Response**: Empty 200 → Proper JSON with continue action
3. **Added Explicit Name Collection**: System prompt now requires asking for name FIRST
4. **Disabled Auto End-Call**: `endCallFunctionEnabled: false` (prevents abrupt hangup)
5. **Increased Response Delay**: 0.5s → 1.0s (prevents cutting off callers)
6. **Removed End Call Phrases**: Empty array prevents accidental triggers

---

## 📁 Files Modified

### 1. New Configuration File
- **File**: `config/vapi-assistant-fixed.json`
- **Status**: ✅ Ready for upload

Key improvements:
- Name collection is now the FIRST step
- Explicit "WAIT" instructions added to system prompt
- Mandatory confirmation of phone numbers and addresses
- Graceful ending that asks "Is there anything else?" before goodbye

### 2. Updated Webhook Handler
- **File**: `app.py`
- **Status**: ✅ Updated with proper response format

Changes:
- Returns JSON with `{"status": "ok", "action": "continue"}`
- Handles multiple message types (transcript, end-of-call-report)
- Proper logging for debugging
- No more empty 200 responses

### 3. Test Script
- **File**: `test_vapi_flow.py`
- **Status**: ✅ Ready to run

Tests:
- Configuration validity
- Conversation flow structure
- Webhook response format
- End-of-call logging

---

## 🚀 Deployment Steps

### Step 1: Deploy Updated Webhook Server

```bash
# Navigate to the revenue-rescue directory
cd ~/.openclaw/workspace/builds/revenue-rescue

# Install dependencies if needed
pip install flask requests

# Start the server
python app.py
```

The server will start on port 8080 (or PORT env variable).

### Step 2: Test Locally (Optional but Recommended)

```bash
# In a new terminal, run the test script
cd ~/.openclaw/workspace/builds/revenue-rescue
python test_vapi_flow.py
```

Expected output:
```
🚀 Vapi Assistant Flow Tester
...
Results: X/X tests passed
🎉 All tests passed!
```

### Step 3: Upload New Config to Vapi Dashboard

1. Log in to [Vapi Dashboard](https://dashboard.vapi.ai)
2. Go to Assistants → Cool Air HVAC Dispatcher
3. Click "Edit"
4. Copy the contents of `config/vapi-assistant-fixed.json`
5. Paste into the configuration editor
6. Click "Save"

### Step 4: Update Webhook URL (If Changed)

1. In Vapi Dashboard → Assistant Settings
2. Find "Server URL" or "Webhook URL" field
3. Ensure it points to your deployed webhook:
   - Local testing: `http://your-ngrok-url.ngrok.io/webhook/vapi`
   - Production: `https://your-domain.com/webhook/vapi`

### Step 5: Test the Phone Call

1. Call your Vapi phone number
2. Listen for the greeting: "Thank you for calling Cool Air HVAC..."
3. When asked "May I have your name please?" - say your name
4. **EXPECT**: AI should acknowledge your name and continue
5. Proceed through the conversation
6. **EXPECT**: No abrupt hangup - AI should ask "Is there anything else?" before ending

---

## 🔧 Rollback Instructions

If issues occur:

```bash
# Revert to original config
cp config/vapi-assistant.json config/vapi-assistant-active.json

# Or revert app.py changes
git checkout app.py
```

---

## 📊 Monitoring & Debugging

### Check Webhook Logs

```bash
# Watch server logs
tail -f ~/.openclaw/workspace/builds/revenue-rescue/server.log

# Or view Flask output directly
python app.py
```

### Key Log Messages to Watch For

| Message | Meaning |
|---------|---------|
| `📞 Vapi webhook hit` | Webhook received a call |
| `📝 Transcript: ...` | Real-time transcript received |
| `✅ Call ended. Duration: Xs` | Call completed successfully |

### Common Issues

**Issue**: Webhook returns 500 error  
**Fix**: Check Flask server is running and port 8080 is accessible

**Issue**: AI still hangs up abruptly  
**Fix**: Verify `endCallFunctionEnabled: false` in config uploaded to Vapi

**Issue**: AI ignores caller's name  
**Fix**: Check system prompt includes "May I have your name please?" as first question

---

## 📞 Support

If issues persist:

1. Check Vapi Dashboard → Call Logs for specific error messages
2. Review webhook server logs
3. Run `python test_vapi_flow.py` to validate setup
4. Compare your config against `config/vapi-assistant-fixed.json`

---

## ✅ Verification Checklist

Before going live:

- [ ] Flask server running on correct port
- [ ] Webhook URL accessible from internet (use ngrok for local testing)
- [ ] Fixed config uploaded to Vapi dashboard
- [ ] Test call completed successfully
- [ ] Name collection works
- [ ] No abrupt hangups
- [ ] Graceful goodbye at end of call
