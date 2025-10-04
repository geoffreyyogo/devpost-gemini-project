// BloomWatch Kenya: Farmer-Centric Bloom Detection for NASA Space Apps 2025
// Focus: Kenya agricultural regions with multi-satellite integration
// Datasets: Sentinel-2 (10m), Landsat 8/9 (30m), MODIS (1km), VIIRS (750m)
// Region: Central Kenya agricultural belt

// Kenya agricultural regions - Central Kenya (Kiambu, Murang'a, Nyeri)
var kenya_central = ee.Geometry.Rectangle([36.5, -1.5, 37.5, -0.5]);
// Rift Valley agricultural areas (Nakuru, Uasin Gishu)
var kenya_rift = ee.Geometry.Rectangle([35.5, -1.0, 36.5, 0.5]);
// Combined Kenya agricultural focus area
var bbox = kenya_central.union(kenya_rift);

var startDate = '2024-01-01';  // Kenya growing seasons
var endDate = '2024-12-31';   // Full agricultural year

// Sentinel-2 NDVI (10m resolution - excellent for Kenya farms)
var sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(bbox)
  .filterDate(startDate, endDate)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .map(function(img) {
    var ndvi = img.normalizedDifference(['B8', 'B4']).rename('NDVI');
    var ari = img.select('B3').divide(img.select('B5')).subtract(
      img.select('B3').divide(img.select('B4'))).rename('ARI');
    return img.addBands([ndvi, ari]).copyProperties(img, ['system:time_start']);
  });

// Landsat 8/9 for gap-filling and validation
var landsat = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
  .merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
  .filterBounds(bbox)
  .filterDate(startDate, endDate)
  .filter(ee.Filter.lt('CLOUD_COVER', 20))
  .map(function(img) {
    var ndvi = img.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI');
    var ari = img.select('SR_B3').divide(10000).pow(-1)
      .subtract(img.select('SR_B5').divide(10000).pow(-1)).rename('ARI');
    return img.addBands([ndvi, ari]).copyProperties(img, ['system:time_start']);
  });

// MODIS for broad trends and gap-filling
var modis = ee.ImageCollection('MODIS/061/MOD13A2')
  .filterBounds(bbox)
  .filterDate(startDate, endDate)
  .select('NDVI')
  .map(function(img) { return img.multiply(0.0001).copyProperties(img, ['system:time_start']); });

// VIIRS for daily monitoring
var viirs = ee.ImageCollection('NOAA/VIIRS/001/VNP13A1')
  .filterBounds(bbox)
  .filterDate(startDate, endDate)
  .select('NDVI')
  .map(function(img) { return img.multiply(0.0001).copyProperties(img, ['system:time_start']); });

// Baseline for anomalies (5-yr avg) - Kenya specific
var baseline_s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterDate('2019-01-01', '2024-01-01')
  .filterBounds(bbox)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .map(function(img) { return img.normalizedDifference(['B8', 'B4']); })
  .mean();

// NDVI Anomaly
var anomaly = modis.map(function(img) {
  return img.subtract(baseline).divide(baseline).multiply(100).rename('anomaly');
});

// Landsat for ARI (Anthocyanin Reflectance Index for pigments/flowers)
var landsat = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
  .filterBounds(bbox)
  .filterDate(startDate, endDate)
  .map(function(img) {
    var green = img.select('SR_B3').divide(10000);  // Scale
    var redEdge = img.select('SR_B5').divide(10000);  // NIR as proxy
    var ari = green.pow(-1).subtract(redEdge.pow(-1)).rename('ARI');
    return img.addBands(ari).set('system:time_start', img.get('system:time_start'));
  });

// Visualization
var ndviVis = {min: -0.2, max: 0.8, palette: ['blue', 'white', 'green']};
var ariVis = {min: -0.1, max: 0.3, palette: ['gray', 'purple', 'red']};
var anomalyVis = {min: -50, max: 50, palette: ['blue', 'white', 'red']};

Map.centerObject(bbox, 10);
Map.addLayer(modis.median(), ndviVis, 'NDVI Median');
Map.addLayer(landsat.select('ARI').median(), ariVis, 'ARI Median');
Map.addLayer(anomaly.median(), anomalyVis, 'NDVI Anomaly');

// Export examples (to Drive; download to data/exports)
Export.image.toDrive({
  image: modis.median().clip(bbox),
  description: 'modis_ndvi_median',
  folder: 'bloomwatch',
  scale: 1000,  // MODIS res
  region: bbox,
  fileFormat: 'GeoTIFF',
  maxPixels: 1e9
});

Export.image.toDrive({
  image: landsat.median().select('ARI').clip(bbox),
  description: 'landsat_ari_median',
  folder: 'bloomwatch',
  scale: 30,  // Landsat res
  region: bbox,
  fileFormat: 'GeoTIFF',
  maxPixels: 1e9
});

// Time-series export (as asset or batch)
print('Prototype ready. Check exports in Drive.');
