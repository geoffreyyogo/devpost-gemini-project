"""
Test script for farmer registration
Tests both registration and login functionality
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

from auth_service import AuthService
from mongodb_service import MongoDBService

print("🌾 BloomWatch Kenya - Registration Test")
print("=" * 60)

# Initialize services
auth_service = AuthService()
mongo_service = MongoDBService()

if not mongo_service.is_connected():
    print("❌ MongoDB not connected. Please check your connection.")
    sys.exit(1)

print("✓ Connected to MongoDB")
print()

# Test 1: Register a new farmer
print("Test 1: Registering a new farmer...")
test_farmer = {
    'name': 'Test Farmer Registration',
    'phone': '+254798765432',
    'email': 'testfarmer@example.com',
    'region': 'central',
    'crops': ['maize', 'beans'],
    'language': 'en',
    'location_lat': -1.2921,
    'location_lon': 36.8219,
    'sms_enabled': True,
    'registered_via': 'web'
}

result = auth_service.register_farmer(test_farmer, 'testpassword123')
print(f"Registration Result: {result}")

if result['success']:
    print("✅ Registration successful!")
    print(f"   Farmer ID: {result.get('farmer_id')}")
    print(f"   Is New: {result.get('is_new')}")
else:
    print(f"❌ Registration failed: {result.get('message')}")
    if 'already registered' in result.get('message', ''):
        print("   (This is expected if farmer already exists)")

print()

# Test 2: Login with the registered farmer
print("Test 2: Testing login...")
login_result = auth_service.login('+254798765432', 'testpassword123')

if login_result['success']:
    print("✅ Login successful!")
    print(f"   Farmer Name: {login_result['farmer'].get('name')}")
    print(f"   Phone: {login_result['farmer'].get('phone')}")
    print(f"   Region: {login_result['farmer'].get('region')}")
    print(f"   Crops: {', '.join(login_result['farmer'].get('crops', []))}")
    print(f"   Session Token: {login_result['session_token'][:20]}...")
    
    # Test 3: Verify session
    print()
    print("Test 3: Verifying session...")
    session = auth_service.verify_session(login_result['session_token'])
    if session:
        print("✅ Session verified successfully!")
        print(f"   Farmer ID: {session.get('farmer_id')}")
        print(f"   Phone: {session.get('phone')}")
    else:
        print("❌ Session verification failed")
    
    # Test 4: Get farmer from session
    print()
    print("Test 4: Getting farmer from session...")
    farmer = auth_service.get_farmer_from_session(login_result['session_token'])
    if farmer:
        print("✅ Farmer retrieved from session!")
        print(f"   Name: {farmer.get('name')}")
        print(f"   Email: {farmer.get('email')}")
    else:
        print("❌ Failed to get farmer from session")
    
    # Test 5: Logout
    print()
    print("Test 5: Testing logout...")
    logout_success = auth_service.logout(login_result['session_token'])
    if logout_success:
        print("✅ Logout successful!")
    else:
        print("❌ Logout failed")
else:
    print(f"❌ Login failed: {login_result.get('message')}")

print()

# Test 6: Test login with existing sample farmer
print("Test 6: Testing login with sample farmer...")
sample_login = auth_service.login('+254712345678', 'password123')

if sample_login['success']:
    print("✅ Sample farmer login successful!")
    print(f"   Name: {sample_login['farmer'].get('name')}")
    print(f"   Region: {sample_login['farmer'].get('region')}")
    print(f"   Crops: {', '.join(sample_login['farmer'].get('crops', []))}")
else:
    print(f"❌ Sample farmer login failed: {sample_login.get('message')}")

print()

# Display database statistics
print("=" * 60)
print("📊 Database Statistics:")
stats = mongo_service.get_farmer_statistics()
print(f"   Total Farmers: {stats.get('total_farmers', 0)}")
print(f"   Active Farmers: {stats.get('active_farmers', 0)}")
print(f"   Farmers by Region: {stats.get('farmers_by_region', {})}")
print(f"   Farmers by Crop: {stats.get('farmers_by_crop', {})}")

print()
print("=" * 60)
print("✅ All tests completed!")
print()
print("🌐 You can now test the Streamlit app at: http://localhost:8501")
print("   - Click 'Get Started' or 'Register'")
print("   - Fill in the registration form")
print("   - Login credentials for sample farmers:")
print("     Phone: +254712345678")
print("     Password: password123")
print("=" * 60)

mongo_service.close()

