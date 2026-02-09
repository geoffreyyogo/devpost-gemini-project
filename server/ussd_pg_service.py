"""
Enhanced USSD Service for Smart Shamba Platform — PostgreSQL + Africa's Talking
Drop-in replacement for ussd_enhanced_service.py

Features:
    - Language selection (English / Kiswahili)
    - Region → County selection flow
    - Dynamic crop selection by county
    - Farm size capture
    - Post-registration menu with Flora AI
    - SMS via Africa's Talking (or demo mode)
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Import DB and SMS services
from database.postgres_service import PostgresService
from africastalking_service import AfricasTalkingService

try:
    from flora_ai_gemini import FloraAIService  # type: ignore[import-untyped]
    FLORA_AVAILABLE = True
except ImportError:
    FloraAIService = None  # type: ignore[misc,assignment]
    FLORA_AVAILABLE = False

try:
    from kenya_sub_counties import get_sub_counties, get_sub_county_info  # type: ignore[import-untyped]
    SUB_COUNTIES_AVAILABLE = True
except ImportError:
    def get_sub_counties(county_id: str) -> dict:  # type: ignore[misc]
        return {}
    def get_sub_county_info(county_id: str, sub_county_name: str) -> dict:  # type: ignore[misc]
        return {}
    SUB_COUNTIES_AVAILABLE = False

try:
    from kenya_regions_counties import (  # type: ignore[import-untyped]
        KENYA_REGIONS_COUNTIES, ALL_KENYA_CROPS,
        get_ussd_crop_codes, get_counties_by_region,
    )
    REGIONS_AVAILABLE = True
except ImportError:
    KENYA_REGIONS_COUNTIES: Dict = {  # type: ignore[no-redef]
        "Central": {"counties": ["Kiambu", "Muranga", "Nyeri", "Kirinyaga", "Nyandarua"]},
        "Rift Valley": {"counties": ["Nakuru", "Uasin Gishu", "Nandi", "Trans Nzoia", "Kericho"]},
        "Western": {"counties": ["Kakamega", "Bungoma", "Busia", "Vihiga"]},
        "Eastern": {"counties": ["Meru", "Embu", "Tharaka-Nithi", "Machakos", "Makueni"]},
        "Coast": {"counties": ["Mombasa", "Kilifi", "Kwale", "Taita-Taveta"]},
        "Nyanza": {"counties": ["Kisumu", "Siaya", "Homa Bay", "Migori", "Kisii", "Nyamira"]},
    }
    _ALL_KENYA_CROP_LIST = [
        "maize", "beans", "coffee", "tea", "wheat", "sorghum",
        "rice", "sugarcane", "potatoes", "millet",
    ]
    ALL_KENYA_CROPS: Dict = {c: {"name": c.title()} for c in _ALL_KENYA_CROP_LIST}  # type: ignore[no-redef]
    REGIONS_AVAILABLE = False

    def get_counties_by_region(region_id: str) -> list:  # type: ignore[misc]
        return KENYA_REGIONS_COUNTIES.get(region_id, {}).get("counties", [])  # type: ignore[union-attr]

    def get_ussd_crop_codes(county: str = None) -> dict:  # type: ignore[misc]
        crops = list(ALL_KENYA_CROPS.keys())[:8]  # type: ignore[union-attr]
        return {str(i + 1): c for i, c in enumerate(crops)}


class EnhancedUSSDService:
    """Enhanced USSD service with PostgreSQL and Africa's Talking."""

    def __init__(self, db_service=None, sms_service=None):
        self.db = db_service or PostgresService()
        self.sms = sms_service or AfricasTalkingService(db_service=self.db)

        self.flora = None
        if FLORA_AVAILABLE and FloraAIService is not None:
            try:
                self.flora = FloraAIService(self.db)
            except Exception as e:
                logger.warning(f"Flora AI not available: {e}")

    # ================================================================== #
    # Main entry point
    # ================================================================== #

    def handle_ussd_request(self, session_id: str, service_code: str,
                            phone_number: str, text: str) -> str:
        """Main USSD request handler (Africa's Talking callback)."""

        # Check if farmer is already registered
        farmer = self.db.get_farmer_by_phone(phone_number)

        if farmer and text == "":
            return self._ussd_main_menu_registered(farmer)
        elif text == "":
            return self._ussd_language_selection()

        # Get or create session
        session = self.db.get_ussd_session(session_id)
        if not session:
            session = {
                "phone": phone_number,
                "step": "language",
                "data": {},
                "is_registered": farmer is not None,
            }

        # Route to handler
        if farmer:
            response = self._handle_registered_user(session, text, farmer)
        else:
            response = self._handle_registration(session, text, phone_number)

        # Persist session
        self.db.save_ussd_session(session_id, session)

        return response

    # ================================================================== #
    # Registration flow
    # ================================================================== #

    def _ussd_language_selection(self) -> str:
        return (
            "CON Welcome to Smart Shamba\n"
            "Karibu Smart Shamba\n\n"
            "Select language / Chagua lugha:\n"
            "1. English\n"
            "2. Kiswahili"
        )

    def _handle_registration(self, session: Dict, text: str, phone: str) -> str:
        user_input = text.split("*")[-1] if "*" in text else text

        # Step 1: Language
        if session["step"] == "language" or text in ("1", "2"):
            if user_input == "1":
                session["data"]["language"] = "en"
                session["step"] = "name"
                return "CON Enter your full name:"
            elif user_input == "2":
                session["data"]["language"] = "sw"
                session["step"] = "name"
                return "CON Weka jina lako kamili:"
            else:
                return "END Invalid option. Dial again.\nChaguo batili. Piga tena."

        # Step 2: Name
        elif session["step"] == "name":
            session["data"]["name"] = user_input
            session["step"] = "region"
            return self._ussd_region_selection(session["data"]["language"])

        # Step 3: Region
        elif session["step"] == "region":
            regions = list(KENYA_REGIONS_COUNTIES.keys())
            try:
                idx = int(user_input) - 1
                if 0 <= idx < len(regions):
                    session["data"]["region"] = regions[idx]
                    session["step"] = "county"
                    return self._ussd_county_selection(
                        session["data"]["region"], session["data"]["language"]
                    )
                raise ValueError
            except Exception:
                return "END Invalid option. Please try again."

        # Step 4: County
        elif session["step"] == "county":
            counties = get_counties_by_region(session["data"]["region"])
            try:
                idx = int(user_input) - 1
                if 0 <= idx < len(counties):
                    session["data"]["county"] = counties[idx]
                    # Try sub-county step if available
                    if SUB_COUNTIES_AVAILABLE:
                        county_id = counties[idx].lower().replace(" ", "_").replace("-", "_").replace("'", "")
                        subs_dict = get_sub_counties(county_id)
                        if subs_dict:
                            session["data"]["_county_id"] = county_id
                            session["data"]["_sub_county_list"] = list(subs_dict.values())
                            session["step"] = "sub_county"
                            return self._ussd_sub_county_selection(
                                county_id, session["data"]["language"]
                            )
                    session["step"] = "farm_size"
                    return self._ussd_farm_size_prompt(session["data"]["language"])
                raise ValueError
            except Exception:
                return "END Invalid option. Please try again."

        # Step 4b: Sub-county
        elif session["step"] == "sub_county":
            subs_list = session["data"].get("_sub_county_list", [])
            if not subs_list:
                county_id = session["data"].get("_county_id", "")
                subs_dict = get_sub_counties(county_id) if SUB_COUNTIES_AVAILABLE else {}
                subs_list = list(subs_dict.values())
            try:
                idx = int(user_input) - 1
                if 0 <= idx < len(subs_list):
                    session["data"]["sub_county"] = subs_list[idx]["name"]
                    session["step"] = "farm_size"
                    return self._ussd_farm_size_prompt(session["data"]["language"])
                raise ValueError
            except Exception:
                return "END Invalid option. Please try again."

        # Step 5: Farm size
        elif session["step"] == "farm_size":
            try:
                farm_size = float(user_input)
                if farm_size <= 0 or farm_size > 10000:
                    raise ValueError
                session["data"]["farm_size"] = farm_size
                session["step"] = "crops"
                return self._ussd_crop_selection(
                    session["data"]["county"], session["data"]["language"]
                )
            except Exception:
                lang = session["data"].get("language", "en")
                msg = (
                    "CON Nambari batili. Weka ukubwa wa shamba kwa ekari (e.g. 2.5):"
                    if lang == "sw"
                    else "CON Invalid number. Enter farm size in acres (e.g. 2.5):"
                )
                return msg

        # Step 6: Crops
        elif session["step"] == "crops":
            return self._handle_crop_selection(session, user_input)

        # Step 6b: Other crop text
        elif session["step"] == "other_crop":
            other_crop = user_input.strip()
            if other_crop:
                session["data"].setdefault("crops", []).append(f"other:{other_crop}")
                session["step"] = "crops_add_more"
                return self._ussd_add_more_crops(session["data"]["language"])
            lang = session["data"].get("language", "en")
            return "CON Enter crop name:" if lang == "en" else "CON Weka jina la mazao:"

        # Step 7: Add more crops?
        elif session["step"] == "crops_add_more":
            if user_input == "1":
                session["step"] = "crops"
                return self._ussd_crop_selection(
                    session["data"]["county"], session["data"]["language"]
                )
            elif user_input == "2":
                session["step"] = "confirm"
                return self._ussd_confirm_registration(session["data"])
            return "END Invalid option."

        # Step 8: Confirm
        elif session["step"] == "confirm":
            if user_input == "1":
                return self._complete_registration(session, phone)
            lang = session["data"].get("language", "en")
            return (
                "END Usajili umeghairiwa."
                if lang == "sw"
                else "END Registration cancelled."
            )

        return "END Session error. Please try again."

    # ------------------------------------------------------------------ #
    # Crop selection
    # ------------------------------------------------------------------ #

    def _handle_crop_selection(self, session: Dict, user_input: str) -> str:
        county = session["data"].get("county", "")
        lang = session["data"].get("language", "en")
        crop_codes = get_ussd_crop_codes(county)

        session["data"].setdefault("crops", [])
        selections = [s.strip() for s in user_input.replace(",", " ").split()]

        valid = []
        for sel in selections:
            if sel in crop_codes:
                crop_id = crop_codes[sel]
                if crop_id == "other":
                    session["step"] = "other_crop"
                    return (
                        "CON Weka jina la mazao:"
                        if lang == "sw"
                        else "CON Enter crop name:"
                    )
                valid.append(crop_id)

        if valid:
            session["data"]["crops"].extend(valid)
            session["step"] = "crops_add_more"
            return self._ussd_add_more_crops(lang)
        return "END Invalid selection. Please try again."

    # ------------------------------------------------------------------ #
    # Complete registration
    # ------------------------------------------------------------------ #

    def _complete_registration(self, session: Dict, phone: str) -> str:
        data = session["data"]
        farmer_data = {
            "phone": phone,
            "name": data["name"],
            "county": data["county"],
            "sub_county": data.get("sub_county"),
            "region": data["region"],
            "farm_size": data["farm_size"],
            "crops": data["crops"],
            "language": data["language"],
            "sms_enabled": True,
            "registration_source": "ussd",
        }

        # Get county coordinates from config (no JSON file dependency)
        try:
            from kenya_counties_config import KENYA_COUNTIES
            cid = data["county"].lower().replace(" ", "_").replace("-", "_").replace("'", "")
            county_cfg = KENYA_COUNTIES.get(cid, {})
            coords = county_cfg.get("coordinates", {})
            farmer_data["location_lat"] = coords.get("lat", 0)
            farmer_data["location_lon"] = coords.get("lon", 0)
        except Exception:
            farmer_data["location_lat"] = 0
            farmer_data["location_lon"] = 0

        result = self.db.register_farmer(farmer_data)

        if result.get("success"):
            self._send_welcome_sms(phone, farmer_data)
            name = data["name"]
            county = data["county"]
            crops_n = len(data["crops"])
            farm_size = data["farm_size"]

            sub_county = data.get("sub_county", "")
            sub_line_sw = f"✓ Kaunti ndogo: {sub_county}\n" if sub_county else ""
            sub_line_en = f"✓ Sub-county: {sub_county}\n" if sub_county else ""

            if data["language"] == "sw":
                return (
                    f"END 🎉 Hongera {name}!\n\n"
                    f"Umesajiliwa kikamilifu kwenye Smart Shamba.\n\n"
                    f"✓ Kaunti: {county}\n"
                    f"{sub_line_sw}"
                    f"✓ Ukubwa: {farm_size} ekari\n"
                    f"✓ Mazao: {crops_n}\n\n"
                    "Utapokea SMS na arifa.\nAsante! 🌾"
                )
            return (
                f"END 🎉 Congratulations {name}!\n\n"
                f"You are now registered with Smart Shamba.\n\n"
                f"✓ County: {county}\n"
                f"{sub_line_en}"
                f"✓ Farm Size: {farm_size} acres\n"
                f"✓ Crops: {crops_n}\n\n"
                "You will receive SMS alerts.\nThank you! 🌾"
            )

        return "END Registration failed. Please try again."

    # ================================================================== #
    # Registered user menu
    # ================================================================== #

    def _ussd_main_menu_registered(self, farmer: Dict) -> str:
        lang = farmer.get("language", "en")
        name = farmer.get("name", "Farmer")

        if lang == "sw":
            return (
                f"CON Karibu {name}!\n"
                "Smart Shamba\n\n"
                "Chagua huduma:\n"
                "1. Data ya kaunti yangu\n"
                "2. Tafsiri data yangu\n"
                "3. Uliza Flora\n"
                "4. Badilisha taarifa\n"
                "5. Hali ya shamba\n"
                "6. Tafuta Agrovet\n"
                "7. Duka la Agrovet\n"
                "8. Uza Mazao"
            )
        return (
            f"CON Welcome {name}!\n"
            "Smart Shamba\n\n"
            "Select service:\n"
            "1. My county data\n"
            "2. Interpret my data\n"
            "3. Ask Flora\n"
            "4. Update details\n"
            "5. Farm health check\n"
            "6. Find agrovet\n"
            "7. Agrovet shop\n"
            "8. Sell produce"
        )

    def _handle_registered_user(self, session: Dict, text: str, farmer: Dict) -> str:
        user_input = text.split("*")[-1] if "*" in text else text
        lang = farmer.get("language", "en")

        if not session.get("data", {}).get("menu_choice"):
            session.setdefault("data", {})
            if user_input == "1":
                session["data"]["menu_choice"] = "county_data"
                return self._process_county_data_request(farmer)
            elif user_input == "2":
                session["data"]["menu_choice"] = "interpret"
                return self._process_interpret_request(farmer)
            elif user_input == "3":
                session["data"]["menu_choice"] = "ask_flora"
                return (
                    "CON Weka swali lako:" if lang == "sw" else "CON Enter your question:"
                )
            elif user_input == "4":
                return (
                    "END Kipengele kinaendelea. Tembelea shamba-smart.ke"
                    if lang == "sw"
                    else "END Update feature coming soon. Visit shamba-smart.ke"
                )
            elif user_input == "5":
                session["data"]["menu_choice"] = "farm_health"
                return self._process_farm_health_check(farmer)
            elif user_input == "6":
                session["data"]["menu_choice"] = "find_agrovet"
                return self._process_find_agrovet(farmer)
            elif user_input == "7":
                session["data"]["menu_choice"] = "agrovet_shop"
                session["data"]["shop_step"] = "category"
                return self._agrovet_shop_categories(farmer)
            elif user_input == "8":
                session["data"]["menu_choice"] = "marketplace"
                session["data"]["market_step"] = "category"
                return self._marketplace_categories(farmer)
            return "END Invalid option."

        if session["data"].get("menu_choice") == "ask_flora":
            self._queue_flora_sms_response(farmer, user_input)
            if lang == "sw":
                return "END Asante! Flora atajibu swali lako kupitia SMS hivi karibuni."
            return "END Thank you! Flora will respond to your question via SMS shortly."

        if session["data"].get("menu_choice") == "agrovet_shop":
            return self._handle_agrovet_shop(session, user_input, farmer)

        if session["data"].get("menu_choice") == "marketplace":
            return self._handle_marketplace(session, user_input, farmer)

        return "END Session error. Please dial again."

    # ================================================================== #
    # SMS helpers
    # ================================================================== #

    def _send_welcome_sms(self, phone: str, farmer_data: Dict):
        lang = farmer_data.get("language", "en")
        name = farmer_data.get("name", "Farmer")
        county = farmer_data.get("county", "")
        sub_county = farmer_data.get("sub_county", "")
        crops_display = self._format_crops_display(farmer_data.get("crops", []))
        loc_sw = f"📍 Kaunti: {county}\n"
        loc_en = f"📍 County: {county}\n"
        if sub_county:
            loc_sw += f"📍 Kaunti ndogo: {sub_county}\n"
            loc_en += f"📍 Sub-county: {sub_county}\n"

        if lang == "sw":
            message = (
                f"🌾 Karibu Smart Shamba {name}!\n\n"
                f"✓ USAJILI UMEFANIKIWA\n\n"
                f"{loc_sw}"
                f"📏 Ukubwa: {farmer_data.get('farm_size', 'N/A')} ekari\n"
                f"🌾 Mazao: {crops_display}\n\n"
                "Utapokea arifa za kilimo.\nAsante!"
            )
        else:
            message = (
                f"🌾 Welcome to Smart Shamba {name}!\n\n"
                f"✓ REGISTRATION SUCCESSFUL\n\n"
                f"{loc_en}"
                f"📏 Farm Size: {farmer_data.get('farm_size', 'N/A')} acres\n"
                f"🌾 Crops: {crops_display}\n\n"
                "You will receive farming alerts.\nThank you!"
            )

        self.sms.send_sms(phone, message)

    def _process_county_data_request(self, farmer: Dict) -> str:
        if self.flora:
            try:
                report = self.flora.generate_county_report(
                    farmer.get("county", ""), farmer, farmer.get("language", "en")
                )
                if len(report) > 1500:
                    report = report[:1497] + "..."
                self.sms.send_sms(farmer["phone"], f"🌾 Smart Shamba\n\n{report}")
            except Exception as e:
                logger.error(f"Error sending county data SMS: {e}")

        lang = farmer.get("language", "en")
        name = farmer.get("name", "Farmer")
        county = farmer.get("county", "")
        if lang == "sw":
            return (
                f"END Asante {name}!\n"
                f"Data ya {county} itatumwa kupitia SMS.\n"
                "Tembelea shamba-smart.ke kwa maelezo zaidi.\n🌾"
            )
        return (
            f"END Thank you {name}!\n"
            f"Data for {county} will be sent via SMS.\n"
            "Visit shamba-smart.ke for more.\n🌾"
        )

    def _process_interpret_request(self, farmer: Dict) -> str:
        if self.flora:
            try:
                interpretation = self.flora.interpret_county_data(
                    farmer.get("county", ""), farmer, farmer.get("language", "en")
                )
                if len(interpretation) > 1500:
                    interpretation = interpretation[:1497] + "..."
                self.sms.send_sms(farmer["phone"], f"🌾 Smart Shamba\n\n{interpretation}")
            except Exception as e:
                logger.error(f"Error sending interpret SMS: {e}")

        lang = farmer.get("language", "en")
        name = farmer.get("name", "Farmer")
        if lang == "sw":
            return (
                f"END Asante {name}!\n"
                "Tafsiri itatumwa kupitia SMS.\n🌾"
            )
        return (
            f"END Thank you {name}!\n"
            "Interpretation will be sent via SMS.\n🌾"
        )

    def _queue_flora_sms_response(self, farmer: Dict, question: str):
        if not self.flora:
            return
        try:
            lang = farmer.get("language", "en")
            result = self.flora.answer_question(question, lang)
            # answer_question returns Dict with 'reply' and 'reasoning'
            reply_text: str = result.get("reply", "") if isinstance(result, dict) else str(result)
            reasoning: Optional[str] = result.get("reasoning") if isinstance(result, dict) else None
            if reply_text and len(reply_text) > 1500:
                reply_text = reply_text[:1497] + "..."
            if reply_text:
                self.sms.send_sms(
                    farmer["phone"],
                    f"🌾 Flora AI ({farmer.get('name','')}):\n\n"
                    f"Q: {question[:100]}\n\n{reply_text}",
                )
                # Save with conversation threading — will auto-create or reuse a USSD conversation
                self.db.save_chat_message(
                    phone=farmer["phone"],
                    role="user",
                    message=question,
                    response=reply_text,
                    farmer_id=farmer.get("id"),
                    via="ussd",
                    language=lang,
                    reasoning=reasoning,
                    conversation_id=None,  # auto-creates conversation
                )
        except Exception as e:
            logger.error(f"Error queuing Flora SMS: {e}")

    # ================================================================== #
    # Agrovet Shop (Browse & Purchase via USSD)
    # ================================================================== #

    PRODUCT_CATEGORIES = {
        "1": ("seeds", "Mbegu", "Seeds"),
        "2": ("fertilizer", "Mbolea", "Fertilizer"),
        "3": ("pesticide", "Dawa", "Pesticide"),
        "4": ("tools", "Vifaa", "Tools"),
        "5": ("animal_feed", "Chakula cha mifugo", "Animal Feed"),
    }

    def _agrovet_shop_categories(self, farmer: Dict) -> str:
        lang = farmer.get("language", "en")
        if lang == "sw":
            header = "CON Chagua aina ya bidhaa:"
            items = "\n".join(f"{k}. {v[1]}" for k, v in self.PRODUCT_CATEGORIES.items())
        else:
            header = "CON Select product category:"
            items = "\n".join(f"{k}. {v[2]}" for k, v in self.PRODUCT_CATEGORIES.items())
        return f"{header}\n{items}"

    def _handle_agrovet_shop(self, session: Dict, user_input: str, farmer: Dict) -> str:
        lang = farmer.get("language", "en")
        shop_step = session["data"].get("shop_step", "category")

        # Step 1: Category selection
        if shop_step == "category":
            cat = self.PRODUCT_CATEGORIES.get(user_input)
            if not cat:
                return "END Invalid option." if lang == "en" else "END Chaguo batili."
            session["data"]["shop_category"] = cat[0]
            session["data"]["shop_step"] = "products"
            return self._fetch_and_display_products(session, farmer)

        # Step 2: Product selection
        elif shop_step == "products":
            products = session["data"].get("_shop_products", [])
            try:
                idx = int(user_input) - 1
                if 0 <= idx < len(products):
                    p = products[idx]
                    session["data"]["selected_product"] = p
                    session["data"]["shop_step"] = "quantity"
                    if lang == "sw":
                        return (
                            f"CON {p['name']}\n"
                            f"Bei: KES {p['price_kes']}/{p['unit']}\n"
                            f"Duka: {p.get('shop_name', 'N/A')}\n\n"
                            "Weka idadi unayotaka:"
                        )
                    return (
                        f"CON {p['name']}\n"
                        f"Price: KES {p['price_kes']}/{p['unit']}\n"
                        f"Shop: {p.get('shop_name', 'N/A')}\n\n"
                        "Enter quantity:"
                    )
                raise ValueError
            except Exception:
                return "END Invalid option." if lang == "en" else "END Chaguo batili."

        # Step 3: Quantity
        elif shop_step == "quantity":
            try:
                qty = float(user_input)
                if qty <= 0:
                    raise ValueError
                product = session["data"]["selected_product"]
                total = qty * product["price_kes"]
                session["data"]["shop_quantity"] = qty
                session["data"]["shop_total"] = total
                session["data"]["shop_step"] = "confirm"
                if lang == "sw":
                    return (
                        f"CON Thibitisha ununuzi:\n"
                        f"Bidhaa: {product['name']}\n"
                        f"Idadi: {qty} {product['unit']}\n"
                        f"Jumla: KES {total:,.0f}\n\n"
                        "1. Thibitisha\n2. Ghairi"
                    )
                return (
                    f"CON Confirm purchase:\n"
                    f"Product: {product['name']}\n"
                    f"Quantity: {qty} {product['unit']}\n"
                    f"Total: KES {total:,.0f}\n\n"
                    "1. Confirm\n2. Cancel"
                )
            except Exception:
                if lang == "sw":
                    return "CON Nambari batili. Weka idadi:"
                return "CON Invalid number. Enter quantity:"

        # Step 4: Confirm purchase
        elif shop_step == "confirm":
            if user_input == "1":
                return self._create_agrovet_order(session, farmer)
            if lang == "sw":
                return "END Ununuzi umeghairiwa."
            return "END Purchase cancelled."

        return "END Session error." if lang == "en" else "END Kosa la kipindi."

    def _fetch_and_display_products(self, session: Dict, farmer: Dict) -> str:
        lang = farmer.get("language", "en")
        category = session["data"].get("shop_category", "")
        county = farmer.get("county", "")
        sub_county = farmer.get("sub_county", "")

        try:
            from agrovet_service import AgrovetRecommendationService
            svc = AgrovetRecommendationService()
            products_raw = svc.search_products(
                query="", category=category, county=county,
                sub_county=sub_county, max_results=6
            )
            products = []
            for p in products_raw:
                products.append({
                    "id": p.get("id"),
                    "name": p.get("name", "Product"),
                    "price_kes": p.get("price_kes", 0),
                    "unit": p.get("unit", "piece"),
                    "shop_name": p.get("supplier_name", p.get("shop_name", "")),
                    "agrovet_id": p.get("agrovet_id"),
                })
            session["data"]["_shop_products"] = products

            if not products:
                cat_name = category.replace("_", " ").title()
                if lang == "sw":
                    return f"END Hakuna bidhaa za {cat_name} katika {sub_county or county}."
                return f"END No {cat_name} products found in {sub_county or county}."

            if lang == "sw":
                header = f"CON Bidhaa ({sub_county or county}):"
            else:
                header = f"CON Products ({sub_county or county}):"

            items = "\n".join(
                f"{i+1}. {p['name']} - KES {p['price_kes']}/{p['unit']}"
                for i, p in enumerate(products[:6])
            )
            return f"{header}\n{items}"

        except ImportError:
            logger.warning("Agrovet service not available for USSD shop")
        except Exception as e:
            logger.error(f"USSD agrovet shop error: {e}")

        if lang == "sw":
            return "END Huduma haipatikani kwa sasa."
        return "END Service temporarily unavailable."

    def _create_agrovet_order(self, session: Dict, farmer: Dict) -> str:
        lang = farmer.get("language", "en")
        product = session["data"].get("selected_product", {})
        qty = session["data"].get("shop_quantity", 1)
        total = session["data"].get("shop_total", 0)

        try:
            from agrovet_service import AgrovetRecommendationService
            svc = AgrovetRecommendationService()
            result = svc.create_order_from_recommendation(
                farmer_id=int(farmer.get("id", 0)),
                product_id=product.get("id"),
                quantity=qty,
                payment_method="mpesa",
                order_source="ussd",
            )

            if result.get("success"):
                order_num = result.get("order_number", "")
                # SMS confirmation
                if lang == "sw":
                    sms = (
                        f"🛒 Smart Shamba - Agizo #{order_num}\n\n"
                        f"Bidhaa: {product['name']}\n"
                        f"Idadi: {qty} {product.get('unit', '')}\n"
                        f"Jumla: KES {total:,.0f}\n\n"
                        "Lipa kupitia M-Pesa.\n"
                        "Tembelea shamba-smart.ke kwa maelezo."
                    )
                else:
                    sms = (
                        f"🛒 Smart Shamba - Order #{order_num}\n\n"
                        f"Product: {product['name']}\n"
                        f"Qty: {qty} {product.get('unit', '')}\n"
                        f"Total: KES {total:,.0f}\n\n"
                        "Pay via M-Pesa.\n"
                        "Visit shamba-smart.ke for details."
                    )
                self.sms.send_sms(farmer["phone"], sms)

                if lang == "sw":
                    return (
                        f"END ✅ Agizo #{order_num} limeundwa!\n"
                        f"Jumla: KES {total:,.0f}\n"
                        "Maelezo yatatumwa kwa SMS."
                    )
                return (
                    f"END ✅ Order #{order_num} placed!\n"
                    f"Total: KES {total:,.0f}\n"
                    "Details sent via SMS."
                )
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"USSD order failed: {error}")
        except ImportError:
            logger.warning("Agrovet service not available for USSD orders")
        except Exception as e:
            logger.error(f"USSD order error: {e}")

        if lang == "sw":
            return "END Samahani, agizo limeshindikana. Jaribu tena baadaye."
        return "END Sorry, order failed. Please try again later."

    # ================================================================== #
    # Marketplace — Sell Produce via USSD
    # ================================================================== #

    PRODUCE_CATEGORIES = {
        "1": ("grains", "Nafaka", "Grains"),
        "2": ("vegetables", "Mboga", "Vegetables"),
        "3": ("fruits", "Matunda", "Fruits"),
        "4": ("dairy", "Maziwa", "Dairy"),
        "5": ("livestock", "Mifugo", "Livestock"),
    }

    PRODUCE_UNITS = {
        "1": ("kg", "Kilo", "Kilograms"),
        "2": ("bag", "Mfuko", "Bags"),
        "3": ("crate", "Sanduku", "Crates"),
        "4": ("piece", "Kipande", "Pieces"),
        "5": ("litre", "Lita", "Litres"),
    }

    def _marketplace_categories(self, farmer: Dict) -> str:
        lang = farmer.get("language", "en")
        if lang == "sw":
            header = "CON Chagua aina ya mazao:"
            items = "\n".join(f"{k}. {v[1]}" for k, v in self.PRODUCE_CATEGORIES.items())
        else:
            header = "CON Select produce category:"
            items = "\n".join(f"{k}. {v[2]}" for k, v in self.PRODUCE_CATEGORIES.items())
        return f"{header}\n{items}"

    def _handle_marketplace(self, session: Dict, user_input: str, farmer: Dict) -> str:
        lang = farmer.get("language", "en")
        market_step = session["data"].get("market_step", "category")

        # Step 1: Category selection
        if market_step == "category":
            cat = self.PRODUCE_CATEGORIES.get(user_input)
            if not cat:
                return "END Invalid option." if lang == "en" else "END Chaguo batili."
            session["data"]["produce_category"] = cat[0]
            session["data"]["market_step"] = "produce_name"
            # Offer farmer's own crops or custom entry
            farmer_crops = farmer.get("crops", [])
            if farmer_crops:
                session["data"]["_crop_options"] = farmer_crops[:6]
                if lang == "sw":
                    header = "CON Chagua zao au weka jina:\n"
                else:
                    header = "CON Select crop or type name:\n"
                items = "\n".join(
                    f"{i+1}. {c.replace('other:', '').title()}"
                    for i, c in enumerate(farmer_crops[:6])
                )
                custom = "0. Weka jina lingine" if lang == "sw" else "0. Enter custom name"
                return f"{header}{items}\n{custom}"
            if lang == "sw":
                return "CON Weka jina la mazao:"
            return "CON Enter produce name:"

        # Step 2: Produce name
        elif market_step == "produce_name":
            crop_options = session["data"].get("_crop_options", [])
            if user_input == "0":
                session["data"]["market_step"] = "custom_produce"
                if lang == "sw":
                    return "CON Weka jina la mazao:"
                return "CON Enter produce name:"
            if crop_options:
                try:
                    idx = int(user_input) - 1
                    if 0 <= idx < len(crop_options):
                        crop = crop_options[idx].replace("other:", "")
                        session["data"]["produce_name"] = crop.title()
                        session["data"]["market_step"] = "quantity"
                        if lang == "sw":
                            return "CON Weka kiasi kinachopatikana (nambari):"
                        return "CON Enter quantity available (number):"
                except (ValueError, IndexError):
                    pass
                return "END Invalid option." if lang == "en" else "END Chaguo batili."
            # Free-text entry
            session["data"]["produce_name"] = user_input.strip().title()
            session["data"]["market_step"] = "quantity"
            if lang == "sw":
                return "CON Weka kiasi kinachopatikana (nambari):"
            return "CON Enter quantity available (number):"

        # Step 2b: Custom produce name
        elif market_step == "custom_produce":
            session["data"]["produce_name"] = user_input.strip().title()
            session["data"]["market_step"] = "quantity"
            if lang == "sw":
                return "CON Weka kiasi kinachopatikana (nambari):"
            return "CON Enter quantity available (number):"

        # Step 3: Quantity
        elif market_step == "quantity":
            try:
                qty = float(user_input)
                if qty <= 0:
                    raise ValueError
                session["data"]["produce_quantity"] = qty
                session["data"]["market_step"] = "unit"
                if lang == "sw":
                    header = "CON Chagua kipimo:"
                    items = "\n".join(f"{k}. {v[1]}" for k, v in self.PRODUCE_UNITS.items())
                else:
                    header = "CON Select unit:"
                    items = "\n".join(f"{k}. {v[2]}" for k, v in self.PRODUCE_UNITS.items())
                return f"{header}\n{items}"
            except Exception:
                if lang == "sw":
                    return "CON Nambari batili. Weka kiasi:"
                return "CON Invalid number. Enter quantity:"

        # Step 4: Unit
        elif market_step == "unit":
            unit = self.PRODUCE_UNITS.get(user_input)
            if not unit:
                return "END Invalid option." if lang == "en" else "END Chaguo batili."
            session["data"]["produce_unit"] = unit[0]
            session["data"]["market_step"] = "price"
            if lang == "sw":
                return f"CON Weka bei kwa {unit[1]} (KES):"
            return f"CON Enter price per {unit[2].lower()} (KES):"

        # Step 5: Price per unit
        elif market_step == "price":
            try:
                price = float(user_input)
                if price <= 0:
                    raise ValueError
                session["data"]["produce_price"] = price
                session["data"]["market_step"] = "confirm"
                # Show confirmation
                d = session["data"]
                qty = d["produce_quantity"]
                unit = d["produce_unit"]
                total_est = qty * price
                if lang == "sw":
                    return (
                        f"CON Thibitisha tangazo:\n"
                        f"Mazao: {d['produce_name']}\n"
                        f"Aina: {d['produce_category'].title()}\n"
                        f"Kiasi: {qty} {unit}\n"
                        f"Bei: KES {price:,.0f}/{unit}\n"
                        f"Thamani: ~KES {total_est:,.0f}\n\n"
                        "1. Thibitisha\n2. Ghairi"
                    )
                return (
                    f"CON Confirm listing:\n"
                    f"Produce: {d['produce_name']}\n"
                    f"Category: {d['produce_category'].title()}\n"
                    f"Quantity: {qty} {unit}\n"
                    f"Price: KES {price:,.0f}/{unit}\n"
                    f"Value: ~KES {total_est:,.0f}\n\n"
                    "1. Confirm\n2. Cancel"
                )
            except Exception:
                if lang == "sw":
                    return "CON Nambari batili. Weka bei (KES):"
                return "CON Invalid number. Enter price (KES):"

        # Step 6: Confirm listing
        elif market_step == "confirm":
            if user_input == "1":
                return self._create_marketplace_listing(session, farmer)
            if lang == "sw":
                return "END Tangazo limeghairiwa."
            return "END Listing cancelled."

        return "END Session error." if lang == "en" else "END Kosa la kipindi."

    def _create_marketplace_listing(self, session: Dict, farmer: Dict) -> str:
        lang = farmer.get("language", "en")
        d = session["data"]

        try:
            from database.connection import engine
            from sqlmodel import Session as SqlSession
            from database.models import MarketplaceListing

            listing = MarketplaceListing(
                farmer_id=int(farmer.get("id", 0)),
                produce_name=d.get("produce_name", ""),
                produce_category=d.get("produce_category", "grains"),
                quantity_available=d.get("produce_quantity", 0),
                unit=d.get("produce_unit", "kg"),
                price_per_unit_kes=d.get("produce_price", 0),
                county=farmer.get("county", ""),
                sub_county=farmer.get("sub_county", ""),
                pickup_location=farmer.get("sub_county", farmer.get("county", "")),
                status="active",
            )

            with SqlSession(engine) as db_session:
                db_session.add(listing)
                db_session.commit()
                db_session.refresh(listing)
                listing_id = listing.id

            # SMS confirmation
            qty = d.get("produce_quantity", 0)
            unit = d.get("produce_unit", "kg")
            price = d.get("produce_price", 0)
            total_est = qty * price

            if lang == "sw":
                sms = (
                    f"📦 Smart Shamba - Tangazo #{listing_id}\n\n"
                    f"Mazao: {d['produce_name']}\n"
                    f"Kiasi: {qty} {unit}\n"
                    f"Bei: KES {price:,.0f}/{unit}\n"
                    f"Thamani: ~KES {total_est:,.0f}\n\n"
                    f"📍 {farmer.get('sub_county', farmer.get('county', ''))}\n"
                    "Tangazo lako linaonekana kwa wanunuzi!\n"
                    "Tembelea shamba-smart.ke kwa maelezo."
                )
            else:
                sms = (
                    f"📦 Smart Shamba - Listing #{listing_id}\n\n"
                    f"Produce: {d['produce_name']}\n"
                    f"Quantity: {qty} {unit}\n"
                    f"Price: KES {price:,.0f}/{unit}\n"
                    f"Value: ~KES {total_est:,.0f}\n\n"
                    f"📍 {farmer.get('sub_county', farmer.get('county', ''))}\n"
                    "Your listing is now visible to buyers!\n"
                    "Visit shamba-smart.ke for details."
                )
            self.sms.send_sms(farmer["phone"], sms)

            if lang == "sw":
                return (
                    f"END ✅ Tangazo #{listing_id} limechapishwa!\n"
                    f"{d['produce_name']} - {qty} {unit}\n"
                    f"KES {price:,.0f}/{unit}\n"
                    "Maelezo yatatumwa kwa SMS."
                )
            return (
                f"END ✅ Listing #{listing_id} published!\n"
                f"{d['produce_name']} - {qty} {unit}\n"
                f"KES {price:,.0f}/{unit}\n"
                "Details sent via SMS."
            )

        except Exception as e:
            logger.error(f"USSD marketplace listing error: {e}")

        if lang == "sw":
            return "END Samahani, tangazo limeshindikana. Jaribu tena."
        return "END Sorry, listing failed. Please try again."

    # ================================================================== #
    # Farm Health Check (IoT deficiency detection via USSD)
    # ================================================================== #

    def _process_farm_health_check(self, farmer: Dict) -> str:
        """Check farmer's latest IoT readings for soil deficiencies and send SMS report."""
        lang = farmer.get("language", "en")
        name = farmer.get("name", "Farmer")

        try:
            from agrovet_service import detect_deficiencies_from_sensors, AgrovetRecommendationService

            # Get latest sensor data
            sensor_data = {}
            if self.db:
                try:
                    from sqlalchemy import text as sa_text
                    from database.connection import engine
                    from sqlmodel import Session
                    with Session(engine) as session:
                        row = session.exec(sa_text(  # type: ignore[arg-type]
                            "SELECT sr.soil_nitrogen, sr.soil_phosphorus, sr.soil_potassium, "
                            "sr.soil_ph, sr.soil_moisture_pct, sr.temperature_c, sr.humidity_pct "
                            "FROM sensor_readings sr "
                            "JOIN farms f ON sr.farm_id = f.id "
                            "WHERE f.farmer_id = :fid ORDER BY sr.ts DESC LIMIT 1"
                        ).bindparams(fid=farmer.get("id"))).first()  # type: ignore[union-attr]
                        if row:
                            sensor_data = {
                                "soil_nitrogen": row[0], "soil_phosphorus": row[1],
                                "soil_potassium": row[2], "soil_ph": row[3],
                                "soil_moisture_pct": row[4], "temperature_c": row[5],
                                "humidity_pct": row[6],
                            }
                except Exception as e:
                    logger.error(f"USSD sensor fetch: {e}")

            if not sensor_data:
                if lang == "sw":
                    return "END Hakuna data ya sensor kwa shamba lako. Hakikisha ESP32 imeunganishwa."
                return "END No sensor data found for your farm. Ensure your ESP32 is connected."

            # Detect deficiencies
            deficiencies = detect_deficiencies_from_sensors(sensor_data)

            if not deficiencies:
                sms_msg = (
                    f"🌾 Smart Shamba - {name}\n\n"
                    f"✅ {'Hali ya udongo ni nzuri!' if lang == 'sw' else 'Soil health is good!'}\n"
                    f"pH: {sensor_data.get('soil_ph', 'N/A')}\n"
                    f"{'Unyevu' if lang == 'sw' else 'Moisture'}: {sensor_data.get('soil_moisture_pct', 'N/A')}%\n"
                    f"N-P-K: {sensor_data.get('soil_nitrogen', '-')}/{sensor_data.get('soil_phosphorus', '-')}/{sensor_data.get('soil_potassium', '-')}"
                )
            else:
                if lang == "sw":
                    sms_msg = f"🌾 Smart Shamba - {name}\n\n⚠️ Masuala {len(deficiencies)} yamegunduliwa:\n"
                else:
                    sms_msg = f"🌾 Smart Shamba - {name}\n\n⚠️ {len(deficiencies)} issue(s) detected:\n"

                agrovet_svc = AgrovetRecommendationService()
                for d in deficiencies[:3]:
                    sms_msg += f"\n🔸 {d['display_name']} ({d['severity']})\n"
                    plan = agrovet_svc.get_treatment_plan(
                        d['condition'], farmer.get('farm_size', 1), farmer.get('crops', [])
                    )
                    if plan and plan.get('treatments'):
                        t = plan['treatments'][0]
                        sms_msg += f"  → {', '.join(t.get('names', [])[:2])}: {t.get('scaled_dose', t.get('dose_per_acre', ''))}\n"

                sms_msg += f"\n{'Tembelea shamba-smart.ke' if lang == 'sw' else 'Visit shamba-smart.ke for details'}"

            self.sms.send_sms(farmer["phone"], sms_msg)

        except ImportError:
            logger.warning("Agrovet service not available for USSD health check")
        except Exception as e:
            logger.error(f"USSD farm health check error: {e}")

        if lang == "sw":
            return f"END Asante {name}! Ripoti ya hali ya shamba itatumwa kupitia SMS."
        return f"END Thank you {name}! Farm health report will be sent via SMS."

    # ================================================================== #
    # Find Nearest Agrovet (USSD)
    # ================================================================== #

    def _process_find_agrovet(self, farmer: Dict) -> str:
        """Find nearest agrovets in farmer's sub-county/county and send via SMS."""
        lang = farmer.get("language", "en")
        name = farmer.get("name", "Farmer")
        county = farmer.get("county", "")
        sub_county = farmer.get("sub_county", "")

        try:
            from agrovet_service import AgrovetRecommendationService

            agrovet_svc = AgrovetRecommendationService()
            shops = agrovet_svc.find_nearest_agrovets(
                county=county, sub_county=sub_county, limit=5
            )

            if not shops:
                if lang == "sw":
                    sms_msg = f"🏪 Hakuna agrovet zilizosajiliwa katika {sub_county or county}. Tembelea shamba-smart.ke kusajili agrovet."
                else:
                    sms_msg = f"🏪 No agrovets registered in {sub_county or county}. Visit shamba-smart.ke to register an agrovet."
            else:
                if lang == "sw":
                    sms_msg = f"🏪 Agrovet karibu nawe ({sub_county or county}):\n\n"
                else:
                    sms_msg = f"🏪 Agrovets near you ({sub_county or county}):\n\n"

                for i, s in enumerate(shops[:3], 1):
                    sms_msg += (
                        f"{i}. {s.get('shop_name', 'Agrovet')}\n"
                        f"   📍 {s.get('location', s.get('sub_county', ''))}\n"
                    )
                    if s.get('phone'):
                        sms_msg += f"   📞 {s['phone']}\n"
                    sms_msg += "\n"

                sms_msg += f"{'Tembelea shamba-smart.ke kwa bidhaa' if lang == 'sw' else 'Visit shamba-smart.ke for products'}"

            self.sms.send_sms(farmer["phone"], sms_msg)

        except ImportError:
            logger.warning("Agrovet service not available for USSD")
        except Exception as e:
            logger.error(f"USSD find agrovet error: {e}")

        if lang == "sw":
            return f"END Asante {name}! Orodha ya agrovet itatumwa kupitia SMS."
        return f"END Thank you {name}! Agrovet list will be sent via SMS."

    # ================================================================== #
    # USSD menu builders
    # ================================================================== #

    def _ussd_region_selection(self, lang: str) -> str:
        regions = list(KENYA_REGIONS_COUNTIES.keys())
        header = "CON Chagua eneo:" if lang == "sw" else "CON Select your region:"
        items = "\n".join(f"{i+1}. {r}" for i, r in enumerate(regions))
        return f"{header}\n{items}"

    def _ussd_county_selection(self, region: str, lang: str) -> str:
        counties = get_counties_by_region(region)
        header = "CON Chagua kaunti:" if lang == "sw" else "CON Select your county:"
        items = "\n".join(f"{i+1}. {c}" for i, c in enumerate(counties[:10]))
        return f"{header}\n{items}"

    def _ussd_sub_county_selection(self, county_id: str, lang: str) -> str:
        subs_dict = get_sub_counties(county_id) if SUB_COUNTIES_AVAILABLE else {}
        subs_list = list(subs_dict.values())
        header = (
            "CON Chagua kaunti ndogo:" if lang == "sw"
            else "CON Select your sub-county:"
        )
        # USSD has ~182-char limit; show max 8 sub-counties
        items = "\n".join(
            f"{i+1}. {s['name']}" for i, s in enumerate(subs_list[:8])
        )
        if len(subs_list) > 8:
            more = "(zaidi haizonyeshwi)" if lang == "sw" else "(more not shown)"
            items += f"\n{more}"
        return f"{header}\n{items}"

    def _ussd_farm_size_prompt(self, lang: str) -> str:
        if lang == "sw":
            return "CON Weka ukubwa wa shamba kwa ekari (e.g. 2.5):"
        return "CON Enter your farm size in acres (e.g. 2.5):"

    def _ussd_crop_selection(self, county: str, lang: str) -> str:
        crop_codes = get_ussd_crop_codes(county)
        header = (
            "CON Chagua mazao (tenganisha kwa koma):"
            if lang == "sw"
            else "CON Select your crops (comma-separated):"
        )
        items = "\n".join(f"{k}. {v}" for k, v in crop_codes.items())
        return f"{header}\n{items}"

    def _ussd_add_more_crops(self, lang: str) -> str:
        if lang == "sw":
            return "CON Ongeza mazao zaidi?\n1. Ndiyo\n2. Hapana"
        return "CON Add more crops?\n1. Yes\n2. No"

    def _ussd_confirm_registration(self, data: Dict) -> str:
        lang = data.get("language", "en")
        crops_display = self._format_crops_display(data.get("crops", []))

        sub = data.get('sub_county', '')
        sub_sw = f"Kaunti ndogo: {sub}\n" if sub else ""
        sub_en = f"Sub-county: {sub}\n" if sub else ""

        if lang == "sw":
            return (
                "CON Thibitisha taarifa:\n"
                f"Jina: {data.get('name')}\n"
                f"Eneo: {data.get('region')}\n"
                f"Kaunti: {data.get('county')}\n"
                f"{sub_sw}"
                f"Ukubwa: {data.get('farm_size')} ekari\n"
                f"Mazao: {crops_display}\n\n"
                "1. Thibitisha\n2. Ghairi"
            )
        return (
            "CON Please confirm:\n"
            f"Name: {data.get('name')}\n"
            f"Region: {data.get('region')}\n"
            f"County: {data.get('county')}\n"
            f"{sub_en}"
            f"Farm Size: {data.get('farm_size')} acres\n"
            f"Crops: {crops_display}\n\n"
            "1. Confirm\n2. Cancel"
        )

    @staticmethod
    def _format_crops_display(crops: List[str]) -> str:
        display = []
        for c in crops:
            if c.startswith("other:"):
                display.append(c.split(":", 1)[1].title())
            else:
                display.append(c.title())
        return ", ".join(display) if display else "N/A"
