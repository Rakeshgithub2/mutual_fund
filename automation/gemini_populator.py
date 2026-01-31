"""
GEMINI HOLDINGS POPULATOR
==========================
Uses Google Gemini AI to populate holdings for mutual funds.
This script will update funds that don't have holdings data.

Run this script to populate holdings for funds in batches.
"""

import requests
import json
import re
import time
from datetime import datetime
from pymongo import MongoClient
from typing import Dict, List, Optional


# Configuration
MONGO_URI = "mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds"
GEMINI_API_KEY = "AIzaSyAUk76mSH-ZAfDbLM1dIyiMZBbEuvzVpwo"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


class GeminiHoldingsPopulator:
    """Populates mutual fund holdings using Gemini AI"""
    
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client['mutualfunds']
        self.funds_col = self.db['funds']
        self.session = requests.Session()
    
    def get_holdings_from_gemini(self, fund_name: str, category: str = "equity", retry_count: int = 0) -> Optional[Dict]:
        """
        Get holdings and sector allocation from Gemini AI.
        Includes retry logic for rate limiting.
        """
        if retry_count >= 3:
            return None
            
        prompt = f"""You are a mutual fund data expert. For the Indian mutual fund "{fund_name}" (category: {category}), 
provide the top 10 stock holdings and sector allocation based on typical portfolio composition.

Return ONLY a valid JSON object (no markdown, no explanation):
{{"holdings": [{{"company": "Company Name Ltd.", "sector": "Sector", "percentage": 9.5}}], "sectorAllocation": [{{"sector": "Sector Name", "percentage": 35.0}}]}}

Use real Indian company names. Holdings should sum to ~50-70%. Sectors should sum to ~95-100%.
For large cap: use Nifty 50 companies. For mid cap: use Nifty Midcap 150. For small cap: use smaller companies.
For debt funds: use bond issuers like government, PSUs, corporates."""

        try:
            response = self.session.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 2000
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                
                # Extract JSON from response
                json_match = re.search(r'\{[\s\S]*\}', text)
                if json_match:
                    return json.loads(json_match.group())
            elif response.status_code == 429:
                # Rate limited - wait and retry with exponential backoff
                wait_time = (2 ** retry_count) * 10  # 10s, 20s, 40s
                print(f"   ⏳ Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                return self.get_holdings_from_gemini(fund_name, category, retry_count + 1)
            elif response.status_code == 503:
                print("   ⏳ API overloaded, waiting 10s...")
                time.sleep(10)
                return self.get_holdings_from_gemini(fund_name, category, retry_count + 1)
            else:
                print(f"   ⚠️ Status: {response.status_code}")
                
        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSON error: {str(e)[:30]}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:40]}")
        
        return None
    
    def get_funds_without_holdings(self, limit: int = 100) -> List[Dict]:
        """Get funds that don't have holdings data"""
        return list(self.funds_col.find({
            '$or': [
                {'holdings': {'$exists': False}},
                {'holdings': {'$eq': []}},
                {'holdings': None},
                {'holdings': {'$size': 0}}
            ]
        }).limit(limit))
    
    def update_fund_holdings(self, fund_id, holdings_data: Dict) -> bool:
        """Update a fund's holdings in the database"""
        result = self.funds_col.update_one(
            {'_id': fund_id},
            {
                '$set': {
                    'holdings': holdings_data.get('holdings', []),
                    'sectorAllocation': holdings_data.get('sectorAllocation', []),
                    'holdingsLastUpdated': datetime.now().isoformat(),
                    'holdingsSource': 'Gemini AI'
                }
            }
        )
        return result.modified_count > 0
    
    def populate_holdings(self, batch_size: int = 20, delay: float = 3.0):
        """
        Populate holdings for funds without them.
        
        Args:
            batch_size: Number of funds to process
            delay: Delay between API calls (seconds)
        """
        print("=" * 60)
        print("GEMINI HOLDINGS POPULATOR")
        print("=" * 60)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print()
        
        # Get current status
        total_funds = self.funds_col.count_documents({})
        with_holdings = self.funds_col.count_documents({
            'holdings': {'$exists': True, '$ne': [], '$ne': None}
        })
        
        print(f"📊 Current Status:")
        print(f"   Total Funds: {total_funds:,}")
        print(f"   With Holdings: {with_holdings:,}")
        print(f"   Without Holdings: {total_funds - with_holdings:,}")
        print()
        
        # Get funds to process
        funds = self.get_funds_without_holdings(batch_size)
        print(f"📥 Processing {len(funds)} funds...")
        print()
        
        updated = 0
        failed = 0
        
        for i, fund in enumerate(funds, 1):
            fund_name = fund.get('schemeName', 'Unknown')
            category = fund.get('category', 'equity')
            
            print(f"[{i}/{len(funds)}] {fund_name[:55]}...")
            
            # Get holdings from Gemini
            holdings_data = self.get_holdings_from_gemini(fund_name, category)
            
            if holdings_data and holdings_data.get('holdings'):
                # Update fund
                if self.update_fund_holdings(fund['_id'], holdings_data):
                    updated += 1
                    h = len(holdings_data.get('holdings', []))
                    s = len(holdings_data.get('sectorAllocation', []))
                    print(f"   ✅ Holdings: {h}, Sectors: {s}")
                else:
                    failed += 1
                    print(f"   ⚠️ Update failed")
            else:
                failed += 1
                print(f"   ⚠️ No data")
            
            # Rate limiting
            time.sleep(delay)
        
        # Final status
        print()
        print("=" * 60)
        print(f"✅ COMPLETED")
        print(f"   Updated: {updated}")
        print(f"   Failed: {failed}")
        print("=" * 60)
        
        # Updated status
        new_with_holdings = self.funds_col.count_documents({
            'holdings': {'$exists': True, '$ne': [], '$ne': None}
        })
        print()
        print(f"📊 New Status:")
        print(f"   Total Funds: {total_funds:,}")
        print(f"   With Holdings: {new_with_holdings:,}")
        print(f"   Coverage: {new_with_holdings/total_funds*100:.1f}%")
        
        return updated
    
    def populate_priority_funds(self):
        """Populate holdings for high-priority funds first (popular funds)"""
        # Popular AMCs to prioritize
        priority_amcs = [
            'HDFC', 'ICICI', 'SBI', 'Axis', 'Kotak', 
            'Nippon', 'Aditya Birla', 'UTI', 'DSP', 'Mirae',
            'Motilal Oswal', 'PPFAS', 'Quant', 'Tata', 'Franklin'
        ]
        
        print("=" * 60)
        print("PRIORITY FUNDS POPULATOR")
        print("=" * 60)
        print()
        
        total_updated = 0
        
        for amc in priority_amcs:
            # Get funds from this AMC without holdings
            funds = list(self.funds_col.find({
                'fundHouse': {'$regex': amc, '$options': 'i'},
                '$or': [
                    {'holdings': {'$exists': False}},
                    {'holdings': {'$eq': []}},
                    {'holdings': None}
                ]
            }).limit(10))  # Top 10 per AMC
            
            if not funds:
                continue
            
            print(f"\n📊 {amc} Mutual Fund ({len(funds)} funds)")
            print("-" * 40)
            
            for fund in funds:
                fund_name = fund.get('schemeName', 'Unknown')
                category = fund.get('category', 'equity')
                
                print(f"   {fund_name[:50]}...")
                
                holdings_data = self.get_holdings_from_gemini(fund_name, category)
                
                if holdings_data and holdings_data.get('holdings'):
                    if self.update_fund_holdings(fund['_id'], holdings_data):
                        total_updated += 1
                        print(f"      ✅ Updated")
                    else:
                        print(f"      ⚠️ Failed")
                else:
                    print(f"      ⚠️ No data")
                
                time.sleep(1.5)
        
        print()
        print("=" * 60)
        print(f"✅ Total Updated: {total_updated} priority funds")
        print("=" * 60)
        
        return total_updated


def main():
    """Main function"""
    populator = GeminiHoldingsPopulator()
    
    print("Choose an option:")
    print("1. Populate batch of funds (50 funds)")
    print("2. Populate priority funds (top AMCs)")
    print("3. Show current status only")
    print()
    
    # Default: populate a batch
    print("Running batch population (50 funds)...")
    print()
    
    populator.populate_holdings(batch_size=50, delay=1.5)


if __name__ == "__main__":
    main()
