"""
ACCURATE DATABASE STATUS
"""
from pymongo import MongoClient

client = MongoClient('mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds?retryWrites=true&w=majority')
db = client['mutualfunds']

print('='*60)
print('CURRENT DATABASE STATUS')
print('='*60)

# Total funds
total = db.funds.count_documents({})
print(f'\nTotal Funds: {total:,}')

# Manually count funds with holdings
holdings_count = 0
sectors_count = 0
funds_list = []

for f in db.funds.find({}, {'schemeCode': 1, 'schemeName': 1, 'topHoldings': 1, 'sectorAllocation': 1}):
    th = f.get('topHoldings')
    sa = f.get('sectorAllocation')
    
    if th and isinstance(th, list) and len(th) > 0:
        holdings_count += 1
        funds_list.append({
            'code': f.get('schemeCode'),
            'name': f.get('schemeName', 'N/A')[:40] if f.get('schemeName') else 'N/A',
            'holdings': len(th),
            'sectors': len(sa) if sa else 0
        })
    
    if sa and isinstance(sa, list) and len(sa) > 0:
        sectors_count += 1

print(f'Funds with REAL Holdings: {holdings_count}')
print(f'Funds with Sector Data: {sectors_count}')

if holdings_count > 0:
    print(f'\nFunds with Holdings:')
    for f in funds_list[:30]:
        print(f"  {f['code']}: {f['holdings']} holdings, {f['sectors']} sectors - {f['name']}")

# Holdings collection
h_coll = db.holdings.count_documents({})
s_coll = db.sector_allocation.count_documents({})
print(f'\nHoldings Collection: {h_coll} records')
print(f'Sector Allocation Collection: {s_coll} records')

# Storage
print('\n' + '='*60)
print('MONGODB STORAGE')
print('='*60)

stats = db.command('dbStats')
data_mb = stats['dataSize'] / (1024 * 1024)
index_mb = stats['indexSize'] / (1024 * 1024)
total_mb = data_mb + index_mb

print(f'\nData Size:      {data_mb:.2f} MB')
print(f'Index Size:     {index_mb:.2f} MB')
print(f'Total Used:     {total_mb:.2f} MB')
print(f'Free Tier:      512 MB')
print(f'Usage:          {(total_mb/512)*100:.1f}%')
print(f'Available:      {512 - total_mb:.1f} MB')

client.close()
