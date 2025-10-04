#!/bin/bash

# BloomWatch Kenya - Professional App Launcher
# This script launches the improved Streamlit application

echo "🌾 BloomWatch Kenya - Professional Platform"
echo "=============================================="
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not activated"
    echo "Activating venv..."
    source venv/bin/activate
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
python3 -c "import streamlit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required packages..."
    pip install streamlit plotly folium streamlit-folium numpy pandas
fi

echo ""
echo "🚀 Starting BloomWatch Kenya..."
echo ""
echo "📱 Access the application at: http://localhost:8501"
echo "🌐 From Windows (WSL): The browser should open automatically"
echo ""
echo "Features:"
echo "  ✓ Professional landing page with Get Started button"
echo "  ✓ Complete farmer registration with confirmation"
echo "  ✓ Secure login/logout system"
echo "  ✓ User dashboard with real-time data"
echo "  ✓ English & Kiswahili support"
echo "  ✓ Smooth animations, no flickers"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=============================================="
echo ""

# Run the new professional app
cd app
streamlit run streamlit_app_v2.py \
    --server.headless true \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --browser.gatherUsageStats false

