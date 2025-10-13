import numpy as np
import rasterio as rio
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d
import xarray as xr
from typing import Tuple, List

def load_raster(file_path: str, band: int = 1) -> np.ndarray:
    """Load raster band as numpy array."""
    with rio.open(file_path) as src:
        return src.read(band)

def compute_anomaly(current: np.ndarray, baseline: np.ndarray) -> np.ndarray:
    """NDVI anomaly: (current - baseline) / baseline * 100."""
    return np.where(baseline != 0, (current - baseline) / baseline * 100, 0)

def smooth_time_series(ts: np.ndarray, sigma: float = 2) -> np.ndarray:
    """Gaussian smoothing for NDVI time-series."""
    return gaussian_filter1d(ts, sigma=sigma, axis=0)

def detect_blooms(ndvi_ts: np.ndarray, ari_values: List[float], 
                  prominence: float = 0.2, anomaly_thresh: float = 20, 
                  ari_thresh: float = 0.1) -> Tuple[List[int], np.ndarray]:
    """
    Detect blooms: NDVI peaks with ARI > thresh and anomaly > thresh.
    ndvi_ts: Time-series array (time, y, x) or flattened.
    ari_values: List of ARI at peak times.
    """
    # Flatten spatial dims for mean TS
    if len(ndvi_ts.shape) > 1:
        mean_ndvi = np.mean(ndvi_ts, axis=(1, 2))
    else:
        mean_ndvi = ndvi_ts
    
    mean_ndvi = smooth_time_series(mean_ndvi)
    peaks, _ = find_peaks(mean_ndvi, prominence=prominence)
    
    # Refine: Check ARI and anomaly at peaks
    refined_peaks = []
    for p in peaks:
        if p < len(ari_values) and ari_values[p] > ari_thresh:
            # Assume anomaly computed separately; placeholder
            anomaly_at_p = 25  # Replace with actual
            if anomaly_at_p > anomaly_thresh:
                refined_peaks.append(p)
    
    bloom_scores = np.zeros_like(mean_ndvi)
    bloom_scores[refined_peaks] = mean_ndvi[refined_peaks]
    
    return refined_peaks, bloom_scores

# Example usage (for tests)
if __name__ == "__main__":
    # Dummy data
    dummy_ndvi = np.random.rand(20, 100, 100) * 0.8  # 20 timesteps
    dummy_ari = [0.05 + np.random.rand() * 0.2 for _ in range(20)]
    peaks, scores = detect_blooms(dummy_ndvi, dummy_ari)
    print(f"Detected {len(peaks)} blooms at indices: {peaks}")
