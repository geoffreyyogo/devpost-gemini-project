#!/bin/bash
# WSL2 DNS Fix for MongoDB Atlas Connectivity
# This script fixes DNS resolution issues in WSL2

echo "🔧 Fixing WSL2 DNS Configuration..."

# Backup original resolv.conf
sudo cp /etc/resolv.conf /etc/resolv.conf.backup

# Configure WSL to not auto-generate resolv.conf
sudo tee /etc/wsl.conf > /dev/null <<EOF
[network]
generateResolvConf = false
EOF

# Set Google DNS and Cloudflare DNS
sudo tee /etc/resolv.conf > /dev/null <<EOF
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
nameserver 1.0.0.1
EOF

# Make it immutable to prevent WSL from overwriting
sudo chattr +i /etc/resolv.conf

echo "✅ DNS configuration updated!"
echo "⚠️  Please restart WSL2 for changes to take effect:"
echo "   1. Exit all WSL terminals"
echo "   2. In PowerShell/CMD run: wsl --shutdown"
echo "   3. Start WSL again"
echo ""
echo "📝 To test DNS after restart, run:"
echo "   nslookup cluster0-shard-00-00.ka2dl.mongodb.net"

