"""
Africa's Talking Service for BloomWatch Kenya
Handles USSD registration and SMS notifications
"""

import africastalking
import os
from dotenv import load_dotenv
import logging
from typing import Dict, List
from datetime import datetime
from mongodb_service import MongoDBService

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AfricasTalkingService:
    """Africa's Talking integration for USSD and SMS"""
    
    def __init__(self):
        """Initialize Africa's Talking SDK"""
        self.username = os.getenv('AT_USERNAME', 'sandbox')
        self.api_key = os.getenv('AT_API_KEY', '')
        
        if not self.api_key:
            logger.warning("Africa's Talking API key not set. Running in demo mode.")
            self.sms = None
            self.ussd = None
        else:
            try:
                # Initialize SDK
                africastalking.initialize(self.username, self.api_key)
                self.sms = africastalking.SMS
                logger.info("✓ Africa's Talking initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Africa's Talking: {e}")
                self.sms = None
        
        # Initialize MongoDB for farmer data
        self.mongo = MongoDBService()
    
    def send_sms(self, phone: str, message: str) -> Dict:
        """Send SMS to farmer"""
        if not self.sms:
            logger.info(f"[DEMO] Would send SMS to {phone}: {message}")
            return {'success': True, 'demo': True, 'message': 'Demo mode - SMS not actually sent'}
        
        try:
            # Ensure phone number is in international format
            if not phone.startswith('+'):
                if phone.startswith('0'):
                    phone = '+254' + phone[1:]  # Kenya country code
                elif phone.startswith('254'):
                    phone = '+' + phone
                else:
                    phone = '+254' + phone
            
            # Send SMS
            response = self.sms.send(message, [phone])
            
            logger.info(f"✓ SMS sent to {phone}")
            return {
                'success': True,
                'response': response,
                'phone': phone
            }
            
        except Exception as e:
            logger.error(f"Error sending SMS to {phone}: {e}")
            return {
                'success': False,
                'error': str(e),
                'phone': phone
            }
    
    def send_bulk_sms(self, recipients: List[Dict], message_template: str) -> Dict:
        """Send SMS to multiple farmers"""
        results = {'sent': 0, 'failed': 0, 'details': []}
        
        for farmer in recipients:
            phone = farmer.get('phone')
            language = farmer.get('language', 'en')
            
            # Personalize message
            message = message_template.format(
                name=farmer.get('name', 'Farmer'),
                crop=', '.join(farmer.get('crops', ['crop']))
            )
            
            result = self.send_sms(phone, message)
            
            if result.get('success'):
                results['sent'] += 1
                # Log alert to database
                self.mongo.log_alert(farmer.get('_id'), {
                    'type': 'sms',
                    'message': message,
                    'phone': phone,
                    'status': 'sent'
                })
            else:
                results['failed'] += 1
            
            results['details'].append(result)
        
        logger.info(f"✓ Bulk SMS: {results['sent']} sent, {results['failed']} failed")
        return results
    
    def handle_ussd_request(self, session_id: str, service_code: str, 
                           phone_number: str, text: str) -> str:
        """
        Handle USSD registration flow
        USSD Code: *384*1234# (example)
        """
        
        # Get or create session
        session = self.mongo.get_ussd_session(session_id)
        if not session:
            session = {
                'phone': phone_number,
                'step': 0,
                'data': {}
            }
        
        # Parse user input
        user_input = text.split('*')[-1] if text else ''
        
        # USSD Flow
        if text == '':
            # Initial menu
            response = self._ussd_menu_main()
            session['step'] = 1
        
        elif session['step'] == 1:
            # Language selection
            if user_input == '1':
                session['data']['language'] = 'en'
                response = self._ussd_menu_registration_en()
            elif user_input == '2':
                session['data']['language'] = 'sw'
                response = self._ussd_menu_registration_sw()
            else:
                response = "END Invalid option. Please try again."
                user_input = None
            
            if user_input:
                session['step'] = 2
        
        elif session['step'] == 2:
            # Name input
            session['data']['name'] = user_input
            lang = session['data'].get('language', 'en')
            response = self._ussd_prompt_region(lang)
            session['step'] = 3
        
        elif session['step'] == 3:
            # Region selection
            regions = ['central', 'rift_valley', 'western', 'eastern']
            try:
                region_idx = int(user_input) - 1
                if 0 <= region_idx < len(regions):
                    session['data']['region'] = regions[region_idx]
                    lang = session['data'].get('language', 'en')
                    response = self._ussd_prompt_crops(lang)
                    session['step'] = 4
                else:
                    raise ValueError("Invalid region")
            except:
                response = "END Invalid option. Please try again."
                user_input = None
        
        elif session['step'] == 4:
            # Crop selection (comma-separated numbers)
            crops_map = {
                '1': 'maize', '2': 'beans', '3': 'coffee', 
                '4': 'tea', '5': 'wheat', '6': 'sorghum'
            }
            
            selected_crops = []
            for num in user_input.replace(',', ' ').split():
                if num in crops_map:
                    selected_crops.append(crops_map[num])
            
            if selected_crops:
                session['data']['crops'] = selected_crops
                session['step'] = 5
                response = self._ussd_confirm_registration(session['data'])
            else:
                response = "END Invalid crops. Please try again."
                user_input = None
        
        elif session['step'] == 5:
            # Confirmation
            if user_input == '1':
                # Register farmer
                farmer_data = {
                    'phone': phone_number,
                    'name': session['data'].get('name'),
                    'region': session['data'].get('region'),
                    'crops': session['data'].get('crops'),
                    'language': session['data'].get('language', 'en'),
                    'sms_enabled': True,
                    'registered_via': 'ussd',
                    'location_lat': self._get_region_coordinates(session['data'].get('region'))[0],
                    'location_lon': self._get_region_coordinates(session['data'].get('region'))[1]
                }
                
                result = self.mongo.register_farmer(farmer_data)
                
                if result.get('success'):
                    lang = session['data'].get('language', 'en')
                    response = self._ussd_success_message(lang, farmer_data)
                    
                    # Send welcome SMS
                    self._send_welcome_sms(phone_number, farmer_data)
                else:
                    response = "END Registration failed. Please try again later."
            else:
                response = "END Registration cancelled."
        
        else:
            response = "END Session expired. Please try again."
        
        # Save session
        if user_input is not None:
            self.mongo.save_ussd_session(session_id, session)
        
        return response
    
    def _ussd_menu_main(self) -> str:
        """Main USSD menu"""
        return """CON Welcome to BloomWatch Kenya
Karibu BloomWatch Kenya

1. English
2. Kiswahili"""
    
    def _ussd_menu_registration_en(self) -> str:
        """Registration menu (English)"""
        return "CON Enter your full name:"
    
    def _ussd_menu_registration_sw(self) -> str:
        """Registration menu (Kiswahili)"""
        return "CON Weka jina lako kamili:"
    
    def _ussd_prompt_region(self, lang: str) -> str:
        """Prompt for region selection"""
        if lang == 'sw':
            return """CON Chagua mkoa wako:
1. Central (Kiambu, Nyeri)
2. Rift Valley (Nakuru, Eldoret)
3. Western (Kakamega, Bungoma)
4. Eastern (Machakos, Kitui)"""
        else:
            return """CON Select your region:
1. Central (Kiambu, Nyeri)
2. Rift Valley (Nakuru, Eldoret)
3. Western (Kakamega, Bungoma)
4. Eastern (Machakos, Kitui)"""
    
    def _ussd_prompt_crops(self, lang: str) -> str:
        """Prompt for crop selection"""
        if lang == 'sw':
            return """CON Chagua mazao unayolima (e.g. 1,2,3):
1. Mahindi (Maize)
2. Maharage (Beans)
3. Kahawa (Coffee)
4. Chai (Tea)
5. Ngano (Wheat)
6. Mtama (Sorghum)"""
        else:
            return """CON Select crops you grow (e.g. 1,2,3):
1. Maize
2. Beans
3. Coffee
4. Tea
5. Wheat
6. Sorghum"""
    
    def _ussd_confirm_registration(self, data: Dict) -> str:
        """Confirmation screen"""
        lang = data.get('language', 'en')
        crops_str = ', '.join(data.get('crops', []))
        
        if lang == 'sw':
            return f"""CON Thibitisha taarifa zako:
Jina: {data.get('name')}
Mkoa: {data.get('region')}
Mazao: {crops_str}

1. Thibitisha
2. Ghairi"""
        else:
            return f"""CON Confirm your details:
Name: {data.get('name')}
Region: {data.get('region')}
Crops: {crops_str}

1. Confirm
2. Cancel"""
    
    def _ussd_success_message(self, lang: str, data: Dict) -> str:
        """Success message"""
        if lang == 'sw':
            return f"""END Hongera {data.get('name')}!
Umesajiliwa kikamilifu kwenye BloomWatch Kenya.

Utapokea arifa za kuchanua kwa mazao yako kupitia SMS.

Asante!"""
        else:
            return f"""END Congratulations {data.get('name')}!
You are now registered with BloomWatch Kenya.

You will receive bloom alerts for your crops via SMS.

Thank you!"""
    
    def _send_welcome_sms(self, phone: str, farmer_data: Dict):
        """Send welcome SMS to new farmer"""
        lang = farmer_data.get('language', 'en')
        name = farmer_data.get('name', 'Farmer')
        crops = ', '.join(farmer_data.get('crops', []))
        region = farmer_data.get('region', '').replace('_', ' ').title()
        
        if lang == 'sw':
            message = f"""🌾 Karibu BloomWatch Kenya {name}!

✓ USAJILI UMEFANIKIWA

Taarifa zako:
📍 Mkoa: {region}
🌾 Mazao: {crops}

Utapokea:
• Arifa za kuchanua kwa SMS
• Mwongozo wa kilimo
• Habari za hali ya hewa

Ili kubadilisha taarifa, piga *384*1234#

Asante kwa kujiunga nasi!"""
        else:
            message = f"""🌾 Welcome to BloomWatch Kenya {name}!

✓ REGISTRATION SUCCESSFUL

Your Details:
📍 Region: {region}
🌾 Crops: {crops}

You will receive:
• Bloom alerts via SMS
• Farming tips
• Weather updates

To update details, dial *384*1234#

Thank you for joining us!"""
        
        self.send_sms(phone, message)
    
    def send_registration_confirmation(self, phone: str, farmer_data: Dict, via: str = 'web'):
        """Send detailed registration confirmation"""
        lang = farmer_data.get('language', 'en')
        name = farmer_data.get('name', 'Farmer')
        
        if lang == 'sw':
            message = f"""🎉 Hongera {name}!

Usajili wako kwenye BloomWatch Kenya umekamilika.

Nambari yako: {phone}
Njia ya usajili: {'Wavuti' if via == 'web' else 'USSD'}

HATUA ZINAZOFUATA:
1. Utapokea SMS ya uthibitisho (hii!)
2. Ingia kwenye wavuti: bloomwatch.ke
3. Tumia nambari yako ya simu kuingia

Kwa msaada, wasiliana nasi:
📞 USSD: *384*1234#
📧 Email: support@bloomwatch.ke

Asante! 🌾"""
        else:
            message = f"""🎉 Congratulations {name}!

Your registration with BloomWatch Kenya is complete.

Your phone: {phone}
Registered via: {'Website' if via == 'web' else 'USSD'}

NEXT STEPS:
1. You'll receive SMS confirmation (this one!)
2. Visit our website: bloomwatch.ke
3. Login using your phone number

For support, contact us:
📞 USSD: *384*1234#
📧 Email: support@bloomwatch.ke

Thank you! 🌾"""
        
        self.send_sms(phone, message)
    
    def _get_region_coordinates(self, region: str) -> tuple:
        """Get approximate coordinates for region"""
        coords = {
            'central': (-0.9, 36.9),
            'rift_valley': (0.2, 35.8),
            'western': (0.5, 34.8),
            'eastern': (-1.5, 37.5)
        }
        return coords.get(region, (-1.0, 37.0))
    
    def send_bloom_alert(self, farmers: List[Dict], bloom_event: Dict) -> Dict:
        """Send bloom alert to farmers"""
        crop = bloom_event.get('crop_type', 'crop')
        intensity = bloom_event.get('bloom_intensity', 0)
        region = bloom_event.get('region', 'your area')
        
        results = {'sent': 0, 'failed': 0}
        
        for farmer in farmers:
            lang = farmer.get('language', 'en')
            name = farmer.get('name', 'Farmer')
            
            if lang == 'sw':
                message = f"""🌾 BloomWatch: Arifa ya Kuchanua

{name}, {crop} inaanza kuchanua karibu na shamba lako!

Mkoa: {region}
Nguvu: {intensity:.1f}

Angalia mazao yako kwa wakati mzuri wa kuvuna."""
            else:
                message = f"""🌾 BloomWatch: Bloom Alert

{name}, {crop} blooming detected near your farm!

Region: {region}
Intensity: {intensity:.1f}

Monitor your crops for optimal harvest timing."""
            
            result = self.send_sms(farmer.get('phone'), message)
            
            if result.get('success'):
                results['sent'] += 1
                self.mongo.log_alert(farmer.get('_id'), {
                    'type': 'bloom_alert',
                    'crop': crop,
                    'message': message,
                    'bloom_event_id': bloom_event.get('_id')
                })
            else:
                results['failed'] += 1
        
        return results

# Demo/Testing
if __name__ == "__main__":
    print("🌾 BloomWatch Kenya - Africa's Talking Service Test")
    print("=" * 60)
    
    # Initialize service
    at_service = AfricasTalkingService()
    
    # Test USSD flow (simulated)
    print("\n📱 USSD Registration Flow Simulation:")
    print("-" * 60)
    
    # Step 1: Initial request
    response = at_service.handle_ussd_request('test_session_1', '*384*1234#', '+254712345678', '')
    print(f"Step 1 - Initial:\n{response}\n")
    
    # Step 2: Select English
    response = at_service.handle_ussd_request('test_session_1', '*384*1234#', '+254712345678', '1')
    print(f"Step 2 - Language (English):\n{response}\n")
    
    # Step 3: Enter name
    response = at_service.handle_ussd_request('test_session_1', '*384*1234#', '+254712345678', '1*John Kamau')
    print(f"Step 3 - Name:\n{response}\n")
    
    # Step 4: Select region
    response = at_service.handle_ussd_request('test_session_1', '*384*1234#', '+254712345678', '1*John Kamau*1')
    print(f"Step 4 - Region (Central):\n{response}\n")
    
    # Step 5: Select crops
    response = at_service.handle_ussd_request('test_session_1', '*384*1234#', '+254712345678', '1*John Kamau*1*1,2')
    print(f"Step 5 - Crops (Maize, Beans):\n{response}\n")
    
    # Step 6: Confirm
    response = at_service.handle_ussd_request('test_session_1', '*384*1234#', '+254712345678', '1*John Kamau*1*1,2*1')
    print(f"Step 6 - Confirm:\n{response}\n")
    
    print("=" * 60)
    print("🛰️ Africa's Talking service test completed!")

