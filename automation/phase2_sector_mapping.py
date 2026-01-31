"""
PHASE 2: SECTOR MAPPING
=======================
Derive sector allocation from holdings company names
"""
from pymongo import MongoClient
from collections import defaultdict
import re

client = MongoClient('mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds')
db = client['mutualfunds']

print('='*70)
print('PHASE 2: SECTOR MAPPING')
print('='*70)

# Comprehensive company-to-sector mapping
SECTOR_KEYWORDS = {
    'Financial Services': [
        'hdfc bank', 'icici bank', 'sbi', 'state bank', 'axis bank', 
        'kotak bank', 'kotak mahindra bank', 'indusind bank', 'yes bank',
        'federal bank', 'idfc first', 'rbl bank', 'bandhan bank',
        'bajaj finance', 'bajaj finserv', 'shriram finance', 'mahindra finance',
        'muthoot', 'manappuram', 'cholamandalam', 'l&t finance',
        'hdfc life', 'sbi life', 'icici prudential life', 'max life',
        'icici lombard', 'hdfc ergo', 'bajaj allianz',
        'hdfc amc', 'nippon amc', 'sbi amc',
        'power finance', 'pfc', 'rec limited', 'rec ltd', 'rural electrification',
        'nabard', 'national bank for agriculture', 'sidbi', 'exim bank',
        'lic housing', 'can fin homes', 'pnb housing',
        'bank of baroda', 'punjab national', 'canara bank', 'union bank',
        'indian bank', 'bank of india', 'central bank', 'uco bank',
        'bse', 'nse', 'cdsl', 'nsdl', 'cams',
    ],
    
    'Information Technology': [
        'infosys', 'tcs', 'tata consultancy', 'wipro', 
        'hcl tech', 'tech mahindra', 'ltimindtree', 'lti mindtree',
        'persistent', 'coforge', 'mphasis', 'mindtree',
        'l&t technology', 'ltts', 'cyient', 'zensar',
        'tata elxsi', 'kpit', 'birlasoft', 'happiest minds',
        'oracle', 'sap', 'microsoft', 'google', 'amazon',
    ],
    
    'Oil & Gas': [
        'reliance industries', 'ril', 'ongc', 'oil & natural gas',
        'indian oil', 'ioc', 'bpcl', 'bharat petroleum',
        'hpcl', 'hindustan petroleum', 'gail', 'petronet lng',
        'oil india', 'chennai petroleum', 'mrpl',
        'adani total gas', 'indraprastha gas', 'igl', 'mahanagar gas',
        'gujarat gas', 'castrol',
    ],
    
    'Healthcare': [
        'sun pharma', 'dr reddy', 'divi', 'cipla', 'lupin',
        'aurobindo', 'torrent pharma', 'zydus', 'cadila',
        'biocon', 'alkem', 'ipca', 'glenmark', 'natco',
        'abbott', 'pfizer', 'sanofi', 'glaxo', 'gsk pharma',
        'apollo hospital', 'fortis', 'max healthcare', 'narayana',
        'lal path', 'dr lal', 'metropolis', 'thyrocare',
        'eris lifesciences', 'ajanta pharma', 'granules',
    ],
    
    'Automobile': [
        'maruti', 'tata motors', 'mahindra & mahindra', 'm&m',
        'bajaj auto', 'hero motocorp', 'eicher motors', 'royal enfield',
        'tvs motor', 'ashok leyland', 'force motors',
        'bosch', 'motherson', 'mrf', 'apollo tyres', 'ceat',
        'balkrishna', 'exide', 'amara raja', 'bharat forge',
        'sona blw', 'uno minda', 'tube investments',
        'escorts', 'atul auto', 'sml isuzu',
    ],
    
    'Consumer Goods': [
        'hindustan unilever', 'hul', 'itc', 'nestle', 'britannia',
        'marico', 'dabur', 'godrej consumer', 'colgate', 'p&g',
        'tata consumer', 'varun beverages', 'radico khaitan',
        'united spirits', 'united breweries',
        'emami', 'jyothy labs', 'bajaj consumer',
        'bikaji', 'patanjali',
    ],
    
    'Metals & Mining': [
        'tata steel', 'jsw steel', 'hindalco', 'vedanta',
        'coal india', 'nmdc', 'hindustan zinc',
        'jindal steel', 'sail', 'steel authority',
        'hindalco', 'nalco', 'moil',
        'apl apollo', 'jindal stainless',
    ],
    
    'Power': [
        'ntpc', 'power grid', 'powergrid', 'tata power', 
        'adani power', 'adani green', 'adani energy',
        'jsw energy', 'nhpc', 'sjvn', 'torrent power',
        'cesc', 'energy exchange', 'iex',
    ],
    
    'Telecom': [
        'bharti airtel', 'airtel', 'vodafone idea', 'vi',
        'reliance jio', 'jio', 'indus towers', 'tata comm',
        'route mobile', 'tanla', 'sterlite tech',
    ],
    
    'Infrastructure': [
        'larsen & toubro', 'l&t', 'ultratech', 'acc', 'ambuja',
        'shree cement', 'dalmia bharat', 'ramco',
        'dlf', 'godrej properties', 'oberoi realty', 'prestige',
        'brigade', 'sobha', 'phoenix mills',
        'irb infra', 'kec international', 'kalpataru',
        'pnc infratech', 'hg infra', 'dilip buildcon',
        'adani ports', 'concor', 'gateway distriparks',
    ],
    
    'Capital Goods': [
        'siemens', 'abb', 'cummins', 'thermax',
        'bhel', 'bharat electronics', 'bel', 'hal',
        'honeywell', 'grindwell norton', 'carborundum',
        'cg power', 'suzlon', 'inox wind',
        'va tech wabag', 'triveni turbine',
    ],
    
    'Chemicals': [
        'pidilite', 'asian paints', 'berger paints', 'kansai nerolac',
        'srf', 'aarti industries', 'deepak nitrite',
        'tata chemicals', 'coromandel', 'chambal fertilizers',
        'atul', 'vinati organics', 'clean science',
        'pi industries', 'upl', 'bayer cropscience',
        'navin fluorine', 'gujarat fluorochemicals',
    ],
    
    'Retail': [
        'avenue supermarts', 'dmart', 'trent', 'titan',
        'reliance retail', 'aditya birla fashion', 'v-mart',
        'shoppers stop', 'metro brands', 'campus activewear',
    ],
    
    'Real Estate': [
        'dlf', 'godrej properties', 'oberoi realty', 'prestige',
        'brigade', 'sobha', 'mahindra lifespace',
        'lodha', 'sunteck', 'kolte patil',
    ],
}

def get_sector(company_name):
    """Map company name to sector using keyword matching"""
    if not company_name or not isinstance(company_name, str):
        return 'Others'
    
    company_lower = company_name.lower()
    
    for sector, keywords in SECTOR_KEYWORDS.items():
        for keyword in keywords:
            if keyword in company_lower:
                return sector
    
    return 'Others'

# Stats
stats = {
    'funds_processed': 0,
    'funds_with_sectors': 0,
    'sectors_derived': defaultdict(int),
}

print('\n📊 Before Sector Mapping:')
with_sectors = db.funds.count_documents({
    'sector_allocation': {
        '$exists': True, 
        '$elemMatch': {'sector': {'$nin': ['Others', 'others', '', None]}}
    }
})
total_funds = db.funds.count_documents({})
print(f'   With Real Sectors: {with_sectors:,} ({with_sectors/total_funds*100:.1f}%)')

print('\n🏭 Deriving sectors from holdings...\n')

# Process all funds with clean holdings
funds = db.funds.find({'holdings': {'$exists': True, '$not': {'$size': 0}}})

for fund in funds:
    stats['funds_processed'] += 1
    holdings = fund.get('holdings', [])
    
    # Aggregate by sector
    sector_totals = defaultdict(float)
    
    for h in holdings:
        if isinstance(h, dict):
            company = h.get('company', h.get('name', h.get('stock', '')))
            pct = h.get('percentage', h.get('weight', h.get('allocation', 0)))
            
            if isinstance(pct, (int, float)) and pct > 0:
                sector = get_sector(company)
                sector_totals[sector] += pct
                
                # Also update holding with sector
                h['sector'] = sector
    
    if sector_totals:
        # Create sector_allocation array
        sector_allocation = [
            {'sector': sector, 'percentage': round(pct, 2)}
            for sector, pct in sorted(sector_totals.items(), key=lambda x: -x[1])
            if pct > 0
        ]
        
        # Check if we have real sectors (not just Others)
        has_real = any(s['sector'] != 'Others' for s in sector_allocation)
        if has_real:
            stats['funds_with_sectors'] += 1
            for s in sector_allocation:
                if s['sector'] != 'Others':
                    stats['sectors_derived'][s['sector']] += 1
        
        # Update fund with holdings (with sector) and sector_allocation
        db.funds.update_one(
            {'_id': fund['_id']},
            {'$set': {
                'holdings': holdings,
                'sector_allocation': sector_allocation
            }}
        )
        
        if stats['funds_with_sectors'] <= 10 and has_real:
            fund_name = fund.get('name', 'N/A')[:40]
            top_sectors = [f"{s['sector']}: {s['percentage']}%" for s in sector_allocation[:3] if s['sector'] != 'Others']
            print(f'   ✓ {fund_name}')
            print(f'     {", ".join(top_sectors)}')

print(f'\n' + '='*70)
print('PHASE 2 RESULTS')
print('='*70)

print(f'\n📊 Sector Mapping Statistics:')
print(f'   Funds Processed:      {stats["funds_processed"]:,}')
print(f'   Funds With Sectors:   {stats["funds_with_sectors"]:,}')

print(f'\n📊 Sector Distribution:')
for sector, count in sorted(stats['sectors_derived'].items(), key=lambda x: -x[1]):
    print(f'   {sector:25} {count:>5} funds')

# After stats
print(f'\n📊 After Sector Mapping:')
with_sectors_after = db.funds.count_documents({
    'sector_allocation': {
        '$exists': True, 
        '$elemMatch': {'sector': {'$nin': ['Others', 'others', '', None]}}
    }
})
print(f'   With Real Sectors: {with_sectors_after:,} ({with_sectors_after/total_funds*100:.1f}%)')
print(f'   Change: {with_sectors} → {with_sectors_after} ({with_sectors_after - with_sectors:+,})')

# Sample
print('\n📋 Sample Fund with Sectors:')
sample = db.funds.find_one({
    'sector_allocation': {
        '$exists': True,
        '$elemMatch': {'sector': 'Financial Services', 'percentage': {'$gte': 5}}
    }
})

if sample:
    print(f'   Fund: {sample.get("name", "N/A")}')
    print(f'   AMC: {sample.get("amc", {}).get("name", "N/A")}')
    print(f'   Sectors:')
    for s in sample.get('sector_allocation', [])[:5]:
        print(f'     → {s["sector"]}: {s["percentage"]}%')

client.close()
print('\n' + '='*70)
print('✅ PHASE 2 COMPLETE')
print('='*70)
