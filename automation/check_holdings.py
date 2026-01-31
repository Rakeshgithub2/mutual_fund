"""Check existing holdings data"""
from pymongo import MongoClient

uri = 'mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds?retryWrites=true&w=majority'
client = MongoClient(uri)
db = client['mutualfunds']

# Check holdings collection
print('HOLDINGS COLLECTION (35 records):')
sample = db.holdings.find_one()
print('Fields:', list(sample.keys()))

holdings_arr = sample.get('holdings', [])
print(f'Holdings count in sample: {len(holdings_arr)}')
if holdings_arr:
    print('First holding:', holdings_arr[0])

sectors_arr = sample.get('sectors', [])
print(f'Sectors count in sample: {len(sectors_arr) if sectors_arr else 0}')
if sectors_arr and isinstance(sectors_arr, list) and len(sectors_arr) > 0:
    print('First sector:', sectors_arr[0])
elif sectors_arr and isinstance(sectors_arr, dict):
    first_key = list(sectors_arr.keys())[0]
    print('First sector:', first_key, sectors_arr[first_key])

print(f"\nScheme Code: {sample.get('schemeCode')}")
print(f"Scheme Name: {sample.get('schemeName')}")

# Check how many unique funds have holdings
unique_funds = db.holdings.distinct('schemeCode')
print(f'\nUnique funds with holdings: {len(unique_funds)}')

# Check sector_allocation collection
print('\n' + '='*50)
print('SECTOR_ALLOCATION COLLECTION (24 records):')
sample = db.sector_allocation.find_one()
if sample:
    print('Fields:', list(sample.keys()))

# Count unique funds in sector_allocation
unique_sector_funds = db.sector_allocation.distinct('schemeCode')
print(f'Unique funds with sector data: {len(unique_sector_funds)}')

client.close()
