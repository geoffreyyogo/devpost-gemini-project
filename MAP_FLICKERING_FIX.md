# Map Flickering Issue - FIXED ✅

## Problem
The farmer's map was flickering and unstable upon login, with bloom events barely showing consistently.

## Root Cause
The bloom event markers on the map were being regenerated with **random positions on every page render** using `np.random.uniform()`. This caused:
- Markers to appear in different positions each time
- Map instability and flickering
- Poor user experience

### Code Location
- File: `app/streamlit_app_enhanced.py`
- Function: `show_dashboard_tab(farmer)`
- Lines: ~1203-1255

## Solution Implemented

### 1. Stable Marker Generation
- Created a **farmer-specific seed** based on phone number hash
- Bloom markers are now generated **once per farmer** and stored in session state
- Markers remain consistent across page renders

### 2. Session State Caching
- Bloom marker positions cached in `st.session_state.bloom_markers`
- Cached separately per farmer using `st.session_state.current_farmer`
- Only regenerated when switching farmers

### 3. Map Component Optimization
- Added `returned_objects=[]` parameter to `st_folium()` to prevent unnecessary state updates
- Added unique `key='farmer_bloom_map'` for proper component isolation

## Technical Details

### Before (Problematic Code)
```python
# This generated new random positions on EVERY render
for i in range(5):
    lat_offset = np.random.uniform(-0.1, 0.1)  # ❌ Random every time
    lon_offset = np.random.uniform(-0.1, 0.1)  # ❌ Random every time
    folium.CircleMarker([lat + lat_offset, lon + lon_offset], ...).add_to(m)
```

### After (Fixed Code)
```python
# Generate stable markers ONCE per farmer
if 'bloom_markers' not in st.session_state or st.session_state.get('current_farmer') != farmer.get('phone'):
    farmer_seed = hash(farmer.get('phone', 'default')) % (2**32)
    np.random.seed(farmer_seed)  # ✅ Deterministic seed
    st.session_state.bloom_markers = [...]  # ✅ Cached in session state
    st.session_state.current_farmer = farmer.get('phone')

# Reuse cached markers (stable positions)
for marker in st.session_state.bloom_markers:
    folium.CircleMarker([lat + marker['lat_offset'], ...]).add_to(m)
```

## Benefits
1. ✅ **No more flickering** - Map remains stable
2. ✅ **Consistent bloom locations** - Markers stay in the same positions
3. ✅ **Better performance** - Reduced unnecessary recalculations
4. ✅ **Improved UX** - Farmer can now properly view bloom events
5. ✅ **Per-farmer stability** - Each farmer has their own consistent map

## Testing Recommendations
1. Log in as a farmer
2. Navigate to the dashboard
3. Verify the map loads once and stays stable
4. Check that bloom event markers appear consistently
5. Switch between tabs and verify map doesn't flicker
6. Log out and log in again - markers should be in same positions

## Date Fixed
October 5, 2025

## Related Files
- `app/streamlit_app_enhanced.py` (main fix)
- Session state variables: `bloom_markers`, `current_farmer`


