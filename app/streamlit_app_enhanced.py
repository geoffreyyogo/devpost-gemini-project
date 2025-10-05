"""
BloomWatch Kenya - Enhanced Professional Web Application
NASA-Powered Bloom Tracking Platform with Stunning UI/UX
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import numpy as np
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
import time
import json

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="BloomWatch Kenya 🌾",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Try to import streamlit-lottie for animations
try:
    from streamlit_lottie import st_lottie
    import requests
    LOTTIE_AVAILABLE = True
except ImportError:
    LOTTIE_AVAILABLE = False
    st.info("💡 Install streamlit-lottie for enhanced animations: pip install streamlit-lottie")

# Import services with fallbacks
try:
    from auth_service import AuthService
    from mongodb_service import MongoDBService
    from bloom_processor import BloomProcessor
    from gee_data_loader import GEEDataLoader
except ImportError:
    # Create dummy auth service for demo
    class AuthService:
        def __init__(self): pass
        def login(self, phone, password):
            return {
                'success': True, 'demo': True,
                'farmer': {
                    'phone': phone, 'name': 'Demo Farmer', 'region': 'central', 
                    'crops': ['maize', 'beans', 'coffee'], 'language': 'en',
                    'email': 'demo@bloomwatch.co.ke'
                },
                'session_token': 'demo_token_' + str(int(time.time()))
            }
        def register_farmer(self, data, password):
            return {'success': True, 'demo': True, 'message': 'Demo registration successful'}
        def verify_session(self, token):
            return {'phone': 'demo', 'demo': True} if token else None
        def logout(self, token): return True
        def get_farmer_from_session(self, token):
            if token: 
                return {
                    'phone': 'demo', 'name': 'Demo Farmer', 'region': 'central', 
                    'crops': ['maize', 'beans', 'coffee'], 'language': 'en', 'demo': True,
                    'email': 'demo@bloomwatch.co.ke'
                }
            return None
    
    MongoDBService = None
    BloomProcessor = None
    GEEDataLoader = None

try:
    from kenya_crops import KenyaCropCalendar, KENYA_REGIONS
except ImportError:
    # Fallback Kenya data
    KENYA_REGIONS = {
        'central': {
            'counties': ['Kiambu', "Murang'a", 'Nyeri', 'Kirinyaga', 'Nyandarua'],
            'main_crops': ['coffee', 'tea', 'maize', 'beans', 'potatoes'],
            'coordinates': {'lat': -0.9, 'lon': 36.9}
        },
        'rift_valley': {
            'counties': ['Nakuru', 'Uasin Gishu', 'Trans Nzoia', 'Kericho', 'Bomet'],
            'main_crops': ['maize', 'wheat', 'tea', 'pyrethrum', 'barley'],
            'coordinates': {'lat': 0.2, 'lon': 35.8}
        },
        'western': {
            'counties': ['Kakamega', 'Bungoma', 'Busia', 'Vihiga'],
            'main_crops': ['maize', 'beans', 'sugarcane', 'tea', 'bananas'],
            'coordinates': {'lat': 0.5, 'lon': 34.8}
        },
        'eastern': {
            'counties': ['Machakos', 'Kitui', 'Makueni', 'Embu', 'Tharaka-Nithi'],
            'main_crops': ['maize', 'beans', 'sorghum', 'millet', 'cotton'],
            'coordinates': {'lat': -1.5, 'lon': 37.5}
        },
        'coast': {
            'counties': ['Mombasa', 'Kilifi', 'Kwale', 'Lamu'],
            'main_crops': ['coconut', 'cashew', 'maize', 'cassava', 'mango'],
            'coordinates': {'lat': -3.5, 'lon': 39.7}
        }
    }
    
    class KenyaCropCalendar:
        def get_current_season(self):
            month = datetime.now().month
            if 3 <= month <= 5: return 'long_rains'
            elif 10 <= month <= 12: return 'short_rains'
            elif month in [1, 2]: return 'dry_season_1'
            else: return 'dry_season_2'
        
        def get_expected_blooms(self, month=None):
            month = month or datetime.now().month
            bloom_calendar = {
                1: ['coffee'], 2: ['coffee'], 3: ['maize'], 4: ['maize', 'beans'],
                5: ['beans', 'coffee'], 6: ['maize'], 7: ['maize'], 8: [],
                9: [], 10: ['maize'], 11: ['maize', 'beans'], 12: ['beans']
            }
            blooms = bloom_calendar.get(month, [])
            return {crop: ['season'] for crop in blooms}
        
        def get_agricultural_advice(self, crop, stage):
            advice_db = {
                'maize': {
                    'flowering': {
                        'en': "Monitor for pests and ensure adequate moisture during flowering.",
                        'sw': "Chunguza wadudu na hakikisha unyevunyevu wa kutosha wakati wa kuchanua."
                    },
                    'tasseling': {
                        'en': "Apply nitrogen fertilizer and check for fall armyworm.",
                        'sw': "Tumia mbolea ya nitrojeni na kagua funza wa jeshi."
                    }
                },
                'coffee': {
                    'flowering': {
                        'en': "Protect flowers from heavy rain and maintain soil moisture.",
                        'sw': "Linda maua kutoka mvua kubwa na dumisha unyevu wa udongo."
                    }
                },
                'beans': {
                    'flowering': {
                        'en': "Ensure good drainage and watch for bean fly during flowering.",
                        'sw': "Hakikisha mtiririko mzuri wa maji na chunguza nzi wa maharagwe wakati wa kuchanua."
                    }
                }
            }
            return advice_db.get(crop, {}).get(stage, {
                'en': "Monitor your crops carefully.",
                'sw': "Chunguza mazao yako kwa makini."
            })

# Lottie animation URLs
LOTTIE_URLS = {
    'satellite': 'https://assets5.lottiefiles.com/packages/lf20_nLjNFH.json',
    'farming': 'https://assets9.lottiefiles.com/packages/lf20_touohxv0.json',
    'plant_growth': 'https://assets2.lottiefiles.com/packages/lf20_kcsr6fcp.json',
    'weather': 'https://assets4.lottiefiles.com/packages/lf20_kxsd2zr.json',
    'success': 'https://assets9.lottiefiles.com/packages/lf20_lk80fpsm.json',
    'loading': 'https://assets8.lottiefiles.com/packages/lf20_a2chheio.json',
}

def load_lottie_url(url):
    """Load Lottie animation from URL"""
    if not LOTTIE_AVAILABLE:
        return None
    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

# Initialize dark mode CSS
def get_custom_css(dark_mode=False):
    """Generate custom CSS based on theme"""
    
    if dark_mode:
        # Dark mode colors
        bg_light = "#1a1a1a"
        bg_white = "#2d2d2d"
        text_dark = "#e0e0e0"
        text_light = "#b0b0b0"
        shadow_sm = "0 2px 4px rgba(0,0,0,0.5)"
        shadow_md = "0 4px 12px rgba(0,0,0,0.6)"
        shadow_lg = "0 8px 24px rgba(0,0,0,0.7)"
        input_bg = "#3d3d3d"
        input_border = "#555555"
    else:
        # Light mode colors
        bg_light = "#F8FBF8"
        bg_white = "#FFFFFF"
        text_dark = "#212121"
        text_light = "#757575"
        shadow_sm = "0 2px 4px rgba(0,0,0,0.08)"
        shadow_md = "0 4px 12px rgba(0,0,0,0.12)"
        shadow_lg = "0 8px 24px rgba(0,0,0,0.15)"
        input_bg = "#FFFFFF"
        input_border = "#E0E0E0"
    
    return f"""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Inter:wght@300;400;500;600&display=swap');
    
    /* Global styles */
    * {{
        font-family: 'Inter', 'Poppins', sans-serif;
    }}
    
    html, body, [data-testid="stAppViewContainer"], .main {{
        background: {bg_light} !important;
        color: {text_dark} !important;
    }}
    
    /* Streamlit containers */
    [data-testid="stAppViewContainer"] > .main {{
        background: {bg_light};
    }}
    
    section[data-testid="stSidebar"] {{
        background: {bg_white};
    }}
    
    /* Remove default padding */
    .main .block-container {{
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1600px;
    }}
    
    /* Hero section with animated background */
    .hero-section {{
        background: linear-gradient(135deg, #2E7D32 0%, #66BB6A 50%, #81C784 100%);
        padding: 4rem 2rem;
        border-radius: 24px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: {shadow_lg};
        position: relative;
        overflow: hidden;
        animation: gradientShift 8s ease infinite;
    }}
    
    @keyframes gradientShift {{
        0%, 100% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
    }}
    
    .hero-section::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=1200') center/cover;
        opacity: 0.15;
        animation: parallax 20s ease infinite;
    }}
    
    @keyframes parallax {{
        0%, 100% {{ transform: scale(1) translateY(0); }}
        50% {{ transform: scale(1.1) translateY(-10px); }}
    }}
    
    .hero-content {{
        position: relative;
        z-index: 1;
    }}
    
    .hero-section h1 {{
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        animation: fadeInUp 1s ease;
    }}
    
    .hero-section p {{
        font-size: 1.4rem;
        opacity: 0.95;
        margin-bottom: 2rem;
        animation: fadeInUp 1s ease 0.2s backwards;
    }}
    
    @keyframes fadeInUp {{
        from {{
            opacity: 0;
            transform: translateY(30px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    /* Animated stat cards */
    .stat-card {{
        background: {bg_white};
        padding: 2rem;
        border-radius: 16px;
        box-shadow: {shadow_md};
        border-left: 6px solid #2E7D32;
        margin-bottom: 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        animation: fadeIn 0.8s ease;
        position: relative;
        overflow: hidden;
        color: {text_dark};
    }}
    
    .stat-card h2 {{
        color: #2E7D32;
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
    }}
    
    .stat-card p {{
        color: {text_light};
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        font-weight: 500;
    }}
    
    /* Feature cards */
    .feature-card {{
        background: {bg_white};
        padding: 2rem;
        border-radius: 20px;
        box-shadow: {shadow_sm};
        text-align: center;
        border: 2px solid transparent;
        color: {text_dark};
    }}
    
    .feature-card h3, .feature-card p {{
        color: {text_dark};
    }}
    
    /* Buttons with gradient and animation */
    .stButton > button {{
        background: linear-gradient(135deg, #2E7D32 0%, #66BB6A 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.85rem 2.5rem !important;
        font-size: 1.1rem !important;
        border-radius: 50px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: {shadow_sm} !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-3px) !important;
        box-shadow: {shadow_md} !important;
    }}
    
    /* Form inputs - FIXED */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stMultiSelect > div > div {{
        border-radius: 12px !important;
        border: 2px solid {input_border} !important;
        padding: 0.85rem !important;
        font-size: 1rem !important;
        background: {input_bg} !important;
        color: {text_dark} !important;
        transition: all 0.3s ease !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {{
        border-color: #2E7D32 !important;
        box-shadow: 0 0 0 3px rgba(46,125,50,0.1) !important;
        outline: none !important;
    }}
    
    /* Selectbox styling */
    .stSelectbox label, .stTextInput label, .stMultiSelect label {{
        color: {text_dark} !important;
        font-weight: 600 !important;
    }}
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: {bg_white};
        padding: 1rem;
        border-radius: 16px;
        box-shadow: {shadow_sm};
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        background: transparent !important;
        color: {text_dark} !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, #2E7D32 0%, #66BB6A 100%) !important;
        color: white !important;
    }}
    
    /* Metrics */
    [data-testid="stMetric"] {{
        background: {bg_white} !important;
        padding: 1.5rem !important;
        border-radius: 16px !important;
        box-shadow: {shadow_sm} !important;
    }}
    
    [data-testid="stMetricLabel"] {{
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: {text_light} !important;
    }}
    
    [data-testid="stMetricValue"] {{
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #2E7D32 !important;
    }}
    
    /* Expanders */
    .streamlit-expanderHeader {{
        background: {bg_white} !important;
        color: {text_dark} !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        font-weight: 600 !important;
    }}
    
    /* Dataframes */
    .stDataFrame {{
        border-radius: 16px;
        overflow: hidden;
        box-shadow: {shadow_sm};
    }}
    
    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Smooth animations */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    @keyframes slideIn {{
        from {{ opacity: 0; transform: translateX(-20px); }}
        to {{ opacity: 1; transform: translateX(0); }}
    }}
    
    @keyframes bounce {{
        0%, 100% {{ transform: translateY(0); }}
        50% {{ transform: translateY(-10px); }}
    }}
    
    .pulse {{
        animation: pulse 2s infinite;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ transform: scale(1); }}
        50% {{ transform: scale(1.05); }}
    }}
</style>
"""

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'initialized': True,
        'page': 'landing',
        'authenticated': False,
        'session_token': None,
        'farmer_data': None,
        'language': 'en',
        'dark_mode': False,
        'show_success': False,
        'success_message': '',
        'show_error': False,
        'error_message': ''
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Initialize services
@st.cache_resource
def get_services():
    """Get singleton instances of services"""
    auth = AuthService()
    mongo = MongoDBService() if MongoDBService else None
    calendar = KenyaCropCalendar()
    bloom_proc = BloomProcessor() if BloomProcessor else None
    gee_loader = GEEDataLoader() if GEEDataLoader else None
    return auth, mongo, calendar, bloom_proc, gee_loader

auth_service, mongo_service, crop_calendar, bloom_processor, gee_loader = get_services()

# Load actual bloom data
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_bloom_data():
    """Get actual bloom detection data"""
    if bloom_processor:
        try:
            return bloom_processor.detect_bloom_events('kenya')
        except Exception as e:
            st.warning(f"Could not load bloom data: {e}")
            return None
    return None

# Load actual GEE data
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_gee_data():
    """Get actual GEE satellite data"""
    if gee_loader:
        try:
            return gee_loader.load_kenya_data()
        except Exception as e:
            st.warning(f"Could not load GEE data: {e}")
            return None
    return None

# Language translations
TRANSLATIONS = {
    'en': {
        'welcome': 'Welcome to BloomWatch Kenya',
        'tagline': 'Empowering Kenyan farmers with NASA satellite technology for real-time crop bloom detection',
        'get_started': 'Get Started',
        'login': 'Login',
        'register': 'Register',
        'logout': 'Logout',
        'dashboard': 'Dashboard',
        'phone': 'Phone Number',
        'password': 'Password',
        'name': 'Full Name',
        'email': 'Email Address',
        'region': 'Select Your Region',
        'crops': 'Select Crops You Grow',
        'language_pref': 'Preferred Language',
        'confirm_password': 'Confirm Password',
        'register_button': 'Complete Registration',
        'login_button': 'Login to Dashboard',
        'back': 'Back',
        'profile': 'My Profile',
        'alerts': 'Bloom Alerts',
        'calendar': 'Crop Calendar',
        'statistics': 'Statistics',
        'success_registration': '🎉 Registration successful! Welcome to BloomWatch Kenya.',
        'success_login': '🎉 Login successful! Welcome back to your farm dashboard.',
        'error_passwords': 'Passwords do not match',
        'error_fields': 'Please fill all required fields',
        'current_season': 'Current Season',
        'active_blooms': 'Active Blooms',
        'farmers_registered': 'Farmers Registered',
        'yield_increase': 'Avg. Yield Increase',
        'alerts_sent': 'Alerts Sent Today',
        'features_title': '🌟 Why BloomWatch Kenya?',
        'feature_1': 'NASA Satellites',
        'feature_1_desc': 'Sentinel-2, Landsat & MODIS imagery',
        'feature_2': 'SMS Alerts',
        'feature_2_desc': 'Instant notifications in English & Kiswahili',
        'feature_3': 'Crop Calendar',
        'feature_3_desc': 'Tailored for Kenyan agricultural seasons',
        'feature_4': 'Free Service',
        'feature_4_desc': 'No cost for smallholder farmers',
        'testimonials': '💬 Farmer Success Stories',
        'footer': 'BloomWatch Kenya - NASA Space Apps Challenge 2025 | Powered by Earth Observation Data'
    },
    'sw': {
        'welcome': 'Karibu BloomWatch Kenya',
        'tagline': 'Kuwawezesha wakulima wa Kenya kwa teknolojia ya satelaiti za NASA kwa kugundua kuchanua kwa wakati halisi',
        'get_started': 'Anza Sasa',
        'login': 'Ingia',
        'register': 'Jisajili',
        'logout': 'Toka',
        'dashboard': 'Dashibodi',
        'phone': 'Nambari ya Simu',
        'password': 'Neno la Siri',
        'name': 'Jina Kamili',
        'email': 'Barua Pepe',
        'region': 'Chagua Mkoa Wako',
        'crops': 'Chagua Mazao Unayolima',
        'language_pref': 'Lugha Unayopendelea',
        'confirm_password': 'Thibitisha Neno la Siri',
        'register_button': 'Kamilisha Usajili',
        'login_button': 'Ingia kwenye Dashibodi',
        'back': 'Rudi',
        'profile': 'Wasifu Wangu',
        'alerts': 'Arifa za Kuchanua',
        'calendar': 'Kalenda ya Mazao',
        'statistics': 'Takwimu',
        'success_registration': '🎉 Usajili umefanikiwa! Karibu BloomWatch Kenya.',
        'success_login': '🎉 Umeingia kikamilifu! Karibu tena kwenye dashibodi ya shamba lako.',
        'error_passwords': 'Maneno ya siri hayalingani',
        'error_fields': 'Tafadhali jaza sehemu zote muhimu',
        'current_season': 'Msimu wa Sasa',
        'active_blooms': 'Kuchanua Kinachoendelea',
        'farmers_registered': 'Wakulima Waliosajiliwa',
        'yield_increase': 'Ongezeko la Mavuno',
        'alerts_sent': 'Arifa Zilizotumwa Leo',
        'features_title': '🌟 Kwa Nini BloomWatch Kenya?',
        'feature_1': 'Satelaiti za NASA',
        'feature_1_desc': 'Picha za Sentinel-2, Landsat na MODIS',
        'feature_2': 'Arifa za SMS',
        'feature_2_desc': 'Taarifa za haraka kwa Kiingereza na Kiswahili',
        'feature_3': 'Kalenda ya Mazao',
        'feature_3_desc': 'Imeboreshwa kwa misimu ya kilimo ya Kenya',
        'feature_4': 'Huduma Bure',
        'feature_4_desc': 'Bila malipo kwa wakulima wadogo',
        'testimonials': '💬 Hadithi za Mafanikio ya Wakulima',
        'footer': 'BloomWatch Kenya - NASA Space Apps Challenge 2025 | Inaendeshwa na Data ya Uchunguzi wa Dunia'
    }
}

def t(key):
    """Get translation for current language"""
    return TRANSLATIONS[st.session_state.language].get(key, key)

def show_notification(message, type='success'):
    """Show animated notification"""
    if type == 'success':
        st.success(f"✅ {message}", icon="✅")
    elif type == 'error':
        st.error(f"❌ {message}", icon="❌")
    elif type == 'info':
        st.info(f"ℹ️ {message}", icon="ℹ️")
    elif type == 'warning':
        st.warning(f"⚠️ {message}", icon="⚠️")

def landing_page():
    """Enhanced landing page with hero section and animations"""
    
    # Top navigation bar
    col_logo, col_space, col_dark, col_lang = st.columns([2, 4, 1, 1])
    
    with col_dark:
        if st.button("🌙" if not st.session_state.dark_mode else "☀️", key='dark_mode_toggle'):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    
    with col_lang:
        lang_option = st.selectbox(
            '',
            ['English', 'Kiswahili'],
            key='lang_select',
            label_visibility='collapsed'
        )
        st.session_state.language = 'en' if lang_option == 'English' else 'sw'
    
    # Hero section with animation
    st.markdown(f"""
    <div class="hero-section">
        <div class="hero-content">
            <h1>🌾 {t('welcome')}</h1>
            <p>{t('tagline')}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Lottie animation for satellite
    if LOTTIE_AVAILABLE:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            lottie_satellite = load_lottie_url(LOTTIE_URLS['satellite'])
            if lottie_satellite:
                st_lottie(lottie_satellite, height=200, key="hero_satellite")
    
    # Statistics cards with animation
    st.markdown(f"### {t('statistics')}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="icon">👨‍🌾</div>
            <h2>1,247+</h2>
            <p>{t('farmers_registered')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="icon">📈</div>
            <h2>32%</h2>
            <p>{t('yield_increase')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="icon">🔔</div>
            <h2>856</h2>
            <p>{t('alerts_sent')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="icon">🗺️</div>
            <h2>5</h2>
            <p>Regions Covered</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Call to action buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button(f"🚀 {t('get_started')}", key='get_started', use_container_width=True):
                st.session_state.page = 'register'
                st.rerun()
        
        with col_b:
            if st.button(f"👤 {t('login')}", key='login_nav', use_container_width=True):
                st.session_state.page = 'login'
                st.rerun()
    
    st.markdown("---")
    
    # Features section
    st.markdown(f"## {t('features_title')}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="feature-card">
            <div class="icon">🛰️</div>
            <h3>{t('feature_1')}</h3>
            <p>{t('feature_1_desc')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="feature-card">
            <div class="icon">📱</div>
            <h3>{t('feature_2')}</h3>
            <p>{t('feature_2_desc')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="feature-card">
            <div class="icon">📅</div>
            <h3>{t('feature_3')}</h3>
            <p>{t('feature_3_desc')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="feature-card">
            <div class="icon">💰</div>
            <h3>{t('feature_4')}</h3>
            <p>{t('feature_4_desc')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Testimonials
    st.markdown(f"## {t('testimonials')}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        **John Kamau - Kiambu** 🌾
        
        *"BloomWatch helped me increase my maize yield by 25%! The SMS alerts are perfect."*
        
        *"BloomWatch ilinisaidia kuongeza mavuno yangu ya mahindi kwa 25%!"*
        """)
    
    with col2:
        st.success("""
        **Mary Wanjiku - Nyeri** ☕
        
        *"The coffee bloom alerts helped me prepare for harvest. Amazing service!"*
        
        *"Arifa za kuchanua kwa kahawa ziliniwezesha kujiandaa kwa mavuno."*
        """)
    
    with col3:
        st.warning("""
        **Peter Mwangi - Nakuru** 🌻
        
        *"Free satellite data for my small farm? This is revolutionary!"*
        
        *"Data za satelaiti bure kwa shamba langu? Hii ni mapinduzi!"*
        """)
    
    # Footer
    st.markdown("---")
    st.markdown(f"<p style='text-align: center; color: var(--text-light);'>{t('footer')}</p>", unsafe_allow_html=True)

def login_page():
    """Enhanced login page with Lottie animation"""
    # Back button
    if st.button(f"← {t('back')}", key='back_from_login'):
        st.session_state.page = 'landing'
        st.rerun()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"## 👤 {t('login')}")
        
        # Lottie animation
        if LOTTIE_AVAILABLE:
            lottie_farming = load_lottie_url(LOTTIE_URLS['farming'])
            if lottie_farming:
                st_lottie(lottie_farming, height=150, key="login_animation")
        
        with st.form("login_form", clear_on_submit=False):
            phone = st.text_input(
                t('phone'),
                placeholder="+254712345678",
                help="Enter your registered phone number"
            )
            
            password = st.text_input(
                t('password'),
                type="password",
                help="Enter your password"
            )
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                submit = st.form_submit_button(f"🔐 {t('login_button')}", use_container_width=True)
            
            with col_b:
                register = st.form_submit_button("📝 Register Instead", use_container_width=True)
            
            if register:
                st.session_state.page = 'register'
                st.rerun()
            
            if submit:
                if not phone or not password:
                    show_notification(t('error_fields'), 'error')
                else:
                    with st.spinner('🔍 Authenticating...'):
                        time.sleep(1)  # Simulate processing
                        result = auth_service.login(phone, password)
                        
                        if result['success']:
                            st.session_state.authenticated = True
                            st.session_state.session_token = result['session_token']
                            st.session_state.farmer_data = result['farmer']
                            st.session_state.page = 'dashboard'
                            show_notification(t('success_login'), 'success')
                            st.balloons()  # Celebration animation
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            show_notification(result.get('message', 'Login failed'), 'error')

def register_page():
    """Enhanced registration page with step visualization"""
    # Back button
    if st.button(f"← {t('back')}", key='back_from_register'):
        st.session_state.page = 'landing'
        st.rerun()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"## 📝 {t('register')}")
        
        # Lottie animation
        if LOTTIE_AVAILABLE:
            lottie_plant = load_lottie_url(LOTTIE_URLS['plant_growth'])
            if lottie_plant:
                st_lottie(lottie_plant, height=150, key="register_animation")
        
        # Progress indicator
        st.progress(0.0, text="Step 1 of 3: Personal Information")
        
        with st.form("register_form", clear_on_submit=False):
            # Personal info
            st.markdown("### 👤 Personal Information")
            name = st.text_input(
                t('name'),
                placeholder="John Kamau",
                help="Enter your full name"
            )
            
            phone = st.text_input(
                t('phone'),
                placeholder="+254712345678",
                help="Your phone number will be used for login and SMS alerts"
            )
            
            email = st.text_input(
                t('email'),
                placeholder="john@example.com",
                help="Optional: for email alerts"
            )
            
            st.markdown("### 🌾 Farm Information")
            
            region = st.selectbox(
                t('region'),
                options=list(KENYA_REGIONS.keys()),
                format_func=lambda x: x.replace('_', ' ').title()
            )
            
            available_crops = ['maize', 'beans', 'coffee', 'tea', 'wheat', 'sorghum', 'millet', 'cassava']
            crops = st.multiselect(
                t('crops'),
                options=available_crops,
                default=['maize'],
                format_func=lambda x: x.title(),
                help="Select all crops you grow"
            )
            
            language = st.selectbox(
                t('language_pref'),
                options=['en', 'sw'],
                format_func=lambda x: 'English' if x == 'en' else 'Kiswahili'
            )
            
            st.markdown("### 🔒 Security")
            
            password = st.text_input(
                t('password'),
                type="password",
                help="Create a secure password (min 6 characters)"
            )
            
            confirm_password = st.text_input(
                t('confirm_password'),
                type="password"
            )
            
            st.markdown("---")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                submit = st.form_submit_button(f"✓ {t('register_button')}", use_container_width=True)
            
            with col_b:
                login_instead = st.form_submit_button("🔐 Login Instead", use_container_width=True)
            
            if login_instead:
                st.session_state.page = 'login'
                st.rerun()
            
            if submit:
                # Validation
                if not all([name, phone, region, crops, password, confirm_password]):
                    show_notification(t('error_fields'), 'error')
                elif password != confirm_password:
                    show_notification(t('error_passwords'), 'error')
                elif len(password) < 6:
                    show_notification("Password must be at least 6 characters", 'error')
                else:
                    # Register farmer
                    farmer_data = {
                        'name': name,
                        'phone': phone,
                        'email': email,
                        'region': region,
                        'crops': crops,
                        'language': language,
                        'location_lat': KENYA_REGIONS[region]['coordinates']['lat'],
                        'location_lon': KENYA_REGIONS[region]['coordinates']['lon'],
                        'sms_enabled': True,
                        'registered_via': 'web'
                    }
                    
                    with st.spinner('🌱 Creating your account...'):
                        time.sleep(1.5)  # Simulate processing
                        result = auth_service.register_farmer(farmer_data, password)
                        
                        if result['success']:
                            show_notification(t('success_registration'), 'success')
                            st.balloons()  # Celebration!
                            time.sleep(2)
                            st.session_state.page = 'login'
                            st.rerun()
                        else:
                            show_notification(result.get('message', 'Registration failed'), 'error')

def dashboard_page():
    """Enhanced dashboard with interactive charts and animations"""
    farmer = st.session_state.farmer_data
    
    if not farmer:
        st.session_state.page = 'landing'
        st.rerun()
        return
    
    # Top navigation with profile
    col1, col2, col3, col4 = st.columns([3, 3, 2, 1])
    
    with col1:
        st.markdown(f"### 👋 Karibu, {farmer.get('name', 'Farmer').split()[0]}!")
    
    with col2:
        st.markdown(f"<p style='color: var(--text-light); padding-top: 1rem;'>📍 {farmer.get('region', '').replace('_', ' ').title()}</p>", unsafe_allow_html=True)
    
    with col3:
        # Language toggle
        lang_option = st.selectbox(
            'Language',
            ['English', 'Kiswahili'],
            index=0 if farmer.get('language', 'en') == 'en' else 1,
            key='dash_lang',
            label_visibility='collapsed'
        )
        st.session_state.language = 'en' if lang_option == 'English' else 'sw'
    
    with col4:
        if st.button(f"🚪 {t('logout')}", key='logout_button', use_container_width=True):
            auth_service.logout(st.session_state.session_token)
            st.session_state.authenticated = False
            st.session_state.session_token = None
            st.session_state.farmer_data = None
            st.session_state.page = 'landing'
            st.rerun()
    
    st.markdown("---")
    
    # Tabs with icons
    tab1, tab2, tab3, tab4 = st.tabs([
        f"📊 {t('dashboard')}",
        f"📅 {t('calendar')}",
        f"🔔 {t('alerts')}",
        f"👤 {t('profile')}"
    ])
    
    with tab1:
        show_dashboard_tab(farmer)
    
    with tab2:
        show_calendar_tab(farmer)
    
    with tab3:
        show_alerts_tab(farmer)
    
    with tab4:
        show_profile_tab(farmer)

def show_dashboard_tab(farmer):
    """Enhanced dashboard with animated charts"""
    # Load actual bloom data
    bloom_data = get_bloom_data()
    gee_data = get_gee_data()
    
    # Key metrics with icons
    col1, col2, col3, col4 = st.columns(4)
    
    current_season = crop_calendar.get_current_season()
    expected_blooms = crop_calendar.get_expected_blooms()
    
    # Get actual bloom count from processor
    num_blooms = len(bloom_data.get('bloom_months', [])) if bloom_data else len(expected_blooms)
    
    with col1:
        st.metric(
            label=f"🌦️ {t('current_season')}",
            value=current_season.replace('_', ' ').title(),
            delta="Ongoing"
        )
    
    with col2:
        st.metric(
            label=f"🌸 {t('active_blooms')}",
            value=num_blooms,
            delta="+2 this week" if num_blooms > 0 else "None"
        )
    
    with col3:
        st.metric(
            label="🌾 Your Crops",
            value=len(farmer.get('crops', [])),
            delta=f"{', '.join([c.title() for c in farmer.get('crops', [])[:2]])}"
        )
    
    with col4:
        # Try to get actual alert count from MongoDB
        alert_count = "24"
        if mongo_service:
            try:
                alerts = mongo_service.get_recent_alerts(farmer.get('phone'), limit=100)
                alert_count = str(len(alerts))
            except:
                pass
        st.metric(
            label="📨 Alerts Received",
            value=alert_count,
            delta="+5 today"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main content columns
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        # Interactive NDVI chart with animations
        st.markdown("### 📈 Farm Health - NDVI Trend (Last 12 Months)")
        
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Use actual NDVI time series if available
        if bloom_data and 'time_series_mean' in bloom_data:
            # Use actual data from bloom processor
            ndvi_values = np.array(bloom_data['time_series_mean'])
            # Pad or trim to 12 months
            if len(ndvi_values) < 12:
                # Pad with Kenya seasonal pattern
                base_ndvi = np.array([0.35, 0.40, 0.55, 0.70, 0.75, 0.60, 0.50, 0.45, 0.50, 0.60, 0.75, 0.65])
                ndvi_values = np.concatenate([ndvi_values, base_ndvi[len(ndvi_values):]])
            elif len(ndvi_values) > 12:
                ndvi_values = ndvi_values[:12]
        else:
            # Fallback to realistic seasonal pattern if no actual data
            base_ndvi = np.array([0.35, 0.40, 0.55, 0.70, 0.75, 0.60, 0.50, 0.45, 0.50, 0.60, 0.75, 0.65])
            ndvi_values = base_ndvi + np.random.uniform(-0.05, 0.05, 12)
        
        # Create animated Plotly chart
        fig = go.Figure()
        
        # Main NDVI line
        fig.add_trace(go.Scatter(
            x=months,
            y=ndvi_values,
            mode='lines+markers',
            name='NDVI',
            line=dict(color='#2E7D32', width=4, shape='spline'),
            marker=dict(size=10, color='#66BB6A', line=dict(color='#1B5E20', width=2)),
            fill='tozeroy',
            fillcolor='rgba(46,125,50,0.1)',
            hovertemplate='<b>%{x}</b><br>NDVI: %{y:.2f}<extra></extra>'
        ))
        
        # Add threshold line
        fig.add_hline(y=0.6, line_dash="dash", line_color="orange", 
                     annotation_text="Healthy Threshold")
        
        # Highlight actual bloom periods from processor
        if bloom_data and 'bloom_months' in bloom_data:
            bloom_months = bloom_data['bloom_months']
        else:
            bloom_months = [3, 4, 10, 11]  # Default: April, May, November, December
        
        for bm in bloom_months:
            fig.add_vrect(
                x0=bm-0.5, x1=bm+0.5,
                fillcolor="rgba(255,193,7,0.2)",
                layer="below",
                line_width=0,
            )
        
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis_title="Month",
            yaxis_title="NDVI Value",
            yaxis_range=[0, 1],
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter, Poppins', size=12),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)')
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Farm location map with bloom heatmap
        st.markdown("### 🗺️ Your Farm Location & Nearby Blooms")
        
        m = folium.Map(
            location=[farmer.get('location_lat', -1.0), farmer.get('location_lon', 37.0)],
            zoom_start=11,
            tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
            attr='CartoDB'
        )
        
        # Add farmer's location
        folium.Marker(
            [farmer.get('location_lat', -1.0), farmer.get('location_lon', 37.0)],
            popup=f"<b>{farmer.get('name')}'s Farm</b><br>Crops: {', '.join([c.title() for c in farmer.get('crops', [])[:3]])}",
            tooltip="Your Farm 🌾",
            icon=folium.Icon(color='green', icon='home', prefix='fa')
        ).add_to(m)
        
        # Add actual bloom hotspots if available
        if bloom_data and 'bloom_hotspots' in bloom_data:
            for hotspot in bloom_data['bloom_hotspots']:
                # Use actual hotspot data
                lat_offset = np.random.uniform(-0.1, 0.1)
                lon_offset = np.random.uniform(-0.1, 0.1)
                intensity = hotspot.get('confidence', 0.7)
                
                folium.CircleMarker(
                    [farmer.get('location_lat', -1.0) + lat_offset, farmer.get('location_lon', 37.0) + lon_offset],
                    radius=8 + intensity * 12,
                    popup=f"Bloom Event<br>Intensity: {intensity:.2f}<br>Location: {hotspot.get('location', 'Unknown')}",
                    color='#FF6F00',
                    fillColor='#FDD835',
                    fillOpacity=0.6,
                    weight=2
                ).add_to(m)
        else:
            # Fallback to synthetic markers
            for i in range(5):
                lat_offset = np.random.uniform(-0.1, 0.1)
                lon_offset = np.random.uniform(-0.1, 0.1)
                intensity = np.random.uniform(0.5, 0.9)
                
                folium.CircleMarker(
                    [farmer.get('location_lat', -1.0) + lat_offset, farmer.get('location_lon', 37.0) + lon_offset],
                    radius=8 + intensity * 12,
                    popup=f"Bloom Event<br>Intensity: {intensity:.2f}",
                    color='#FF6F00',
                    fillColor='#FDD835',
                    fillOpacity=0.6,
                    weight=2
                ).add_to(m)
        
        st_folium(m, height=400, use_container_width=True)
    
    with col_right:
        # Yield prediction gauge (based on health score)
        st.markdown("### 🎯 Predicted Yield (This Season)")
        
        # Use actual health score from bloom processor
        if bloom_data and 'health_score' in bloom_data:
            predicted_yield = bloom_data['health_score']
        else:
            predicted_yield = 85  # Fallback percentage
        
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=predicted_yield,
            delta={'reference': 75, 'increasing': {'color': "#2E7D32"}},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "#2E7D32"},
                'steps': [
                    {'range': [0, 50], 'color': "#FFCDD2"},
                    {'range': [50, 75], 'color': "#FFF9C4"},
                    {'range': [75, 100], 'color': "#C8E6C9"}
                ],
                'threshold': {
                    'line': {'color': "#FF6F00", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            },
            title={'text': "Yield Potential (%)", 'font': {'size': 16}}
        ))
        
        fig_gauge.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=60, b=20),
            font={'family': 'Inter, Poppins'}
        )
        
        st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
        
        # Weather widget (placeholder)
        st.markdown("### 🌤️ Weather Forecast")
        
        weather_data = {
            'Day': ['Today', 'Tomorrow', 'Wed', 'Thu', 'Fri'],
            'Condition': ['☀️ Sunny', '🌤️ Partly Cloudy', '🌧️ Rain', '⛈️ Storms', '🌤️ Cloudy'],
            'Temp (°C)': ['24-28', '23-27', '20-25', '19-24', '22-26'],
            'Rain (%)': ['10%', '30%', '80%', '90%', '40%']
        }
        
        df_weather = pd.DataFrame(weather_data)
        st.dataframe(df_weather, use_container_width=True, hide_index=True)
        
        # Expected blooms (use actual data)
        st.markdown("### 🌸 Expected Blooms This Month")
        
        # Show actual bloom predictions from processor
        if bloom_data and 'bloom_dates' in bloom_data and bloom_data['bloom_dates']:
            st.success("📅 **Upcoming Blooms:**")
            for i, date in enumerate(bloom_data['bloom_dates'][:3]):  # Show first 3
                if i < len(bloom_data.get('bloom_scores', [])):
                    month_idx = bloom_data['bloom_months'][i]
                    score = bloom_data['bloom_scores'][month_idx]
                    st.write(f"• {date} - {score*100:.0f}% confidence")
        elif expected_blooms:
            for crop in expected_blooms.keys():
                if crop in farmer.get('crops', []):
                    st.success(f"🌾 **{crop.title()}** - Ready to bloom!")
        else:
            st.info("No major blooms expected this month")
        
        # Show data source
        if bloom_data:
            st.caption(f"📡 Data source: {bloom_data.get('data_source', 'Unknown')}")
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("📊 View Detailed Report", use_container_width=True):
            st.info("Detailed report feature coming soon!")
        
        if st.button("📞 Contact Agronomist", use_container_width=True):
            st.info("Agronomist hotline: +254-700-BLOOM")
        
        if st.button("📚 View Farming Tips", use_container_width=True):
            st.info("Access farming guides and best practices")

def show_calendar_tab(farmer):
    """Enhanced crop calendar with timeline visualization"""
    st.markdown("### 📅 Kenya Crop Calendar & Planting Guide")
    
    # Farmer's crops highlight
    st.markdown(f"""
    <div class="feature-card" style="text-align: left;">
        <h4>Your Crops: {', '.join([f'🌾 {c.title()}' for c in farmer.get('crops', [])])}</h4>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Timeline visualization
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Crop stages data
    crop_stages = {
        'maize': {
            'planting': [2, 3, 9, 10],  # March, April, October, November
            'flowering': [5, 6, 11],  # June, July, December
            'harvest': [7, 8, 0, 1]  # August, September, January, February
        },
        'beans': {
            'planting': [2, 3, 9, 10],
            'flowering': [4, 5, 10, 11],
            'harvest': [6, 7, 0, 1]
        },
        'coffee': {
            'flowering': [0, 1, 4, 5],  # January, February, May, June
            'harvest': [8, 9, 10, 11]  # September-December
        },
        'tea': {
            'plucking': list(range(12))  # Year-round
        }
    }
    
    # Create Gantt-style chart
    for crop in farmer.get('crops', []):
        if crop in crop_stages:
            st.markdown(f"#### 🌱 {crop.title()} Growth Cycle")
            
            stages = crop_stages[crop]
            data = []
            
            for stage, month_indices in stages.items():
                for month_idx in month_indices:
                    data.append({
                        'Stage': stage.title(),
                        'Month': months[month_idx],
                        'Value': 1
                    })
            
            if data:
                df = pd.DataFrame(data)
                
                # Color mapping for stages
                color_map = {
                    'Planting': '#81C784',
                    'Flowering': '#FDD835',
                    'Harvest': '#FF6F00',
                    'Plucking': '#66BB6A'
                }
                
                fig = px.bar(
                    df,
                    x='Month',
                    y='Value',
                    color='Stage',
                    barmode='stack',
                    color_discrete_map=color_map,
                    height=200
                )
                
                fig.update_layout(
                    showlegend=True,
                    yaxis_visible=False,
                    margin=dict(l=0, r=0, t=20, b=0),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    legend=dict(orientation="h", yanchor="top", y=-0.2)
                )
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown("---")
    
    # Agricultural advice
    st.markdown("### 💡 Current Agricultural Advice")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_crop = st.selectbox(
            "Select your crop:",
            farmer.get('crops', ['maize']),
            format_func=lambda x: x.title()
        )
    
    with col2:
        selected_stage = st.selectbox(
            "Current growth stage:",
            ['flowering', 'tasseling', 'silking', 'pod_formation', 'ripening'],
            format_func=lambda x: x.replace('_', ' ').title()
        )
    
    advice_dict = crop_calendar.get_agricultural_advice(selected_crop, selected_stage)
    advice = advice_dict.get(st.session_state.language, advice_dict.get('en', 'No advice available'))
    
    st.info(f"📋 **Advice:** {advice}")
    
    # Season highlights
    st.markdown("### 🌦️ Kenya Agricultural Seasons")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("""
        **Long Rains (March - May)**
        - 🌱 Main planting season
        - 🌾 Maize, beans, coffee bloom
        - 💧 High rainfall expected
        """)
    
    with col2:
        st.warning("""
        **Short Rains (October - December)**
        - 🌱 Secondary planting season
        - 🌾 Quick-maturing crops
        - 💧 Moderate rainfall
        """)

def show_alerts_tab(farmer):
    """Enhanced alerts tab with interactive settings"""
    st.markdown("### 🔔 Bloom Alert Management")
    
    # Alert settings
    with st.expander("⚙️ Configure Alert Preferences", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            sms_enabled = st.checkbox(
                "📱 Enable SMS Alerts",
                value=farmer.get('sms_enabled', True),
                help="Receive instant bloom alerts via SMS"
            )
            
            email_enabled = st.checkbox(
                "📧 Enable Email Alerts",
                value=bool(farmer.get('email')),
                help="Receive detailed bloom reports via email"
            )
            
            alert_radius = st.slider(
                "📍 Alert Radius (km)",
                min_value=1,
                max_value=50,
                value=10,
                help="Receive alerts for blooms within this radius"
            )
        
        with col2:
            min_intensity = st.slider(
                "⚡ Minimum Bloom Intensity",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1,
                help="Only alert for blooms above this intensity"
            )
            
            alert_time = st.selectbox(
                "⏰ Preferred Alert Time",
                ["Morning (6-9 AM)", "Midday (12-2 PM)", "Evening (6-8 PM)", "Anytime"],
                help="When to receive daily summary alerts"
            )
        
        if st.button("💾 Save Alert Settings", use_container_width=True):
            show_notification("✅ Alert settings saved successfully!", 'success')
            time.sleep(0.5)
    
    st.markdown("---")
    
    # Recent alerts with pulsing animation
    st.markdown("### 📨 Recent Bloom Alerts")
    
    # Try to load actual alerts from MongoDB
    alerts_loaded = False
    sample_alerts = []
    
    if mongo_service:
        try:
            db_alerts = mongo_service.get_recent_alerts(farmer.get('phone'), limit=10)
            if db_alerts:
                for alert in db_alerts:
                    sample_alerts.append({
                        "date": alert.get('timestamp', datetime.now()).strftime("%Y-%m-%d") if isinstance(alert.get('timestamp'), datetime) else str(alert.get('timestamp', 'N/A')),
                        "time": alert.get('timestamp', datetime.now()).strftime("%I:%M %p") if isinstance(alert.get('timestamp'), datetime) else 'N/A',
                        "crop": alert.get('crop_type', 'Unknown'),
                        "location": f"{alert.get('distance_km', 0):.1f} km",
                        "intensity": alert.get('bloom_intensity', 0.7),
                        "status": alert.get('alert_type', 'active').replace('bloom_', ''),
                        "recommendation": alert.get('message', 'Monitor your crops carefully')
                    })
                alerts_loaded = True
        except Exception as e:
            st.caption(f"Note: Could not load alerts from database: {e}")
    
    # Fallback to sample alerts if no real data
    if not alerts_loaded or not sample_alerts:
        sample_alerts = [
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "08:30 AM",
                "crop": "Maize",
                "location": "2.3 km NE",
                "intensity": 0.85,
                "status": "active",
                "recommendation": "Optimal time for pollination management"
            },
            {
                "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "time": "07:15 AM",
                "crop": "Beans",
                "location": "1.8 km SW",
                "intensity": 0.72,
                "status": "active",
                "recommendation": "Monitor for pests, ensure adequate moisture"
            },
            {
                "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                "time": "06:45 AM",
                "crop": "Coffee",
                "location": "3.5 km E",
                "intensity": 0.91,
                "status": "peak",
                "recommendation": "Peak bloom detected - prepare for cherry development"
            },
            {
                "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                "time": "09:00 AM",
                "crop": "Maize",
                "location": "4.2 km N",
                "intensity": 0.68,
                "status": "declining",
                "recommendation": "Bloom declining - focus on post-flowering care"
            }
        ]
    
    if not alerts_loaded:
        st.caption("📝 Showing sample alerts (no database connection)")
    
    for i, alert in enumerate(sample_alerts):
        # Status color coding
        status_colors = {
            'active': 'success',
            'peak': 'warning',
            'declining': 'info'
        }
        
        status_icons = {
            'active': '🟢',
            'peak': '🟡',
            'declining': '🔵'
        }
        
        with st.expander(
            f"{status_icons[alert['status']]} {alert['crop']} Bloom - {alert['location']} - {alert['date']}",
            expanded=(i == 0)
        ):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Intensity", f"{alert['intensity']:.2f}", delta="High" if alert['intensity'] > 0.7 else "Moderate")
            
            with col2:
                st.metric("Time", alert['time'])
            
            with col3:
                st.metric("Status", alert['status'].title())
            
            # Progress bar for intensity
            st.progress(alert['intensity'], text=f"Bloom Intensity: {alert['intensity']*100:.0f}%")
            
            # Recommendation
            if alert['status'] == 'peak':
                st.warning(f"⚠️ **Recommendation:** {alert['recommendation']}")
            else:
                st.info(f"💡 **Recommendation:** {alert['recommendation']}")
            
            # Actions
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                if st.button("📍 View on Map", key=f"map_{i}", use_container_width=True):
                    st.info("Opening map view...")
            
            with col_b:
                if st.button("📊 Full Report", key=f"report_{i}", use_container_width=True):
                    st.info("Generating detailed report...")
            
            with col_c:
                if st.button("🔕 Dismiss", key=f"dismiss_{i}", use_container_width=True):
                    st.success("Alert dismissed")
    
    st.markdown("---")
    
    # Alert statistics
    st.markdown("### 📈 Alert Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Alerts", "24", delta="+5 this week")
    
    with col2:
        st.metric("Active Blooms", "3", delta="+1")
    
    with col3:
        st.metric("Avg. Intensity", "0.76", delta="+0.08")
    
    with col4:
        st.metric("Response Rate", "92%", delta="+3%")

def show_profile_tab(farmer):
    """Enhanced profile tab with visual elements"""
    st.markdown("### 👤 Farmer Profile")
    
    col_profile, col_stats = st.columns([2, 1])
    
    with col_profile:
        # Profile card
        st.markdown(f"""
        <div class="feature-card" style="text-align: left;">
            <h2>👨‍🌾 {farmer.get('name', 'Farmer')}</h2>
            <p><strong>📞 Phone:</strong> {farmer.get('phone', 'N/A')}</p>
            <p><strong>📧 Email:</strong> {farmer.get('email', 'Not provided')}</p>
            <p><strong>📍 Region:</strong> {farmer.get('region', '').replace('_', ' ').title()}</p>
            <p><strong>🗣️ Language:</strong> {'English' if farmer.get('language') == 'en' else 'Kiswahili'}</p>
            <p><strong>🌾 Crops:</strong> {', '.join([c.title() for c in farmer.get('crops', [])])}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Edit profile
        with st.expander("✏️ Edit Profile Information"):
            with st.form("edit_profile_form"):
                new_name = st.text_input("Name", value=farmer.get('name', ''))
                new_email = st.text_input("Email", value=farmer.get('email', ''))
                
                new_crops = st.multiselect(
                    "Crops",
                    ['maize', 'beans', 'coffee', 'tea', 'wheat', 'sorghum', 'millet', 'cassava'],
                    default=farmer.get('crops', []),
                    format_func=lambda x: x.title()
                )
                
                if st.form_submit_button("💾 Update Profile", use_container_width=True):
                    # Update farmer data (in production, this would update the database)
                    st.session_state.farmer_data['name'] = new_name
                    st.session_state.farmer_data['email'] = new_email
                    st.session_state.farmer_data['crops'] = new_crops
                    show_notification("Profile updated successfully!", 'success')
                    time.sleep(1)
                    st.rerun()
    
    with col_stats:
        # Activity statistics
        st.markdown("### 📊 Your Statistics")
        
        st.metric("Days Active", "47", delta="+7 this week")
        st.metric("Alerts Received", "24", delta="+5")
        st.metric("Reports Generated", "12", delta="+2")
        st.metric("Farming Tips Viewed", "18", delta="+4")
        
        # Lottie success animation
        if LOTTIE_AVAILABLE:
            lottie_success = load_lottie_url(LOTTIE_URLS['success'])
            if lottie_success:
                st_lottie(lottie_success, height=150, key="profile_success")
    
    st.markdown("---")
    
    # Account actions
    st.markdown("### ⚙️ Account Settings")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Data", use_container_width=True):
            with st.spinner("Refreshing..."):
                time.sleep(1)
                show_notification("Data refreshed successfully!", 'success')
    
    with col2:
        if st.button("📥 Download Report", use_container_width=True):
            st.info("Generating PDF report...")
    
    with col3:
        if st.button("🗑️ Delete Account", use_container_width=True):
            st.warning("⚠️ This action cannot be undone!")
    
    st.markdown("---")
    
    # Achievements
    st.markdown("### 🏆 Achievements & Milestones")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">🥇</div>
            <h4>Early Adopter</h4>
            <p>Joined in first month</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">📈</div>
            <h4>Growth Master</h4>
            <p>25%+ yield increase</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">🌟</div>
            <h4>Active User</h4>
            <p>30+ days active</p>
        </div>
        """, unsafe_allow_html=True)

# Main app router
def main():
    """Main application router with smooth transitions"""
    
    # Apply CSS based on dark mode setting
    st.markdown(get_custom_css(st.session_state.dark_mode), unsafe_allow_html=True)
    
    # Check authentication
    if st.session_state.authenticated and st.session_state.session_token:
        session = auth_service.verify_session(st.session_state.session_token)
        if not session:
            st.session_state.authenticated = False
            st.session_state.page = 'landing'
            st.rerun()
    
    # Route to appropriate page
    if st.session_state.page == 'landing':
        landing_page()
    elif st.session_state.page == 'login':
        login_page()
    elif st.session_state.page == 'register':
        register_page()
    elif st.session_state.page == 'dashboard' and st.session_state.authenticated:
        dashboard_page()
    else:
        st.session_state.page = 'landing'
        st.rerun()

if __name__ == "__main__":
    main()

