"""Analyze Real vs Sample Data and Clean Up"""
from pymongo import MongoClient

uri = 'mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds?retryWrites=true&w=majority'
client = MongoClient(uri)
db = client['mutualfunds']

print('='*70)
print('ANALYZING DATA: REAL vs SAMPLE')
print('='*70)

# Check sample fund to see what data looks like
sample = db.funds.find_one({'category': 'equity', 'topHoldings.0': {'$exists': True}})

print('\nSAMPLE DATA I JUST ADDED (FAKE):')
print('-'*40)
for h in sample.get('topHoldings', [])[:3]:
    print(f"  - {h.get('name')}: {h.get('percentage')}%")

print('\nSample Fund Sectors:')
for s in sample.get('sectorAllocation', [])[:3]:
    print(f"  - {s.get('sector')}: {s.get('percentage')}%")

# Check if holdingsAsOf indicates sample data
holdings_as_of = sample.get('holdingsAsOf')
data_complete = sample.get('dataComplete')
print(f'\nholdingsAsOf: {holdings_as_of}')
print(f'dataComplete: {data_complete}')

# Check the original holdings collection (real data)
print('\n' + '='*70)
print('ORIGINAL HOLDINGS COLLECTION (REAL DATA FROM BEFORE):')
print('='*70)
real_holdings = db.holdings.find_one()
if real_holdings:
    scheme_name = real_holdings.get('schemeName', 'N/A')
    if scheme_name:
        scheme_name = scheme_name[:50]
    print(f'Scheme: {scheme_name}')
    print('Real Holdings:')
    for h in real_holdings.get('holdings', [])[:5]:
        company = h.get('company', 'N/A')
        sector = h.get('sector', 'N/A')
        pct = h.get('holdingPercent', 0)
        print(f"  - {company}: {pct}% ({sector})")
    
    print('\nReal Sectors:')
    sectors = real_holdings.get('sectors', {})
    if isinstance(sectors, dict):
        for k, v in list(sectors.items())[:5]:
            print(f"  - {k}: {v}%")

print('\n' + '='*70)
print('DECISION: Delete sample data, keep real data structure')
print('='*70)

client.close()
