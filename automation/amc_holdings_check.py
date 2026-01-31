"""
Check Holdings & Sector Allocation for Top AMCs
"""
from pymongo import MongoClient

client = MongoClient('mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds')
db = client['mutualfunds']

print('='*80)
print('TOP AMCs - HOLDINGS & SECTOR ALLOCATION ANALYSIS')
print('='*80)

top_amcs = [
    'ICICI Prudential Mutual Fund',
    'Nippon India Mutual Fund',
    'UTI Mutual Fund',
    'Kotak Mahindra Mutual Fund',
    'HDFC Mutual Fund',
    'SBI Mutual Fund'
]

summary_data = []

for amc_name in top_amcs:
    print(f'\n🏢 {amc_name}')
    print('-'*70)
    
    # Get all funds for this AMC
    total = db.funds.count_documents({'amc.name': amc_name})
    with_holdings = db.funds.count_documents({
        'amc.name': amc_name,
        'holdings': {'$exists': True, '$not': {'$size': 0}, '$ne': None}
    })
    with_sectors = db.funds.count_documents({
        'amc.name': amc_name,
        'sector_allocation': {'$exists': True, '$not': {'$size': 0}, '$ne': None}
    })
    
    hold_pct = (with_holdings/total*100) if total > 0 else 0
    sect_pct = (with_sectors/total*100) if total > 0 else 0
    
    summary_data.append({
        'amc': amc_name,
        'total': total,
        'holdings': with_holdings,
        'hold_pct': hold_pct,
        'sectors': with_sectors,
        'sect_pct': sect_pct
    })
    
    print(f'   Total Funds: {total}')
    print(f'   With Holdings: {with_holdings} ({hold_pct:.1f}%)')
    print(f'   With Sectors:  {with_sectors} ({sect_pct:.1f}%)')
    
    # Category breakdown
    print(f'\n   📊 By Category:')
    pipeline = [
        {'$match': {'amc.name': amc_name}},
        {'$group': {
            '_id': '$category',
            'total': {'$sum': 1},
            'with_holdings': {
                '$sum': {'$cond': [
                    {'$and': [
                        {'$ne': ['$holdings', None]},
                        {'$ne': ['$holdings', []]},
                        {'$gt': [{'$size': {'$ifNull': ['$holdings', []]}}, 0]}
                    ]},
                    1, 0
                ]}
            },
            'with_sectors': {
                '$sum': {'$cond': [
                    {'$and': [
                        {'$ne': ['$sector_allocation', None]},
                        {'$ne': ['$sector_allocation', []]},
                        {'$gt': [{'$size': {'$ifNull': ['$sector_allocation', []]}}, 0]}
                    ]},
                    1, 0
                ]}
            }
        }},
        {'$sort': {'total': -1}}
    ]
    categories = list(db.funds.aggregate(pipeline))
    
    header = f"{'Category':20} {'Total':>8} {'Holdings':>12} {'Sectors':>12}"
    print(f'   {header}')
    print(f'   ' + '-'*55)
    for cat in categories:
        cat_name = cat['_id'] if cat['_id'] else 'Other'
        h_pct = (cat['with_holdings']/cat['total']*100) if cat['total'] > 0 else 0
        s_pct = (cat['with_sectors']/cat['total']*100) if cat['total'] > 0 else 0
        row = f"{cat_name:20} {cat['total']:>8} {cat['with_holdings']:>5} ({h_pct:>3.0f}%) {cat['with_sectors']:>5} ({s_pct:>3.0f}%)"
        print(f'   {row}')

    # Sub-category breakdown for equity
    print(f'\n   📈 Equity Sub-Categories (Top 10):')
    pipeline = [
        {'$match': {'amc.name': amc_name, 'category': 'equity'}},
        {'$group': {
            '_id': '$sub_category',
            'total': {'$sum': 1},
            'with_holdings': {
                '$sum': {'$cond': [
                    {'$gt': [{'$size': {'$ifNull': ['$holdings', []]}}, 0]},
                    1, 0
                ]}
            }
        }},
        {'$sort': {'total': -1}},
        {'$limit': 10}
    ]
    subcats = list(db.funds.aggregate(pipeline))
    
    subheader = f"{'Sub-Category':28} {'Total':>6} {'Holdings':>12}"
    print(f'   {subheader}')
    print(f'   ' + '-'*48)
    for subcat in subcats:
        sub_name = (subcat['_id'] or 'Other')[:28]
        h_pct = (subcat['with_holdings']/subcat['total']*100) if subcat['total'] > 0 else 0
        subrow = f"{sub_name:28} {subcat['total']:>6} {subcat['with_holdings']:>5} ({h_pct:>3.0f}%)"
        print(f'   {subrow}')

# Summary Table
print('\n' + '='*80)
print('📊 SUMMARY - TOP 6 AMCs HOLDINGS COVERAGE')
print('='*80)
print(f"\n{'AMC':40} {'Total':>8} {'Holdings':>12} {'Sectors':>12}")
print('-'*75)
for s in summary_data:
    short_name = s['amc'].replace(' Mutual Fund', '')
    row = f"{short_name:40} {s['total']:>8} {s['holdings']:>5} ({s['hold_pct']:>4.1f}%) {s['sectors']:>5} ({s['sect_pct']:>4.1f}%)"
    print(row)

total_funds = sum(s['total'] for s in summary_data)
total_holdings = sum(s['holdings'] for s in summary_data)
total_sectors = sum(s['sectors'] for s in summary_data)
print('-'*75)
print(f"{'TOTAL':40} {total_funds:>8} {total_holdings:>5} ({total_holdings/total_funds*100:>4.1f}%) {total_sectors:>5} ({total_sectors/total_funds*100:>4.1f}%)")

# Check what users actually see
print('\n' + '='*80)
print('👁️ WHAT USERS SEE - SAMPLE FUND DATA')
print('='*80)

# Show sample fund with holdings
sample = db.funds.find_one({
    'amc.name': 'HDFC Mutual Fund',
    'holdings': {'$exists': True, '$not': {'$size': 0}}
})

if sample:
    print(f'\n✅ Sample Fund WITH Holdings:')
    print(f'   Name: {sample.get("name", "N/A")}')
    print(f'   Category: {sample.get("category", "N/A")} / {sample.get("sub_category", "N/A")}')
    holdings = sample.get('holdings', [])
    print(f'   Holdings Count: {len(holdings)}')
    if holdings:
        print(f'   Top 5 Holdings:')
        for h in holdings[:5]:
            if isinstance(h, dict):
                name = h.get('name', h.get('stock', h.get('company', 'Unknown')))
                pct = h.get('percentage', h.get('weight', h.get('allocation', 'N/A')))
                print(f'     - {name}: {pct}%')
    sectors = sample.get('sector_allocation', [])
    print(f'   Sector Allocation: {len(sectors)} sectors')
    if sectors:
        for s in sectors[:5]:
            if isinstance(s, dict):
                name = s.get('sector', s.get('name', 'Unknown'))
                pct = s.get('percentage', s.get('weight', s.get('allocation', 'N/A')))
                print(f'     - {name}: {pct}%')

# Show sample fund without holdings
sample_no = db.funds.find_one({
    'amc.name': 'HDFC Mutual Fund',
    '$or': [
        {'holdings': {'$exists': False}},
        {'holdings': None},
        {'holdings': []}
    ]
})

if sample_no:
    print(f'\n❌ Sample Fund WITHOUT Holdings:')
    print(f'   Name: {sample_no.get("name", "N/A")}')
    print(f'   Category: {sample_no.get("category", "N/A")} / {sample_no.get("sub_category", "N/A")}')
    print(f'   Holdings: None/Empty - Users will see empty section')

# Check if holdings have proper structure
print('\n' + '='*80)
print('🔍 HOLDINGS DATA STRUCTURE CHECK')
print('='*80)

# Check a few random funds with holdings
funds_with_holdings = list(db.funds.find(
    {'holdings': {'$exists': True, '$not': {'$size': 0}}},
    {'name': 1, 'holdings': {'$slice': 2}, 'amc.name': 1}
).limit(5))

print('\nSample Holdings Structure:')
for f in funds_with_holdings:
    print(f'\n   Fund: {f.get("name", "N/A")[:50]}')
    print(f'   AMC: {f.get("amc", {}).get("name", "N/A")}')
    for h in f.get('holdings', [])[:2]:
        print(f'   Holding: {h}')

client.close()
print('\n' + '='*80)
print('ANALYSIS COMPLETE')
print('='*80)
