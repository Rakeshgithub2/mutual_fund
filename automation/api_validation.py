"""
API & DATA VALIDATION SCRIPT
"""
from pymongo import MongoClient

uri = 'mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds?retryWrites=true&w=majority'
client = MongoClient(uri)
db = client['mutualfunds']

print('='*60)
print('BACKEND API VALIDATION')
print('='*60)

# Check funds with real holdings
funds_with_holdings = []
for f in db.funds.find({'topHoldings': {'$exists': True}}, {'schemeCode': 1, 'schemeName': 1, 'topHoldings': 1, 'category': 1}).limit(50):
    th = f.get('topHoldings', [])
    if th and len(th) > 0:
        funds_with_holdings.append({
            'code': f.get('schemeCode'),
            'name': f.get('schemeName', 'N/A')[:40] if f.get('schemeName') else 'N/A',
            'category': f.get('category'),
            'holdings': len(th)
        })

print(f'Funds with REAL holdings in funds collection: {len(funds_with_holdings)}')
for f in funds_with_holdings[:10]:
    print(f"  {f['code']}: {f['holdings']} holdings - {f['name']}")

# Check holdings collection  
h_count = db.holdings.count_documents({})
print(f'\nHoldings collection records: {h_count}')

# Sample fund with full data
sample = db.funds.find_one({'schemeCode': '118632'})
if sample:
    print()
    print('='*60)
    print('SAMPLE FUND DATA (schemeCode: 118632)')
    print('='*60)
    print(f"Name: {sample.get('schemeName', 'N/A')}")
    print(f"Category: {sample.get('category')} / {sample.get('subCategory')}")
    
    nav = sample.get('nav', {})
    print(f"NAV: {nav.get('value') if nav else 'N/A'}")
    
    aum = sample.get('aum', {})
    print(f"AUM: {aum.get('value') if aum else 'N/A'} Cr")
    
    returns = sample.get('returns', {})
    print(f"Returns: 1Y={returns.get('1Y')}%, 3Y={returns.get('3Y')}%, 5Y={returns.get('5Y')}%")
    
    holdings = sample.get('topHoldings', [])
    print(f"Holdings: {len(holdings)}")
    for h in holdings[:5]:
        print(f"  - {h.get('name', 'N/A')}: {h.get('percentage')}%")
    
    sectors = sample.get('sectorAllocation', [])
    print(f"Sectors: {len(sectors)}")
    for s in sectors[:5]:
        print(f"  - {s.get('sector', 'N/A')}: {s.get('percentage')}%")

client.close()
