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
            # Add SSL/TLS parameters for Atlas compatibility in WSL
            import ssl
            import certifi
            
            # Create custom SSL context for WSL
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Increased timeouts for WSL2 DNS resolution issues
            self.client = MongoClient(
                self.connection_string, 
                serverSelectionTimeoutMS=30000,  # Increased from 5s to 30s
                connectTimeoutMS=30000,  # 30 seconds for initial connection
                socketTimeoutMS=30000,   # 30 seconds for socket operations
                tls=True,
                tlsAllowInvalidCertificates=True,
                tlsCAFile=certifi.where(),
                retryWrites=True,  # Enable retry writes
                retryReads=True,   # Enable retry reads
                maxPoolSize=10,
                minPoolSize=1
            )
            # Test connection with retry
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    self.client.server_info()
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise e
                    logger.warning(f"MongoDB connection attempt {retry_count} failed, retrying...")
                    import time
                    time.sleep(2)
            
            self.db = self.client['bloomwatch_kenya']
            logger.info("✓ Connected to MongoDB successfully")
            
            # Initialize collections
            self.farmers = self.db['farmers']
            self.alerts = self.db['alerts']
            self.ussd_sessions = self.db['ussd_sessions']
            self.bloom_events = self.db['bloom_events']
            self.crops = self.db['crops']
            self.regions = self.db['regions']
            self.message_templates = self.db['message_templates']
            self.agricultural_advice = self.db['agricultural_advice']
            self.system_config = self.db['system_config']
            
            # Create indexes
            self._create_indexes()
            
        except Exception as e:
            logger.warning(f"MongoDB connection failed: {e}")
            logger.info("Running in demo mode without MongoDB")
            self.client = None
            self.db = None
            self.farmers = None
            self.alerts = None
            self.ussd_sessions = None
            self.bloom_events = None
            self.crops = None
            self.regions = None
            self.message_templates = None
            self.agricultural_advice = None
            self.system_config = None
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        if self.db is None:
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
        
        # Reference data indexes
        self.crops.create_index('crop_id', unique=True)
        self.regions.create_index('region_id', unique=True)
        self.message_templates.create_index('template_id', unique=True)
        self.message_templates.create_index('category')
        self.agricultural_advice.create_index([('crop', ASCENDING), ('stage', ASCENDING)])
        
        logger.info("✓ Database indexes created")
    
    def is_connected(self):
        """Check if MongoDB is connected"""
        return self.client is not None and self.db is not None
    
    def get_db(self):
        """Get database object"""
        return self.db
    
    def get_farmers_collection(self):
        """Get farmers collection"""
        return self.farmers
    
    def get_sessions_collection(self):
        """Get USSD sessions collection"""
        return self.ussd_sessions
    
    def get_alerts_collection(self):
        """Get alerts collection"""
        return self.alerts
    
    def register_farmer(self, farmer_data: Dict) -> Dict:
        """Register a new farmer or update existing"""
        if self.db is None:
            return {'success': False, 'message': 'MongoDB not available', 'demo': True}
        
        try:
            # Add metadata
            farmer_data['updated_at'] = datetime.now()
            farmer_data['active'] = True
            
            if 'alert_count' not in farmer_data:
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
        if self.db is None:
            return None
        
        farmer = self.farmers.find_one({'phone': phone})
        if farmer:
            farmer['_id'] = str(farmer['_id'])
        return farmer
    
    def get_farmers_in_radius(self, lat: float, lon: float, radius_km: float = 50) -> List[Dict]:
        """Get farmers within radius using geospatial query"""
        if self.db is None:
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
        if self.db is None:
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
        if self.db is None:
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
        if self.db is None:
            return False
        
        try:
            # Prepare update data without created_at
            update_data = {k: v for k, v in session_data.items() if k != 'created_at'}
            update_data['session_id'] = session_id
            update_data['updated_at'] = datetime.now()
            
            self.ussd_sessions.update_one(
                {'session_id': session_id},
                {'$set': update_data, '$setOnInsert': {'created_at': datetime.now()}},
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving USSD session: {e}")
            return False
    
    def get_ussd_session(self, session_id: str) -> Optional[Dict]:
        """Get USSD session data"""
        if self.db is None:
            return None
        
        return self.ussd_sessions.find_one({'session_id': session_id})
    
    def save_bloom_event(self, event_data: Dict) -> str:
        """Save bloom event detection"""
        if self.db is None:
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
        if self.db is None:
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
        if self.db is None:
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
    
    def get_template(self, template_id: str, language: str = 'en') -> Optional[Dict]:
        """Get message template by ID"""
        if self.db is None:
            return None
        
        template = self.message_templates.find_one({'template_id': template_id})
        return template
    
    def get_crop_info(self, crop_id: str) -> Optional[Dict]:
        """Get crop information"""
        if self.db is None:
            return None
        
        crop = self.crops.find_one({'crop_id': crop_id})
        if crop:
            crop['_id'] = str(crop['_id'])
        return crop
    
    def get_region_info(self, region_id: str) -> Optional[Dict]:
        """Get region information"""
        if self.db is None:
            return None
        
        region = self.regions.find_one({'region_id': region_id})
        if region:
            region['_id'] = str(region['_id'])
        return region
    
    def get_agricultural_advice(self, crop: str, stage: str, language: str = 'en') -> Optional[str]:
        """Get agricultural advice for crop and stage"""
        if self.db is None:
            return None
        
        advice = self.agricultural_advice.find_one({'crop': crop, 'stage': stage})
        if advice:
            return advice.get(f'advice_{language}', advice.get('advice_en'))
        return None
    
    def get_all_crops(self) -> List[Dict]:
        """Get all available crops"""
        if self.db is None:
            return []
        
        crops = list(self.crops.find({}))
        for crop in crops:
            crop['_id'] = str(crop['_id'])
        return crops
    
    def get_all_regions(self) -> List[Dict]:
        """Get all available regions"""
        if self.db is None:
            return []
        
        regions = list(self.regions.find({}))
        for region in regions:
            region['_id'] = str(region['_id'])
        return regions
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alerts"""
        if self.db is None:
            return []
        
        try:
            alerts = list(self.alerts.find().sort('sent_at', -1).limit(limit))
            return alerts
        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
            return []
    
    def delete_farmer(self, farmer_id: str) -> bool:
        """Delete a farmer by ID"""
        if self.db is None:
            return False
        
        try:
            from bson import ObjectId
            result = self.farmers.delete_one({'_id': ObjectId(farmer_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting farmer: {e}")
            return False
    
    def get_recent_registrations(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """Get recent farmer registrations"""
        if self.db is None:
            return []
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            farmers = list(
                self.farmers.find({
                    'registered_at': {'$gte': cutoff_date}
                }).sort('registered_at', -1).limit(limit)
            )
            return farmers
        except Exception as e:
            logger.error(f"Error getting recent registrations: {e}")
            return []

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

