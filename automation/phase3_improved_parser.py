"""
PHASE 3: IMPROVED PDF PARSER
============================
Better extraction logic with garbage filtering, proper table detection,
and AMC-specific handling
"""
import pdfplumber
import os
import re
from pymongo import MongoClient
from collections import defaultdict
from pathlib import Path

# MongoDB connection
client = MongoClient('mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds')
db = client['mutualfunds']

# PDF folder
PDF_FOLDER = r"c:\MF root folder\factsheet"

# Garbage patterns to skip during extraction
GARBAGE_PATTERNS = [
    r'^since\s*inception', r'^year', r'^month', r'^quarter', r'^days?$',
    r'^1\s*yr', r'^3\s*yr', r'^5\s*yr', r'^10\s*yr', r'^ytd',
    r'^return', r'^cagr', r'^annualized', r'^absolute',
    r'^nav', r'^aum', r'^expense', r'^exit\s*load',
    r'^standard\s*deviation', r'^sharpe', r'^beta', r'^alpha',
    r'^tracking\s*error', r'^information\s*ratio', r'^sortino',
    r'^benchmark', r'^crisil', r'^nifty', r'^sensex', r'^bse',
    r'^index\s*fund', r'^etf', r'^tri\s',
    r'^direct\s*plan', r'^regular\s*plan', r'^growth', r'^idcw', r'^dividend',
    r'^cr\.?$', r'^lacs?$', r'^crores?$', r'^rs\.?$', r'^₹',
    r'^\d+\.?\d*%?$', r'^%$',
    r'^type\s*of', r'^investment\s*objective', r'^fund\s*manager',
    r'^asset\s*allocation', r'^risk', r'^moderate', r'^high', r'^low',
    r'^rating', r'^maturity', r'^modified\s*duration', r'^yield',
    r'^average', r'^total', r'^net\s*assets', r'^portfolio', r'^holding',
    r'^treps', r'^cblo', r'^repo', r'^reverse\s*repo',
    r'^sovereign', r'^aaa', r'^aa\+?', r'^a\+?', r'^bbb',
    r'^g-?sec', r'^t-?bill', r'^treasury',
    r'^nil', r'^n/?a', r'^-+$', r'^\*+$', r'^#',
    r'mutual\s*fund', r'scheme', r'plan.*growth', r'plan.*idcw',
    r'^riskometer', r'^date', r'^as\s*on', r'^inception',
]
GARBAGE_REGEX = [re.compile(p, re.IGNORECASE) for p in GARBAGE_PATTERNS]

# Sector keywords for mapping
SECTOR_KEYWORDS = {
    'Financial Services': [
        'hdfc bank', 'icici bank', 'sbi', 'state bank', 'axis bank', 
        'kotak bank', 'indusind', 'yes bank', 'federal bank', 'idfc first',
        'bajaj finance', 'bajaj finserv', 'shriram', 'mahindra finance',
        'muthoot', 'manappuram', 'cholamandalam', 'l&t finance',
        'hdfc life', 'sbi life', 'icici prudential life', 'max life',
        'icici lombard', 'hdfc ergo', 'bajaj allianz',
        'power finance', 'pfc', 'rec limited', 'rec ltd', 'rural electrification',
        'nabard', 'sidbi', 'exim bank', 'lic housing', 'can fin homes',
        'bank of baroda', 'punjab national', 'canara bank', 'union bank',
    ],
    'Information Technology': [
        'infosys', 'tcs', 'tata consultancy', 'wipro', 
        'hcl tech', 'tech mahindra', 'ltimindtree', 'lti mindtree',
        'persistent', 'coforge', 'mphasis', 'mindtree',
        'l&t technology', 'ltts', 'cyient', 'zensar',
        'tata elxsi', 'kpit', 'birlasoft', 'happiest minds',
    ],
    'Oil & Gas': [
        'reliance industries', 'ril', 'ongc', 'oil & natural gas',
        'indian oil', 'ioc', 'bpcl', 'bharat petroleum',
        'hpcl', 'hindustan petroleum', 'gail', 'petronet lng',
        'oil india', 'chennai petroleum', 'mrpl',
        'adani total gas', 'indraprastha gas', 'igl', 'mahanagar gas',
    ],
    'Healthcare': [
        'sun pharma', 'dr reddy', 'divi', 'cipla', 'lupin',
        'aurobindo', 'torrent pharma', 'zydus', 'cadila',
        'biocon', 'alkem', 'ipca', 'glenmark', 'natco',
        'abbott', 'pfizer', 'sanofi', 'glaxo', 'gsk pharma',
        'apollo hospital', 'fortis', 'max healthcare',
    ],
    'Automobile': [
        'maruti', 'tata motors', 'mahindra & mahindra', 'm&m',
        'bajaj auto', 'hero motocorp', 'eicher motors',
        'tvs motor', 'ashok leyland', 'force motors',
        'bosch', 'motherson', 'mrf', 'apollo tyres', 'ceat',
    ],
    'Consumer Goods': [
        'hindustan unilever', 'hul', 'itc', 'nestle', 'britannia',
        'marico', 'dabur', 'godrej consumer', 'colgate',
        'tata consumer', 'varun beverages', 'united spirits',
    ],
    'Metals & Mining': [
        'tata steel', 'jsw steel', 'hindalco', 'vedanta',
        'coal india', 'nmdc', 'hindustan zinc', 'jindal steel', 'sail',
    ],
    'Power': [
        'ntpc', 'power grid', 'powergrid', 'tata power', 
        'adani power', 'adani green', 'jsw energy', 'nhpc', 'sjvn',
    ],
    'Telecom': [
        'bharti airtel', 'airtel', 'vodafone idea', 'vi',
        'indus towers', 'tata comm', 'route mobile',
    ],
    'Infrastructure': [
        'larsen & toubro', 'l&t', 'ultratech', 'acc', 'ambuja',
        'shree cement', 'dalmia bharat', 'dlf', 'godrej properties',
        'oberoi realty', 'prestige', 'adani ports',
    ],
    'Capital Goods': [
        'siemens', 'abb', 'cummins', 'thermax',
        'bhel', 'bharat electronics', 'bel', 'hal',
        'honeywell', 'cg power', 'suzlon',
    ],
    'Chemicals': [
        'pidilite', 'asian paints', 'berger paints',
        'srf', 'aarti industries', 'deepak nitrite',
        'tata chemicals', 'pi industries', 'upl',
    ],
    'Retail': [
        'avenue supermarts', 'dmart', 'trent', 'titan',
        'aditya birla fashion', 'v-mart', 'shoppers stop',
    ],
}

def is_garbage(text):
    """Check if text is garbage data"""
    if not text or not isinstance(text, str):
        return True
    
    text = text.strip()
    if len(text) < 3:
        return True
    
    for pattern in GARBAGE_REGEX:
        if pattern.search(text):
            return True
    
    # Only numbers/symbols
    if re.match(r'^[\d\s\.\,\%\-\+\(\)\/]+$', text):
        return True
    
    return False

def get_sector(company_name):
    """Map company to sector"""
    if not company_name:
        return 'Others'
    
    company_lower = company_name.lower()
    
    for sector, keywords in SECTOR_KEYWORDS.items():
        for keyword in keywords:
            if keyword in company_lower:
                return sector
    
    return 'Others'

def extract_percentage(text):
    """Extract percentage from text"""
    if not text:
        return None
    
    # Clean text
    text = str(text).strip().replace(',', '')
    
    # Match percentage patterns
    match = re.search(r'(\d+\.?\d*)\s*%?', text)
    if match:
        val = float(match.group(1))
        if 0 < val <= 25:  # Valid holding percentage
            return val
    
    return None

def parse_holdings_table(table):
    """Parse a holdings table and extract clean data"""
    holdings = []
    
    if not table or len(table) < 2:
        return holdings
    
    # Find column indices
    header_row = table[0]
    company_col = -1
    sector_col = -1
    pct_col = -1
    
    for i, cell in enumerate(header_row):
        if cell:
            cell_lower = str(cell).lower()
            if any(w in cell_lower for w in ['company', 'stock', 'name', 'instrument', 'security', 'issuer']):
                company_col = i
            elif any(w in cell_lower for w in ['sector', 'industry']):
                sector_col = i
            elif any(w in cell_lower for w in ['%', 'weight', 'allocation', 'holding', 'asset']):
                pct_col = i
    
    # If no header found, try first two columns
    if company_col == -1:
        company_col = 0
    if pct_col == -1 and len(header_row) > 1:
        pct_col = len(header_row) - 1  # Last column often has %
    
    # Extract holdings from data rows
    for row in table[1:]:
        if len(row) <= company_col:
            continue
        
        company = str(row[company_col]).strip() if row[company_col] else ''
        
        # Skip garbage
        if is_garbage(company):
            continue
        
        # Get percentage
        pct = None
        if pct_col >= 0 and pct_col < len(row):
            pct = extract_percentage(row[pct_col])
        
        if not pct:
            # Try to find percentage in any column
            for cell in row:
                pct = extract_percentage(cell)
                if pct:
                    break
        
        if not pct:
            continue
        
        # Get sector
        sector = 'Others'
        if sector_col >= 0 and sector_col < len(row) and row[sector_col]:
            sector = str(row[sector_col]).strip()
            if is_garbage(sector):
                sector = get_sector(company)
        else:
            sector = get_sector(company)
        
        holdings.append({
            'company': company,
            'sector': sector,
            'percentage': round(pct, 2)
        })
    
    return holdings

def extract_holdings_from_text(text):
    """Extract holdings from plain text using patterns"""
    holdings = []
    
    # Pattern: Company Name followed by percentage
    pattern = r'([A-Z][A-Za-z\s\.\&\-]+(?:Ltd\.?|Limited|Inc\.?|Corp\.?)?)\s+(\d+\.?\d*)\s*%'
    
    matches = re.findall(pattern, text)
    for company, pct in matches:
        company = company.strip()
        if not is_garbage(company) and len(company) > 5:
            pct_val = float(pct)
            if 0 < pct_val <= 25:
                holdings.append({
                    'company': company,
                    'sector': get_sector(company),
                    'percentage': round(pct_val, 2)
                })
    
    return holdings

def detect_fund_names(text):
    """Detect fund names in PDF text"""
    fund_patterns = [
        r'([A-Za-z\s]+(?:Large|Mid|Small|Multi|Flexi|Focused|Contra|Value|Growth|Balanced|Equity|Debt|Hybrid|ELSS|Tax|Saver|Advantage|Opportunities|Dynamic|Index)\s*(?:Cap|Fund|Scheme|Plan)?[^\n]*)',
    ]
    
    funds = []
    for pattern in fund_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        funds.extend(matches)
    
    return list(set(funds))

def parse_pdf_improved(pdf_path):
    """Parse PDF with improved logic"""
    all_holdings = []
    fund_name = None
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Extract tables
                tables = page.extract_tables()
                for table in tables:
                    holdings = parse_holdings_table(table)
                    all_holdings.extend(holdings)
                
                # Also try text extraction
                text = page.extract_text() or ''
                text_holdings = extract_holdings_from_text(text)
                
                # Add text holdings if not duplicates
                existing_companies = {h['company'].lower() for h in all_holdings}
                for h in text_holdings:
                    if h['company'].lower() not in existing_companies:
                        all_holdings.append(h)
                        existing_companies.add(h['company'].lower())
    
    except Exception as e:
        print(f'   ❌ Error parsing PDF: {e}')
        return []
    
    # Deduplicate and sort by percentage
    seen = set()
    unique_holdings = []
    for h in all_holdings:
        key = h['company'].lower()
        if key not in seen:
            seen.add(key)
            unique_holdings.append(h)
    
    # Sort by percentage descending
    unique_holdings.sort(key=lambda x: x['percentage'], reverse=True)
    
    # Keep top 20 holdings
    return unique_holdings[:20]

def derive_sector_allocation(holdings):
    """Derive sector allocation from holdings"""
    sector_totals = defaultdict(float)
    
    for h in holdings:
        sector = h.get('sector', 'Others')
        pct = h.get('percentage', 0)
        sector_totals[sector] += pct
    
    sector_allocation = [
        {'sector': sector, 'percentage': round(pct, 2)}
        for sector, pct in sorted(sector_totals.items(), key=lambda x: -x[1])
        if pct > 0
    ]
    
    return sector_allocation

def update_database(amc_name, holdings):
    """Update funds in database with extracted holdings"""
    if not holdings:
        return 0
    
    # Find funds for this AMC that don't have good holdings
    query = {
        'amc.name': {'$regex': amc_name, '$options': 'i'},
        '$or': [
            {'holdings': {'$exists': False}},
            {'holdings': None},
            {'holdings': []},
            {'holdings': {'$size': 1}},  # Only 1 holding is likely bad
        ]
    }
    
    funds = list(db.funds.find(query))
    updated = 0
    
    sector_allocation = derive_sector_allocation(holdings)
    
    for fund in funds:
        db.funds.update_one(
            {'_id': fund['_id']},
            {'$set': {
                'holdings': holdings,
                'sector_allocation': sector_allocation,
                'holdingsLastUpdated': __import__('datetime').datetime.utcnow(),
                'holdingsSource': 'AMC Factsheet (Improved Parser)'
            }}
        )
        updated += 1
    
    return updated

# AMC to PDF mapping
AMC_PDF_MAP = {
    'HDFC': ['HDFC MF Factsheet', 'Fund Facts - HDFC'],
    'SBI': ['sbimf-schemes-factsheet', 'all-sbimf'],
    'ICICI Prudential': ['Complete Factsheet December', 'Factsheet-December-2025'],
    'Kotak Mahindra': ['KotakMFFactsheet'],
    'Nippon India': ['Nippon-FS'],
    'Axis': ['Axis Fund Factsheet'],
    'Aditya Birla': ['ABSLMF-Empower'],
    'UTI': ['UTI Fund Watch'],
    'Tata': ['TataMF-Factsheet'],
    'Canara Robeco': ['Canara-Robeco-factsheet'],
    'Bajaj Finserv': ['bajaj_finserv_factsheet'],
    'Bandhan': ['bandhan-passive-factsheet'],
}

def main():
    print('='*70)
    print('PHASE 3: IMPROVED PDF PARSER')
    print('='*70)
    
    # Get initial stats
    print('\n📊 Before Processing:')
    total = db.funds.count_documents({})
    with_holdings = db.funds.count_documents({'holdings': {'$exists': True, '$not': {'$size': 0}}})
    print(f'   Total Funds: {total:,}')
    print(f'   With Holdings: {with_holdings:,} ({with_holdings/total*100:.1f}%)')
    
    # Get PDF files
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith('.pdf')]
    print(f'\n📁 Found {len(pdf_files)} PDF files')
    
    total_updated = 0
    
    # Process each AMC
    print('\n🔄 Processing PDFs with improved parser...\n')
    
    for amc_name, pdf_patterns in AMC_PDF_MAP.items():
        print(f'\n🏢 {amc_name} Mutual Fund')
        print('-'*50)
        
        # Find matching PDFs
        matching_pdfs = []
        for pdf in pdf_files:
            for pattern in pdf_patterns:
                if pattern.lower() in pdf.lower():
                    matching_pdfs.append(pdf)
                    break
        
        if not matching_pdfs:
            print(f'   ⚠️ No PDF found')
            continue
        
        all_holdings = []
        
        for pdf_file in matching_pdfs:
            pdf_path = os.path.join(PDF_FOLDER, pdf_file)
            print(f'   📄 Parsing: {pdf_file}')
            
            holdings = parse_pdf_improved(pdf_path)
            print(f'      Found {len(holdings)} clean holdings')
            
            if holdings:
                all_holdings.extend(holdings)
        
        if all_holdings:
            # Deduplicate
            seen = set()
            unique = []
            for h in all_holdings:
                key = h['company'].lower()
                if key not in seen:
                    seen.add(key)
                    unique.append(h)
            
            # Sort and limit
            unique.sort(key=lambda x: x['percentage'], reverse=True)
            unique = unique[:15]  # Top 15 holdings
            
            print(f'   📊 Top holdings:')
            for h in unique[:5]:
                print(f'      → {h["company"]}: {h["percentage"]}% ({h["sector"]})')
            
            # Update database
            updated = update_database(amc_name, unique)
            total_updated += updated
            print(f'   ✅ Updated {updated} funds')
    
    # Final stats
    print('\n' + '='*70)
    print('PHASE 3 RESULTS')
    print('='*70)
    
    print(f'\n📊 After Processing:')
    with_holdings_after = db.funds.count_documents({'holdings': {'$exists': True, '$not': {'$size': 0}}})
    with_real_sectors = db.funds.count_documents({
        'sector_allocation': {'$elemMatch': {'sector': {'$nin': ['Others', '', None]}}}
    })
    
    print(f'   Total Funds: {total:,}')
    print(f'   With Holdings: {with_holdings_after:,} ({with_holdings_after/total*100:.1f}%)')
    print(f'   With Real Sectors: {with_real_sectors:,} ({with_real_sectors/total*100:.1f}%)')
    print(f'   Funds Updated: {total_updated}')
    print(f'   Change: {with_holdings} → {with_holdings_after} ({with_holdings_after - with_holdings:+,})')
    
    client.close()
    print('\n' + '='*70)
    print('✅ PHASE 3 COMPLETE')
    print('='*70)

if __name__ == '__main__':
    main()
