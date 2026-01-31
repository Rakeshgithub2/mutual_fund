"""
FULL SYSTEM AUDIT
==================
Comprehensive audit of the mutual fund platform
"""
from pymongo import MongoClient
from datetime import datetime
import json

# MongoDB connection
client = MongoClient('mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds')
db = client['mutualfunds']

print('='*80)
print('🔍 FULL SYSTEM AUDIT - MUTUAL FUND PLATFORM')
print('='*80)
print(f'Audit Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('='*80)

# ============================================================================
# PART 1: DATABASE ANALYSIS
# ============================================================================
print('\n' + '='*80)
print('📊 PART 1: DATABASE ANALYSIS')
print('='*80)

# Total counts
total_funds = db.funds.count_documents({})
equity_funds = db.funds.count_documents({'category': 'equity'})
debt_funds = db.funds.count_documents({'category': 'debt'})
hybrid_funds = db.funds.count_documents({'category': 'hybrid'})
commodity_funds = db.funds.count_documents({'category': {'$in': ['commodity', 'gold', 'other']}})
solution_funds = db.funds.count_documents({'category': 'solution'})

print('\n📈 FUND COUNTS BY CATEGORY:')
print(f'   Total Funds:     {total_funds:,}')
print(f'   Equity Funds:    {equity_funds:,}')
print(f'   Debt Funds:      {debt_funds:,}')
print(f'   Hybrid Funds:    {hybrid_funds:,}')
print(f'   Commodity/Gold:  {commodity_funds:,}')
print(f'   Solution Funds:  {solution_funds:,}')

# Data availability checks
print('\n📋 DATA AVAILABILITY PER FUND:')

basic_metadata = db.funds.count_documents({'schemeName': {'$exists': True}})
with_amc = db.funds.count_documents({'amc': {'$exists': True}})
with_nav = db.funds.count_documents({'nav': {'$exists': True}})
with_returns = db.funds.count_documents({'returns': {'$exists': True}})
with_holdings = db.funds.count_documents({'holdings': {'$exists': True, '$not': {'$size': 0}}})
with_sectors = db.funds.count_documents({'sector_allocation': {'$exists': True, '$not': {'$size': 0}}})
with_fund_manager = db.funds.count_documents({'fund_manager': {'$exists': True}})
with_market_cap = db.funds.count_documents({'market_cap_allocation': {'$exists': True}})
with_expense_ratio = db.funds.count_documents({'expense_ratio': {'$exists': True}})
with_aum = db.funds.count_documents({'aum': {'$exists': True}})

print(f'''
| Data Type                    | Fund Count | Percentage |
|------------------------------|------------|------------|
| Basic fund metadata          | {basic_metadata:>10,} | {basic_metadata/total_funds*100:>9.1f}% |
| AMC details                  | {with_amc:>10,} | {with_amc/total_funds*100:>9.1f}% |
| NAV data                     | {with_nav:>10,} | {with_nav/total_funds*100:>9.1f}% |
| Returns data                 | {with_returns:>10,} | {with_returns/total_funds*100:>9.1f}% |
| Holdings available           | {with_holdings:>10,} | {with_holdings/total_funds*100:>9.1f}% |
| Sector allocation            | {with_sectors:>10,} | {with_sectors/total_funds*100:>9.1f}% |
| Fund manager details         | {with_fund_manager:>10,} | {with_fund_manager/total_funds*100:>9.1f}% |
| Market cap allocation        | {with_market_cap:>10,} | {with_market_cap/total_funds*100:>9.1f}% |
| Expense ratio                | {with_expense_ratio:>10,} | {with_expense_ratio/total_funds*100:>9.1f}% |
| AUM data                     | {with_aum:>10,} | {with_aum/total_funds*100:>9.1f}% |
''')

# Data authenticity check
print('\n🔍 DATA AUTHENTICITY CHECK:')

# Check for mock/sample data patterns
mock_patterns = [
    'sample', 'mock', 'test', 'demo', 'fake', 'placeholder', 'example'
]

# Check holdings for mock data
mock_holdings = 0
real_holdings = 0
holdings_sources = {}

for fund in db.funds.find({'holdings': {'$exists': True, '$not': {'$size': 0}}}):
    source = fund.get('holdingsSource', 'Unknown')
    holdings_sources[source] = holdings_sources.get(source, 0) + 1
    
    holdings = fund.get('holdings', [])
    is_mock = False
    for h in holdings:
        company = str(h.get('company', '')).lower()
        for pattern in mock_patterns:
            if pattern in company:
                is_mock = True
                break
    
    if is_mock:
        mock_holdings += 1
    else:
        real_holdings += 1

print(f'\n   Holdings Classification:')
print(f'   ├── Real-world data:   {real_holdings:,} funds')
print(f'   └── Mock/sample data:  {mock_holdings:,} funds')

print(f'\n   Holdings Sources:')
for source, count in sorted(holdings_sources.items(), key=lambda x: -x[1]):
    print(f'   ├── {source}: {count:,} funds')

# Check sectors for quality
real_sectors = db.funds.count_documents({
    'sector_allocation': {'$exists': True, '$not': {'$size': 0}},
    'sector_allocation.0.sector': {'$nin': ['Not Available', 'N/A', '', None, 'Others']}
})

print(f'\n   Sector Allocation Quality:')
print(f'   ├── With real sectors:     {real_sectors:,} funds')
print(f'   └── With "Others" only:    {with_sectors - real_sectors:,} funds')

# ============================================================================
# PART 2: STORAGE AUDIT
# ============================================================================
print('\n' + '='*80)
print('💾 PART 2: STORAGE AUDIT (512 MB FREE TIER)')
print('='*80)

# Get database stats
db_stats = db.command('dbStats')
data_size = db_stats.get('dataSize', 0) / (1024 * 1024)  # Convert to MB
storage_size = db_stats.get('storageSize', 0) / (1024 * 1024)
index_size = db_stats.get('indexSize', 0) / (1024 * 1024)
total_size = data_size + index_size

free_tier_limit = 512
remaining = free_tier_limit - total_size
avg_per_fund = total_size / total_funds if total_funds > 0 else 0
max_funds = int(free_tier_limit / avg_per_fund) if avg_per_fund > 0 else 0

# User estimation (rough: 100KB per concurrent user session)
safe_users = int((remaining * 1024) / 100)  # 100KB per user

print(f'''
| Metric                  | Value              |
|-------------------------|-------------------|
| Current data size       | {data_size:>10.2f} MB     |
| Index size              | {index_size:>10.2f} MB     |
| Total storage used      | {total_size:>10.2f} MB     |
| Free tier limit         | {free_tier_limit:>10.0f} MB     |
| Remaining capacity      | {remaining:>10.2f} MB     |
| Usage percentage        | {total_size/free_tier_limit*100:>10.1f}%      |
| Avg storage per fund    | {avg_per_fund*1024:>10.2f} KB     |
| Max funds supported     | {max_funds:>10,} funds  |
| Safe user concurrency   | {safe_users:>10,} users  |
''')

# ============================================================================
# PART 3: COLLECTION ANALYSIS
# ============================================================================
print('\n' + '='*80)
print('📂 PART 3: COLLECTION ANALYSIS')
print('='*80)

collections = db.list_collection_names()
print(f'\n   Collections in database: {len(collections)}')
for coll in collections:
    count = db[coll].count_documents({})
    print(f'   ├── {coll}: {count:,} documents')

# ============================================================================
# PART 4: AMC COVERAGE ANALYSIS
# ============================================================================
print('\n' + '='*80)
print('🏢 PART 4: AMC COVERAGE ANALYSIS')
print('='*80)

# Get AMC stats
pipeline = [
    {'$group': {
        '_id': '$amc.name',
        'count': {'$sum': 1},
        'with_holdings': {'$sum': {'$cond': [{'$gt': [{'$size': {'$ifNull': ['$holdings', []]}}, 0]}, 1, 0]}},
        'with_sectors': {'$sum': {'$cond': [{'$gt': [{'$size': {'$ifNull': ['$sector_allocation', []]}}, 0]}, 1, 0]}}
    }},
    {'$sort': {'count': -1}},
    {'$limit': 15}
]

amc_stats = list(db.funds.aggregate(pipeline))
print(f'\n   Top 15 AMCs by Fund Count:')
print(f'   {"AMC Name":<40} {"Total":>8} {"Holdings":>10} {"Sectors":>10}')
print(f'   {"-"*40} {"-"*8} {"-"*10} {"-"*10}')

for amc in amc_stats:
    name = (amc['_id'] or 'Unknown')[:40]
    total = amc['count']
    holdings = amc['with_holdings']
    sectors = amc['with_sectors']
    h_pct = holdings/total*100 if total > 0 else 0
    s_pct = sectors/total*100 if total > 0 else 0
    print(f'   {name:<40} {total:>8} {holdings:>6} ({h_pct:>3.0f}%) {sectors:>6} ({s_pct:>3.0f}%)')

# ============================================================================
# PART 5: SAMPLE DATA INSPECTION
# ============================================================================
print('\n' + '='*80)
print('🔬 PART 5: SAMPLE DATA INSPECTION')
print('='*80)

# Get sample funds with good data
sample_good = db.funds.find_one({
    'holdings': {'$exists': True, '$not': {'$size': 0}},
    'sector_allocation': {'$exists': True, '$not': {'$size': 0}},
    'category': 'equity'
})

if sample_good:
    print('\n✅ SAMPLE FUND WITH COMPLETE DATA:')
    print(f'   Scheme Name: {sample_good.get("schemeName", "N/A")[:60]}')
    print(f'   Scheme Code: {sample_good.get("schemeCode", "N/A")}')
    print(f'   Category: {sample_good.get("category", "N/A")} / {sample_good.get("subCategory", "N/A")}')
    print(f'   AMC: {sample_good.get("amc", {}).get("name", "N/A") if isinstance(sample_good.get("amc"), dict) else sample_good.get("amc", "N/A")}')
    
    holdings = sample_good.get('holdings', [])
    print(f'\n   Holdings ({len(holdings)} items):')
    for h in holdings[:5]:
        print(f'   ├── {h.get("company", "N/A")}: {h.get("percentage", 0)}% ({h.get("sector", "N/A")})')
    
    sectors = sample_good.get('sector_allocation', [])
    print(f'\n   Sector Allocation ({len(sectors)} sectors):')
    for s in sectors[:5]:
        print(f'   ├── {s.get("sector", "N/A")}: {s.get("percentage", 0)}%')

# Get sample fund with missing data
sample_bad = db.funds.find_one({
    '$or': [
        {'holdings': {'$exists': False}},
        {'holdings': {'$size': 0}}
    ]
})

if sample_bad:
    print('\n⚠️ SAMPLE FUND WITH MISSING DATA:')
    print(f'   Scheme Name: {sample_bad.get("schemeName", "N/A")[:60]}')
    print(f'   Scheme Code: {sample_bad.get("schemeCode", "N/A")}')
    print(f'   Category: {sample_bad.get("category", "N/A")}')
    print(f'   Holdings: {"Empty" if not sample_bad.get("holdings") else len(sample_bad.get("holdings", []))}')
    print(f'   Sectors: {"Empty" if not sample_bad.get("sector_allocation") else len(sample_bad.get("sector_allocation", []))}')

# ============================================================================
# PART 6: USER COLLECTION CHECK
# ============================================================================
print('\n' + '='*80)
print('👤 PART 6: USER & AUTH COLLECTION CHECK')
print('='*80)

if 'users' in collections:
    user_count = db.users.count_documents({})
    print(f'\n   Users collection: {user_count} documents')
    
    # Check user structure
    sample_user = db.users.find_one({}, {'password': 0})
    if sample_user:
        print(f'   User fields: {list(sample_user.keys())}')
else:
    print('\n   ⚠️ Users collection not found')

# Check for sessions/tokens
if 'sessions' in collections:
    session_count = db.sessions.count_documents({})
    print(f'   Sessions collection: {session_count} documents')

# ============================================================================
# PART 7: DATA QUALITY ISSUES
# ============================================================================
print('\n' + '='*80)
print('⚠️ PART 7: DATA QUALITY ISSUES')
print('='*80)

issues = []

# Check for funds without scheme name
no_name = db.funds.count_documents({'schemeName': {'$exists': False}})
if no_name > 0:
    issues.append(f'❌ {no_name} funds without scheme name')

# Check for funds without category
no_category = db.funds.count_documents({'category': {'$exists': False}})
if no_category > 0:
    issues.append(f'❌ {no_category} funds without category')

# Check for funds with garbage holdings
garbage_patterns = ['Since Inception', 'Year', 'Month', 'Annualized', 'CAGR', 'Benchmark']
for pattern in garbage_patterns:
    count = db.funds.count_documents({'holdings.company': pattern})
    if count > 0:
        issues.append(f'⚠️ {count} funds with garbage holding "{pattern}"')

# Check for empty holdings arrays
empty_holdings = db.funds.count_documents({'holdings': {'$size': 0}})
if empty_holdings > 0:
    issues.append(f'⚠️ {empty_holdings} funds with empty holdings array')

# Check for missing sectors on funds with holdings
has_holdings_no_sectors = db.funds.count_documents({
    'holdings': {'$exists': True, '$not': {'$size': 0}},
    '$or': [
        {'sector_allocation': {'$exists': False}},
        {'sector_allocation': {'$size': 0}}
    ]
})
if has_holdings_no_sectors > 0:
    issues.append(f'⚠️ {has_holdings_no_sectors} funds with holdings but no sectors')

if issues:
    print('\n   Issues Found:')
    for issue in issues:
        print(f'   {issue}')
else:
    print('\n   ✅ No major data quality issues found')

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print('\n' + '='*80)
print('📋 FINAL AUDIT SUMMARY')
print('='*80)

# Calculate scores
holdings_score = with_holdings / total_funds * 100
sectors_score = with_sectors / total_funds * 100
mock_percentage = mock_holdings / with_holdings * 100 if with_holdings > 0 else 0
storage_score = (1 - total_size / free_tier_limit) * 100

print(f'''
┌────────────────────────────────────────────────────────────────────┐
│ MUTUAL FUND PLATFORM - SYSTEM AUDIT REPORT                        │
├────────────────────────────────────────────────────────────────────┤
│ 1. Total funds in database:        {total_funds:>10,}                     │
│ 2. Funds with holdings:            {with_holdings:>10,} ({holdings_score:.1f}%)             │
│ 3. Funds with sector allocation:   {with_sectors:>10,} ({sectors_score:.1f}%)             │
│ 4. Funds with mock data:           {mock_holdings:>10,} ({mock_percentage:.1f}%)              │
│ 5. Current MongoDB usage:          {total_size:>10.2f} MB / 512 MB        │
│ 6. Remaining storage:              {remaining:>10.2f} MB                  │
│ 7. Safe concurrent users:          {safe_users:>10,} users               │
├────────────────────────────────────────────────────────────────────┤
│ DATA COVERAGE SCORES                                               │
├────────────────────────────────────────────────────────────────────┤
│ Holdings Coverage:     {'█' * int(holdings_score/5)}{'░' * (20-int(holdings_score/5))} {holdings_score:>5.1f}%           │
│ Sector Coverage:       {'█' * int(sectors_score/5)}{'░' * (20-int(sectors_score/5))} {sectors_score:>5.1f}%           │
│ Storage Available:     {'█' * int(storage_score/5)}{'░' * (20-int(storage_score/5))} {storage_score:>5.1f}%           │
├────────────────────────────────────────────────────────────────────┤
│ PRODUCTION READINESS                                               │
├────────────────────────────────────────────────────────────────────┤
''')

# Determine readiness
readiness_issues = []
if holdings_score < 80:
    readiness_issues.append('Holdings coverage below 80%')
if sectors_score < 80:
    readiness_issues.append('Sector coverage below 80%')
if mock_percentage > 10:
    readiness_issues.append('Mock data above 10%')
if total_size > free_tier_limit * 0.9:
    readiness_issues.append('Storage above 90%')

if len(readiness_issues) == 0:
    print('│ ✅ PRODUCTION READY                                              │')
    print('│    All systems are functioning correctly with real data.        │')
elif len(readiness_issues) <= 2:
    print('│ ⚠️ NEEDS ATTENTION                                               │')
    for issue in readiness_issues:
        print(f'│    - {issue:<55} │')
else:
    print('│ ❌ NOT PRODUCTION READY                                          │')
    for issue in readiness_issues:
        print(f'│    - {issue:<55} │')

print('└────────────────────────────────────────────────────────────────────┘')

client.close()
print('\n' + '='*80)
print('✅ AUDIT COMPLETE')
print('='*80)
