"""
MONEYCONTROL HOLDINGS SCRAPER
==============================
Scrapes REAL holdings data from Moneycontrol website.
Moneycontrol has publicly accessible portfolio data.

This scraper uses the public Moneycontrol pages which don't require login.
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
from datetime import datetime
import time
import json


class MoneycontrolScraper:
    """
    Scrapes real holdings data from Moneycontrol.
    Uses multiple techniques to extract data.
    """
    
    BASE_URL = "https://www.moneycontrol.com"
    
    # Headers that mimic a real browser
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Fund URL slugs (from Moneycontrol)
    FUND_SLUGS = {
        "HDFC Top 100 Fund - Direct Plan": "hdfc-top-100-fund-direct-plan/MHD015",
        "ICICI Prudential Bluechip Fund - Direct Plan": "icici-prudential-bluechip-fund-direct-plan/MIC010",
        "SBI Bluechip Fund - Direct Plan": "sbi-bluechip-fund-direct-plan/MSB010",
        "Axis Bluechip Fund - Direct Plan": "axis-bluechip-fund-direct-plan/MAX010",
        "Nippon India Large Cap Fund - Direct Plan": "nippon-india-large-cap-fund-direct-plan/MRE010",
        "Kotak Bluechip Fund - Direct Plan": "kotak-bluechip-fund-direct-plan/MKO010",
        "Mirae Asset Large Cap Fund - Direct Plan": "mirae-asset-large-cap-fund-direct-plan/MMI010",
        "Parag Parikh Flexi Cap Fund - Direct Plan": "parag-parikh-flexi-cap-fund-direct-plan/MPP010",
        "Quant Active Fund - Direct Plan": "quant-active-fund-direct-plan/MQU010",
        "HDFC Flexi Cap Fund - Direct Plan": "hdfc-flexi-cap-fund-direct-plan/MHD020",
        "HDFC Mid-Cap Opportunities Fund - Direct Plan": "hdfc-mid-cap-opportunities-fund-direct-plan/MHD025",
        "Axis Midcap Fund - Direct Plan": "axis-midcap-fund-direct-plan/MAX015",
        "Nippon India Small Cap Fund - Direct Plan": "nippon-india-small-cap-fund-direct-plan/MRE015",
        "Axis Small Cap Fund - Direct Plan": "axis-small-cap-fund-direct-plan/MAX020",
        "SBI Small Cap Fund - Direct Plan": "sbi-small-cap-fund-direct-plan/MSB015",
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def get_fund_holdings(self, fund_slug: str) -> Optional[Dict]:
        """
        Get holdings for a fund from Moneycontrol.
        
        Args:
            fund_slug: The URL slug for the fund (e.g., "hdfc-top-100-fund-direct-plan/MHD015")
        """
        # Moneycontrol portfolio URL
        url = f"{self.BASE_URL}/mutual-funds/nav/{fund_slug}"
        
        try:
            print(f"   Fetching: {url}")
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                print(f"   ⚠️ Status {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract NAV
            nav = self._extract_nav(soup)
            
            # Try to find portfolio link and extract holdings
            holdings = self._extract_holdings_from_page(soup, response.text)
            sectors = self._extract_sectors_from_page(soup, response.text)
            
            return {
                'nav': nav,
                'holdings': holdings,
                'sectorAllocation': sectors,
                'source': 'Moneycontrol',
                'extractedAt': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return None
    
    def _extract_nav(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract current NAV"""
        # Look for NAV in various formats
        nav_patterns = [
            soup.find('span', class_=re.compile(r'nav|price', re.I)),
            soup.find('div', class_=re.compile(r'nav|price', re.I)),
            soup.find(string=re.compile(r'₹\s*\d+\.?\d*')),
        ]
        
        for elem in nav_patterns:
            if elem:
                text = elem.get_text() if hasattr(elem, 'get_text') else str(elem)
                match = re.search(r'(\d+\.?\d*)', text.replace(',', ''))
                if match:
                    value = float(match.group(1))
                    if 5 < value < 5000:  # Reasonable NAV range
                        return value
        return None
    
    def _extract_holdings_from_page(self, soup: BeautifulSoup, html: str) -> List[Dict]:
        """Extract holdings from the page"""
        holdings = []
        
        # Look for embedded JSON data
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'holdings' in script.string.lower():
                # Try to extract JSON
                try:
                    # Look for JSON-like structures
                    json_match = re.search(r'\{[^{}]*"holdings"[^{}]*\}', script.string)
                    if json_match:
                        data = json.loads(json_match.group())
                        if 'holdings' in data:
                            return data['holdings']
                except:
                    pass
        
        # Look for table-based holdings
        tables = soup.find_all('table')
        for table in tables:
            headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
            
            # Check if this is a holdings table
            if any('holding' in h or 'stock' in h or 'company' in h for h in headers):
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        name = cells[0].get_text(strip=True)
                        # Find percentage
                        for cell in cells[1:]:
                            text = cell.get_text(strip=True)
                            pct_match = re.search(r'(\d+\.?\d*)%?', text)
                            if pct_match:
                                pct = float(pct_match.group(1))
                                if 0.5 < pct < 15:
                                    holdings.append({
                                        'company': name[:60],
                                        'percentage': pct,
                                        'sector': ''
                                    })
                                    break
                
                if holdings:
                    break
        
        # Look for list-based holdings in divs
        if not holdings:
            holding_sections = soup.find_all('div', class_=re.compile(r'holding|portfolio|stock', re.I))
            for section in holding_sections:
                items = section.find_all(['li', 'div', 'tr'])
                for item in items[:15]:
                    text = item.get_text(strip=True)
                    pct_match = re.search(r'(\d+\.?\d*)%', text)
                    if pct_match:
                        # Extract company name (before percentage)
                        name = re.sub(r'\d+\.?\d*%.*', '', text).strip()
                        if name and len(name) > 3:
                            holdings.append({
                                'company': name[:60],
                                'percentage': float(pct_match.group(1)),
                                'sector': ''
                            })
        
        return holdings[:10]
    
    def _extract_sectors_from_page(self, soup: BeautifulSoup, html: str) -> List[Dict]:
        """Extract sector allocation from the page"""
        sectors = []
        
        # Look for sector allocation section
        sector_sections = soup.find_all(['div', 'section', 'table'], 
                                       class_=re.compile(r'sector|allocation|industry', re.I))
        
        for section in sector_sections:
            items = section.find_all(['tr', 'li', 'div'])
            for item in items[:12]:
                text = item.get_text(strip=True)
                pct_match = re.search(r'(\d+\.?\d*)%', text)
                if pct_match:
                    sector_name = re.sub(r'\d+\.?\d*%.*', '', text).strip()
                    if sector_name and len(sector_name) > 3 and len(sector_name) < 50:
                        pct = float(pct_match.group(1))
                        if 1 < pct < 50:
                            sectors.append({
                                'sector': sector_name,
                                'percentage': pct
                            })
        
        return sectors[:10]
    
    def scrape_all(self) -> Dict[str, Dict]:
        """Scrape holdings for all known funds"""
        results = {}
        total = len(self.FUND_SLUGS)
        
        print(f"📊 Scraping {total} funds from Moneycontrol...")
        print()
        
        for i, (fund_name, slug) in enumerate(self.FUND_SLUGS.items(), 1):
            print(f"[{i}/{total}] {fund_name[:50]}...")
            
            data = self.get_fund_holdings(slug)
            
            if data:
                results[fund_name] = data
                h_count = len(data.get('holdings', []))
                s_count = len(data.get('sectorAllocation', []))
                print(f"   ✅ NAV: {data.get('nav')}, Holdings: {h_count}, Sectors: {s_count}")
            else:
                print(f"   ⚠️ No data extracted")
            
            # Rate limiting
            time.sleep(2)
        
        return results


def main():
    print("=" * 60)
    print("MONEYCONTROL HOLDINGS SCRAPER")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    scraper = MoneycontrolScraper()
    
    # Test with HDFC Top 100
    print("Testing with HDFC Top 100 Fund...")
    
    result = scraper.get_fund_holdings("hdfc-top-100-fund-direct-plan/MHD015")
    
    if result:
        print("\n✅ Successfully extracted data:")
        print(f"   NAV: {result.get('nav')}")
        print(f"   Holdings: {len(result.get('holdings', []))}")
        print(f"   Sectors: {len(result.get('sectorAllocation', []))}")
        
        if result.get('holdings'):
            print("\n   Top Holdings:")
            for h in result['holdings'][:5]:
                print(f"     - {h['company']}: {h['percentage']}%")
    else:
        print("\n⚠️ Could not extract data")
        print("   Most financial websites require JavaScript rendering.")
        print("   Solution: Use Selenium or Playwright")


if __name__ == "__main__":
    main()
