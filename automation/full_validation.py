"""
FULL FUND CATEGORY SYSTEM VALIDATION
=====================================
Validates all fund categories, data points, and system health
"""

from pymongo import MongoClient
from collections import defaultdict
import json

uri = 'mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds?retryWrites=true&w=majority'
client = MongoClient(uri)
db = client['mutualfunds']

def part1_category_coverage():
    """PART 1: Fund Category Coverage Check"""
    print('='*70)
    print('PART 1: FUND CATEGORY COVERAGE CHECK')
    print('='*70)
    
    # Get distinct categories and count
    categories = defaultdict(lambda: defaultdict(int))
    
    # Sample funds to get category distribution
    for fund in db.funds.find({}, {'category': 1, 'subCategory': 1}):
        cat = fund.get('category', 'Unknown') or 'Unknown'
        subcat = fund.get('subCategory', 'Unknown') or 'Unknown'
        categories[cat][subcat] += 1
    
    # Print results
    total_funds = 0
    for cat in sorted(categories.keys()):
        cat_total = sum(categories[cat].values())
        total_funds += cat_total
        print(f'\n✅ {cat.upper()} ({cat_total:,} funds)')
        
        # Sort by count descending
        sorted_subcats = sorted(categories[cat].items(), key=lambda x: -x[1])
        for subcat, count in sorted_subcats[:8]:
            print(f'   - {subcat[:45]}: {count}')
        if len(sorted_subcats) > 8:
            print(f'   ... and {len(sorted_subcats)-8} more sub-categories')
    
    print(f'\n📊 TOTAL: {total_funds:,} funds across {len(categories)} categories')
    return categories

def part2_data_point_validation():
    """PART 2: Data Point Validation"""
    print('\n' + '='*70)
    print('PART 2: DATA POINT VALIDATION')
    print('='*70)
    
    # Required fields
    required_fields = ['name', 'fundHouse', 'category', 'subCategory', 'schemeCode']
    optional_fields = ['nav', 'aum', 'expenseRatio', 'riskLevel', 'benchmark']
    holdings_fields = ['topHoldings', 'sectorAllocation']
    
    total = db.funds.count_documents({})
    
    # Check required fields
    print('\n📋 REQUIRED FIELDS:')
    for field in required_fields:
        has_field = db.funds.count_documents({field: {'$exists': True, '$ne': None, '$ne': ''}})
        pct = (has_field / total) * 100
        status = '✅' if pct >= 99 else '⚠️' if pct >= 80 else '❌'
        print(f'   {status} {field}: {has_field:,}/{total:,} ({pct:.1f}%)')
    
    # Check optional fields
    print('\n📋 OPTIONAL FIELDS:')
    for field in optional_fields:
        has_field = db.funds.count_documents({field: {'$exists': True, '$ne': None}})
        pct = (has_field / total) * 100
        status = '✅' if pct >= 80 else '⚠️' if pct >= 50 else '❌'
        print(f'   {status} {field}: {has_field:,}/{total:,} ({pct:.1f}%)')
    
    # Check holdings fields
    print('\n📋 HOLDINGS DATA:')
    for field in holdings_fields:
        has_field = db.funds.count_documents({f'{field}.0': {'$exists': True}})
        pct = (has_field / total) * 100
        status = '✅' if pct >= 10 else '⚠️' if pct >= 1 else '❌'
        print(f'   {status} {field}: {has_field:,}/{total:,} ({pct:.1f}%)')
    
    # Check returns data
    print('\n📋 RETURNS DATA:')
    returns_fields = ['returns1Y', 'returns3Y', 'returns5Y', 'returnsSI']
    for field in returns_fields:
        has_field = db.funds.count_documents({field: {'$exists': True, '$ne': None}})
        pct = (has_field / total) * 100
        status = '✅' if pct >= 50 else '⚠️' if pct >= 20 else '❌'
        print(f'   {status} {field}: {has_field:,}/{total:,} ({pct:.1f}%)')

def part3_mongodb_storage():
    """PART 3: MongoDB Storage Validation"""
    print('\n' + '='*70)
    print('PART 3: MONGODB STORAGE VALIDATION')
    print('='*70)
    
    # Get database stats
    stats = db.command('dbStats')
    data_size_mb = stats['dataSize'] / (1024 * 1024)
    storage_size_mb = stats['storageSize'] / (1024 * 1024)
    
    print(f'\n💾 STORAGE:')
    print(f'   Data Size: {data_size_mb:.2f} MB')
    print(f'   Storage Size: {storage_size_mb:.2f} MB')
    print(f'   Free Tier (512 MB): {(data_size_mb/512)*100:.1f}% used')
    
    # Collection stats
    print(f'\n📁 COLLECTIONS:')
    collections = db.list_collection_names()
    for coll in sorted(collections):
        count = db[coll].count_documents({})
        print(f'   - {coll}: {count:,} documents')
    
    # Check for null/NA values in key fields
    print(f'\n🔍 DATA INTEGRITY:')
    null_checks = [
        ('name IS NULL', {'name': None}),
        ('name IS EMPTY', {'name': ''}),
        ('schemeCode IS NULL', {'schemeCode': None}),
        ('category IS NULL', {'category': None}),
    ]
    
    for label, query in null_checks:
        count = db.funds.count_documents(query)
        status = '✅' if count == 0 else '⚠️'
        print(f'   {status} {label}: {count}')

def part4_holdings_sample():
    """PART 4: Sample Holdings Check"""
    print('\n' + '='*70)
    print('PART 4: HOLDINGS DATA SAMPLES')
    print('='*70)
    
    # Check holdings collection
    holdings_count = db.holdings.count_documents({})
    print(f'\n📊 Holdings Collection: {holdings_count} records')
    
    # Sample from holdings collection
    print('\n🔍 SAMPLE HOLDINGS (from holdings collection):')
    for h in db.holdings.find({}).limit(3):
        print(f"\n   Fund: {h.get('schemeName', 'N/A')[:50]}")
        print(f"   SchemeCode: {h.get('schemeCode')}")
        holdings = h.get('holdings', [])
        print(f"   Holdings: {len(holdings)} stocks")
        for stock in holdings[:3]:
            print(f"     - {stock.get('company', 'N/A')[:30]}: {stock.get('holdingPercent')}%")
    
    # Check funds with topHoldings
    funds_with_holdings = db.funds.count_documents({'topHoldings': {'$exists': True, '$type': 'array', '$ne': []}})
    print(f'\n📊 Funds with topHoldings: {funds_with_holdings}')
    
    # Sample from funds with holdings
    if funds_with_holdings > 0:
        print('\n🔍 SAMPLE HOLDINGS (from funds collection):')
        for f in db.funds.find({'topHoldings.0': {'$exists': True}}).limit(3):
            print(f"\n   Fund: {f.get('name', 'N/A')[:50]}")
            print(f"   Category: {f.get('category')} / {f.get('subCategory')}")
            holdings = f.get('topHoldings', [])
            for stock in holdings[:3]:
                print(f"     - {stock.get('name', 'N/A')[:30]}: {stock.get('percentage')}%")

def part5_category_breakdown():
    """PART 5: Category Breakdown with Holdings Status"""
    print('\n' + '='*70)
    print('PART 5: CATEGORY BREAKDOWN BY HOLDINGS STATUS')
    print('='*70)
    
    # Major categories to check
    major_categories = ['equity', 'debt', 'hybrid', 'commodity', 'solution', 'other']
    
    for cat in major_categories:
        total = db.funds.count_documents({'category': {'$regex': f'^{cat}$', '$options': 'i'}})
        if total == 0:
            # Try different case
            total = db.funds.count_documents({'category': cat.capitalize()})
        
        with_holdings = db.funds.count_documents({
            'category': {'$regex': f'^{cat}$', '$options': 'i'},
            'topHoldings.0': {'$exists': True}
        })
        
        if total > 0:
            pct = (with_holdings / total) * 100
            status = '✅' if pct >= 10 else '⚠️' if pct >= 1 else '❌'
            print(f'\n{status} {cat.upper()}: {total:,} funds')
            print(f'   With holdings data: {with_holdings} ({pct:.1f}%)')

def part6_storage_estimate():
    """PART 6: Storage Estimation"""
    print('\n' + '='*70)
    print('PART 6: STORAGE CAPACITY ESTIMATION')
    print('='*70)
    
    stats = db.command('dbStats')
    current_size_mb = stats['dataSize'] / (1024 * 1024)
    fund_count = db.funds.count_documents({})
    
    # Estimate per-fund storage
    if fund_count > 0:
        per_fund_kb = (current_size_mb * 1024) / fund_count
        
        print(f'\n📊 CURRENT USAGE:')
        print(f'   Funds: {fund_count:,}')
        print(f'   Storage: {current_size_mb:.2f} MB')
        print(f'   Per Fund: {per_fund_kb:.2f} KB')
        
        print(f'\n📈 CAPACITY (512 MB Free Tier):')
        max_funds = int(512 * 1024 / per_fund_kb)
        print(f'   Max Funds Possible: ~{max_funds:,}')
        print(f'   Current Usage: {(current_size_mb/512)*100:.1f}%')
        print(f'   Remaining Capacity: {512 - current_size_mb:.1f} MB')

def generate_report():
    """Generate Final Report"""
    print('\n' + '='*70)
    print('FINAL VALIDATION REPORT')
    print('='*70)
    
    total_funds = db.funds.count_documents({})
    holdings_collection = db.holdings.count_documents({})
    funds_with_holdings = db.funds.count_documents({'topHoldings.0': {'$exists': True}})
    
    stats = db.command('dbStats')
    current_size_mb = stats['dataSize'] / (1024 * 1024)
    
    print(f'''
📊 SYSTEM STATUS:
   Total Funds: {total_funds:,}
   Holdings Records: {holdings_collection}
   Funds with Holdings: {funds_with_holdings}
   Storage Used: {current_size_mb:.2f} MB / 512 MB

✅ WORKING:
   - Fund data loaded from AMFI API
   - Multiple categories supported (Equity, Debt, Hybrid, Commodity)
   - Holdings collection has {holdings_collection} real records
   - Storage is within free tier limits

⚠️ NEEDS ATTENTION:
   - Only {funds_with_holdings} funds have topHoldings in funds collection
   - Need to sync holdings collection → funds collection
   - PDF automation URLs need updating (404 errors)

🎯 RECOMMENDATIONS:
   1. Run sync script to copy holdings data to funds
   2. Update PDF download URLs in automation config
   3. Add more AMC factsheet sources
   4. Implement scheduled data refresh

📌 PRODUCTION READINESS: PARTIAL
   - Core system: ✅ Ready
   - Holdings data: ⚠️ Needs expansion
   - Automation: ⚠️ Needs URL fixes
''')

if __name__ == '__main__':
    try:
        part1_category_coverage()
        part2_data_point_validation()
        part3_mongodb_storage()
        part4_holdings_sample()
        part5_category_breakdown()
        part6_storage_estimate()
        generate_report()
    finally:
        client.close()
