# Render Root Directory - Complete Guide

## 🎯 What is Root Directory?

The `rootDirectory` setting tells Render to run all commands from a specific subdirectory instead of the repository root.

### Benefits:
- ✅ Deploy only part of a monorepo
- ✅ Auto-deploy only when files in that directory change
- ✅ Keep each service isolated
- ✅ Separate dependencies per service

---

## 📊 Your Current Setup (Recommended)

**You DON'T need to set `rootDirectory`** because your current structure works perfectly:

```
bloom-detector/              ← Render runs from here
├── app/
│   ├── streamlit_app_enhanced.py
│   └── admin_dashboard.py
├── backend/
│   └── ussd_api.py
├── requirements.txt         ← Shared dependencies
└── render.yaml
```

### Current render.yaml (Works Great!):
```yaml
services:
  - type: web
    name: bloomwatch-web
    # No rootDirectory needed
    startCommand: streamlit run app/streamlit_app_enhanced.py ...
    
  - type: web
    name: bloomwatch-ussd
    # No rootDirectory needed
    startCommand: cd backend && gunicorn ussd_api:app ...
```

**✅ This is the best approach for your project!**

---

## 🔄 Alternative: Monorepo Structure

If you reorganize your project, you could use `rootDirectory`:

### New Structure:
```
bloom-detector/
├── services/
│   ├── web/
│   │   ├── requirements.txt
│   │   ├── app.py
│   │   └── ...
│   ├── admin/
│   │   ├── requirements.txt
│   │   ├── admin.py
│   │   └── ...
│   └── api/
│       ├── requirements.txt
│       ├── ussd_api.py
│       └── ...
└── shared/
    └── common_code/
```

### render.yaml with rootDirectory:
```yaml
services:
  - type: web
    name: bloomwatch-web
    rootDirectory: ./services/web
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run app.py ...
    
  - type: web
    name: bloomwatch-admin
    rootDirectory: ./services/admin
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run admin.py ...
    
  - type: web
    name: bloomwatch-api
    rootDirectory: ./services/api
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn ussd_api:app ...
```

---

## 🤔 Should You Use Root Directory?

### ✅ Use Root Directory When:
- Each service has its own `requirements.txt`
- Services are in separate folders
- You want to deploy only when specific folders change
- You have a monorepo with multiple projects

### ❌ Don't Use Root Directory When:
- ✅ **Your current setup** - All services share dependencies
- Services run from repository root
- You use `cd` in start commands
- Simple project structure

---

## 📝 Example Scenarios

### Scenario 1: Your Current Setup ✅ RECOMMENDED
```yaml
# render.yaml (no rootDirectory)
services:
  - type: web
    name: bloomwatch-web
    startCommand: streamlit run app/streamlit_app_enhanced.py
    # Works because 'app/' is relative to root
```

**Deploys when:** Any file in repo changes  
**Dependencies:** Root `requirements.txt`

---

### Scenario 2: Using Root Directory for USSD API

**Current way (works fine):**
```yaml
startCommand: cd backend && gunicorn ussd_api:app
```

**Alternative with rootDirectory:**
```yaml
rootDirectory: ./backend
startCommand: gunicorn ussd_api:app
# No 'cd' needed since we're already in backend/
```

**Benefits of rootDirectory approach:**
- ✅ Only redeploys when `backend/` files change
- ✅ Cleaner start command
- ✅ Service isolated to backend folder

**To use this approach:**

1. **Create `backend/requirements.txt`:**
```bash
# Copy dependencies needed by backend
cat > backend/requirements.txt << 'EOF'
flask==3.0.0
gunicorn==21.2.0
pymongo==4.6.1
africastalking==1.2.7
python-dotenv==1.0.0
bcrypt==4.1.2
certifi==2023.11.17
EOF
```

2. **Update `render.yaml`:**
```yaml
- type: web
  name: bloomwatch-ussd
  rootDirectory: ./backend
  buildCommand: pip install -r requirements.txt
  startCommand: gunicorn ussd_api:app --bind 0.0.0.0:$PORT
```

---

## 🛠️ How to Implement (If You Want To)

### Option 1: Keep Current Setup ✅ RECOMMENDED
**No changes needed!** Your current `render.yaml` is perfect.

### Option 2: Use Root Directory for Backend Only

**Step 1:** Create backend requirements
```bash
cat > backend/requirements.txt << 'EOF'
flask==3.0.0
gunicorn==21.2.0
pymongo==4.6.1
africastalking==1.2.7
python-dotenv==1.0.0
bcrypt==4.1.2
certifi==2023.11.17
numpy==1.24.3
scipy==1.11.4
requests==2.31.0
python-dateutil==2.8.2
EOF
```

**Step 2:** Update `render.yaml` for USSD service
```yaml
- type: web
  name: bloomwatch-ussd
  rootDirectory: ./backend  # Add this line
  buildCommand: pip install -r requirements.txt
  startCommand: gunicorn ussd_api:app --bind 0.0.0.0:$PORT
  # Remove 'cd backend &&' from start command
```

**Step 3:** Push changes
```bash
git add backend/requirements.txt render.yaml
git commit -m "Use rootDirectory for USSD API"
git push
```

### Option 3: Full Monorepo Structure

This requires significant reorganization. Only do this if you're building a large project with many services.

---

## 📊 Comparison

| Aspect | Current Setup | With Root Directory |
|--------|---------------|---------------------|
| **Simplicity** | ✅ Very simple | ⚠️ More complex |
| **Dependencies** | Shared | Separate per service |
| **Auto-deploy** | Any file change | Only when service folder changes |
| **Start command** | `cd backend && ...` | Just `...` |
| **Best for** | **Your project** ✅ | Large monorepos |

---

## 💡 My Recommendation

**Keep your current setup!** Here's why:

✅ **Pros of current approach:**
- Simple and clear
- All dependencies in one place
- Easy to manage
- Works perfectly for your project size
- No need to duplicate dependencies

❌ **Cons of rootDirectory for your project:**
- More complex
- Need separate requirements.txt files
- More configuration to maintain
- Doesn't provide significant benefits for your use case

---

## 🔍 When to Reconsider

You might want to use `rootDirectory` in the future if:

1. Your project grows significantly
2. Services have very different dependencies
3. You want to deploy services independently
4. You have multiple teams working on different services
5. You need faster deploys (only affected service rebuilds)

---

## 📚 Summary

### Current Setup (✅ Use This):
```yaml
# render.yaml
services:
  - type: web
    startCommand: streamlit run app/streamlit_app_enhanced.py
    # No rootDirectory - runs from repo root

  - type: web
    startCommand: cd backend && gunicorn ussd_api:app
    # No rootDirectory - uses 'cd' to change directory
```

**Benefits:**
- ✅ Simple
- ✅ Works great
- ✅ Easy to maintain
- ✅ Single source of dependencies

### With Root Directory (Optional):
```yaml
# render.yaml
services:
  - type: web
    rootDirectory: ./backend
    startCommand: gunicorn ussd_api:app
    # rootDirectory set - runs from backend/
```

**When to use:**
- Large monorepo
- Separate dependencies per service
- Want selective auto-deploys

---

## ✅ Action Items

**For your project, I recommend:**

- [ ] ✅ Keep current `render.yaml` as-is
- [ ] ✅ Use the existing setup (no rootDirectory)
- [ ] ✅ Deploy with current configuration

**Only if you want to experiment:**

- [ ] Create `backend/requirements.txt`
- [ ] Add `rootDirectory: ./backend` to USSD service
- [ ] Test deployment
- [ ] Compare with current setup

---

## 🎉 Conclusion

**You're already doing it right!** Your current setup without `rootDirectory` is perfect for BloomWatch Kenya. The `rootDirectory` setting is useful for large monorepos, but your project structure is optimized and doesn't need it.

**Just deploy with your current `render.yaml` and you'll be fine!** 🚀

















