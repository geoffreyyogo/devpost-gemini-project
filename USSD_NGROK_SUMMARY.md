# 🌾 BloomWatch Kenya - ngrok USSD Setup Summary

## ✅ What Was Created

| File | Size | Purpose |
|------|------|---------|
| `setup_ngrok.sh` | 2.6KB | Install ngrok automatically |
| `start_ussd_with_ngrok.sh` | 4.6KB | Start USSD API + ngrok together |
| `NGROK_USSD_SETUP.md` | 13KB | Complete documentation |
| `NGROK_QUICK_START.txt` | 4.8KB | Quick reference card |

---

## 🚀 Quick Start (3 Commands)

```bash
# 1. Install ngrok
./setup_ngrok.sh

# 2. Configure auth token (get from https://dashboard.ngrok.com)
ngrok config add-authtoken YOUR_TOKEN_HERE

# 3. Start everything!
./start_ussd_with_ngrok.sh
```

**That's it!** Your USSD API will be publicly accessible.

---

## 📱 How It Works

```
Farmer → Dials *384*1234#
   ↓
Africa's Talking → Receives USSD request
   ↓
Sends to → https://abc123.ngrok.io/ussd (your ngrok URL)
   ↓
ngrok → Forwards to localhost:5000
   ↓
Flask USSD API → Processes registration
   ↓
MongoDB → Saves farmer data
   ↓
SMS → Sends welcome message
   ↓
✅ Farmer registered!
```

---

## 🎯 What You Get

### For Farmers
- ✅ Register via USSD code (no smartphone needed!)
- ✅ Works on any phone
- ✅ English and Swahili support
- ✅ Immediate SMS confirmation
- ✅ Access to bloom alerts

### For You (Developer)
- ✅ Automatic USSD API startup
- ✅ Automatic ngrok tunnel
- ✅ Public URL for callbacks
- ✅ Real-time monitoring
- ✅ Web testing interface
- ✅ Easy debugging

---

## 📊 Testing Options

### Option 1: Web Interface
```bash
./start_ussd_with_ngrok.sh
# Visit: http://localhost:5000/test-ussd
```

### Option 2: Real Phone
```bash
./start_ussd_with_ngrok.sh
# Configure Africa's Talking
# Dial: *384*1234#
```

### Option 3: curl
```bash
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=test_123" \
  -d "serviceCode=*384*1234#" \
  -d "phoneNumber=+254712345678" \
  -d "text="
```

---

## 🔍 Monitoring

### ngrok Dashboard
**URL:** http://localhost:4040

Shows:
- All incoming requests
- Request/response bodies
- Timing information
- Replay requests

### USSD Test Page
**URL:** http://localhost:5000/test-ussd

Interactive form to simulate USSD flows

### Health Check
**URL:** http://localhost:5000/health

API status check

### Farmer Statistics
**URL:** http://localhost:5000/stats

View registration numbers

---

## 🌍 USSD Registration Flow

### Step 1: Language Selection
```
CON Welcome to BloomWatch Kenya
1. English
2. Kiswahili
```

### Step 2: Name Entry
```
CON Enter your name:
```
Farmer types: `John Kamau`

### Step 3: Region Selection
```
CON Select your region:
1. Central Kenya
2. Rift Valley
3. Western
4. Eastern
5. Coast
```

### Step 4: Crop Selection
```
CON Select crops (comma-separated):
1. Maize
2. Beans
3. Coffee
4. Tea
5. Wheat
```
Farmer types: `1,2,3`

### Step 5: Alert Language
```
CON Select language for alerts:
1. English
2. Kiswahili
```

### Step 6: Confirmation
```
END ✅ Registration successful!
You'll receive bloom alerts via SMS.
Welcome to BloomWatch Kenya, John!
```

---

## 🔧 Configuration

### Africa's Talking Setup

1. **Login:** https://account.africastalking.com/
2. **Go to USSD:** Apps → Sandbox/Production → USSD
3. **Set Callback URL:**
   ```
   https://YOUR_NGROK_URL/ussd
   ```
   Example: `https://abc123.ngrok-free.app/ussd`
4. **Save**

### Environment Variables (Optional)

Create `.env` file:
```bash
AFRICASTALKING_USERNAME=your_username
AFRICASTALKING_API_KEY=your_api_key
AFRICASTALKING_SHORTCODE=*384*1234#
MONGODB_URI=mongodb://localhost:27017/bloomwatch
```

---

## 💡 Tips & Best Practices

### 1. Keep Terminal Open
ngrok tunnel requires the terminal to stay open

### 2. Note the URL
Copy your ngrok URL each time (it changes on restart with free plan)

### 3. Monitor Requests
Check http://localhost:4040 for all incoming requests

### 4. Test Locally First
Use http://localhost:5000/test-ussd before testing on phone

### 5. Check Logs
Watch the terminal for request logs and errors

---

## 🆘 Troubleshooting

### ngrok not found
```bash
./setup_ngrok.sh
```

### Port 5000 already in use
```bash
lsof -ti:5000 | xargs kill -9
./start_ussd_with_ngrok.sh
```

### Authentication required
```bash
ngrok config add-authtoken YOUR_TOKEN
```

### Cannot detect ngrok URL
Manually check: http://localhost:4040

### Flask not starting
```bash
source venv/bin/activate
pip install flask
cd backend && python ussd_api.py
```

### Africa's Talking not calling back
- Check ngrok URL is correct
- Ensure ngrok is running
- Verify callback URL in AT dashboard
- Test locally first: http://localhost:5000/test-ussd

---

## 💰 Costs

### ngrok (Free Plan)
- ✅ 1 online process
- ✅ 40 requests/minute
- ✅ Basic inspection
- ❌ URL changes on restart
- ❌ Custom domains

**Cost:** FREE

### Africa's Talking
- **Sandbox:** FREE (testing only)
- **Production USSD:** ~$100-500 setup + $50-100/month
- **SMS:** ~$0.01-0.02 per message

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `NGROK_QUICK_START.txt` | Quick reference card |
| `NGROK_USSD_SETUP.md` | Detailed setup guide |
| `USSD_SMS_DEPLOYMENT_GUIDE.md` | Production deployment |
| `INTEGRATION_STATUS.md` | Overall system status |

---

## 🎓 Learn More

- **ngrok Docs:** https://ngrok.com/docs
- **Africa's Talking USSD:** https://developers.africastalking.com/docs/ussd/overview
- **Flask Docs:** https://flask.palletsprojects.com/

---

## ✅ Checklist

- [ ] Install ngrok (`./setup_ngrok.sh`)
- [ ] Sign up for ngrok account
- [ ] Get ngrok auth token
- [ ] Configure token (`ngrok config add-authtoken`)
- [ ] Start services (`./start_ussd_with_ngrok.sh`)
- [ ] Copy ngrok URL
- [ ] Configure Africa's Talking callback
- [ ] Test with web interface
- [ ] Test with real phone
- [ ] Monitor in ngrok dashboard
- [ ] Check farmer registrations

---

## 🎉 You're Ready!

Your USSD registration system is now set up and ready to use. Farmers can register by simply dialing a USSD code on any phone - no smartphone or app required!

**Get Started:**
```bash
./start_ussd_with_ngrok.sh
```

Then configure the callback URL in Africa's Talking and start testing! 🚀

