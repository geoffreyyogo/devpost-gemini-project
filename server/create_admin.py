"""
Create Admin User for BloomWatch Kenya
Run this script to create or update a farmer account with admin privileges
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv
import logging

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from mongodb_service import MongoDBService
from auth_service import AuthService

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_admin_user(phone: str, password: str, name: str = "Admin User", county: str = "Nairobi"):
    """
    Create or update a farmer account with admin privileges
    
    Args:
        phone: Phone number (e.g., +254712345678)
        password: Account password
        name: Admin user's name
        county: County for the admin account
    """
    logger.info("=" * 60)
    logger.info("🔐 BloomWatch Kenya - Create Admin User")
    logger.info("=" * 60)
    
    try:
        # Initialize services
        mongo_service = MongoDBService()
        auth_service = AuthService()
        
        if not mongo_service.is_connected():
            logger.error("❌ Failed to connect to MongoDB")
            logger.info("   Check your MONGODB_URI in .env file")
            return False
        
        logger.info("✓ Connected to MongoDB")
        
        # Check if user already exists
        existing_farmer = mongo_service.get_farmer_by_phone(phone)
        
        if existing_farmer:
            logger.info(f"📝 Farmer account found for {phone}")
            logger.info(f"   Name: {existing_farmer.get('name')}")
            logger.info(f"   County: {existing_farmer.get('county')}")
            
            # Hash the new password using auth_service method
            password_hash, salt = auth_service.hash_password(password)
            
            # Update to admin AND update password
            result = mongo_service.db.farmers.update_one(
                {'phone': phone},
                {
                    '$set': {
                        'is_admin': True,
                        'password_hash': password_hash,
                        'salt': salt,
                        'admin_granted_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info("✅ ADMIN PRIVILEGES GRANTED & PASSWORD UPDATED")
                logger.info("")
                logger.info("=" * 60)
                logger.info("🎉 Admin Account Ready!")
                logger.info("=" * 60)
                logger.info(f"   Phone: {phone}")
                logger.info(f"   Password: {password}")
                logger.info(f"   Name: {existing_farmer.get('name')}")
                logger.info(f"   Role: ADMINISTRATOR")
                logger.info("=" * 60)
                logger.info("\n🔑 Login Instructions:")
                logger.info("   1. Go to: http://localhost:3000/login")
                logger.info(f"   2. Phone: {phone}")
                logger.info(f"   3. Password: {password}")
                logger.info("   4. Access admin panel: http://localhost:3000/admin")
                logger.info("=" * 60)
                logger.info("\n⚠️  PASSWORD HAS BEEN UPDATED!")
                logger.info("=" * 60)
                return True
            else:
                logger.info("Account already has admin privileges")
                logger.info("Password has been updated to the new one provided")
                logger.info(f"\n🔑 Login with: {phone} / {password}")
                return True
        
        else:
            logger.info(f"🆕 Creating new admin account for {phone}")
            
            # Create new farmer account with admin flag
            farmer_data = {
                'name': name,
                'phone': phone,
                'email': f'admin@bloomwatch.ke',
                'region': 'nairobi',
                'county': county,
                'farm_size': 0,
                'crops': ['maize', 'beans'],
                'language': 'en',
                'sms_enabled': True,
                'registered_via': 'admin',
                'is_admin': True,
                'admin_granted_at': datetime.now()
            }
            
            # Register with password
            result = auth_service.register_farmer(farmer_data, password)
            
            if result['success']:
                logger.info("✅ ADMIN ACCOUNT CREATED")
                logger.info("")
                logger.info("=" * 60)
                logger.info("🎉 Admin Account Created Successfully!")
                logger.info("=" * 60)
                logger.info(f"   Phone: {phone}")
                logger.info(f"   Password: {password}")
                logger.info(f"   Name: {name}")
                logger.info(f"   Role: ADMINISTRATOR")
                logger.info("=" * 60)
                logger.info("\n🔑 Login Instructions:")
                logger.info("   1. Go to: http://localhost:3000/login")
                logger.info(f"   2. Phone: {phone}")
                logger.info(f"   3. Password: {password}")
                logger.info("   4. Access admin panel: http://localhost:3000/admin")
                logger.info("=" * 60)
                logger.info("\n⚠️  IMPORTANT: Keep these credentials secure!")
                logger.info("=" * 60)
                return True
            else:
                logger.error(f"❌ Failed to create admin account: {result.get('message')}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if mongo_service:
            mongo_service.close()

def list_admins():
    """List all admin users in the database"""
    try:
        mongo_service = MongoDBService()
        
        if not mongo_service.is_connected():
            logger.error("❌ Failed to connect to MongoDB")
            return
        
        admins = list(mongo_service.db.farmers.find({'is_admin': True}))
        
        if not admins:
            logger.info("ℹ️  No admin users found in database")
            logger.info("   Run: python create_admin.py --create")
        else:
            logger.info("=" * 60)
            logger.info(f"👥 Found {len(admins)} admin user(s):")
            logger.info("=" * 60)
            for admin in admins:
                logger.info(f"\n📋 {admin['name']}")
                logger.info(f"   Phone: {admin['phone']}")
                logger.info(f"   County: {admin.get('county', 'N/A')}")
                logger.info(f"   Created: {admin.get('created_at', 'Unknown')}")
                logger.info(f"   Admin since: {admin.get('admin_granted_at', 'Unknown')}")
            logger.info("\n" + "=" * 60)
        
        mongo_service.close()
        
    except Exception as e:
        logger.error(f"Error listing admins: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Create or manage admin users')
    parser.add_argument('--create', action='store_true', help='Create new admin user')
    parser.add_argument('--list', action='store_true', help='List all admin users')
    parser.add_argument('--phone', type=str, help='Phone number (e.g., +254712345678)')
    parser.add_argument('--password', type=str, help='Password for the account')
    parser.add_argument('--name', type=str, default='Admin User', help='Admin user name')
    parser.add_argument('--county', type=str, default='Nairobi', help='Admin user county')
    
    args = parser.parse_args()
    
    if args.list:
        list_admins()
    elif args.create:
        if not args.phone or not args.password:
            logger.error("❌ --phone and --password are required for creating admin")
            logger.info("\nUsage:")
            logger.info("  python create_admin.py --create --phone +254712345678 --password yourpassword")
            logger.info("  python create_admin.py --create --phone +254712345678 --password admin123 --name 'Jane Doe' --county Kiambu")
            sys.exit(1)
        
        success = create_admin_user(
            phone=args.phone,
            password=args.password,
            name=args.name,
            county=args.county
        )
        
        sys.exit(0 if success else 1)
    else:
        print("BloomWatch Kenya - Admin User Management")
        print("=" * 60)
        print("\nUsage:")
        print("  python create_admin.py --list")
        print("    → List all admin users")
        print("")
        print("  python create_admin.py --create --phone +254712345678 --password yourpassword")
        print("    → Create new admin user")
        print("")
        print("  python create_admin.py --create --phone +254712345678 --password admin123 --name 'Admin Name' --county Nairobi")
        print("    → Create admin with custom details")
        print("")
        print("Examples:")
        print("  python create_admin.py --list")
        print("  python create_admin.py --create --phone +254700000000 --password BloomAdmin2025")
        print("=" * 60)

