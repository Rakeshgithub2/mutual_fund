"""
FIX #1: CLEAN GARBAGE HOLDINGS
==============================
Remove garbage holdings entries like "Since Inception", "Year", etc.
"""
from pymongo import MongoClient
from datetime import datetime

# MongoDB connection
client = MongoClient('mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds')
db = client['mutualfunds']

print('='*70)
print('FIX #1: CLEAN GARBAGE HOLDINGS')
print('='*70)

# Garbage patterns to remove
GARBAGE_PATTERNS = [
    'Since Inception', 'Year', 'Years', 'Month', 'Months', 'Week',
    'Annualized', 'CAGR', 'Benchmark', 'Returns', 'NAV', 'Date',
    'Inception Date', 'Fund Manager', 'Expense Ratio', 'Exit Load',
    'Min Investment', 'SIP', 'Lumpsum', 'AUM', 'Category', 'Risk',
    'Rating', 'Rank', 'Quartile', 'Percentile', 'Alpha', 'Beta',
    'Sharpe', 'Sortino', 'Standard Deviation', 'Volatility',
    'As on', 'As of', 'Data as', 'Updated', 'Last Updated'
]

# Count before
print('\n📊 Before Cleaning:')
for pattern in GARBAGE_PATTERNS[:5]:
    count = db.funds.count_documents({'holdings.company': pattern})
    if count > 0:
        print(f'   Funds with "{pattern}": {count}')

# Find and fix funds with garbage holdings
print('\n🔧 Cleaning garbage holdings...')

fixed = 0
for fund in db.funds.find({'holdings': {'$exists': True, '$not': {'$size': 0}}}):
    holdings = fund.get('holdings', [])
    
    # Filter out garbage
    clean_holdings = []
    for h in holdings:
        company = str(h.get('company', ''))
        
        # Check if this is garbage
        is_garbage = False
        for pattern in GARBAGE_PATTERNS:
            if pattern.lower() == company.lower() or company.lower().startswith(pattern.lower()):
                is_garbage = True
                break
        
        # Also check for numeric-only or very short names
        if not is_garbage:
            # Remove entries that are just numbers or dates
            if company.replace('.', '').replace('-', '').replace(' ', '').isdigit():
                is_garbage = True
            elif len(company) < 3:
                is_garbage = True
        
        if not is_garbage:
            clean_holdings.append(h)
    
    # Update if we removed any garbage
    if len(clean_holdings) != len(holdings):
        # Recalculate sector allocation
        from collections import defaultdict
        sector_totals = defaultdict(float)
        for h in clean_holdings:
            sector = h.get('sector', 'Others')
            pct = h.get('percentage', 0)
            sector_totals[sector] += pct
        
        sector_allocation = [
            {'sector': sector, 'percentage': round(pct, 2)}
            for sector, pct in sorted(sector_totals.items(), key=lambda x: -x[1])
        ]
        
        db.funds.update_one(
            {'_id': fund['_id']},
            {'$set': {
                'holdings': clean_holdings,
                'sector_allocation': sector_allocation,
                'holdingsLastUpdated': datetime.utcnow()
            }}
        )
        fixed += 1

print(f'\n✅ Fixed {fixed} funds')

# Count after
print('\n📊 After Cleaning:')
for pattern in GARBAGE_PATTERNS[:5]:
    count = db.funds.count_documents({'holdings.company': pattern})
    print(f'   Funds with "{pattern}": {count}')

# Final stats
total = db.funds.count_documents({})
with_holdings = db.funds.count_documents({'holdings': {'$exists': True, '$not': {'$size': 0}}})
print(f'\n📊 Final Stats:')
print(f'   Total Funds: {total:,}')
print(f'   With Holdings: {with_holdings:,} ({with_holdings/total*100:.1f}%)')

client.close()
print('\n' + '='*70)
print('✅ FIX #1 COMPLETE')
print('='*70)
