"""
Real Data Integration for Streamlit App
Drop-in replacement functions that use real satellite data

Usage:
    from streamlit_realdata_integration import show_kenya_climate_map_real, show_farmer_dashboard_map_real
"""

import sys
import os
import folium
import streamlit as st
from streamlit_folium import st_folium
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from streamlit_data_loader import StreamlitDataLoader
    DATA_LOADER_AVAILABLE = True
except ImportError:
    DATA_LOADER_AVAILABLE = False
    st.warning("⚠️ Real data loader not available. Using fallback mode.")


def show_kenya_climate_map_real():
    """
    Enhanced Kenya map with REAL satellite data from all 47 counties
    Drop-in replacement for show_kenya_climate_map()
    """
    st.markdown("<div class='scroll-animate'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #2E7D32; font-size: 2.5rem;'>🗺️ Kenya Live Climate & Bloom Data</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'><b>Real-time agricultural insights powered by NASA satellite technology</b></p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Load real data
    if DATA_LOADER_AVAILABLE:
        loader = StreamlitDataLoader()
        map_data = loader.get_landing_page_map_data()
        freshness = loader.get_data_freshness_info()
        climate_stats = loader.get_climate_summary_stats()
        
        # Show data freshness indicator
        if freshness['is_fresh']:
            st.success(f"✅ Live satellite data | Last updated: {freshness['age_str']}")
        else:
            st.warning(f"⚠️ {freshness['message']} | Last updated: {freshness['age_str']}")
        
        markers = map_data['markers']
        has_real_data = map_data['has_real_data']
    else:
        # Fallback to demo data
        markers = []
        has_real_data = False
        climate_stats = {
            'avg_bloom_level': "N/A",
            'avg_temperature': "N/A",
            'avg_rainfall': "N/A",
            'total_bloom_area': "N/A"
        }
    
    # Create comprehensive Kenya map
    m = folium.Map(
        location=[-0.5, 37.0],
        zoom_start=6,
        tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
        attr='CartoDB',
        scrollWheelZoom=False
    )
    
    # Add markers for each county
    for marker in markers:
        # Parse bloom probability
        try:
            bloom_pct = int(marker['bloom_probability'].rstrip('%'))
        except:
            bloom_pct = 0
        
        # Color code by bloom intensity
        if bloom_pct >= 70:
            color = 'darkgreen'
            icon_color = 'green'
        elif bloom_pct >= 40:
            color = 'orange'
            icon_color = 'orange'
        else:
            color = 'red'
            icon_color = 'red'
        
        # Data source badge
        source_badge = "🛰️ NASA" if marker['is_real_data'] else "📊 Demo"
        
        popup_html = f"""
        <div style="font-family: Arial; min-width: 250px;">
            <h4 style="margin: 0 0 10px 0; color: #2E7D32;">{marker['name']}</h4>
            <p style="margin: 5px 0; font-size: 11px; color: #666;">{source_badge}</p>
            <hr style="margin: 8px 0; border: none; border-top: 1px solid #ddd;">
            <p style="margin: 5px 0;"><b>🌸 Bloom Probability:</b> {marker['bloom_probability']}</p>
            <p style="margin: 5px 0;"><b>🌱 NDVI:</b> {marker['ndvi']}</p>
            <p style="margin: 5px 0;"><b>🌡️ Temperature:</b> {marker['temperature']}</p>
            <p style="margin: 5px 0;"><b>🌧️ Rainfall:</b> {marker['rainfall']}</p>
            <p style="margin: 5px 0;"><b>📊 Confidence:</b> {marker['confidence']}</p>
        </div>
        """
        
        folium.Marker(
            [marker['lat'], marker['lon']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{marker['name']}: {marker['bloom_probability']} bloom",
            icon=folium.Icon(color=color, icon='leaf', prefix='fa')
        ).add_to(m)
        
        # Add circle marker for bloom intensity
        folium.CircleMarker(
            [marker['lat'], marker['lon']],
            radius=bloom_pct / 8,
            color=icon_color,
            fill=True,
            fillColor=icon_color,
            fillOpacity=0.3,
            weight=2
        ).add_to(m)
    
    # Display map
    st_folium(m, height=500, width=None, returned_objects=[], key='climate_map_real')
    
    # Climate summary stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🌸 Avg Bloom Level", climate_stats['avg_bloom_level'], 
                 delta=climate_stats.get('bloom_level_delta', '+5%'))
    with col2:
        st.metric("🌡️ Avg Temperature", climate_stats['avg_temperature'], 
                 delta=climate_stats.get('temperature_delta', '+1°C'))
    with col3:
        st.metric("🌧️ Avg Rainfall", climate_stats['avg_rainfall'], 
                 delta=climate_stats.get('rainfall_delta', '+15mm'))
    with col4:
        st.metric("📍 Total Bloom Area", climate_stats['total_bloom_area'])
    
    # Real data indicator
    if has_real_data:
        st.info("✅ **Real NASA satellite data displayed** | Covering all 47 Kenya counties")
    else:
        st.warning("⚠️ **Demo data displayed** | Run `python backend/kenya_data_fetcher.py --all` to fetch real satellite data")
    
    # CTA for map exploration
    col_cta1, col_cta2, col_cta3 = st.columns([1, 2, 1])
    with col_cta2:
        if st.button("📊 Explore Your Region's Data", key='explore_region_real'):
            st.info("🔐 Please log in to access personalized regional data and alerts!")


def get_farmer_dashboard_bloom_markers(farmer_region: str = None):
    """
    Get real bloom markers for farmer dashboard
    
    Args:
        farmer_region: Filter by farmer's region
    
    Returns:
        List of bloom markers with real satellite data
    """
    if not DATA_LOADER_AVAILABLE:
        return []
    
    loader = StreamlitDataLoader()
    dashboard_data = loader.get_farmer_dashboard_data(farmer_region=farmer_region)
    
    return dashboard_data.get('bloom_markers', [])


def show_bloom_prediction_summary():
    """
    Display bloom prediction summary panel
    Can be added to farmer dashboard
    """
    if not DATA_LOADER_AVAILABLE:
        st.warning("Real data not available")
        return
    
    loader = StreamlitDataLoader()
    summary = loader.get_bloom_prediction_summary()
    
    if 'error' in summary:
        st.error(f"Error loading prediction summary: {summary['error']}")
        return
    
    st.markdown("### 🔮 National Bloom Prediction Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Avg Bloom Probability", f"{summary['avg_bloom_probability']:.1f}%")
    with col2:
        st.metric("Max Probability", f"{summary['max_bloom_probability']:.1f}%")
    with col3:
        st.metric("Counties Analyzed", summary['total_counties_analyzed'])
    
    # High risk counties
    if summary['high_risk_counties']:
        st.markdown("#### 🔴 High Risk Counties (>70% probability)")
        for county in summary['high_risk_counties'][:5]:
            st.write(f"- **{county['name']}**: {county['probability']:.1f}%")
    
    # Moderate risk counties
    if summary['moderate_risk_counties']:
        st.markdown("#### 🟡 Moderate Risk Counties (40-70% probability)")
        for county in summary['moderate_risk_counties'][:3]:
            st.write(f"- **{county['name']}**: {county['probability']:.1f}%")


def refresh_data_button():
    """
    Add a button to manually trigger data refresh
    """
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🔄 Refresh Satellite Data", key='refresh_data'):
            with st.spinner("Fetching latest satellite data from NASA..."):
                try:
                    import subprocess
                    # Run data fetcher in background
                    subprocess.Popen([
                        'python', 
                        os.path.join(os.path.dirname(__file__), '..', 'backend', 'kenya_data_fetcher.py'),
                        '--all'
                    ])
                    st.success("✅ Data refresh started! This may take 10-15 minutes.")
                    st.info("💡 Refresh this page in a few minutes to see updated data.")
                except Exception as e:
                    st.error(f"❌ Error starting data refresh: {e}")


# Quick setup guide for users
def show_data_setup_guide():
    """
    Display setup instructions for real data
    """
    st.markdown("### 🚀 Setting Up Real Satellite Data")
    
    st.markdown("""
    To enable real NASA satellite data for all 47 Kenya counties:
    
    #### Option 1: Manual One-Time Fetch
    ```bash
    cd backend
    python kenya_data_fetcher.py --all
    ```
    
    #### Option 2: Automated Scheduled Fetching
    ```bash
    cd backend
    python data_scheduler.py --run-scheduler
    ```
    This will:
    - Fetch all counties every 6 hours
    - Fetch priority counties every hour
    - Retrain the ML model weekly
    
    #### Option 3: Quick Priority Counties Only
    ```bash
    cd backend
    python kenya_data_fetcher.py --region central
    ```
    
    #### Check Data Status
    ```bash
    cd backend
    python kenya_data_fetcher.py --summary
    ```
    """)
    
    if st.button("✅ I've set up the data"):
        st.balloons()
        st.success("Great! Reload the page to see real satellite data.")

