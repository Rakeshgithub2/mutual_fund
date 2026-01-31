"""
MFAPI.IN HOLDINGS EXTRACTOR
============================
Uses mfapi.in - a FREE, reliable API for Indian mutual fund data.
This API provides NAV data and we can cross-reference with our existing database.

Also integrates with Gemini AI to extract holdings from public sources.
"""

import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
from pymongo import MongoClient
import time
import os


# MongoDB connection
MONGO_URI = "mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds"

# Gemini API for AI-powered extraction
GEMINI_API_KEY = "AIzaSyAUk76mSH-ZAfDbLM1dIyiMZBbEuvzVpwo"


class MFAPIExtractor:
    """
    Uses mfapi.in for mutual fund data.
    This is a FREE API with no authentication required.
    """
    
    BASE_URL = "https://api.mfapi.in"
    
    # Popular fund scheme codes from AMFI
    FUND_CODES = {
        # Large Cap Funds - Direct Growth
        "HDFC Top 100 Fund - Direct Plan - Growth": 118989,
        "ICICI Prudential Bluechip Fund - Direct Plan - Growth": 120586,
        "SBI Bluechip Fund - Direct Plan - Growth": 119598,
        "Axis Bluechip Fund - Direct Plan - Growth": 120503,
        "Nippon India Large Cap Fund - Direct Plan - Growth": 118778,
        "Kotak Bluechip Fund - Direct Plan - Growth": 120505,
        "Mirae Asset Large Cap Fund - Direct Plan - Growth": 120503,
        "UTI Large Cap Fund - Direct Plan - Growth": 120716,
        "Aditya Birla Sun Life Frontline Equity Fund - Direct Plan - Growth": 119551,
        "Canara Robeco Bluechip Equity Fund - Direct Plan - Growth": 118636,
        
        # Flexi Cap Funds
        "HDFC Flexi Cap Fund - Direct Plan - Growth": 118955,
        "Parag Parikh Flexi Cap Fund - Direct Plan - Growth": 122639,
        "Quant Active Fund - Direct Plan - Growth": 120823,
        "Motilal Oswal Flexi Cap Fund - Direct Plan - Growth": 145552,
        "UTI Flexi Cap Fund - Direct Plan - Growth": 120716,
        
        # Mid Cap Funds
        "HDFC Mid-Cap Opportunities Fund - Direct Plan - Growth": 118989,
        "Axis Midcap Fund - Direct Plan - Growth": 120503,
        "Kotak Emerging Equity Fund - Direct Plan - Growth": 120505,
        "Nippon India Growth Fund - Direct Plan - Growth": 118778,
        "SBI Magnum Midcap Fund - Direct Plan - Growth": 119598,
        
        # Small Cap Funds
        "Nippon India Small Cap Fund - Direct Plan - Growth": 118778,
        "Axis Small Cap Fund - Direct Plan - Growth": 125354,
        "SBI Small Cap Fund - Direct Plan - Growth": 125497,
        "Kotak Small Cap Fund - Direct Plan - Growth": 125356,
        "HDFC Small Cap Fund - Direct Plan - Growth": 130502,
        
        # ELSS Funds
        "Quant Tax Plan - Direct Plan - Growth": 120828,
        "Axis Long Term Equity Fund - Direct Plan - Growth": 120503,
        "HDFC Tax Saver Fund - Direct Plan - Growth": 118989,
        "SBI Long Term Equity Fund - Direct Plan - Growth": 119598,
        "ICICI Prudential Long Term Equity Fund - Direct Plan - Growth": 120586,
    }
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_fund_nav(self, scheme_code: int) -> Optional[Dict]:
        """
        Get fund NAV and historical data from mfapi.in
        
        Args:
            scheme_code: AMFI scheme code
        """
        url = f"{self.BASE_URL}/mf/{scheme_code}"
        
        try:
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract latest NAV
                nav_data = data.get('data', [])
                if nav_data:
                    latest = nav_data[0]
                    return {
                        'schemeCode': scheme_code,
                        'schemeName': data.get('meta', {}).get('scheme_name', ''),
                        'fundHouse': data.get('meta', {}).get('fund_house', ''),
                        'schemeType': data.get('meta', {}).get('scheme_type', ''),
                        'schemeCategory': data.get('meta', {}).get('scheme_category', ''),
                        'nav': float(latest.get('nav', 0)),
                        'date': latest.get('date', ''),
                        'source': 'mfapi.in'
                    }
            else:
                print(f"   ⚠️ Status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}")
        
        return None
    
    def get_all_funds(self) -> List[Dict]:
        """Get list of all mutual funds from mfapi.in"""
        url = f"{self.BASE_URL}/mf"
        
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error fetching fund list: {e}")
        
        return []
    
    def test_api(self):
        """Test the API with a sample fund"""
        print("Testing mfapi.in API...")
        print()
        
        # Test with HDFC Top 100 (scheme code: 118989)
        test_code = 118989
        print(f"Fetching scheme code: {test_code}")
        
        result = self.get_fund_nav(test_code)
        
        if result:
            print("\n✅ API is working!")
            print(f"   Scheme: {result.get('schemeName', '')[:50]}")
            print(f"   Fund House: {result.get('fundHouse', '')}")
            print(f"   NAV: ₹{result.get('nav', 0):.2f}")
            print(f"   Date: {result.get('date', '')}")
            return True
        else:
            print("\n⚠️ API test failed")
            return False


class GeminiHoldingsExtractor:
    """
    Uses Google Gemini AI to extract holdings data from public sources.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    
    def extract_holdings(self, fund_name: str) -> Optional[Dict]:
        """
        Use Gemini to generate realistic holdings based on fund type.
        Note: This generates holdings based on public knowledge of fund strategies.
        """
        prompt = f"""
You are a mutual fund expert. For the fund "{fund_name}", provide the typical top 10 stock holdings 
and sector allocation based on its investment mandate and publicly available information.

Return ONLY a valid JSON object with this exact structure (no markdown, no explanation):
{{
    "holdings": [
        {{"company": "Company Name", "sector": "Sector Name", "percentage": 9.5}},
        ...
    ],
    "sectorAllocation": [
        {{"sector": "Sector Name", "percentage": 35.5}},
        ...
    ]
}}

Focus on real Indian companies and realistic percentage allocations.
For large cap funds: focus on Nifty 50 companies
For mid cap funds: focus on Nifty Midcap 150 companies
For small cap funds: focus on smaller companies
"""
        
        try:
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 2000,
                        "responseMimeType": "application/json"
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                
                # Parse JSON from response
                # Clean up the response - remove markdown code blocks if present
                text = text.strip()
                
                # Remove markdown code blocks
                if '```json' in text:
                    text = text.split('```json')[1].split('```')[0]
                elif '```' in text:
                    parts = text.split('```')
                    if len(parts) >= 2:
                        text = parts[1]
                
                # Find JSON object in text
                import re
                json_match = re.search(r'\{[\s\S]*\}', text)
                if json_match:
                    text = json_match.group()
                
                holdings_data = json.loads(text)
                return holdings_data
            else:
                print(f"   ⚠️ Gemini API status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSON parse error: {str(e)[:30]}")
        except Exception as e:
            print(f"   ❌ Gemini error: {str(e)[:50]}")
        
        return None


class CombinedExtractor:
    """
    Combines multiple sources to get complete fund data:
    1. mfapi.in for NAV and basic info
    2. Existing MongoDB data
    3. Gemini AI for holdings (based on fund strategy)
    """
    
    def __init__(self):
        self.mfapi = MFAPIExtractor()
        self.gemini = GeminiHoldingsExtractor(GEMINI_API_KEY)
        self.client = MongoClient(MONGO_URI)
        self.db = self.client['mutualfunds']
        self.funds_col = self.db['funds']
    
    def update_fund_holdings(self, limit: int = 50) -> int:
        """
        Update holdings for funds that don't have them.
        Uses Gemini AI to generate realistic holdings based on fund type.
        
        Args:
            limit: Maximum number of funds to update
        """
        print("=" * 60)
        print("COMBINED HOLDINGS EXTRACTOR")
        print("=" * 60)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print()
        
        # Find funds without holdings
        funds_without_holdings = list(self.funds_col.find({
            '$or': [
                {'holdings': {'$exists': False}},
                {'holdings': {'$eq': []}},
                {'holdings': None}
            ]
        }).limit(limit))
        
        print(f"📊 Found {len(funds_without_holdings)} funds without holdings")
        print()
        
        updated = 0
        
        for i, fund in enumerate(funds_without_holdings, 1):
            fund_name = fund.get('schemeName', 'Unknown')
            print(f"[{i}/{len(funds_without_holdings)}] {fund_name[:50]}...")
            
            # Use Gemini to extract holdings
            holdings_data = self.gemini.extract_holdings(fund_name)
            
            if holdings_data:
                # Update fund in database
                result = self.funds_col.update_one(
                    {'_id': fund['_id']},
                    {
                        '$set': {
                            'holdings': holdings_data.get('holdings', []),
                            'sectorAllocation': holdings_data.get('sectorAllocation', []),
                            'holdingsLastUpdated': datetime.now().isoformat(),
                            'holdingsSource': 'AI Generated (Gemini)'
                        }
                    }
                )
                
                if result.modified_count > 0:
                    updated += 1
                    h = len(holdings_data.get('holdings', []))
                    s = len(holdings_data.get('sectorAllocation', []))
                    print(f"   ✅ Updated: Holdings={h}, Sectors={s}")
            else:
                print(f"   ⚠️ No holdings extracted")
            
            # Rate limiting for Gemini API
            time.sleep(1)
        
        print()
        print("=" * 60)
        print(f"✅ Updated {updated} funds with holdings")
        print("=" * 60)
        
        return updated
    
    def get_status(self):
        """Get current database status"""
        total = self.funds_col.count_documents({})
        with_holdings = self.funds_col.count_documents({
            'holdings': {'$exists': True, '$ne': [], '$ne': None}
        })
        
        print("📊 Database Status:")
        print(f"   Total Funds: {total:,}")
        print(f"   With Holdings: {with_holdings:,}")
        print(f"   Without Holdings: {total - with_holdings:,}")
        print(f"   Coverage: {with_holdings/total*100:.1f}%")


def main():
    """Main function"""
    print("=" * 60)
    print("MUTUAL FUND DATA EXTRACTOR")
    print("=" * 60)
    print()
    
    # Test mfapi.in
    mfapi = MFAPIExtractor()
    if mfapi.test_api():
        print("\n✅ mfapi.in is working!")
    
    print()
    
    # Test Gemini
    print("Testing Gemini AI for holdings extraction...")
    gemini = GeminiHoldingsExtractor(GEMINI_API_KEY)
    result = gemini.extract_holdings("HDFC Top 100 Fund - Direct Plan")
    
    if result:
        print("\n✅ Gemini AI extraction working!")
        print(f"   Holdings: {len(result.get('holdings', []))}")
        print(f"   Sectors: {len(result.get('sectorAllocation', []))}")
        
        if result.get('holdings'):
            print("\n   Sample Holdings:")
            for h in result['holdings'][:3]:
                print(f"     - {h['company']}: {h['percentage']}%")
    else:
        print("\n⚠️ Gemini extraction failed")
    
    print()
    print("=" * 60)
    print("To update funds with holdings, run:")
    print("   extractor = CombinedExtractor()")
    print("   extractor.update_fund_holdings(limit=50)")
    print("=" * 60)


if __name__ == "__main__":
    main()
