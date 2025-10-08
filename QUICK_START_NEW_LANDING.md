# 🚀 Quick Start Guide - New Landing Page

## Welcome to the Enhanced BloomWatch Kenya Landing Page!

This guide will help you get the new landing page up and running in just a few minutes.

---

## ✅ Prerequisites

- Python 3.11+
- Git
- Virtual environment tool (venv)
- OpenAI API key (optional, for Flora chatbot)

---

## 📦 Installation Steps

### 1. Clone & Setup

```bash
# Clone the repository
git clone git@github.com:geoffreyyogo/bloom-detector.git
cd bloom-detector

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**New packages included**:
- `openai==1.54.3` - For Flora AI chatbot
- `streamlit-lottie==0.0.5` - For animations
- `Pillow==10.4.0` - For image handling

### 3. Configure Environment Variables

```bash
# Copy the template
cp env.template .env

# Edit .env file and add your keys
nano .env  # or use your preferred editor
```

**Required for Flora (optional)**:
```env
OPENAI_API_KEY=sk-proj-your_actual_openai_api_key_here
```

**Other keys (optional for full functionality)**:
```env
MONGODB_URI=your_mongodb_connection_string
AFRICASTALKING_USERNAME=your_at_username
AFRICASTALKING_API_KEY=your_at_api_key
```

---

## 🎯 Running the Application

### Start the Streamlit App

```bash
streamlit run app/streamlit_app_enhanced.py
```

The app will open automatically in your browser at `http://localhost:8501`

---

## 🌟 New Features Tour

### 1. Hero Section
- **What to see**: Swahili tagline "Track Maua, Master Ukulima"
- **What to try**: Click "Get Started" or "Log In" buttons
- **Note**: USSD code `*384*42434#` displayed prominently

### 2. Kenya Climate Map
- **What to see**: Interactive map with 10 major counties
- **What to try**: Click on county markers to see climate data
  - Bloom percentage
  - Temperature
  - Humidity
  - Rainfall
- **Colors**:
  - 🟢 Green = High bloom (≥80%)
  - 🟠 Orange = Moderate (60-79%)
  - 🔴 Red = Low (<60%)

### 3. Flora AI Chatbot
- **What to see**: Mock chat interface showing sample conversation
- **What to try**: 
  - Click "Chat with Flora Now" button
  - If OpenAI key is configured, ask Flora questions like:
    - "When should I plant maize in Nyeri?"
    - "What crops grow best in Nakuru?"
    - "How do I prepare for the long rains?"

**Testing Flora**:
```bash
# Make sure you have an OpenAI API key
export OPENAI_API_KEY=sk-proj-your_key_here  # Linux/Mac
set OPENAI_API_KEY=sk-proj-your_key_here     # Windows

# Then run the app
streamlit run app/streamlit_app_enhanced.py
```

### 4. Stat Counters
- **What to see**: Large animated statistics
  - 500+ farmers registered
  - 25% average yield increase
  - 47 counties covered
  - $500 extra income per season
- **Design**: Clean cards with icons and context

### 5. Testimonials
- **What to see**: Success stories from 3 farmers
  - Jane Wanjiru (Nakuru - Maize)
  - Peter Kamau (Kericho - Coffee)
  - Mary Atieno (Machakos - Vegetables)
- **Featured**: John Odhiambo's detailed success story

### 6. USSD Phone Demo
- **What to see**: Realistic phone mockup showing USSD dial
- **Left side**: Step-by-step USSD instructions
- **Center**: Animated phone screen
- **Right side**: Sample SMS alert format

### 7. Pictures Carousel
- **What to see**: 6 images of Kenyan agriculture
  - Maize fields
  - Coffee blooms
  - Tea plantations
  - Mount Kenya backdrop
  - Kenyan farmers at work
- **What to try**: Navigate through tabs to see all images

### 8. Footer
- **What to see**: 
  - Quick links to app downloads
  - Partner logos (NASA, Google Earth Engine, etc.)
  - GitHub repository link
  - Social media handles
  - Contact information

---

## 🎨 Testing Different Modes

### Dark Mode
- Click the 🌙 button in top-right corner
- Watch colors adapt automatically
- All text remains readable

### Language Switch
- Use the dropdown in top-right (English/Kiswahili)
- Some UI elements will translate
- Flora supports both languages

### Mobile View
- Resize your browser to mobile width (<768px)
- Notice responsive layout changes:
  - Single-column layouts
  - Larger buttons
  - Simplified navigation

---

## 🔍 Troubleshooting

### Flora Not Working?

**Issue**: "Flora is currently unavailable"

**Solutions**:
1. Check if OpenAI API key is in `.env` file
2. Verify key format: `OPENAI_API_KEY=sk-proj-...`
3. Check API key is valid at https://platform.openai.com
4. Restart Streamlit app after adding key

```bash
# Restart the app
# Press Ctrl+C to stop
# Then run again:
streamlit run app/streamlit_app_enhanced.py
```

### Map Not Loading?

**Issue**: Kenya map shows blank or loading forever

**Solutions**:
1. Check internet connection (map tiles load from CDN)
2. Clear browser cache
3. Try incognito/private browsing mode
4. Check for ad-blockers (may block map tiles)

### Images Not Showing?

**Issue**: Carousel images show placeholders

**Solutions**:
1. Check internet connection (images load from Unsplash)
2. Wait a few seconds (images lazy-load)
3. Refresh the page
4. Fallback: Gradient placeholders with captions will show

### Import Errors?

**Issue**: "ModuleNotFoundError: No module named 'openai'"

**Solutions**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall requirements
pip install -r requirements.txt

# Verify installation
pip list | grep openai
```

---

## 🧪 Quick Testing Checklist

Run through these to verify everything works:

- [ ] Page loads without errors
- [ ] Hero section displays with gradient background
- [ ] "Get Started" button navigates to registration
- [ ] "Log In" button navigates to login page
- [ ] Kenya map shows all 10 counties with markers
- [ ] Click on a map marker - popup shows climate data
- [ ] Flora section displays mock chat
- [ ] "Chat with Flora" button toggles live demo
- [ ] Stat counters show: 500+, 25%, 47, $500
- [ ] Three testimonial cards display
- [ ] Featured farmer spotlight shows John's story
- [ ] Phone mockup renders correctly
- [ ] USSD code visible: *384*42434#
- [ ] Sample SMS alert displays
- [ ] Image carousel has 6 tabs
- [ ] Footer has 4 columns with links
- [ ] GitHub link points to: geoffreyyogo/bloom-detector
- [ ] Dark mode toggle works
- [ ] Language selector switches between EN/SW

---

## 📱 Mobile Testing

### Test on Real Device

```bash
# Get your local IP address
# Linux/Mac:
ifconfig | grep "inet "
# Windows:
ipconfig

# Run Streamlit on network
streamlit run app/streamlit_app_enhanced.py --server.address 0.0.0.0

# Access from phone browser:
# http://YOUR_IP_ADDRESS:8501
```

### Responsive Breakpoints

Test these widths in browser DevTools:
- **Desktop**: 1920x1080
- **Laptop**: 1366x768
- **Tablet**: 768x1024
- **Mobile Large**: 414x896 (iPhone 11)
- **Mobile Small**: 375x667 (iPhone SE)

---

## 🚀 Development Workflow

### Making Changes

```bash
# 1. Edit the file
nano app/streamlit_app_enhanced.py

# 2. Save changes

# 3. Streamlit will auto-reload
# Watch terminal for "Source file changed" message

# 4. Browser will refresh automatically
```

### Adding New Sections

To add a new section to the landing page:

1. **Create section function**:
```python
def show_new_section():
    """Your new section"""
    st.markdown("## New Section Title")
    # Your content here
```

2. **Add to landing_page()**:
```python
def landing_page():
    # ... existing sections ...
    
    # Add your section
    show_new_section()
    
    st.markdown("<br>", unsafe_allow_html=True)
```

3. **Save and test**

### Customizing Flora

Edit the system prompt in `get_flora_response()`:

```python
system_prompt = """You are Flora, an AI agricultural assistant...
[Customize prompt here]
"""
```

---

## 📊 Monitoring Usage

### View Logs

```bash
# Terminal will show:
# - Page loads
# - Button clicks
# - Flora API calls
# - Any errors

# Watch for:
# "Flora is thinking..." - AI request sent
# "🌺 Flora says:" - Response received
```

### Check API Usage

- OpenAI Dashboard: https://platform.openai.com/usage
- Monitor Flora query costs
- GPT-4o-mini is cost-effective (~$0.0001 per query)

---

## 🎓 Learning Resources

### Streamlit Documentation
- https://docs.streamlit.io

### OpenAI API Guide
- https://platform.openai.com/docs

### Folium (Maps)
- https://python-visualization.github.io/folium/

### Design Inspiration
- Material Design: https://material.io
- Kenya Tourism: https://magicalkenya.com

---

## 💡 Tips & Best Practices

### Performance
- Images auto-lazy-load
- Map renders on-demand
- Flora responses cached per session

### Accessibility
- All buttons have min 44px tap targets
- High contrast text for readability
- Keyboard navigation supported

### Cultural Relevance
- Use Swahili greetings: "Habari", "Karibu"
- Reference local crops: maize, beans, coffee, tea
- Mention Kenyan regions: Nakuru, Eldoret, Kericho
- Include local seasons: long rains, short rains

---

## 🔗 Useful Links

- **GitHub Repo**: https://github.com/geoffreyyogo/bloom-detector
- **Landing Page Guide**: See `LANDING_PAGE_GUIDE.md`
- **Environment Template**: See `env.template`
- **Requirements**: See `requirements.txt`

---

## 🆘 Getting Help

### Issues?

1. **Check this guide first**
2. **Review `LANDING_PAGE_GUIDE.md`** for detailed info
3. **Check GitHub Issues**: https://github.com/geoffreyyogo/bloom-detector/issues
4. **Create new issue** with:
   - Error message
   - Steps to reproduce
   - Your environment (OS, Python version)
   - Screenshots if applicable

### Contact

- **Email**: hello@bloomwatch.ke
- **GitHub**: @geoffreyyogo
- **Twitter**: @BloomWatchKE

---

## ✅ You're All Set!

The new landing page is ready to impress visitors and convert farmers! 

**Next Steps**:
1. Test all sections thoroughly
2. Get OpenAI API key for Flora demo
3. Customize content for your needs
4. Deploy to production when ready

**Deployment Guide**: See `DEPLOYMENT_GUIDE.md`

---

*🌾 Happy Farming! Track Maua, Master Ukulima! 🌾*

**Last Updated**: January 2025





