"""
VALUE RESEARCH HOLDINGS SCRAPER
================================
Scrapes REAL holdings data from Value Research website.
Value Research has accurate, up-to-date portfolio data for all mutual funds.

URL Pattern: https://www.valueresearchonline.com/funds/{fund_code}/portfolio
Example: https://www.valueresearchonline.com/funds/16180/portfolio

This is the production solution for getting REAL holdings data.
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
from datetime import datetime
import time


class ValueResearchScraper:
    """
    Scrapes real holdings data from Value Research.
    This is the most reliable source for mutual fund portfolios.
    """
    
    BASE_URL = "https://www.valueresearchonline.com"
    
    # Headers to mimic browser
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    # Popular funds with their Value Research codes
    FUND_CODES = {
        # Large Cap Funds
        "HDFC Top 100 Fund - Direct Plan": 16180,
        "ICICI Prudential Bluechip Fund - Direct Plan": 16369,
        "SBI Bluechip Fund - Direct Plan": 15916,
        "Axis Bluechip Fund - Direct Plan": 16208,
        "Nippon India Large Cap Fund - Direct Plan": 16122,
        "Kotak Bluechip Fund - Direct Plan": 16320,
        "Mirae Asset Large Cap Fund - Direct Plan": 23421,
        "UTI Large Cap Fund - Direct Plan": 16181,
        
        # Flexi Cap Funds
        "HDFC Flexi Cap Fund - Direct Plan": 16177,
        "Parag Parikh Flexi Cap Fund - Direct Plan": 20252,
        "Quant Active Fund - Direct Plan": 16143,
        "Motilal Oswal Flexi Cap Fund - Direct Plan": 27498,
        "PGIM India Flexi Cap Fund - Direct Plan": 44461,
        
        # Mid Cap Funds
        "HDFC Mid-Cap Opportunities Fund - Direct Plan": 16178,
        "Axis Midcap Fund - Direct Plan": 16207,
        "Kotak Emerging Equity Fund - Direct Plan": 16318,
        "Nippon India Growth Fund - Direct Plan": 16123,
        "SBI Magnum Midcap Fund - Direct Plan": 15919,
        
        # Small Cap Funds  
        "Nippon India Small Cap Fund - Direct Plan": 16127,
        "Axis Small Cap Fund - Direct Plan": 26017,
        "SBI Small Cap Fund - Direct Plan": 15920,
        "Kotak Small Cap Fund - Direct Plan": 28118,
        "HDFC Small Cap Fund - Direct Plan": 16179,
        
        # ELSS Funds
        "Quant Tax Plan - Direct Plan": 16142,
        "Axis Long Term Equity Fund - Direct Plan": 16209,
        "HDFC Tax Saver Fund - Direct Plan": 16184,
        "SBI Long Term Equity Fund - Direct Plan": 15917,
        "ICICI Prudential Long Term Equity Fund - Direct Plan": 16372,
        
        # Index Funds
        "UTI Nifty 50 Index Fund - Direct Plan": 37502,
        "HDFC Index Fund - Nifty 50 Plan - Direct Plan": 40273,
        "Nippon India Index Fund - Nifty 50 Plan - Direct Plan": 16130,
        
        # Debt Funds
        "HDFC Corporate Bond Fund - Direct Plan": 16176,
        "ICICI Prudential Corporate Bond Fund - Direct Plan": 16367,
        "SBI Corporate Bond Fund - Direct Plan": 25447,
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def get_fund_portfolio(self, fund_code: int) -> Optional[Dict]:
        """
        Get portfolio holdings for a fund from Value Research.
        Returns dict with holdings and sector allocation.
        """
        url = f"{self.BASE_URL}/funds/{fund_code}/portfolio"
        
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                print(f"   ⚠️ Status {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract holdings
            holdings = self._extract_holdings(soup)
            
            # Extract sector allocation
            sectors = self._extract_sectors(soup)
            
            # Extract fund info
            fund_info = self._extract_fund_info(soup)
            
            if holdings or sectors:
                return {
                    'holdings': holdings,
                    'sectorAllocation': sectors,
                    'fundInfo': fund_info,
                    'source': 'Value Research',
                    'extractedAt': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}")
            return None
    
    def _extract_holdings(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract stock holdings from the page"""
        holdings = []
        
        # Try to find holdings table
        # Value Research uses various table structures
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    # Check if this looks like a holding row
                    first_cell = cells[0].get_text(strip=True)
                    
                    # Skip headers and totals
                    if any(x in first_cell.lower() for x in ['name', 'holding', 'total', 'net', '%']):
                        continue
                    
                    # Try to extract percentage from second cell
                    for cell in cells[1:]:
                        cell_text = cell.get_text(strip=True)
                        pct_match = re.search(r'(\d+\.?\d*)', cell_text)
                        if pct_match:
                            pct = float(pct_match.group(1))
                            if 0.5 < pct < 15:  # Reasonable holding percentage
                                holdings.append({
                                    'company': first_cell[:50],
                                    'percentage': pct,
                                    'sector': ''
                                })
                                break
        
        # Alternative: look for list-based holdings
        if not holdings:
            # Look for div-based holdings layout
            holding_divs = soup.find_all('div', class_=re.compile(r'holding|stock|company', re.I))
            for div in holding_divs[:10]:
                text = div.get_text(strip=True)
                # Extract company name and percentage
                pct_match = re.search(r'(\d+\.?\d*)\s*%', text)
                if pct_match:
                    company = re.sub(r'\d+\.?\d*\s*%', '', text).strip()
                    if company and len(company) > 3:
                        holdings.append({
                            'company': company[:50],
                            'percentage': float(pct_match.group(1)),
                            'sector': ''
                        })
        
        return holdings[:10]
    
    def _extract_sectors(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract sector allocation from the page"""
        sectors = []
        
        # Look for sector-related content
        sector_keywords = ['sector', 'industry', 'allocation']
        
        for keyword in sector_keywords:
            sections = soup.find_all(['div', 'section', 'table'], 
                                    class_=re.compile(keyword, re.I))
            for section in sections:
                # Extract sector-percentage pairs
                text = section.get_text()
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    pct_match = re.search(r'(\d+\.?\d*)\s*%', line)
                    if pct_match:
                        sector_name = re.sub(r'\d+\.?\d*\s*%', '', line).strip()
                        if sector_name and len(sector_name) > 3 and len(sector_name) < 40:
                            sectors.append({
                                'sector': sector_name,
                                'percentage': float(pct_match.group(1))
                            })
        
        return sectors[:10]
    
    def _extract_fund_info(self, soup: BeautifulSoup) -> Dict:
        """Extract additional fund information"""
        info = {}
        
        # Try to extract NAV
        nav_match = soup.find(string=re.compile(r'NAV', re.I))
        if nav_match:
            nav_text = nav_match.find_next().get_text() if nav_match.find_next() else ""
            nav_num = re.search(r'(\d+\.?\d*)', nav_text)
            if nav_num:
                info['nav'] = float(nav_num.group(1))
        
        # Try to extract AUM
        aum_match = soup.find(string=re.compile(r'AUM|Assets', re.I))
        if aum_match:
            aum_text = aum_match.find_next().get_text() if aum_match.find_next() else ""
            aum_num = re.search(r'(\d+[\d,]*\.?\d*)', aum_text)
            if aum_num:
                info['aum'] = float(aum_num.group(1).replace(',', ''))
        
        return info
    
    def scrape_all_funds(self) -> Dict[str, Dict]:
        """Scrape holdings for all known funds"""
        results = {}
        total = len(self.FUND_CODES)
        
        print(f"📊 Scraping {total} funds from Value Research...")
        print()
        
        for i, (fund_name, fund_code) in enumerate(self.FUND_CODES.items(), 1):
            print(f"[{i}/{total}] {fund_name[:50]}...")
            
            data = self.get_fund_portfolio(fund_code)
            
            if data:
                results[fund_name] = data
                h_count = len(data.get('holdings', []))
                s_count = len(data.get('sectorAllocation', []))
                print(f"   ✅ Holdings: {h_count}, Sectors: {s_count}")
            else:
                print(f"   ⚠️ No data extracted")
            
            # Rate limiting - be respectful
            time.sleep(1)
        
        return results


def main():
    print("=" * 60)
    print("VALUE RESEARCH HOLDINGS SCRAPER")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    scraper = ValueResearchScraper()
    
    # Test with one fund first
    print("Testing with HDFC Top 100 Fund...")
    test_code = 16180  # HDFC Top 100
    
    result = scraper.get_fund_portfolio(test_code)
    
    if result:
        print("\n✅ Successfully extracted data:")
        print(f"   Holdings: {len(result.get('holdings', []))}")
        print(f"   Sectors: {len(result.get('sectorAllocation', []))}")
        
        if result.get('holdings'):
            print("\n   Top Holdings:")
            for h in result['holdings'][:5]:
                print(f"     - {h['company']}: {h['percentage']}%")
    else:
        print("\n⚠️ Could not extract data from Value Research")
        print("   The website may require JavaScript rendering.")
        print("   Try using Selenium or Playwright for dynamic content.")


if __name__ == "__main__":
    main()
