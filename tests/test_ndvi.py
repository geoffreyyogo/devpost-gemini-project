import pytest
import numpy as np
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from ndvi_utils import compute_anomaly, detect_blooms, smooth_time_series

def test_compute_anomaly():
    """Test NDVI anomaly calculation."""
    current = np.array([0.5, 0.6])
    baseline = np.array([0.4, 0.5])
    expected = np.array([25.0, 20.0])
    result = compute_anomaly(current, baseline)
    assert np.allclose(result, expected), f"Expected {expected}, got {result}"

def test_compute_anomaly_zero_baseline():
    """Test anomaly calculation with zero baseline."""
    current = np.array([0.5, 0.6])
    baseline = np.array([0.0, 0.5])
    expected = np.array([0.0, 20.0])  # Zero baseline should return 0
    result = compute_anomaly(current, baseline)
    assert np.allclose(result, expected), f"Expected {expected}, got {result}"

def test_detect_blooms():
    """Test bloom detection algorithm."""
    # Create synthetic time series with clear peaks
    ts = np.array([0.1, 0.8, 0.2, 0.9, 0.1])[:, np.newaxis, np.newaxis]  # Fake spatial dims
    ari = [0.05, 0.15, 0.05, 0.12, 0.05]  # ARI values corresponding to time steps
    
    peaks, scores = detect_blooms(ts, ari, prominence=0.5, ari_thresh=0.1)
    
    # Should detect peaks at indices 1 and 3 (both have ARI > 0.1)
    assert len(peaks) >= 1, f"Expected at least 1 bloom, got {len(peaks)}"
    assert all(p in [1, 3] for p in peaks), f"Unexpected peak indices: {peaks}"

def test_detect_blooms_no_peaks():
    """Test bloom detection with no significant peaks."""
    ts = np.array([0.3, 0.31, 0.29, 0.32])[:, np.newaxis, np.newaxis]  # Flat signal
    ari = [0.05, 0.06, 0.04, 0.05]  # Low ARI values
    
    peaks, scores = detect_blooms(ts, ari, prominence=0.5, ari_thresh=0.1)
    
    # Should detect no blooms due to low prominence and ARI
    assert len(peaks) == 0, f"Expected no blooms, got {len(peaks)}"

def test_smooth_time_series():
    """Test Gaussian smoothing of time series."""
    ts = np.array([1.0, 2.0, 1.0])
    smoothed = smooth_time_series(ts, sigma=1.0)
    
    # Smoothed signal should be less peaked
    assert smoothed[1] < ts[1], "Peak should be reduced by smoothing"
    assert smoothed[0] > ts[0], "Valleys should be increased by smoothing"
    assert smoothed[2] > ts[2], "Valleys should be increased by smoothing"

def test_smooth_time_series_2d():
    """Test smoothing with 2D input (time, space)."""
    ts = np.array([[1.0, 1.0], [2.0, 2.0], [1.0, 1.0]])  # 3 timesteps, 2 spatial points
    smoothed = smooth_time_series(ts, sigma=1.0)
    
    assert smoothed.shape == ts.shape, "Shape should be preserved"
    assert np.all(smoothed[1] < ts[1]), "Peak should be reduced by smoothing"

def test_detect_blooms_edge_cases():
    """Test bloom detection edge cases."""
    # Empty time series
    ts = np.array([]).reshape(0, 1, 1)
    ari = []
    peaks, scores = detect_blooms(ts, ari)
    assert len(peaks) == 0, "Empty input should return no peaks"
    
    # Single point
    ts = np.array([0.5])[:, np.newaxis, np.newaxis]
    ari = [0.15]
    peaks, scores = detect_blooms(ts, ari)
    # Single point cannot have prominence, so no peaks expected
    assert len(peaks) == 0, "Single point should return no peaks"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
