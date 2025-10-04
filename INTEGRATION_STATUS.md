# 🔗 BloomWatch Kenya - Integration Status

## Overview
This document explains how the different components of BloomWatch Kenya are integrated.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Google Earth Engine                  │
│  (gee_bloom_detector.js - Satellite Data Processing)   │
└─────────────────────┬───────────────────────────────────┘
                      │ Export GeoTIFF
                      ↓
┌─────────────────────────────────────────────────────────┐
│              data/exports/ (Local Storage)              │
│     Sentinel-2, Landsat 8/9, MODIS, VIIRS data         │
└─────────────────────┬───────────────────────────────────┘
                      │ Load via rasterio
                      ↓
┌─────────────────────────────────────────────────────────┐
│           Backend Processing Layer (Python)             │
│                                                           │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ gee_data_loader│  │bloom_processor│  │ MongoDB     │ │
│  │  (Load data)   │→ │(Detect blooms)│→ │ (Storage)   │ │
│  └────────────────┘  └──────────────┘  └─────────────┘ │
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │    Notification Services                           │ │
│  │  • Africa's Talking (SMS/USSD)                    │ │
│  │  • Twilio (optional)                              │ │
│  │  • SendGrid (optional)                            │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────┘
                      │ Data API
                      ↓
┌─────────────────────────────────────────────────────────┐
│           Streamlit Web Application                      │
│         (app/streamlit_app_v2.py)                       │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐   │
│  │ Landing  │→ │Register/ │→ │ Farmer Dashboard   │   │
│  │ Page     │  │ Login    │  │ (Bloom insights)   │   │
│  └──────────┘  └──────────┘  └────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                      ↕
┌─────────────────────────────────────────────────────────┐
│              USSD Interface (Flask API)                  │
│          (backend/ussd_api.py)                          │
│                                                           │
│  Feature Phone Users → *XXX# → Register/Login           │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow: GEE to Streamlit

### Step 1: GEE Export
**File**: `gee/gee_bloom_detector.js`

```javascript
// Processes satellite imagery for Kenya
- Sentinel-2: 10m resolution, 5-day revisit
- Landsat 8/9: 30m resolution, 16-day revisit
- MODIS: 1km resolution, daily
- VIIRS: 750m resolution, daily

// Calculates vegetation indices
- NDVI (Normalized Difference Vegetation Index)
- ARI (Anthocyanin Reflectance Index)

// Exports to Google Drive as GeoTIFF
Export.image.toDrive({...})
```

### Step 2: Data Loading
**File**: `backend/gee_data_loader.py`

```python
class GEEDataLoader:
    def load_kenya_data():
        # 1. Scan data/exports/ directory
        # 2. Load GeoTIFF files using rasterio
        # 3. Prioritize: Sentinel-2 > Landsat > MODIS
        # 4. Fallback to synthetic data if no exports
        return {'ndvi': array, 'ari': array, 'source': 'Sentinel-2'}
```

**Current Status**: 
- ✅ Implemented
- ⚠️ No GEE exports yet (using synthetic data)
- 💡 **Action needed**: Export data from GEE (see GEE_INTEGRATION_GUIDE.md)

### Step 3: Bloom Detection
**File**: `backend/bloom_processor.py`

```python
class BloomProcessor:
    def detect_bloom_events():
        # 1. Load data via GEEDataLoader
        # 2. Analyze NDVI time series
        # 3. Find peaks (high vegetation)
        # 4. Check ARI for flower pigments
        # 5. Adjust for Kenya crop calendar
        return {
            'bloom_months': [3, 4, 10, 11],
            'bloom_scores': [0.8, 0.7, ...],
            'health_score': 75.3
        }
```

**Current Status**: 
- ✅ Implemented and working
- ✅ Using synthetic data for demo
- 🎯 Ready for real GEE data

### Step 4: Streamlit Display
**File**: `app/streamlit_app_v2.py`

```python
# The app doesn't directly use these new modules yet
# Currently using hardcoded demo data

# TODO: Update to use:
from backend.gee_data_loader import GEEDataLoader
from backend.bloom_processor import BloomProcessor

loader = GEEDataLoader()
processor = BloomProcessor()
results = processor.detect_bloom_events('kenya')

# Display results in dashboard
st.metric("Health Score", f"{results['health_score']}/100")
st.write("Next Bloom:", results['bloom_dates'][0])
```

**Current Status**: 
- ⚠️ **Action needed**: Update Streamlit app to use new processors
- 📝 Currently uses inline demo data generation

---

## 🗄️ MongoDB Integration

### Connection Status
**File**: `backend/mongodb_service.py`

```python
class MongoDBService:
    def __init__(self):
        # Connects to MongoDB Atlas or local instance
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client['bloomwatch_kenya']
        
        # Collections:
        self.farmers      # Farmer profiles
        self.alerts       # Bloom alerts
        self.ussd_sessions # USSD state
        self.bloom_events  # Historical blooms
```

**Current Status**: 
- ✅ **CONNECTED** (based on latest test)
- ✅ Database: `bloomwatch_kenya`
- ✅ Indexes created
- 🐛 Fixed: Truth value testing error

**What was fixed**:
```python
# Before (caused error):
if not self.db:
    return

# After (correct):
if self.db is None:
    return
```

MongoDB database objects don't support boolean testing, must explicitly compare with `None`.

---

## 📱 Notification Flow

### SMS Alerts via Africa's Talking
**File**: `backend/africastalking_service.py`

```python
class AfricasTalkingService:
    def send_sms(phone, message):
        # Send SMS via Africa's Talking API
        
    def handle_ussd_request(session_id, phone, text):
        # Handle USSD menu navigation
        # Registration, login, alerts
```

**Integration Points**:
1. **Registration Confirmation**: 
   - Web → `auth_service.py` → `africastalking_service.py` → SMS sent
   - USSD → Direct SMS after registration

2. **Bloom Alerts**:
   - `bloom_processor.py` detects bloom
   - `scheduler.py` triggers alerts
   - `africastalking_service.py` sends SMS
   - MongoDB logs alert

**Current Status**:
- ✅ Africa's Talking initialized
- ✅ SMS service ready (sandbox mode)
- 📝 Need production credentials for live SMS

---

## 🔐 Authentication Flow

### Web Registration
```
User → Streamlit Form → auth_service.register_farmer()
    ↓
MongoDB.farmers.insert()
    ↓
AfricasTalking.send_registration_confirmation()
    ↓
User receives SMS with credentials
```

### USSD Registration
```
User dials *XXX# → AT sends to ussd_api.py (Flask)
    ↓
ussd_api handles menu navigation
    ↓
Saves to MongoDB
    ↓
Sends welcome SMS
```

### Login & Sessions
```
User logs in → auth_service.login()
    ↓
MongoDB.sessions.insert({token, phone, expires_at})
    ↓
Streamlit stores token in st.session_state
    ↓
All requests verified via auth_service.verify_session()
```

**Current Status**:
- ✅ Auth service implemented
- ✅ MongoDB sessions working
- ⚠️ Demo mode fallback available
- 🎯 Ready for production

---

## 🚀 Deployment Architecture

### Local Development
```
Terminal 1: MongoDB (local or Atlas)
Terminal 2: Streamlit app (port 8501)
Terminal 3: Flask USSD API (port 5000)
Terminal 4: Scheduler (background alerts)
```

### Production (Docker)
```
docker-compose.yml:
  - MongoDB container (or Atlas)
  - Streamlit container
  - Flask API container
  - Nginx reverse proxy
  - Background scheduler
```

---

## ✅ Integration Checklist

### Core Components
- [x] MongoDB service implemented
- [x] GEE data loader implemented
- [x] Bloom processor implemented
- [x] Africa's Talking service implemented
- [x] Authentication service implemented
- [x] Streamlit app v2 created
- [ ] **TODO**: Connect Streamlit to bloom processor
- [ ] **TODO**: Export real GEE data

### Data Pipeline
- [x] GEE script ready (`gee_bloom_detector.js`)
- [ ] **TODO**: Run GEE exports
- [ ] **TODO**: Download to `data/exports/`
- [x] Data loader reads exports (fallback to synthetic)
- [x] Bloom processor analyzes data
- [ ] **TODO**: Streamlit displays processed results

### User Management
- [x] Web registration working
- [x] USSD registration implemented
- [x] Session management working
- [x] Login/logout functional
- [x] Confirmation SMS implemented

### Notifications
- [x] SMS via Africa's Talking
- [x] Registration confirmations
- [ ] **TODO**: Automated bloom alerts
- [ ] **TODO**: Scheduler integration

---

## 🎯 Next Steps to Complete Integration

### 1. Update Streamlit App (Priority: HIGH)
**File to edit**: `app/streamlit_app_v2.py`

Replace the hardcoded data generation with:

```python
# At the top, after other imports
from backend.gee_data_loader import GEEDataLoader
from backend.bloom_processor import BloomProcessor

@st.cache_resource
def get_processors():
    loader = GEEDataLoader()
    processor = BloomProcessor()
    return loader, processor

# In the dashboard section
loader, processor = get_processors()
bloom_data = processor.detect_bloom_events('kenya')

# Display real data
st.metric("Health Score", f"{bloom_data['health_score']:.1f}/100")
st.metric("Data Source", bloom_data['data_source'])

for date in bloom_data['bloom_dates']:
    st.success(f"🌸 Expected bloom: {date}")
```

### 2. Export GEE Data (Priority: MEDIUM)
1. Open GEE Code Editor: https://code.earthengine.google.com/
2. Paste `gee/gee_bloom_detector.js`
3. Click **Run**
4. Go to **Tasks** tab
5. Click **RUN** on each export task
6. Wait ~10-20 minutes
7. Download from Google Drive
8. Move to `data/exports/`

**Test with**:
```bash
python backend/gee_data_loader.py
```

### 3. Test Complete Pipeline (Priority: HIGH)
```bash
# Run comprehensive test
python test_pipeline.py

# Should show all ✅ green checkmarks
```

### 4. Set Up Automated Alerts (Priority: MEDIUM)
**File to complete**: `backend/scheduler.py`

Add:
```python
from bloom_processor import BloomProcessor
from africastalking_service import AfricasTalkingService
from mongodb_service import MongoDBService

def check_and_alert():
    processor = BloomProcessor()
    results = processor.detect_bloom_events('kenya')
    
    # Get farmers in affected regions
    mongo = MongoDBService()
    farmers = mongo.get_all_farmers()
    
    # Send alerts
    at = AfricasTalkingService()
    for farmer in farmers:
        if should_alert(farmer, results):
            at.send_bloom_alert(farmer['phone'], results)
```

---

## 📚 Reference Documents

- **GEE_INTEGRATION_GUIDE.md**: Complete guide for GEE data export
- **AFRICA_TALKING_SETUP.md**: SMS/USSD setup instructions
- **SETUP_COMPLETE.md**: Full project setup guide
- **README.md**: Project overview
- **test_pipeline.py**: Run this to check all integrations

---

## 🐛 Troubleshooting

### MongoDB Connection Issues
```bash
# Check MongoDB status
python -c "from backend.mongodb_service import MongoDBService; m = MongoDBService(); print('Connected' if m.is_connected() else 'Not connected')"

# Common fixes:
# 1. Check MONGODB_URI in .env
# 2. Whitelist IP in MongoDB Atlas
# 3. Check network/firewall
```

### GEE Data Not Loading
```bash
# Check exports directory
ls -lh data/exports/

# Test data loader
python backend/gee_data_loader.py

# If no exports, app uses synthetic data automatically
```

### SMS Not Sending
```bash
# Check credentials
python -c "from backend.africastalking_service import AfricasTalkingService; at = AfricasTalkingService(); print(f'Username: {at.username}')"

# Sandbox mode limitations:
# - Only works with registered test numbers
# - For production, use real AT username (not 'sandbox')
```

---

## 📊 Current System Status

Based on latest `test_pipeline.py` run:

| Component | Status | Notes |
|-----------|--------|-------|
| MongoDB | ✅ **CONNECTED** | Fixed truth value error |
| GEE Data Loader | ✅ Working | Using synthetic data |
| Bloom Processor | ✅ Working | Ready for real data |
| Africa's Talking | ✅ Initialized | Sandbox mode |
| Notifications | ⚠️ Partial | AT works, Twilio optional |
| Authentication | ⚠️ Demo mode | Depends on MongoDB |
| Streamlit App | ✅ Running | Needs processor integration |

**Overall**: 🎯 **Core systems operational!** App can run in demo mode. Need to complete Streamlit integration and export GEE data for full production readiness.

---

**Last Updated**: October 4, 2025  
**Next Review**: After completing Streamlit integration


