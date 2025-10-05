"""
Example: How to Add Custom Lottie Animations to BloomWatch Kenya

This file demonstrates different ways to integrate Lottie animations
into your Streamlit app for maximum visual impact.
"""

import streamlit as st
from streamlit_lottie import st_lottie
import requests
import json

# Page config
st.set_page_config(page_title="Animation Examples", layout="wide")

st.title("🎬 Custom Lottie Animations Guide")

st.markdown("""
This guide shows you how to add stunning animations to your BloomWatch app.
Choose from URL loading, local files, or inline JSON.
""")

# Method 1: Load from URL (CDN)
st.header("Method 1: Load from URL")

st.code("""
def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    return None

lottie_animation = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_nLjNFH.json")
st_lottie(lottie_animation, height=300, key="satellite")
""", language="python")

def load_lottie_url(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

# Example 1: Satellite
col1, col2 = st.columns(2)

with col1:
    st.subheader("🛰️ Satellite Animation")
    satellite_url = "https://assets5.lottiefiles.com/packages/lf20_nLjNFH.json"
    lottie_satellite = load_lottie_url(satellite_url)
    if lottie_satellite:
        st_lottie(lottie_satellite, height=250, key="satellite_example")
    else:
        st.error("Failed to load animation")

with col2:
    st.markdown("**Use Case**: Landing page hero, dashboard header")
    st.markdown("**URL**: `https://assets5.lottiefiles.com/packages/lf20_nLjNFH.json`")
    st.markdown("**Height**: 200-300px recommended")
    st.markdown("**Loop**: True (default)")

st.markdown("---")

# Method 2: Load from Local File
st.header("Method 2: Load from Local File")

st.code("""
import json

def load_lottie_file(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

# Save animation JSON to: app/assets/animations/farming.json
lottie_animation = load_lottie_file("app/assets/animations/farming.json")
st_lottie(lottie_animation, height=300, key="farming")
""", language="python")

st.info("""
**Advantages of Local Files**:
- ✅ Works offline
- ✅ Faster loading (no network request)
- ✅ No dependency on external CDN
- ✅ Full control over animation
""")

st.markdown("**Steps to use local files:**")
st.markdown("""
1. Download animation from [LottieFiles.com](https://lottiefiles.com)
2. Save JSON to `app/assets/animations/your_animation.json`
3. Load and use in your app
""")

st.markdown("---")

# Method 3: Popular Agriculture-Themed Animations
st.header("Method 3: Recommended Agriculture Animations")

st.markdown("### 🌱 Best Animations for BloomWatch")

animations = {
    "Plant Growing": {
        "url": "https://assets2.lottiefiles.com/packages/lf20_kcsr6fcp.json",
        "use_case": "Registration page, profile achievements",
        "description": "Seed sprouting into plant"
    },
    "Weather": {
        "url": "https://assets4.lottiefiles.com/packages/lf20_kxsd2zr.json",
        "use_case": "Dashboard weather widget",
        "description": "Sun, clouds, rain animations"
    },
    "Success Checkmark": {
        "url": "https://assets9.lottiefiles.com/packages/lf20_lk80fpsm.json",
        "use_case": "Login success, form submission",
        "description": "Animated checkmark with celebration"
    },
    "Loading": {
        "url": "https://assets8.lottiefiles.com/packages/lf20_a2chheio.json",
        "use_case": "Data loading states",
        "description": "Spinning loader"
    }
}

col1, col2 = st.columns([1, 2])

with col1:
    selected_animation = st.selectbox(
        "Choose animation to preview:",
        list(animations.keys())
    )

with col2:
    anim_data = animations[selected_animation]
    st.markdown(f"**Use Case**: {anim_data['use_case']}")
    st.markdown(f"**Description**: {anim_data['description']}")
    st.code(f"URL: {anim_data['url']}", language="text")

# Show selected animation
lottie_anim = load_lottie_url(anim_data['url'])
if lottie_anim:
    col_center1, col_center2, col_center3 = st.columns([1, 2, 1])
    with col_center2:
        st_lottie(lottie_anim, height=300, key=f"preview_{selected_animation}")

st.markdown("---")

# Method 4: Advanced Configuration
st.header("Method 4: Advanced Configuration")

st.markdown("### Customize Animation Behavior")

col1, col2 = st.columns(2)

with col1:
    anim_height = st.slider("Height (px)", 100, 500, 300)
    anim_speed = st.slider("Speed", 0.5, 2.0, 1.0, 0.1)
    anim_loop = st.checkbox("Loop", value=True)

with col2:
    st.code(f"""
st_lottie(
    lottie_animation,
    height={anim_height},
    speed={anim_speed},
    loop={anim_loop},
    quality="high",
    key="custom_anim"
)
    """, language="python")

# Demo with custom settings
st.markdown("### Live Preview with Your Settings")
demo_url = "https://assets2.lottiefiles.com/packages/lf20_kcsr6fcp.json"
demo_anim = load_lottie_url(demo_url)
if demo_anim:
    col_demo1, col_demo2, col_demo3 = st.columns([1, 2, 1])
    with col_demo2:
        st_lottie(
            demo_anim,
            height=anim_height,
            speed=anim_speed,
            loop=anim_loop,
            quality="high",
            key="custom_preview"
        )

st.markdown("---")

# Method 5: Creating Animation Library
st.header("Method 5: Create Your Animation Library")

st.markdown("### Organized Animation Management")

st.code("""
# In your main app file:

ANIMATION_LIBRARY = {
    'agriculture': {
        'satellite': 'https://assets5.lottiefiles.com/packages/lf20_nLjNFH.json',
        'farming': 'https://assets9.lottiefiles.com/packages/lf20_touohxv0.json',
        'plant_growth': 'https://assets2.lottiefiles.com/packages/lf20_kcsr6fcp.json',
    },
    'feedback': {
        'success': 'https://assets9.lottiefiles.com/packages/lf20_lk80fpsm.json',
        'error': 'https://assets1.lottiefiles.com/packages/lf20_error.json',
        'loading': 'https://assets8.lottiefiles.com/packages/lf20_a2chheio.json',
    },
    'weather': {
        'sunny': 'https://assets4.lottiefiles.com/packages/lf20_sunny.json',
        'rainy': 'https://assets4.lottiefiles.com/packages/lf20_rainy.json',
        'cloudy': 'https://assets4.lottiefiles.com/packages/lf20_cloudy.json',
    }
}

# Usage:
def show_animation(category, name, height=300):
    url = ANIMATION_LIBRARY.get(category, {}).get(name)
    if url:
        anim = load_lottie_url(url)
        if anim:
            st_lottie(anim, height=height, key=f"{category}_{name}")

# In your pages:
show_animation('agriculture', 'satellite', height=250)
show_animation('feedback', 'success', height=150)
""", language="python")

st.markdown("---")

# Tips and Best Practices
st.header("💡 Tips & Best Practices")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### ✅ Do's")
    st.markdown("""
    - Use animations purposefully (enhance, don't distract)
    - Keep file sizes small (< 100KB)
    - Test loading times
    - Have fallbacks for slow connections
    - Use consistent animation style
    - Cache loaded animations
    - Consider accessibility (allow disabling)
    """)

with col2:
    st.markdown("### ❌ Don'ts")
    st.markdown("""
    - Overuse animations (causes fatigue)
    - Use very large files (> 500KB)
    - Auto-play sound (without user consent)
    - Block content with animations
    - Use conflicting animation styles
    - Load all animations upfront
    - Ignore mobile performance
    """)

st.markdown("---")

# Where to Find Animations
st.header("🔍 Where to Find Great Animations")

resources = {
    "LottieFiles": {
        "url": "https://lottiefiles.com",
        "description": "Largest library of free Lottie animations",
        "license": "Free + Premium options"
    },
    "IconScout": {
        "url": "https://iconscout.com/lottie-animations",
        "description": "High-quality animated icons",
        "license": "Free + Premium"
    },
    "Motion Elements": {
        "url": "https://www.motionelements.com",
        "description": "Professional animations",
        "license": "Subscription-based"
    },
    "Lottie Creator (Adobe)": {
        "url": "https://www.adobe.com/products/lottie.html",
        "description": "Create custom animations in After Effects",
        "license": "Adobe subscription"
    }
}

for name, info in resources.items():
    with st.expander(f"📚 {name}"):
        st.markdown(f"**URL**: [{info['url']}]({info['url']})")
        st.markdown(f"**Description**: {info['description']}")
        st.markdown(f"**License**: {info['license']}")

st.markdown("---")

# Integration Example
st.header("🔧 Full Integration Example")

st.markdown("### Complete Code for BloomWatch Landing Page")

st.code("""
import streamlit as st
from streamlit_lottie import st_lottie
import requests

# Load animation function
@st.cache_data
def load_lottie_url(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

# Page content
st.markdown('''
<div style="text-align: center;">
    <h1>🌾 Welcome to BloomWatch Kenya</h1>
    <p>NASA-powered bloom detection for farmers</p>
</div>
''', unsafe_allow_html=True)

# Show satellite animation
satellite_anim = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_nLjNFH.json")
if satellite_anim:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st_lottie(satellite_anim, height=300, key="hero_satellite")

# Rest of landing page...
st.button("🚀 Get Started")
""", language="python")

st.markdown("---")

# Troubleshooting
st.header("🐛 Troubleshooting")

with st.expander("Animation not loading"):
    st.markdown("""
    **Problem**: Animation doesn't appear
    
    **Solutions**:
    1. Check internet connection (for URL loading)
    2. Verify URL is correct and accessible
    3. Check for CORS issues
    4. Try with different animation URL
    5. Check browser console for errors
    6. Ensure `streamlit-lottie` is installed: `pip install streamlit-lottie`
    """)

with st.expander("Slow performance"):
    st.markdown("""
    **Problem**: App becomes slow with animations
    
    **Solutions**:
    1. Reduce animation file size (use online optimizers)
    2. Limit number of simultaneous animations
    3. Use `@st.cache_data` for load functions
    4. Consider lower quality setting
    5. Lazy load animations (show only when needed)
    6. Use static image as fallback on mobile
    """)

with st.expander("Animation appears distorted"):
    st.markdown("""
    **Problem**: Animation doesn't look right
    
    **Solutions**:
    1. Check aspect ratio matches original
    2. Adjust height parameter
    3. Try different container width
    4. Check animation JSON for issues
    5. Test with different browser
    6. Update streamlit-lottie: `pip install --upgrade streamlit-lottie`
    """)

st.markdown("---")

# Footer
st.success("""
🎉 **You're ready to add amazing animations to BloomWatch Kenya!**

Remember: Animations should enhance the user experience, not distract from it.
Use them strategically to guide users, celebrate actions, and make the app feel alive.
""")

st.info("""
**Next Steps**:
1. Browse [LottieFiles.com](https://lottiefiles.com) for agriculture-themed animations
2. Test animations with different heights and speeds
3. Integrate into your BloomWatch pages
4. Get feedback from test users
5. Optimize for performance
""")

st.markdown("---")
st.markdown("*Built for BloomWatch Kenya - NASA Space Apps Challenge 2025* 🚀🌾")




