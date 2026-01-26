"""
Utility functions for populating checklist configuration.
"""
from .models import VisualChecklistConfig

# Hardcoded data from frontend (LIGHT vehicles)
LIGHT_ZONES = [
    {
        'id': 'zone1',
        'titleAm': 'ማንነት እና ሰነዶች',
        'titleEn': 'Zone 1: Identification & Documentation',
        'items': [
            { 'id': 1, 'am': 'የሰሌዳ ቁጥር ትክክለኛነት', 'en': 'Registration Plate Validity', 'points': 5 },
            { 'id': 2, 'am': 'የቻሲስ ቁጥር ማዛመድ', 'en': 'Chassis Number Match', 'points': 5 },
            { 'id': 3, 'am': 'የሞተር ቁጥር ማዛመድ', 'en': 'Engine Number Match', 'points': 5 },
            { 'id': 4, 'am': 'የባለቤትነት ማረጋገጫ', 'en': 'Title Certificate Check', 'points': 5 },
        ],
    },
    {
        'id': 'zone2',
        'titleAm': 'ብርሃን እና እይታ',
        'titleEn': 'Zone 2: Visibility & Lighting',
        'items': [
            { 'id': 5, 'am': 'የፊት መብራቶች (ከፍተኛ/ዝቅተኛ)', 'en': 'Headlights (High/Low)', 'points': 4 },
            { 'id': 6, 'am': 'የምልክት መብራቶች', 'en': 'Signal Lights', 'points': 3 },
            { 'id': 7, 'am': 'የብሬክ መብራቶች', 'en': 'Brake Lights', 'points': 4 },
            { 'id': 8, 'am': 'የኋላ መብራቶች', 'en': 'Reverse Lights', 'points': 2 },
            { 'id': 9, 'am': 'ዋይፐር እና ማጠቢያ', 'en': 'Wipers & Washers', 'points': 3 },
            { 'id': 10, 'am': 'የንፋስ መከላከያ ሁኔታ', 'en': 'Windshield Condition', 'points': 4 },
            { 'id': 11, 'am': 'የጎን/ኋላ መስተዋቶች', 'en': 'Side/Rear Mirrors', 'points': 3 },
        ],
    },
    {
        'id': 'zone3',
        'titleAm': 'መሪ እና ሳስፔንሽን',
        'titleEn': 'Zone 3: Steering & Suspension',
        'items': [
            { 'id': 12, 'am': 'የመሪ ጨዋታ', 'en': 'Steering Play', 'points': 5 },
            { 'id': 13, 'am': 'የደወል ተግባር', 'en': 'Horn Function', 'points': 2 },
            { 'id': 14, 'am': 'ሾክ አብሶርበሮች', 'en': 'Shock Absorbers', 'points': 4 },
            { 'id': 15, 'am': 'ሊፍ ስፕሪንግስ/ሳስፔንሽን', 'en': 'Leaf Springs/Suspension', 'points': 4 },
            { 'id': 16, 'am': 'የጎማ ሁኔታ', 'en': 'Tire Tread/Condition', 'points': 5 },
            { 'id': 17, 'am': 'የዊል ነትስ/ስታድስ', 'en': 'Wheel Nuts/Studs', 'points': 3 },
        ],
    },
    {
        'id': 'zone4',
        'titleAm': 'ሰውነት እና ውስጥ',
        'titleEn': 'Zone 4: Body & Interior',
        'items': [
            { 'id': 18, 'am': 'የበር ሜካኒዝም', 'en': 'Door Mechanisms', 'points': 3 },
            { 'id': 19, 'am': 'የመስኮት ስራዎች', 'en': 'Window Operations', 'points': 2 },
            { 'id': 20, 'am': 'የመቀመጫ ሁኔታዎች', 'en': 'Seat Conditions', 'points': 3 },
            { 'id': 21, 'am': 'የደህንነት ቀበቶዎች', 'en': 'Seat Belts', 'points': 4 },
            { 'id': 22, 'am': 'የወለል/ሰውነት ዝገት', 'en': 'Floor/Body Corrosion', 'points': 3 },
            { 'id': 23, 'am': 'የጭስ ማስወጫ ስርዓት', 'en': 'Exhaust System', 'points': 3 },
            { 'id': 24, 'am': 'የነዳጅ ታንክ ክዳን/ፍሳሽ', 'en': 'Fuel Tank Cap/Leak', 'points': 4 },
            { 'id': 25, 'am': 'የባምፐር ሁኔታ', 'en': 'Bumper Condition', 'points': 2 },
        ],
    },
    {
        'id': 'zone5',
        'titleAm': 'የደህንነት መሳሪያዎች',
        'titleEn': 'Zone 5: Safety Equipment',
        'items': [
            { 'id': 26, 'am': 'የእሳት ማጥፊያ', 'en': 'Fire Extinguisher', 'points': 3 },
            { 'id': 27, 'am': 'የመጀመሪያ እርዳታ ኪት', 'en': 'First Aid Kit', 'points': 2 },
            { 'id': 28, 'am': 'የማስጠንቀቂያ ትሪያንግል', 'en': 'Warning Triangle', 'points': 2 },
            { 'id': 29, 'am': 'ተጠባባቂ ጎማ', 'en': 'Spare Wheel', 'points': 3 },
            { 'id': 30, 'am': 'ጭቃ መከላከያዎች', 'en': 'Mudguards', 'points': 2 },
        ],
    },
]

# Hardcoded data from frontend (HEAVY vehicles)
HEAVY_ZONES = [
    {
        'id': 'zone1',
        'titleAm': 'ማንነት እና ሰነዶች',
        'titleEn': 'Zone 1: Identification & Documentation',
        'items': [
            { 'id': 1, 'am': 'የሰሌዳ ቁጥር ትክክለኛነት', 'en': 'Registration Plate Validity', 'points': 8 },
            { 'id': 2, 'am': 'የቻሲስ ቁጥር ማዛመድ', 'en': 'Chassis Number Match', 'points': 8 },
            { 'id': 3, 'am': 'የሞተር ቁጥር ማዛመድ', 'en': 'Engine Number Match', 'points': 8 },
            { 'id': 4, 'am': 'የባለቤትነት ማረጋገጫ', 'en': 'Title Certificate Check', 'points': 10 },
        ],
    },
    {
        'id': 'zone2',
        'titleAm': 'ብርሃን እና እይታ',
        'titleEn': 'Zone 2: Visibility & Lighting',
        'items': [
            { 'id': 5, 'am': 'የፊት መብራቶች (ከፍተኛ/ዝቅተኛ)', 'en': 'Headlights (High/Low)', 'points': 6 },
            { 'id': 6, 'am': 'የምልክት መብራቶች', 'en': 'Signal Lights', 'points': 4 },
            { 'id': 7, 'am': 'የብሬክ መብራቶች', 'en': 'Brake Lights', 'points': 6 },
            { 'id': 8, 'am': 'የኋላ መብራቶች', 'en': 'Reverse Lights', 'points': 4 },
            { 'id': 9, 'am': 'ዋይፐር እና ማጠቢያ', 'en': 'Wipers & Washers', 'points': 4 },
            { 'id': 10, 'am': 'የንፋስ መከላከያ ሁኔታ', 'en': 'Windshield Condition', 'points': 5 },
            { 'id': 11, 'am': 'የጎን/ኋላ መስተዋቶች', 'en': 'Side/Rear Mirrors', 'points': 5 },
        ],
    },
    {
        'id': 'zone3',
        'titleAm': 'መሪ እና ሳስፔንሽን',
        'titleEn': 'Zone 3: Steering & Suspension',
        'items': [
            { 'id': 12, 'am': 'የመሪ ጨዋታ', 'en': 'Steering Play', 'points': 8 },
            { 'id': 13, 'am': 'የደወል ተግባር', 'en': 'Horn Function', 'points': 3 },
            { 'id': 14, 'am': 'ሾክ አብሶርበሮች', 'en': 'Shock Absorbers', 'points': 6 },
            { 'id': 15, 'am': 'ሊፍ ስፕሪንግስ/ሳስፔንሽን', 'en': 'Leaf Springs/Suspension', 'points': 6 },
            { 'id': 16, 'am': 'የጎማ ሁኔታ', 'en': 'Tire Tread/Condition', 'points': 8 },
            { 'id': 17, 'am': 'የዊል ነትስ/ስታድስ', 'en': 'Wheel Nuts/Studs', 'points': 5 },
        ],
    },
    {
        'id': 'zone4',
        'titleAm': 'ሰውነት፣ ውስጥ እና ልዩ መሳሪያዎች',
        'titleEn': 'Zone 4: Body, Interior & Special Equipment',
        'items': [
            { 'id': 18, 'am': 'የበር ሜካኒዝም', 'en': 'Door Mechanisms', 'points': 4 },
            { 'id': 19, 'am': 'የመስኮት ስራዎች', 'en': 'Window Operations', 'points': 3 },
            { 'id': 20, 'am': 'የመቀመጫ ሁኔታዎች', 'en': 'Seat Conditions', 'points': 4 },
            { 'id': 21, 'am': 'ስፒድ ሊሚተር እና GPS', 'en': 'Speed Limiter & GPS', 'points': 10, 'critical': True, 'mandatory': True },
            { 'id': 22, 'am': 'የወለል/ሰውነት ዝገት', 'en': 'Floor/Body Corrosion', 'points': 4 },
            { 'id': 23, 'am': 'የተሳፋሪ መቀመጫ ማያያዣ', 'en': 'Passenger Seat Fixation', 'points': 8, 'critical': True },
            { 'id': 24, 'am': 'የጭስ ማስወጫ ስርዓት', 'en': 'Exhaust System', 'points': 5 },
            { 'id': 25, 'am': 'የባምፐር ሁኔታ', 'en': 'Bumper Condition', 'points': 3 },
        ],
    },
    {
        'id': 'zone5',
        'titleAm': 'የደህንነት መሳሪያዎች',
        'titleEn': 'Zone 5: Safety Equipment',
        'items': [
            { 'id': 26, 'am': 'የእሳት ማጥፊያ', 'en': 'Fire Extinguisher', 'points': 4 },
            { 'id': 27, 'am': 'የመጀመሪያ እርዳታ ኪት', 'en': 'First Aid Kit', 'points': 3 },
            { 'id': 28, 'am': 'የማስጠንቀቂያ ትሪያንግል', 'en': 'Warning Triangle', 'points': 3 },
            { 'id': 29, 'am': 'ተጠባባቂ ጎማ', 'en': 'Spare Wheel', 'points': 4 },
            { 'id': 30, 'am': 'ጭቃ መከላከያዎች', 'en': 'Mudguards', 'points': 3 },
        ],
    },
]


def populate_checklist_config(user):
    """
    Populate visual checklist configuration from hardcoded data.
    Returns summary of created/updated items.
    """
    created_count = 0
    updated_count = 0
    
    # Populate LIGHT vehicle checklist
    for zone in LIGHT_ZONES:
        for item in zone['items']:
            config_id = f"CFG-LIGHT-{zone['id']}-{item['id']:02d}"
            config, created = VisualChecklistConfig.objects.get_or_create(
                config_id=config_id,
                defaults={
                    'vehicle_category': 'LIGHT',
                    'zone_id': zone['id'],
                    'zone_name_en': zone['titleEn'],
                    'zone_name_am': zone['titleAm'],
                    'item_number': item['id'],
                    'item_name_en': item['en'],
                    'item_name_am': item['am'],
                    'points_possible': item['points'],
                    'is_critical': item.get('critical', False),
                    'is_mandatory': item.get('mandatory', False),
                    'display_order': item['id'],
                    'status': 'active',
                    'created_by': user,
                }
            )
            if created:
                created_count += 1
            else:
                # Update existing
                config.zone_name_en = zone['titleEn']
                config.zone_name_am = zone['titleAm']
                config.item_name_en = item['en']
                config.item_name_am = item['am']
                config.points_possible = item['points']
                config.is_critical = item.get('critical', False)
                config.is_mandatory = item.get('mandatory', False)
                config.display_order = item['id']
                config.status = 'active'
                config.save()
                updated_count += 1
    
    light_total = created_count + updated_count
    
    # Reset counters
    created_count = 0
    updated_count = 0
    
    # Populate HEAVY vehicle checklist
    for zone in HEAVY_ZONES:
        for item in zone['items']:
            config_id = f"CFG-HEAVY-{zone['id']}-{item['id']:02d}"
            config, created = VisualChecklistConfig.objects.get_or_create(
                config_id=config_id,
                defaults={
                    'vehicle_category': 'HEAVY',
                    'zone_id': zone['id'],
                    'zone_name_en': zone['titleEn'],
                    'zone_name_am': zone['titleAm'],
                    'item_number': item['id'],
                    'item_name_en': item['en'],
                    'item_name_am': item['am'],
                    'points_possible': item['points'],
                    'is_critical': item.get('critical', False),
                    'is_mandatory': item.get('mandatory', False),
                    'display_order': item['id'],
                    'status': 'active',
                    'created_by': user,
                }
            )
            if created:
                created_count += 1
            else:
                # Update existing
                config.zone_name_en = zone['titleEn']
                config.zone_name_am = zone['titleAm']
                config.item_name_en = item['en']
                config.item_name_am = item['am']
                config.points_possible = item['points']
                config.is_critical = item.get('critical', False)
                config.is_mandatory = item.get('mandatory', False)
                config.display_order = item['id']
                config.status = 'active'
                config.save()
                updated_count += 1
    
    heavy_total = created_count + updated_count
    
    return {
        'light': {
            'created': light_total - updated_count,
            'updated': updated_count,
            'total': light_total
        },
        'heavy': {
            'created': created_count,
            'updated': updated_count,
            'total': heavy_total
        },
        'total': light_total + heavy_total
    }

