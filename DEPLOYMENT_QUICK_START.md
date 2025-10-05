# 🚀 BloomWatch Kenya - Quick Deployment Guide

## 📍 Accessing Your Dashboards

### Local Development

| Service | URL | Access |
|---------|-----|--------|
| **Main App** | http://localhost:8501 | Public (farmers) |
| **Admin Dashboard** | http://localhost:8502 | Admin only |
| **USSD API** | http://localhost:5000 | Internal API |

**Note:** Admin dashboard is on a **separate port** (8502), not a route on the main app.

### Starting Services Locally

```bash
# Terminal 1: Main App
./start_app.sh
# or
streamlit run app/streamlit_app_enhanced.py

# Terminal 2: Admin Dashboard
./start_admin.sh
# or
streamlit run app/admin_dashboard.py --server.port 8502

# Terminal 3: USSD API (optional)
cd backend && python ussd_api.py
```

---

## 🌐 After Render Deployment

Your services will be available at:

```
Main App (Public):
https://bloomwatch-web.onrender.com
└─ Farmers register and view bloom alerts

Admin Dashboard:
https://bloomwatch-admin.onrender.com
└─ Manage farmers, send alerts, view queues

USSD API:
https://bloomwatch-ussd.onrender.com/ussd
└─ Africa's Talking callbacks
```

---

## 🔐 Admin Dashboard Access

### Default Credentials

**Username:** `admin`  
**Password:** `bloomwatch2024`

⚠️ **IMPORTANT:** Change these in production!

To change admin credentials, edit:
```python
# app/admin_dashboard.py
ADMIN_CREDENTIALS = {
    'admin': 'your_new_password',  # Change this!
    'your_username': 'your_password'  # Add more admins
}
```

Or set via environment variable:
```bash
# In Render dashboard, add:
ADMIN_PASSWORD=your_secure_password
```

---

## 🚀 Deployment Steps (Summary)

### 1. Prepare Repository
```bash
# Copy production requirements
cp requirements-render.txt requirements.txt

# Commit and push
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 2. Set Up MongoDB Atlas
1. Create free M0 cluster at https://www.mongodb.com/cloud/atlas
2. Create database user
3. Whitelist all IPs (0.0.0.0/0)
4. Get connection string
5. Save for Render env vars

### 3. Deploy to Render
1. Go to https://render.com
2. New → Blueprint
3. Select your GitHub repo
4. Render auto-detects `render.yaml`
5. Add environment variables:
   ```
   MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/bloomwatch
   AFRICASTALKING_USERNAME=your_username
   AFRICASTALKING_API_KEY=your_api_key
   ADMIN_PASSWORD=your_admin_password
   ```
6. Click "Apply"
7. Wait ~5 minutes for deployment

### 4. Configure Africa's Talking
1. Go to https://account.africastalking.com/
2. USSD Section
3. Set callback URL: `https://bloomwatch-ussd.onrender.com/ussd`
4. Save

### 5. Test Everything
- ✅ Visit main app URL
- ✅ Register a test farmer
- ✅ Login to admin dashboard
- ✅ Send test alert
- ✅ Dial USSD code on phone

---

## 📱 Using the Admin Dashboard

### 1. Dashboard (Home)
- View total farmers
- See recent registrations
- Check statistics
- View farmers by region
- See popular crops

### 2. Farmers Page
- Search farmers
- Filter by region/source
- View farmer details
- Edit farmer info
- Delete farmers
- Send individual alerts

### 3. Create Farmer
- Manually add farmers
- Set all details
- Enable/disable SMS
- Send welcome message

### 4. Send Alerts
- Send to all farmers
- Filter by region
- Filter by crop
- Send to specific farmer
- Choose alert type:
  - Bloom detection
  - Weather update
  - Custom message
- Preview recipients
- View alert history
- Check statistics

### 5. Message Queue
- Search by phone number
- View all messages
- See pending messages
- See delivered messages
- Filter by status

---

## 🎯 Quick Actions

### Register New Farmer via Admin
1. Login to admin dashboard
2. Click "➕ Create Farmer"
3. Fill in details
4. Click "Create Farmer"
5. Farmer receives welcome SMS!

### Send Alert to All Farmers
1. Go to "📨 Send Alerts"
2. Select "All Farmers"
3. Choose alert type
4. Click "Preview Recipients"
5. Click "Send Alert Now"
6. Monitor success rate

### View Farmer's Message History
1. Go to "📬 Message Queue"
2. Enter farmer's phone number
3. View all pending/delivered messages
4. See message details

---

## 🔧 Troubleshooting

### Admin Dashboard Won't Load
**Check:**
- Port 8502 is not in use
- MongoDB is connected
- Check terminal for errors

### Can't Login to Admin
**Check:**
- Username and password are correct
- Check `ADMIN_CREDENTIALS` in code
- Try default: admin/bloomwatch2024

### Farmers Not Showing
**Check:**
- MongoDB connection string
- Database has data (check MongoDB Atlas)
- No errors in logs

### Alerts Not Sending
**Check:**
- Africa's Talking credentials
- SMS balance
- Phone numbers are valid (+254...)
- Check logs for API errors

---

## 📊 Monitoring

### View Logs (Render)
1. Go to Render dashboard
2. Select service
3. Click "Logs"
4. See real-time logs

### Check Database (MongoDB Atlas)
1. Go to MongoDB Atlas
2. Click "Browse Collections"
3. See all data:
   - `farmers` collection
   - `alerts` collection
   - `ussd_sessions` collection

### Monitor SMS Usage (Africa's Talking)
1. Go to Africa's Talking dashboard
2. Check SMS balance
3. View delivery reports
4. See API usage

---

## 💡 Tips

### Free Tier Limitations
- Services sleep after 15 min inactivity
- First request takes ~30s to wake up
- Use UptimeRobot to keep awake (free)

### Security Best Practices
- Change default admin password
- Use strong passwords
- Rotate API keys regularly
- Monitor access logs
- Whitelist IPs when possible

### Performance
- MongoDB Atlas M0 (free): Good for 100-1000 farmers
- Render free tier: Good for testing
- Upgrade to paid plans for production

---

## 📚 Full Documentation

For complete details, see:
- **Full Deployment Guide:** `RENDER_DEPLOYMENT.md`
- **Admin Dashboard Code:** `app/admin_dashboard.py`
- **Environment Variables:** `env.template`
- **Render Config:** `render.yaml`

---

## ✅ Deployment Checklist

- [ ] Repository pushed to GitHub
- [ ] MongoDB Atlas configured
- [ ] Render services deployed
- [ ] Environment variables set
- [ ] Main app accessible
- [ ] Admin dashboard accessible
- [ ] USSD API responding
- [ ] Africa's Talking configured
- [ ] Test farmer created
- [ ] Test alert sent
- [ ] USSD tested on phone
- [ ] Admin password changed

---

## 🎉 You're Live!

**Main App:** https://bloomwatch-web.onrender.com  
**Admin Dashboard:** https://bloomwatch-admin.onrender.com  

Start managing farmers and sending bloom alerts! 🌾

