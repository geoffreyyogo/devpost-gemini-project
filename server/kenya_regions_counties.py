"""
Kenya Regions, Counties, and Crops Data
Comprehensive mapping for Smart Shamba
"""

# Region to Counties Mapping (all 47 counties)
KENYA_REGIONS_COUNTIES = {
    'central': {
        'name': 'Central',
        'name_sw': 'Kati',
        'counties': ['Kiambu', 'Kirinyaga', 'Murang\'a', 'Nyeri', 'Nyandarua']
    },
    'coast': {
        'name': 'Coast',
        'name_sw': 'Pwani',
        'counties': ['Kilifi', 'Kwale', 'Lamu', 'Mombasa', 'Taita-Taveta', 'Tana River']
    },
    'eastern': {
        'name': 'Eastern',
        'name_sw': 'Mashariki',
        'counties': ['Embu', 'Isiolo', 'Kitui', 'Machakos', 'Makueni', 'Marsabit', 'Meru', 'Tharaka-Nithi']
    },
    'nairobi': {
        'name': 'Nairobi',
        'name_sw': 'Nairobi',
        'counties': ['Nairobi']
    },
    'north_eastern': {
        'name': 'North Eastern',
        'name_sw': 'Kaskazini Mashariki',
        'counties': ['Garissa', 'Mandera', 'Wajir']
    },
    'nyanza': {
        'name': 'Nyanza',
        'name_sw': 'Nyanza',
        'counties': ['Homa Bay', 'Kisii', 'Kisumu', 'Migori', 'Nyamira', 'Siaya']
    },
    'rift_valley': {
        'name': 'Rift Valley',
        'name_sw': 'Bonde la Ufa',
        'counties': ['Baringo', 'Bomet', 'Elgeyo-Marakwet', 'Kajiado', 'Kericho', 'Laikipia', 
                     'Nakuru', 'Nandi', 'Narok', 'Samburu', 'Trans Nzoia', 'Turkana', 
                     'Uasin Gishu', 'West Pokot']
    },
    'western': {
        'name': 'Western',
        'name_sw': 'Magharibi',
        'counties': ['Bungoma', 'Busia', 'Kakamega', 'Vihiga']
    }
}

# All crops grown in Kenya (extracted from county data)
ALL_KENYA_CROPS = {
    'maize': {'name': 'Maize', 'name_sw': 'Mahindi', 'category': 'cereal', 'icon': '🌽'},
    'beans': {'name': 'Beans', 'name_sw': 'Maharagwe', 'category': 'legume', 'icon': '🫘'},
    'coffee': {'name': 'Coffee', 'name_sw': 'Kahawa', 'category': 'cash_crop', 'icon': '☕'},
    'tea': {'name': 'Tea', 'name_sw': 'Chai', 'category': 'cash_crop', 'icon': '🍵'},
    'wheat': {'name': 'Wheat', 'name_sw': 'Ngano', 'category': 'cereal', 'icon': '🌾'},
    'sorghum': {'name': 'Sorghum', 'name_sw': 'Mtama', 'category': 'cereal', 'icon': '🌾'},
    'rice': {'name': 'Rice', 'name_sw': 'Mchele', 'category': 'cereal', 'icon': '🌾'},
    'millet': {'name': 'Millet', 'name_sw': 'Ulezi', 'category': 'cereal', 'icon': '🌾'},
    'barley': {'name': 'Barley', 'name_sw': 'Shayiri', 'category': 'cereal', 'icon': '🌾'},
    'potatoes': {'name': 'Potatoes', 'name_sw': 'Viazi', 'category': 'tuber', 'icon': '🥔'},
    'sweet_potatoes': {'name': 'Sweet Potatoes', 'name_sw': 'Viazi Vitamu', 'category': 'tuber', 'icon': '🍠'},
    'cassava': {'name': 'Cassava', 'name_sw': 'Muhogo', 'category': 'tuber', 'icon': '🥔'},
    'sugarcane': {'name': 'Sugarcane', 'name_sw': 'Miwa', 'category': 'cash_crop', 'icon': '🎋'},
    'cotton': {'name': 'Cotton', 'name_sw': 'Pamba', 'category': 'cash_crop', 'icon': '🌱'},
    'tobacco': {'name': 'Tobacco', 'name_sw': 'Tumbaku', 'category': 'cash_crop', 'icon': '🌿'},
    'pyrethrum': {'name': 'Pyrethrum', 'name_sw': 'Pyrethrum', 'category': 'cash_crop', 'icon': '🌼'},
    'sisal': {'name': 'Sisal', 'name_sw': 'Sisal', 'category': 'fibre', 'icon': '🌿'},
    'miraa': {'name': 'Miraa', 'name_sw': 'Miraa', 'category': 'cash_crop', 'icon': '🌿'},
    'bananas': {'name': 'Bananas', 'name_sw': 'Ndizi', 'category': 'fruit', 'icon': '🍌'},
    'mangoes': {'name': 'Mangoes', 'name_sw': 'Maembe', 'category': 'fruit', 'icon': '🥭'},
    'cashew_nuts': {'name': 'Cashew Nuts', 'name_sw': 'Korosho', 'category': 'nut', 'icon': '🥜'},
    'macadamia': {'name': 'Macadamia', 'name_sw': 'Macadamia', 'category': 'nut', 'icon': '🌰'},
    'coconut': {'name': 'Coconut', 'name_sw': 'Nazi', 'category': 'fruit', 'icon': '🥥'},
    'fruits': {'name': 'Fruits (General)', 'name_sw': 'Matunda', 'category': 'fruit', 'icon': '🍎'},
    'vegetables': {'name': 'Vegetables', 'name_sw': 'Mboga', 'category': 'vegetable', 'icon': '🥬'},
    'cabbages': {'name': 'Cabbages', 'name_sw': 'Kabichi', 'category': 'vegetable', 'icon': '🥬'},
    'horticulture': {'name': 'Horticulture', 'name_sw': 'Bustani', 'category': 'vegetable', 'icon': '🥕'},
    'pigeon_peas': {'name': 'Pigeon Peas', 'name_sw': 'Mbaazi', 'category': 'legume', 'icon': '🫘'},
    'dairy': {'name': 'Dairy Farming', 'name_sw': 'Ufugaji Maziwa', 'category': 'livestock', 'icon': '🐄'},
    'livestock': {'name': 'Livestock', 'name_sw': 'Mifugo', 'category': 'livestock', 'icon': '🐑'},
    'fishing': {'name': 'Fishing', 'name_sw': 'Uvuvi', 'category': 'aquaculture', 'icon': '🐟'},
    'urban_farming': {'name': 'Urban Farming', 'name_sw': 'Kilimo cha Mijini', 'category': 'urban', 'icon': '🏙️'}
}

# County-specific crops (loaded from JSON files)
def get_county_crops(county_id: str) -> list:
    """Get crops specific to a county"""
    import json
    import os
    
    try:
        # Clean county_id for filename
        clean_id = county_id.lower().replace(" ", "_").replace("-", "_").replace("'", "")
        file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'county_data', f'{clean_id}.json')
        with open(file_path, 'r') as f:
            data = json.load(f)
            return data.get('main_crops', [])
    except Exception as e:
        print(f"Error loading crops for {county_id}: {e}")
        return []

def get_region_by_county(county_name: str) -> str:
    """Get region for a given county"""
    for region_id, region_data in KENYA_REGIONS_COUNTIES.items():
        if county_name in region_data['counties']:
            return region_id
    return 'unknown'

def get_all_counties() -> list:
    """Get all counties in Kenya"""
    counties = []
    for region_data in KENYA_REGIONS_COUNTIES.values():
        counties.extend(region_data['counties'])
    return sorted(counties)

def get_counties_by_region(region_id: str) -> list:
    """Get counties in a specific region"""
    return KENYA_REGIONS_COUNTIES.get(region_id, {}).get('counties', [])

# Common crops by category (for quick selection)
COMMON_CROPS_BY_CATEGORY = {
    'cereals': ['maize', 'wheat', 'rice', 'sorghum', 'millet', 'barley'],
    'legumes': ['beans', 'pigeon_peas'],
    'cash_crops': ['coffee', 'tea', 'sugarcane', 'cotton', 'tobacco', 'pyrethrum', 'miraa', 'sisal'],
    'tubers': ['potatoes', 'sweet_potatoes', 'cassava'],
    'fruits': ['bananas', 'mangoes', 'coconut', 'fruits'],
    'nuts': ['cashew_nuts', 'macadamia'],
    'vegetables': ['vegetables', 'cabbages', 'horticulture'],
    'livestock': ['dairy', 'livestock', 'fishing'],
    'urban': ['urban_farming']
}

# USSD crop codes (for numeric selection via USSD)
def get_ussd_crop_codes(county: str = None) -> dict:
    """Get crop codes for USSD selection, optionally filtered by county"""
    if county:
        # Get county-specific crops
        county_crops = get_county_crops(county.lower().replace(" ", "_").replace("-", "_").replace("'", ""))
        # Map to crop IDs
        crop_ids = []
        for crop_name in county_crops:
            crop_id = crop_name.lower().replace(" ", "_").replace("-", "_")
            if crop_id in ALL_KENYA_CROPS:
                crop_ids.append(crop_id)
            # Handle special cases
            elif 'horticulture' in crop_name.lower():
                crop_ids.append('horticulture')
        
        # Create codes mapping
        codes = {}
        for i, crop_id in enumerate(crop_ids, 1):
            codes[str(i)] = crop_id
        # Always add "Other" option
        codes[str(len(codes) + 1)] = 'other'
        return codes
    else:
        # Return most common crops for general selection
        common = ['maize', 'beans', 'coffee', 'tea', 'wheat', 'potatoes', 
                  'horticulture', 'rice', 'sugarcane', 'bananas']
        codes = {str(i+1): crop for i, crop in enumerate(common)}
        codes[str(len(codes) + 1)] = 'other'
        return codes

if __name__ == "__main__":
    print("=" * 80)
    print("Kenya Regions, Counties, and Crops Data")
    print("=" * 80)
    
    print(f"\n📍 Total Regions: {len(KENYA_REGIONS_COUNTIES)}")
    print(f"📍 Total Counties: {len(get_all_counties())}")
    print(f"🌾 Total Crops: {len(ALL_KENYA_CROPS)}")
    
    print("\n🗺️  REGIONS AND COUNTIES:")
    print("-" * 80)
    for region_id, region_data in KENYA_REGIONS_COUNTIES.items():
        print(f"\n{region_data['name']} ({len(region_data['counties'])} counties):")
        print(f"  {', '.join(region_data['counties'])}")
    
    print("\n\n🌾 ALL CROPS IN KENYA:")
    print("-" * 80)
    for category in COMMON_CROPS_BY_CATEGORY:
        crops_in_category = COMMON_CROPS_BY_CATEGORY[category]
        print(f"\n{category.upper()}:")
        for crop_id in crops_in_category:
            crop_data = ALL_KENYA_CROPS.get(crop_id, {})
            print(f"  {crop_data.get('icon', '•')} {crop_data.get('name', crop_id)} ({crop_data.get('name_sw', '')})")
    
    print("\n\n📱 USSD CROP CODES (Example for Kiambu):")
    print("-" * 80)
    codes = get_ussd_crop_codes('Kiambu')
    for code, crop_id in codes.items():
        if crop_id == 'other':
            print(f"  {code}. Other (Enter crop name)")
        else:
            crop_data = ALL_KENYA_CROPS.get(crop_id, {})
            print(f"  {code}. {crop_data.get('name', crop_id)}")
    
    print("\n" + "=" * 80)


