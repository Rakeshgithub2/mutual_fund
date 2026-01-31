"""
Delete Sample Data and Restore Clean State
============================================
Removes the fake topHoldings/sectorAllocation I added
Keeps the real data in 'holdings' collection
"""
from pymongo import MongoClient

uri = 'mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds?retryWrites=true&w=majority'
client = MongoClient(uri)
db = client['mutualfunds']

print('='*70)
print('DELETING SAMPLE/FAKE DATA')
print('='*70)

# Count before
before_holdings = db.funds.count_documents({'topHoldings.0': {'$exists': True}})
before_sectors = db.funds.count_documents({'sectorAllocation.0': {'$exists': True}})
before_complete = db.funds.count_documents({'dataComplete': True})

print(f'\nBefore cleanup:')
print(f'  Funds with topHoldings: {before_holdings:,}')
print(f'  Funds with sectorAllocation: {before_sectors:,}')
print(f'  Funds with dataComplete: {before_complete:,}')

# Remove the sample fields I added
print('\nRemoving sample data fields...')
result = db.funds.update_many(
    {},
    {
        '$unset': {
            'topHoldings': '',
            'sectorAllocation': '',
            'holdingsAsOf': '',
            'dataComplete': ''
        }
    }
)
print(f'  Modified: {result.modified_count:,} documents')

# Verify
after_holdings = db.funds.count_documents({'topHoldings.0': {'$exists': True}})
after_sectors = db.funds.count_documents({'sectorAllocation.0': {'$exists': True}})
after_complete = db.funds.count_documents({'dataComplete': True})

print(f'\nAfter cleanup:')
print(f'  Funds with topHoldings: {after_holdings:,}')
print(f'  Funds with sectorAllocation: {after_sectors:,}')
print(f'  Funds with dataComplete: {after_complete:,}')

# Check storage
stats = db.command('dbStats')
data_size_mb = stats['dataSize'] / (1024 * 1024)
print(f'\nStorage: {data_size_mb:.2f} MB')

# Check the REAL holdings collection is still intact
real_count = db.holdings.count_documents({})
print(f'\nReal holdings collection (intact): {real_count} records')

client.close()
print('\n✅ Sample data deleted!')
print('   Real holdings collection preserved.')
