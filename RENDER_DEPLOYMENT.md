# 🚀 BloomWatch Kenya - Render Deployment Guide

Complete guide to deploy BloomWatch Kenya on Render.com

---

## 📋 Prerequisites

- ✅ GitHub account
- ✅ Render account (https://render.com - free tier available)
- ✅ MongoDB Atlas account (free tier - https://www.mongodb.com/cloud/atlas)
- ✅ Africa's Talking account (for SMS/USSD)
- ✅ Your code pushed to GitHub

---

## 🎯 Architecture Overview

Your deployment will consist of:

```
┌─────────────────────────────────────────────────────┐
│  BloomWatch Kenya on Render                         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Main Web App (streamlit_app_enhanced.py)       │
│     URL: https://bloomwatch-web.onrender.com       │
│     Port: Assigned by Render                        │
│                                                     │
│  2. Admin Dashboard (admin_dashboard.py)            │
│     URL: https://bloomwatch-admin.onrender.com     │
│     Port: Assigned by Render                        │
│                                                     │
│  3. USSD API (ussd_api.py)                         │
│     URL: https://bloomwatch-ussd.onrender.com      │
│     Port: Assigned by Render                        │
│                                                     │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │  MongoDB Atlas (Database)    │
          │  Free M0 Cluster             │
          └──────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │  Africa's Talking (SMS)      │
          │  API Integration             │
          └──────────────────────────────┘
```

---

## 📦 Step 1: Prepare Your Repository

### 1.1 Update requirements.txt

```bash
# Use the Render-optimized requirements
cp requirements-render.txt requirements.txt
```

Or merge both:
```bash
cat requirements-render.txt >> requirements.txt
sort -u requirements.txt -o requirements.txt
```

### 1.2 Create .gitignore (if not exists)

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/
dist/
build/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Data
data/exports/*.tif
data/exports/*.tif.aux.xml
*.log

# MongoDB
*.wt
*.turtle

# Secrets
credentials.json
service-account.json
EOF
```

### 1.3 Commit and Push

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

---

## 🗄️ Step 2: Set Up MongoDB Atlas

### 2.1 Create Free Cluster

1. Go to https://www.mongodb.com/cloud/atlas
2. Sign up / Log in
3. Click "Build a Database"
4. Select **FREE** tier (M0)
5. Choose a region (closer to your users is better)
6. Name your cluster: `bloomwatch`
7. Click "Create"

### 2.2 Create Database User

1. In Atlas dashboard, go to **Database Access**
2. Click "Add New Database User"
3. Choose **Password** authentication
4. Username: `bloomwatch_user`
5. Password: Generate strong password (save it!)
6. Database User Privileges: **Atlas admin**
7. Click "Add User"

### 2.3 Whitelist IP Addresses

1. Go to **Network Access**
2. Click "Add IP Address"
3. Click "Allow Access from Anywhere" (for Render)
   - IP: `0.0.0.0/0`
4. Click "Confirm"

### 2.4 Get Connection String

1. Go to **Database** → **Connect**
2. Choose "Connect your application"
3. Driver: Python, Version: 3.11 or later
4. Copy the connection string:
   ```
   mongodb+srv://bloomwatch_user:<password>@bloomwatch.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. Replace `<password>` with your actual password
6. Add database name: `/bloomwatch`
   ```
   mongodb+srv://bloomwatch_user:YOUR_PASSWORD@bloomwatch.xxxxx.mongodb.net/bloomwatch?retryWrites=true&w=majority
   ```

**Save this connection string!** You'll need it for Render.

---

## 🚀 Step 3: Deploy to Render

### 3.1 Connect GitHub to Render

1. Go to https://render.com
2. Sign up / Log in
3. Click "Dashboard"
4. Connect your GitHub account

### 3.2 Deploy Using Blueprint (Recommended)

This deploys all 3 services at once!

1. Click "New" → "Blueprint"
2. Select your GitHub repository
3. Render will detect `render.yaml`
4. Name: `bloomwatch-kenya`
5. Branch: `main`
6. Click "Apply"

### 3.3 Configure Environment Variables

For **each service**, add these environment variables:

#### All Services
```
MONGODB_URI=mongodb+srv://bloomwatch_user:YOUR_PASSWORD@bloomwatch.xxxxx.mongodb.net/bloomwatch?retryWrites=true&w=majority
```

#### With Africa's Talking
```
AFRICASTALKING_USERNAME=your_username
AFRICASTALKING_API_KEY=your_api_key
AFRICASTALKING_SHORTCODE=*384*1234#
```

#### Admin Dashboard Only
```
ADMIN_PASSWORD=your_secure_admin_password
```

### 3.4 Manual Service Creation (Alternative)

If not using Blueprint:

#### Service 1: Main Web App

1. Click "New" → "Web Service"
2. Connect repository
3. Settings:
   - **Name:** `bloomwatch-web`
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app/streamlit_app_enhanced.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`
   - **Plan:** Free
4. Add environment variables (see above)
5. Click "Create Web Service"

#### Service 2: Admin Dashboard

1. Click "New" → "Web Service"
2. Same repository
3. Settings:
   - **Name:** `bloomwatch-admin`
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app/admin_dashboard.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`
   - **Plan:** Free
4. Add environment variables
5. Click "Create Web Service"

#### Service 3: USSD API

1. Click "New" → "Web Service"
2. Same repository
3. Settings:
   - **Name:** `bloomwatch-ussd`
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `cd backend && gunicorn ussd_api:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - **Plan:** Free
4. Add environment variables
5. Click "Create Web Service"

---

## 🔧 Step 4: Configure Custom Domains (Optional)

### 4.1 Get Render URLs

After deployment, you'll have:
- Main: `https://bloomwatch-web.onrender.com`
- Admin: `https://bloomwatch-admin.onrender.com`
- USSD: `https://bloomwatch-ussd.onrender.com`

### 4.2 Add Custom Domain

1. Go to service settings
2. Click "Custom Domains"
3. Add your domain (requires DNS configuration)

---

## 📱 Step 5: Configure Africa's Talking

### 5.1 Update SMS Callback

1. Go to Africa's Talking dashboard
2. Navigate to SMS → Callback URLs
3. No callback needed for sending SMS

### 5.2 Update USSD Callback

1. Go to USSD section
2. Set callback URL:
   ```
   https://bloomwatch-ussd.onrender.com/ussd
   ```
3. Save

### 5.3 Test USSD

Dial your USSD code (e.g., `*384*1234#`) on a phone!

---

## ✅ Step 6: Verify Deployment

### 6.1 Check Main App

Visit: `https://bloomwatch-web.onrender.com`

Expected:
- ✅ Landing page loads
- ✅ Can register farmer
- ✅ Can login
- ✅ Dashboard shows bloom data

### 6.2 Check Admin Dashboard

Visit: `https://bloomwatch-admin.onrender.com`

Login:
- Username: `admin`
- Password: (from ADMIN_PASSWORD env var)

Expected:
- ✅ Login works
- ✅ Can see farmer list
- ✅ Can create farmers
- ✅ Can send alerts

### 6.3 Check USSD API

Test endpoint:
```bash
curl https://bloomwatch-ussd.onrender.com/health
```

Expected:
```json
{
  "status": "healthy",
  "service": "BloomWatch Kenya USSD API"
}
```

### 6.4 Check Database Connection

From admin dashboard:
- ✅ Farmer count shows
- ✅ Can create new farmer
- ✅ Data persists after refresh

---

## 🎯 Your Live URLs

After successful deployment:

| Service | URL | Purpose |
|---------|-----|---------|
| **Main App** | `https://bloomwatch-web.onrender.com` | Farmer portal |
| **Admin** | `https://bloomwatch-admin.onrender.com` | Admin dashboard |
| **USSD API** | `https://bloomwatch-ussd.onrender.com` | USSD callbacks |

---

## ⚡ Performance Optimization

### Free Tier Limitations

Render free tier services:
- ✅ Spin down after 15 minutes of inactivity
- ✅ Take ~30 seconds to wake up
- ✅ 750 hours/month free

### Keep Services Awake (Optional)

Use **UptimeRobot** (free):
1. Sign up at https://uptimerobot.com
2. Add monitors for your URLs
3. Set check interval: 5 minutes
4. Services stay awake!

---

## 🔒 Security Checklist

- [ ] Change default admin password
- [ ] Set strong ADMIN_PASSWORD in Render
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS (automatic on Render)
- [ ] Whitelist only necessary IPs in MongoDB Atlas
- [ ] Rotate API keys regularly
- [ ] Monitor logs for suspicious activity

---

## 📊 Monitoring

### View Logs

1. Go to Render dashboard
2. Select service
3. Click "Logs" tab
4. Real-time logs!

### Check Metrics

1. Service dashboard shows:
   - CPU usage
   - Memory usage
   - Request count
   - Response times

---

## 🐛 Troubleshooting

### Service Won't Start

**Check logs for:**
```
ModuleNotFoundError: No module named 'xxx'
```
**Fix:** Add missing module to `requirements.txt`

### Database Connection Error

**Check:**
- MONGODB_URI is correct
- Password has no special characters (or URL encode them)
- IP whitelist includes `0.0.0.0/0`

### Streamlit Port Binding Error

**Ensure start command includes:**
```
--server.port=$PORT --server.address=0.0.0.0
```

### Africa's Talking Not Receiving USSD

**Check:**
- USSD callback URL is correct
- Service is running (check Render logs)
- Test with: `curl https://your-ussd-url.onrender.com/health`

---

## 💰 Costs

### Free Tier (Sufficient for Testing)

| Service | Cost |
|---------|------|
| Render Web Services (3) | FREE (750 hrs each/month) |
| MongoDB Atlas M0 | FREE (512MB storage) |
| Africa's Talking Sandbox | FREE (testing only) |
| **Total** | **$0/month** |

### Production (Recommended)

| Service | Cost |
|---------|------|
| Render Starter (3 services) | $7 × 3 = $21/month |
| MongoDB Atlas M10 | $57/month |
| Africa's Talking (SMS + USSD) | ~$100-200/month |
| **Total** | **~$178-278/month** |

---

## 🔄 Continuous Deployment

Changes you push to GitHub automatically deploy to Render!

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Render automatically:
# 1. Detects push
# 2. Builds new version
# 3. Deploys if build succeeds
# 4. Rolls back if deployment fails
```

---

## 📚 Additional Resources

- **Render Docs:** https://render.com/docs
- **MongoDB Atlas:** https://docs.atlas.mongodb.com/
- **Streamlit Deployment:** https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app
- **Africa's Talking:** https://developers.africastalking.com/

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] MongoDB Atlas cluster created
- [ ] Database user created
- [ ] IP whitelist configured (0.0.0.0/0)
- [ ] Connection string obtained
- [ ] Render account created
- [ ] GitHub connected to Render
- [ ] Blueprint deployed (or manual services)
- [ ] Environment variables configured
- [ ] Main app accessible
- [ ] Admin dashboard accessible
- [ ] USSD API responding
- [ ] Africa's Talking callback configured
- [ ] USSD tested on phone
- [ ] Admin password changed
- [ ] Monitoring set up (optional)

---

## 🎉 You're Live!

Your BloomWatch Kenya platform is now deployed and accessible worldwide!

**Main App:** `https://bloomwatch-web.onrender.com`  
**Admin:** `https://bloomwatch-admin.onrender.com`  
**USSD:** Dial `*384*1234#` (or your code)

Share these URLs with farmers and start helping them track bloom events! 🌾

---

## 🆘 Need Help?

1. Check Render logs
2. Check MongoDB Atlas metrics
3. Test each service individually
4. Review this guide again
5. Check Africa's Talking callback logs

**Common Issues:**
- Service sleeping: Wait 30s for wake-up
- Database timeout: Check connection string
- USSD not working: Verify callback URL
- Admin can't login: Check ADMIN_PASSWORD env var

