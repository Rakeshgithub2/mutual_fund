"""Check fund categories and sub-categories in MongoDB"""

from pymongo import MongoClient
from collections import defaultdict

uri = 'mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds?retryWrites=true&w=majority'
client = MongoClient(uri)
db = client['mutualfunds']

# Get all unique categories
categories = db.funds.distinct('category')
valid_cats = [c for c in categories if c]
print(f'\n{"="*60}')
print(f'CATEGORIES: {len(valid_cats)} unique')
print("="*60)
for cat in sorted(valid_cats):
    count = db.funds.count_documents({'category': cat})
    print(f'  {cat}: {count} funds')

# Get all unique sub-categories
subcats = db.funds.distinct('subCategory')
valid_subcats = [s for s in subcats if s]
print(f'\n{"="*60}')
print(f'SUB-CATEGORIES: {len(valid_subcats)} unique')
print("="*60)

# Group by category -> subcategory
pipeline = [
    {'$match': {'category': {'$exists': True, '$ne': None}}},
    {'$group': {'_id': {'category': '$category', 'subCategory': '$subCategory'}, 'count': {'$sum': 1}}},
    {'$sort': {'_id.category': 1, '_id.subCategory': 1}}
]
results = list(db.funds.aggregate(pipeline))

category_subs = defaultdict(list)
for r in results:
    cat = r['_id'].get('category', 'Unknown')
    subcat = r['_id'].get('subCategory', 'N/A')
    count = r['count']
    category_subs[cat].append((subcat, count))

print(f'\n{"="*60}')
print('CATEGORY -> SUB-CATEGORIES BREAKDOWN')
print("="*60)
for cat in sorted(category_subs.keys()):
    if cat:
        total = sum(c for _, c in category_subs[cat])
        print(f'\n{cat} ({total} funds):')
        for subcat, count in category_subs[cat]:
            subcat_display = subcat if subcat else "(none)"
            print(f'    - {subcat_display}: {count}')

# AMC breakdown
print(f'\n{"="*60}')
print('AMC BREAKDOWN')
print("="*60)

# Try different field names for AMC
amc_pipeline = [
    {'$group': {'_id': '$amc.name', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}},
    {'$limit': 25}
]
amc_results = list(db.funds.aggregate(amc_pipeline))
for r in amc_results:
    name = r['_id']
    if name:
        if isinstance(name, dict):
            name = str(name)
        print(f'  {name}: {r["count"]} funds')

client.close()
print(f'\n{"="*60}')
print('SUMMARY')
print("="*60)
print(f'Total Funds: 14,216')
print(f'Total Categories: {len(valid_cats)}')
print(f'Total Sub-Categories: {len(valid_subcats)}')
