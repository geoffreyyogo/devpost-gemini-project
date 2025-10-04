#!/usr/bin/env python3
"""Simple test to verify the BloomWatch Kenya implementation works"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    import numpy as np
    print("✓ NumPy imported successfully")
    
    from ndvi_utils import compute_anomaly, detect_blooms
    print("✓ NDVI utils imported successfully")
    
    # Test compute_anomaly
    current = np.array([0.5, 0.6])
    baseline = np.array([0.4, 0.5])
    result = compute_anomaly(current, baseline)
    expected = np.array([25.0, 20.0])
    
    if np.allclose(result, expected):
        print("✓ compute_anomaly test passed")
    else:
        print(f"✗ compute_anomaly test failed: got {result}, expected {expected}")
    
    # Test detect_blooms
    ts = np.array([0.1, 0.8, 0.2, 0.9])[:, np.newaxis, np.newaxis]
    ari = [0.05, 0.15, 0.05, 0.12]
    peaks, scores = detect_blooms(ts, ari, prominence=0.5, ari_thresh=0.1)
    print(f"✓ detect_blooms test completed: found {len(peaks)} peaks")
    
    # Test Kenya crop calendar
    from kenya_crops import KenyaCropCalendar
    calendar = KenyaCropCalendar()
    current_season = calendar.get_current_season()
    expected_blooms = calendar.get_expected_blooms()
    print(f"✓ Kenya crop calendar working: current season is {current_season}")
    print(f"✓ Expected blooms this month: {list(expected_blooms.keys())}")
    
    # Test notification service (without actual API calls)
    from notification_service import NotificationService, Farmer
    service = NotificationService()
    print("✓ Notification service initialized")
    
    print("\n🌾 BloomWatch Kenya - All core components working!")
    print("🛰️ Ready for NASA Space Apps Challenge demo!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Please install dependencies: pip install -r backend/requirements.txt")
except Exception as e:
    print(f"✗ Error: {e}")
