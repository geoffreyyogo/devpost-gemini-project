#!/bin/bash
# Start USSD API and expose it via ngrok
# This makes your local USSD endpoint accessible to Africa's Talking

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║    🌾 BloomWatch Kenya - USSD API with ngrok                       ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed!"
    echo "   Run: ./setup_ngrok.sh"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "📦 Installing Flask..."
    pip install flask
fi

echo "🚀 Starting USSD API..."
echo ""

# Kill any existing processes on port 5000
lsof -ti:5000 | xargs kill -9 2>/dev/null || true

# Start Flask app in background
cd backend
python ussd_api.py &
FLASK_PID=$!
cd ..

# Wait for Flask to start
sleep 3

# Check if Flask started successfully
if ! curl -s http://localhost:5000/health > /dev/null; then
    echo "❌ Flask failed to start!"
    kill $FLASK_PID 2>/dev/null || true
    exit 1
fi

echo "✅ USSD API running on http://localhost:5000"
echo ""

# Start ngrok
echo "🌐 Starting ngrok tunnel..."
echo ""

# Start ngrok in background and capture URL
ngrok http 5000 --log=stdout > /tmp/ngrok.log &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

# Get public URL from ngrok API
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null || echo "")

if [ -z "$NGROK_URL" ]; then
    echo "⚠️  Could not automatically detect ngrok URL"
    echo "   Please check: http://localhost:4040"
else
    echo "✅ ngrok tunnel established!"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📡 PUBLIC USSD ENDPOINT"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "   USSD Callback URL:  ${NGROK_URL}/ussd"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
fi

echo "📊 Useful URLs:"
echo "   • ngrok Dashboard:  http://localhost:4040"
echo "   • USSD Test Page:   http://localhost:5000/test-ussd"
echo "   • Health Check:     http://localhost:5000/health"
echo "   • Farmer Stats:     http://localhost:5000/stats"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 Configure Africa's Talking:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Go to: https://account.africastalking.com/apps/sandbox/ussd"
echo "2. Set Callback URL to: ${NGROK_URL}/ussd"
echo "3. Save and test by dialing your USSD code"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to stop all services..."
echo ""

# Trap Ctrl+C to cleanup
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $FLASK_PID 2>/dev/null || true
    kill $NGROK_PID 2>/dev/null || true
    echo "✅ All services stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep script running
wait

