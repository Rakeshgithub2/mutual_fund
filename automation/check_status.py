"""Check database status after PDF parsing"""
from pymongo import MongoClient

client = MongoClient('mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds')
db = client['mutualfunds']
funds = db['funds']

total = funds.count_documents({})
with_holdings = funds.count_documents({'holdings': {'$exists': True, '$ne': [], '$ne': None}})

print('=' * 50)
print('DATABASE STATUS')
print('=' * 50)
print(f'Total Funds: {total:,}')
print(f'With Holdings: {with_holdings:,}')
print(f'Without Holdings: {total - with_holdings:,}')
print(f'Coverage: {with_holdings/total*100:.1f}%')

# Sample a Kotak fund with holdings
sample = funds.find_one({
    'holdings': {'$exists': True, '$ne': []},
    'schemeName': {'$regex': 'Kotak', '$options': 'i'}
})

if sample:
    print()
    print('Sample Kotak Fund:')
    name = sample.get('schemeName', 'N/A')
    print(f'  Name: {name[:60]}')
    print(f'  Holdings: {len(sample.get("holdings", []))}')
    print(f'  Sectors: {len(sample.get("sectorAllocation", []))}')
    if sample.get('holdings'):
        print('  Top Holdings:')
        for h in sample['holdings'][:5]:
            print(f'    - {h.get("company", "N/A")}: {h.get("percentage", 0)}%')
