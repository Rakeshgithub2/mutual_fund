from pymongo import MongoClient
client = MongoClient('mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds')
db = client['mutualfunds']

# Check market indices
print('='*60)
print('MARKET INDICES CHECK')
print('='*60)
indices = list(db.market_indices.find())
print(f'Total indices in market_indices: {len(indices)}')
if indices:
    for idx in indices[:5]:
        print(f"  - {idx.get('name', 'N/A')}: {idx.get('value', idx.get('current', 'N/A'))}")

indices2 = list(db.marketindices.find())
print(f'Total indices in marketindices: {len(indices2)}')
if indices2:
    for idx in indices2[:5]:
        print(f"  - {idx.get('name', 'N/A')}: {idx.get('value', idx.get('current', 'N/A'))}")

# Check users
print()
print('='*60)
print('USERS CHECK')
print('='*60)
users = db.users.count_documents({})
print(f'Total users: {users}')

# Check User collection (capitalized)
users2 = db.User.count_documents({})
print(f'Total User (capitalized): {users2}')

# Sample user structure
sample = db.users.find_one({}, {'password': 0, 'refreshTokens': 0})
if sample:
    print(f'Sample user fields: {list(sample.keys())}')

client.close()
