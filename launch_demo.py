#!/usr/bin/env python3
"""
BloomWatch Kenya - Quick Launch Script
Launches the Streamlit demo with proper setup
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("🌾 BloomWatch Kenya - NASA Space Apps Challenge 2025")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("app/streamlit_app.py").exists():
        print("❌ Error: Please run this script from the bloom-detector directory")
        print("   Current directory:", os.getcwd())
        return False
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Virtual environment not detected")
        print("   Consider running: source venv/bin/activate")
    
    print("🚀 Launching BloomWatch Kenya Dashboard...")
    print("📍 URL: http://localhost:8501")
    print("🌍 Focus: Kenya Agricultural Regions")
    print("🛰️  Data: Multi-satellite integration (Sentinel-2, Landsat, MODIS, VIIRS)")
    print("📱 Features: SMS/Email alerts, English/Kiswahili support")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Launch Streamlit
        result = subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "app/streamlit_app.py",
            "--server.headless", "true",
            "--server.port", "8501"
        ], check=True)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching Streamlit: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 BloomWatch Kenya demo stopped")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
