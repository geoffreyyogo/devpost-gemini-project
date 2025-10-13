"""
Complete Configuration for All 47 Kenya Counties
With coordinates, agricultural data, and satellite data regions
"""

# All 47 Kenya Counties with accurate coordinates and agricultural information
KENYA_COUNTIES = {
    # Central Kenya
    'kiambu': {
        'name': 'Kiambu',
        'region': 'central',
        'coordinates': {'lat': -1.171, 'lon': 36.835},
        'bbox': [36.6, -1.4, 37.1, -0.9],
        'main_crops': ['coffee', 'tea', 'maize', 'beans', 'potatoes'],
        'population': 2417735,
        'agricultural': True
    },
    'kirinyaga': {
        'name': 'Kirinyaga',
        'region': 'central',
        'coordinates': {'lat': -0.659, 'lon': 37.383},
        'bbox': [37.2, -0.9, 37.6, -0.4],
        'main_crops': ['rice', 'maize', 'beans', 'coffee', 'tea'],
        'population': 610411,
        'agricultural': True
    },
    'muranga': {
        'name': "Murang'a",
        'region': 'central',
        'coordinates': {'lat': -0.722, 'lon': 37.152},
        'bbox': [36.9, -1.0, 37.4, -0.5],
        'main_crops': ['coffee', 'tea', 'maize', 'beans', 'macadamia'],
        'population': 1056640,
        'agricultural': True
    },
    'nyandarua': {
        'name': 'Nyandarua',
        'region': 'central',
        'coordinates': {'lat': -0.180, 'lon': 36.480},
        'bbox': [36.2, -0.5, 36.8, 0.1],
        'main_crops': ['potatoes', 'cabbages', 'wheat', 'maize', 'pyrethrum'],
        'population': 638289,
        'agricultural': True
    },
    'nyeri': {
        'name': 'Nyeri',
        'region': 'central',
        'coordinates': {'lat': -0.420, 'lon': 36.950},
        'bbox': [36.7, -0.7, 37.2, -0.1],
        'main_crops': ['coffee', 'tea', 'maize', 'beans', 'dairy'],
        'population': 759164,
        'agricultural': True
    },
    
    # Rift Valley
    'baringo': {
        'name': 'Baringo',
        'region': 'rift_valley',
        'coordinates': {'lat': 0.468, 'lon': 36.089},
        'bbox': [35.8, 0.1, 36.4, 0.9],
        'main_crops': ['maize', 'sorghum', 'millet', 'livestock'],
        'population': 666763,
        'agricultural': True
    },
    'bomet': {
        'name': 'Bomet',
        'region': 'rift_valley',
        'coordinates': {'lat': -0.803, 'lon': 35.308},
        'bbox': [35.1, -1.0, 35.6, -0.6],
        'main_crops': ['tea', 'maize', 'pyrethrum', 'dairy'],
        'population': 875689,
        'agricultural': True
    },
    'elgeyo_marakwet': {
        'name': 'Elgeyo-Marakwet',
        'region': 'rift_valley',
        'coordinates': {'lat': 0.850, 'lon': 35.450},
        'bbox': [35.2, 0.5, 35.7, 1.2],
        'main_crops': ['maize', 'wheat', 'pyrethrum', 'dairy'],
        'population': 454509,
        'agricultural': True
    },
    'kajiado': {
        'name': 'Kajiado',
        'region': 'rift_valley',
        'coordinates': {'lat': -1.852, 'lon': 36.777},
        'bbox': [36.0, -2.9, 37.5, -1.0],
        'main_crops': ['maize', 'beans', 'livestock', 'horticulture'],
        'population': 1117840,
        'agricultural': True
    },
    'kericho': {
        'name': 'Kericho',
        'region': 'rift_valley',
        'coordinates': {'lat': -0.368, 'lon': 35.283},
        'bbox': [35.0, -0.7, 35.6, 0.0],
        'main_crops': ['tea', 'maize', 'pyrethrum', 'dairy'],
        'population': 901777,
        'agricultural': True
    },
    'laikipia': {
        'name': 'Laikipia',
        'region': 'rift_valley',
        'coordinates': {'lat': 0.362, 'lon': 36.782},
        'bbox': [36.3, -0.2, 37.3, 0.9],
        'main_crops': ['wheat', 'maize', 'barley', 'livestock'],
        'population': 518560,
        'agricultural': True
    },
    'nakuru': {
        'name': 'Nakuru',
        'region': 'rift_valley',
        'coordinates': {'lat': -0.303, 'lon': 36.080},
        'bbox': [35.5, -1.1, 36.5, 0.4],
        'main_crops': ['wheat', 'maize', 'pyrethrum', 'horticulture'],
        'population': 2162202,
        'agricultural': True
    },
    'nandi': {
        'name': 'Nandi',
        'region': 'rift_valley',
        'coordinates': {'lat': 0.183, 'lon': 35.127},
        'bbox': [34.9, -0.2, 35.4, 0.5],
        'main_crops': ['tea', 'maize', 'pyrethrum', 'dairy'],
        'population': 885711,
        'agricultural': True
    },
    'narok': {
        'name': 'Narok',
        'region': 'rift_valley',
        'coordinates': {'lat': -1.085, 'lon': 35.871},
        'bbox': [35.0, -1.9, 36.5, -0.3],
        'main_crops': ['wheat', 'maize', 'barley', 'livestock'],
        'population': 1157873,
        'agricultural': True
    },
    'samburu': {
        'name': 'Samburu',
        'region': 'rift_valley',
        'coordinates': {'lat': 1.216, 'lon': 36.944},
        'bbox': [36.3, 0.5, 37.7, 2.5],
        'main_crops': ['livestock', 'maize', 'sorghum'],
        'population': 310327,
        'agricultural': False
    },
    'trans_nzoia': {
        'name': 'Trans Nzoia',
        'region': 'rift_valley',
        'coordinates': {'lat': 1.049, 'lon': 34.950},
        'bbox': [34.7, 0.8, 35.2, 1.4],
        'main_crops': ['maize', 'wheat', 'dairy', 'pyrethrum'],
        'population': 990341,
        'agricultural': True
    },
    'turkana': {
        'name': 'Turkana',
        'region': 'rift_valley',
        'coordinates': {'lat': 3.117, 'lon': 35.597},
        'bbox': [34.5, 1.5, 36.8, 5.5],
        'main_crops': ['livestock', 'sorghum', 'millet'],
        'population': 926976,
        'agricultural': False
    },
    'uasin_gishu': {
        'name': 'Uasin Gishu',
        'region': 'rift_valley',
        'coordinates': {'lat': 0.514, 'lon': 35.270},
        'bbox': [34.9, 0.1, 35.6, 0.9],
        'main_crops': ['maize', 'wheat', 'pyrethrum', 'dairy'],
        'population': 1163186,
        'agricultural': True
    },
    'west_pokot': {
        'name': 'West Pokot',
        'region': 'rift_valley',
        'coordinates': {'lat': 1.621, 'lon': 35.363},
        'bbox': [34.8, 1.0, 35.8, 2.5],
        'main_crops': ['maize', 'sorghum', 'livestock'],
        'population': 621241,
        'agricultural': True
    },
    
    # Eastern Kenya
    'embu': {
        'name': 'Embu',
        'region': 'eastern',
        'coordinates': {'lat': -0.531, 'lon': 37.450},
        'bbox': [37.2, -0.8, 37.7, -0.3],
        'main_crops': ['coffee', 'tea', 'maize', 'beans', 'miraa'],
        'population': 608599,
        'agricultural': True
    },
    'isiolo': {
        'name': 'Isiolo',
        'region': 'eastern',
        'coordinates': {'lat': 0.355, 'lon': 37.583},
        'bbox': [37.0, -0.5, 38.5, 1.5],
        'main_crops': ['livestock', 'maize', 'sorghum'],
        'population': 268002,
        'agricultural': False
    },
    'kitui': {
        'name': 'Kitui',
        'region': 'eastern',
        'coordinates': {'lat': -1.367, 'lon': 38.010},
        'bbox': [37.5, -2.0, 38.8, -0.5],
        'main_crops': ['maize', 'beans', 'millet', 'sorghum', 'livestock'],
        'population': 1136187,
        'agricultural': True
    },
    'machakos': {
        'name': 'Machakos',
        'region': 'eastern',
        'coordinates': {'lat': -1.522, 'lon': 37.263},
        'bbox': [36.8, -2.0, 37.7, -0.9],
        'main_crops': ['maize', 'beans', 'fruits', 'vegetables'],
        'population': 1421932,
        'agricultural': True
    },
    'makueni': {
        'name': 'Makueni',
        'region': 'eastern',
        'coordinates': {'lat': -2.280, 'lon': 37.820},
        'bbox': [37.4, -2.8, 38.4, -1.5],
        'main_crops': ['maize', 'beans', 'pigeon peas', 'fruits'],
        'population': 987653,
        'agricultural': True
    },
    'marsabit': {
        'name': 'Marsabit',
        'region': 'eastern',
        'coordinates': {'lat': 2.333, 'lon': 37.983},
        'bbox': [37.0, 1.0, 38.5, 4.5],
        'main_crops': ['livestock', 'maize'],
        'population': 459785,
        'agricultural': False
    },
    'meru': {
        'name': 'Meru',
        'region': 'eastern',
        'coordinates': {'lat': 0.050, 'lon': 37.650},
        'bbox': [37.3, -0.4, 38.0, 0.5],
        'main_crops': ['miraa', 'coffee', 'tea', 'maize', 'beans'],
        'population': 1545714,
        'agricultural': True
    },
    'tharaka_nithi': {
        'name': 'Tharaka-Nithi',
        'region': 'eastern',
        'coordinates': {'lat': -0.281, 'lon': 37.733},
        'bbox': [37.4, -0.6, 38.0, 0.1],
        'main_crops': ['coffee', 'tea', 'miraa', 'maize', 'beans'],
        'population': 393177,
        'agricultural': True
    },
    
    # Western Kenya
    'bungoma': {
        'name': 'Bungoma',
        'region': 'western',
        'coordinates': {'lat': 0.564, 'lon': 34.558},
        'bbox': [34.2, 0.3, 34.9, 0.9],
        'main_crops': ['maize', 'sugarcane', 'beans', 'bananas'],
        'population': 1670570,
        'agricultural': True
    },
    'busia': {
        'name': 'Busia',
        'region': 'western',
        'coordinates': {'lat': 0.450, 'lon': 34.111},
        'bbox': [33.9, 0.0, 34.4, 0.8],
        'main_crops': ['maize', 'cassava', 'sweet potatoes', 'millet'],
        'population': 893681,
        'agricultural': True
    },
    'kakamega': {
        'name': 'Kakamega',
        'region': 'western',
        'coordinates': {'lat': 0.282, 'lon': 34.752},
        'bbox': [34.5, -0.1, 35.0, 0.7],
        'main_crops': ['maize', 'sugarcane', 'tea', 'bananas'],
        'population': 1867579,
        'agricultural': True
    },
    'vihiga': {
        'name': 'Vihiga',
        'region': 'western',
        'coordinates': {'lat': 0.070, 'lon': 34.728},
        'bbox': [34.5, -0.2, 34.9, 0.3],
        'main_crops': ['tea', 'maize', 'bananas', 'beans'],
        'population': 590013,
        'agricultural': True
    },
    
    # Nyanza
    'homa_bay': {
        'name': 'Homa Bay',
        'region': 'nyanza',
        'coordinates': {'lat': -0.523, 'lon': 34.457},
        'bbox': [34.0, -0.9, 34.9, -0.1],
        'main_crops': ['maize', 'sorghum', 'fishing', 'cotton'],
        'population': 1131950,
        'agricultural': True
    },
    'kisii': {
        'name': 'Kisii',
        'region': 'nyanza',
        'coordinates': {'lat': -0.677, 'lon': 34.778},
        'bbox': [34.5, -1.0, 35.1, -0.4],
        'main_crops': ['tea', 'bananas', 'maize', 'beans'],
        'population': 1266860,
        'agricultural': True
    },
    'kisumu': {
        'name': 'Kisumu',
        'region': 'nyanza',
        'coordinates': {'lat': -0.091, 'lon': 34.768},
        'bbox': [34.4, -0.4, 35.1, 0.3],
        'main_crops': ['maize', 'sugarcane', 'rice', 'fishing'],
        'population': 1155574,
        'agricultural': True
    },
    'migori': {
        'name': 'Migori',
        'region': 'nyanza',
        'coordinates': {'lat': -1.063, 'lon': 34.473},
        'bbox': [34.0, -1.5, 34.9, -0.6],
        'main_crops': ['sugarcane', 'maize', 'tobacco', 'sorghum'],
        'population': 1116436,
        'agricultural': True
    },
    'nyamira': {
        'name': 'Nyamira',
        'region': 'nyanza',
        'coordinates': {'lat': -0.568, 'lon': 34.935},
        'bbox': [34.7, -0.9, 35.2, -0.3],
        'main_crops': ['tea', 'bananas', 'maize', 'beans'],
        'population': 605576,
        'agricultural': True
    },
    'siaya': {
        'name': 'Siaya',
        'region': 'nyanza',
        'coordinates': {'lat': -0.063, 'lon': 34.288},
        'bbox': [33.9, -0.4, 34.6, 0.3],
        'main_crops': ['maize', 'sorghum', 'cassava', 'fishing'],
        'population': 993183,
        'agricultural': True
    },
    
    # Coast
    'kilifi': {
        'name': 'Kilifi',
        'region': 'coast',
        'coordinates': {'lat': -3.631, 'lon': 39.853},
        'bbox': [39.3, -4.1, 40.2, -2.7],
        'main_crops': ['coconut', 'cashew nuts', 'maize', 'cassava'],
        'population': 1453787,
        'agricultural': True
    },
    'kwale': {
        'name': 'Kwale',
        'region': 'coast',
        'coordinates': {'lat': -4.174, 'lon': 39.453},
        'bbox': [38.8, -4.7, 39.7, -3.5],
        'main_crops': ['cashew nuts', 'coconut', 'maize', 'cassava'],
        'population': 866820,
        'agricultural': True
    },
    'lamu': {
        'name': 'Lamu',
        'region': 'coast',
        'coordinates': {'lat': -2.271, 'lon': 40.902},
        'bbox': [40.0, -2.7, 41.5, -1.6],
        'main_crops': ['coconut', 'fishing', 'maize'],
        'population': 143920,
        'agricultural': True
    },
    'mombasa': {
        'name': 'Mombasa',
        'region': 'coast',
        'coordinates': {'lat': -4.043, 'lon': 39.668},
        'bbox': [39.5, -4.2, 39.8, -3.9],
        'main_crops': ['fishing', 'coconut'],
        'population': 1208333,
        'agricultural': False
    },
    'taita_taveta': {
        'name': 'Taita-Taveta',
        'region': 'coast',
        'coordinates': {'lat': -3.316, 'lon': 38.348},
        'bbox': [37.6, -4.0, 38.9, -2.8],
        'main_crops': ['maize', 'beans', 'horticulture', 'sisal'],
        'population': 340671,
        'agricultural': True
    },
    'tana_river': {
        'name': 'Tana River',
        'region': 'coast',
        'coordinates': {'lat': -1.519, 'lon': 39.992},
        'bbox': [39.0, -2.5, 40.5, -0.5],
        'main_crops': ['maize', 'bananas', 'mangoes', 'livestock'],
        'population': 315943,
        'agricultural': True
    },
    
    # North Eastern
    'garissa': {
        'name': 'Garissa',
        'region': 'north_eastern',
        'coordinates': {'lat': -0.453, 'lon': 39.646},
        'bbox': [38.5, -1.6, 41.0, 1.5],
        'main_crops': ['livestock', 'maize'],
        'population': 841353,
        'agricultural': False
    },
    'mandera': {
        'name': 'Mandera',
        'region': 'north_eastern',
        'coordinates': {'lat': 3.937, 'lon': 41.867},
        'bbox': [40.5, 2.5, 42.5, 4.9],
        'main_crops': ['livestock'],
        'population': 1025756,
        'agricultural': False
    },
    'wajir': {
        'name': 'Wajir',
        'region': 'north_eastern',
        'coordinates': {'lat': 1.747, 'lon': 40.057},
        'bbox': [39.0, 0.5, 41.5, 3.5],
        'main_crops': ['livestock'],
        'population': 781263,
        'agricultural': False
    },
    
    # Nairobi
    'nairobi': {
        'name': 'Nairobi',
        'region': 'nairobi',
        'coordinates': {'lat': -1.286, 'lon': 36.817},
        'bbox': [36.6, -1.4, 37.1, -1.1],
        'main_crops': ['urban farming', 'horticulture'],
        'population': 4397073,
        'agricultural': False
    }
}

# Regional groupings
KENYA_REGIONS = {
    'central': {
        'name': 'Central Kenya',
        'counties': ['kiambu', 'kirinyaga', 'muranga', 'nyandarua', 'nyeri'],
        'coordinates': {'lat': -0.7, 'lon': 37.0}
    },
    'rift_valley': {
        'name': 'Rift Valley',
        'counties': ['baringo', 'bomet', 'elgeyo_marakwet', 'kajiado', 'kericho', 'laikipia', 
                    'nakuru', 'nandi', 'narok', 'samburu', 'trans_nzoia', 'turkana', 
                    'uasin_gishu', 'west_pokot'],
        'coordinates': {'lat': 0.2, 'lon': 35.8}
    },
    'eastern': {
        'name': 'Eastern Kenya',
        'counties': ['embu', 'isiolo', 'kitui', 'machakos', 'makueni', 'marsabit', 'meru', 'tharaka_nithi'],
        'coordinates': {'lat': -0.5, 'lon': 37.8}
    },
    'western': {
        'name': 'Western Kenya',
        'counties': ['bungoma', 'busia', 'kakamega', 'vihiga'],
        'coordinates': {'lat': 0.3, 'lon': 34.6}
    },
    'nyanza': {
        'name': 'Nyanza',
        'counties': ['homa_bay', 'kisii', 'kisumu', 'migori', 'nyamira', 'siaya'],
        'coordinates': {'lat': -0.4, 'lon': 34.5}
    },
    'coast': {
        'name': 'Coast',
        'counties': ['kilifi', 'kwale', 'lamu', 'mombasa', 'taita_taveta', 'tana_river'],
        'coordinates': {'lat': -3.5, 'lon': 39.7}
    },
    'north_eastern': {
        'name': 'North Eastern',
        'counties': ['garissa', 'mandera', 'wajir'],
        'coordinates': {'lat': 1.5, 'lon': 40.0}
    },
    'nairobi': {
        'name': 'Nairobi',
        'counties': ['nairobi'],
        'coordinates': {'lat': -1.286, 'lon': 36.817}
    }
}

# Agricultural counties (for prioritized data fetching)
AGRICULTURAL_COUNTIES = [county_id for county_id, data in KENYA_COUNTIES.items() if data['agricultural']]

def get_county_info(county_id):
    """Get information for a specific county"""
    return KENYA_COUNTIES.get(county_id)

def get_counties_in_region(region):
    """Get all counties in a region"""
    return KENYA_REGIONS.get(region, {}).get('counties', [])

def get_all_agricultural_counties():
    """Get all agricultural counties"""
    return AGRICULTURAL_COUNTIES

