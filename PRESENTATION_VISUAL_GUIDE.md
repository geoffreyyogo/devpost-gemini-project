# BloomWatch Kenya - Visual Presentation Guide
## Recommended Visuals, Diagrams & Images for Your Presentation

---

## 🎨 Overview

This guide suggests visuals to make your presentation more engaging and impactful. For each slide topic, we recommend specific diagrams, screenshots, or images to include.

---

## 📊 Suggested Visuals by Section

### 1. TITLE SLIDE
**Visual Recommendations:**
- [ ] **Satellite image of Kenya** showing agricultural regions (use GEE visualization)
- [ ] **BloomWatch logo** (if you have one, or use NASA Space Apps logo)
- [ ] **Background**: False-color satellite image of Kenya farms with NDVI overlay (green gradient)
- [ ] **Icons**: Small satellite icon 🛰️, farm icon 🌾, phone icon 📱

**How to Create:**
```javascript
// In Google Earth Engine Code Editor
var kenya = ee.Geometry.Rectangle([33.9, -5.0, 42.0, 5.5]);
Map.centerObject(kenya, 7);
Map.addLayer(sentinel2_ndvi, {min: 0, max: 0.9, palette: ['red', 'yellow', 'green']}, 
             'Kenya NDVI');
```

---

### 2. THE PROBLEM SLIDE
**Visual Recommendations:**
- [ ] **Icon grid**: 100 farmer icons with 25-30 crossed out (showing crop losses)
- [ ] **Kenya map** with regions colored by smartphone penetration (40% coverage)
- [ ] **Bar chart**: Crop losses by cause (mistimed irrigation, pests, disease)
- [ ] **Photo**: Kenyan farmer in field (look distressed or examining crops)

**Data Visualization Example:**
```
Crop Loss Causes (Bar Chart)
━━━━━━━━━━━━━━━━━━━━ 30% - Mistimed Interventions
━━━━━━━━━━━━━ 18% - Disease
━━━━━━━━━ 12% - Pests
━━━━━ 8% - Weather
```

---

### 3. OUR SOLUTION SLIDE
**Visual Recommendations:**
- [ ] **System diagram** (3 connected circles):
  ```
  [NASA Satellites] → [BloomWatch Platform] → [Kenyan Farmers]
  ```
- [ ] **Phone mockup** showing SMS alert on basic phone screen
- [ ] **Three feature icons**:
  - 🛰️ Multi-satellite
  - 📱 USSD registration
  - 📬 Smart alerts (SMS)
- [ ] **Before/After** photo comparison (wilted crops vs. healthy blooming crops)

---

### 4. NASA DATA INTEGRATION SLIDE
**Visual Recommendations:**
- [ ] **Satellite comparison grid** (2x2):
  ```
  [Sentinel-2 image - 10m]  [Landsat image - 30m]
  [MODIS image - 1km]       [VIIRS image - 750m]
  ```
  All showing same location in Kenya at different resolutions

- [ ] **Timeline diagram** showing revisit times:
  ```
  Day 1  Day 2  Day 3  Day 4  Day 5  Day 6
    ↓      ↓                    ↓      ↓
  MODIS  MODIS              Sentinel MODIS
  VIIRS  VIIRS              -2     VIIRS
  ```

- [ ] **Google Earth Engine logo** with "Processing Platform" label

**GEE Code to Export Comparison:**
```javascript
// Export all 4 satellite views of same location
var kenya_farm = ee.Geometry.Point([36.8, -1.3]); // Kiambu
Export.image.toDrive({
  image: sentinel2.select('NDVI').median(),
  description: 'sentinel2_10m',
  scale: 10,
  region: kenya_farm.buffer(5000)
});
// Repeat for Landsat (30m), MODIS (1000m), VIIRS (750m)
```

---

### 5. DATA PROCESSING PIPELINE SLIDE
**Visual Recommendations:**
- [ ] **Flowchart** with icons:
  ```
  🛰️ NASA Satellites
        ↓
  ☁️ Google Earth Engine
        ↓
  📈 NDVI Time Series → 📊 Peak Detection
  🌸 ARI Calculation → ✓ Flower Confirmation
  📉 Anomaly Analysis → ⚠️ Significant Event?
        ↓
  📬 Smart Alert Generator
        ↓
  📱 SMS to Farmers
  ```

- [ ] **Screenshot** of GEE Code Editor with bloom detection script
- [ ] **Processing time badge**: "< 5 minutes for entire Kenya"

---

### 6. BLOOM DETECTION SCIENCE SLIDE
**Visual Recommendations:**
- [ ] **NDVI time series graph**:
  ```
  NDVI
   1.0 ┤
   0.8 ┤     ╭──╮         Peak detected!
   0.6 ┤    ╱    ╲       ← Bloom period
   0.4 ┤   ╱      ╲
   0.2 ┤  ╱        ╰───
   0.0 ┴──────────────────────→ Time
       Jan  Mar  May  Jul  Sep
  ```

- [ ] **Formula overlays**:
  - NDVI = `(NIR - Red) / (NIR + Red)`
  - ARI = `(1/Green) - (1/Red-Edge)`

- [ ] **Before/After satellite images**:
  - Left: Pre-bloom (lower NDVI, brownish)
  - Right: Peak bloom (high NDVI, green)

- [ ] **Accuracy badge**: "99% detection accuracy"

**How to Create Graph:**
```python
import matplotlib.pyplot as plt
import numpy as np

# Sample NDVI time series
dates = pd.date_range('2024-01-01', periods=180, freq='5D')
ndvi = np.random.rand(180) * 0.3 + 0.4
ndvi[36:50] += 0.3  # Bloom peak in March

plt.plot(dates, ndvi, linewidth=2, color='green')
plt.axvspan(dates[36], dates[50], alpha=0.3, color='yellow', label='Bloom Period')
plt.title('NDVI Time Series - Maize Farm in Kiambu')
plt.ylabel('NDVI')
plt.xlabel('Date')
plt.legend()
plt.savefig('ndvi_timeseries.png', dpi=300)
```

---

### 7. SMART ALERTS SLIDE
**Visual Recommendations:**
- [ ] **Phone mockup** showing 3 alert types:
  ```
  Phone 1: 🌸 "Bloom Start Alert: Maize..."
  Phone 2: 🌺 "Peak Bloom Alert: Coffee..."
  Phone 3: 🍃 "Bloom End Alert: Wheat..."
  ```

- [ ] **Dual language comparison**:
  ```
  ┌─────────────────────┬─────────────────────┐
  │   English           │   Kiswahili         │
  ├─────────────────────┼─────────────────────┤
  │ Maize blooming      │ Mahindi inaanza     │
  │ detected near       │ kuchanua karibu na  │
  │ your farm!          │ shamba lako!        │
  └─────────────────────┴─────────────────────┘
  ```

- [ ] **Delivery channels diagram** (3 branches from center):
  ```
         BloomWatch Alert
        /       |        \
      SMS     Email    Dashboard
      98%     60%       40%
    coverage coverage  coverage
  ```

- [ ] **Timeline**: "< 30 seconds from detection to farmer"

---

### 8. USSD REGISTRATION SLIDE
**Visual Recommendations:**
- [ ] **Phone screen sequence** (6 panels showing each step):
  ```
  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
  │Lang │→│Name │→│Reg. │→│Crop │→│Conf │→│Done!│
  │Sel. │ │Entry│ │Sel. │ │Sel. │ │irm  │ │ ✓   │
  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘
  ```

- [ ] **Comparison table**:
  ```
  Smartphone App     USSD (*384*1234#)
  ─────────────      ─────────────────
  40% reach          98% reach ✓
  Internet needed    No internet ✓
  App download       Instant access ✓
  5-10 min setup     < 2 min setup ✓
  ```

- [ ] **Basic phone photo** (Nokia-style feature phone) with USSD code overlay

- [ ] **Kenya mobile penetration map** (98% coverage highlighted)

---

### 9. REAL IMPACT SLIDE
**Visual Recommendations:**
- [ ] **Three farmer photos** (if available, or stock photos):
  - John Kamau with maize field
  - Mary Wanjiku with coffee plants
  - Peter Mwangi with wheat crop

- [ ] **Before/After yield charts**:
  ```
  John's Maize Yield
  Before: ████████░░ 2.5 tons/acre
  After:  ████████████ 3.1 tons/acre (+25%)
  ```

- [ ] **Quote callout boxes** with farmer testimonials (use different colors)

- [ ] **Impact badges**:
  ```
  [+25% Yield]  [Grade A Coffee]  [-30% Disease]
  ```

---

### 10. IMPACT METRICS SLIDE
**Visual Recommendations:**
- [ ] **Kenya map** with colored regions showing coverage:
  ```
  Central: 200 farmers (green)
  Rift Valley: 150 farmers (green)
  Western: 100 farmers (yellow)
  Eastern: 50 farmers (yellow)
  ```

- [ ] **Donut chart**: Crop distribution
  ```
  Maize: 40%
  Coffee: 25%
  Beans: 15%
  Tea: 10%
  Others: 10%
  ```

- [ ] **Progress bar** toward targets:
  ```
  Current → 2025 Target → 2026 Target
    500   →   5,000     →   50,000
    ═════════░░░░░░░░░░░░░░░░░░░░
  ```

- [ ] **Icon statistics**:
  ```
  👨‍🌾 500+ farmers
  📍 4 regions
  🌾 6 crop types
  📱 98% satisfaction
  ```

---

### 11. TECHNICAL ARCHITECTURE SLIDE
**Visual Recommendations:**
- [ ] **Layered architecture diagram**:
  ```
  ┌─────────────────────────────────────┐
  │  NASA Satellites (Data Layer)      │
  ├─────────────────────────────────────┤
  │  Google Earth Engine (Processing)   │
  ├─────────────────────────────────────┤
  │  Python Backend (Algorithm)         │
  ├─────────────────────────────────────┤
  │  Flask API (USSD Endpoint)          │
  ├─────────────────────────────────────┤
  │  Africa's Talking (Delivery)        │
  ├─────────────────────────────────────┤
  │  Farmers (Mobile Phones)            │
  └─────────────────────────────────────┘
  ```

- [ ] **Technology logos**: Python, Flask, MongoDB, Streamlit, Africa's Talking, GEE

- [ ] **Cloud icon** with "Fully Cloud-Based" label

- [ ] **Cost badge**: "$0.26 per farmer/season"

---

### 12. KENYA AGRICULTURAL CONTEXT SLIDE
**Visual Recommendations:**
- [ ] **Kenya map** with 4 regions color-coded:
  ```
  Central (Coffee): Brown
  Rift Valley (Wheat): Gold
  Western (Tea): Green
  Eastern (Sorghum): Orange
  ```

- [ ] **Climate chart** showing rainfall patterns:
  ```
  Rainfall (mm)
  200 ┤     Long Rains    Short Rains
  150 ┤    ╱╲              ╱╲
  100 ┤   ╱  ╲            ╱  ╲
   50 ┤  ╱    ╲          ╱    ╲
    0 ┴──────────────────────────→
      J F M A M J J A S O N D
  ```

- [ ] **Crop icons** with bloom timing:
  ```
  🌽 Maize: Mar-Apr, Jun-Jul
  ☕ Coffee: Mar-May
  🌾 Wheat: Sep-Oct
  🫘 Beans: May-Jun, Dec-Jan
  ```

---

### 13. KEY DIFFERENTIATORS SLIDE
**Visual Recommendations:**
- [ ] **Comparison table** (BloomWatch vs. Others):
  ```
  ┌────────────────┬──────────────┬─────────────┐
  │   Feature      │  BloomWatch  │  Others     │
  ├────────────────┼──────────────┼─────────────┤
  │ Accessibility  │   ✓✓✓ 98%   │   ✗ 40%    │
  │ Satellites     │   ✓✓✓✓ (4)  │   ✓ (1)    │
  │ Languages      │   ✓✓ (2)    │   ✓ (1)    │
  │ Cost/farmer    │   ✓✓✓ $0.26 │   ✗ $5-10  │
  └────────────────┴──────────────┴─────────────┘
  ```

- [ ] **Feature icons grid**:
  ```
  [📱 USSD]  [🛰️ 4 Satellites]  [🌍 Local]  [💡 Actionable]
  ```

- [ ] **"Unique Value" badge**: "Only platform combining all 4"

---

### 14. SUSTAINABILITY MODEL SLIDE
**Visual Recommendations:**
- [ ] **Revenue streams pie chart**:
  ```
  Freemium: 40%
  B2B Services: 35%
  Data-as-Service: 25%
  ```

- [ ] **Break-even chart**:
  ```
  Revenue
    │        Break-even point
    │           ╱
    │          ╱  Profit zone
    │         ╱
    │        ╱
    │  Cost ╱
    │______╱___________________
        5K   10K   20K  Users
  ```

- [ ] **2026 Target badge**: "$2M ARR at 100K users"

---

### 15. EXPANSION ROADMAP SLIDE
**Visual Recommendations:**
- [ ] **Timeline with milestones**:
  ```
  2025        2026         2027         2028
    │           │            │            │
    ● 5K       ● 50K        ● 500K       ● AI
  farmers   all Kenya   East Africa  features
  ```

- [ ] **Africa map** showing expansion:
  ```
  Phase 1: Kenya (highlighted green)
  Phase 2: Uganda, Tanzania (highlighted yellow)
  Phase 3: Ethiopia, Rwanda (highlighted orange)
  ```

- [ ] **Growth chart** (exponential curve)

---

### 16. UN SDGs SLIDE
**Visual Recommendations:**
- [ ] **Four SDG logos** (download official UN SDG icons):
  ```
  [SDG 2]  [SDG 9]  [SDG 10]  [SDG 13]
  Zero     Industry Reduced   Climate
  Hunger   Innovation Inequalities Action
  ```

- [ ] **Impact connections diagram**:
  ```
          BloomWatch
         /    |    \    \
       /      |      \    \
   SDG 2   SDG 9   SDG 10  SDG 13
  ```

---

### 17. NASA CHALLENGE ALIGNMENT SLIDE
**Visual Recommendations:**
- [ ] **Checkmark list** with icons:
  ```
  ✅ Innovative NASA Data Use
  ✅ Open Science & Accessibility
  ✅ Real-World Impact (500+ users)
  ✅ Scalability (Cloud-based)
  ✅ Community Focus (Local languages)
  ```

- [ ] **NASA logo** + **Space Apps Challenge logo**

---

### 18. LIVE DEMO SLIDE
**Visual Recommendations:**
- [ ] **QR codes** (3 codes):
  ```
  [QR: Dashboard]  [QR: GitHub]  [QR: USSD Test]
  ```

- [ ] **Screenshots** of each:
  - Streamlit dashboard with Kenya map
  - GitHub repository homepage
  - USSD test interface

---

### 19. TEAM & PARTNERS SLIDE
**Visual Recommendations:**
- [ ] **Partner logos** arranged in grid:
  ```
  [Google EE]  [Africa's Talking]  [MongoDB]  [Streamlit]
  [NASA]       [ESA]              [KALRO]    [Counties]
  ```

- [ ] **Team photos** (if available)

---

### 20. CALL TO ACTION SLIDE
**Visual Recommendations:**
- [ ] **Three large buttons/boxes**:
  ```
  ┌────────────────┐
  │  👨‍🌾 FARMERS   │
  │ Dial *384*1234│
  └────────────────┘
  
  ┌────────────────┐
  │  🤝 PARTNERS   │
  │ Contact us     │
  └────────────────┘
  
  ┌────────────────┐
  │  💻 DEVELOPERS │
  │ GitHub: ⭐     │
  └────────────────┘
  ```

- [ ] **Phone icon** with `*384*1234#` prominently displayed

---

### 21. CONTACT SLIDE
**Visual Recommendations:**
- [ ] **Contact information cards**:
  ```
  📧 Email: bloomwatch.kenya@example.com
  🌐 Web: www.bloomwatch.ke
  💻 GitHub: [URL]
  🐦 Twitter: @BloomWatchKE
  ```

- [ ] **QR code** linking to GitHub repository

- [ ] **Kenya flag** 🇰🇪 or Kenya map outline

---

### 22. CLOSING SLIDE
**Visual Recommendations:**
- [ ] **Inspiring photo**: Kenyan farmer smiling with healthy crop
- [ ] **Satellite image** of Kenya as background (semi-transparent)
- [ ] **Quote overlay**:
  > "Space technology is not just for scientists—  
  > it can directly improve the lives of smallholder farmers."

- [ ] **NASA Space Apps Challenge logo**

---

## 🎨 Design Guidelines

### Color Palette (Kenya-Themed)
- **Primary Green**: `#006400` (agriculture, growth)
- **Kenya Red**: `#DC143C` (Kenya flag)
- **Kenya Black**: `#000000` (Kenya flag)
- **Sky Blue**: `#4682B4` (satellite/space)
- **Earth Brown**: `#8B4513` (soil)
- **Bloom Yellow**: `#FFD700` (flowering)

### Font Recommendations
- **Headings**: Montserrat Bold or Raleway Bold
- **Body**: Open Sans or Roboto
- **Code**: Fira Code or Source Code Pro

### Icon Resources
- **Satellite icons**: Font Awesome, Noun Project
- **Farm icons**: Flaticon "Agriculture" pack
- **Phone icons**: Material Design Icons
- **Emoji**: Use native OS emoji for universality

---

## 📸 Where to Get Images

### Satellite Imagery
1. **Google Earth Engine Code Editor**
   - Export visualizations directly from GEE
   - Use `Map.screenshot()` for Kenya maps

2. **NASA Earthdata Search**
   - https://search.earthdata.nasa.gov/
   - Download sample Landsat/MODIS images

3. **Sentinel Hub EO Browser**
   - https://apps.sentinel-hub.com/eo-browser/
   - High-res Sentinel-2 images of Kenya

### Stock Photos (Free)
- **Unsplash**: Search "Kenya farmer", "maize field", "coffee farm"
- **Pexels**: Search "African agriculture", "farming Kenya"
- **Pixabay**: Search "farm", "crop", "harvest"

### Kenya Maps
- **Mapbox Studio**: Create custom Kenya maps
- **QGIS**: Open-source GIS for professional maps
- **GeoPandas**: Generate maps programmatically in Python

---

## 🖼️ Creating Diagrams

### Recommended Tools

1. **Excalidraw** (Free, Web-Based)
   - Great for hand-drawn style flowcharts
   - https://excalidraw.com/

2. **draw.io / diagrams.net** (Free)
   - Professional diagrams
   - https://app.diagrams.net/

3. **Figma** (Free Tier)
   - Professional design tool
   - https://www.figma.com/

4. **Canva** (Free Tier)
   - Easy presentation graphics
   - https://www.canva.com/

5. **Python (Matplotlib/Plotly)**
   - Programmatic chart generation
   - Full control over visuals

### Python Code Examples

**Create Kenya Map with Farmer Locations:**
```python
import folium
import pandas as pd

# Farmer locations
farmers = pd.DataFrame({
    'lat': [-1.29, -0.42, 0.35, -1.52],
    'lon': [36.82, 36.95, 34.75, 37.26],
    'name': ['John Kamau', 'Mary Wanjiku', 'Peter Mwangi', 'Jane Njeri'],
    'region': ['Central', 'Central', 'Western', 'Eastern']
})

# Create map
m = folium.Map(location=[-0.5, 37.0], zoom_start=7)

# Add farmers
for idx, row in farmers.iterrows():
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=f"{row['name']} ({row['region']})",
        icon=folium.Icon(color='green', icon='leaf')
    ).add_to(m)

m.save('kenya_farmers_map.html')
```

**Create Impact Chart:**
```python
import matplotlib.pyplot as plt

metrics = ['Yield Increase', 'Disease Reduction', 'Income Gain', 'Satisfaction']
values = [25, 30, 500, 98]

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(metrics, values, color=['#006400', '#228B22', '#32CD32', '#7CFC00'])

# Add value labels
for i, (metric, value) in enumerate(zip(metrics, values)):
    if 'Income' in metric:
        ax.text(value, i, f' ${value}', va='center', fontweight='bold')
    else:
        ax.text(value, i, f' {value}%', va='center', fontweight='bold')

ax.set_xlabel('Value', fontsize=12)
ax.set_title('BloomWatch Kenya - Impact Metrics', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('impact_metrics.png', dpi=300, bbox_inches='tight')
```

---

## 🎬 Animation Ideas

If presenting digitally (PowerPoint/Google Slides):

1. **Satellite orbit animation** (slide in from top)
2. **Data flow animation** (arrows moving through pipeline)
3. **Kenya map zoom** (start from Africa, zoom to Kenya, then regions)
4. **Number counters** (500 farmers counting up from 0)
5. **USSD flow** (phone screens transitioning)
6. **Alert delivery** (satellite → phone with message appearing)

---

## 📱 Interactive Demo Elements

If presenting with live internet:

1. **Streamlit Dashboard**: Navigate live through features
2. **USSD Simulator**: Show registration flow step-by-step
3. **GEE Code Editor**: Run bloom detection live
4. **GitHub Repository**: Show open-source code
5. **MongoDB Compass**: Display real farmer data (anonymized)

---

## ✅ Pre-Presentation Checklist

- [ ] All images exported at **300 DPI** minimum
- [ ] All diagrams use **consistent color scheme**
- [ ] All text is **readable from 20 feet away** (font size ≥ 18pt)
- [ ] All satellite images have **labels** (date, location, sensor)
- [ ] All charts have **axes labels** and **legends**
- [ ] All quotes have **attribution** (name, location)
- [ ] All logos are **high resolution** (no pixelation)
- [ ] All QR codes are **tested** and working
- [ ] All animations are **smooth** (not distracting)
- [ ] **Backup plan** if internet fails (screenshots of live demos)

---

## 🎤 Presentation Tips

1. **Start Strong**: Open with satellite image of Kenya + bold statement
2. **Tell Stories**: Lead with farmer testimonials, not tech specs
3. **Show Don't Tell**: Use visuals > text on slides
4. **Demo Live**: If possible, show USSD flow or dashboard live
5. **End with Impact**: Close with farmer success story + call to action

---

**Good luck with your presentation! 🚀🌾**

*Remember: You're not just presenting technology—you're presenting hope for 500,000 farmers.*


