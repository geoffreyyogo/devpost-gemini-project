# 🛰️ GEE Integration Guide for BloomWatch Kenya

## Complete Pipeline: GEE → Backend → Streamlit

This guide shows how to connect the Google Earth Engine exports to your Streamlit application.

---

## 📋 Overview

**Data Flow:**
```
Google Earth Engine (gee_bloom_detector.js)
    ↓ Export to Google Drive
    ↓ Download to data/exports/
Backend (gee_data_loader.py)
    ↓ Load GeoTIFF files
    ↓ Process for bloom detection
Streamlit App (streamlit_app_v2.py)
    ↓ Display to farmers
```

---

## Step 1: Export Data from GEE

### 1.1 Open GEE Code Editor
Visit: https://code.earthengine.google.com/

### 1.2 Copy Your Script
Open `gee/gee_bloom_detector.js` and copy the contents

### 1.3 Run the Script
- Paste into GEE Code Editor
- Click **Run**
- View results on the map

### 1.4 Export Data
The script automatically creates export tasks. To run them:
1. Click **Tasks** tab (top right)
2. Find your export tasks
3. Click **RUN** for each:
   - `modis_ndvi_median`
   - `landsat_ari_median`
   - Any time-series exports

### 1.5 Configure Export
- **Destination**: Google Drive
- **Folder**: `bloomwatch` (or your choice)
- **Format**: GeoTIFF
- Click **Run**

### 1.6 Wait for Export
- Exports take 5-30 minutes depending on size
- Check progress in **Tasks** tab
- You'll get email notification when complete

---

## Step 2: Download Exports

### 2.1 From Google Drive
1. Go to Google Drive
2. Find `bloomwatch` folder
3. Download all `.tif` files

### 2.2 Place in Project
```bash
cd /home/yogo/bloom-detector
mkdir -p data/exports
# Move downloaded files here
mv ~/Downloads/*ndvi*.tif data/exports/
mv ~/Downloads/*ari*.tif data/exports/
```

---

## Step 3: Test Data Loading

### 3.1 Test the Loader
```bash
cd /home/yogo/bloom-detector
source venv/bin/activate
python backend/gee_data_loader.py
```

Expected output:
```
🛰️ GEE Data Loader Test
============================================================
📁 Export Directory: ../data/exports
📊 Total Files: X
✓ Sentinel-2: True/False
✓ Landsat: True/False
✓ MODIS: True/False
✓ ARI Data: True/False

🌾 Loading Kenya Data...
✓ Data Source: Sentinel-2 / Landsat / MODIS / Synthetic
✓ NDVI Shape: (height, width)
✓ NDVI Range: 0.XXX - 0.XXX
```

---

## Step 4: Integrate with Streamlit

### 4.1 The Data Loader is Already Integrated!

The new app (`streamlit_app_v2.py`) automatically:
- Looks for GEE exports in `data/exports/`
- Falls back to synthetic data if exports not found
- Shows data source in sidebar

### 4.2 Run the App
```bash
./RUN_APP.sh
```

### 4.3 Check Data Source
In the Streamlit app sidebar, you'll see:
- 📡 **Data: Sentinel-2** (if GEE data found)
- 📊 **Using synthetic demo data** (if no exports)

---

## 📊 Supported Data Types

### Priority Order (Best to Good):
1. **Sentinel-2 NDVI** (10m resolution) - Best for Kenya farms
2. **Landsat 8/9 NDVI** (30m resolution) - Good coverage
3. **MODIS NDVI** (1km resolution) - Daily, broad scale
4. **VIIRS NDVI** (750m resolution) - Daily monitoring

### Filename Patterns:
The loader automatically finds files matching:
- `*sentinel*ndvi*.tif` or `*s2*ndvi*.tif`
- `*landsat*ndvi*.tif` or `*l8*ndvi*.tif` or `*l9*ndvi*.tif`
- `*landsat*ari*.tif` (for flower detection)
- `*modis*ndvi*.tif` or `*mod13*.tif`
- `*viirs*ndvi*.tif` or `*vnp13*.tif`

---

## 🔧 Advanced: Custom GEE Exports

### Export Time Series (Multiple Dates)

Add this to your `gee_bloom_detector.js`:

```javascript
// Export time series (one file per month)
var months = ee.List.sequence(1, 12);

months.evaluate(function(monthList) {
  monthList.forEach(function(month) {
    var startDate = ee.Date.fromYMD(2024, month, 1);
    var endDate = startDate.advance(1, 'month');
    
    var monthly = modis
      .filterDate(startDate, endDate)
      .median()
      .clip(bbox);
    
    Export.image.toDrive({
      image: monthly,
      description: 'modis_ndvi_2024_' + String(month).padStart(2, '0'),
      folder: 'bloomwatch',
      scale: 1000,
      region: bbox,
      fileFormat: 'GeoTIFF'
    });
  });
});
```

### Export High-Resolution Sentinel-2

```javascript
// Export Sentinel-2 NDVI (10m resolution)
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(bbox)
  .filterDate('2024-01-01', '2024-12-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .map(function(img) {
    var ndvi = img.normalizedDifference(['B8', 'B4']).rename('NDVI');
    return ndvi.copyProperties(img, ['system:time_start']);
  });

Export.image.toDrive({
  image: s2.median().clip(bbox),
  description: 'sentinel2_ndvi_kenya_2024',
  folder: 'bloomwatch',
  scale: 10,  // 10m resolution!
  region: bbox,
  fileFormat: 'GeoTIFF',
  maxPixels: 1e9
});
```

---

## 🐛 Troubleshooting

### "No GEE exports found"
**Solution**: 
1. Check `data/exports/` directory exists
2. Ensure `.tif` files are there
3. Check filenames match patterns above
4. Try: `ls -la data/exports/`

### "Cannot load GeoTIFF - rasterio not available"
**Solution**:
```bash
# Install rasterio (requires GDAL)
sudo apt-get install gdal-bin libgdal-dev
pip install rasterio
```

**Alternative**: The app saves `.npy` fallback files automatically

### "Export failed in GEE"
**Common causes**:
- Region too large (reduce bbox size)
- Too many pixels (increase scale parameter)
- Not authenticated (run `earthengine authenticate`)

**Solution**:
```javascript
// In your GEE script, increase scale or reduce region
scale: 1000,  // Larger number = lower resolution = faster
maxPixels: 1e9  // Increase if needed
```

### App shows synthetic data even with exports
**Solution**:
1. Check file names: `ls data/exports/`
2. Test loader: `python backend/gee_data_loader.py`
3. Check logs for errors
4. Ensure files are valid GeoTIFF: `gdalinfo data/exports/yourfile.tif`

---

## 📈 Performance Tips

### 1. Use Appropriate Resolution
- **Small areas** (< 100km²): Use Sentinel-2 (10m)
- **Medium areas** (100-1000km²): Use Landsat (30m)  
- **Large areas** (> 1000km²): Use MODIS (1km)

### 2. Optimize Export Size
```javascript
// Reduce file size
var ndvi = modis.median()
  .multiply(10000)  // Scale to integer
  .toInt16()  // Convert to 16-bit integer
  .clip(bbox);

Export.image.toDrive({
  image: ndvi,
  // ... other params
  formatOptions: {
    cloudOptimized: true  // Enable COG format
  }
});
```

### 3. Cache Data in App
The Streamlit app uses `@st.cache_data` to avoid reloading files on every interaction.

---

## 🎯 Best Practices

### For Hackathon Demo:
1. **Use Pre-exported Data**: Export 1-2 sample files before demo
2. **Have Fallback**: App automatically uses synthetic data if needed
3. **Show Both**: Demonstrate with real GEE data, then explain fallback
4. **Explain Process**: Show GEE script → Export → App pipeline

### For Production:
1. **Automated Pipeline**: Schedule exports with GEE Python API
2. **Cloud Storage**: Use Google Cloud Storage instead of Drive
3. **Data Management**: Implement automatic cleanup of old exports
4. **Monitoring**: Log data freshness and quality metrics

---

## 📝 Quick Reference

### File Locations:
- **GEE Script**: `gee/gee_bloom_detector.js`
- **Data Loader**: `backend/gee_data_loader.py`
- **Export Directory**: `data/exports/`
- **Streamlit App**: `app/streamlit_app_v2.py`

### Commands:
```bash
# Test data loader
python backend/gee_data_loader.py

# Run app
./RUN_APP.sh

# Check exports
ls -lh data/exports/

# Install rasterio
pip install rasterio
```

### GEE Export Checklist:
- [ ] Script runs without errors
- [ ] Export tasks appear in Tasks tab
- [ ] Tasks complete successfully
- [ ] Files downloaded to `data/exports/`
- [ ] Filenames match expected patterns
- [ ] Data loader recognizes files
- [ ] App shows correct data source

---

## 🚀 Next Steps

### For Your Hackathon:
1. Export sample data now (takes 10-20 min)
2. Test with real data
3. Keep synthetic fallback for demo reliability
4. Show judges both real and synthetic modes

### After Hackathon:
1. Set up automated exports with GEE Python API
2. Implement cloud storage integration
3. Add data quality checks
4. Create data refresh schedule
5. Monitor bloom detection accuracy

---

## 💡 Pro Tips

1. **Start Small**: Export a small test region first
2. **Use Sandboxes**: Test in GEE sandbox mode
3. **Check Quota**: GEE has daily export limits
4. **Verify Data**: Always check exported files before using
5. **Document**: Note which satellite/date each export came from

---

**Ready to connect your real satellite data!** 🛰️

For questions, see:
- GEE Docs: https://developers.google.com/earth-engine
- Rasterio Docs: https://rasterio.readthedocs.io/


