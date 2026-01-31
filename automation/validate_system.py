"""Full System Validation Script"""

from pymongo import MongoClient
from collections import defaultdict

uri = 'mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds?retryWrites=true&w=majority'
client = MongoClient(uri)
db = client['mutualfunds']

print('='*70)
print('MONGODB COLLECTIONS VALIDATION')
print('='*70)

# List all collections
collections = db.list_collection_names()
print(f'\nCollections found: {len(collections)}')
for col in sorted(collections):
    count = db[col].count_documents({})
    print(f'  {col}: {count:,} documents')

# Check sample fund for data completeness
print('\n' + '='*70)
print('SAMPLE FUND DATA COMPLETENESS CHECK')
print('='*70)

# Get one fund from each category
categories = ['equity', 'debt', 'commodity']
for cat in categories:
    fund = db.funds.find_one({'category': cat})
    if fund:
        name = fund.get('name', 'N/A')
        if name:
            name = name[:50]
        print(f'\n{cat.upper()} Fund: {name}')
        
        # Check holdings
        holdings = fund.get('holdings', fund.get('topHoldings', []))
        print(f'  Holdings: {len(holdings) if holdings else 0} items')
        
        # Check sectors
        sectors = fund.get('sectors', fund.get('sectorAllocation', []))
        print(f'  Sectors: {len(sectors) if sectors else 0} items')
        
        # Fund manager
        fm = fund.get('fundManager', 'N/A')
        print(f'  Fund Manager: {fm}')
        
        # AUM
        aum = fund.get('aum', 'N/A')
        print(f'  AUM: {aum}')
        
        # Returns
        returns = fund.get('returns', {})
        if isinstance(returns, dict):
            r1y = returns.get('1Y', returns.get('oneYear', 'N/A'))
        else:
            r1y = fund.get('return1Y', 'N/A')
        print(f'  Returns 1Y: {r1y}')
    else:
        print(f'\n{cat.upper()}: No funds found')

# Check for funds WITH holdings
print('\n' + '='*70)
print('FUNDS WITH HOLDINGS DATA')
print('='*70)
with_holdings = db.funds.count_documents({'$or': [
    {'holdings.0': {'$exists': True}},
    {'topHoldings.0': {'$exists': True}}
]})
print(f'Funds with embedded holdings: {with_holdings:,} / 14,216')

# Check for funds WITH sector allocation
with_sectors = db.funds.count_documents({'$or': [
    {'sectors.0': {'$exists': True}},
    {'sectorAllocation.0': {'$exists': True}}
]})
print(f'Funds with embedded sectors: {with_sectors:,} / 14,216')

# Check FundHoldings collection
print('\n' + '='*70)
print('FUND_HOLDINGS COLLECTION CHECK')
print('='*70)
# Try different collection names
for col_name in ['fundholdings', 'fundHoldings', 'fund_holdings', 'holdings']:
    if col_name in collections:
        count = db[col_name].count_documents({})
        print(f'{col_name}: {count:,} records')
        if count > 0:
            sample = db[col_name].find_one()
            print(f'  Sample fields: {list(sample.keys())[:10]}')

# Check fund returns field structure
print('\n' + '='*70)
print('RETURNS FIELD STRUCTURE CHECK')
print('='*70)
sample_fund = db.funds.find_one({'category': 'equity'})
if sample_fund:
    print(f"Returns field type: {type(sample_fund.get('returns'))}")
    if 'returns' in sample_fund:
        returns = sample_fund['returns']
        if isinstance(returns, dict):
            print(f"Returns keys: {list(returns.keys())}")
    # Check for flat return fields
    flat_return_fields = [k for k in sample_fund.keys() if 'return' in k.lower() or 'Y' in k]
    print(f"Flat return fields: {flat_return_fields[:10]}")

# Check fund manager fields
print('\n' + '='*70)
print('FUND MANAGER FIELDS CHECK')
print('='*70)
fund_with_manager = db.funds.find_one({'fundManager': {'$exists': True, '$ne': None}})
if fund_with_manager:
    fm_fields = [k for k in fund_with_manager.keys() if 'manager' in k.lower() or 'Manager' in k]
    print(f"Fund Manager fields: {fm_fields}")
    print(f"Fund Manager value: {fund_with_manager.get('fundManager')}")

# Storage size estimate
print('\n' + '='*70)
print('STORAGE SIZE ESTIMATE')
print('='*70)
stats = db.command('dbStats')
data_size_mb = stats['dataSize'] / (1024 * 1024)
storage_size_mb = stats['storageSize'] / (1024 * 1024)
print(f"Data Size: {data_size_mb:.2f} MB")
print(f"Storage Size: {storage_size_mb:.2f} MB")
print(f"Free Tier Limit: 512 MB")
print(f"Usage: {(storage_size_mb/512)*100:.1f}%")

client.close()

print('\n' + '='*70)
print('VALIDATION COMPLETE')
print('='*70)
