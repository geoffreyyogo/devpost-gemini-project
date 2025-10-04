"""
MongoDB Service for BloomWatch Kenya
Manages farmer data, alerts, and USSD sessions
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBService:
    """MongoDB service for farmer and alert management"""
    
    def __init__(self, connection_string: str = None):
        """Initialize MongoDB connection"""
        self.connection_string = connection_string or os.getenv(
            'MONGODB_URI', 
            'mongodb://localhost:27017/'
        )
        
        try:
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.server_info()
            self.db = self.client['bloomwatch_kenya']
            logger.info("✓ Connected to MongoDB successfully")
            
            # Initialize collections
            self.farmers = self.db['farmers']
            self.alerts = self.db['alerts']
            self.ussd_sessions = self.db['ussd_sessions']
            self.bloom_events = self.db['bloom_events']
            
            # Create indexes
            self._create_indexes()
            
        except Exception as e:
            logger.warning(f"MongoDB connection failed: {e}")
            logger.info("Running in demo mode without MongoDB")
            self.client = None
            self.db = None
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        if not self.db:
            return
        
        # Farmer indexes
        self.farmers.create_index('phone', unique=True)
        self.farmers.create_index([('location', '2dsphere')])
        self.farmers.create_index('region')
        
        # Alert indexes
        self.alerts.create_index('farmer_id')
        self.alerts.create_index('created_at', expireAfterSeconds=2592000)  # 30 days
        
        # USSD session indexes
        self.ussd_sessions.create_index('session_id', unique=True)
        self.ussd_sessions.create_index('created_at', expireAfterSeconds=3600)  # 1 hour
        
        # Bloom event indexes
        self.bloom_events.create_index([('location', '2dsphere')])
        self.bloom_events.create_index('timestamp')
        
        logger.info("✓ Database indexes created")
    
    def register_farmer(self, farmer_data: Dict) -> Dict:
        """Register a new farmer or update existing"""
        if not self.db:
            return {'success': False, 'message': 'MongoDB not available', 'demo': True}
        
        try:
            # Add metadata
            farmer_data['created_at'] = datetime.now()
            farmer_data['updated_at'] = datetime.now()
            farmer_data['active'] = True
            farmer_data['alert_count'] = 0
            
            # Create geospatial index for location-based queries
            if 'location_lat' in farmer_data and 'location_lon' in farmer_data:
                farmer_data['location'] = {
                    'type': 'Point',
                    'coordinates': [farmer_data['location_lon'], farmer_data['location_lat']]
                }
            
            # Upsert farmer (update if exists, insert if new)
            result = self.farmers.update_one(
                {'phone': farmer_data['phone']},
                {'$set': farmer_data, '$setOnInsert': {'created_at': datetime.now()}},
                upsert=True
            )
            
            farmer_id = result.upserted_id if result.upserted_id else self.farmers.find_one(
                {'phone': farmer_data['phone']}
            )['_id']
            
            logger.info(f"✓ Farmer registered: {farmer_data.get('name')} ({farmer_data.get('phone')})")
            
            return {
                'success': True,
                'farmer_id': str(farmer_id),
                'message': 'Farmer registered successfully',
                'is_new': result.upserted_id is not None
            }
            
        except Exception as e:
            logger.error(f"Error registering farmer: {e}")
            return {'success': False, 'message': str(e)}
    
    def get_farmer_by_phone(self, phone: str) -> Optional[Dict]:
        """Get farmer by phone number"""
        if not self.db:
            return None
        
        farmer = self.farmers.find_one({'phone': phone})
        if farmer:
            farmer['_id'] = str(farmer['_id'])
        return farmer
    
    def get_farmers_in_radius(self, lat: float, lon: float, radius_km: float = 50) -> List[Dict]:
        """Get farmers within radius using geospatial query"""
        if not self.db:
            return []
        
        try:
            # MongoDB geospatial query (radius in meters)
            farmers = self.farmers.find({
                'location': {
                    '$near': {
                        '$geometry': {
                            'type': 'Point',
                            'coordinates': [lon, lat]
                        },
                        '$maxDistance': radius_km * 1000  # Convert to meters
                    }
                },
                'active': True,
                'sms_enabled': True
            })
            
            result = []
            for farmer in farmers:
                farmer['_id'] = str(farmer['_id'])
                result.append(farmer)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting farmers in radius: {e}")
            return []
    
    def get_farmers_by_crop(self, crop: str, region: str = None) -> List[Dict]:
        """Get farmers growing specific crop, optionally filtered by region"""
        if not self.db:
            return []
        
        query = {'crops': crop, 'active': True}
        if region:
            query['region'] = region
        
        farmers = self.farmers.find(query)
        result = []
        for farmer in farmers:
            farmer['_id'] = str(farmer['_id'])
            result.append(farmer)
        
        return result
    
    def log_alert(self, farmer_id: str, alert_data: Dict) -> bool:
        """Log an alert sent to farmer"""
        if not self.db:
            return False
        
        try:
            alert_data['farmer_id'] = farmer_id
            alert_data['created_at'] = datetime.now()
            alert_data['status'] = 'sent'
            
            self.alerts.insert_one(alert_data)
            
            # Update farmer alert count
            self.farmers.update_one(
                {'_id': farmer_id},
                {'$inc': {'alert_count': 1}, '$set': {'last_alert': datetime.now()}}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging alert: {e}")
            return False
    
    def save_ussd_session(self, session_id: str, session_data: Dict) -> bool:
        """Save or update USSD session data"""
        if not self.db:
            return False
        
        try:
            session_data['session_id'] = session_id
            session_data['updated_at'] = datetime.now()
            
            self.ussd_sessions.update_one(
                {'session_id': session_id},
                {'$set': session_data, '$setOnInsert': {'created_at': datetime.now()}},
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving USSD session: {e}")
            return False
    
    def get_ussd_session(self, session_id: str) -> Optional[Dict]:
        """Get USSD session data"""
        if not self.db:
            return None
        
        return self.ussd_sessions.find_one({'session_id': session_id})
    
    def save_bloom_event(self, event_data: Dict) -> str:
        """Save bloom event detection"""
        if not self.db:
            return None
        
        try:
            event_data['timestamp'] = datetime.now()
            
            # Create geospatial index
            if 'location_lat' in event_data and 'location_lon' in event_data:
                event_data['location'] = {
                    'type': 'Point',
                    'coordinates': [event_data['location_lon'], event_data['location_lat']]
                }
            
            result = self.bloom_events.insert_one(event_data)
            logger.info(f"✓ Bloom event saved: {event_data.get('crop_type')} in {event_data.get('region')}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error saving bloom event: {e}")
            return None
    
    def get_recent_bloom_events(self, days: int = 7, region: str = None) -> List[Dict]:
        """Get recent bloom events"""
        if not self.db:
            return []
        
        query = {'timestamp': {'$gte': datetime.now() - timedelta(days=days)}}
        if region:
            query['region'] = region
        
        events = self.bloom_events.find(query).sort('timestamp', DESCENDING)
        
        result = []
        for event in events:
            event['_id'] = str(event['_id'])
            result.append(event)
        
        return result
    
    def get_farmer_statistics(self) -> Dict:
        """Get overall farmer statistics"""
        if not self.db:
            return {
                'total_farmers': 0,
                'active_farmers': 0,
                'farmers_by_region': {},
                'farmers_by_crop': {},
                'total_alerts_sent': 0
            }
        
        try:
            stats = {
                'total_farmers': self.farmers.count_documents({}),
                'active_farmers': self.farmers.count_documents({'active': True}),
                'farmers_by_region': {},
                'farmers_by_crop': {},
                'total_alerts_sent': self.alerts.count_documents({})
            }
            
            # Aggregate by region
            region_pipeline = [
                {'$group': {'_id': '$region', 'count': {'$sum': 1}}}
            ]
            for doc in self.farmers.aggregate(region_pipeline):
                stats['farmers_by_region'][doc['_id']] = doc['count']
            
            # Aggregate by crop (unwind array)
            crop_pipeline = [
                {'$unwind': '$crops'},
                {'$group': {'_id': '$crops', 'count': {'$sum': 1}}}
            ]
            for doc in self.farmers.aggregate(crop_pipeline):
                stats['farmers_by_crop'][doc['_id']] = doc['count']
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Demo/Testing
if __name__ == "__main__":
    print("🌾 BloomWatch Kenya - MongoDB Service Test")
    print("=" * 60)
    
    # Initialize service
    mongo = MongoDBService()
    
    # Test farmer registration
    test_farmer = {
        'name': 'John Kamau',
        'phone': '+254712345678',
        'email': 'john@example.com',
        'location_lat': -1.2921,
        'location_lon': 36.8219,
        'region': 'central',
        'crops': ['maize', 'beans'],
        'language': 'en',
        'sms_enabled': True
    }
    
    result = mongo.register_farmer(test_farmer)
    print(f"\n✓ Farmer registration: {result}")
    
    # Test farmer retrieval
    farmer = mongo.get_farmer_by_phone('+254712345678')
    if farmer:
        print(f"✓ Farmer retrieved: {farmer.get('name')}")
    
    # Test statistics
    stats = mongo.get_farmer_statistics()
    print(f"\n📊 Statistics:")
    print(f"   Total farmers: {stats.get('total_farmers', 0)}")
    print(f"   Active farmers: {stats.get('active_farmers', 0)}")
    print(f"   By region: {stats.get('farmers_by_region', {})}")
    
    print("\n🛰️ MongoDB service test completed!")
    mongo.close()

