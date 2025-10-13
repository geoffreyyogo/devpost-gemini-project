#!/bin/bash

# BloomWatch Kenya - Deployment Script
# Automates the deployment process

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║   BloomWatch Kenya - Deployment to Render (Next.js + FastAPI)   ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "ℹ $1"
}

# Step 1: Check if we're in the right directory
echo "Step 1: Verifying directory structure..."
if [ ! -d "frontend" ] || [ ! -d "server" ]; then
    print_error "Error: frontend/ or server/ directory not found!"
    print_info "Make sure you're in the bloom-detector root directory"
    exit 1
fi
print_success "Directory structure verified"
echo ""

# Step 2: Check for uncommitted changes
echo "Step 2: Checking git status..."
if [[ -n $(git status -s) ]]; then
    print_warning "You have uncommitted changes"
    git status -s
    echo ""
    read -p "Do you want to continue? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Deployment cancelled"
        exit 1
    fi
else
    print_success "Working directory is clean"
fi
echo ""

# Step 3: Create deployment branch
echo "Step 3: Creating deployment branch..."
BRANCH_NAME="deploy-nextjs-fastapi"

# Check if branch already exists
if git rev-parse --verify $BRANCH_NAME >/dev/null 2>&1; then
    print_warning "Branch '$BRANCH_NAME' already exists"
    read -p "Switch to existing branch? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git checkout $BRANCH_NAME
        print_success "Switched to branch '$BRANCH_NAME'"
    else
        print_info "Staying on current branch"
    fi
else
    git checkout -b $BRANCH_NAME
    print_success "Created and switched to branch '$BRANCH_NAME'"
fi
echo ""

# Step 4: Stage and commit changes
echo "Step 4: Committing changes..."
read -p "Do you want to commit all changes? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add .
    
    # Default commit message
    COMMIT_MSG="feat: Migrate from Streamlit to Next.js + FastAPI

- Add Next.js frontend with modern UI components
- Add FastAPI backend with improved API structure
- Implement scroll animations and enhanced UX
- Update map components and data visualizations
- Add county-specific ML predictions
- Fix dashboard rendering issues
- Improve admin features and data management"
    
    echo ""
    print_info "Default commit message:"
    echo "$COMMIT_MSG"
    echo ""
    read -p "Use this commit message? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git commit -m "$COMMIT_MSG"
    else
        echo "Enter your commit message (end with Ctrl+D):"
        CUSTOM_MSG=$(cat)
        git commit -m "$CUSTOM_MSG"
    fi
    
    print_success "Changes committed"
else
    print_warning "Skipping commit"
fi
echo ""

# Step 5: Push to GitHub
echo "Step 5: Pushing to GitHub..."
read -p "Push branch '$BRANCH_NAME' to GitHub? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if git push -u origin $BRANCH_NAME; then
        print_success "Pushed to GitHub successfully"
    else
        print_error "Failed to push to GitHub"
        print_info "You may need to push manually: git push -u origin $BRANCH_NAME"
    fi
else
    print_warning "Skipping push to GitHub"
    print_info "Remember to push manually before deploying to Render"
fi
echo ""

# Step 6: Verify deployment files
echo "Step 6: Verifying deployment configuration..."
if [ ! -f "render-nextjs.yaml" ]; then
    print_error "render-nextjs.yaml not found!"
    exit 1
fi
print_success "Deployment configuration found"
echo ""

# Step 7: Check environment variables
echo "Step 7: Environment variables checklist..."
echo ""
print_info "Make sure you have these environment variables ready for Render:"
echo ""
echo "Backend (FastAPI):"
echo "  - MONGODB_URI"
echo "  - AFRICASTALKING_USERNAME"
echo "  - AFRICASTALKING_API_KEY"
echo "  - JWT_SECRET_KEY (will be auto-generated)"
echo ""
echo "Frontend (Next.js):"
echo "  - NEXT_PUBLIC_API_URL (set after backend deploys)"
echo ""
read -p "Do you have all required environment variables? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Get your environment variables ready before deploying"
fi
echo ""

# Step 8: Next steps
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                      NEXT STEPS                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
print_success "Branch '$BRANCH_NAME' is ready for deployment!"
echo ""
print_info "To deploy to Render:"
echo "  1. Go to https://dashboard.render.com"
echo "  2. Click 'New +' → 'Blueprint'"
echo "  3. Connect to your GitHub repo"
echo "  4. Select branch: $BRANCH_NAME"
echo "  5. Render will detect render-nextjs.yaml"
echo "  6. Click 'Apply' to deploy"
echo ""
print_info "After deployment:"
echo "  1. Get backend URL from Render"
echo "  2. Update frontend NEXT_PUBLIC_API_URL"
echo "  3. Test thoroughly at:"
echo "     - Frontend: https://bloomwatch-nextjs.onrender.com"
echo "     - Backend: https://bloomwatch-fastapi.onrender.com"
echo ""
print_info "See DEPLOYMENT_GUIDE.md for complete instructions"
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                   DEPLOYMENT READY! 🚀                           ║"
echo "╚══════════════════════════════════════════════════════════════════╝"

