"""
Farmer Notification Service for BloomWatch Kenya
Supports SMS (Twilio) and Email (SendGrid) alerts for bloom events
"""

import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
import json

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Farmer:
    """Farmer profile with contact information and preferences"""
    id: int
    name: str
    phone: str
    email: str
    location_lat: float
    location_lon: float
    crops: List[str]
    language: str = 'en'  # en, sw (Swahili)
    sms_enabled: bool = True
    email_enabled: bool = True
    alert_radius_km: float = 5.0

@dataclass
class BloomAlert:
    """Bloom event alert information"""
    id: str
    location_lat: float
    location_lon: float
    bloom_intensity: float
    crop_type: str
    alert_type: str  # 'bloom_start', 'bloom_peak', 'bloom_end'
    timestamp: datetime
    message: str

class FarmerDatabase:
    """SQLite database for farmer profiles and alert history"""
    
    def __init__(self, db_path: str = "farmers.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Farmers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS farmers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                email TEXT,
                location_lat REAL NOT NULL,
                location_lon REAL NOT NULL,
                crops TEXT,  -- JSON array
                language TEXT DEFAULT 'en',
                sms_enabled BOOLEAN DEFAULT 1,
                email_enabled BOOLEAN DEFAULT 1,
                alert_radius_km REAL DEFAULT 5.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Alerts history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farmer_id INTEGER,
                alert_id TEXT,
                alert_type TEXT,
                message TEXT,
                sent_sms BOOLEAN DEFAULT 0,
                sent_email BOOLEAN DEFAULT 0,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (farmer_id) REFERENCES farmers (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_farmer(self, farmer: Farmer) -> int:
        """Add new farmer to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO farmers (name, phone, email, location_lat, location_lon, 
                               crops, language, sms_enabled, email_enabled, alert_radius_km)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            farmer.name, farmer.phone, farmer.email, farmer.location_lat, 
            farmer.location_lon, json.dumps(farmer.crops), farmer.language,
            farmer.sms_enabled, farmer.email_enabled, farmer.alert_radius_km
        ))
        
        farmer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return farmer_id
    
    def get_farmers_in_radius(self, lat: float, lon: float, max_radius_km: float = 50) -> List[Farmer]:
        """Get farmers within radius of bloom event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple distance calculation (for more accuracy, use PostGIS)
        cursor.execute('''
            SELECT * FROM farmers 
            WHERE alert_radius_km >= ? AND
                  ABS(location_lat - ?) * 111 + ABS(location_lon - ?) * 111 * COS(RADIANS(?)) <= ?
        ''', (0, lat, lon, lat, max_radius_km))
        
        farmers = []
        for row in cursor.fetchall():
            farmer = Farmer(
                id=row[0], name=row[1], phone=row[2], email=row[3],
                location_lat=row[4], location_lon=row[5], 
                crops=json.loads(row[6]) if row[6] else [],
                language=row[7], sms_enabled=bool(row[8]), 
                email_enabled=bool(row[9]), alert_radius_km=row[10]
            )
            farmers.append(farmer)
        
        conn.close()
        return farmers

class NotificationService:
    """Main notification service for sending alerts to farmers"""
    
    def __init__(self):
        self.db = FarmerDatabase()
        
        # Initialize Twilio (SMS)
        self.twilio_client = None
        if os.getenv('TWILIO_ACCOUNT_SID') and os.getenv('TWILIO_AUTH_TOKEN'):
            self.twilio_client = Client(
                os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN')
            )
            self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        
        # Initialize SendGrid (Email)
        self.sendgrid_client = None
        if os.getenv('SENDGRID_API_KEY'):
            self.sendgrid_client = SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
            self.from_email = os.getenv('FROM_EMAIL', 'alerts@bloomwatch.ke')
    
    def generate_message(self, alert: BloomAlert, farmer: Farmer) -> Dict[str, str]:
        """Generate localized messages for farmers"""
        
        messages = {
            'en': {
                'bloom_start': f"🌸 BloomWatch Alert: {alert.crop_type} blooming detected near your farm! "
                              f"Intensity: {alert.bloom_intensity:.1f}. Check your crops for optimal harvest timing.",
                'bloom_peak': f"🌺 Peak Bloom Alert: {alert.crop_type} at peak bloom near you! "
                             f"Perfect time for pollination activities. Intensity: {alert.bloom_intensity:.1f}",
                'bloom_end': f"🍃 Bloom Ending: {alert.crop_type} bloom cycle ending. "
                            f"Consider post-bloom care and disease prevention."
            },
            'sw': {  # Swahili
                'bloom_start': f"🌸 Onyo la BloomWatch: {alert.crop_type} inaanza kuchanua karibu na shamba lako! "
                              f"Nguvu: {alert.bloom_intensity:.1f}. Angalia mazao yako kwa wakati mzuri wa kuvuna.",
                'bloom_peak': f"🌺 Onyo la Kilele cha Kuchanua: {alert.crop_type} iko kwenye kilele cha kuchanua! "
                             f"Wakati mzuri wa shughuli za uchavushaji. Nguvu: {alert.bloom_intensity:.1f}",
                'bloom_end': f"🍃 Kuchanua Kunaisha: Mzunguko wa kuchanua kwa {alert.crop_type} unaisha. "
                            f"Fikiria utunzaji baada ya kuchanua na kuzuia magonjwa."
            }
        }
        
        lang = farmer.language if farmer.language in messages else 'en'
        message = messages[lang].get(alert.alert_type, messages['en'][alert.alert_type])
        
        return {
            'sms': message,
            'email_subject': f"BloomWatch Alert - {alert.crop_type} {alert.alert_type.replace('_', ' ').title()}",
            'email_body': f"""
Dear {farmer.name},

{message}

Location: {alert.location_lat:.4f}, {alert.location_lon:.4f}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M')}

For more details, visit our dashboard or reply to this message.

Best regards,
BloomWatch Kenya Team
Powered by NASA Earth Observation Data
            """
        }
    
    def send_sms(self, farmer: Farmer, message: str) -> bool:
        """Send SMS alert to farmer"""
        if not self.twilio_client or not farmer.sms_enabled:
            return False
        
        try:
            # Format phone number for Kenya (+254)
            phone = farmer.phone
            if not phone.startswith('+'):
                if phone.startswith('0'):
                    phone = '+254' + phone[1:]
                else:
                    phone = '+254' + phone
            
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=phone
            )
            
            logger.info(f"SMS sent to {farmer.name} ({phone}): {message_obj.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {farmer.name}: {str(e)}")
            return False
    
    def send_email(self, farmer: Farmer, subject: str, body: str) -> bool:
        """Send email alert to farmer"""
        if not self.sendgrid_client or not farmer.email_enabled or not farmer.email:
            return False
        
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=farmer.email,
                subject=subject,
                html_content=body.replace('\n', '<br>')
            )
            
            response = self.sendgrid_client.send(message)
            logger.info(f"Email sent to {farmer.name} ({farmer.email}): {response.status_code}")
            return response.status_code == 202
            
        except Exception as e:
            logger.error(f"Failed to send email to {farmer.name}: {str(e)}")
            return False
    
    def send_bloom_alert(self, alert: BloomAlert) -> Dict[str, int]:
        """Send bloom alert to all relevant farmers"""
        farmers = self.db.get_farmers_in_radius(
            alert.location_lat, alert.location_lon, max_radius_km=50
        )
        
        stats = {'sms_sent': 0, 'email_sent': 0, 'farmers_notified': 0}
        
        for farmer in farmers:
            # Check if farmer grows the relevant crop
            if alert.crop_type.lower() not in [crop.lower() for crop in farmer.crops]:
                continue
            
            messages = self.generate_message(alert, farmer)
            
            sms_success = self.send_sms(farmer, messages['sms'])
            email_success = self.send_email(farmer, messages['email_subject'], messages['email_body'])
            
            if sms_success:
                stats['sms_sent'] += 1
            if email_success:
                stats['email_sent'] += 1
            if sms_success or email_success:
                stats['farmers_notified'] += 1
            
            # Log to database
            self.log_alert(farmer.id, alert, sms_success, email_success)
        
        logger.info(f"Alert sent: {stats}")
        return stats
    
    def log_alert(self, farmer_id: int, alert: BloomAlert, sms_sent: bool, email_sent: bool):
        """Log alert to database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alert_history (farmer_id, alert_id, alert_type, message, sent_sms, sent_email)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (farmer_id, alert.id, alert.alert_type, alert.message, sms_sent, email_sent))
        
        conn.commit()
        conn.close()

# Example usage and testing
if __name__ == "__main__":
    # Initialize service
    service = NotificationService()
    
    # Add sample farmers
    farmers = [
        Farmer(0, "John Kamau", "0712345678", "john@example.com", -1.2921, 36.8219, 
               ["maize", "beans"], "en"),
        Farmer(0, "Mary Wanjiku", "0723456789", "mary@example.com", -1.2821, 36.8319, 
               ["coffee", "maize"], "sw"),
    ]
    
    for farmer in farmers:
        service.db.add_farmer(farmer)
    
    # Create sample bloom alert
    alert = BloomAlert(
        id="bloom_001",
        location_lat=-1.2921,
        location_lon=36.8219,
        bloom_intensity=0.8,
        crop_type="maize",
        alert_type="bloom_start",
        timestamp=datetime.now(),
        message="Maize bloom detected"
    )
    
    # Send alert (will only work with proper API keys)
    stats = service.send_bloom_alert(alert)
    print(f"Notification stats: {stats}")
