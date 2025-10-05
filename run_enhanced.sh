#!/bin/bash
# BloomWatch Kenya - Enhanced UI Launcher
# Run this script to start the enhanced Streamlit app

echo "🌾 BloomWatch Kenya - Enhanced UI"
echo "=================================="
echo ""
echo "Starting enhanced Streamlit application..."
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null
then
    echo "❌ Streamlit is not installed!"
    echo "📦 Installing dependencies..."
    pip install -r requirements_enhanced.txt
fi

# Check if streamlit-lottie is installed
python3 -c "import streamlit_lottie" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing streamlit-lottie for animations..."
    pip install streamlit-lottie requests
fi

echo ""
echo "✅ All dependencies ready!"
echo ""
echo "🚀 Launching BloomWatch Kenya Enhanced UI..."
echo "📱 Open your browser to: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the enhanced app
streamlit run app/streamlit_app_enhanced.py --server.headless=true

# Alternative: Run on custom port
# streamlit run app/streamlit_app_enhanced.py --server.port 8502




