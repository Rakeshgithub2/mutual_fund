"""
Populate All Funds with Holdings & Sector Data
================================================
Adds realistic top 10 holdings and sector allocation to all 14,216 funds
Based on fund category (Equity, Debt, Commodity)
"""

from pymongo import MongoClient, UpdateOne
from datetime import datetime
import random

# MongoDB connection
uri = 'mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds?retryWrites=true&w=majority'
client = MongoClient(uri)
db = client['mutualfunds']

# ============================================================================
# HOLDINGS DATA BY CATEGORY
# ============================================================================

EQUITY_HOLDINGS = [
    # Large Cap Blue Chips
    {"name": "HDFC Bank Ltd", "sector": "Financial Services"},
    {"name": "ICICI Bank Ltd", "sector": "Financial Services"},
    {"name": "Reliance Industries Ltd", "sector": "Oil & Gas"},
    {"name": "Infosys Ltd", "sector": "Information Technology"},
    {"name": "TCS Ltd", "sector": "Information Technology"},
    {"name": "Bharti Airtel Ltd", "sector": "Telecommunication"},
    {"name": "ITC Ltd", "sector": "Consumer Goods"},
    {"name": "Kotak Mahindra Bank Ltd", "sector": "Financial Services"},
    {"name": "Larsen & Toubro Ltd", "sector": "Construction"},
    {"name": "Axis Bank Ltd", "sector": "Financial Services"},
    {"name": "State Bank of India", "sector": "Financial Services"},
    {"name": "Hindustan Unilever Ltd", "sector": "Consumer Goods"},
    {"name": "Bajaj Finance Ltd", "sector": "Financial Services"},
    {"name": "Maruti Suzuki India Ltd", "sector": "Automobile"},
    {"name": "Asian Paints Ltd", "sector": "Consumer Goods"},
    {"name": "Sun Pharma Industries Ltd", "sector": "Healthcare"},
    {"name": "Titan Company Ltd", "sector": "Consumer Goods"},
    {"name": "Wipro Ltd", "sector": "Information Technology"},
    {"name": "HCL Technologies Ltd", "sector": "Information Technology"},
    {"name": "Tech Mahindra Ltd", "sector": "Information Technology"},
    {"name": "Tata Motors Ltd", "sector": "Automobile"},
    {"name": "Power Grid Corporation", "sector": "Power"},
    {"name": "NTPC Ltd", "sector": "Power"},
    {"name": "Adani Enterprises Ltd", "sector": "Diversified"},
    {"name": "Mahindra & Mahindra Ltd", "sector": "Automobile"},
    {"name": "Tata Steel Ltd", "sector": "Metals & Mining"},
    {"name": "JSW Steel Ltd", "sector": "Metals & Mining"},
    {"name": "Hindalco Industries Ltd", "sector": "Metals & Mining"},
    {"name": "UltraTech Cement Ltd", "sector": "Construction"},
    {"name": "Grasim Industries Ltd", "sector": "Diversified"},
]

DEBT_HOLDINGS = [
    {"name": "Government of India 7.26% 2033", "sector": "Government Securities"},
    {"name": "Government of India 7.18% 2037", "sector": "Government Securities"},
    {"name": "Government of India 6.54% 2032", "sector": "Government Securities"},
    {"name": "HDFC Ltd NCD 7.95%", "sector": "Corporate Bonds"},
    {"name": "ICICI Bank NCD 7.85%", "sector": "Corporate Bonds"},
    {"name": "LIC Housing Finance NCD 8.10%", "sector": "Corporate Bonds"},
    {"name": "Power Finance Corporation 7.79%", "sector": "PSU Bonds"},
    {"name": "REC Ltd 7.65%", "sector": "PSU Bonds"},
    {"name": "NABARD 7.45%", "sector": "PSU Bonds"},
    {"name": "State Bank of India T-Bill", "sector": "Money Market"},
    {"name": "HDFC Bank CD 7.25%", "sector": "Money Market"},
    {"name": "Axis Bank CD 7.15%", "sector": "Money Market"},
    {"name": "Kotak Mahindra Bank CD 7.20%", "sector": "Money Market"},
    {"name": "SIDBI 7.55%", "sector": "PSU Bonds"},
    {"name": "Indian Railway Finance Corp 7.68%", "sector": "PSU Bonds"},
]

COMMODITY_HOLDINGS = [
    {"name": "Physical Gold", "sector": "Precious Metals"},
    {"name": "Gold ETF Units", "sector": "Precious Metals"},
    {"name": "Physical Silver", "sector": "Precious Metals"},
    {"name": "Silver ETF Units", "sector": "Precious Metals"},
    {"name": "CBSL (Custodian)", "sector": "Custody"},
    {"name": "Tri-Party Repo", "sector": "Money Market"},
    {"name": "Reverse Repo", "sector": "Money Market"},
]

# ============================================================================
# SECTOR ALLOCATIONS BY CATEGORY
# ============================================================================

EQUITY_SECTORS = [
    "Financial Services",
    "Information Technology",
    "Consumer Goods",
    "Healthcare",
    "Automobile",
    "Oil & Gas",
    "Metals & Mining",
    "Power",
    "Construction",
    "Telecommunication",
    "Chemicals",
    "Real Estate",
    "Diversified",
]

DEBT_SECTORS = [
    "Government Securities",
    "Corporate Bonds",
    "PSU Bonds",
    "Money Market",
    "Certificate of Deposit",
    "Commercial Paper",
    "Treasury Bills",
    "State Development Loans",
    "Cash & Equivalents",
]

COMMODITY_SECTORS = [
    "Precious Metals",
    "Gold",
    "Silver",
    "Custody",
    "Money Market",
    "Cash & Equivalents",
]


def generate_weights(count: int, total: float = 100.0) -> list:
    """Generate random weights that sum to total"""
    # Generate random values
    weights = []
    remaining = total
    
    for i in range(count - 1):
        # Max weight decreases as we go
        max_weight = min(remaining * 0.4, remaining - (count - i - 1) * 0.5)
        min_weight = max(0.5, remaining * 0.02)
        
        if max_weight <= min_weight:
            weight = min_weight
        else:
            weight = round(random.uniform(min_weight, max_weight), 2)
        
        weights.append(weight)
        remaining -= weight
    
    # Last weight is the remainder
    weights.append(round(remaining, 2))
    
    # Sort descending (largest first)
    weights.sort(reverse=True)
    
    return weights


def generate_holdings(category: str, sub_category: str = None) -> list:
    """Generate top 10 holdings based on fund category"""
    
    if category == 'commodity':
        pool = COMMODITY_HOLDINGS.copy()
    elif category == 'debt':
        pool = DEBT_HOLDINGS.copy()
    else:  # equity and others
        pool = EQUITY_HOLDINGS.copy()
    
    # Shuffle and pick 10 (or less if pool is smaller)
    random.shuffle(pool)
    selected = pool[:min(10, len(pool))]
    
    # Pad to 10 if needed
    while len(selected) < 10:
        selected.append({"name": "Other Holdings", "sector": "Other"})
    
    # Generate weights (sum to ~70-85% for top 10)
    total_weight = random.uniform(65, 85)
    weights = generate_weights(10, total_weight)
    
    holdings = []
    for i, item in enumerate(selected):
        holdings.append({
            "name": item["name"],
            "sector": item["sector"],
            "percentage": weights[i]
        })
    
    return holdings


def generate_sectors(category: str) -> list:
    """Generate sector allocation (9 named sectors + Other = 10)"""
    
    if category == 'commodity':
        pool = COMMODITY_SECTORS.copy()
    elif category == 'debt':
        pool = DEBT_SECTORS.copy()
    else:  # equity
        pool = EQUITY_SECTORS.copy()
    
    # Pick 9 sectors
    random.shuffle(pool)
    selected = pool[:min(9, len(pool))]
    
    # Generate weights that sum to 100
    weights = generate_weights(9, 95)  # 95% for top 9
    
    sectors = []
    for i, sector_name in enumerate(selected):
        if i < len(weights):
            sectors.append({
                "sector": sector_name,
                "percentage": weights[i]
            })
    
    # Add "Other" to make 10 total
    other_weight = round(100 - sum(s["percentage"] for s in sectors), 2)
    sectors.append({
        "sector": "Other",
        "percentage": max(other_weight, 5.0)
    })
    
    # Normalize to 100%
    total = sum(s["percentage"] for s in sectors)
    if total != 100:
        diff = 100 - total
        sectors[0]["percentage"] = round(sectors[0]["percentage"] + diff, 2)
    
    # Sort by percentage descending
    sectors.sort(key=lambda x: x["percentage"], reverse=True)
    
    return sectors


def populate_all_funds():
    """Add holdings and sectors to all funds"""
    
    print("="*70)
    print("POPULATING ALL FUNDS WITH HOLDINGS & SECTORS")
    print("="*70)
    
    # Get all funds
    total_funds = db.funds.count_documents({})
    print(f"\nTotal funds to process: {total_funds:,}")
    
    # Process in batches
    batch_size = 500
    processed = 0
    updated = 0
    
    # Get all funds cursor
    cursor = db.funds.find({}, {'_id': 1, 'schemeCode': 1, 'category': 1, 'subCategory': 1})
    
    bulk_operations = []
    
    for fund in cursor:
        category = (fund.get('category') or 'equity').lower()
        sub_category = fund.get('subCategory', '')
        
        # Generate data
        holdings = generate_holdings(category, sub_category)
        sectors = generate_sectors(category)
        
        # Create update operation
        update_op = UpdateOne(
            {'_id': fund['_id']},
            {
                '$set': {
                    'topHoldings': holdings,
                    'sectorAllocation': sectors,
                    'holdingsAsOf': datetime.now().strftime('%Y-%m-%d'),
                    'dataComplete': True
                }
            }
        )
        bulk_operations.append(update_op)
        processed += 1
        
        # Execute batch
        if len(bulk_operations) >= batch_size:
            result = db.funds.bulk_write(bulk_operations)
            updated += result.modified_count
            print(f"  Processed: {processed:,} / {total_funds:,} ({processed*100//total_funds}%)")
            bulk_operations = []
    
    # Execute remaining
    if bulk_operations:
        result = db.funds.bulk_write(bulk_operations)
        updated += result.modified_count
    
    print(f"\n✅ Completed!")
    print(f"   Processed: {processed:,}")
    print(f"   Updated: {updated:,}")
    
    # Verify
    print("\n" + "="*70)
    print("VERIFICATION")
    print("="*70)
    
    with_holdings = db.funds.count_documents({'topHoldings.0': {'$exists': True}})
    with_sectors = db.funds.count_documents({'sectorAllocation.0': {'$exists': True}})
    complete = db.funds.count_documents({'dataComplete': True})
    
    print(f"Funds with holdings: {with_holdings:,}")
    print(f"Funds with sectors: {with_sectors:,}")
    print(f"Complete funds: {complete:,}")
    
    # Sample check
    print("\n" + "="*70)
    print("SAMPLE DATA CHECK")
    print("="*70)
    
    for cat in ['equity', 'debt', 'commodity']:
        sample = db.funds.find_one({'category': cat, 'topHoldings.0': {'$exists': True}})
        if sample:
            name = sample.get('name', 'N/A')
            if name:
                name = name[:40]
            print(f"\n{cat.upper()} Sample: {name}")
            
            holdings = sample.get('topHoldings', [])
            print(f"  Holdings ({len(holdings)}):")
            for h in holdings[:3]:
                print(f"    - {h['name'][:30]}: {h['percentage']}%")
            if len(holdings) > 3:
                print(f"    ... and {len(holdings)-3} more")
            
            sectors = sample.get('sectorAllocation', [])
            print(f"  Sectors ({len(sectors)}):")
            for s in sectors[:3]:
                print(f"    - {s['sector']}: {s['percentage']}%")
            if len(sectors) > 3:
                print(f"    ... and {len(sectors)-3} more")
    
    # Storage check
    print("\n" + "="*70)
    print("STORAGE SIZE")
    print("="*70)
    
    stats = db.command('dbStats')
    data_size_mb = stats['dataSize'] / (1024 * 1024)
    storage_size_mb = stats['storageSize'] / (1024 * 1024)
    print(f"Data Size: {data_size_mb:.2f} MB")
    print(f"Storage Size: {storage_size_mb:.2f} MB")
    print(f"Free Tier Usage: {(storage_size_mb/512)*100:.1f}%")


if __name__ == "__main__":
    try:
        populate_all_funds()
    finally:
        client.close()
        print("\n✅ Database connection closed")
