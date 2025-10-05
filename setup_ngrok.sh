#!/bin/bash
# Setup script for ngrok - Expose USSD API to the internet
# This allows Africa's Talking to send USSD callbacks to your local server

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║      🌾 BloomWatch Kenya - ngrok Setup for USSD Registration      ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if ngrok is installed
if command -v ngrok &> /dev/null; then
    echo "✅ ngrok is already installed"
    ngrok version
else
    echo "📥 Installing ngrok..."
    echo ""
    
    # Detect system architecture
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        NGROK_ARCH="amd64"
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        NGROK_ARCH="arm64"
    else
        echo "❌ Unsupported architecture: $ARCH"
        exit 1
    fi
    
    # Download ngrok
    echo "Downloading ngrok for Linux $NGROK_ARCH..."
    wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-${NGROK_ARCH}.tgz -O /tmp/ngrok.tgz
    
    # Extract and install
    tar -xzf /tmp/ngrok.tgz -C /tmp/
    sudo mv /tmp/ngrok /usr/local/bin/
    sudo chmod +x /usr/local/bin/ngrok
    
    # Cleanup
    rm /tmp/ngrok.tgz
    
    echo "✅ ngrok installed successfully"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Sign up for a free ngrok account:"
echo "   👉 https://dashboard.ngrok.com/signup"
echo ""
echo "2. Get your auth token:"
echo "   👉 https://dashboard.ngrok.com/get-started/your-authtoken"
echo ""
echo "3. Configure ngrok with your auth token:"
echo "   ngrok config add-authtoken YOUR_TOKEN_HERE"
echo ""
echo "4. Run the start script:"
echo "   ./start_ussd_with_ngrok.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

