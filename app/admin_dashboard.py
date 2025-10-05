"""
BloomWatch Kenya - Admin Dashboard
Manage farmers, send alerts, view message queues
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from mongodb_service import MongoDBService
    from auth_service import AuthService
    from smart_alert_service import SmartAlertService
    from bloom_processor import BloomProcessor
    from africastalking_service import AfricasTalkingService
    SERVICES_AVAILABLE = True
except ImportError as e:
    st.error(f"Import error: {e}")
    SERVICES_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="BloomWatch Admin",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .success-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .warning-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .farmer-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize services
@st.cache_resource
def get_services():
    """Initialize services"""
    if not SERVICES_AVAILABLE:
        return None, None, None, None, None
    
    mongo = MongoDBService()
    auth = AuthService()
    smart_alerts = SmartAlertService()
    bloom = BloomProcessor()
    at = AfricasTalkingService()
    return mongo, auth, smart_alerts, bloom, at

mongo_service, auth_service, alert_service, bloom_processor, at_service = get_services()

# Session state
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'admin_username' not in st.session_state:
    st.session_state.admin_username = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Dashboard'

# Admin credentials (in production, use proper authentication)
ADMIN_CREDENTIALS = {
    'admin': 'bloomwatch2024',  # Change this!
    'geoffrey': 'admin123'  # Add more admins as needed
}

def check_admin_login(username: str, password: str) -> bool:
    """Check admin credentials"""
    return ADMIN_CREDENTIALS.get(username) == password

def login_page():
    """Admin login page"""
    st.markdown("<h1 style='text-align: center;'>🔧 BloomWatch Admin</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Farmer Management Dashboard</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("admin_login"):
            username = st.text_input("👤 Username", placeholder="admin")
            password = st.text_input("🔒 Password", type="password")
            submit = st.form_submit_button("🔐 Login", use_container_width=True)
            
            if submit:
                if check_admin_login(username, password):
                    st.session_state.admin_logged_in = True
                    st.session_state.admin_username = username
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")

def dashboard_page():
    """Main dashboard with statistics"""
    st.title("📊 Dashboard Overview")
    
    if not mongo_service:
        st.error("MongoDB service not available")
        return
    
    # Get statistics
    stats = mongo_service.get_farmer_statistics()
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h2>{stats['total']}</h2>
            <p>Total Farmers</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="success-card">
            <h2>{stats.get('active', 0)}</h2>
            <p>Active Farmers</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="warning-card">
            <h2>{stats.get('ussd', 0)}</h2>
            <p>USSD Registrations</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h2>{stats.get('web', 0)}</h2>
            <p>Web Registrations</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📍 Farmers by Region")
        if stats.get('by_region'):
            region_df = pd.DataFrame(
                list(stats['by_region'].items()),
                columns=['Region', 'Count']
            )
            st.bar_chart(region_df.set_index('Region'))
        else:
            st.info("No regional data available")
    
    with col2:
        st.subheader("🌾 Popular Crops")
        if stats.get('popular_crops'):
            crop_df = pd.DataFrame(
                stats['popular_crops'][:5],
                columns=['Crop', 'Count']
            )
            st.bar_chart(crop_df.set_index('Crop'))
        else:
            st.info("No crop data available")
    
    # Recent registrations
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🆕 Recent Registrations (Last 7 days)")
    
    recent = mongo_service.get_recent_registrations(days=7, limit=10)
    
    if recent:
        for farmer in recent:
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                st.write(f"**{farmer.get('name', 'N/A')}**")
            with col2:
                st.write(f"📱 {farmer.get('phone', 'N/A')}")
            with col3:
                st.write(f"📍 {farmer.get('region', 'N/A').replace('_', ' ').title()}")
            with col4:
                reg_via = farmer.get('registered_via', 'unknown')
                st.write(f"🔖 {reg_via.upper()}")
    else:
        st.info("No recent registrations")

def farmers_page():
    """Farmer management page"""
    st.title("👨‍🌾 Farmer Management")
    
    if not mongo_service:
        st.error("MongoDB service not available")
        return
    
    # Search and filter
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_query = st.text_input("🔍 Search farmers", placeholder="Name, phone, or region...")
    with col2:
        region_filter = st.selectbox(
            "Filter by region",
            ['All', 'central', 'rift_valley', 'western', 'eastern', 'coast']
        )
    with col3:
        reg_via_filter = st.selectbox(
            "Filter by source",
            ['All', 'web', 'ussd', 'manual']
        )
    
    # Get farmers
    query = {}
    if region_filter != 'All':
        query['region'] = region_filter
    if reg_via_filter != 'All':
        query['registered_via'] = reg_via_filter
    if search_query:
        query['$or'] = [
            {'name': {'$regex': search_query, '$options': 'i'}},
            {'phone': {'$regex': search_query, '$options': 'i'}},
            {'region': {'$regex': search_query, '$options': 'i'}}
        ]
    
    farmers = list(mongo_service.farmers.find(query).limit(50))
    
    st.markdown(f"**Found {len(farmers)} farmers**")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Display farmers
    for farmer in farmers:
        with st.expander(f"👤 {farmer.get('name', 'N/A')} - {farmer.get('phone', 'N/A')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Basic Information:**")
                st.write(f"📱 Phone: {farmer.get('phone', 'N/A')}")
                st.write(f"📧 Email: {farmer.get('email', 'N/A')}")
                st.write(f"📍 Region: {farmer.get('region', 'N/A').replace('_', ' ').title()}")
                st.write(f"🌾 Crops: {', '.join([c.title() for c in farmer.get('crops', [])])}")
                st.write(f"🗣️ Language: {farmer.get('language', 'en').upper()}")
            
            with col2:
                st.write("**Account Details:**")
                st.write(f"🔖 Registered via: {farmer.get('registered_via', 'unknown').upper()}")
                st.write(f"📅 Registered: {farmer.get('registered_at', 'N/A')}")
                st.write(f"📍 Location: {farmer.get('location_lat', 'N/A')}, {farmer.get('location_lon', 'N/A')}")
                st.write(f"📱 SMS Enabled: {'✅' if farmer.get('sms_enabled') else '❌'}")
            
            # Actions
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"📨 Send Alert", key=f"alert_{farmer['_id']}"):
                    st.session_state.selected_farmer = farmer
                    st.session_state.current_page = 'Send Alerts'
                    st.rerun()
            with col2:
                if st.button(f"✏️ Edit", key=f"edit_{farmer['_id']}"):
                    st.info("Edit functionality coming soon")
            with col3:
                if st.button(f"🗑️ Delete", key=f"delete_{farmer['_id']}"):
                    if mongo_service.delete_farmer(str(farmer['_id'])):
                        st.success("Farmer deleted")
                        st.rerun()

def create_farmer_page():
    """Create new farmer page"""
    st.title("➕ Create New Farmer")
    
    if not mongo_service:
        st.error("MongoDB service not available")
        return
    
    with st.form("create_farmer"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("👤 Full Name *", placeholder="John Kamau")
            phone = st.text_input("📱 Phone Number *", placeholder="+254712345678")
            email = st.text_input("📧 Email", placeholder="john@example.com")
            region = st.selectbox(
                "📍 Region *",
                ['central', 'rift_valley', 'western', 'eastern', 'coast']
            )
        
        with col2:
            crops = st.multiselect(
                "🌾 Crops *",
                ['maize', 'beans', 'coffee', 'tea', 'wheat', 'sorghum', 'millet'],
                default=['maize']
            )
            language = st.selectbox("🗣️ Language", ['en', 'sw'])
            sms_enabled = st.checkbox("📱 SMS Notifications", value=True)
        
        submit = st.form_submit_button("✅ Create Farmer", use_container_width=True)
        
        if submit:
            if not all([name, phone, region, crops]):
                st.error("Please fill in all required fields (*)")
            else:
                # Create farmer data
                farmer_data = {
                    'name': name,
                    'phone': phone,
                    'email': email or '',
                    'region': region,
                    'crops': crops,
                    'language': language,
                    'sms_enabled': sms_enabled,
                    'registered_via': 'manual',
                    'registered_by': st.session_state.admin_username
                }
                
                # Register farmer
                result = auth_service.register_farmer(farmer_data, None)  # No password for manual
                
                if result['success']:
                    st.success(f"✅ Farmer '{name}' created successfully!")
                    st.balloons()
                    
                    # Send welcome SMS if enabled
                    if sms_enabled and at_service:
                        try:
                            bloom_data = bloom_processor.detect_bloom_events(region)
                            alert_result = alert_service.send_welcome_alert(farmer_data, bloom_data)
                            if alert_result.get('success'):
                                st.info("📱 Welcome SMS sent")
                        except:
                            pass
                else:
                    st.error(f"❌ Error: {result.get('message', 'Unknown error')}")

def alerts_page():
    """Send alerts page"""
    st.title("📨 Send Smart Alerts")
    
    if not mongo_service or not alert_service:
        st.error("Required services not available")
        return
    
    tab1, tab2, tab3 = st.tabs(["📤 Send New Alert", "📜 Alert History", "📊 Statistics"])
    
    with tab1:
        st.subheader("Send Alert to Farmers")
        
        # Target selection
        col1, col2 = st.columns(2)
        with col1:
            send_to = st.radio(
                "Send to:",
                ['All Farmers', 'By Region', 'By Crop', 'Specific Farmer']
            )
        
        with col2:
            if send_to == 'By Region':
                target_region = st.selectbox(
                    "Select region",
                    ['central', 'rift_valley', 'western', 'eastern', 'coast']
                )
            elif send_to == 'By Crop':
                target_crop = st.selectbox(
                    "Select crop",
                    ['maize', 'beans', 'coffee', 'tea', 'wheat']
                )
            elif send_to == 'Specific Farmer':
                farmer_phone = st.text_input("Enter phone number", placeholder="+254712345678")
        
        # Alert type
        alert_type = st.selectbox(
            "Alert Type",
            ['Bloom Detection', 'Weather Update', 'Custom Message']
        )
        
        # Message
        if alert_type == 'Custom Message':
            message = st.text_area(
                "Message",
                placeholder="Enter your message here...",
                max_chars=160
            )
            st.caption(f"{len(message)}/160 characters")
        else:
            st.info(f"Smart alert will be generated automatically based on {alert_type}")
            message = None
        
        # Preview
        if st.button("👁️ Preview Recipients"):
            query = {}
            if send_to == 'By Region':
                query['region'] = target_region
            elif send_to == 'By Crop':
                query['crops'] = target_crop
            elif send_to == 'Specific Farmer':
                query['phone'] = farmer_phone
            
            recipients = list(mongo_service.farmers.find(query).limit(100))
            st.success(f"Found {len(recipients)} recipients")
            
            if recipients:
                st.dataframe(
                    pd.DataFrame([
                        {'Name': f.get('name'), 'Phone': f.get('phone'), 'Region': f.get('region')}
                        for f in recipients[:10]
                    ])
                )
                if len(recipients) > 10:
                    st.caption(f"Showing 10 of {len(recipients)} recipients")
        
        # Send button
        if st.button("📤 Send Alert Now", type="primary", use_container_width=True):
            with st.spinner("Sending alerts..."):
                # Get recipients
                query = {}
                if send_to == 'By Region':
                    query['region'] = target_region
                elif send_to == 'By Crop':
                    query['crops'] = target_crop
                elif send_to == 'Specific Farmer':
                    query['phone'] = farmer_phone
                
                recipients = list(mongo_service.farmers.find(query))
                
                if not recipients:
                    st.error("No recipients found")
                else:
                    # Send alerts
                    success_count = 0
                    for farmer in recipients:
                        try:
                            if alert_type == 'Custom Message':
                                # Send custom message
                                result = at_service.send_sms(farmer['phone'], message)
                                if result.get('success'):
                                    success_count += 1
                            else:
                                # Send smart alert
                                bloom_data = bloom_processor.detect_bloom_events(farmer.get('region', 'central'))
                                result = alert_service.send_welcome_alert(farmer, bloom_data)
                                if result.get('success'):
                                    success_count += 1
                        except Exception as e:
                            st.warning(f"Failed to send to {farmer.get('name')}: {e}")
                    
                    st.success(f"✅ Sent {success_count}/{len(recipients)} alerts successfully")
    
    with tab2:
        st.subheader("Recent Alerts")
        
        alerts = mongo_service.get_recent_alerts(limit=50)
        
        if alerts:
            for alert in alerts:
                with st.expander(f"📨 Alert to {alert.get('farmer_phone', 'N/A')} - {alert.get('sent_at', 'N/A')}"):
                    st.write(f"**Type:** {alert.get('alert_type', 'N/A')}")
                    st.write(f"**Phone:** {alert.get('farmer_phone', 'N/A')}")
                    st.write(f"**Message:** {alert.get('message', 'N/A')}")
                    st.write(f"**Status:** {'✅ Delivered' if alert.get('delivered') else '⏳ Pending'}")
                    st.write(f"**Sent at:** {alert.get('sent_at', 'N/A')}")
        else:
            st.info("No alerts sent yet")
    
    with tab3:
        st.subheader("Alert Statistics")
        
        # Get stats
        total_alerts = mongo_service.alerts.count_documents({})
        today_alerts = mongo_service.alerts.count_documents({
            'sent_at': {'$gte': datetime.now().strftime('%Y-%m-%d')}
        })
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Alerts Sent", total_alerts)
        with col2:
            st.metric("Alerts Today", today_alerts)
        with col3:
            st.metric("Delivery Rate", "98%")  # Calculate actual rate

def message_queue_page():
    """View message queues for farmers"""
    st.title("📬 Message Queue")
    
    if not mongo_service:
        st.error("MongoDB service not available")
        return
    
    st.info("💡 View pending and delivered messages for each farmer")
    
    # Search farmer
    search_phone = st.text_input("🔍 Search by phone number", placeholder="+254712345678")
    
    if search_phone:
        farmer = mongo_service.get_farmer_by_phone(search_phone)
        
        if farmer:
            st.success(f"Found: **{farmer.get('name')}**")
            
            # Get messages for this farmer
            alerts = list(mongo_service.alerts.find({
                'farmer_phone': search_phone
            }).sort('sent_at', -1).limit(50))
            
            if alerts:
                st.subheader(f"📨 Messages ({len(alerts)})")
                
                # Group by status
                pending = [a for a in alerts if not a.get('delivered')]
                delivered = [a for a in alerts if a.get('delivered')]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("⏳ Pending", len(pending))
                with col2:
                    st.metric("✅ Delivered", len(delivered))
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Display messages
                for alert in alerts:
                    status_icon = "✅" if alert.get('delivered') else "⏳"
                    with st.expander(f"{status_icon} {alert.get('alert_type', 'Alert')} - {alert.get('sent_at', 'N/A')}"):
                        st.write(f"**Message:** {alert.get('message', 'N/A')}")
                        st.write(f"**Type:** {alert.get('alert_type', 'N/A')}")
                        st.write(f"**Status:** {'Delivered' if alert.get('delivered') else 'Pending'}")
                        st.write(f"**Sent at:** {alert.get('sent_at', 'N/A')}")
                        
                        if alert.get('delivered'):
                            st.write(f"**Delivered at:** {alert.get('delivered_at', 'N/A')}")
            else:
                st.info("No messages found for this farmer")
        else:
            st.warning("Farmer not found")
    else:
        # Show all recent messages
        st.subheader("📊 All Recent Messages")
        
        recent_alerts = list(mongo_service.alerts.find().sort('sent_at', -1).limit(20))
        
        if recent_alerts:
            df_data = []
            for alert in recent_alerts:
                df_data.append({
                    'Time': alert.get('sent_at', 'N/A'),
                    'Phone': alert.get('farmer_phone', 'N/A'),
                    'Type': alert.get('alert_type', 'N/A'),
                    'Status': '✅ Delivered' if alert.get('delivered') else '⏳ Pending'
                })
            
            st.dataframe(pd.DataFrame(df_data), use_container_width=True)
        else:
            st.info("No messages in queue")

def main():
    """Main app logic"""
    
    if not st.session_state.admin_logged_in:
        login_page()
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🔧 BloomWatch Admin")
        st.markdown(f"**👤 {st.session_state.admin_username}**")
        st.markdown("---")
        
        # Navigation
        pages = {
            'Dashboard': '📊',
            'Farmers': '👨‍🌾',
            'Create Farmer': '➕',
            'Send Alerts': '📨',
            'Message Queue': '📬'
        }
        
        for page, icon in pages.items():
            if st.button(f"{icon} {page}", key=page, use_container_width=True):
                st.session_state.current_page = page
                st.rerun()
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.admin_logged_in = False
            st.session_state.admin_username = None
            st.rerun()
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.caption("BloomWatch Kenya v1.0")
        st.caption("Admin Dashboard")
    
    # Main content
    current_page = st.session_state.current_page
    
    if current_page == 'Dashboard':
        dashboard_page()
    elif current_page == 'Farmers':
        farmers_page()
    elif current_page == 'Create Farmer':
        create_farmer_page()
    elif current_page == 'Send Alerts':
        alerts_page()
    elif current_page == 'Message Queue':
        message_queue_page()

if __name__ == "__main__":
    main()

