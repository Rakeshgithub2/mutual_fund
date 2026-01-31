"""
PHASE 4: AI ENHANCEMENT
=======================
Use Gemini AI to get high-quality holdings for top equity funds
Rate limited: ~10 requests/minute
"""
import google.generativeai as genai
import time
import json
import re
from pymongo import MongoClient
from datetime import datetime

# Configuration
GEMINI_API_KEY = "AIzaSyAUk76mSH-ZAfDbLM1dIyiMZBbEuvzVpwo"
genai.configure(api_key=GEMINI_API_KEY)

# MongoDB connection
client = MongoClient('mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds')
db = client['mutualfunds']

# Rate limiting
REQUESTS_PER_MINUTE = 8  # Stay under 10 to be safe
DELAY_BETWEEN_REQUESTS = 60 / REQUESTS_PER_MINUTE  # ~7.5 seconds

def get_holdings_from_gemini(fund_name, amc_name, category):
    """Get holdings from Gemini AI"""
    
    prompt = f"""You are a mutual fund data expert. Provide the TOP 10 HOLDINGS for this Indian mutual fund:

Fund Name: {fund_name}
AMC: {amc_name}
Category: {category}

Return ONLY a JSON array with this exact format (no markdown, no explanation):
[
  {{"company": "Company Name Ltd", "sector": "Sector Name", "percentage": 8.5}},
  {{"company": "Another Company Ltd", "sector": "Sector Name", "percentage": 7.2}}
]

Rules:
1. Use real Indian company names (HDFC Bank Ltd, Infosys Ltd, Reliance Industries Ltd, etc.)
2. Use standard sector names: Financial Services, Information Technology, Oil & Gas, Healthcare, Automobile, Consumer Goods, Metals & Mining, Power, Telecom, Infrastructure, Capital Goods, Chemicals
3. Percentages should be realistic (typically 3-10% for top holdings)
4. Total should not exceed 60%
5. If you don't know the exact holdings, provide typical holdings for this fund category

Return ONLY the JSON array, nothing else."""

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        # Parse response
        text = response.text.strip()
        
        # Remove markdown code blocks if present
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        
        holdings = json.loads(text)
        
        # Validate
        if isinstance(holdings, list) and len(holdings) > 0:
            # Filter valid holdings
            valid_holdings = []
            for h in holdings:
                if isinstance(h, dict) and 'company' in h and 'percentage' in h:
                    pct = h.get('percentage', 0)
                    if isinstance(pct, (int, float)) and 0 < pct <= 15:
                        valid_holdings.append({
                            'company': str(h.get('company', '')),
                            'sector': str(h.get('sector', 'Others')),
                            'percentage': round(float(pct), 2)
                        })
            
            return valid_holdings[:10]  # Top 10
        
        return None
    
    except Exception as e:
        print(f'      ❌ Error: {e}')
        return None

def derive_sector_allocation(holdings):
    """Derive sector allocation from holdings"""
    from collections import defaultdict
    
    sector_totals = defaultdict(float)
    for h in holdings:
        sector = h.get('sector', 'Others')
        pct = h.get('percentage', 0)
        sector_totals[sector] += pct
    
    return [
        {'sector': sector, 'percentage': round(pct, 2)}
        for sector, pct in sorted(sector_totals.items(), key=lambda x: -x[1])
    ]

def get_top_equity_funds(limit=500):
    """Get top equity funds by AUM"""
    
    # Find equity funds, sorted by AUM
    pipeline = [
        {'$match': {
            'category': 'equity',
            'aum': {'$exists': True, '$ne': None}
        }},
        {'$sort': {'aum': -1}},
        {'$limit': limit}
    ]
    
    funds = list(db.funds.aggregate(pipeline))
    return funds

def main():
    print('='*70)
    print('PHASE 4: AI ENHANCEMENT (Gemini)')
    print('='*70)
    print(f'Rate limit: {REQUESTS_PER_MINUTE} requests/minute')
    print(f'Delay: {DELAY_BETWEEN_REQUESTS:.1f} seconds between requests')
    
    # Get initial stats
    print('\n📊 Before Processing:')
    total = db.funds.count_documents({})
    with_holdings = db.funds.count_documents({'holdings': {'$exists': True, '$not': {'$size': 0}}})
    print(f'   Total Funds: {total:,}')
    print(f'   With Holdings: {with_holdings:,} ({with_holdings/total*100:.1f}%)')
    
    # Get top equity funds
    print('\n🔍 Finding top equity funds by AUM...')
    top_funds = get_top_equity_funds(500)
    print(f'   Found {len(top_funds)} equity funds')
    
    # Process funds
    print('\n🤖 Processing with Gemini AI...\n')
    
    processed = 0
    updated = 0
    errors = 0
    start_time = time.time()
    
    for i, fund in enumerate(top_funds):
        fund_name = fund.get('schemeName', fund.get('name', 'Unknown'))
        amc_data = fund.get('amc', {})
        amc_name = amc_data.get('name', 'Unknown AMC') if isinstance(amc_data, dict) else str(amc_data)
        category = fund.get('category', 'equity')
        sub_cat = fund.get('subCategory', fund.get('sub_category', ''))
        
        # Handle AUM (could be dict, number, or string)
        aum_raw = fund.get('aum', 0)
        if isinstance(aum_raw, dict):
            aum = aum_raw.get('value', 0) or 0
        elif isinstance(aum_raw, (int, float)):
            aum = aum_raw
        else:
            aum = 0
        
        print(f'[{i+1}/{len(top_funds)}] {fund_name[:50]}')
        print(f'         AMC: {amc_name}, AUM: ₹{aum:,.0f} Cr')
        
        # Get holdings from Gemini
        holdings = get_holdings_from_gemini(fund_name, amc_name, f'{category} - {sub_cat}')
        
        if holdings and len(holdings) >= 5:
            # Derive sector allocation
            sector_allocation = derive_sector_allocation(holdings)
            
            # Update database
            db.funds.update_one(
                {'_id': fund['_id']},
                {'$set': {
                    'holdings': holdings,
                    'sector_allocation': sector_allocation,
                    'holdingsLastUpdated': datetime.utcnow(),
                    'holdingsSource': 'Gemini AI Enhanced'
                }}
            )
            
            updated += 1
            print(f'         ✅ Updated with {len(holdings)} holdings')
            
            # Show sample
            if updated <= 5:
                for h in holdings[:3]:
                    print(f'            → {h["company"]}: {h["percentage"]}% ({h["sector"]})')
        else:
            errors += 1
            print(f'         ⚠️ Skipped (no valid holdings)')
        
        processed += 1
        
        # Rate limiting
        if processed < len(top_funds):
            print(f'         ⏳ Waiting {DELAY_BETWEEN_REQUESTS:.1f}s...')
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # Progress update every 50
        if processed % 50 == 0:
            elapsed = time.time() - start_time
            rate = processed / elapsed * 60
            remaining = (len(top_funds) - processed) / rate if rate > 0 else 0
            print(f'\n📊 Progress: {processed}/{len(top_funds)} ({processed/len(top_funds)*100:.0f}%)')
            print(f'   Rate: {rate:.1f} funds/min, ETA: {remaining:.0f} min\n')
    
    # Final stats
    elapsed_total = time.time() - start_time
    
    print('\n' + '='*70)
    print('PHASE 4 RESULTS')
    print('='*70)
    
    print(f'\n📊 Processing Statistics:')
    print(f'   Funds Processed: {processed}')
    print(f'   Successfully Updated: {updated}')
    print(f'   Errors/Skipped: {errors}')
    print(f'   Time Elapsed: {elapsed_total/60:.1f} minutes')
    
    print(f'\n📊 After Processing:')
    with_holdings_after = db.funds.count_documents({'holdings': {'$exists': True, '$not': {'$size': 0}}})
    with_ai_holdings = db.funds.count_documents({'holdingsSource': 'Gemini AI Enhanced'})
    
    print(f'   Total Funds: {total:,}')
    print(f'   With Holdings: {with_holdings_after:,} ({with_holdings_after/total*100:.1f}%)')
    print(f'   AI Enhanced: {with_ai_holdings:,}')
    
    client.close()
    print('\n' + '='*70)
    print('✅ PHASE 4 COMPLETE')
    print('='*70)

if __name__ == '__main__':
    main()
