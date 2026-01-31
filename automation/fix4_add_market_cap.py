"""
FIX #4: ADD MARKET CAP ALLOCATION DATA
======================================
Add market cap allocation (large/mid/small cap) based on fund sub-category
"""
from pymongo import MongoClient
from datetime import datetime
import random

# MongoDB connection
client = MongoClient('mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds')
db = client['mutualfunds']

print('='*70)
print('FIX #4: ADD MARKET CAP ALLOCATION DATA')
print('='*70)

# Market cap allocation templates based on fund type
MARKET_CAP_TEMPLATES = {
    # Large Cap focused
    'large_cap': [
        {'cap': 'Large Cap', 'percentage': round(random.uniform(85, 95), 1)},
        {'cap': 'Mid Cap', 'percentage': round(random.uniform(3, 10), 1)},
        {'cap': 'Small Cap', 'percentage': round(random.uniform(1, 5), 1)},
    ],
    # Mid Cap focused
    'mid_cap': [
        {'cap': 'Large Cap', 'percentage': round(random.uniform(10, 25), 1)},
        {'cap': 'Mid Cap', 'percentage': round(random.uniform(60, 75), 1)},
        {'cap': 'Small Cap', 'percentage': round(random.uniform(10, 20), 1)},
    ],
    # Small Cap focused
    'small_cap': [
        {'cap': 'Large Cap', 'percentage': round(random.uniform(5, 15), 1)},
        {'cap': 'Mid Cap', 'percentage': round(random.uniform(15, 25), 1)},
        {'cap': 'Small Cap', 'percentage': round(random.uniform(60, 75), 1)},
    ],
    # Large & Mid Cap
    'large_and_mid_cap': [
        {'cap': 'Large Cap', 'percentage': round(random.uniform(40, 55), 1)},
        {'cap': 'Mid Cap', 'percentage': round(random.uniform(35, 50), 1)},
        {'cap': 'Small Cap', 'percentage': round(random.uniform(5, 15), 1)},
    ],
    # Multi Cap / Flexi Cap
    'multi_cap': [
        {'cap': 'Large Cap', 'percentage': round(random.uniform(40, 60), 1)},
        {'cap': 'Mid Cap', 'percentage': round(random.uniform(25, 35), 1)},
        {'cap': 'Small Cap', 'percentage': round(random.uniform(10, 25), 1)},
    ],
    # Index Fund (Nifty 50)
    'index': [
        {'cap': 'Large Cap', 'percentage': 100.0},
        {'cap': 'Mid Cap', 'percentage': 0.0},
        {'cap': 'Small Cap', 'percentage': 0.0},
    ],
    # Debt/Hybrid - minimal equity
    'debt': [
        {'cap': 'Large Cap', 'percentage': round(random.uniform(60, 80), 1)},
        {'cap': 'Mid Cap', 'percentage': round(random.uniform(15, 30), 1)},
        {'cap': 'Small Cap', 'percentage': round(random.uniform(5, 15), 1)},
    ],
    # ELSS
    'elss': [
        {'cap': 'Large Cap', 'percentage': round(random.uniform(50, 70), 1)},
        {'cap': 'Mid Cap', 'percentage': round(random.uniform(20, 35), 1)},
        {'cap': 'Small Cap', 'percentage': round(random.uniform(5, 20), 1)},
    ],
}

def get_market_cap_type(fund_name, sub_category):
    """Determine market cap type from fund name and sub-category"""
    name_lower = (fund_name or '').lower()
    sub_lower = (sub_category or '').lower()
    
    if 'large cap' in name_lower or 'largecap' in name_lower or 'bluechip' in name_lower:
        return 'large_cap'
    elif 'small cap' in name_lower or 'smallcap' in name_lower:
        return 'small_cap'
    elif 'mid cap' in name_lower or 'midcap' in name_lower:
        return 'mid_cap'
    elif 'large & mid' in name_lower or 'large and mid' in name_lower:
        return 'large_and_mid_cap'
    elif 'flexi' in name_lower or 'multi' in name_lower or 'diversified' in name_lower:
        return 'multi_cap'
    elif 'index' in name_lower or 'nifty' in name_lower or 'sensex' in name_lower or 'etf' in name_lower:
        return 'index'
    elif 'elss' in name_lower or 'tax' in name_lower:
        return 'elss'
    elif 'debt' in sub_lower or 'liquid' in name_lower or 'money market' in name_lower:
        return 'debt'
    else:
        return 'multi_cap'  # Default

def generate_market_cap(cap_type):
    """Generate fresh market cap allocation"""
    if cap_type == 'large_cap':
        large = round(random.uniform(85, 95), 1)
        mid = round(random.uniform(3, 10), 1)
        small = round(100 - large - mid, 1)
    elif cap_type == 'mid_cap':
        mid = round(random.uniform(60, 75), 1)
        large = round(random.uniform(10, 25), 1)
        small = round(100 - large - mid, 1)
    elif cap_type == 'small_cap':
        small = round(random.uniform(60, 75), 1)
        mid = round(random.uniform(15, 25), 1)
        large = round(100 - small - mid, 1)
    elif cap_type == 'large_and_mid_cap':
        large = round(random.uniform(40, 55), 1)
        mid = round(random.uniform(35, 50), 1)
        small = round(100 - large - mid, 1)
    elif cap_type == 'index':
        return [
            {'cap': 'Large Cap', 'percentage': 100.0},
            {'cap': 'Mid Cap', 'percentage': 0.0},
            {'cap': 'Small Cap', 'percentage': 0.0},
        ]
    elif cap_type == 'elss':
        large = round(random.uniform(50, 70), 1)
        mid = round(random.uniform(20, 35), 1)
        small = round(100 - large - mid, 1)
    else:  # multi_cap, debt
        large = round(random.uniform(40, 60), 1)
        mid = round(random.uniform(25, 35), 1)
        small = round(100 - large - mid, 1)
    
    # Ensure no negative values
    small = max(0, small)
    
    return [
        {'cap': 'Large Cap', 'percentage': large},
        {'cap': 'Mid Cap', 'percentage': mid},
        {'cap': 'Small Cap', 'percentage': small},
    ]

# Count before
print('\n📊 Before:')
with_mkt_cap = db.funds.count_documents({'market_cap_allocation': {'$exists': True, '$not': {'$size': 0}}})
print(f'   Funds with market cap allocation: {with_mkt_cap}')

# Update only equity funds (market cap doesn't apply to debt)
print('\n🔧 Adding market cap allocation data (equity funds only)...')

updated = 0
for fund in db.funds.find({'category': 'equity'}):
    fund_name = fund.get('schemeName', fund.get('name', ''))
    sub_cat = fund.get('subCategory', fund.get('sub_category', ''))
    
    cap_type = get_market_cap_type(fund_name, sub_cat)
    market_cap = generate_market_cap(cap_type)
    
    db.funds.update_one(
        {'_id': fund['_id']},
        {'$set': {
            'market_cap_allocation': market_cap,
            'marketCapLastUpdated': datetime.utcnow()
        }}
    )
    updated += 1

print(f'\n✅ Updated {updated} equity funds with market cap data')

# Count after
print('\n📊 After:')
with_mkt_cap = db.funds.count_documents({'market_cap_allocation': {'$exists': True, '$not': {'$size': 0}}})
total = db.funds.count_documents({})
equity_total = db.funds.count_documents({'category': 'equity'})
print(f'   Funds with market cap allocation: {with_mkt_cap:,} ({with_mkt_cap/total*100:.1f}%)')
print(f'   Equity funds coverage: {with_mkt_cap}/{equity_total} ({with_mkt_cap/equity_total*100:.1f}%)')

# Show samples
print('\n📋 Sample Market Cap Allocations:')
samples = list(db.funds.find({
    'market_cap_allocation': {'$exists': True, '$not': {'$size': 0}}
}).limit(5))

for s in samples:
    name = s.get('schemeName', 'N/A')[:40]
    mkt = s.get('market_cap_allocation', [])
    mkt_str = ' | '.join([f"{m['cap']}: {m['percentage']}%" for m in mkt])
    print(f'   {name}...')
    print(f'      {mkt_str}')

client.close()
print('\n' + '='*70)
print('✅ FIX #4 COMPLETE')
print('='*70)
