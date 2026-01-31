"""
SMART HOLDINGS POPULATOR
=========================
Intelligently populates holdings for mutual funds by:
1. Processing only Direct Plan Growth funds (most important)
2. Copying holdings to related fund variants (Regular, IDCW, etc.)
3. Using rate-limit aware API calls

This reduces API calls by ~80% while covering all funds.
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


class SmartHoldingsPopulator:
    """
    Smart populator that minimizes API calls by:
    - Processing only base funds (Direct Growth)
    - Copying holdings to related variants
    """
    
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client['mutualfunds']
        self.funds_col = self.db['funds']
        self.session = requests.Session()
        self.api_calls = 0
        self.last_call_time = 0
    
    def get_base_fund_name(self, fund_name: str) -> str:
        """Extract base fund name without plan/option variants"""
        # Remove common suffixes
        base = fund_name
        patterns = [
            r'\s*-\s*(Direct|Regular)\s*(Plan)?',
            r'\s*-\s*(Growth|IDCW|Dividend|Bonus)',
            r'\s*-\s*(Daily|Weekly|Monthly|Quarterly|Annual)\s*(IDCW|Dividend)?',
            r'\s*-\s*Reinvestment',
            r'\s*-\s*Payout',
            r'\s*\(.*?\)',  # Remove parenthetical content
        ]
        
        for pattern in patterns:
            base = re.sub(pattern, '', base, flags=re.IGNORECASE)
        
        return base.strip()
    
    def get_unique_base_funds(self, limit: int = 100) -> List[Dict]:
        """
        Get unique base funds (without variants) that need holdings.
        Returns one fund per base name.
        """
        # Get all funds without holdings
        funds_without = list(self.funds_col.find({
            '$or': [
                {'holdings': {'$exists': False}},
                {'holdings': {'$eq': []}},
                {'holdings': None}
            ],
            # Prefer Direct Plan Growth
            'schemeName': {'$regex': 'Direct.*Growth', '$options': 'i'}
        }).limit(limit * 3))
        
        # Group by base name
        base_funds = {}
        for fund in funds_without:
            base_name = self.get_base_fund_name(fund.get('schemeName', ''))
            if base_name and base_name not in base_funds:
                base_funds[base_name] = fund
        
        return list(base_funds.values())[:limit]
    
    def find_related_funds(self, base_name: str) -> List[Dict]:
        """Find all fund variants with the same base name"""
        # Escape regex special characters
        escaped = re.escape(base_name)
        return list(self.funds_col.find({
            'schemeName': {'$regex': escaped, '$options': 'i'}
        }))
    
    def rate_limited_api_call(self, prompt: str, min_delay: float = 3.0) -> Optional[Dict]:
        """Make rate-limited API call with exponential backoff"""
        # Ensure minimum delay between calls
        elapsed = time.time() - self.last_call_time
        if elapsed < min_delay:
            time.sleep(min_delay - elapsed)
        
        for retry in range(3):
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
                
                self.last_call_time = time.time()
                self.api_calls += 1
                
                if response.status_code == 200:
                    data = response.json()
                    text = data['candidates'][0]['content']['parts'][0]['text']
                    json_match = re.search(r'\{[\s\S]*\}', text)
                    if json_match:
                        return json.loads(json_match.group())
                    return None
                    
                elif response.status_code == 429:
                    wait = (2 ** retry) * 15  # 15s, 30s, 60s
                    print(f"   ⏳ Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    
                elif response.status_code == 503:
                    print(f"   ⏳ API overloaded, waiting 15s...")
                    time.sleep(15)
                    
                else:
                    print(f"   ⚠️ Status: {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:40]}")
                time.sleep(5)
        
        return None
    
    def get_holdings_for_fund(self, fund_name: str, category: str = "equity") -> Optional[Dict]:
        """Get holdings from Gemini AI"""
        prompt = f"""You are a mutual fund data expert. For "{fund_name}" (category: {category}), 
provide top 10 stock holdings and sector allocation.

Return ONLY valid JSON (no markdown):
{{"holdings": [{{"company": "Company Name Ltd.", "sector": "Sector", "percentage": 9.5}}], "sectorAllocation": [{{"sector": "Sector Name", "percentage": 35.0}}]}}

Use real Indian companies. For large cap: Nifty 50. For mid cap: Midcap 150. For small cap: smaller companies.
For debt: government bonds, PSU bonds, corporate bonds."""

        return self.rate_limited_api_call(prompt)
    
    def update_fund_holdings(self, fund_id, holdings_data: Dict) -> bool:
        """Update a fund's holdings"""
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
    
    def populate_smart(self, batch_size: int = 30):
        """
        Smart population: Get holdings for base funds, copy to variants.
        """
        print("=" * 60)
        print("SMART HOLDINGS POPULATOR")
        print("=" * 60)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print()
        
        # Current status
        total = self.funds_col.count_documents({})
        with_holdings = self.funds_col.count_documents({
            'holdings': {'$exists': True, '$ne': [], '$ne': None}
        })
        
        print(f"📊 Current Status:")
        print(f"   Total Funds: {total:,}")
        print(f"   With Holdings: {with_holdings:,} ({with_holdings/total*100:.1f}%)")
        print(f"   Without Holdings: {total - with_holdings:,}")
        print()
        
        # Get unique base funds
        base_funds = self.get_unique_base_funds(batch_size)
        print(f"📥 Processing {len(base_funds)} unique base funds...")
        print("   (Holdings will be copied to related variants)")
        print()
        
        funds_updated = 0
        variants_updated = 0
        
        for i, fund in enumerate(base_funds, 1):
            fund_name = fund.get('schemeName', 'Unknown')
            category = fund.get('category', 'equity')
            base_name = self.get_base_fund_name(fund_name)
            
            print(f"[{i}/{len(base_funds)}] {base_name[:50]}...")
            
            # Get holdings from Gemini
            holdings_data = self.get_holdings_for_fund(fund_name, category)
            
            if holdings_data and holdings_data.get('holdings'):
                h = len(holdings_data.get('holdings', []))
                s = len(holdings_data.get('sectorAllocation', []))
                
                # Find and update all related funds
                related = self.find_related_funds(base_name)
                
                for rel_fund in related:
                    if self.update_fund_holdings(rel_fund['_id'], holdings_data):
                        if rel_fund['_id'] == fund['_id']:
                            funds_updated += 1
                        else:
                            variants_updated += 1
                
                print(f"   ✅ Holdings: {h}, Sectors: {s} → {len(related)} funds")
            else:
                print(f"   ⚠️ No data")
        
        # Final status
        print()
        print("=" * 60)
        print(f"✅ COMPLETED (API calls: {self.api_calls})")
        print(f"   Base funds updated: {funds_updated}")
        print(f"   Variants updated: {variants_updated}")
        print(f"   Total updated: {funds_updated + variants_updated}")
        print("=" * 60)
        
        # New status
        new_with = self.funds_col.count_documents({
            'holdings': {'$exists': True, '$ne': [], '$ne': None}
        })
        print()
        print(f"📊 New Status:")
        print(f"   With Holdings: {new_with:,} ({new_with/total*100:.1f}%)")
        print(f"   Improvement: +{new_with - with_holdings:,} funds")
        
        return funds_updated + variants_updated


def main():
    """Main function"""
    populator = SmartHoldingsPopulator()
    
    print("Smart Holdings Populator")
    print("========================")
    print("This will process unique base funds and copy holdings to variants.")
    print()
    
    # Run with batch of 30 (covers ~150+ fund variants due to copying)
    populator.populate_smart(batch_size=30)


if __name__ == "__main__":
    main()
