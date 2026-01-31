"""
GROWW API HOLDINGS EXTRACTOR
=============================
Uses Groww's public API endpoints to get REAL holdings data.
Groww has well-structured JSON APIs that don't require JavaScript rendering.

This is the MOST RELIABLE solution for getting real holdings data.
"""

import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
from pymongo import MongoClient
import time
import re


# MongoDB connection
MONGO_URI = "mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds"


class GrowwAPI:
    """
    Fetches mutual fund holdings from Groww's public API.
    Groww provides clean JSON responses without needing browser automation.
    """
    
    BASE_URL = "https://groww.in/v1/api"
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://groww.in',
        'Referer': 'https://groww.in/mutual-funds',
    }
    
    # Groww search slugs for major funds
    # Format: Fund Name -> Groww URL slug
    FUND_SLUGS = {
        # Large Cap
        "HDFC Top 100 Fund - Direct Plan": "hdfc-top-100-fund-direct-plan-growth",
        "ICICI Prudential Bluechip Fund - Direct Plan": "icici-prudential-bluechip-fund-direct-plan-growth",
        "SBI Bluechip Fund - Direct Plan": "sbi-blue-chip-fund-direct-plan-growth",
        "Axis Bluechip Fund - Direct Plan": "axis-bluechip-fund-direct-plan-growth",
        "Nippon India Large Cap Fund - Direct Plan": "nippon-india-large-cap-fund-direct-plan-growth",
        "Kotak Bluechip Fund - Direct Plan": "kotak-bluechip-fund-direct-plan-growth",
        "Mirae Asset Large Cap Fund - Direct Plan": "mirae-asset-large-cap-fund-direct-plan-growth",
        "UTI Large Cap Fund - Direct Plan": "uti-large-cap-fund-direct-plan-growth",
        
        # Flexi Cap
        "HDFC Flexi Cap Fund - Direct Plan": "hdfc-flexi-cap-fund-direct-plan-growth",
        "Parag Parikh Flexi Cap Fund - Direct Plan": "parag-parikh-flexi-cap-fund-direct-plan-growth",
        "Quant Active Fund - Direct Plan": "quant-active-fund-direct-plan-growth",
        "Motilal Oswal Flexi Cap Fund - Direct Plan": "motilal-oswal-flexi-cap-fund-direct-plan-growth",
        "PGIM India Flexi Cap Fund - Direct Plan": "pgim-india-flexi-cap-fund-direct-plan-growth",
        
        # Mid Cap
        "HDFC Mid-Cap Opportunities Fund - Direct Plan": "hdfc-mid-cap-opportunities-fund-direct-plan-growth",
        "Axis Midcap Fund - Direct Plan": "axis-midcap-fund-direct-plan-growth",
        "Kotak Emerging Equity Fund - Direct Plan": "kotak-emerging-equity-fund-direct-plan-growth",
        "Nippon India Growth Fund - Direct Plan": "nippon-india-growth-fund-direct-plan-growth",
        "SBI Magnum Midcap Fund - Direct Plan": "sbi-magnum-midcap-fund-direct-plan-growth",
        
        # Small Cap
        "Nippon India Small Cap Fund - Direct Plan": "nippon-india-small-cap-fund-direct-plan-growth",
        "Axis Small Cap Fund - Direct Plan": "axis-small-cap-fund-direct-plan-growth",
        "SBI Small Cap Fund - Direct Plan": "sbi-small-cap-fund-direct-plan-growth",
        "Kotak Small Cap Fund - Direct Plan": "kotak-small-cap-fund-direct-plan-growth",
        "HDFC Small Cap Fund - Direct Plan": "hdfc-small-cap-fund-direct-plan-growth",
        
        # ELSS
        "Quant Tax Plan - Direct Plan": "quant-tax-plan-direct-plan-growth",
        "Axis Long Term Equity Fund - Direct Plan": "axis-long-term-equity-fund-direct-plan-growth",
        "HDFC Tax Saver Fund - Direct Plan": "hdfc-taxsaver-direct-plan-growth",
        "SBI Long Term Equity Fund - Direct Plan": "sbi-long-term-equity-fund-direct-plan-growth",
        "ICICI Prudential Long Term Equity Fund - Direct Plan": "icici-prudential-long-term-equity-fund-tax-saving-direct-plan-growth",
        
        # Index Funds
        "UTI Nifty 50 Index Fund - Direct Plan": "uti-nifty-index-fund-direct-plan-growth",
        "HDFC Index Fund - Nifty 50 Plan - Direct Plan": "hdfc-index-fund-nifty-50-plan-direct-plan",
        "Nippon India Index Fund - Nifty 50 Plan - Direct Plan": "nippon-india-index-fund-nifty-50-plan-direct-plan",
        
        # Focused Funds
        "HDFC Focused 30 Fund - Direct Plan": "hdfc-focused-30-fund-direct-plan-growth",
        "ICICI Prudential Focused Equity Fund - Direct Plan": "icici-prudential-focused-equity-fund-direct-plan-growth",
        "SBI Focused Equity Fund - Direct Plan": "sbi-focused-equity-fund-direct-plan-growth",
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def get_fund_details(self, slug: str) -> Optional[Dict]:
        """
        Get fund details including holdings from Groww API.
        
        Args:
            slug: Groww URL slug (e.g., "hdfc-top-100-fund-direct-plan-growth")
        """
        # Primary endpoint
        url = f"https://groww.in/v1/api/data/mf/web/v1/scheme/{slug}"
        
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract relevant fields
                return {
                    'schemeName': data.get('schemeName', ''),
                    'nav': data.get('nav', {}).get('nav', 0),
                    'aum': data.get('aum', 0),
                    'expenseRatio': data.get('expenseRatio', 0),
                    'category': data.get('category', ''),
                    'subCategory': data.get('subCategory', ''),
                    'riskRating': data.get('riskRating', ''),
                    'fundManager': data.get('fundManager', {}).get('name', '') if data.get('fundManager') else '',
                    'holdings': self._parse_holdings(data.get('holdings', [])),
                    'sectorAllocation': self._parse_sectors(data.get('sectorAllocation', [])),
                    'source': 'Groww',
                    'extractedAt': datetime.now().isoformat()
                }
            else:
                print(f"   ⚠️ Status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}")
            return None
    
    def _parse_holdings(self, holdings_data: list) -> List[Dict]:
        """Parse holdings from API response"""
        holdings = []
        
        for item in holdings_data[:10]:
            if isinstance(item, dict):
                holdings.append({
                    'company': item.get('companyName', item.get('name', '')),
                    'sector': item.get('sector', ''),
                    'percentage': item.get('percentage', item.get('corpusPer', 0))
                })
        
        return holdings
    
    def _parse_sectors(self, sector_data: list) -> List[Dict]:
        """Parse sector allocation from API response"""
        sectors = []
        
        for item in sector_data[:10]:
            if isinstance(item, dict):
                sectors.append({
                    'sector': item.get('sectorName', item.get('name', '')),
                    'percentage': item.get('percentage', item.get('corpusPer', 0))
                })
        
        return sectors
    
    def search_fund(self, query: str) -> Optional[str]:
        """Search for a fund and get its slug"""
        url = f"https://groww.in/v1/api/search/v1/entity"
        params = {
            'q': query,
            'entity_type': 'mutualfund',
            'size': 5
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                results = data.get('content', [])
                if results:
                    return results[0].get('searchId', '')
        except:
            pass
        return None
    
    def scrape_all_funds(self) -> Dict[str, Dict]:
        """Scrape holdings for all known funds"""
        print("=" * 60)
        print("GROWW API HOLDINGS EXTRACTOR")
        print("=" * 60)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print()
        
        results = {}
        total = len(self.FUND_SLUGS)
        success = 0
        
        print(f"📊 Fetching {total} funds from Groww API...\n")
        
        for i, (fund_name, slug) in enumerate(self.FUND_SLUGS.items(), 1):
            print(f"[{i}/{total}] {fund_name[:50]}...")
            
            data = self.get_fund_details(slug)
            
            if data:
                results[fund_name] = data
                h_count = len(data.get('holdings', []))
                s_count = len(data.get('sectorAllocation', []))
                print(f"   ✅ Holdings: {h_count}, Sectors: {s_count}")
                success += 1
            else:
                print(f"   ⚠️ No data extracted")
            
            # Rate limiting
            time.sleep(0.5)
        
        print()
        print("=" * 60)
        print(f"✅ Successfully extracted: {success}/{total} funds")
        print("=" * 60)
        
        return results
    
    def save_to_mongodb(self, results: Dict[str, Dict]) -> int:
        """Save extracted holdings to MongoDB"""
        print("\n💾 Saving to MongoDB...")
        
        client = MongoClient(MONGO_URI)
        db = client['mutualfunds']
        funds_col = db['funds']
        
        updated = 0
        not_found = []
        
        for fund_name, data in results.items():
            if not data.get('holdings'):
                continue
            
            # Find matching fund in database
            # Try exact match first
            fund = funds_col.find_one({
                'schemeName': {'$regex': f'^{re.escape(fund_name)}$', '$options': 'i'}
            })
            
            if not fund:
                # Try partial match without " - Direct Plan"
                base_name = fund_name.replace(' - Direct Plan', '')
                fund = funds_col.find_one({
                    'schemeName': {'$regex': base_name, '$options': 'i'}
                })
            
            if fund:
                update_data = {
                    'holdings': data.get('holdings', []),
                    'sectorAllocation': data.get('sectorAllocation', []),
                    'holdingsLastUpdated': datetime.now().isoformat(),
                    'holdingsSource': 'Groww API'
                }
                
                result = funds_col.update_one(
                    {'_id': fund['_id']},
                    {'$set': update_data}
                )
                
                if result.modified_count > 0:
                    updated += 1
                    print(f"   ✅ Updated: {fund['schemeName'][:50]}")
            else:
                not_found.append(fund_name)
        
        if not_found:
            print(f"\n⚠️ {len(not_found)} funds not found in database:")
            for name in not_found[:5]:
                print(f"   - {name}")
        
        print(f"\n✅ Updated {updated} funds in MongoDB")
        return updated


def main():
    """Main extraction function"""
    api = GrowwAPI()
    
    # Test with one fund first
    print("Testing Groww API...")
    print()
    
    # Test HDFC Top 100
    slug = "hdfc-top-100-fund-direct-plan-growth"
    print(f"Fetching: {slug}")
    
    result = api.get_fund_details(slug)
    
    if result:
        print("\n✅ Successfully extracted data:")
        print(f"   NAV: ₹{result.get('nav', 0):.2f}")
        print(f"   AUM: ₹{result.get('aum', 0):.0f} Cr")
        print(f"   Holdings: {len(result.get('holdings', []))}")
        print(f"   Sectors: {len(result.get('sectorAllocation', []))}")
        
        if result.get('holdings'):
            print("\n   Top Holdings:")
            for h in result['holdings'][:5]:
                print(f"     - {h['company']}: {h['percentage']:.2f}%")
        
        if result.get('sectorAllocation'):
            print("\n   Sector Allocation:")
            for s in result['sectorAllocation'][:5]:
                print(f"     - {s['sector']}: {s['percentage']:.2f}%")
        
        print("\n" + "=" * 60)
        print("✅ Groww API is working!")
        print("Run 'scrape_all_funds()' to extract all funds")
        print("=" * 60)
    else:
        print("\n⚠️ Could not extract data from Groww API")


if __name__ == "__main__":
    main()
