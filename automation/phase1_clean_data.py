"""
PHASE 1: DATA CLEANING
======================
Remove garbage holdings, normalize data, fix corrupted entries
"""
from pymongo import MongoClient
import re

client = MongoClient('mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds')
db = client['mutualfunds']

print('='*70)
print('PHASE 1: DATA CLEANING')
print('='*70)

# Garbage patterns to remove from holdings
GARBAGE_PATTERNS = [
    # Time periods / Return labels
    r'since inception', r'year', r'month', r'quarter', r'days',
    r'1\s*yr', r'3\s*yr', r'5\s*yr', r'10\s*yr', r'ytd',
    r'return', r'cagr', r'annualized', r'absolute',
    
    # Financial metrics
    r'nav', r'aum', r'expense ratio', r'exit load',
    r'standard deviation', r'sharpe ratio', r'beta', r'alpha',
    r'tracking error', r'information ratio', r'sortino',
    
    # Benchmark names
    r'benchmark', r'crisil', r'nifty', r'sensex', r'bse',
    r'index fund', r'etf',
    
    # Plan types
    r'direct plan', r'regular plan', r'growth', r'idcw', r'dividend',
    
    # Currency / Units
    r'^cr\.?$', r'^lacs?$', r'^crores?$', r'^rs\.?$', r'^₹',
    r'^%$', r'^\d+\.?\d*%?$',  # Just numbers or percentages
    
    # Other garbage
    r'^type of scheme', r'^investment objective', r'^fund manager',
    r'^asset allocation', r'^risk', r'^moderate', r'^high',
    r'^low', r'^rating', r'^maturity', r'^modified duration',
    r'^yield', r'^average', r'^total', r'^others?$',
    r'^equity', r'^debt', r'^cash', r'^money market',
    r'^net assets', r'^portfolio', r'^holding',
    r'^feb-', r'^jan-', r'^mar-', r'^dec-', r'^nov-',
    r'^treps', r'^cblo', r'^repo', r'^reverse repo',
    r'^sovereign', r'^aaa', r'^aa\+?', r'^a\+?',
    r'^g-?sec', r'^t-?bill', r'^treasury',
    r'^nil', r'^n/?a', r'^-+$', r'^\*+$',
    
    # Fund names as holdings (other funds)
    r'mutual fund', r'scheme', r'plan.*growth', r'plan.*idcw',
]

# Compile patterns for efficiency
GARBAGE_REGEX = [re.compile(p, re.IGNORECASE) for p in GARBAGE_PATTERNS]

def is_garbage(company_name):
    """Check if company name is garbage data"""
    if not company_name or not isinstance(company_name, str):
        return True
    
    name = company_name.strip()
    
    # Too short
    if len(name) < 3:
        return True
    
    # Check against garbage patterns
    for pattern in GARBAGE_REGEX:
        if pattern.search(name):
            return True
    
    # Contains only numbers and symbols
    if re.match(r'^[\d\s\.\,\%\-\+\(\)]+$', name):
        return True
    
    return False

def is_valid_percentage(pct):
    """Check if percentage is valid"""
    if not isinstance(pct, (int, float)):
        return False
    if pct <= 0 or pct > 25:  # Single holding > 25% is suspicious
        return False
    return True

# Stats
stats = {
    'funds_processed': 0,
    'funds_cleaned': 0,
    'holdings_removed': 0,
    'holdings_kept': 0,
    'funds_emptied': 0,  # Funds where all holdings were garbage
}

print('\n📊 Before Cleaning:')
total_funds = db.funds.count_documents({})
with_holdings = db.funds.count_documents({'holdings': {'$exists': True, '$not': {'$size': 0}}})
print(f'   Total Funds: {total_funds:,}')
print(f'   With Holdings: {with_holdings:,} ({with_holdings/total_funds*100:.1f}%)')

print('\n🧹 Cleaning garbage holdings...\n')

# Process all funds with holdings
funds = db.funds.find({'holdings': {'$exists': True, '$not': {'$size': 0}}})

for fund in funds:
    stats['funds_processed'] += 1
    holdings = fund.get('holdings', [])
    original_count = len(holdings)
    
    # Filter out garbage holdings
    clean_holdings = []
    for h in holdings:
        if isinstance(h, dict):
            company = h.get('company', h.get('name', h.get('stock', '')))
            pct = h.get('percentage', h.get('weight', h.get('allocation', 0)))
            
            if is_garbage(company):
                stats['holdings_removed'] += 1
                continue
            
            if not is_valid_percentage(pct):
                stats['holdings_removed'] += 1
                continue
            
            # Keep this holding
            clean_holdings.append(h)
            stats['holdings_kept'] += 1
    
    # Update if changed
    if len(clean_holdings) != original_count:
        stats['funds_cleaned'] += 1
        
        if len(clean_holdings) == 0:
            stats['funds_emptied'] += 1
            # Remove holdings entirely if all were garbage
            db.funds.update_one(
                {'_id': fund['_id']},
                {'$unset': {'holdings': '', 'sector_allocation': ''}}
            )
        else:
            db.funds.update_one(
                {'_id': fund['_id']},
                {'$set': {'holdings': clean_holdings}}
            )
        
        if stats['funds_cleaned'] <= 10:
            fund_name = fund.get('name', 'N/A')[:40]
            print(f'   ✓ {fund_name}: {original_count} → {len(clean_holdings)} holdings')

print(f'\n' + '='*70)
print('PHASE 1 RESULTS')
print('='*70)
print(f'\n📊 Cleaning Statistics:')
print(f'   Funds Processed:   {stats["funds_processed"]:,}')
print(f'   Funds Cleaned:     {stats["funds_cleaned"]:,}')
print(f'   Funds Emptied:     {stats["funds_emptied"]:,} (all holdings were garbage)')
print(f'   Holdings Removed:  {stats["holdings_removed"]:,}')
print(f'   Holdings Kept:     {stats["holdings_kept"]:,}')

# After stats
print('\n📊 After Cleaning:')
with_holdings_after = db.funds.count_documents({'holdings': {'$exists': True, '$not': {'$size': 0}}})
print(f'   Total Funds: {total_funds:,}')
print(f'   With Holdings: {with_holdings_after:,} ({with_holdings_after/total_funds*100:.1f}%)')
print(f'   Change: {with_holdings} → {with_holdings_after} ({with_holdings_after - with_holdings:+,})')

# Sample of cleaned data
print('\n📋 Sample Cleaned Holdings:')
sample = db.funds.find_one({
    'holdings': {'$exists': True, '$not': {'$size': 0}},
    'amc.name': 'HDFC Mutual Fund'
})

if sample:
    print(f'   Fund: {sample.get("name", "N/A")}')
    for h in sample.get('holdings', [])[:5]:
        print(f'   → {h.get("company", "N/A")}: {h.get("percentage", 0)}%')

client.close()
print('\n' + '='*70)
print('✅ PHASE 1 COMPLETE')
print('='*70)
