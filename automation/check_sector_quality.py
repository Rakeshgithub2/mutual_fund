"""
Check sector allocation quality
"""
from pymongo import MongoClient

client = MongoClient('mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds')
db = client['mutualfunds']

print('='*70)
print('CHECKING SECTOR ALLOCATION QUALITY')
print('='*70)

# Find funds with REAL sector data (not just 'Others')
good_sectors = db.funds.find({
    'sector_allocation': {
        '$exists': True,
        '$not': {'$size': 0},
        '$elemMatch': {'sector': {'$nin': ['Others', 'others']}}
    }
})

count = 0
sectors_found = set()

for fund in good_sectors:
    sectors = fund.get('sector_allocation', [])
    for s in sectors:
        if s.get('sector') != 'Others':
            sectors_found.add(s.get('sector'))
    count += 1
    
    if count <= 10:
        print(f'\n✅ {fund.get("name", "N/A")[:50]}')
        print(f'   AMC: {fund.get("amc", {}).get("name", "N/A")}')
        for s in sectors[:5]:
            print(f'   → {s["sector"]}: {s["percentage"]}%')

print(f'\n' + '='*70)
print(f'SUMMARY')
print('='*70)
print(f'Funds with real sector data: {count}')
print(f'Unique sectors found: {len(sectors_found)}')
print(f'Sectors: {sorted(sectors_found)}')

# Check holdings with proper company names
print(f'\n' + '='*70)
print('CHECKING HOLDINGS WITH PROPER COMPANY NAMES')
print('='*70)

# Look for holdings with known company names
known_companies = ['HDFC Bank', 'ICICI Bank', 'Infosys', 'TCS', 'Reliance', 'State Bank']

for company in known_companies:
    result = db.funds.find_one({
        'holdings': {
            '$elemMatch': {
                'company': {'$regex': company, '$options': 'i'}
            }
        }
    })
    if result:
        print(f'\n✅ Found holding with "{company}":')
        print(f'   Fund: {result.get("name", "N/A")}')
        for h in result.get('holdings', [])[:3]:
            print(f'   → {h}')
    else:
        print(f'\n❌ No holding found with "{company}"')

# Check all unique sector values
print(f'\n' + '='*70)
print('ALL UNIQUE SECTORS IN DATABASE')
print('='*70)

pipeline = [
    {'$unwind': '$sector_allocation'},
    {'$group': {'_id': '$sector_allocation.sector', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]

sectors = list(db.funds.aggregate(pipeline))
for s in sectors:
    print(f'   {s["_id"]}: {s["count"]} funds')

# Check all unique holdings companies (sample)
print(f'\n' + '='*70)
print('SAMPLE HOLDINGS COMPANIES')
print('='*70)

pipeline = [
    {'$unwind': '$holdings'},
    {'$group': {'_id': '$holdings.company'}},
    {'$limit': 50}
]

companies = list(db.funds.aggregate(pipeline))
print(f'Sample of {len(companies)} unique company names:')
for c in companies[:30]:
    print(f'   - {c["_id"]}')

client.close()
