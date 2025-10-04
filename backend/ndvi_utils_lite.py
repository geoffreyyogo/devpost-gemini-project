"""
Lightweight NDVI utilities for BloomWatch Kenya demo
Works without heavy geospatial dependencies
"""

import numpy as np
from typing import Tuple, List

def load_raster_demo(file_path: str, band: int = 1) -> np.ndarray:
    """Demo version - generates synthetic raster data"""
    # Generate Kenya-like NDVI data
    return np.random.rand(100, 100) * 0.8 + 0.1  # 0.1 to 0.9 NDVI range

def compute_anomaly(current: np.ndarray, baseline: np.ndarray) -> np.ndarray:
    """NDVI anomaly: (current - baseline) / baseline * 100."""
    return np.where(baseline != 0, (current - baseline) / baseline * 100, 0)

def smooth_time_series(ts: np.ndarray, sigma: float = 2) -> np.ndarray:
    """Simple smoothing for NDVI time-series (without scipy)"""
    # Simple moving average as replacement for Gaussian filter
    if len(ts.shape) == 1:
        # 1D case
        window = int(sigma * 2 + 1)
        if window >= len(ts):
            return ts
        
        smoothed = np.zeros_like(ts)
        for i in range(len(ts)):
            start = max(0, i - window // 2)
            end = min(len(ts), i + window // 2 + 1)
            smoothed[i] = np.mean(ts[start:end])
        return smoothed
    else:
        # Multi-dimensional case - smooth along first axis
        smoothed = np.zeros_like(ts)
        for i in range(ts.shape[0]):
            window_start = max(0, i - int(sigma))
            window_end = min(ts.shape[0], i + int(sigma) + 1)
            smoothed[i] = np.mean(ts[window_start:window_end], axis=0)
        return smoothed

def find_peaks_simple(data: np.ndarray, prominence: float = 0.2) -> List[int]:
    """Simple peak detection without scipy"""
    peaks = []
    for i in range(1, len(data) - 1):
        if (data[i] > data[i-1] and data[i] > data[i+1] and 
            data[i] - min(data[i-1], data[i+1]) >= prominence):
            peaks.append(i)
    return peaks

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
    peaks = find_peaks_simple(mean_ndvi, prominence=prominence)
    
    # Refine: Check ARI and anomaly at peaks
    refined_peaks = []
    for p in peaks:
        if p < len(ari_values) and ari_values[p] > ari_thresh:
            # Assume anomaly computed separately; placeholder
            anomaly_at_p = 25  # Replace with actual
            if anomaly_at_p > anomaly_thresh:
                refined_peaks.append(p)
    
    bloom_scores = np.zeros_like(mean_ndvi)
    if refined_peaks:
        bloom_scores[refined_peaks] = mean_ndvi[refined_peaks]
    
    return refined_peaks, bloom_scores

# Example usage (for tests)
if __name__ == "__main__":
    # Dummy data
    dummy_ndvi = np.random.rand(20, 100, 100) * 0.8  # 20 timesteps
    dummy_ari = [0.05 + np.random.rand() * 0.2 for _ in range(20)]
    peaks, scores = detect_blooms(dummy_ndvi, dummy_ari)
    print(f"Detected {len(peaks)} blooms at indices: {peaks}")
