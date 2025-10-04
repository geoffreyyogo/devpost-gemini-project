# 🚀 BloomWatch Kenya - Quick Start Guide

## ✅ System Status: READY FOR PRODUCTION

---

## 🧪 Test Everything Locally (RIGHT NOW)

### 1. Test Complete Integration
```bash
cd /home/yogo/bloom-detector/backend
python test_ussd_sms_integration.py
```
**Result**: All tests pass ✅

### 2. Test USSD with Web Interface
```bash
cd /home/yogo/bloom-detector/backend
python ussd_api.py
```
Open: **http://localhost:5000/test-ussd**

### 3. Test Web Registration
```bash
cd /home/yogo/bloom-detector/app
streamlit run streamlit_app_v2.py
```
Open: **http://localhost:8501**  
Login: **+254712345678** / **password123**

---

## 🔑 Add Africa's Talking (For Production)

### Step 1: Get Credentials
1. Sign up: https://africastalking.com/
2. Create app (sandbox is free!)
3. Get: **Username** & **API Key**

### Step 2: Update .env
```bash
AT_USERNAME=your_username_here
AT_API_KEY=your_api_key_here
```

### Step 3: Test
```bash
python -c "from africastalking_service import AfricasTalkingService; at=AfricasTalkingService(); print(at.send_sms('+254712345678', 'Test SMS'))"
```

**That's it!** SMS will now send for real.

---

## 📱 USSD Production Setup

### Option A: Use ngrok (Quick Test)
```bash
# Terminal 1
cd /home/yogo/bloom-detector/backend
python ussd_api.py

# Terminal 2
ngrok http 5000
```
Copy the https URL (e.g., `https://abc123.ngrok.io`)

### Option B: Deploy to Server
See: `USSD_SMS_DEPLOYMENT_GUIDE.md`

### Configure Africa's Talking
- Go to USSD section in dashboard
- Set callback URL: `https://your-url.com/ussd`
- Method: POST
- Save

### Test
Dial your USSD code on a phone: **\*384\*1234#**

---

## 📊 Check Database

```bash
python -c "from mongodb_service import MongoDBService; m=MongoDBService(); s=m.get_farmer_statistics(); print(f'Farmers: {s[\"total_farmers\"]}')"
```

---

## 📚 Full Documentation

| Guide | Purpose |
|-------|---------|
| **INTEGRATION_COMPLETE_SUMMARY.md** | Complete overview |
| **USSD_SMS_DEPLOYMENT_GUIDE.md** | Production deployment |
| **REGISTRATION_SETUP_COMPLETE.md** | Registration details |

---

## 🎯 What Works RIGHT NOW

✅ Web registration  
✅ USSD registration (local simulator)  
✅ SMS alerts (demo mode)  
✅ Bloom detection integration  
✅ Database (10 farmers registered)  
✅ Bilingual support (EN/SW)  
✅ All tests passing  

## 🎯 What Needs API Keys

⏭️ Real SMS sending  
⏭️ USSD on real phones  

---

## 💰 Cost (Kenya)

**With 1000 farmers:**
- SMS: ~KES 3,200/month (~$22)
- USSD setup: ~$100-500 one-time
- USSD monthly: ~$50-100
- **Total: ~KES 8,700/month (~$60)**

**Testing (Sandbox): FREE!**

---

## 🆘 Need Help?

### Test Not Working?
```bash
# Check MongoDB connection
python -c "from mongodb_service import MongoDBService; print('✅ Connected' if MongoDBService().is_connected() else '❌ Not Connected')"

# Check Africa's Talking
python -c "from africastalking_service import AfricasTalkingService; print(AfricasTalkingService().api_key or '❌ No API key')"
```

### Common Issues
1. **MongoDB connection fails**: Check IP whitelist in Atlas
2. **SMS "invalid auth"**: API key not set (demo mode is OK!)
3. **USSD not working**: Normal without callback URL configured

---

## 🎉 YOU'RE READY!

Everything is built and tested. Add your API keys when you're ready for production!

**Start testing now:**
```bash
python backend/test_ussd_sms_integration.py
```

