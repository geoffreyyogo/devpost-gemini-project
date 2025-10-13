"""
Flora AI Service for BloomWatch Kenya
Personalized agricultural AI assistant with multi-language support
Uses GPT-4, satellite data, and local knowledge
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Make OpenAI optional
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None
    logging.warning("OpenAI not installed. Flora AI will use fallback responses.")

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FloraAIService:
    """AI-powered agricultural assistant for Kenyan farmers"""
    
    def __init__(self, mongodb_service=None):
        """Initialize Flora AI with GPT-4 and data access"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.openai_available = OPENAI_AVAILABLE and self.api_key
        
        if self.openai_available:
            openai.api_key = self.api_key
            logger.info("✓ Flora AI initialized with OpenAI")
        else:
            if not OPENAI_AVAILABLE:
                logger.warning("⚠ OpenAI module not installed. Flora will use fallback responses.")
            elif not self.api_key:
                logger.warning("⚠ OpenAI API key not set. Flora will use fallback responses.")
        
        self.mongo = mongodb_service
        self.county_data_cache = {}
    
    def get_county_data(self, county: str) -> Dict:
        """Load county data from JSON files"""
        if county in self.county_data_cache:
            return self.county_data_cache[county]
        
        try:
            county_id = county.lower().replace(" ", "_").replace("-", "_").replace("'", "")
            file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'county_data', f'{county_id}.json')
            
            with open(file_path, 'r') as f:
                data = json.load(f)
                self.county_data_cache[county] = data
                return data
        except Exception as e:
            logger.error(f"Error loading county data for {county}: {e}")
            return {}
    
    def answer_question(self, question: str, farmer_data: Optional[Dict] = None, 
                       language: str = 'en', use_internet: bool = True) -> str:
        """
        Answer farmer's question with personalization and internet search
        
        Args:
            question: Farmer's question in any language
            farmer_data: Farmer profile (name, county, crops, farm_size, etc.)
            language: Preferred response language ('en' or 'sw')
            use_internet: Whether to use internet search for current information
        """
        
        if not self.openai_available:
            return self._fallback_response(question, language)
        
        try:
            # Build context
            context = self._build_context(farmer_data)
            
            # Create system prompt
            system_prompt = self._create_system_prompt(language, farmer_data)
            
            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{context}\n\nQuestion: {question}"}
            ]
            
            # Call GPT-4 (or GPT-3.5-turbo as fallback)
            if not OPENAI_AVAILABLE or not openai:
                return self._fallback_response(question, language)
            
            response = openai.ChatCompletion.create(
                model="gpt-4" if use_internet else "gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Log interaction if farmer is logged in
            if farmer_data and self.mongo:
                self._log_chat_history(farmer_data, question, answer)
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating Flora response: {e}")
            return self._fallback_response(question, language)
    
    def _create_system_prompt(self, language: str, farmer_data: Optional[Dict] = None) -> str:
        """Create system prompt for Flora AI"""
        
        base_prompt = """You are Flora, an AI agricultural assistant for BloomWatch Kenya. 
You help Kenyan farmers with crop advice, bloom detection insights, weather information, 
and farming practices using NASA satellite data (Sentinel-2, Landsat, MODIS).

Key capabilities:
- Interpret NDVI (crop health), NDWI (water stress), temperature, and rainfall data
- Provide crop-specific advice based on growth stages
- Explain bloom cycles and optimal harvest timing
- Suggest pest and disease management strategies
- Offer weather-based farming recommendations
- Support both English and Kiswahili languages

Guidelines:
- Be friendly, respectful, and encouraging
- Use simple language that farmers can understand
- Provide practical, actionable advice
- Reference local Kenyan farming practices
- Include relevant satellite data when available
- Be culturally sensitive and use local examples
"""
        
        if language == 'sw':
            base_prompt += "\n\nIMPORTANT: Respond in Kiswahili (Swahili). Use clear, simple Kiswahili that farmers can understand."
        else:
            base_prompt += "\n\nIMPORTANT: Respond in English. Use clear, simple language."
        
        if farmer_data:
            personalization = f"""
FARMER PROFILE:
- Name: {farmer_data.get('name', 'Farmer')}
- County: {farmer_data.get('county', 'Unknown')}
- Region: {farmer_data.get('region', 'Unknown')}
- Crops: {', '.join(farmer_data.get('crops', []))}
- Farm Size: {farmer_data.get('farm_size', 'Unknown')} acres
- Language: {farmer_data.get('language', language)}

Personalize your response using the farmer's name and reference their specific crops and location.
"""
            base_prompt += personalization
        
        return base_prompt
    
    def _build_context(self, farmer_data: Optional[Dict] = None) -> str:
        """Build context from satellite and county data"""
        context = "CURRENT DATA:\n"
        
        if farmer_data and farmer_data.get('county'):
            county = farmer_data['county']
            county_data = self.get_county_data(county)
            
            if county_data:
                satellite = county_data.get('satellite_data', {})
                bloom = county_data.get('bloom_data', {})
                
                context += f"\nCounty: {county}\n"
                context += f"Region: {county_data.get('region', 'Unknown')}\n"
                context += f"\nSATELLITE DATA (from {satellite.get('data_source', 'Unknown')}):\n"
                context += f"- NDVI (Crop Health): {satellite.get('ndvi', 0):.2f} (0-1 scale, higher = healthier)\n"
                context += f"- NDWI (Water Status): {satellite.get('ndwi', 0):.2f} (-1 to 1, negative = dry)\n"
                context += f"- Temperature: {satellite.get('temperature_c', 0):.1f}°C\n"
                context += f"- Rainfall: {satellite.get('rainfall_mm', 0):.1f}mm\n"
                context += f"\nBLOOM DETECTION:\n"
                context += f"- Bloom Probability: {bloom.get('bloom_probability', 0)}%\n"
                context += f"- Prediction: {bloom.get('bloom_prediction', 'Unknown')}\n"
                context += f"- Confidence: {bloom.get('confidence', 'Unknown')}\n"
                context += f"- Message: {bloom.get('message', 'No data')}\n"
                
                crops = county_data.get('main_crops', [])
                if crops:
                    context += f"\nMain Crops in {county}: {', '.join(crops)}\n"
        
        context += f"\nCurrent Date: {datetime.now().strftime('%B %d, %Y')}\n"
        
        return context
    
    def generate_county_report(self, county: str, farmer_data: Optional[Dict] = None, 
                              language: str = 'en') -> str:
        """Generate personalized county bloom and climate report"""
        
        county_data = self.get_county_data(county)
        if not county_data:
            return "County data not available. Please try again later." if language == 'en' else "Data ya kaunti haipatikani. Tafadhali jaribu baadaye."
        
        prompt = f"""Generate a personalized agricultural report for {county} county focusing on:
1. Current bloom status and what it means for farmers
2. Crop health assessment based on NDVI data
3. Water stress analysis (NDWI)
4. Weather conditions and recommendations
5. Specific advice for the main crops grown in this county
6. Action items for the coming week

Make it practical and actionable."""
        
        if farmer_data:
            prompt += f"\n\nPersonalize for {farmer_data.get('name', 'the farmer')} who grows {', '.join(farmer_data.get('crops', []))} on {farmer_data.get('farm_size', 'their')} acres."
        
        return self.answer_question(prompt, farmer_data, language, use_internet=False)
    
    def interpret_county_data(self, county: str, farmer_data: Optional[Dict] = None, 
                             language: str = 'en') -> str:
        """Interpret county data and provide agricultural advice"""
        
        county_data = self.get_county_data(county)
        if not county_data:
            return "County data not available." if language == 'en' else "Data ya kaunti haipatikani."
        
        prompt = f"""As an agricultural expert, interpret the satellite data for {county} and provide:
1. What the NDVI value means for crop health
2. What the NDWI value indicates about water availability
3. How current temperature affects crops
4. Bloom probability interpretation
5. Specific farming actions recommended this week
6. Potential risks or concerns
7. Opportunities for optimal crop management

Be specific and actionable."""
        
        if farmer_data:
            prompt += f"\n\nFocus on {farmer_data.get('name', 'farmer')}'s crops: {', '.join(farmer_data.get('crops', []))}"
        
        return self.answer_question(prompt, farmer_data, language, use_internet=False)
    
    def _fallback_response(self, question: str, language: str = 'en') -> str:
        """Provide fallback response when AI is not available"""
        
        if language == 'sw':
            return """Samahani, huduma ya Flora haipo kwa sasa. Tafadhali jaribu baadaye au wasiliana na timu yetu kwa msaada.

Unaweza pia kutembelea wavuti yetu: bloomwatch.ke kwa taarifa zaidi.

Asante!"""
        else:
            return """Sorry, Flora AI service is currently unavailable. Please try again later or contact our support team.

You can also visit our website: bloomwatch.ke for more information.

Thank you!"""
    
    def _log_chat_history(self, farmer_data: Dict, question: str, answer: str):
        """Log chat interaction to database"""
        if not self.mongo:
            return
        
        try:
            chat_entry = {
                'farmer_id': farmer_data.get('_id'),
                'phone': farmer_data.get('phone'),
                'question': question,
                'answer': answer,
                'language': farmer_data.get('language', 'en'),
                'county': farmer_data.get('county'),
                'timestamp': datetime.now()
            }
            
            # Save to chat_history collection
            if hasattr(self.mongo, 'db') and self.mongo.db:
                self.mongo.db['chat_history'].insert_one(chat_entry)
                logger.info(f"✓ Chat logged for farmer {farmer_data.get('phone')}")
        except Exception as e:
            logger.error(f"Error logging chat history: {e}")
    
    def get_chat_history(self, farmer_phone: str, limit: int = 20) -> List[Dict]:
        """Get chat history for a farmer"""
        if not self.mongo or not hasattr(self.mongo, 'db') or not self.mongo.db:
            return []
        
        try:
            history = list(
                self.mongo.db['chat_history']
                .find({'phone': farmer_phone})
                .sort('timestamp', -1)
                .limit(limit)
            )
            
            for entry in history:
                entry['_id'] = str(entry['_id'])
            
            return history
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []

# Test/Demo
if __name__ == "__main__":
    print("=" * 80)
    print("🌸 Flora AI Service Test")
    print("=" * 80)
    
    from mongodb_service import MongoDBService
    
    # Initialize services
    mongo = MongoDBService()
    flora = FloraAIService(mongo)
    
    # Test farmer data
    test_farmer = {
        'name': 'John Kamau',
        'phone': '+254712345678',
        'county': 'Kiambu',
        'region': 'central',
        'crops': ['coffee', 'maize', 'beans'],
        'farm_size': 5,
        'language': 'en'
    }
    
    print("\n📊 Test 1: Generate County Report (English)")
    print("-" * 80)
    report = flora.generate_county_report('Kiambu', test_farmer, 'en')
    print(report)
    
    print("\n\n📊 Test 2: Interpret County Data (Kiswahili)")
    print("-" * 80)
    interpretation = flora.interpret_county_data('Kiambu', test_farmer, 'sw')
    print(interpretation)
    
    print("\n\n💬 Test 3: Answer Custom Question")
    print("-" * 80)
    question = "When is the best time to plant maize in Kiambu?"
    answer = flora.answer_question(question, test_farmer, 'en')
    print(f"Q: {question}")
    print(f"A: {answer}")
    
    print("\n" + "=" * 80)
    print("✓ Flora AI test completed!")

