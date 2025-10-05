// BloomWatch Kenya: Farmer-Centric Bloom Detection for NASA Space Apps 2025
// Focus: Kenya agricultural regions with multi-satellite integration
// Datasets: Landsat 8/9 (30m), MODIS (1km)
// Region: Central Kenya agricultural belt

// Kenya agricultural regions - Central Kenya (Kiambu, Murang'a, Nyeri)
var kenya_central = ee.Geometry.Rectangle([36.5, -1.5, 37.5, -0.5]);
// Rift Valley agricultural areas (Nakuru, Uasin Gishu)
var kenya_rift = ee.Geometry.Rectangle([35.5, -1.0, 36.5, 0.5]);
// Combined Kenya agricultural focus area
var bbox = kenya_central.union(kenya_rift);

var startDate = '2024-01-01';  // Kenya growing seasons
var endDate = '2024-12-31';   // Full agricultural year

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

// Baseline for anomalies (5-yr avg) - MODIS-based
var baseline = ee.ImageCollection('MODIS/061/MOD13A2')
  .filterDate('2019-01-01', '2024-01-01')
  .filterBounds(bbox)
  .select('NDVI')
  .map(function(img) { return img.multiply(0.0001); })
  .mean();

// NDVI Anomaly
var anomaly = modis.map(function(img) {
  return img.subtract(baseline).divide(baseline).multiply(100).rename('anomaly');
});

// Visualization
var ndviVis = {min: -0.2, max: 0.8, palette: ['blue', 'white', 'green']};
var ariVis = {min: -0.1, max: 0.3, palette: ['gray', 'purple', 'red']};
var anomalyVis = {min: -50, max: 50, palette: ['blue', 'white', 'red']};

Map.centerObject(bbox, 10);
Map.addLayer(modis.median(), ndviVis, 'MODIS NDVI Median');
Map.addLayer(landsat.select('ARI').median(), ariVis, 'Landsat ARI Median');
Map.addLayer(anomaly.median(), anomalyVis, 'NDVI Anomaly (MODIS)');

// Export all datasets (to Drive; download to data/exports)

// 1. MODIS NDVI (1km - broad trends)
Export.image.toDrive({
  image: modis.median().clip(bbox),
  description: 'modis_ndvi_median',
  folder: 'bloomwatch',
  scale: 1000,  // MODIS res
  region: bbox,
  fileFormat: 'GeoTIFF',
  maxPixels: 1e9
});

// 2. Landsat ARI (flower detection)
Export.image.toDrive({
  image: landsat.select('ARI').median().clip(bbox),
  description: 'landsat_ari_median',
  folder: 'bloomwatch',
  scale: 30,  // Landsat res
  region: bbox,
  fileFormat: 'GeoTIFF',
  maxPixels: 1e9
});

// 3. NDVI Anomaly (MODIS-based)
Export.image.toDrive({
  image: anomaly.median().clip(bbox),
  description: 'modis_ndvi_anomaly',
  folder: 'bloomwatch',
  scale: 1000,  // MODIS res
  region: bbox,
  fileFormat: 'GeoTIFF',
  maxPixels: 1e9
});

// Time-series export (as asset or batch)
print('Prototype ready. Check exports in Drive.');
