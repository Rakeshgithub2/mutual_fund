from pymongo import MongoClient
client = MongoClient('mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds?retryWrites=true&w=majority')
db = client['mutualfunds']

# Direct update test
result = db.funds.update_one(
    {'schemeCode': '118632'},
    {'$set': {
        'topHoldings': [
            {'name': 'HDFC Bank Ltd', 'sector': 'Financial Services', 'percentage': 9.0},
            {'name': 'Reliance Industries Ltd', 'sector': 'Oil & Gas', 'percentage': 8.3},
            {'name': 'ICICI Bank Ltd', 'sector': 'Financial Services', 'percentage': 7.6}
        ],
        'holdingsSource': 'REAL_TEST'
    }}
)
print(f'Matched: {result.matched_count}, Modified: {result.modified_count}')

# Verify
fund = db.funds.find_one({'schemeCode': '118632'})
holdings = fund.get('topHoldings', [])
print(f'Holdings in fund: {len(holdings)}')
print(f'Source: {fund.get("holdingsSource")}')
for h in holdings:
    print(f'  - {h}')

# Count all with holdings
count = db.funds.count_documents({'topHoldings.0': {'$exists': True}})
print(f'\nTotal funds with holdings: {count}')

client.close()
