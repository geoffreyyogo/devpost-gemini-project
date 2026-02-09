"""
Complete Sub-County Configuration for All 47 Kenya Counties
Based on the Kenya Constitution 2010 administrative boundaries.
Each sub-county has approximate centre coordinates and a bounding box
suitable for Google Earth Engine satellite image extraction.
"""

# fmt: off

KENYA_SUB_COUNTIES: dict[str, dict] = {

    # =========================================================================
    # CENTRAL KENYA
    # =========================================================================
    'kiambu': {
        'county_name': 'Kiambu',
        'sub_counties': {
            'gatundu_north':   {'name': 'Gatundu North',   'coordinates': {'lat': -1.03, 'lon': 36.91}, 'bbox': [36.80, -1.10, 37.00, -0.95]},
            'gatundu_south':   {'name': 'Gatundu South',   'coordinates': {'lat': -1.10, 'lon': 36.92}, 'bbox': [36.82, -1.18, 37.02, -1.03]},
            'githunguri':      {'name': 'Githunguri',      'coordinates': {'lat': -1.05, 'lon': 36.78}, 'bbox': [36.68, -1.12, 36.88, -0.98]},
            'juja':            {'name': 'Juja',            'coordinates': {'lat': -1.10, 'lon': 37.01}, 'bbox': [36.90, -1.18, 37.12, -1.02]},
            'kabete':          {'name': 'Kabete',          'coordinates': {'lat': -1.25, 'lon': 36.73}, 'bbox': [36.63, -1.32, 36.83, -1.18]},
            'kiambaa':         {'name': 'Kiambaa',         'coordinates': {'lat': -1.17, 'lon': 36.78}, 'bbox': [36.68, -1.24, 36.88, -1.10]},
            'kiambu_town':     {'name': 'Kiambu Town',     'coordinates': {'lat': -1.17, 'lon': 36.83}, 'bbox': [36.75, -1.24, 36.91, -1.10]},
            'kikuyu':          {'name': 'Kikuyu',          'coordinates': {'lat': -1.25, 'lon': 36.67}, 'bbox': [36.57, -1.32, 36.77, -1.18]},
            'lari':            {'name': 'Lari',            'coordinates': {'lat': -1.08, 'lon': 36.63}, 'bbox': [36.50, -1.20, 36.76, -0.96]},
            'limuru':          {'name': 'Limuru',          'coordinates': {'lat': -1.10, 'lon': 36.65}, 'bbox': [36.55, -1.18, 36.75, -1.02]},
            'ruiru':           {'name': 'Ruiru',           'coordinates': {'lat': -1.15, 'lon': 36.96}, 'bbox': [36.88, -1.22, 37.05, -1.08]},
            'thika_town':      {'name': 'Thika Town',      'coordinates': {'lat': -1.03, 'lon': 37.07}, 'bbox': [36.97, -1.10, 37.17, -0.96]},
        },
    },
    'kirinyaga': {
        'county_name': 'Kirinyaga',
        'sub_counties': {
            'gichugu':         {'name': 'Gichugu',         'coordinates': {'lat': -0.55, 'lon': 37.40}, 'bbox': [37.30, -0.65, 37.55, -0.45]},
            'kirinyaga_central': {'name': 'Kirinyaga Central', 'coordinates': {'lat': -0.65, 'lon': 37.35}, 'bbox': [37.25, -0.75, 37.45, -0.55]},
            'mwea':            {'name': 'Mwea',            'coordinates': {'lat': -0.75, 'lon': 37.35}, 'bbox': [37.20, -0.90, 37.50, -0.65]},
            'ndia':            {'name': 'Ndia',            'coordinates': {'lat': -0.60, 'lon': 37.28}, 'bbox': [37.18, -0.70, 37.38, -0.50]},
        },
    },
    'muranga': {
        'county_name': "Murang'a",
        'sub_counties': {
            'gatanga':         {'name': 'Gatanga',         'coordinates': {'lat': -0.90, 'lon': 37.00}, 'bbox': [36.85, -1.02, 37.15, -0.80]},
            'kahuro':          {'name': 'Kahuro',          'coordinates': {'lat': -0.72, 'lon': 37.12}, 'bbox': [37.02, -0.80, 37.22, -0.65]},
            'kandara':         {'name': 'Kandara',         'coordinates': {'lat': -0.85, 'lon': 36.95}, 'bbox': [36.82, -0.96, 37.08, -0.76]},
            'kangema':         {'name': 'Kangema',         'coordinates': {'lat': -0.68, 'lon': 36.95}, 'bbox': [36.85, -0.78, 37.05, -0.58]},
            'kigumo':          {'name': 'Kigumo',          'coordinates': {'lat': -0.78, 'lon': 36.90}, 'bbox': [36.78, -0.88, 37.02, -0.68]},
            'kiharu':          {'name': 'Kiharu',          'coordinates': {'lat': -0.72, 'lon': 37.05}, 'bbox': [36.95, -0.82, 37.15, -0.62]},
            'mathioya':        {'name': 'Mathioya',        'coordinates': {'lat': -0.65, 'lon': 36.98}, 'bbox': [36.88, -0.75, 37.08, -0.55]},
            'muranga_south':   {'name': "Murang'a South",  'coordinates': {'lat': -0.88, 'lon': 37.08}, 'bbox': [36.95, -0.98, 37.18, -0.78]},
        },
    },
    'nyandarua': {
        'county_name': 'Nyandarua',
        'sub_counties': {
            'kinangop':        {'name': 'Kinangop',        'coordinates': {'lat': -0.63, 'lon': 36.50}, 'bbox': [36.35, -0.78, 36.65, -0.50]},
            'kipipiri':        {'name': 'Kipipiri',        'coordinates': {'lat': -0.40, 'lon': 36.55}, 'bbox': [36.40, -0.55, 36.70, -0.28]},
            'ndaragwa':        {'name': 'Ndaragwa',        'coordinates': {'lat': -0.15, 'lon': 36.55}, 'bbox': [36.38, -0.30, 36.72, -0.02]},
            'ol_kalou':        {'name': 'Ol Kalou',        'coordinates': {'lat': -0.28, 'lon': 36.38}, 'bbox': [36.22, -0.42, 36.55, -0.15]},
            'ol_joro_orok':    {'name': 'Ol Joro Orok',    'coordinates': {'lat': -0.05, 'lon': 36.40}, 'bbox': [36.25, -0.18, 36.55, 0.08]},
        },
    },
    'nyeri': {
        'county_name': 'Nyeri',
        'sub_counties': {
            'kieni_east':      {'name': 'Kieni East',      'coordinates': {'lat': -0.18, 'lon': 37.00}, 'bbox': [36.85, -0.32, 37.15, -0.05]},
            'kieni_west':      {'name': 'Kieni West',      'coordinates': {'lat': -0.18, 'lon': 36.82}, 'bbox': [36.68, -0.32, 36.95, -0.05]},
            'mathira_east':    {'name': 'Mathira East',    'coordinates': {'lat': -0.40, 'lon': 37.05}, 'bbox': [36.95, -0.52, 37.15, -0.30]},
            'mathira_west':    {'name': 'Mathira West',    'coordinates': {'lat': -0.42, 'lon': 36.90}, 'bbox': [36.78, -0.54, 37.02, -0.32]},
            'mukurweini':      {'name': 'Mukurweini',      'coordinates': {'lat': -0.53, 'lon': 37.00}, 'bbox': [36.88, -0.62, 37.10, -0.44]},
            'nyeri_town':      {'name': 'Nyeri Town',      'coordinates': {'lat': -0.42, 'lon': 36.95}, 'bbox': [36.88, -0.48, 37.02, -0.36]},
            'othaya':          {'name': 'Othaya',          'coordinates': {'lat': -0.55, 'lon': 36.95}, 'bbox': [36.82, -0.65, 37.08, -0.46]},
            'tetu':            {'name': 'Tetu',            'coordinates': {'lat': -0.48, 'lon': 36.88}, 'bbox': [36.78, -0.56, 36.98, -0.40]},
        },
    },

    # =========================================================================
    # RIFT VALLEY
    # =========================================================================
    'baringo': {
        'county_name': 'Baringo',
        'sub_counties': {
            'baringo_central': {'name': 'Baringo Central', 'coordinates': {'lat': 0.50, 'lon': 35.98}, 'bbox': [35.82, 0.35, 36.15, 0.65]},
            'baringo_north':   {'name': 'Baringo North',   'coordinates': {'lat': 0.75, 'lon': 35.95}, 'bbox': [35.78, 0.58, 36.12, 0.92]},
            'baringo_south':   {'name': 'Baringo South',   'coordinates': {'lat': 0.28, 'lon': 35.85}, 'bbox': [35.68, 0.12, 36.02, 0.45]},
            'eldama_ravine':   {'name': 'Eldama Ravine',   'coordinates': {'lat': 0.05, 'lon': 35.73}, 'bbox': [35.58, -0.10, 35.88, 0.20]},
            'mogotio':         {'name': 'Mogotio',         'coordinates': {'lat': 0.08, 'lon': 36.00}, 'bbox': [35.85, -0.08, 36.15, 0.25]},
            'tiaty':           {'name': 'Tiaty',           'coordinates': {'lat': 0.90, 'lon': 36.20}, 'bbox': [35.95, 0.55, 36.45, 1.30]},
        },
    },
    'bomet': {
        'county_name': 'Bomet',
        'sub_counties': {
            'bomet_central':   {'name': 'Bomet Central',   'coordinates': {'lat': -0.78, 'lon': 35.35}, 'bbox': [35.22, -0.90, 35.48, -0.68]},
            'bomet_east':      {'name': 'Bomet East',      'coordinates': {'lat': -0.72, 'lon': 35.45}, 'bbox': [35.32, -0.85, 35.58, -0.60]},
            'chepalungu':      {'name': 'Chepalungu',      'coordinates': {'lat': -0.90, 'lon': 35.30}, 'bbox': [35.15, -1.02, 35.45, -0.78]},
            'konoin':          {'name': 'Konoin',          'coordinates': {'lat': -0.65, 'lon': 35.25}, 'bbox': [35.12, -0.78, 35.38, -0.52]},
            'sotik':           {'name': 'Sotik',           'coordinates': {'lat': -0.82, 'lon': 35.18}, 'bbox': [35.05, -0.95, 35.32, -0.70]},
        },
    },
    'elgeyo_marakwet': {
        'county_name': 'Elgeyo-Marakwet',
        'sub_counties': {
            'keiyo_north':     {'name': 'Keiyo North',     'coordinates': {'lat': 0.55, 'lon': 35.55}, 'bbox': [35.40, 0.40, 35.70, 0.70]},
            'keiyo_south':     {'name': 'Keiyo South',     'coordinates': {'lat': 0.35, 'lon': 35.52}, 'bbox': [35.38, 0.22, 35.68, 0.48]},
            'marakwet_east':   {'name': 'Marakwet East',   'coordinates': {'lat': 0.95, 'lon': 35.55}, 'bbox': [35.38, 0.78, 35.72, 1.12]},
            'marakwet_west':   {'name': 'Marakwet West',   'coordinates': {'lat': 0.90, 'lon': 35.40}, 'bbox': [35.25, 0.72, 35.55, 1.08]},
        },
    },
    'kajiado': {
        'county_name': 'Kajiado',
        'sub_counties': {
            'kajiado_central': {'name': 'Kajiado Central', 'coordinates': {'lat': -1.85, 'lon': 36.78}, 'bbox': [36.55, -2.10, 37.00, -1.60]},
            'kajiado_east':    {'name': 'Kajiado East',    'coordinates': {'lat': -1.55, 'lon': 37.05}, 'bbox': [36.80, -1.80, 37.30, -1.30]},
            'kajiado_north':   {'name': 'Kajiado North',   'coordinates': {'lat': -1.30, 'lon': 36.78}, 'bbox': [36.50, -1.55, 37.05, -1.05]},
            'kajiado_south':   {'name': 'Kajiado South',   'coordinates': {'lat': -2.50, 'lon': 36.90}, 'bbox': [36.40, -2.85, 37.40, -2.15]},
            'kajiado_west':    {'name': 'Kajiado West',    'coordinates': {'lat': -1.85, 'lon': 36.40}, 'bbox': [36.05, -2.15, 36.75, -1.55]},
        },
    },
    'kericho': {
        'county_name': 'Kericho',
        'sub_counties': {
            'ainamoi':         {'name': 'Ainamoi',         'coordinates': {'lat': -0.38, 'lon': 35.28}, 'bbox': [35.15, -0.50, 35.42, -0.26]},
            'belgut':          {'name': 'Belgut',          'coordinates': {'lat': -0.45, 'lon': 35.40}, 'bbox': [35.28, -0.58, 35.52, -0.32]},
            'bureti':          {'name': 'Bureti',          'coordinates': {'lat': -0.55, 'lon': 35.22}, 'bbox': [35.08, -0.68, 35.35, -0.42]},
            'kipkelion_east':  {'name': 'Kipkelion East',  'coordinates': {'lat': -0.25, 'lon': 35.55}, 'bbox': [35.40, -0.38, 35.70, -0.12]},
            'kipkelion_west':  {'name': 'Kipkelion West',  'coordinates': {'lat': -0.22, 'lon': 35.40}, 'bbox': [35.25, -0.35, 35.55, -0.10]},
            'sigowet_soin':    {'name': 'Sigowet/Soin',    'coordinates': {'lat': -0.35, 'lon': 35.50}, 'bbox': [35.38, -0.48, 35.62, -0.22]},
        },
    },
    'laikipia': {
        'county_name': 'Laikipia',
        'sub_counties': {
            'laikipia_east':   {'name': 'Laikipia East',   'coordinates': {'lat': 0.30, 'lon': 37.05}, 'bbox': [36.80, 0.05, 37.30, 0.55]},
            'laikipia_north':  {'name': 'Laikipia North',  'coordinates': {'lat': 0.60, 'lon': 36.85}, 'bbox': [36.55, 0.35, 37.15, 0.85]},
            'laikipia_west':   {'name': 'Laikipia West',   'coordinates': {'lat': 0.20, 'lon': 36.60}, 'bbox': [36.35, -0.05, 36.85, 0.45]},
        },
    },
    'nakuru': {
        'county_name': 'Nakuru',
        'sub_counties': {
            'bahati':          {'name': 'Bahati',          'coordinates': {'lat': -0.18, 'lon': 36.20}, 'bbox': [36.08, -0.30, 36.32, -0.05]},
            'gilgil':          {'name': 'Gilgil',          'coordinates': {'lat': -0.50, 'lon': 36.28}, 'bbox': [36.10, -0.68, 36.45, -0.32]},
            'kuresoi_north':   {'name': 'Kuresoi North',   'coordinates': {'lat': -0.18, 'lon': 35.72}, 'bbox': [35.58, -0.32, 35.88, -0.05]},
            'kuresoi_south':   {'name': 'Kuresoi South',   'coordinates': {'lat': -0.35, 'lon': 35.68}, 'bbox': [35.52, -0.50, 35.85, -0.22]},
            'molo':            {'name': 'Molo',            'coordinates': {'lat': -0.25, 'lon': 35.75}, 'bbox': [35.60, -0.38, 35.90, -0.12]},
            'naivasha':        {'name': 'Naivasha',        'coordinates': {'lat': -0.72, 'lon': 36.43}, 'bbox': [36.20, -0.95, 36.68, -0.52]},
            'nakuru_town_east': {'name': 'Nakuru Town East', 'coordinates': {'lat': -0.28, 'lon': 36.10}, 'bbox': [36.00, -0.38, 36.22, -0.18]},
            'nakuru_town_west': {'name': 'Nakuru Town West', 'coordinates': {'lat': -0.30, 'lon': 36.05}, 'bbox': [35.92, -0.40, 36.18, -0.20]},
            'njoro':           {'name': 'Njoro',           'coordinates': {'lat': -0.35, 'lon': 35.95}, 'bbox': [35.80, -0.50, 36.10, -0.20]},
            'rongai':          {'name': 'Rongai',          'coordinates': {'lat': -0.20, 'lon': 35.88}, 'bbox': [35.72, -0.35, 36.05, -0.08]},
            'subukia':         {'name': 'Subukia',         'coordinates': {'lat': -0.08, 'lon': 36.15}, 'bbox': [36.02, -0.22, 36.28, 0.05]},
        },
    },
    'nandi': {
        'county_name': 'Nandi',
        'sub_counties': {
            'aldai':           {'name': 'Aldai',           'coordinates': {'lat': 0.05, 'lon': 35.10}, 'bbox': [34.95, -0.10, 35.25, 0.20]},
            'chesumei':        {'name': 'Chesumei',        'coordinates': {'lat': 0.15, 'lon': 35.05}, 'bbox': [34.90, 0.02, 35.20, 0.28]},
            'emgwen':          {'name': 'Emgwen',          'coordinates': {'lat': 0.12, 'lon': 35.18}, 'bbox': [35.05, -0.02, 35.32, 0.25]},
            'mosop':           {'name': 'Mosop',           'coordinates': {'lat': 0.35, 'lon': 35.12}, 'bbox': [34.98, 0.22, 35.28, 0.48]},
            'nandi_hills':     {'name': 'Nandi Hills',     'coordinates': {'lat': 0.10, 'lon': 35.18}, 'bbox': [35.05, -0.05, 35.30, 0.22]},
            'tinderet':        {'name': 'Tinderet',        'coordinates': {'lat': -0.02, 'lon': 35.30}, 'bbox': [35.15, -0.15, 35.45, 0.12]},
        },
    },
    'narok': {
        'county_name': 'Narok',
        'sub_counties': {
            'emurua_dikirr':   {'name': 'Emurua Dikirr',   'coordinates': {'lat': -1.05, 'lon': 35.30}, 'bbox': [35.12, -1.22, 35.48, -0.88]},
            'kilgoris':        {'name': 'Kilgoris',        'coordinates': {'lat': -1.20, 'lon': 34.88}, 'bbox': [34.65, -1.45, 35.10, -0.95]},
            'narok_east':      {'name': 'Narok East',      'coordinates': {'lat': -0.95, 'lon': 36.10}, 'bbox': [35.85, -1.20, 36.35, -0.70]},
            'narok_north':     {'name': 'Narok North',     'coordinates': {'lat': -0.80, 'lon': 35.85}, 'bbox': [35.55, -1.05, 36.15, -0.55]},
            'narok_south':     {'name': 'Narok South',     'coordinates': {'lat': -1.50, 'lon': 35.60}, 'bbox': [35.25, -1.85, 35.95, -1.15]},
            'narok_west':      {'name': 'Narok West',      'coordinates': {'lat': -1.10, 'lon': 35.55}, 'bbox': [35.28, -1.40, 35.82, -0.82]},
        },
    },
    'samburu': {
        'county_name': 'Samburu',
        'sub_counties': {
            'samburu_central': {'name': 'Samburu Central', 'coordinates': {'lat': 1.10, 'lon': 36.70}, 'bbox': [36.45, 0.80, 36.95, 1.40]},
            'samburu_east':    {'name': 'Samburu East',    'coordinates': {'lat': 1.30, 'lon': 37.30}, 'bbox': [36.90, 0.90, 37.70, 1.70]},
            'samburu_north':   {'name': 'Samburu North',   'coordinates': {'lat': 1.80, 'lon': 36.85}, 'bbox': [36.40, 1.35, 37.30, 2.30]},
        },
    },
    'trans_nzoia': {
        'county_name': 'Trans Nzoia',
        'sub_counties': {
            'cherangany':      {'name': 'Cherangany',      'coordinates': {'lat': 1.10, 'lon': 35.10}, 'bbox': [34.95, 0.95, 35.25, 1.25]},
            'endebess':        {'name': 'Endebess',        'coordinates': {'lat': 1.15, 'lon': 34.88}, 'bbox': [34.72, 1.00, 35.05, 1.30]},
            'kiminini':        {'name': 'Kiminini',        'coordinates': {'lat': 0.90, 'lon': 34.95}, 'bbox': [34.80, 0.78, 35.12, 1.05]},
            'kwanza':          {'name': 'Kwanza',          'coordinates': {'lat': 1.20, 'lon': 34.95}, 'bbox': [34.78, 1.05, 35.12, 1.35]},
            'saboti':          {'name': 'Saboti',          'coordinates': {'lat': 1.00, 'lon': 34.82}, 'bbox': [34.68, 0.85, 34.98, 1.15]},
        },
    },
    'turkana': {
        'county_name': 'Turkana',
        'sub_counties': {
            'loima':           {'name': 'Loima',           'coordinates': {'lat': 2.90, 'lon': 35.30}, 'bbox': [34.80, 2.40, 35.80, 3.40]},
            'turkana_central': {'name': 'Turkana Central', 'coordinates': {'lat': 3.10, 'lon': 35.60}, 'bbox': [35.10, 2.60, 36.10, 3.60]},
            'turkana_east':    {'name': 'Turkana East',    'coordinates': {'lat': 2.50, 'lon': 36.30}, 'bbox': [35.80, 2.00, 36.80, 3.00]},
            'turkana_north':   {'name': 'Turkana North',   'coordinates': {'lat': 4.00, 'lon': 35.70}, 'bbox': [35.00, 3.40, 36.40, 4.70]},
            'turkana_south':   {'name': 'Turkana South',   'coordinates': {'lat': 2.00, 'lon': 35.90}, 'bbox': [35.40, 1.50, 36.40, 2.50]},
            'turkana_west':    {'name': 'Turkana West',    'coordinates': {'lat': 3.60, 'lon': 35.00}, 'bbox': [34.50, 3.00, 35.50, 4.20]},
        },
    },
    'uasin_gishu': {
        'county_name': 'Uasin Gishu',
        'sub_counties': {
            'ainabkoi':        {'name': 'Ainabkoi',        'coordinates': {'lat': 0.38, 'lon': 35.38}, 'bbox': [35.22, 0.22, 35.55, 0.55]},
            'kapseret':        {'name': 'Kapseret',        'coordinates': {'lat': 0.52, 'lon': 35.18}, 'bbox': [35.02, 0.38, 35.35, 0.68]},
            'kesses':          {'name': 'Kesses',          'coordinates': {'lat': 0.40, 'lon': 35.30}, 'bbox': [35.15, 0.25, 35.45, 0.55]},
            'moiben':          {'name': 'Moiben',          'coordinates': {'lat': 0.65, 'lon': 35.45}, 'bbox': [35.28, 0.48, 35.62, 0.82]},
            'soy':             {'name': 'Soy',             'coordinates': {'lat': 0.60, 'lon': 35.22}, 'bbox': [35.05, 0.42, 35.40, 0.78]},
            'turbo':           {'name': 'Turbo',           'coordinates': {'lat': 0.65, 'lon': 35.08}, 'bbox': [34.90, 0.48, 35.25, 0.82]},
        },
    },
    'west_pokot': {
        'county_name': 'West Pokot',
        'sub_counties': {
            'kapenguria':      {'name': 'Kapenguria',      'coordinates': {'lat': 1.24, 'lon': 35.12}, 'bbox': [34.95, 1.08, 35.30, 1.40]},
            'kacheliba':       {'name': 'Kacheliba',       'coordinates': {'lat': 1.85, 'lon': 35.05}, 'bbox': [34.80, 1.55, 35.30, 2.15]},
            'pokot_south':     {'name': 'Pokot South',     'coordinates': {'lat': 1.10, 'lon': 35.55}, 'bbox': [35.30, 0.85, 35.80, 1.35]},
            'sigor':           {'name': 'Sigor',           'coordinates': {'lat': 1.50, 'lon': 35.40}, 'bbox': [35.15, 1.20, 35.65, 1.80]},
        },
    },

    # =========================================================================
    # EASTERN KENYA
    # =========================================================================
    'embu': {
        'county_name': 'Embu',
        'sub_counties': {
            'manyatta':        {'name': 'Manyatta',        'coordinates': {'lat': -0.52, 'lon': 37.45}, 'bbox': [37.32, -0.62, 37.58, -0.42]},
            'mbeere_north':    {'name': 'Mbeere North',    'coordinates': {'lat': -0.55, 'lon': 37.60}, 'bbox': [37.45, -0.68, 37.75, -0.42]},
            'mbeere_south':    {'name': 'Mbeere South',    'coordinates': {'lat': -0.68, 'lon': 37.58}, 'bbox': [37.40, -0.82, 37.75, -0.55]},
            'runyenjes':       {'name': 'Runyenjes',       'coordinates': {'lat': -0.42, 'lon': 37.48}, 'bbox': [37.35, -0.55, 37.62, -0.30]},
        },
    },
    'isiolo': {
        'county_name': 'Isiolo',
        'sub_counties': {
            'garbatulla':      {'name': 'Garbatulla',      'coordinates': {'lat': 0.52, 'lon': 38.50}, 'bbox': [37.80, 0.00, 39.20, 1.05]},
            'isiolo_north':    {'name': 'Isiolo North',    'coordinates': {'lat': 0.80, 'lon': 37.80}, 'bbox': [37.30, 0.35, 38.30, 1.25]},
            'isiolo_south':    {'name': 'Isiolo South',    'coordinates': {'lat': 0.10, 'lon': 37.60}, 'bbox': [37.20, -0.25, 38.00, 0.45]},
        },
    },
    'kitui': {
        'county_name': 'Kitui',
        'sub_counties': {
            'kitui_central':   {'name': 'Kitui Central',   'coordinates': {'lat': -1.37, 'lon': 38.01}, 'bbox': [37.85, -1.52, 38.18, -1.22]},
            'kitui_east':      {'name': 'Kitui East',      'coordinates': {'lat': -1.30, 'lon': 38.35}, 'bbox': [38.15, -1.55, 38.55, -1.05]},
            'kitui_rural':     {'name': 'Kitui Rural',     'coordinates': {'lat': -1.42, 'lon': 38.10}, 'bbox': [37.92, -1.60, 38.28, -1.25]},
            'kitui_south':     {'name': 'Kitui South',     'coordinates': {'lat': -1.75, 'lon': 38.20}, 'bbox': [37.95, -2.00, 38.45, -1.50]},
            'kitui_west':      {'name': 'Kitui West',      'coordinates': {'lat': -1.35, 'lon': 37.78}, 'bbox': [37.55, -1.55, 38.00, -1.15]},
            'mwingi_central':  {'name': 'Mwingi Central',  'coordinates': {'lat': -0.93, 'lon': 38.05}, 'bbox': [37.85, -1.12, 38.25, -0.75]},
            'mwingi_north':    {'name': 'Mwingi North',    'coordinates': {'lat': -0.68, 'lon': 38.20}, 'bbox': [37.95, -0.90, 38.45, -0.48]},
            'mwingi_west':     {'name': 'Mwingi West',     'coordinates': {'lat': -0.85, 'lon': 37.82}, 'bbox': [37.60, -1.05, 38.05, -0.65]},
        },
    },
    'machakos': {
        'county_name': 'Machakos',
        'sub_counties': {
            'kangundo':        {'name': 'Kangundo',        'coordinates': {'lat': -1.28, 'lon': 37.38}, 'bbox': [37.25, -1.40, 37.52, -1.16]},
            'kathiani':        {'name': 'Kathiani',        'coordinates': {'lat': -1.38, 'lon': 37.18}, 'bbox': [37.05, -1.50, 37.32, -1.26]},
            'machakos_town':   {'name': 'Machakos Town',   'coordinates': {'lat': -1.52, 'lon': 37.26}, 'bbox': [37.12, -1.65, 37.40, -1.40]},
            'masinga':         {'name': 'Masinga',         'coordinates': {'lat': -0.98, 'lon': 37.58}, 'bbox': [37.38, -1.18, 37.78, -0.78]},
            'matungulu':       {'name': 'Matungulu',       'coordinates': {'lat': -1.22, 'lon': 37.42}, 'bbox': [37.28, -1.38, 37.58, -1.08]},
            'mavoko':          {'name': 'Mavoko',          'coordinates': {'lat': -1.45, 'lon': 36.98}, 'bbox': [36.82, -1.58, 37.15, -1.32]},
            'mwala':           {'name': 'Mwala',           'coordinates': {'lat': -1.35, 'lon': 37.55}, 'bbox': [37.38, -1.52, 37.72, -1.20]},
            'yatta':           {'name': 'Yatta',           'coordinates': {'lat': -1.05, 'lon': 37.45}, 'bbox': [37.25, -1.25, 37.65, -0.85]},
        },
    },
    'makueni': {
        'county_name': 'Makueni',
        'sub_counties': {
            'kaiti':           {'name': 'Kaiti',           'coordinates': {'lat': -1.78, 'lon': 37.68}, 'bbox': [37.48, -1.95, 37.88, -1.62]},
            'kibwezi_east':    {'name': 'Kibwezi East',    'coordinates': {'lat': -2.38, 'lon': 38.08}, 'bbox': [37.82, -2.60, 38.35, -2.15]},
            'kibwezi_west':    {'name': 'Kibwezi West',    'coordinates': {'lat': -2.40, 'lon': 37.72}, 'bbox': [37.45, -2.65, 37.98, -2.15]},
            'kilome':          {'name': 'Kilome',          'coordinates': {'lat': -1.82, 'lon': 37.52}, 'bbox': [37.35, -1.98, 37.70, -1.68]},
            'makueni':         {'name': 'Makueni',         'coordinates': {'lat': -2.00, 'lon': 37.58}, 'bbox': [37.38, -2.20, 37.78, -1.80]},
            'mbooni':          {'name': 'Mbooni',          'coordinates': {'lat': -1.70, 'lon': 37.42}, 'bbox': [37.25, -1.85, 37.60, -1.55]},
        },
    },
    'marsabit': {
        'county_name': 'Marsabit',
        'sub_counties': {
            'laisamis':        {'name': 'Laisamis',        'coordinates': {'lat': 1.60, 'lon': 37.80}, 'bbox': [37.00, 1.00, 38.60, 2.20]},
            'marsabit_central': {'name': 'Marsabit Central', 'coordinates': {'lat': 2.33, 'lon': 37.98}, 'bbox': [37.60, 2.00, 38.40, 2.65]},
            'moyale':          {'name': 'Moyale',          'coordinates': {'lat': 3.52, 'lon': 39.05}, 'bbox': [38.40, 3.00, 39.70, 4.00]},
            'north_horr':      {'name': 'North Horr',      'coordinates': {'lat': 3.32, 'lon': 37.08}, 'bbox': [36.40, 2.70, 37.80, 4.00]},
            'saku':            {'name': 'Saku',            'coordinates': {'lat': 2.35, 'lon': 37.95}, 'bbox': [37.65, 2.10, 38.25, 2.60]},
        },
    },
    'meru': {
        'county_name': 'Meru',
        'sub_counties': {
            'buuri':           {'name': 'Buuri',           'coordinates': {'lat': 0.12, 'lon': 37.50}, 'bbox': [37.30, -0.05, 37.70, 0.30]},
            'central_imenti':  {'name': 'Central Imenti',  'coordinates': {'lat': 0.05, 'lon': 37.65}, 'bbox': [37.50, -0.10, 37.80, 0.20]},
            'igembe_central':  {'name': 'Igembe Central',  'coordinates': {'lat': 0.22, 'lon': 37.82}, 'bbox': [37.65, 0.08, 37.98, 0.35]},
            'igembe_north':    {'name': 'Igembe North',    'coordinates': {'lat': 0.30, 'lon': 37.90}, 'bbox': [37.72, 0.15, 38.08, 0.45]},
            'igembe_south':    {'name': 'Igembe South',    'coordinates': {'lat': 0.15, 'lon': 37.78}, 'bbox': [37.60, 0.02, 37.95, 0.28]},
            'north_imenti':    {'name': 'North Imenti',    'coordinates': {'lat': 0.08, 'lon': 37.60}, 'bbox': [37.45, -0.08, 37.75, 0.22]},
            'south_imenti':    {'name': 'South Imenti',    'coordinates': {'lat': -0.02, 'lon': 37.62}, 'bbox': [37.45, -0.15, 37.78, 0.10]},
            'tigania_east':    {'name': 'Tigania East',    'coordinates': {'lat': 0.25, 'lon': 37.98}, 'bbox': [37.80, 0.10, 38.15, 0.40]},
            'tigania_west':    {'name': 'Tigania West',    'coordinates': {'lat': 0.20, 'lon': 37.85}, 'bbox': [37.68, 0.05, 38.02, 0.35]},
        },
    },
    'tharaka_nithi': {
        'county_name': 'Tharaka-Nithi',
        'sub_counties': {
            'chuka_igambang_ombe': {'name': "Chuka/Igamba Ng'ombe", 'coordinates': {'lat': -0.33, 'lon': 37.65}, 'bbox': [37.48, -0.48, 37.82, -0.18]},
            'maara':           {'name': 'Maara',           'coordinates': {'lat': -0.20, 'lon': 37.72}, 'bbox': [37.55, -0.35, 37.88, -0.05]},
            'tharaka':         {'name': 'Tharaka',         'coordinates': {'lat': -0.15, 'lon': 37.92}, 'bbox': [37.72, -0.35, 38.12, 0.05]},
        },
    },

    # =========================================================================
    # WESTERN KENYA
    # =========================================================================
    'bungoma': {
        'county_name': 'Bungoma',
        'sub_counties': {
            'bumula':          {'name': 'Bumula',          'coordinates': {'lat': 0.48, 'lon': 34.42}, 'bbox': [34.28, 0.35, 34.58, 0.62]},
            'kabuchai':        {'name': 'Kabuchai',        'coordinates': {'lat': 0.55, 'lon': 34.52}, 'bbox': [34.38, 0.42, 34.68, 0.68]},
            'kanduyi':         {'name': 'Kanduyi',         'coordinates': {'lat': 0.56, 'lon': 34.56}, 'bbox': [34.42, 0.44, 34.70, 0.68]},
            'kimilili':        {'name': 'Kimilili',        'coordinates': {'lat': 0.72, 'lon': 34.72}, 'bbox': [34.58, 0.58, 34.85, 0.85]},
            'mt_elgon':        {'name': 'Mt. Elgon',       'coordinates': {'lat': 0.85, 'lon': 34.55}, 'bbox': [34.38, 0.68, 34.72, 1.02]},
            'sirisia':         {'name': 'Sirisia',         'coordinates': {'lat': 0.68, 'lon': 34.50}, 'bbox': [34.35, 0.55, 34.65, 0.82]},
            'tongaren':        {'name': 'Tongaren',        'coordinates': {'lat': 0.62, 'lon': 34.68}, 'bbox': [34.52, 0.48, 34.82, 0.75]},
            'webuye_east':     {'name': 'Webuye East',     'coordinates': {'lat': 0.58, 'lon': 34.78}, 'bbox': [34.65, 0.45, 34.90, 0.70]},
            'webuye_west':     {'name': 'Webuye West',     'coordinates': {'lat': 0.55, 'lon': 34.72}, 'bbox': [34.58, 0.42, 34.85, 0.68]},
        },
    },
    'busia': {
        'county_name': 'Busia',
        'sub_counties': {
            'budalangi':       {'name': 'Budalangi',       'coordinates': {'lat': 0.12, 'lon': 34.00}, 'bbox': [33.82, -0.02, 34.18, 0.25]},
            'butula':          {'name': 'Butula',          'coordinates': {'lat': 0.32, 'lon': 34.30}, 'bbox': [34.15, 0.18, 34.45, 0.45]},
            'funyula':         {'name': 'Funyula',         'coordinates': {'lat': 0.20, 'lon': 34.08}, 'bbox': [33.90, 0.05, 34.25, 0.35]},
            'matayos':         {'name': 'Matayos',         'coordinates': {'lat': 0.35, 'lon': 34.15}, 'bbox': [34.00, 0.22, 34.30, 0.48]},
            'nambale':         {'name': 'Nambale',         'coordinates': {'lat': 0.47, 'lon': 34.22}, 'bbox': [34.08, 0.33, 34.38, 0.60]},
            'teso_north':      {'name': 'Teso North',      'coordinates': {'lat': 0.55, 'lon': 34.25}, 'bbox': [34.10, 0.42, 34.40, 0.68]},
            'teso_south':      {'name': 'Teso South',      'coordinates': {'lat': 0.48, 'lon': 34.18}, 'bbox': [34.02, 0.35, 34.35, 0.62]},
        },
    },
    'kakamega': {
        'county_name': 'Kakamega',
        'sub_counties': {
            'butere':          {'name': 'Butere',          'coordinates': {'lat': 0.20, 'lon': 34.55}, 'bbox': [34.40, 0.08, 34.70, 0.32]},
            'ikolomani':       {'name': 'Ikolomani',       'coordinates': {'lat': 0.18, 'lon': 34.72}, 'bbox': [34.58, 0.05, 34.85, 0.30]},
            'khwisero':        {'name': 'Khwisero',        'coordinates': {'lat': 0.12, 'lon': 34.60}, 'bbox': [34.45, -0.02, 34.75, 0.25]},
            'likuyani':        {'name': 'Likuyani',        'coordinates': {'lat': 0.42, 'lon': 34.85}, 'bbox': [34.70, 0.28, 35.00, 0.55]},
            'lugari':          {'name': 'Lugari',          'coordinates': {'lat': 0.48, 'lon': 34.90}, 'bbox': [34.75, 0.35, 35.05, 0.62]},
            'lurambi':         {'name': 'Lurambi',         'coordinates': {'lat': 0.28, 'lon': 34.75}, 'bbox': [34.62, 0.15, 34.88, 0.42]},
            'malava':          {'name': 'Malava',          'coordinates': {'lat': 0.38, 'lon': 34.82}, 'bbox': [34.68, 0.25, 34.95, 0.52]},
            'matungu':         {'name': 'Matungu',         'coordinates': {'lat': 0.15, 'lon': 34.48}, 'bbox': [34.32, 0.02, 34.62, 0.28]},
            'mumias_east':     {'name': 'Mumias East',     'coordinates': {'lat': 0.35, 'lon': 34.55}, 'bbox': [34.40, 0.22, 34.70, 0.48]},
            'mumias_west':     {'name': 'Mumias West',     'coordinates': {'lat': 0.33, 'lon': 34.48}, 'bbox': [34.32, 0.20, 34.62, 0.46]},
            'navakholo':       {'name': 'Navakholo',       'coordinates': {'lat': 0.25, 'lon': 34.68}, 'bbox': [34.55, 0.12, 34.82, 0.38]},
            'shinyalu':        {'name': 'Shinyalu',        'coordinates': {'lat': 0.22, 'lon': 34.80}, 'bbox': [34.65, 0.08, 34.92, 0.35]},
        },
    },
    'vihiga': {
        'county_name': 'Vihiga',
        'sub_counties': {
            'emuhaya':         {'name': 'Emuhaya',         'coordinates': {'lat': 0.08, 'lon': 34.65}, 'bbox': [34.52, -0.05, 34.78, 0.20]},
            'hamisi':          {'name': 'Hamisi',          'coordinates': {'lat': 0.05, 'lon': 34.78}, 'bbox': [34.65, -0.08, 34.90, 0.18]},
            'luanda':          {'name': 'Luanda',          'coordinates': {'lat': 0.10, 'lon': 34.58}, 'bbox': [34.45, -0.02, 34.72, 0.22]},
            'sabatia':         {'name': 'Sabatia',         'coordinates': {'lat': 0.12, 'lon': 34.72}, 'bbox': [34.58, -0.02, 34.85, 0.25]},
            'vihiga':          {'name': 'Vihiga',          'coordinates': {'lat': 0.05, 'lon': 34.70}, 'bbox': [34.58, -0.08, 34.82, 0.18]},
        },
    },

    # =========================================================================
    # NYANZA
    # =========================================================================
    'homa_bay': {
        'county_name': 'Homa Bay',
        'sub_counties': {
            'homa_bay_town':   {'name': 'Homa Bay Town',   'coordinates': {'lat': -0.52, 'lon': 34.46}, 'bbox': [34.32, -0.62, 34.60, -0.42]},
            'kabondo_kasipul': {'name': 'Kabondo Kasipul', 'coordinates': {'lat': -0.58, 'lon': 34.62}, 'bbox': [34.48, -0.70, 34.78, -0.48]},
            'karachuonyo':     {'name': 'Karachuonyo',     'coordinates': {'lat': -0.40, 'lon': 34.55}, 'bbox': [34.38, -0.55, 34.72, -0.28]},
            'kasipul':         {'name': 'Kasipul',         'coordinates': {'lat': -0.62, 'lon': 34.50}, 'bbox': [34.35, -0.75, 34.65, -0.50]},
            'mbita':           {'name': 'Mbita',           'coordinates': {'lat': -0.42, 'lon': 34.18}, 'bbox': [34.02, -0.55, 34.35, -0.30]},
            'ndhiwa':          {'name': 'Ndhiwa',          'coordinates': {'lat': -0.72, 'lon': 34.38}, 'bbox': [34.20, -0.88, 34.55, -0.58]},
            'rangwe':          {'name': 'Rangwe',          'coordinates': {'lat': -0.55, 'lon': 34.52}, 'bbox': [34.38, -0.68, 34.65, -0.42]},
            'suba_north':      {'name': 'Suba North',      'coordinates': {'lat': -0.48, 'lon': 34.22}, 'bbox': [34.05, -0.60, 34.40, -0.35]},
        },
    },
    'kisii': {
        'county_name': 'Kisii',
        'sub_counties': {
            'bobasi':          {'name': 'Bobasi',          'coordinates': {'lat': -0.80, 'lon': 34.80}, 'bbox': [34.65, -0.92, 34.95, -0.68]},
            'bomachoge_borabu': {'name': 'Bomachoge Borabu', 'coordinates': {'lat': -0.78, 'lon': 34.90}, 'bbox': [34.78, -0.90, 35.02, -0.66]},
            'bomachoge_chache': {'name': 'Bomachoge Chache', 'coordinates': {'lat': -0.72, 'lon': 34.82}, 'bbox': [34.68, -0.85, 34.95, -0.60]},
            'bonchari':        {'name': 'Bonchari',        'coordinates': {'lat': -0.70, 'lon': 34.75}, 'bbox': [34.62, -0.82, 34.88, -0.58]},
            'kitutu_chache_north': {'name': 'Kitutu Chache North', 'coordinates': {'lat': -0.65, 'lon': 34.80}, 'bbox': [34.68, -0.78, 34.92, -0.52]},
            'kitutu_chache_south': {'name': 'Kitutu Chache South', 'coordinates': {'lat': -0.68, 'lon': 34.78}, 'bbox': [34.65, -0.80, 34.90, -0.55]},
            'nyaribari_chache': {'name': 'Nyaribari Chache', 'coordinates': {'lat': -0.73, 'lon': 34.72}, 'bbox': [34.58, -0.85, 34.85, -0.62]},
            'nyaribari_masaba': {'name': 'Nyaribari Masaba', 'coordinates': {'lat': -0.65, 'lon': 34.88}, 'bbox': [34.75, -0.78, 35.00, -0.52]},
            'south_mugirango': {'name': 'South Mugirango', 'coordinates': {'lat': -0.82, 'lon': 34.88}, 'bbox': [34.72, -0.95, 35.05, -0.70]},
        },
    },
    'kisumu': {
        'county_name': 'Kisumu',
        'sub_counties': {
            'kisumu_central':  {'name': 'Kisumu Central',  'coordinates': {'lat': -0.09, 'lon': 34.77}, 'bbox': [34.65, -0.18, 34.88, 0.00]},
            'kisumu_east':     {'name': 'Kisumu East',     'coordinates': {'lat': -0.05, 'lon': 34.85}, 'bbox': [34.72, -0.18, 34.98, 0.08]},
            'kisumu_west':     {'name': 'Kisumu West',     'coordinates': {'lat': -0.12, 'lon': 34.68}, 'bbox': [34.52, -0.25, 34.82, 0.00]},
            'muhoroni':        {'name': 'Muhoroni',        'coordinates': {'lat': -0.15, 'lon': 35.05}, 'bbox': [34.88, -0.30, 35.22, 0.00]},
            'nyakach':         {'name': 'Nyakach',         'coordinates': {'lat': -0.30, 'lon': 34.82}, 'bbox': [34.65, -0.45, 34.98, -0.18]},
            'nyando':          {'name': 'Nyando',          'coordinates': {'lat': -0.15, 'lon': 34.95}, 'bbox': [34.80, -0.28, 35.10, -0.02]},
            'seme':            {'name': 'Seme',            'coordinates': {'lat': -0.10, 'lon': 34.55}, 'bbox': [34.40, -0.22, 34.70, 0.02]},
        },
    },
    'migori': {
        'county_name': 'Migori',
        'sub_counties': {
            'awendo':          {'name': 'Awendo',          'coordinates': {'lat': -0.98, 'lon': 34.55}, 'bbox': [34.40, -1.12, 34.70, -0.85]},
            'kuria_east':      {'name': 'Kuria East',      'coordinates': {'lat': -1.15, 'lon': 34.68}, 'bbox': [34.52, -1.30, 34.82, -1.00]},
            'kuria_west':      {'name': 'Kuria West',      'coordinates': {'lat': -1.12, 'lon': 34.52}, 'bbox': [34.35, -1.28, 34.68, -0.98]},
            'nyatike':         {'name': 'Nyatike',         'coordinates': {'lat': -0.90, 'lon': 34.22}, 'bbox': [34.05, -1.05, 34.40, -0.75]},
            'rongo':           {'name': 'Rongo',           'coordinates': {'lat': -0.80, 'lon': 34.58}, 'bbox': [34.42, -0.95, 34.72, -0.68]},
            'suna_east':       {'name': 'Suna East',       'coordinates': {'lat': -1.05, 'lon': 34.42}, 'bbox': [34.25, -1.20, 34.58, -0.90]},
            'suna_west':       {'name': 'Suna West',       'coordinates': {'lat': -1.03, 'lon': 34.30}, 'bbox': [34.12, -1.18, 34.48, -0.88]},
            'uriri':           {'name': 'Uriri',           'coordinates': {'lat': -0.92, 'lon': 34.48}, 'bbox': [34.32, -1.05, 34.62, -0.78]},
        },
    },
    'nyamira': {
        'county_name': 'Nyamira',
        'sub_counties': {
            'borabu':          {'name': 'Borabu',          'coordinates': {'lat': -0.62, 'lon': 35.05}, 'bbox': [34.90, -0.78, 35.20, -0.48]},
            'manga':           {'name': 'Manga',           'coordinates': {'lat': -0.55, 'lon': 34.92}, 'bbox': [34.78, -0.68, 35.08, -0.42]},
            'masaba_north':    {'name': 'Masaba North',    'coordinates': {'lat': -0.58, 'lon': 34.98}, 'bbox': [34.82, -0.72, 35.15, -0.45]},
            'nyamira_north':   {'name': 'Nyamira North',   'coordinates': {'lat': -0.55, 'lon': 34.88}, 'bbox': [34.72, -0.68, 35.02, -0.42]},
            'nyamira_south':   {'name': 'Nyamira South',   'coordinates': {'lat': -0.62, 'lon': 34.88}, 'bbox': [34.72, -0.75, 35.05, -0.50]},
        },
    },
    'siaya': {
        'county_name': 'Siaya',
        'sub_counties': {
            'alego_usonga':    {'name': 'Alego Usonga',    'coordinates': {'lat': 0.05, 'lon': 34.30}, 'bbox': [34.12, -0.10, 34.48, 0.20]},
            'bondo':           {'name': 'Bondo',           'coordinates': {'lat': -0.10, 'lon': 34.28}, 'bbox': [34.08, -0.25, 34.48, 0.05]},
            'gem':             {'name': 'Gem',             'coordinates': {'lat': 0.02, 'lon': 34.42}, 'bbox': [34.25, -0.12, 34.58, 0.18]},
            'rarieda':         {'name': 'Rarieda',         'coordinates': {'lat': -0.15, 'lon': 34.18}, 'bbox': [34.00, -0.28, 34.35, -0.02]},
            'ugenya':          {'name': 'Ugenya',          'coordinates': {'lat': 0.12, 'lon': 34.28}, 'bbox': [34.10, -0.02, 34.45, 0.25]},
            'ugunja':          {'name': 'Ugunja',          'coordinates': {'lat': 0.15, 'lon': 34.32}, 'bbox': [34.18, 0.02, 34.48, 0.28]},
        },
    },

    # =========================================================================
    # COAST
    # =========================================================================
    'kilifi': {
        'county_name': 'Kilifi',
        'sub_counties': {
            'ganze':           {'name': 'Ganze',           'coordinates': {'lat': -3.45, 'lon': 39.55}, 'bbox': [39.30, -3.70, 39.80, -3.20]},
            'kaloleni':        {'name': 'Kaloleni',        'coordinates': {'lat': -3.72, 'lon': 39.72}, 'bbox': [39.55, -3.88, 39.88, -3.55]},
            'kilifi_north':    {'name': 'Kilifi North',    'coordinates': {'lat': -3.50, 'lon': 39.85}, 'bbox': [39.65, -3.70, 40.05, -3.30]},
            'kilifi_south':    {'name': 'Kilifi South',    'coordinates': {'lat': -3.75, 'lon': 39.85}, 'bbox': [39.65, -3.95, 40.05, -3.55]},
            'magarini':        {'name': 'Magarini',        'coordinates': {'lat': -3.15, 'lon': 39.95}, 'bbox': [39.70, -3.40, 40.20, -2.90]},
            'malindi':         {'name': 'Malindi',         'coordinates': {'lat': -3.22, 'lon': 40.12}, 'bbox': [39.90, -3.42, 40.30, -3.02]},
            'rabai':           {'name': 'Rabai',           'coordinates': {'lat': -3.88, 'lon': 39.62}, 'bbox': [39.48, -4.02, 39.78, -3.75]},
        },
    },
    'kwale': {
        'county_name': 'Kwale',
        'sub_counties': {
            'kinango':         {'name': 'Kinango',         'coordinates': {'lat': -4.15, 'lon': 39.32}, 'bbox': [39.05, -4.40, 39.58, -3.90]},
            'lunga_lunga':     {'name': 'Lunga Lunga',     'coordinates': {'lat': -4.50, 'lon': 39.45}, 'bbox': [39.18, -4.70, 39.72, -4.30]},
            'matuga':          {'name': 'Matuga',          'coordinates': {'lat': -4.12, 'lon': 39.55}, 'bbox': [39.35, -4.30, 39.75, -3.95]},
            'msambweni':       {'name': 'Msambweni',       'coordinates': {'lat': -4.45, 'lon': 39.52}, 'bbox': [39.28, -4.65, 39.75, -4.25]},
        },
    },
    'lamu': {
        'county_name': 'Lamu',
        'sub_counties': {
            'lamu_east':       {'name': 'Lamu East',       'coordinates': {'lat': -2.05, 'lon': 41.10}, 'bbox': [40.70, -2.40, 41.50, -1.70]},
            'lamu_west':       {'name': 'Lamu West',       'coordinates': {'lat': -2.30, 'lon': 40.65}, 'bbox': [40.20, -2.65, 41.10, -1.95]},
        },
    },
    'mombasa': {
        'county_name': 'Mombasa',
        'sub_counties': {
            'changamwe':       {'name': 'Changamwe',       'coordinates': {'lat': -4.03, 'lon': 39.63}, 'bbox': [39.55, -4.10, 39.72, -3.95]},
            'jomvu':           {'name': 'Jomvu',           'coordinates': {'lat': -4.00, 'lon': 39.65}, 'bbox': [39.58, -4.08, 39.72, -3.92]},
            'kisauni':         {'name': 'Kisauni',         'coordinates': {'lat': -3.98, 'lon': 39.72}, 'bbox': [39.65, -4.08, 39.80, -3.90]},
            'likoni':          {'name': 'Likoni',          'coordinates': {'lat': -4.08, 'lon': 39.65}, 'bbox': [39.58, -4.15, 39.72, -4.00]},
            'mvita':           {'name': 'Mvita',           'coordinates': {'lat': -4.05, 'lon': 39.67}, 'bbox': [39.60, -4.12, 39.75, -3.98]},
            'nyali':           {'name': 'Nyali',           'coordinates': {'lat': -4.02, 'lon': 39.70}, 'bbox': [39.62, -4.10, 39.78, -3.95]},
        },
    },
    'taita_taveta': {
        'county_name': 'Taita-Taveta',
        'sub_counties': {
            'mwatate':         {'name': 'Mwatate',         'coordinates': {'lat': -3.50, 'lon': 38.38}, 'bbox': [38.15, -3.72, 38.62, -3.28]},
            'taveta':          {'name': 'Taveta',          'coordinates': {'lat': -3.40, 'lon': 37.68}, 'bbox': [37.40, -3.68, 37.98, -3.15]},
            'voi':             {'name': 'Voi',             'coordinates': {'lat': -3.38, 'lon': 38.55}, 'bbox': [38.28, -3.62, 38.82, -3.15]},
            'wundanyi':        {'name': 'Wundanyi',        'coordinates': {'lat': -3.40, 'lon': 38.35}, 'bbox': [38.18, -3.58, 38.52, -3.22]},
        },
    },
    'tana_river': {
        'county_name': 'Tana River',
        'sub_counties': {
            'bura':            {'name': 'Bura',            'coordinates': {'lat': -1.10, 'lon': 39.92}, 'bbox': [39.55, -1.50, 40.30, -0.70]},
            'galole':          {'name': 'Galole',          'coordinates': {'lat': -1.68, 'lon': 40.10}, 'bbox': [39.65, -2.10, 40.55, -1.25]},
            'garsen':          {'name': 'Garsen',          'coordinates': {'lat': -2.28, 'lon': 40.12}, 'bbox': [39.65, -2.70, 40.60, -1.88]},
        },
    },

    # =========================================================================
    # NORTH EASTERN
    # =========================================================================
    'garissa': {
        'county_name': 'Garissa',
        'sub_counties': {
            'balambala':       {'name': 'Balambala',       'coordinates': {'lat': 0.05, 'lon': 39.60}, 'bbox': [39.10, -0.40, 40.10, 0.50]},
            'dadaab':          {'name': 'Dadaab',          'coordinates': {'lat': 0.08, 'lon': 40.35}, 'bbox': [39.80, -0.40, 40.90, 0.55]},
            'fafi':            {'name': 'Fafi',            'coordinates': {'lat': -0.50, 'lon': 40.20}, 'bbox': [39.70, -1.00, 40.70, 0.00]},
            'garissa_township': {'name': 'Garissa Township', 'coordinates': {'lat': -0.45, 'lon': 39.65}, 'bbox': [39.40, -0.70, 39.90, -0.20]},
            'hulugho':         {'name': 'Hulugho',         'coordinates': {'lat': -1.02, 'lon': 40.28}, 'bbox': [39.78, -1.50, 40.78, -0.55]},
            'ijara':           {'name': 'Ijara',           'coordinates': {'lat': -1.55, 'lon': 40.52}, 'bbox': [40.00, -2.00, 41.00, -1.10]},
            'lagdera':         {'name': 'Lagdera',         'coordinates': {'lat': 0.55, 'lon': 39.75}, 'bbox': [39.25, 0.10, 40.25, 1.00]},
        },
    },
    'mandera': {
        'county_name': 'Mandera',
        'sub_counties': {
            'banissa':         {'name': 'Banissa',         'coordinates': {'lat': 3.70, 'lon': 40.98}, 'bbox': [40.50, 3.30, 41.45, 4.10]},
            'kutulo':          {'name': 'Kutulo',          'coordinates': {'lat': 3.30, 'lon': 41.40}, 'bbox': [40.90, 2.90, 41.90, 3.70]},
            'lafey':           {'name': 'Lafey',           'coordinates': {'lat': 2.85, 'lon': 41.55}, 'bbox': [41.05, 2.50, 42.05, 3.20]},
            'mandera_east':    {'name': 'Mandera East',    'coordinates': {'lat': 3.92, 'lon': 41.85}, 'bbox': [41.40, 3.55, 42.30, 4.30]},
            'mandera_north':   {'name': 'Mandera North',   'coordinates': {'lat': 4.20, 'lon': 41.50}, 'bbox': [41.00, 3.80, 42.00, 4.60]},
            'mandera_south':   {'name': 'Mandera South',   'coordinates': {'lat': 3.40, 'lon': 41.20}, 'bbox': [40.70, 3.00, 41.70, 3.80]},
        },
    },
    'wajir': {
        'county_name': 'Wajir',
        'sub_counties': {
            'eldas':           {'name': 'Eldas',           'coordinates': {'lat': 2.20, 'lon': 39.65}, 'bbox': [39.15, 1.75, 40.15, 2.65]},
            'tarbaj':          {'name': 'Tarbaj',          'coordinates': {'lat': 1.58, 'lon': 39.82}, 'bbox': [39.32, 1.15, 40.32, 2.02]},
            'wajir_east':      {'name': 'Wajir East',      'coordinates': {'lat': 1.60, 'lon': 40.45}, 'bbox': [39.95, 1.15, 40.95, 2.05]},
            'wajir_north':     {'name': 'Wajir North',     'coordinates': {'lat': 2.55, 'lon': 40.35}, 'bbox': [39.80, 2.05, 40.90, 3.05]},
            'wajir_south':     {'name': 'Wajir South',     'coordinates': {'lat': 0.85, 'lon': 40.15}, 'bbox': [39.60, 0.40, 40.70, 1.30]},
            'wajir_west':      {'name': 'Wajir West',      'coordinates': {'lat': 1.75, 'lon': 39.50}, 'bbox': [39.00, 1.30, 40.00, 2.20]},
        },
    },

    # =========================================================================
    # NAIROBI
    # =========================================================================
    'nairobi': {
        'county_name': 'Nairobi',
        'sub_counties': {
            'dagoretti_north': {'name': 'Dagoretti North', 'coordinates': {'lat': -1.27, 'lon': 36.74}, 'bbox': [36.68, -1.32, 36.80, -1.22]},
            'dagoretti_south': {'name': 'Dagoretti South', 'coordinates': {'lat': -1.30, 'lon': 36.73}, 'bbox': [36.67, -1.35, 36.79, -1.25]},
            'embakasi_central': {'name': 'Embakasi Central', 'coordinates': {'lat': -1.32, 'lon': 36.90}, 'bbox': [36.84, -1.37, 36.96, -1.27]},
            'embakasi_east':   {'name': 'Embakasi East',   'coordinates': {'lat': -1.30, 'lon': 36.95}, 'bbox': [36.88, -1.36, 37.02, -1.24]},
            'embakasi_north':  {'name': 'Embakasi North',  'coordinates': {'lat': -1.28, 'lon': 36.90}, 'bbox': [36.84, -1.33, 36.96, -1.23]},
            'embakasi_south':  {'name': 'Embakasi South',  'coordinates': {'lat': -1.35, 'lon': 36.92}, 'bbox': [36.85, -1.40, 36.98, -1.30]},
            'embakasi_west':   {'name': 'Embakasi West',   'coordinates': {'lat': -1.30, 'lon': 36.87}, 'bbox': [36.80, -1.36, 36.94, -1.24]},
            'kamukunji':       {'name': 'Kamukunji',       'coordinates': {'lat': -1.28, 'lon': 36.85}, 'bbox': [36.80, -1.32, 36.90, -1.24]},
            'kasarani':        {'name': 'Kasarani',        'coordinates': {'lat': -1.22, 'lon': 36.90}, 'bbox': [36.84, -1.28, 36.96, -1.16]},
            'kibra':           {'name': 'Kibra',           'coordinates': {'lat': -1.32, 'lon': 36.78}, 'bbox': [36.72, -1.37, 36.84, -1.27]},
            'langata':         {'name': 'Langata',         'coordinates': {'lat': -1.35, 'lon': 36.75}, 'bbox': [36.68, -1.42, 36.82, -1.28]},
            'makadara':        {'name': 'Makadara',        'coordinates': {'lat': -1.30, 'lon': 36.88}, 'bbox': [36.82, -1.35, 36.94, -1.25]},
            'mathare':         {'name': 'Mathare',         'coordinates': {'lat': -1.26, 'lon': 36.86}, 'bbox': [36.82, -1.30, 36.90, -1.22]},
            'roysambu':        {'name': 'Roysambu',        'coordinates': {'lat': -1.22, 'lon': 36.88}, 'bbox': [36.82, -1.28, 36.94, -1.16]},
            'ruaraka':         {'name': 'Ruaraka',         'coordinates': {'lat': -1.24, 'lon': 36.88}, 'bbox': [36.82, -1.28, 36.94, -1.20]},
            'starehe':         {'name': 'Starehe',         'coordinates': {'lat': -1.28, 'lon': 36.82}, 'bbox': [36.78, -1.32, 36.86, -1.24]},
            'westlands':       {'name': 'Westlands',       'coordinates': {'lat': -1.25, 'lon': 36.80}, 'bbox': [36.74, -1.30, 36.86, -1.20]},
        },
    },
}

# fmt: on


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_sub_counties(county_id: str) -> dict:
    """Return sub-county dict for a given county, or empty dict."""
    entry = KENYA_SUB_COUNTIES.get(county_id)
    return entry["sub_counties"] if entry else {}


def get_sub_county_info(county_id: str, sub_county_id: str) -> dict | None:
    """Return info for a specific sub-county, or None."""
    subs = get_sub_counties(county_id)
    return subs.get(sub_county_id)


def get_sub_county_bbox(county_id: str, sub_county_id: str) -> list | None:
    """Return [west, south, east, north] bbox for GEE queries."""
    info = get_sub_county_info(county_id, sub_county_id)
    return info["bbox"] if info else None


def get_all_sub_county_ids(county_id: str) -> list[str]:
    """Return list of sub-county keys for a county."""
    return list(get_sub_counties(county_id).keys())


def get_all_sub_counties_flat() -> list[dict]:
    """Return a flat list of all sub-counties with county context included."""
    result = []
    for county_id, county_data in KENYA_SUB_COUNTIES.items():
        for sc_id, sc_info in county_data["sub_counties"].items():
            result.append({
                "county_id": county_id,
                "county_name": county_data["county_name"],
                "sub_county_id": sc_id,
                **sc_info,
            })
    return result


def search_sub_county(name: str) -> list[dict]:
    """Fuzzy text search across all sub-county names (case-insensitive)."""
    name_lower = name.lower()
    matches = []
    for county_id, county_data in KENYA_SUB_COUNTIES.items():
        for sc_id, sc_info in county_data["sub_counties"].items():
            if name_lower in sc_info["name"].lower() or name_lower in sc_id:
                matches.append({
                    "county_id": county_id,
                    "county_name": county_data["county_name"],
                    "sub_county_id": sc_id,
                    **sc_info,
                })
    return matches


def count_sub_counties() -> dict:
    """Return {county_id: count} for reporting."""
    return {cid: len(cd["sub_counties"]) for cid, cd in KENYA_SUB_COUNTIES.items()}


def total_sub_counties() -> int:
    """Return total number of sub-counties."""
    return sum(len(cd["sub_counties"]) for cd in KENYA_SUB_COUNTIES.values())
