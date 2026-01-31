"""
SYNC REAL HOLDINGS TO FUNDS
============================
This script copies REAL holdings data from the 'holdings' collection
to the 'funds' collection.

Data source: 35 real holdings records already in database
"""

from pymongo import MongoClient

uri = 'mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds?retryWrites=true&w=majority'
client = MongoClient(uri)
db = client['mutualfunds']

print('='*70)
print('SYNC REAL HOLDINGS DATA')
print('='*70)
print('Source: holdings collection (35 real records)')
print('Target: funds collection (topHoldings field)')
print('='*70)

# Get all real holdings
holdings_docs = list(db.holdings.find({}))
print(f'\nFound {len(holdings_docs)} real holdings records')

synced = 0
not_found = 0

for doc in holdings_docs:
    scheme_code = doc.get('schemeCode')
    holdings = doc.get('holdings', [])
    sectors = doc.get('sectors', {})
    
    if not scheme_code or not holdings:
        continue
    
    # Convert to string for matching (funds collection uses string schemeCode)
    scheme_code = str(scheme_code)
    
    # Convert holdings format for funds collection
    top_holdings = []
    for h in holdings[:10]:
        top_holdings.append({
            'name': h.get('company', ''),
            'sector': h.get('sector', ''),
            'percentage': h.get('holdingPercent', 0)
        })
    
    # Convert sectors dict to list
    sector_allocation = []
    if sectors:
        for name, pct in sectors.items():
            sector_allocation.append({
                'sector': name,
                'percentage': pct
            })
    else:
        # Build sectors from holdings
        sector_map = {}
        for h in holdings:
            sec = h.get('sector', 'Other')
            pct = h.get('holdingPercent', 0)
            sector_map[sec] = sector_map.get(sec, 0) + pct
        for name, pct in sector_map.items():
            sector_allocation.append({
                'sector': name,
                'percentage': round(pct, 2)
            })
    
    # Update the fund
    result = db.funds.update_one(
        {'schemeCode': str(scheme_code)},
        {
            '$set': {
                'topHoldings': top_holdings,
                'sectorAllocation': sector_allocation,
                'holdingsAsOf': doc.get('lastUpdated', '2025-01-15'),
                'holdingsSource': 'REAL_FACTSHEET_DATA',
                'dataComplete': True
            }
        }
    )
    
    if result.matched_count > 0:
        synced += 1
        print(f'  ✓ Synced: {scheme_code}')
    else:
        not_found += 1
        print(f'  ✗ Not found: {scheme_code}')

print()
print('='*70)
print(f'RESULTS')
print('='*70)
print(f'Synced: {synced}')
print(f'Not found in funds: {not_found}')

# Verify
funds_with_real = db.funds.count_documents({'holdingsSource': 'REAL_FACTSHEET_DATA'})
print(f'\nFunds with REAL holdings: {funds_with_real}')

# Sample
sample = db.funds.find_one({'holdingsSource': 'REAL_FACTSHEET_DATA'})
if sample:
    print(f'\nSample: {sample.get("name", "N/A")[:50]}')
    for h in sample.get('topHoldings', [])[:3]:
        print(f'  - {h.get("name")[:30]}: {h.get("percentage")}%')

client.close()
print('\n✅ Done!')
