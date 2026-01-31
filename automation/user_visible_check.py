"""
Check user-visible data quality for top AMCs
"""
from pymongo import MongoClient

client = MongoClient('mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds')
db = client['mutualfunds']

print('FUNDS WITH GOOD DATA (Real holdings + Real sectors)')
print('='*70)

# Find funds with both good holdings AND good sectors
good_funds = db.funds.find({
    'sector_allocation': {
        '$exists': True,
        '$elemMatch': {'sector': {'$in': ['Financial Services', 'Information Technology', 'Healthcare', 'Oil & Gas', 'Automobile']}}
    },
    'holdings': {'$exists': True, '$not': {'$size': 0}}
}).limit(5)

for fund in good_funds:
    print(f'\nFund: {fund.get("name", "N/A")}')
    print(f'AMC: {fund.get("amc", {}).get("name", "N/A")}')
    print(f'Category: {fund.get("category", "N/A")}')
    
    print('Holdings:')
    for h in fund.get('holdings', [])[:5]:
        print(f'  - {h.get("company", "N/A")}: {h.get("percentage", 0)}%')
    
    print('Sectors:')
    for s in fund.get('sector_allocation', [])[:5]:
        print(f'  - {s.get("sector", "N/A")}: {s.get("percentage", 0)}%')

# Summary counts
print('\n' + '='*70)
print('SUMMARY FOR TOP AMCs - SECTOR ALLOCATION QUALITY')
print('='*70)

top_amcs = [
    'HDFC Mutual Fund', 
    'SBI Mutual Fund', 
    'ICICI Prudential Mutual Fund', 
    'Kotak Mahindra Mutual Fund', 
    'UTI Mutual Fund', 
    'Nippon India Mutual Fund'
]

total_all = 0
good_all = 0

for amc in top_amcs:
    total = db.funds.count_documents({'amc.name': amc})
    with_good_sectors = db.funds.count_documents({
        'amc.name': amc,
        'sector_allocation': {
            '$elemMatch': {'sector': {'$nin': ['Others', 'others', '', None]}}
        }
    })
    total_all += total
    good_all += with_good_sectors
    pct = (with_good_sectors/total*100) if total > 0 else 0
    short_name = amc.replace(' Mutual Fund', '')
    print(f'{short_name:32} {with_good_sectors:>5}/{total:<5} ({pct:>3.0f}%) with real sectors')

print('-'*70)
pct_all = (good_all/total_all*100) if total_all > 0 else 0
print(f'{"TOTAL":32} {good_all:>5}/{total_all:<5} ({pct_all:>3.0f}%)')

# Check what users actually see
print('\n' + '='*70)
print('WHAT USERS WILL SEE')
print('='*70)

# Funds with GOOD sector breakdown
print('\n✅ Example of GOOD fund (visible to users):')
good_example = db.funds.find_one({
    'sector_allocation': {
        '$elemMatch': {'sector': 'Financial Services', 'percentage': {'$gte': 10}}
    },
    'holdings': {'$exists': True, '$not': {'$size': 0}}
})

if good_example:
    print(f'   Name: {good_example.get("name", "N/A")}')
    print(f'   AMC: {good_example.get("amc", {}).get("name", "N/A")}')
    print(f'   Category: {good_example.get("category", "N/A")}')
    print(f'\n   Sector Allocation:')
    for s in good_example.get('sector_allocation', []):
        if s.get('percentage', 0) > 0:
            print(f'     {s["sector"]:25} {s["percentage"]:>6.2f}%')
    
    print(f'\n   Top Holdings:')
    for h in good_example.get('holdings', [])[:7]:
        company = h.get('company', 'N/A')
        # Skip garbage
        if company and len(company) > 3 and not any(x in company.lower() for x in ['inception', 'year', 'month', 'days']):
            print(f'     {company[:40]:42} {h.get("percentage", 0):>6.2f}%')

# Count funds with clean data
print('\n' + '='*70)
print('OVERALL DATA QUALITY')
print('='*70)

total_funds = db.funds.count_documents({})
with_holdings = db.funds.count_documents({'holdings': {'$exists': True, '$not': {'$size': 0}}})
with_sectors = db.funds.count_documents({'sector_allocation': {'$exists': True, '$not': {'$size': 0}}})
with_good_sectors = db.funds.count_documents({
    'sector_allocation': {
        '$elemMatch': {'sector': {'$nin': ['Others', 'others', '', None]}}
    }
})

print(f'Total Funds:           {total_funds:,}')
print(f'With Holdings:         {with_holdings:,} ({with_holdings/total_funds*100:.1f}%)')
print(f'With Sector Allocation:{with_sectors:,} ({with_sectors/total_funds*100:.1f}%)')
print(f'With REAL Sectors:     {with_good_sectors:,} ({with_good_sectors/total_funds*100:.1f}%)')

client.close()
