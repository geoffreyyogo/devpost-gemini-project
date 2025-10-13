"""
Authentication Service for BloomWatch Kenya
Handles user login, session management, and password hashing
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from mongodb_service import MongoDBService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional imports for smart alerts
try:
    from smart_alert_service import SmartAlertService
    from bloom_processor import BloomProcessor
    from africastalking_service import AfricasTalkingService
    SMART_ALERTS_AVAILABLE = True
except ImportError:
    SMART_ALERTS_AVAILABLE = False
    logger.warning("Smart alerts not available - missing dependencies")

class AuthService:
    """Authentication and session management"""
    
    def __init__(self, mongo_service=None):
        self.mongo = mongo_service if mongo_service is not None else MongoDBService()
        self.sessions = {}  # In-memory sessions (fallback)
        
        # Use MongoDB for session persistence
        if self.mongo and self.mongo.db is not None:
            self.db_sessions = self.mongo.db['sessions']
            # Create index for session expiry
            try:
                self.db_sessions.create_index('expires_at', expireAfterSeconds=0)
                self.db_sessions.create_index('session_token', unique=True)
            except:
                pass
        else:
            self.db_sessions = None
        
        # Initialize smart alert service if available
        if SMART_ALERTS_AVAILABLE:
            try:
                self.at_service = AfricasTalkingService()
                self.bloom_processor = BloomProcessor()
                self.alert_service = SmartAlertService(
                    mongo_service=self.mongo,
                    africastalking_service=self.at_service
                )
                logger.info("Smart alerts enabled")
            except Exception as e:
                logger.warning(f"Could not initialize smart alerts: {e}")
                self.alert_service = None
        else:
            self.alert_service = None
    
    def hash_password(self, password: str, salt: str = None) -> tuple:
        """Hash password with salt"""
        if not salt:
            salt = secrets.token_hex(16)
        
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        
        return pwd_hash.hex(), salt
    
    def verify_password(self, password: str, pwd_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        computed_hash, _ = self.hash_password(password, salt)
        return computed_hash == pwd_hash
    
    def register_farmer(self, farmer_data: Dict, password: str) -> Dict:
        """Register new farmer with password"""
        if self.mongo.db is None:
            return {'success': False, 'message': 'Database not available', 'demo': True}
        
        # Check if phone already exists
        existing = self.mongo.get_farmer_by_phone(farmer_data['phone'])
        if existing:
            return {'success': False, 'message': 'Phone number already registered'}
        
        # Hash password
        pwd_hash, salt = self.hash_password(password)
        farmer_data['password_hash'] = pwd_hash
        farmer_data['password_salt'] = salt
        
        # Register farmer
        result = self.mongo.register_farmer(farmer_data)
        
        if result['success']:
            logger.info(f"✓ New farmer registered: {farmer_data['name']}")
            
            # Send welcome alert with current bloom status
            if self.alert_service:
                try:
                    logger.info(f"Sending welcome alert to {farmer_data['name']}...")
                    
                    # Get current bloom data for farmer's region
                    bloom_data = self.bloom_processor.detect_bloom_events(farmer_data.get('region', 'kenya'))
                    
                    # Send personalized welcome SMS
                    alert_result = self.alert_service.send_welcome_alert(farmer_data, bloom_data)
                    
                    if alert_result['success']:
                        logger.info(f"✓ Sent {alert_result['alerts_sent']} welcome alerts to {farmer_data['name']}")
                        result['alerts_sent'] = alert_result['alerts_sent']
                    else:
                        logger.warning("Failed to send welcome alerts")
                        
                except Exception as e:
                    logger.error(f"Error sending welcome alert: {e}")
                    # Don't fail registration if alert fails
        
        return result
    
    def login(self, phone: str, password: str) -> Dict:
        """Authenticate farmer"""
        if self.mongo.db is None:
            # Demo mode
            return {
                'success': True,
                'demo': True,
                'farmer': {
                    'phone': phone,
                    'name': 'Demo Farmer',
                    'region': 'central',
                    'crops': ['maize', 'beans']
                },
                'session_token': 'demo_token'
            }
        
        farmer = self.mongo.get_farmer_by_phone(phone)
        
        if not farmer:
            return {'success': False, 'message': 'Phone number not registered'}
        
        # Verify password
        if not self.verify_password(password, farmer['password_hash'], farmer['password_salt']):
            return {'success': False, 'message': 'Incorrect password'}
        
        # Create session
        session_token = secrets.token_urlsafe(32)
        session_data = {
            'session_token': session_token,
            'farmer_id': str(farmer['_id']),
            'phone': farmer['phone'],
            'farmer_data': {
                'phone': farmer['phone'],
                'name': farmer['name'],
                'email': farmer.get('email'),
                'region': farmer.get('region'),
                'county': farmer.get('county'),
                'crops': farmer.get('crops', []),
                'language': farmer.get('language', 'en'),
                'created_at': farmer.get('created_at'),
                'farm_size': farmer.get('farm_size')
            },
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=24)  # Industry standard: 24 hours
        }
        
        # Store in memory
        self.sessions[session_token] = session_data
        
        # Also store in MongoDB for persistence
        if self.db_sessions is not None:
            try:
                # Remove old sessions for this farmer
                self.db_sessions.delete_many({'phone': farmer['phone']})
                # Insert new session
                self.db_sessions.insert_one(session_data)
            except Exception as e:
                logger.warning(f"Could not persist session to DB: {e}")
        
        # Update last login
        if self.mongo.db is not None:
            self.mongo.farmers.update_one(
                {'phone': phone},
                {'$set': {'last_login': datetime.now()}}
            )
        
        # Remove sensitive data
        farmer.pop('password_hash', None)
        farmer.pop('password_salt', None)
        
        logger.info(f"✓ Farmer logged in: {farmer['name']}")
        
        return {
            'success': True,
            'farmer': farmer,
            'session_token': session_token
        }
    
    def verify_session(self, session_token: str) -> Optional[Dict]:
        """Verify session token - checks both memory and MongoDB"""
        if session_token == 'demo_token':
            return {
                'phone': 'demo',
                'farmer_id': 'demo',
                'demo': True,
                'farmer_data': {
                    'phone': 'demo',
                    'name': 'Demo Farmer',
                    'region': 'central',
                    'crops': ['maize', 'beans'],
                    'language': 'en'
                }
            }
        
        # First check in-memory sessions
        session = self.sessions.get(session_token)
        
        # If not in memory, check MongoDB
        if not session and self.db_sessions is not None:
            try:
                session = self.db_sessions.find_one({'session_token': session_token})
                if session:
                    # Restore to memory for faster access
                    self.sessions[session_token] = session
            except Exception as e:
                logger.warning(f"Could not retrieve session from DB: {e}")
                return None
        
        if not session:
            return None
        
        # Check if expired
        expires_at = session.get('expires_at')
        if expires_at and datetime.now() > expires_at:
            # Delete expired session
            del self.sessions[session_token]
            if self.db_sessions is not None:
                try:
                    self.db_sessions.delete_one({'session_token': session_token})
                except:
                    pass
            return None
        
        return session
    
    def logout(self, session_token: str) -> bool:
        """Logout and invalidate session"""
        # Remove from memory
        if session_token in self.sessions:
            del self.sessions[session_token]
        
        # Remove from MongoDB
        if self.db_sessions is not None:
            try:
                self.db_sessions.delete_one({'session_token': session_token})
            except Exception as e:
                logger.warning(f"Could not delete session from DB: {e}")
        
        logger.info("✓ Farmer logged out")
        return True
    
    def get_farmer_from_session(self, session_token: str) -> Optional[Dict]:
        """Get farmer data from session"""
        session = self.verify_session(session_token)
        
        if not session:
            return None
        
        if session.get('demo'):
            return {
                'phone': 'demo',
                'name': 'Demo Farmer',
                'region': 'central',
                'crops': ['maize', 'beans'],
                'language': 'en',
                'demo': True
            }
        
        farmer_id = session.get('farmer_id')
        if not farmer_id or self.mongo.db is None:
            return None
        
        from bson import ObjectId
        # Convert string ID to ObjectId if needed
        if isinstance(farmer_id, str):
            try:
                farmer_id = ObjectId(farmer_id)
            except:
                return None
        
        farmer = self.mongo.farmers.find_one({'_id': farmer_id})
        if farmer:
            farmer['_id'] = str(farmer['_id'])
            farmer.pop('password_hash', None)
            farmer.pop('password_salt', None)
        
        return farmer
    
    def update_farmer_profile(self, session_token: str, updates: Dict) -> Dict:
        """Update farmer profile"""
        session = self.verify_session(session_token)
        
        if not session:
            return {'success': False, 'message': 'Session expired'}
        
        if session.get('demo'):
            return {'success': True, 'message': 'Profile updated (demo mode)', 'demo': True}
        
        from bson import ObjectId
        farmer_id = session.get('farmer_id')
        
        # Convert string ID to ObjectId if needed
        if isinstance(farmer_id, str):
            try:
                farmer_id = ObjectId(farmer_id)
            except:
                return {'success': False, 'message': 'Invalid farmer ID'}
        
        # Don't allow updating sensitive fields
        updates.pop('password_hash', None)
        updates.pop('password_salt', None)
        updates.pop('phone', None)
        updates['updated_at'] = datetime.now()
        
        if self.mongo.db is not None:
            self.mongo.farmers.update_one(
                {'_id': farmer_id},
                {'$set': updates}
            )
        
        return {'success': True, 'message': 'Profile updated successfully'}
    
    def change_password(self, session_token: str, old_password: str, new_password: str) -> Dict:
        """Change farmer password"""
        session = self.verify_session(session_token)
        
        if not session:
            return {'success': False, 'message': 'Session expired'}
        
        if session.get('demo'):
            return {'success': True, 'message': 'Password changed (demo mode)', 'demo': True}
        
        from bson import ObjectId
        farmer_id = session.get('farmer_id')
        
        # Convert string ID to ObjectId if needed
        if isinstance(farmer_id, str):
            try:
                farmer_id = ObjectId(farmer_id)
            except:
                return {'success': False, 'message': 'Invalid farmer ID'}
        
        farmer = self.mongo.farmers.find_one({'_id': farmer_id})
        
        if not farmer:
            return {'success': False, 'message': 'Farmer not found'}
        
        # Verify old password
        if not self.verify_password(old_password, farmer['password_hash'], farmer['password_salt']):
            return {'success': False, 'message': 'Incorrect current password'}
        
        # Hash new password
        pwd_hash, salt = self.hash_password(new_password)
        
        self.mongo.farmers.update_one(
            {'_id': farmer_id},
            {'$set': {
                'password_hash': pwd_hash,
                'password_salt': salt,
                'password_changed_at': datetime.now()
            }}
        )
        
        return {'success': True, 'message': 'Password changed successfully'}

# Testing
if __name__ == "__main__":
    print("🌾 BloomWatch Kenya - Auth Service Test")
    print("=" * 60)
    
    auth = AuthService()
    
    # Test registration
    test_farmer = {
        'name': 'Test Farmer',
        'phone': '+254799999999',
        'email': 'test@example.com',
        'location_lat': -1.2921,
        'location_lon': 36.8219,
        'region': 'central',
        'crops': ['maize', 'beans'],
        'language': 'en'
    }
    
    result = auth.register_farmer(test_farmer, 'test123')
    print(f"\n✓ Registration: {result}")
    
    # Test login
    login_result = auth.login('+254799999999', 'test123')
    print(f"✓ Login: Success={login_result['success']}")
    
    if login_result['success']:
        token = login_result['session_token']
        
        # Test session verification
        session = auth.verify_session(token)
        print(f"✓ Session verified: {session is not None}")
        
        # Test logout
        auth.logout(token)
        print(f"✓ Logout successful")
    
    print("\n🛰️ Auth service test completed!")

