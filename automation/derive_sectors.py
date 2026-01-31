"""
Analyze holdings and derive sector allocation
"""
from pymongo import MongoClient
from collections import defaultdict

client = MongoClient('mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds')
db = client['mutualfunds']

print('='*70)
print('ANALYZING HOLDINGS STRUCTURE')
print('='*70)

# Check actual holdings structure from different AMCs
amcs_to_check = ['HDFC Mutual Fund', 'SBI Mutual Fund', 'ICICI Prudential Mutual Fund', 'Kotak Mahindra Mutual Fund']

all_keys = set()
sample_holdings = []

for amc in amcs_to_check:
    fund = db.funds.find_one({
        'amc.name': amc,
        'holdings': {'$exists': True, '$not': {'$size': 0}}
    })
    
    if fund:
        print(f'\n🏢 {amc}')
        print(f'   Fund: {fund.get("name", "N/A")}')
        holdings = fund.get('holdings', [])
        print(f'   Holdings count: {len(holdings)}')
        
        for h in holdings[:5]:
            if isinstance(h, dict):
                all_keys.update(h.keys())
                print(f'   → {h}')
                sample_holdings.append(h)

print(f'\n\nAll keys found in holdings: {all_keys}')

# Check if sector exists
has_sector = any('sector' in h for h in sample_holdings if isinstance(h, dict))
print(f'Holdings have sector field: {has_sector}')

# If sector exists, derive sector allocation
if has_sector or 'sector' in all_keys:
    print('\n' + '='*70)
    print('DERIVING SECTOR ALLOCATION FROM HOLDINGS')
    print('='*70)
    
    updated = 0
    funds_with_holdings = db.funds.find({
        'holdings': {'$exists': True, '$not': {'$size': 0}}
    })
    
    for fund in funds_with_holdings:
        holdings = fund.get('holdings', [])
        
        # Aggregate by sector
        sector_totals = defaultdict(float)
        for h in holdings:
            if isinstance(h, dict):
                sector = h.get('sector', 'Others')
                pct = h.get('percentage', h.get('weight', h.get('allocation', 0)))
                if isinstance(pct, (int, float)):
                    sector_totals[sector] += pct
        
        if sector_totals:
            # Create sector_allocation array
            sector_allocation = [
                {'sector': sector, 'percentage': round(pct, 2)}
                for sector, pct in sorted(sector_totals.items(), key=lambda x: -x[1])
            ]
            
            # Update fund
            db.funds.update_one(
                {'_id': fund['_id']},
                {'$set': {'sector_allocation': sector_allocation}}
            )
            updated += 1
            
            if updated <= 5:
                print(f'\n✅ {fund.get("name", "N/A")[:50]}')
                print(f'   Sectors: {sector_allocation[:5]}')
    
    print(f'\n\nUpdated {updated} funds with sector allocation')

else:
    # No sector in holdings - need to map companies to sectors
    print('\n' + '='*70)
    print('NO SECTOR FIELD - MAPPING COMPANIES TO SECTORS')
    print('='*70)
    
    # Define sector mapping for common Indian stocks
    SECTOR_MAPPING = {
        # Financial Services
        'HDFC Bank': 'Financial Services',
        'ICICI Bank': 'Financial Services',
        'State Bank of India': 'Financial Services',
        'SBI': 'Financial Services',
        'Axis Bank': 'Financial Services',
        'Kotak Mahindra Bank': 'Financial Services',
        'Bajaj Finance': 'Financial Services',
        'Bajaj Finserv': 'Financial Services',
        'Power Finance Corporation': 'Financial Services',
        'REC': 'Financial Services',
        'HDFC Life': 'Financial Services',
        'SBI Life': 'Financial Services',
        'ICICI Lombard': 'Financial Services',
        'HDFC AMC': 'Financial Services',
        
        # IT / Technology
        'Infosys': 'Information Technology',
        'TCS': 'Information Technology',
        'Tata Consultancy': 'Information Technology',
        'Wipro': 'Information Technology',
        'HCL Technologies': 'Information Technology',
        'Tech Mahindra': 'Information Technology',
        'LTIMindtree': 'Information Technology',
        'Persistent': 'Information Technology',
        'Coforge': 'Information Technology',
        
        # Consumer / FMCG
        'Hindustan Unilever': 'Consumer Goods',
        'ITC': 'Consumer Goods',
        'Nestle': 'Consumer Goods',
        'Britannia': 'Consumer Goods',
        'Marico': 'Consumer Goods',
        'Dabur': 'Consumer Goods',
        'Godrej Consumer': 'Consumer Goods',
        'Colgate': 'Consumer Goods',
        'Tata Consumer': 'Consumer Goods',
        
        # Automobile
        'Maruti': 'Automobile',
        'Tata Motors': 'Automobile',
        'Mahindra': 'Automobile',
        'M&M': 'Automobile',
        'Bajaj Auto': 'Automobile',
        'Hero MotoCorp': 'Automobile',
        'Eicher Motors': 'Automobile',
        'TVS Motor': 'Automobile',
        
        # Pharma / Healthcare
        'Sun Pharma': 'Healthcare',
        'Dr Reddy': 'Healthcare',
        'Cipla': 'Healthcare',
        'Divi': 'Healthcare',
        'Apollo': 'Healthcare',
        'Lupin': 'Healthcare',
        'Biocon': 'Healthcare',
        'Torrent Pharma': 'Healthcare',
        
        # Energy / Oil & Gas
        'Reliance': 'Energy',
        'Reliance Industries': 'Energy',
        'ONGC': 'Energy',
        'Indian Oil': 'Energy',
        'BPCL': 'Energy',
        'HPCL': 'Energy',
        'GAIL': 'Energy',
        'Adani Total Gas': 'Energy',
        'Petronet LNG': 'Energy',
        
        # Power / Utilities
        'NTPC': 'Power',
        'Power Grid': 'Power',
        'Tata Power': 'Power',
        'Adani Power': 'Power',
        'Adani Green': 'Power',
        'JSW Energy': 'Power',
        
        # Metals & Mining
        'Tata Steel': 'Metals & Mining',
        'JSW Steel': 'Metals & Mining',
        'Hindalco': 'Metals & Mining',
        'Vedanta': 'Metals & Mining',
        'Coal India': 'Metals & Mining',
        'NMDC': 'Metals & Mining',
        
        # Infrastructure / Construction
        'Larsen & Toubro': 'Infrastructure',
        'L&T': 'Infrastructure',
        'Ultratech': 'Infrastructure',
        'ACC': 'Infrastructure',
        'Ambuja': 'Infrastructure',
        'Shree Cement': 'Infrastructure',
        'DLF': 'Infrastructure',
        'Godrej Properties': 'Infrastructure',
        
        # Telecom
        'Bharti Airtel': 'Telecom',
        'Airtel': 'Telecom',
        'Vodafone Idea': 'Telecom',
        'Indus Towers': 'Telecom',
        
        # Others
        'Asian Paints': 'Consumer Durables',
        'Pidilite': 'Chemicals',
        'Adani Enterprises': 'Conglomerate',
        'Adani Ports': 'Infrastructure',
    }
    
    def get_sector(company_name):
        """Map company name to sector"""
        if not company_name or not isinstance(company_name, str):
            return 'Others'
        
        company_upper = company_name.upper()
        
        # Skip garbage data
        garbage_words = ['SINCE INCEPTION', 'YEAR', 'MONTH', 'QUARTER', 'RETURN', 'NAV', 'AUM']
        if any(word in company_upper for word in garbage_words):
            return None  # Skip this holding
        
        for key, sector in SECTOR_MAPPING.items():
            if key.upper() in company_upper:
                return sector
        
        # Default categorization based on keywords
        if any(word in company_upper for word in ['BANK', 'FINANCE', 'INSURANCE', 'CAPITAL']):
            return 'Financial Services'
        if any(word in company_upper for word in ['PHARMA', 'DRUG', 'HOSPITAL', 'HEALTH', 'MEDIC']):
            return 'Healthcare'
        if any(word in company_upper for word in ['TECH', 'SOFTWARE', 'IT ', 'INFOTECH', 'DIGITAL']):
            return 'Information Technology'
        if any(word in company_upper for word in ['OIL', 'GAS', 'PETRO', 'ENERGY']):
            return 'Energy'
        if any(word in company_upper for word in ['AUTO', 'MOTOR', 'VEHICLE']):
            return 'Automobile'
        if any(word in company_upper for word in ['CEMENT', 'STEEL', 'METAL', 'INFRA']):
            return 'Infrastructure'
        if any(word in company_upper for word in ['POWER', 'ELECTRIC']):
            return 'Power'
        if any(word in company_upper for word in ['FOOD', 'CONSUMER', 'FMCG']):
            return 'Consumer Goods'
        if any(word in company_upper for word in ['TELECOM', 'COMMUNICATION']):
            return 'Telecom'
        if any(word in company_upper for word in ['CHEMICAL', 'FERTILIZER']):
            return 'Chemicals'
        
        return 'Others'
    
    # Process all funds with holdings
    updated = 0
    cleaned = 0
    
    funds_with_holdings = list(db.funds.find({
        'holdings': {'$exists': True, '$not': {'$size': 0}}
    }))
    
    print(f'Processing {len(funds_with_holdings)} funds with holdings...\n')
    
    for fund in funds_with_holdings:
        holdings = fund.get('holdings', [])
        
        # Clean holdings (remove garbage) and aggregate by sector
        sector_totals = defaultdict(float)
        clean_holdings = []
        
        for h in holdings:
            if isinstance(h, dict):
                company = h.get('company', h.get('name', h.get('stock', '')))
                sector = get_sector(company)
                
                if sector is None:  # Garbage data
                    continue
                
                pct = h.get('percentage', h.get('weight', h.get('allocation', 0)))
                if isinstance(pct, (int, float)) and pct > 0:
                    sector_totals[sector] += pct
                    
                    # Also add sector to holding
                    h['sector'] = sector
                    clean_holdings.append(h)
        
        if sector_totals:
            # Create sector_allocation array
            sector_allocation = [
                {'sector': sector, 'percentage': round(pct, 2)}
                for sector, pct in sorted(sector_totals.items(), key=lambda x: -x[1])
            ]
            
            # Update fund with both cleaned holdings and sector allocation
            update_data = {'sector_allocation': sector_allocation}
            if len(clean_holdings) < len(holdings):
                update_data['holdings'] = clean_holdings
                cleaned += 1
            
            db.funds.update_one(
                {'_id': fund['_id']},
                {'$set': update_data}
            )
            updated += 1
            
            if updated <= 10:
                print(f'✅ {fund.get("name", "N/A")[:50]}')
                for sa in sector_allocation[:3]:
                    print(f'   → {sa["sector"]}: {sa["percentage"]}%')
    
    print(f'\n' + '='*70)
    print(f'RESULTS')
    print('='*70)
    print(f'Funds updated with sector allocation: {updated}')
    print(f'Funds with cleaned holdings: {cleaned}')

# Final verification
print('\n' + '='*70)
print('VERIFICATION')
print('='*70)

with_sectors = db.funds.count_documents({
    'sector_allocation': {'$exists': True, '$not': {'$size': 0}}
})
total = db.funds.count_documents({})
print(f'Total funds: {total}')
print(f'With sector allocation: {with_sectors} ({with_sectors/total*100:.1f}%)')

# Sample output
sample = db.funds.find_one({
    'sector_allocation': {'$exists': True, '$not': {'$size': 0}}
})
if sample:
    print(f'\nSample fund: {sample.get("name", "N/A")}')
    print(f'Sector allocation:')
    for s in sample.get('sector_allocation', [])[:5]:
        print(f'  - {s["sector"]}: {s["percentage"]}%')

client.close()
print('\n' + '='*70)
