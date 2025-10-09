#!/usr/bin/env python3
"""
Quick test script to verify light mode fixes are working
"""

import streamlit as st
from app.apply_light_mode_fix import apply_light_mode_fix

st.set_page_config(
    page_title="Light Mode Fix Test",
    page_icon="🌞",
    layout="wide"
)

# Apply the light mode fix
apply_light_mode_fix()

st.title("🌞 Light Mode Fix Test")
st.markdown("This page tests all the form components to ensure they have proper light mode styling.")

# Test form with all components
with st.container():
    st.subheader("📝 Registration Form Test")
    
    with st.form("test_registration_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Name", placeholder="Enter your name")
            st.text_input("Email", placeholder="Enter your email")
            st.text_input("Phone", placeholder="+254712345678")
            st.text_input("Password", type="password", placeholder="Enter password")
            st.text_input("Confirm Password", type="password", placeholder="Confirm password")
        
        with col2:
            st.selectbox("Select Your Region", ["Central", "Rift Valley", "Western", "Eastern"])
            st.multiselect("Select Crops You Grow", ["Maize", "Beans", "Coffee", "Tea", "Wheat", "Sorghum"])
            st.selectbox("Preferred Language", ["English", "Kiswahili"])
        
        # Submit button
        st.form_submit_button("Complete Registration")

# Test individual components
st.subheader("🔧 Individual Component Tests")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Text Inputs**")
    st.text_input("Test Input 1")
    st.text_input("Test Input 2", type="password")

with col2:
    st.markdown("**Selectboxes**")
    st.selectbox("Test Selectbox 1", ["Option 1", "Option 2", "Option 3"])
    st.selectbox("Test Selectbox 2", ["A", "B", "C"])

with col3:
    st.markdown("**Multiselect**")
    st.multiselect("Test Multiselect 1", ["Item 1", "Item 2", "Item 3"])
    st.multiselect("Test Multiselect 2", ["X", "Y", "Z"])

# Test buttons
st.subheader("🔘 Button Tests")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.button("Regular Button")
with col2:
    st.button("Another Button")
with col3:
    st.button("Third Button")
with col4:
    st.button("Fourth Button")

# Status indicators
st.subheader("✅ Test Results")

with st.container():
    st.success("✅ If you can see this with proper light styling, the fixes are working!")
    st.info("🔍 Check that:")
    st.markdown("""
    - Input fields have white backgrounds
    - Text in inputs is dark and readable
    - Selectboxes have white backgrounds
    - Multiselect components are properly styled
    - Buttons have proper light styling
    - All text is readable with good contrast
    """)

st.markdown("---")
st.markdown("**Test completed!** If all components look properly styled in light mode, the fixes are working correctly.")
