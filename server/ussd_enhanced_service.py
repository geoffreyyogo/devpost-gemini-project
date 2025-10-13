"""
Enhanced Africa's Talking USSD Service for BloomWatch Kenya
Features:
- Language selection (English/Kiswahili)
- Region -> County selection flow
- Dynamic crop selection based on county
- Farm size capture
- "Other" crop option with text input
- Post-registration menu with Flora AI integration
"""

import africastalking
import os
from dotenv import load_dotenv
import logging
from typing import Dict, List, Optional
from datetime import datetime
from mongodb_service import MongoDBService
from flora_ai_service import FloraAIService
from kenya_regions_counties import (
    KENYA_REGIONS_COUNTIES, ALL_KENYA_CROPS,
    get_ussd_crop_codes, get_counties_by_region
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedUSSDService:
    """Enhanced USSD service with comprehensive registration and Flora AI"""
    
    def __init__(self):
        """Initialize enhanced USSD service"""
        self.username = os.getenv('AFRICASTALKING_USERNAME', 'sandbox')
        self.api_key = os.getenv('AFRICASTALKING_API_KEY', '')
        
        if self.api_key:
            try:
                africastalking.initialize(self.username, self.api_key)
                self.sms = africastalking.SMS
                logger.info("✓ Africa's Talking initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Africa's Talking: {e}")
                self.sms = None
        else:
            logger.warning("Africa's Talking API key not set. Running in demo mode.")
            self.sms = None
        
        self.mongo = MongoDBService()
        self.flora = FloraAIService(self.mongo)
    
    def handle_ussd_request(self, session_id: str, service_code: str, 
                           phone_number: str, text: str) -> str:
        """Main USSD request handler"""
        
        # Check if farmer is registered
        farmer = self.mongo.get_farmer_by_phone(phone_number)
        
        if farmer and text == '':
            # Registered farmer - show main menu
            return self._ussd_main_menu_registered(farmer)
        elif text == '':
            # New farmer - start registration
            return self._ussd_language_selection()
        
        # Get or create session
        session = self.mongo.get_ussd_session(session_id)
        if not session:
            session = {
                'phone': phone_number,
                'step': 'language',
                'data': {},
                'is_registered': farmer is not None
            }
        
        # Route to appropriate handler
        if farmer:
            response = self._handle_registered_user(session, text, farmer)
        else:
            response = self._handle_registration(session, text, phone_number)
        
        # Save session
        self.mongo.save_ussd_session(session_id, session)
        
        return response
    
    # ============================================================================
    # REGISTRATION FLOW
    # ============================================================================
    
    def _ussd_language_selection(self) -> str:
        """Step 1: Language selection"""
        return """CON Welcome to BloomWatch Kenya
Karibu BloomWatch Kenya

Select language / Chagua lugha:
1. English
2. Kiswahili"""
    
    def _handle_registration(self, session: Dict, text: str, phone: str) -> str:
        """Handle registration flow"""
        
        user_input = text.split('*')[-1] if '*' in text else text
        
        # Step 1: Language selection
        if session['step'] == 'language' or text in ['1', '2']:
            if user_input == '1':
                session['data']['language'] = 'en'
                session['step'] = 'name'
                return "CON Enter your full name:"
            elif user_input == '2':
                session['data']['language'] = 'sw'
                session['step'] = 'name'
                return "CON Weka jina lako kamili:"
            else:
                return "END Invalid option. Dial again to retry.\nChaguo batili. Piga tena."
        
        # Step 2: Name
        elif session['step'] == 'name':
            session['data']['name'] = user_input
            session['step'] = 'region'
            return self._ussd_region_selection(session['data']['language'])
        
        # Step 3: Region
        elif session['step'] == 'region':
            regions = list(KENYA_REGIONS_COUNTIES.keys())
            try:
                region_idx = int(user_input) - 1
                if 0 <= region_idx < len(regions):
                    session['data']['region'] = regions[region_idx]
                    session['step'] = 'county'
                    return self._ussd_county_selection(session['data']['region'], session['data']['language'])
                else:
                    raise ValueError("Invalid region")
            except:
                return "END Invalid option. Please try again.\nChaguo batili. Tafadhali jaribu tena."
        
        # Step 4: County
        elif session['step'] == 'county':
            region = session['data']['region']
            counties = get_counties_by_region(region)
            try:
                county_idx = int(user_input) - 1
                if 0 <= county_idx < len(counties):
                    session['data']['county'] = counties[county_idx]
                    session['step'] = 'farm_size'
                    return self._ussd_farm_size_prompt(session['data']['language'])
                else:
                    raise ValueError("Invalid county")
            except:
                return "END Invalid option. Please try again.\nChaguo batili. Tafadhali jaribu tena."
        
        # Step 5: Farm size
        elif session['step'] == 'farm_size':
            try:
                farm_size = float(user_input)
                if farm_size <= 0 or farm_size > 10000:
                    raise ValueError("Invalid farm size")
                session['data']['farm_size'] = farm_size
                session['step'] = 'crops'
                return self._ussd_crop_selection(session['data']['county'], session['data']['language'])
            except:
                lang = session['data']['language']
                if lang == 'sw':
                    return "CON Nambari batili. Weka ukubwa wa shamba kwa ekari (e.g. 2.5):"
                else:
                    return "CON Invalid number. Enter farm size in acres (e.g. 2.5):"
        
        # Step 6: Crops
        elif session['step'] == 'crops':
            return self._handle_crop_selection(session, user_input)
        
        # Step 7: Other crop (if selected)
        elif session['step'] == 'other_crop':
            other_crop = user_input.strip()
            if other_crop:
                if 'crops' not in session['data']:
                    session['data']['crops'] = []
                session['data']['crops'].append(f"other:{other_crop}")
                session['step'] = 'crops_add_more'
                return self._ussd_add_more_crops(session['data']['language'])
            else:
                lang = session['data']['language']
                return "CON Enter crop name:" if lang == 'en' else "CON Weka jina la mazao:"
        
        # Step 8: Add more crops?
        elif session['step'] == 'crops_add_more':
            lang = session['data']['language']
            if user_input == '1':  # Yes, add more
                session['step'] = 'crops'
                return self._ussd_crop_selection(session['data']['county'], lang)
            elif user_input == '2':  # No, continue
                session['step'] = 'confirm'
                return self._ussd_confirm_registration(session['data'])
            else:
                return "END Invalid option.\nChaguo batili."
        
        # Step 9: Confirmation
        elif session['step'] == 'confirm':
            if user_input == '1':  # Confirm
                return self._complete_registration(session, phone)
            else:  # Cancel
                lang = session['data'].get('language', 'en')
                return "END Registration cancelled.\nUsajili umeghairiwa." if lang == 'sw' else "END Registration cancelled."
        
        return "END Session error. Please try again.\nKosa la kipindi. Tafadhali jaribu tena."
    
    def _handle_crop_selection(self, session: Dict, user_input: str) -> str:
        """Handle crop selection with multiple choices"""
        county = session['data']['county']
        lang = session['data']['language']
        crop_codes = get_ussd_crop_codes(county)
        
        if 'crops' not in session['data']:
            session['data']['crops'] = []
        
        # Parse input (can be comma-separated like "1,2,3" or single number)
        selections = [s.strip() for s in user_input.replace(',', ' ').split()]
        
        valid_selections = []
        for sel in selections:
            if sel in crop_codes:
                crop_id = crop_codes[sel]
                if crop_id == 'other':
                    # Handle "Other" option
                    session['step'] = 'other_crop'
                    return "CON Enter crop name:" if lang == 'en' else "CON Weka jina la mazao:"
                else:
                    valid_selections.append(crop_id)
        
        if valid_selections:
            session['data']['crops'].extend(valid_selections)
            session['step'] = 'crops_add_more'
            return self._ussd_add_more_crops(lang)
        else:
            return "END Invalid selection. Please try again.\nChaguo batili. Tafadhali jaribu tena."
    
    def _complete_registration(self, session: Dict, phone: str) -> str:
        """Complete farmer registration"""
        farmer_data = {
            'phone': phone,
            'name': session['data']['name'],
            'county': session['data']['county'],
            'region': session['data']['region'],
            'farm_size': session['data']['farm_size'],
            'crops': session['data']['crops'],
            'language': session['data']['language'],
            'sms_enabled': True,
            'registration_source': 'ussd',  # Track registration source
            'registered_at': datetime.now().isoformat()
        }
        
        # Get county coordinates
        try:
            from kenya_regions_counties import get_county_crops
            import json
            county_id = session['data']['county'].lower().replace(" ", "_").replace("-", "_").replace("'", "")
            file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'county_data', f'{county_id}.json')
            with open(file_path, 'r') as f:
                county_data = json.load(f)
                coords = county_data.get('coordinates', {})
                farmer_data['location_lat'] = coords.get('lat', 0)
                farmer_data['location_lon'] = coords.get('lon', 0)
        except:
            farmer_data['location_lat'] = 0
            farmer_data['location_lon'] = 0
        
        # Register farmer
        result = self.mongo.register_farmer(farmer_data)
        
        if result.get('success'):
            # Send welcome SMS
            self._send_welcome_sms(phone, farmer_data)
            
            lang = session['data']['language']
            name = session['data']['name']
            
            if lang == 'sw':
                return f"""END 🎉 Hongera {name}!

Umesajiliwa kikamilifu kwenye BloomWatch Kenya.

✓ Kaunti: {session['data']['county']}
✓ Ukubwa wa shamba: {session['data']['farm_size']} ekari
✓ Mazao: {len(session['data']['crops'])}

Utapokea SMS na arifa za kuchanua.

Piga *384*42434# kwa huduma zaidi.

Asante! 🌾"""
            else:
                return f"""END 🎉 Congratulations {name}!

You are now registered with BloomWatch Kenya.

✓ County: {session['data']['county']}
✓ Farm Size: {session['data']['farm_size']} acres
✓ Crops: {len(session['data']['crops'])}

You will receive SMS and bloom alerts.

Dial *384*42434# for more services.

Thank you! 🌾"""
        else:
            return "END Registration failed. Please try again.\nUsajili umeshindwa. Tafadhali jaribu tena."
    
    # ============================================================================
    # REGISTERED USER MENU
    # ============================================================================
    
    def _ussd_main_menu_registered(self, farmer: Dict) -> str:
        """Main menu for registered farmers"""
        lang = farmer.get('language', 'en')
        name = farmer.get('name', 'Farmer')
        
        if lang == 'sw':
            return f"""CON Karibu {name}!
BloomWatch Kenya

Chagua huduma:
1. Data ya kaunti yangu
2. Tafsiri data yangu
3. Uliza Flora
4. Badilisha taarifa"""
        else:
            return f"""CON Welcome {name}!
BloomWatch Kenya

Select service:
1. My county's data
2. Interpret my data
3. Ask Flora
4. Update my details"""
    
    def _handle_registered_user(self, session: Dict, text: str, farmer: Dict) -> str:
        """Handle registered user interactions"""
        
        user_input = text.split('*')[-1] if '*' in text else text
        lang = farmer.get('language', 'en')
        
        # Main menu selection
        if not session.get('menu_choice'):
            if user_input == '1':  # County data
                session['menu_choice'] = 'county_data'
                return self._process_county_data_request(farmer)
            elif user_input == '2':  # Interpret data
                session['menu_choice'] = 'interpret'
                return self._process_interpret_request(farmer)
            elif user_input == '3':  # Ask Flora
                session['menu_choice'] = 'ask_flora'
                return "CON Enter your question:" if lang == 'en' else "CON Weka swali lako:"
            elif user_input == '4':  # Update details
                return "END Update feature coming soon. Visit bloomwatch.ke\nKipengele kinaendelea. Tembelea bloomwatch.ke"
            else:
                return "END Invalid option.\nChaguo batili."
        
        # Handle Flora question
        elif session.get('menu_choice') == 'ask_flora':
            question = user_input
            # Queue Flora response to be sent via SMS (USSD response is limited)
            self._queue_flora_sms_response(farmer, question)
            
            if lang == 'sw':
                return "END Asante! Flora atajibu swali lako kupitia SMS hivi karibuni.\n\nEndelea kufuatilia kwenye bloomwatch.ke"
            else:
                return "END Thank you! Flora will respond to your question via SMS shortly.\n\nTrack responses at bloomwatch.ke"
        
        return "END Session error. Please dial again.\nKosa. Tafadhali piga tena."
    
    def _process_county_data_request(self, farmer: Dict) -> str:
        """Process county data request and queue SMS"""
        self._queue_county_data_sms(farmer)
        
        lang = farmer.get('language', 'en')
        if lang == 'sw':
            return f"""END Asante {farmer.get('name', 'Farmer')}!

Data ya {farmer.get('county', 'kaunti yako')} na ushauri wa kilimo utatumwa kupitia SMS hivi karibuni.

Tembelea bloomwatch.ke kwa maelezo zaidi.

🌾 BloomWatch Kenya"""
        else:
            return f"""END Thank you {farmer.get('name', 'Farmer')}!

Data for {farmer.get('county', 'your county')} with agricultural advice will be sent via SMS shortly.

Visit bloomwatch.ke for more details.

🌾 BloomWatch Kenya"""
    
    def _process_interpret_request(self, farmer: Dict) -> str:
        """Process data interpretation request and queue SMS"""
        self._queue_interpret_sms(farmer)
        
        lang = farmer.get('language', 'en')
        if lang == 'sw':
            return f"""END Asante {farmer.get('name', 'Farmer')}!

Tafsiri ya data ya {farmer.get('county', 'kaunti yako')} na ushauri maalum kwa mazao yako utatumwa kupitia SMS.

Tembelea bloomwatch.ke kwa historia kamili.

🌾 BloomWatch Kenya"""
        else:
            return f"""END Thank you {farmer.get('name', 'Farmer')}!

Interpretation of {farmer.get('county', 'your county')}'s data with personalized advice will be sent via SMS.

Visit bloomwatch.ke for full history.

🌾 BloomWatch Kenya"""
    
    # ============================================================================
    # SMS FUNCTIONS
    # ============================================================================
    
    def _send_welcome_sms(self, phone: str, farmer_data: Dict):
        """Send welcome SMS"""
        lang = farmer_data.get('language', 'en')
        name = farmer_data.get('name', 'Farmer')
        county = farmer_data.get('county', '')
        crops_display = self._format_crops_display(farmer_data.get('crops', []))
        
        if lang == 'sw':
            message = f"""🌾 Karibu BloomWatch Kenya {name}!

✓ USAJILI UMEFANIKIWA

Taarifa zako:
📍 Kaunti: {county}
📏 Ukubwa: {farmer_data.get('farm_size', 'N/A')} ekari
🌾 Mazao: {crops_display}

Utapokea:
• Arifa za kuchanua
• Mwongozo wa kilimo
• Habari za hali ya hewa

Piga *384*42434# kwa huduma zaidi.

Asante kwa kujiunga nasi!"""
        else:
            message = f"""🌾 Welcome to BloomWatch Kenya {name}!

✓ REGISTRATION SUCCESSFUL

Your Details:
📍 County: {county}
📏 Farm Size: {farmer_data.get('farm_size', 'N/A')} acres
🌾 Crops: {crops_display}

You will receive:
• Bloom alerts
• Farming tips
• Weather updates

Dial *384*42434# for more services.

Thank you for joining us!"""
        
        self._send_sms(phone, message)
    
    def _queue_county_data_sms(self, farmer: Dict):
        """Queue county data SMS with Flora report"""
        try:
            report = self.flora.generate_county_report(
                farmer.get('county', ''),
                farmer,
                farmer.get('language', 'en')
            )
            
            # Truncate if too long (SMS limit ~1600 chars for concatenated messages)
            if len(report) > 1500:
                report = report[:1497] + "..."
            
            self._send_sms(farmer.get('phone'), f"🌾 BloomWatch Kenya\n\n{report}")
        except Exception as e:
            logger.error(f"Error sending county data SMS: {e}")
    
    def _queue_interpret_sms(self, farmer: Dict):
        """Queue interpretation SMS"""
        try:
            interpretation = self.flora.interpret_county_data(
                farmer.get('county', ''),
                farmer,
                farmer.get('language', 'en')
            )
            
            if len(interpretation) > 1500:
                interpretation = interpretation[:1497] + "..."
            
            self._send_sms(farmer.get('phone'), f"🌾 BloomWatch Kenya\n\n{interpretation}")
        except Exception as e:
            logger.error(f"Error sending interpretation SMS: {e}")
    
    def _queue_flora_sms_response(self, farmer: Dict, question: str):
        """Queue Flora AI response SMS"""
        try:
            answer = self.flora.answer_question(
                question,
                farmer,
                farmer.get('language', 'en'),
                use_internet=True
            )
            
            if len(answer) > 1500:
                answer = answer[:1497] + "..."
            
            lang = farmer.get('language', 'en')
            header = "🌸 Flora AI (BloomWatch Kenya)" if lang == 'en' else "🌸 Flora AI (BloomWatch Kenya)"
            
            self._send_sms(farmer.get('phone'), f"{header}\n\nQ: {question}\n\nA: {answer}")
        except Exception as e:
            logger.error(f"Error sending Flora SMS: {e}")
    
    def _send_sms(self, phone: str, message: str) -> Dict:
        """Send SMS via Africa's Talking or fallback services"""
        # Try Africa's Talking first
        if self.sms and self.api_key:
            try:
                if not phone.startswith('+'):
                    if phone.startswith('0'):
                        phone = '+254' + phone[1:]
                    elif phone.startswith('254'):
                        phone = '+' + phone
                    else:
                        phone = '+254' + phone
                
                response = self.sms.send(message, [phone])
                logger.info(f"✓ SMS sent to {phone} via Africa's Talking")
                return {'success': True, 'response': response, 'provider': 'africastalking'}
            except Exception as e:
                logger.error(f"Error sending SMS via Africa's Talking: {e}")
                # Try fallback
                pass
        
        # Try smart alert service if available
        try:
            from smart_alert_service import SmartAlertService
            from africastalking_service import AfricasTalkingService
            
            at_service = AfricasTalkingService()
            smart_alerts = SmartAlertService(self.mongo, at_service)
            result = at_service.send_sms(phone, message)
            
            if result.get('success'):
                logger.info(f"✓ SMS sent to {phone} via Smart Alert Service")
                return {'success': True, 'provider': 'smart_alert'}
        except Exception as e:
            logger.error(f"Smart Alert Service unavailable: {e}")
        
        # Demo mode
        logger.info(f"[DEMO] SMS to {phone}: {message[:100]}...")
        return {'success': True, 'demo': True, 'provider': 'demo'}
    
    # ============================================================================
    # HELPER FUNCTIONS
    # ============================================================================
    
    def _ussd_region_selection(self, lang: str) -> str:
        """Region selection menu"""
        if lang == 'sw':
            return """CON Chagua mkoa wako:
1. Central
2. Coast (Pwani)
3. Eastern (Mashariki)
4. Nairobi
5. North Eastern
6. Nyanza
7. Rift Valley
8. Western (Magharibi)"""
        else:
            return """CON Select your region:
1. Central
2. Coast
3. Eastern
4. Nairobi
5. North Eastern
6. Nyanza
7. Rift Valley
8. Western"""
    
    def _ussd_county_selection(self, region: str, lang: str) -> str:
        """County selection menu based on region"""
        counties = get_counties_by_region(region)
        
        # Split into pages if more than 8 counties
        if len(counties) <= 8:
            menu = "CON Chagua kaunti yako:\n" if lang == 'sw' else "CON Select your county:\n"
            for i, county in enumerate(counties, 1):
                menu += f"{i}. {county}\n"
            return menu.rstrip()
        else:
            # First page (8 counties)
            menu = "CON Chagua kaunti yako (1/2):\n" if lang == 'sw' else "CON Select county (Page 1/2):\n"
            for i, county in enumerate(counties[:8], 1):
                menu += f"{i}. {county}\n"
            menu += "9. More..." if lang == 'en' else "9. Zaidi..."
            return menu.rstrip()
    
    def _ussd_farm_size_prompt(self, lang: str) -> str:
        """Farm size input prompt"""
        if lang == 'sw':
            return "CON Weka ukubwa wa shamba lako kwa ekari (e.g. 2.5):"
        else:
            return "CON Enter your farm size in acres (e.g. 2.5):"
    
    def _ussd_crop_selection(self, county: str, lang: str) -> str:
        """Dynamic crop selection based on county"""
        crop_codes = get_ussd_crop_codes(county)
        
        if lang == 'sw':
            menu = "CON Chagua mazao (e.g. 1,2,3):\n"
        else:
            menu = "CON Select crops (e.g. 1,2,3):\n"
        
        for code, crop_id in crop_codes.items():
            if crop_id == 'other':
                menu += f"{code}. Other (Weka jina)\n" if lang == 'sw' else f"{code}. Other (Enter name)\n"
            else:
                crop_data = ALL_KENYA_CROPS.get(crop_id, {})
                if lang == 'sw':
                    name = crop_data.get('name_sw', crop_data.get('name', crop_id))
                else:
                    name = crop_data.get('name', crop_id)
                menu += f"{code}. {name}\n"
        
        return menu.rstrip()
    
    def _ussd_add_more_crops(self, lang: str) -> str:
        """Ask if farmer wants to add more crops"""
        if lang == 'sw':
            return """CON Mazao yamewekwa!
Ongeza mazao mengine?
1. Ndio
2. Hapana, endelea"""
        else:
            return """CON Crops added!
Add more crops?
1. Yes
2. No, continue"""
    
    def _ussd_confirm_registration(self, data: Dict) -> str:
        """Confirmation screen"""
        lang = data.get('language', 'en')
        crops_display = self._format_crops_display(data.get('crops', []))
        
        if lang == 'sw':
            return f"""CON Thibitisha taarifa:
Jina: {data.get('name')}
Kaunti: {data.get('county')}
Ukubwa: {data.get('farm_size')} ekari
Mazao: {crops_display}

1. Thibitisha
2. Ghairi"""
        else:
            return f"""CON Confirm details:
Name: {data.get('name')}
County: {data.get('county')}
Farm Size: {data.get('farm_size')} acres
Crops: {crops_display}

1. Confirm
2. Cancel"""
    
    def _format_crops_display(self, crops: List[str]) -> str:
        """Format crops list for display"""
        display_crops = []
        for crop in crops[:5]:  # Limit to 5 for display
            if crop.startswith('other:'):
                display_crops.append(crop.split(':', 1)[1])
            else:
                crop_data = ALL_KENYA_CROPS.get(crop, {})
                display_crops.append(crop_data.get('name', crop))
        
        result = ', '.join(display_crops)
        if len(crops) > 5:
            result += f" +{len(crops) - 5} more"
        return result

# Demo/Testing
if __name__ == "__main__":
    print("=" * 80)
    print("🌾 Enhanced USSD Service Test")
    print("=" * 80)
    
    service = EnhancedUSSDService()
    
    # Simulate registration flow
    print("\n📱 Registration Flow Simulation:")
    print("-" * 80)
    
    # Step 1: Initial
    resp = service.handle_ussd_request('test1', '*384*42434#', '+254700000001', '')
    print(f"1. Initial:\n{resp}\n")
    
    # Step 2: Select English
    resp = service.handle_ussd_request('test1', '*384*42434#', '+254700000001', '1')
    print(f"2. Language (English):\n{resp}\n")
    
    # Step 3: Enter name
    resp = service.handle_ussd_request('test1', '*384*42434#', '+254700000001', '1*Mary Wanjiru')
    print(f"3. Name:\n{resp}\n")
    
    # Step 4: Select region (Central)
    resp = service.handle_ussd_request('test1', '*384*42434#', '+254700000001', '1*Mary Wanjiru*1')
    print(f"4. Region (Central):\n{resp}\n")
    
    print("=" * 80)
    print("✓ Enhanced USSD test completed!")

