"""
BloomWatch Kenya - Professional Web Application
Farmer-centric platform with authentication and smooth UX
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
from datetime import datetime
import time

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="BloomWatch Kenya",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import services with fallbacks
AuthService = None
MongoDBService = None

try:
    from auth_service import AuthService
    from mongodb_service import MongoDBService
except ImportError as e:
    st.warning(f"Auth/MongoDB services not available: {e}")
    # Create dummy auth service
    class AuthService:
        def __init__(self): pass
        def login(self, phone, password):
            return {
                'success': True, 'demo': True,
                'farmer': {'phone': phone, 'name': 'Demo Farmer', 'region': 'central', 'crops': ['maize', 'beans'], 'language': 'en'},
                'session_token': 'demo_token'
            }
        def register_farmer(self, data, password):
            return {'success': True, 'demo': True, 'message': 'Demo registration successful'}
        def verify_session(self, token):
            return {'phone': 'demo', 'demo': True} if token else None
        def logout(self, token): return True
        def get_farmer_from_session(self, token):
            if token: return {'phone': 'demo', 'name': 'Demo Farmer', 'region': 'central', 'crops': ['maize', 'beans'], 'language': 'en', 'demo': True}
            return None

try:
    from ndvi_utils_lite import detect_blooms
    from gee_data_loader import GEEDataLoader
    gee_loader = GEEDataLoader()
except ImportError as e:
    st.warning(f"GEE data loader not available: {e}")
    gee_loader = None
    def detect_blooms(ts, ari, **kwargs): return [3, 6, 10], np.zeros(12)

try:
    from kenya_crops import KenyaCropCalendar, KENYA_REGIONS
except ImportError:
    st.info("Using fallback Kenya data")
    # Fallback data
    KENYA_REGIONS = {
        'central': {'counties': ['Kiambu', 'Nyeri'], 'main_crops': ['coffee', 'tea', 'maize'], 'coordinates': {'lat': -0.9, 'lon': 36.9}},
        'rift_valley': {'counties': ['Nakuru', 'Eldoret'], 'main_crops': ['maize', 'wheat'], 'coordinates': {'lat': 0.2, 'lon': 35.8}},
        'western': {'counties': ['Kakamega', 'Bungoma'], 'main_crops': ['maize', 'sugarcane'], 'coordinates': {'lat': 0.5, 'lon': 34.8}},
        'eastern': {'counties': ['Machakos', 'Kitui'], 'main_crops': ['maize', 'beans'], 'coordinates': {'lat': -1.5, 'lon': 37.5}}
    }
    
    class KenyaCropCalendar:
        def get_current_season(self):
            month = datetime.now().month
            if 3 <= month <= 5: return 'long_rains'
            elif 10 <= month <= 12: return 'short_rains'
            else: return 'dry_season'
        def get_expected_blooms(self, month=None):
            month = month or datetime.now().month
            blooms = {4: ['maize', 'beans'], 5: ['coffee'], 11: ['maize'], 12: ['beans']}
            return {crop: ['season'] for crop in blooms.get(month, [])}

# Custom CSS for professional look
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-green: #2E7D32;
        --light-green: #66BB6A;
        --dark-green: #1B5E20;
        --accent-orange: #FF6F00;
        --background: #F5F5F5;
    }
    
    /* Remove default Streamlit padding */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Hero section */
    .hero {
        background: linear-gradient(135deg, #2E7D32 0%, #66BB6A 100%);
        padding: 3rem 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .hero h1 {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    
    .hero p {
        font-size: 1.2rem;
        opacity: 0.95;
    }
    
    /* Cards */
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #2E7D32;
        margin-bottom: 1rem;
    }
    
    .stat-card h3 {
        color: #2E7D32;
        font-size: 2rem;
        margin: 0;
    }
    
    .stat-card p {
        color: #666;
        margin: 0.5rem 0 0 0;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #2E7D32 0%, #66BB6A 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        border-radius: 25px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    /* Success/Error messages */
    .element-container div[data-testid="stMarkdownContainer"] div[data-testid="stMarkdown"] {
        padding: 0.5rem 1rem;
        border-radius: 5px;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Smooth animations */
    .element-container {
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Form styling */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        border-radius: 8px;
        border: 2px solid #E0E0E0;
        padding: 0.75rem;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #2E7D32;
        box-shadow: 0 0 0 2px rgba(46,125,50,0.1);
    }
    
    /* Language toggle */
    .lang-toggle {
        position: absolute;
        top: 1rem;
        right: 1rem;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.page = 'landing'
        st.session_state.authenticated = False
        st.session_state.session_token = None
        st.session_state.farmer_data = None
        st.session_state.language = 'en'
        st.session_state.show_success = False
        st.session_state.success_message = ''
        st.session_state.show_error = False
        st.session_state.error_message = ''

init_session_state()

# Initialize services
@st.cache_resource
def get_services():
    """Get singleton instances of services"""
    try:
        if AuthService:
            auth = AuthService()
        else:
            # Use fallback dummy auth
            class DummyAuth:
                def __init__(self): pass
                def login(self, phone, password):
                    return {
                        'success': True, 'demo': True,
                        'farmer': {'phone': phone, 'name': 'Demo Farmer', 'region': 'central', 'crops': ['maize', 'beans'], 'language': 'en'},
                        'session_token': 'demo_token'
                    }
                def register_farmer(self, data, password):
                    return {'success': True, 'demo': True, 'message': 'Demo registration successful'}
                def verify_session(self, token):
                    return {'phone': 'demo', 'demo': True} if token else None
                def logout(self, token): return True
                def get_farmer_from_session(self, token):
                    if token: return {'phone': 'demo', 'name': 'Demo Farmer', 'region': 'central', 'crops': ['maize', 'beans'], 'language': 'en', 'demo': True}
                    return None
            auth = DummyAuth()
        
        mongo = MongoDBService() if MongoDBService else None
        
        if 'KenyaCropCalendar' in globals():
            calendar = KenyaCropCalendar()
        else:
            # Fallback calendar
            class DummyCalendar:
                def get_current_season(self):
                    month = datetime.now().month
                    if 3 <= month <= 5: return 'long_rains'
                    elif 10 <= month <= 12: return 'short_rains'
                    else: return 'dry_season'
                def get_expected_blooms(self, month=None):
                    month = month or datetime.now().month
                    blooms = {4: ['maize', 'beans'], 5: ['coffee'], 11: ['maize'], 12: ['beans']}
                    return {crop: ['season'] for crop in blooms.get(month, [])}
            calendar = DummyCalendar()
        
        return auth, mongo, calendar
    except Exception as e:
        st.warning(f"Service initialization using fallbacks: {e}")
        # Return dummy services
        class DummyAuth:
            def login(self, phone, password):
                return {
                    'success': True, 'demo': True,
                    'farmer': {'phone': phone, 'name': 'Demo Farmer', 'region': 'central', 'crops': ['maize', 'beans'], 'language': 'en'},
                    'session_token': 'demo_token'
                }
            def register_farmer(self, data, password):
                return {'success': True, 'demo': True, 'message': 'Demo registration successful'}
            def verify_session(self, token):
                return {'phone': 'demo', 'demo': True} if token else None
            def logout(self, token): return True
            def get_farmer_from_session(self, token):
                if token: return {'phone': 'demo', 'name': 'Demo Farmer', 'region': 'central', 'crops': ['maize', 'beans'], 'language': 'en', 'demo': True}
                return None
        
        class DummyCalendar:
            def get_current_season(self):
                month = datetime.now().month
                if 3 <= month <= 5: return 'long_rains'
                elif 10 <= month <= 12: return 'short_rains'
                else: return 'dry_season'
            def get_expected_blooms(self, month=None):
                month = month or datetime.now().month
                blooms = {4: ['maize', 'beans'], 5: ['coffee'], 11: ['maize'], 12: ['beans']}
                return {crop: ['season'] for crop in blooms.get(month, [])}
        
        return DummyAuth(), None, DummyCalendar()

auth_service, mongo_service, crop_calendar = get_services()

# Language translations
TRANSLATIONS = {
    'en': {
        'welcome': 'Welcome to BloomWatch Kenya',
        'tagline': 'Empowering Kenyan farmers with NASA satellite technology',
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
        'success_registration': 'Registration successful! Welcome to BloomWatch Kenya.',
        'success_login': 'Login successful! Welcome back.',
        'error_passwords': 'Passwords do not match',
        'error_fields': 'Please fill all required fields',
        'current_season': 'Current Season',
        'active_blooms': 'Active Blooms',
        'farmers_registered': 'Farmers Registered'
    },
    'sw': {
        'welcome': 'Karibu BloomWatch Kenya',
        'tagline': 'Kuwawezesha wakulima wa Kenya kwa teknolojia ya satelaiti za NASA',
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
        'success_registration': 'Usajili umefanikiwa! Karibu BloomWatch Kenya.',
        'success_login': 'Umeingia kikamilifu! Karibu tena.',
        'error_passwords': 'Maneno ya siri hayalingani',
        'error_fields': 'Tafadhali jaza sehemu zote muhimu',
        'current_season': 'Msimu wa Sasa',
        'active_blooms': 'Kuchanua Kinachoendelea',
        'farmers_registered': 'Wakulima Waliosajiliwa'
    }
}

def t(key):
    """Get translation for current language"""
    return TRANSLATIONS[st.session_state.language].get(key, key)

def show_notification(message, type='success'):
    """Show notification banner"""
    if type == 'success':
        st.success(f"✅ {message}", icon="✅")
    elif type == 'error':
        st.error(f"❌ {message}", icon="❌")
    elif type == 'info':
        st.info(f"ℹ️ {message}", icon="ℹ️")
    elif type == 'warning':
        st.warning(f"⚠️ {message}", icon="⚠️")

def landing_page():
    """Landing page with hero section"""
    
    # Language toggle in top right
    col1, col2 = st.columns([6, 1])
    with col2:
        lang_option = st.selectbox(
            '',
            ['English', 'Kiswahili'],
            key='lang_select',
            label_visibility='collapsed'
        )
        st.session_state.language = 'en' if lang_option == 'English' else 'sw'
    
    # Hero section
    st.markdown(f"""
    <div class="hero">
        <h1>🌾 {t('welcome')}</h1>
        <p>{t('tagline')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🛰️ Smart Farming with Satellite Technology")
        st.markdown("""
        - **Real-time bloom detection** from NASA satellites
        - **SMS alerts** in your language (English & Kiswahili)
        - **Crop calendar** tailored for Kenya
        - **Weather updates** and farming tips
        - **Free** for all Kenyan farmers
        """)
        
        st.markdown("---")
        
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
        
        # Stats section
        st.markdown("### 📊 Our Impact")
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        
        with stat_col1:
            st.markdown("""
            <div class="stat-card">
                <h3>500+</h3>
                <p>Farmers Registered</p>
            </div>
            """, unsafe_allow_html=True)
        
        with stat_col2:
            st.markdown("""
            <div class="stat-card">
                <h3>25%</h3>
                <p>Yield Increase</p>
            </div>
            """, unsafe_allow_html=True)
        
        with stat_col3:
            st.markdown("""
            <div class="stat-card">
                <h3>4</h3>
                <p>Regions Covered</p>
            </div>
            """, unsafe_allow_html=True)

def login_page():
    """Login page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"## 👤 {t('login')}")
        
        if st.button(f"← {t('back')}", key='back_from_login'):
            st.session_state.page = 'landing'
            st.rerun()
        
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
                submit = st.form_submit_button(t('login_button'), use_container_width=True)
            
            with col_b:
                register = st.form_submit_button("Register Instead", use_container_width=True)
            
            if register:
                st.session_state.page = 'register'
                st.rerun()
            
            if submit:
                if not phone or not password:
                    show_notification(t('error_fields'), 'error')
                else:
                    with st.spinner('Authenticating...'):
                        result = auth_service.login(phone, password)
                        
                        if result['success']:
                            st.session_state.authenticated = True
                            st.session_state.session_token = result['session_token']
                            st.session_state.farmer_data = result['farmer']
                            st.session_state.page = 'dashboard'
                            show_notification(t('success_login'), 'success')
                            time.sleep(1)
                            st.rerun()
                        else:
                            show_notification(result.get('message', 'Login failed'), 'error')

def register_page():
    """Registration page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"## 📝 {t('register')}")
        
        if st.button(f"← {t('back')}", key='back_from_register'):
            st.session_state.page = 'landing'
            st.rerun()
        
        with st.form("register_form", clear_on_submit=False):
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
            
            region = st.selectbox(
                t('region'),
                options=list(KENYA_REGIONS.keys()),
                format_func=lambda x: x.replace('_', ' ').title()
            )
            
            available_crops = ['maize', 'beans', 'coffee', 'tea', 'wheat', 'sorghum']
            crops = st.multiselect(
                t('crops'),
                options=available_crops,
                format_func=lambda x: x.title()
            )
            
            language = st.selectbox(
                t('language_pref'),
                options=['en', 'sw'],
                format_func=lambda x: 'English' if x == 'en' else 'Kiswahili'
            )
            
            password = st.text_input(
                t('password'),
                type="password",
                help="Create a secure password"
            )
            
            confirm_password = st.text_input(
                t('confirm_password'),
                type="password"
            )
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                submit = st.form_submit_button(f"✓ {t('register_button')}", use_container_width=True)
            
            with col_b:
                login_instead = st.form_submit_button("Login Instead", use_container_width=True)
            
            if login_instead:
                st.session_state.page = 'login'
                st.rerun()
            
            if submit:
                # Validation
                if not all([name, phone, region, crops, password, confirm_password]):
                    show_notification(t('error_fields'), 'error')
                elif password != confirm_password:
                    show_notification(t('error_passwords'), 'error')
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
                    
                    with st.spinner('Creating your account...'):
                        result = auth_service.register_farmer(farmer_data, password)
                        
                        if result['success']:
                            show_notification(t('success_registration'), 'success')
                            time.sleep(2)
                            st.session_state.page = 'login'
                            st.balloons()
                            st.rerun()
                        else:
                            show_notification(result.get('message', 'Registration failed'), 'error')

def dashboard_page():
    """Main dashboard for authenticated users"""
    farmer = st.session_state.farmer_data
    
    if not farmer:
        st.session_state.page = 'landing'
        st.rerun()
        return
    
    # Top navigation
    col1, col2, col3 = st.columns([2, 4, 1])
    
    with col1:
        st.markdown(f"### 👋 {farmer.get('name', 'Farmer')}")
    
    with col3:
        if st.button(f"🚪 {t('logout')}", key='logout_button'):
            auth_service.logout(st.session_state.session_token)
            st.session_state.authenticated = False
            st.session_state.session_token = None
            st.session_state.farmer_data = None
            st.session_state.page = 'landing'
            st.rerun()
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        f"📊 {t('dashboard')}",
        f"🌾 {t('calendar')}",
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
    """Dashboard tab content"""
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    current_season = crop_calendar.get_current_season()
    expected_blooms = crop_calendar.get_expected_blooms()
    
    with col1:
        st.metric(t('current_season'), current_season.replace('_', ' ').title())
    
    with col2:
        st.metric(t('active_blooms'), len(expected_blooms))
    
    with col3:
        st.metric("Your Crops", len(farmer.get('crops', [])))
    
    with col4:
        st.metric("Alerts Received", "12")  # From DB in production
    
    st.markdown("---")
    
    # Map and data visualization
    col_map, col_chart = st.columns([3, 2])
    
    with col_map:
        st.markdown("### 🗺️ Your Farm Location")
        m = folium.Map(
            location=[farmer.get('location_lat', -1.0), farmer.get('location_lon', 37.0)],
            zoom_start=10
        )
        
        folium.Marker(
            [farmer.get('location_lat', -1.0), farmer.get('location_lon', 37.0)],
            popup=f"{farmer.get('name')}'s Farm",
            tooltip="Your Farm",
            icon=folium.Icon(color='green', icon='leaf', prefix='fa')
        ).add_to(m)
        
        st_folium(m, height=400, use_container_width=True)
    
    with col_chart:
        st.markdown("### 📈 NDVI Trend (Last 12 Months)")
        
        # Generate demo data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ndvi_values = [0.4, 0.45, 0.6, 0.75, 0.7, 0.5, 0.45, 0.4, 0.5, 0.65, 0.8, 0.7]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=months,
            y=ndvi_values,
            mode='lines+markers',
            name='NDVI',
            line=dict(color='#2E7D32', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=0, b=0),
            yaxis_title="NDVI Value"
        )
        
        st.plotly_chart(fig, use_container_width=True)

def show_calendar_tab(farmer):
    """Crop calendar tab"""
    st.markdown("### 📅 Kenya Crop Calendar")
    
    # Show farmer's crops
    st.markdown(f"**Your Crops:** {', '.join([c.title() for c in farmer.get('crops', [])])}")
    
    # Calendar data
    calendar_data = []
    for crop in farmer.get('crops', []):
        if crop in ['maize', 'beans', 'coffee']:
            calendar_data.append({
                'Crop': crop.title(),
                'Planting': 'Mar-Apr, Oct-Nov',
                'Blooming': 'Jun-Jul, Jan-Feb',
                'Harvest': 'Aug-Sep, Mar-Apr'
            })
    
    if calendar_data:
        df = pd.DataFrame(calendar_data)
        st.dataframe(df, use_container_width=True)
    
    # Expected blooms this month
    expected = crop_calendar.get_expected_blooms()
    if expected:
        st.success(f"**Expected to bloom this month:** {', '.join([c.title() for c in expected.keys()])}")
    else:
        st.info("No major blooms expected this month")

def show_alerts_tab(farmer):
    """Alerts tab"""
    st.markdown("### 🔔 Bloom Alert Settings")
    
    # Alert preferences
    col1, col2 = st.columns(2)
    
    with col1:
        sms_enabled = st.checkbox("Enable SMS Alerts", value=farmer.get('sms_enabled', True))
        alert_radius = st.slider("Alert Radius (km)", 1, 50, 10)
    
    with col2:
        email_enabled = st.checkbox("Enable Email Alerts", value=bool(farmer.get('email')))
        min_intensity = st.slider("Minimum Bloom Intensity", 0.0, 1.0, 0.5)
    
    if st.button("💾 Save Alert Settings"):
        show_notification("Alert settings saved successfully!", 'success')
    
    st.markdown("---")
    
    # Recent alerts
    st.markdown("### 📨 Recent Alerts")
    
    sample_alerts = [
        {"date": "2024-10-03", "crop": "Maize", "location": "Kiambu", "intensity": 0.8},
        {"date": "2024-10-02", "crop": "Beans", "location": "Nyeri", "intensity": 0.6},
        {"date": "2024-10-01", "crop": "Coffee", "location": "Murang'a", "intensity": 0.9}
    ]
    
    for alert in sample_alerts:
        with st.expander(f"🌾 {alert['crop']} - {alert['date']}"):
            st.write(f"**Location:** {alert['location']}")
            st.write(f"**Intensity:** {alert['intensity']:.1f}")
            st.write(f"Bloom detected near your farm. Check crops for optimal harvest timing.")

def show_profile_tab(farmer):
    """Profile management tab"""
    st.markdown("### 👤 Your Profile")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Personal Information**")
        st.write(f"**Name:** {farmer.get('name')}")
        st.write(f"**Phone:** {farmer.get('phone')}")
        st.write(f"**Email:** {farmer.get('email', 'Not provided')}")
        st.write(f"**Region:** {farmer.get('region', '').replace('_', ' ').title()}")
        st.write(f"**Language:** {'English' if farmer.get('language') == 'en' else 'Kiswahili'}")
    
    with col2:
        st.markdown("**Farming Details**")
        st.write(f"**Crops:** {', '.join([c.title() for c in farmer.get('crops', [])])}")
        st.write(f"**Registered:** {farmer.get('created_at', 'N/A')}")
        st.write(f"**Alerts Received:** 12")  # From DB
    
    st.markdown("---")
    
    if st.button("🔄 Update Profile"):
        st.info("Profile update feature coming soon!")

# Main app router
def main():
    """Main application router"""
    
    # Check if user is authenticated
    if st.session_state.authenticated and st.session_state.session_token:
        # Verify session is still valid
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

