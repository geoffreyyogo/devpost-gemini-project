# ngrok Setup for USSD Registration

## 🎯 Overview

This guide helps you expose your local USSD API to the internet using **ngrok**, allowing Africa's Talking to send USSD callbacks to your development machine.

---

## 📋 Prerequisites

- ✅ Working USSD API (`backend/ussd_api.py`)
- ✅ Africa's Talking account
- ✅ Internet connection
- ✅ Linux/Mac/WSL environment

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install ngrok

```bash
chmod +x setup_ngrok.sh
./setup_ngrok.sh
```

### Step 2: Configure ngrok Auth Token

1. Sign up for free ngrok account: https://dashboard.ngrok.com/signup
2. Get your auth token: https://dashboard.ngrok.com/get-started/your-authtoken
3. Configure it:

```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
```

### Step 3: Start USSD API with ngrok

```bash
chmod +x start_ussd_with_ngrok.sh
./start_ussd_with_ngrok.sh
```

**Done!** Your USSD endpoint is now publicly accessible.

---

## 📡 What Happens

When you run `start_ussd_with_ngrok.sh`:

```
┌─────────────────────────────────────────┐
│  1. Flask USSD API starts (port 5000)   │
│     http://localhost:5000               │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  2. ngrok creates public tunnel         │
│     https://abc123.ngrok.io             │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  3. Africa's Talking can reach you!     │
│     Callback: https://abc123.ngrok.io/ussd │
└─────────────────────────────────────────┘
```

---

## 🔧 Configure Africa's Talking

### Option 1: Sandbox (Testing)

1. Go to: https://account.africastalking.com/apps/sandbox/ussd
2. Find your **USSD Callback URL** field
3. Enter: `https://YOUR_NGROK_URL/ussd`
4. Click **Save**

Example:
```
Callback URL: https://abc123.ngrok-free.app/ussd
```

### Option 2: Production

1. Go to: https://account.africastalking.com/apps/production/ussd
2. Apply for a USSD code (e.g., `*384*1234#`)
3. Set callback URL: `https://YOUR_NGROK_URL/ussd`

**Note:** For production, consider using a permanent domain instead of ngrok.

---

## 📱 Testing USSD Registration

### Test 1: Local Test Interface

Visit: http://localhost:5000/test-ussd

This provides a web form to simulate USSD requests.

### Test 2: Real Phone (Sandbox)

1. Ensure ngrok is running
2. Configure Africa's Talking callback URL
3. Dial sandbox USSD code on a phone: `*384*1234#`
4. Follow the registration menu

### Test 3: Monitor Requests

Watch ngrok dashboard: http://localhost:4040

You'll see all incoming requests, responses, and timing.

---

## 🌾 USSD Registration Flow

When a farmer dials `*384*1234#`:

```
┌────────────────────────────────────────────────────┐
│ Step 1: Select Language                            │
│ CON Welcome to BloomWatch Kenya                    │
│ 1. English                                         │
│ 2. Kiswahili                                       │
└────────────────────────────────────────────────────┘
                     │ User presses: 1
┌────────────────────▼───────────────────────────────┐
│ Step 2: Enter Name                                 │
│ CON Enter your name:                               │
└────────────────────────────────────────────────────┘
                     │ User types: John Kamau
┌────────────────────▼───────────────────────────────┐
│ Step 3: Select Region                              │
│ CON Select your region:                            │
│ 1. Central Kenya                                   │
│ 2. Rift Valley                                     │
│ 3. Western                                         │
│ 4. Eastern                                         │
│ 5. Coast                                           │
└────────────────────────────────────────────────────┘
                     │ User presses: 1
┌────────────────────▼───────────────────────────────┐
│ Step 4: Select Crops                               │
│ CON Select crops (comma-separated):                │
│ 1. Maize                                           │
│ 2. Beans                                           │
│ 3. Coffee                                          │
│ 4. Tea                                             │
│ 5. Wheat                                           │
└────────────────────────────────────────────────────┘
                     │ User types: 1,2,3
┌────────────────────▼───────────────────────────────┐
│ Step 5: Select Language Preference                 │
│ CON Select language for alerts:                    │
│ 1. English                                         │
│ 2. Kiswahili                                       │
└────────────────────────────────────────────────────┘
                     │ User presses: 1
┌────────────────────▼───────────────────────────────┐
│ Step 6: Confirmation                               │
│ END ✅ Registration successful!                    │
│ You'll receive bloom alerts via SMS.               │
│ Welcome to BloomWatch Kenya, John!                 │
└────────────────────────────────────────────────────┘
                     │
┌────────────────────▼───────────────────────────────┐
│ Farmer saved to MongoDB                            │
│ Welcome SMS sent                                   │
│ Dashboard access created                           │
└────────────────────────────────────────────────────┘
```

---

## 🛠️ Troubleshooting

### Issue 1: ngrok not found

```bash
./setup_ngrok.sh
```

### Issue 2: Port 5000 already in use

```bash
# Find and kill process
lsof -ti:5000 | xargs kill -9

# Restart
./start_ussd_with_ngrok.sh
```

### Issue 3: ngrok authentication required

```bash
ngrok config add-authtoken YOUR_TOKEN
```

Get token from: https://dashboard.ngrok.com/get-started/your-authtoken

### Issue 4: Flask not starting

```bash
source venv/bin/activate
pip install flask
python backend/ussd_api.py
```

### Issue 5: Cannot detect ngrok URL

Manually check: http://localhost:4040

Copy the `https://` URL shown there.

---

## 📊 Monitoring

### View Live Requests

ngrok Dashboard: http://localhost:4040

Shows:
- All incoming requests
- Request headers and body
- Response status and data
- Request timing
- Replay requests

### View USSD Sessions

```bash
source venv/bin/activate
python backend/test_ussd_sms_integration.py
```

Or check MongoDB:
```python
from mongodb_service import MongoDBService
mongo = MongoDBService()

# View USSD sessions
sessions = list(mongo.ussd_sessions.find())
print(f"Active sessions: {len(sessions)}")

# View farmers registered via USSD
ussd_farmers = list(mongo.farmers.find({'registered_via': 'ussd'}))
print(f"USSD registrations: {len(ussd_farmers)}")
```

### Check Logs

```bash
# Flask logs (in terminal running start_ussd_with_ngrok.sh)
tail -f /tmp/ngrok.log
```

---

## 💰 ngrok Pricing

### Free Plan (Good for Testing)
- ✅ 1 online ngrok process
- ✅ 40 connections/minute
- ✅ Random URLs (changes on restart)
- ✅ Basic inspection
- ❌ Custom domains

**Perfect for development and testing!**

### Paid Plans (Production)
- **Personal ($8/month):**
  - 3 ngrok processes
  - 120 connections/minute
  - Reserved domains (consistent URLs)
  
- **Pro ($20/month):**
  - 10 processes
  - 600 connections/minute
  - Custom domains
  - IP whitelisting

**For production, consider deploying to a server instead.**

---

## 🚀 Production Deployment

For production, ngrok is not ideal (URLs change, limited connections). Instead:

### Option 1: Deploy to VPS

```bash
# On your VPS (Ubuntu/Debian)
sudo apt update
sudo apt install python3-pip python3-venv nginx certbot

# Clone your repo
git clone https://github.com/yourusername/bloom-detector.git
cd bloom-detector

# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with systemd
sudo cp config/bloomwatch-ussd.service /etc/systemd/system/
sudo systemctl enable bloomwatch-ussd
sudo systemctl start bloomwatch-ussd

# Setup nginx reverse proxy
sudo cp config/nginx-ussd.conf /etc/nginx/sites-available/bloomwatch-ussd
sudo ln -s /etc/nginx/sites-available/bloomwatch-ussd /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com
```

### Option 2: Deploy to Cloud

- **Heroku:** Easy deployment, free tier available
- **Railway:** Modern alternative to Heroku
- **Render:** Simple deployment with free tier
- **AWS/GCP/Azure:** Full control, more complex

See `DEPLOYMENT_GUIDE.md` for details.

---

## 📚 Quick Reference

### Start Everything
```bash
./start_ussd_with_ngrok.sh
```

### Stop Everything
Press `Ctrl+C` in the terminal

### View Status
- ngrok: http://localhost:4040
- USSD Test: http://localhost:5000/test-ussd
- Health: http://localhost:5000/health
- Stats: http://localhost:5000/stats

### Get Current ngrok URL
```bash
curl http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url'
```

### Test USSD Locally
```bash
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=test_123" \
  -d "serviceCode=*384*1234#" \
  -d "phoneNumber=+254712345678" \
  -d "text="
```

---

## ✅ Checklist

- [ ] Install ngrok (`./setup_ngrok.sh`)
- [ ] Get ngrok auth token
- [ ] Configure token (`ngrok config add-authtoken TOKEN`)
- [ ] Start services (`./start_ussd_with_ngrok.sh`)
- [ ] Get public URL from http://localhost:4040
- [ ] Configure Africa's Talking callback URL
- [ ] Test with web interface (http://localhost:5000/test-ussd)
- [ ] Test with real phone (dial USSD code)
- [ ] Monitor requests in ngrok dashboard
- [ ] Check MongoDB for registered farmers

---

## 🎓 Additional Resources

- ngrok Docs: https://ngrok.com/docs
- Africa's Talking USSD: https://developers.africastalking.com/docs/ussd/overview
- Flask Docs: https://flask.palletsprojects.com/
- MongoDB Docs: https://www.mongodb.com/docs/

---

## 🆘 Support

If you encounter issues:

1. Check logs in terminal
2. Check ngrok dashboard: http://localhost:4040
3. Test locally first: http://localhost:5000/test-ussd
4. Review `USSD_SMS_DEPLOYMENT_GUIDE.md`
5. Run test suite: `python backend/test_ussd_sms_integration.py`

---

**Ready to enable USSD registration for farmers! 🌾**

```bash
./setup_ngrok.sh
ngrok config add-authtoken YOUR_TOKEN
./start_ussd_with_ngrok.sh
```

