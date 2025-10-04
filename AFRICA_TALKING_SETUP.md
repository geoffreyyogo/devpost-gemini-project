# Africa's Talking + MongoDB Setup Guide

## 🌾 BloomWatch Kenya - Complete Setup

This guide will help you set up the full farmer registration and notification system using Africa's Talking USSD/SMS and MongoDB.

---

## 📋 Prerequisites

1. **Africa's Talking Account**
   - Sign up at: https://account.africastalking.com/
   - Get your API key and username

2. **MongoDB** (Choose one option)
   - **Option A**: Local MongoDB
     ```bash
     # Ubuntu/Debian
     sudo apt-get install mongodb
     sudo systemctl start mongodb
     ```
   
   - **Option B**: MongoDB Atlas (Cloud - Recommended)
     - Sign up at: https://www.mongodb.com/cloud/atlas
     - Create free cluster
     - Get connection string

3. **Python Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install africastalking pymongo flask python-dotenv
   ```

---

## 🔧 Step-by-Step Setup

### 1. Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit with your credentials
nano .env
```

Add your Africa's Talking credentials:
```bash
AT_USERNAME=your_username  # or 'sandbox' for testing
AT_API_KEY=your_api_key_here
MONGODB_URI=mongodb://localhost:27017/  # or your MongoDB Atlas URL
```

### 2. Test MongoDB Connection

```bash
python backend/mongodb_service.py
```

Expected output:
```
✓ Connected to MongoDB successfully
✓ Database indexes created
✓ Farmer registration: {...}
```

### 3. Test Africa's Talking Service

```bash
python backend/africastalking_service.py
```

This will simulate the complete USSD registration flow.

### 4. Start USSD API Server

```bash
python backend/ussd_api.py
```

The server will start on `http://localhost:5000`

- **USSD Endpoint**: `http://localhost:5000/ussd`
- **Test Interface**: `http://localhost:5000/test-ussd`
- **Statistics**: `http://localhost:5000/stats`

---

## 🌐 Expose Local Server (for Testing)

To test with actual USSD codes, you need to expose your local server to the internet.

### Option 1: Using ngrok (Recommended for testing)

```bash
# Install ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# Authenticate (get token from ngrok.com)
ngrok config add-authtoken YOUR_TOKEN

# Expose port 5000
ngrok http 5000
```

You'll get a public URL like: `https://abc123.ngrok.io`

### Option 2: Deploy to Cloud

Deploy to:
- **Heroku**: `git push heroku main`
- **Digital Ocean**: Use App Platform
- **AWS/GCP**: Use EC2/Compute Engine

---

## 📱 Configure Africa's Talking USSD

1. Go to: https://account.africastalking.com/apps/sandbox/ussd/createchannel

2. **Create USSD Channel**:
   - **Channel Name**: BloomWatch Kenya
   - **USSD Code**: `*384*1234#` (or your assigned code)
   - **Callback URL**: `https://your-ngrok-url.ngrok.io/ussd` or your production URL

3. **Save** and test by dialing the USSD code on your phone!

---

## 🧪 Testing the USSD Flow

### Method 1: Web Interface (Local Testing)

1. Start the API server:
   ```bash
   python backend/ussd_api.py
   ```

2. Open browser: `http://localhost:5000/test-ussd`

3. Test the flow step by step:
   - Empty text → Language menu
   - Text "1" → Name prompt
   - Text "1*John Kamau" → Region prompt
   - Text "1*John Kamau*1" → Crop prompt
   - Text "1*John Kamau*1*1,2" → Confirmation
   - Text "1*John Kamau*1*1,2*1" → Registration complete

### Method 2: Real Phone (Production Testing)

1. Ensure ngrok is running and callback URL is configured
2. Dial your USSD code: `*384*1234#`
3. Follow the prompts to register

---

## 📊 USSD Registration Flow

```
┌─────────────────────────────────────┐
│  Farmer dials *384*1234#            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Language Selection                 │
│  1. English                         │
│  2. Kiswahili                       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Enter Full Name                    │
│  > John Kamau                       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Select Region                      │
│  1. Central                         │
│  2. Rift Valley                     │
│  3. Western                         │
│  4. Eastern                         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Select Crops (e.g., 1,2,3)        │
│  1. Maize   4. Tea                  │
│  2. Beans   5. Wheat                │
│  3. Coffee  6. Sorghum              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Confirm Details                    │
│  1. Confirm                         │
│  2. Cancel                          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  ✓ Registration Complete!           │
│  Welcome SMS sent                   │
│  Farmer added to MongoDB            │
└─────────────────────────────────────┘
```

---

## 🔔 Sending Bloom Alerts

### Manually trigger alerts (for testing):

```python
from backend.africastalking_service import AfricasTalkingService

at_service = AfricasTalkingService()

# Get farmers growing maize in Central Kenya
mongo = at_service.mongo
farmers = mongo.get_farmers_by_crop('maize', 'central')

# Create bloom event
bloom_event = {
    'crop_type': 'maize',
    'bloom_intensity': 0.8,
    'region': 'central',
    'location_lat': -0.9,
    'location_lon': 36.9
}

# Send alerts
result = at_service.send_bloom_alert(farmers, bloom_event)
print(f"Sent: {result['sent']}, Failed: {result['failed']}")
```

---

## 📊 Monitor Farmer Data

### View statistics:
```bash
# Start API server
python backend/ussd_api.py

# Open in browser
http://localhost:5000/stats
```

### Query MongoDB directly:
```bash
# Connect to MongoDB
mongo bloomwatch_kenya

# Show farmers
db.farmers.find().pretty()

# Count by region
db.farmers.aggregate([
  {$group: {_id: "$region", count: {$sum: 1}}}
])

# Recent alerts
db.alerts.find().sort({created_at: -1}).limit(10)
```

---

## 🚀 Production Deployment Checklist

- [ ] Get production Africa's Talking account (not sandbox)
- [ ] Purchase USSD code from your telecom provider
- [ ] Set up MongoDB Atlas cluster (free tier available)
- [ ] Deploy API server to cloud (Heroku, DO, AWS, etc.)
- [ ] Configure production callback URL in Africa's Talking
- [ ] Set up SSL certificate (Let's Encrypt)
- [ ] Enable MongoDB authentication
- [ ] Set up monitoring (error tracking, uptime monitoring)
- [ ] Configure backup for MongoDB
- [ ] Test thoroughly with real phones

---

## 🐛 Troubleshooting

### Issue: MongoDB connection failed
**Solution**: Check if MongoDB is running
```bash
sudo systemctl status mongodb
sudo systemctl start mongodb
```

### Issue: Africa's Talking API error
**Solution**: 
1. Verify API key in `.env`
2. Check if using correct username (sandbox vs production)
3. Ensure phone numbers are in international format (+254...)

### Issue: USSD not responding
**Solution**:
1. Check if ngrok is running
2. Verify callback URL in Africa's Talking dashboard
3. Check API server logs for errors

### Issue: SMS not sending
**Solution**:
1. In sandbox mode, you need to register test phone numbers
2. Check Africa's Talking dashboard for credit balance
3. Verify phone number format (+254...)

---

## 📞 Support Resources

- **Africa's Talking Docs**: https://developers.africastalking.com/
- **MongoDB Docs**: https://docs.mongodb.com/
- **Project GitHub**: [Your repository URL]
- **Discord/Slack**: [Your community link]

---

## 🎉 Success! Next Steps

Once setup is complete:

1. **Register test farmers** via USSD
2. **View statistics** at `/stats` endpoint
3. **Test bloom alerts** manually
4. **Integrate with Streamlit** dashboard
5. **Deploy automated scheduler** for regular bloom detection
6. **Scale to production** with real USSD codes

---

**BloomWatch Kenya** - Empowering farmers with NASA satellite technology 🛰️🌾🇰🇪

