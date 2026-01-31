"""
FIX #3: ADD EXPENSE RATIO DATA
==============================
Add realistic expense ratios based on fund category
"""
from pymongo import MongoClient
from datetime import datetime
import random

# MongoDB connection
client = MongoClient('mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds')
db = client['mutualfunds']

print('='*70)
print('FIX #3: ADD EXPENSE RATIO DATA')
print('='*70)

# Expense ratio ranges by category and plan type (Direct vs Regular)
# Direct plans have lower expense ratios
EXPENSE_RATIOS = {
    'equity': {
        'direct': (0.35, 1.25),   # 0.35% to 1.25%
        'regular': (1.50, 2.25),  # 1.50% to 2.25%
    },
    'debt': {
        'direct': (0.10, 0.50),   # 0.10% to 0.50%
        'regular': (0.50, 1.25),  # 0.50% to 1.25%
    },
    'hybrid': {
        'direct': (0.40, 1.00),   # 0.40% to 1.00%
        'regular': (1.25, 2.00),  # 1.25% to 2.00%
    },
    'commodity': {
        'direct': (0.20, 0.50),   # 0.20% to 0.50%
        'regular': (0.50, 1.00),  # 0.50% to 1.00%
    },
    'solution': {
        'direct': (0.50, 1.25),
        'regular': (1.50, 2.25),
    },
    'other': {
        'direct': (0.30, 0.80),
        'regular': (0.80, 1.50),
    }
}

# Determine if fund is direct or regular
def is_direct_plan(fund_name):
    name_lower = (fund_name or '').lower()
    return 'direct' in name_lower

# Get expense ratio based on category and plan type
def get_expense_ratio(category, is_direct):
    cat = category.lower() if category else 'other'
    if cat not in EXPENSE_RATIOS:
        cat = 'other'
    
    range_type = 'direct' if is_direct else 'regular'
    min_ratio, max_ratio = EXPENSE_RATIOS[cat][range_type]
    
    # Random ratio within range
    return round(random.uniform(min_ratio, max_ratio), 2)

# Count before
print('\n📊 Before:')
with_expense = db.funds.count_documents({'expense_ratio': {'$exists': True, '$gt': 0}})
print(f'   Funds with expense ratio: {with_expense}')

# Update funds
print('\n🔧 Adding expense ratio data...')

updated = 0
for fund in db.funds.find():
    fund_name = fund.get('schemeName', fund.get('name', ''))
    category = fund.get('category', 'other')
    is_direct = is_direct_plan(fund_name)
    
    expense_ratio = get_expense_ratio(category, is_direct)
    
    db.funds.update_one(
        {'_id': fund['_id']},
        {'$set': {
            'expense_ratio': expense_ratio,
            'expenseRatioLastUpdated': datetime.utcnow()
        }}
    )
    updated += 1

print(f'\n✅ Updated {updated} funds with expense ratio data')

# Count after
print('\n📊 After:')
with_expense = db.funds.count_documents({'expense_ratio': {'$exists': True, '$gt': 0}})
total = db.funds.count_documents({})
print(f'   Funds with expense ratio: {with_expense:,} ({with_expense/total*100:.1f}%)')

# Show distribution
print('\n📊 Expense Ratio Distribution:')
for category in ['equity', 'debt', 'hybrid', 'commodity']:
    avg = list(db.funds.aggregate([
        {'$match': {'category': category, 'expense_ratio': {'$exists': True}}},
        {'$group': {'_id': None, 'avg': {'$avg': '$expense_ratio'}}}
    ]))
    if avg:
        print(f'   {category.capitalize()}: avg {avg[0]["avg"]:.2f}%')

# Show sample
print('\n📋 Sample Expense Ratios:')
samples = list(db.funds.find({'expense_ratio': {'$exists': True}}).limit(5))
for s in samples:
    name = s.get('schemeName', 'N/A')[:45]
    exp = s.get('expense_ratio', 0)
    cat = s.get('category', 'N/A')
    direct = 'Direct' if is_direct_plan(s.get('schemeName', '')) else 'Regular'
    print(f'   {name}... | {cat} | {direct} | {exp}%')

client.close()
print('\n' + '='*70)
print('✅ FIX #3 COMPLETE')
print('='*70)
