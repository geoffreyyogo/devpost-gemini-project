#!/bin/bash
# Start BloomWatch Kenya Admin Dashboard

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║       🔧 BloomWatch Kenya - Admin Dashboard                        ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if streamlit is installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "📦 Installing Streamlit..."
    pip install streamlit pandas
fi

echo "🚀 Starting Admin Dashboard..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Admin Dashboard Features:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✓ View and manage all farmers"
echo "  ✓ Create new farmers manually"
echo "  ✓ Send smart alerts to farmers"
echo "  ✓ View message queues"
echo "  ✓ Statistics and analytics"
echo ""
echo "🔐 Default Login:"
echo "  Username: admin"
echo "  Password: bloomwatch2024"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start Streamlit
cd app
streamlit run admin_dashboard.py --server.port 8502 --server.headless true

