"""
Comprehensive Database Analysis Script
"""
from pymongo import MongoClient

client = MongoClient('mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds')
db = client['mutualfunds']

print('='*70)
print('COMPREHENSIVE DATABASE ANALYSIS')
print('='*70)

# 1. Storage Stats
stats = db.command('dbStats')
storage_used_mb = stats['storageSize'] / (1024 * 1024)
data_size_mb = stats['dataSize'] / (1024 * 1024)
index_size_mb = stats['indexSize'] / (1024 * 1024)
total_used_mb = storage_used_mb + index_size_mb
free_tier_limit = 512  # MongoDB Atlas free tier
remaining_mb = free_tier_limit - total_used_mb
usage_percent = (total_used_mb / free_tier_limit) * 100

print(f'\n📦 STORAGE ANALYSIS (MongoDB Atlas Free Tier: 512 MB)')
print('-'*50)
print(f'   Data Size:      {data_size_mb:.2f} MB')
print(f'   Storage Size:   {storage_used_mb:.2f} MB')
print(f'   Index Size:     {index_size_mb:.2f} MB')
print(f'   Total Used:     {total_used_mb:.2f} MB ({usage_percent:.1f}%)')
print(f'   Remaining:      {remaining_mb:.2f} MB ({100-usage_percent:.1f}%)')

# Visual storage bar
bar_len = 40
filled = int(bar_len * usage_percent / 100)
bar = '█' * filled + '░' * (bar_len - filled)
print(f'\n   [{bar}] {usage_percent:.1f}%')

# 2. All Collections Overview
print(f'\n📊 COLLECTIONS OVERVIEW')
print('-'*50)
collections = db.list_collection_names()
collection_stats = []
for coll_name in sorted(collections):
    coll = db[coll_name]
    count = coll.count_documents({})
    stats_coll = db.command('collStats', coll_name)
    size_kb = stats_coll['size'] / 1024
    collection_stats.append({'name': coll_name, 'count': count, 'size_kb': size_kb})
    print(f'   {coll_name:30} {count:>8} docs  ({size_kb:.1f} KB)')

# 3. Funds with Holdings & Sectors
print(f'\n🏦 FUNDS HOLDINGS & SECTORS')
print('-'*50)
total_funds = db.funds.count_documents({})
with_holdings = db.funds.count_documents({'holdings': {'$exists': True, '$not': {'$size': 0}, '$ne': None}})
with_sectors = db.funds.count_documents({'sector_allocation': {'$exists': True, '$not': {'$size': 0}, '$ne': None}})
without_holdings = total_funds - with_holdings
print(f'   Total Funds:            {total_funds:,}')
print(f'   With Holdings:          {with_holdings:,} ({with_holdings/total_funds*100:.1f}%)')
print(f'   With Sector Allocation: {with_sectors:,} ({with_sectors/total_funds*100:.1f}%)')
print(f'   Without Holdings:       {without_holdings:,} ({without_holdings/total_funds*100:.1f}%)')

# 4. Category Breakdown
print(f'\n📁 FUNDS BY CATEGORY')
print('-'*50)
pipeline = [
    {'$group': {'_id': '$category', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]
categories = list(db.funds.aggregate(pipeline))
for cat in categories:
    cat_name = cat['_id'] if cat['_id'] else 'Uncategorized'
    cnt = cat['count']
    print(f'   {cat_name:35} {cnt:>6}')

# 5. Holdings by Category
print(f'\n📊 HOLDINGS COVERAGE BY CATEGORY')
print('-'*50)
for cat in categories[:15]:  # Top 15
    cat_name = cat['_id'] if cat['_id'] else 'Uncategorized'
    cat_filter = {'category': cat['_id']} if cat['_id'] else {'category': None}
    total_in_cat = cat['count']
    with_hold = db.funds.count_documents({**cat_filter, 'holdings': {'$exists': True, '$not': {'$size': 0}}})
    pct = (with_hold / total_in_cat * 100) if total_in_cat > 0 else 0
    print(f'   {cat_name[:30]:30} {with_hold:>5}/{total_in_cat:<5} ({pct:.0f}%)')

# 6. AMC Distribution (Top 15)
print(f'\n🏢 TOP 15 AMCs BY FUND COUNT')
print('-'*50)
pipeline = [
    {'$group': {'_id': '$amc', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}},
    {'$limit': 15}
]
amcs = list(db.funds.aggregate(pipeline))
for amc in amcs:
    amc_name = str(amc['_id'])[:35] if amc['_id'] else 'Unknown'
    cnt = amc['count']
    print(f'   {amc_name:35} {cnt:>6}')

# 7. User-related collections
print(f'\n👤 USER & AUTH DATA')
print('-'*50)
user_collections = ['users', 'accounts', 'sessions', 'verification_tokens', 'authenticators']
for coll_name in user_collections:
    if coll_name in collections:
        count = db[coll_name].count_documents({})
        print(f'   {coll_name:30} {count:>8} records')
    else:
        print(f'   {coll_name:30}     N/A (not created)')

# 8. Watchlist & User Features
print(f'\n⭐ WATCHLIST & USER FEATURES')
print('-'*50)
feature_collections = ['watchlists', 'watchlist', 'portfolios', 'portfolio', 'alerts', 'reminders', 'notifications']
for coll_name in feature_collections:
    if coll_name in collections:
        count = db[coll_name].count_documents({})
        print(f'   {coll_name:30} {count:>8} records')
    else:
        print(f'   {coll_name:30}     N/A')

# 9. NAV & Market Data
print(f'\n📈 NAV & MARKET DATA')
print('-'*50)
market_collections = ['fund_navs', 'navs', 'nav_history', 'market_indices', 'indices', 'index_data']
for coll_name in market_collections:
    if coll_name in collections:
        count = db[coll_name].count_documents({})
        stats_coll = db.command('collStats', coll_name)
        size_kb = stats_coll['size'] / 1024
        print(f'   {coll_name:30} {count:>8} records ({size_kb:.1f} KB)')
    else:
        print(f'   {coll_name:30}     N/A')

# 10. Compare & Overlap
print(f'\n🔄 COMPARE & OVERLAP DATA')
print('-'*50)
compare_collections = ['comparisons', 'compare_history', 'overlaps', 'overlap_analysis']
for coll_name in compare_collections:
    if coll_name in collections:
        count = db[coll_name].count_documents({})
        print(f'   {coll_name:30} {count:>8} records')
    else:
        print(f'   {coll_name:30}     N/A')

# 11. Capacity Estimation
print(f'\n📐 CAPACITY ESTIMATION')
print('-'*50)
avg_user_size_kb = 2  # Auth + session
avg_watchlist_kb = 1  # Per watchlist item
avg_nav_record_kb = 0.5
avg_comparison_kb = 3

remaining_kb = remaining_mb * 1024
est_users = int(remaining_kb / avg_user_size_kb)
est_watchlist_items = int(remaining_kb / avg_watchlist_kb)
est_nav_records = int(remaining_kb / avg_nav_record_kb)
est_comparisons = int(remaining_kb / avg_comparison_kb)

print(f'   With {remaining_mb:.1f} MB remaining, you can add approximately:')
print(f'   ')
print(f'   👤 Users (auth+session):     ~{est_users:,} users')
print(f'   ⭐ Watchlist items:          ~{est_watchlist_items:,} items')
print(f'   📊 NAV records:              ~{est_nav_records:,} records')
print(f'   🔄 Comparison saves:         ~{est_comparisons:,} saves')
print(f'   ')
print(f'   Realistic Mixed Usage Estimate:')
print(f'   ~{int(est_users/10):,} active users with watchlists, comparisons, and history')

# 12. Per-user storage breakdown
print(f'\n👥 PER-USER STORAGE ESTIMATE')
print('-'*50)
print(f'   Typical user footprint:')
print(f'     - User profile & auth:    ~2 KB')
print(f'     - 10 watchlist items:     ~10 KB')
print(f'     - 5 comparisons saved:    ~15 KB')
print(f'     - NAV history (30 days):  ~5 KB')
print(f'     - Overlap analyses:       ~8 KB')
print(f'   ----------------------------------------')
print(f'     Total per active user:    ~40 KB')
print(f'   ')
est_active_users = int(remaining_kb / 40)
print(f'   Maximum active users:       ~{est_active_users:,} users')

client.close()
print(f'\n' + '='*70)
print('ANALYSIS COMPLETE')
print('='*70)
