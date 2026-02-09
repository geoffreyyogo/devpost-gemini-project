#!/bin/bash

# Smart Shamba Frontend - Installation Script
# This script sets up the Next.js frontend automatically

set -e  # Exit on error

echo "🌾 Smart Shamba - Frontend Installation"
echo "==========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Node.js is installed
echo -e "${BLUE}Checking prerequisites...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    echo "Please install Node.js 18+ from: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo -e "${RED}❌ Node.js version must be 18 or higher (current: $(node -v))${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Node.js $(node -v) detected${NC}"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ npm $(npm -v) detected${NC}"
echo ""

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
npm install

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi
echo ""

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    echo -e "${BLUE}Creating environment file...${NC}"
    
    # Generate a random secret
    SECRET=$(openssl rand -base64 32 2>/dev/null || echo "change-this-secret-in-production")
    
    cat > .env.local << EOF
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXT_PUBLIC_APP_NAME=Smart Shamba

# NextAuth
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=$SECRET

# Optional: Add your own API keys below
# OPENAI_API_KEY=
# SENDGRID_API_KEY=
EOF
    
    echo -e "${GREEN}✓ Created .env.local${NC}"
    echo -e "${BLUE}  Please edit .env.local with your actual API keys${NC}"
else
    echo -e "${GREEN}✓ .env.local already exists${NC}"
fi
echo ""

# Check if backend is running
echo -e "${BLUE}Checking backend connection...${NC}"
BACKEND_URL="http://localhost:5000"

if curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health" | grep -q "200"; then
    echo -e "${GREEN}✓ Backend is running at $BACKEND_URL${NC}"
else
    echo -e "${RED}⚠ Backend is not responding at $BACKEND_URL${NC}"
    echo -e "${BLUE}  Make sure your Python backend is running:${NC}"
    echo -e "${BLUE}    cd ../backend${NC}"
    echo -e "${BLUE}    python ussd_api.py${NC}"
fi
echo ""

# Build check (optional)
read -p "Do you want to test the build? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Testing production build...${NC}"
    npm run build
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Build successful!${NC}"
    else
        echo -e "${RED}❌ Build failed${NC}"
        echo -e "${BLUE}  Check the error messages above${NC}"
        exit 1
    fi
fi
echo ""

# Success message
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}🎉 Installation Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo -e "1. ${GREEN}Configure your environment:${NC}"
echo -e "   nano .env.local"
echo ""
echo -e "2. ${GREEN}Start the development server:${NC}"
echo -e "   npm run dev"
echo ""
echo -e "3. ${GREEN}Open your browser:${NC}"
echo -e "   http://localhost:3000"
echo ""
echo -e "4. ${GREEN}Read the documentation:${NC}"
echo -e "   - README.md (overview)"
echo -e "   - SETUP_GUIDE.md (detailed setup)"
echo -e "   - IMPLEMENTATION_SUMMARY.md (what's included)"
echo ""
echo -e "${BLUE}For help, check the documentation or run: npm run dev${NC}"
echo ""

