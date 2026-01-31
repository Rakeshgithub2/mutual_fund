"""
MORNINGSTAR INDIA HOLDINGS SCRAPER
===================================
Scrapes REAL holdings data from Morningstar India website using Selenium.
Morningstar has detailed portfolio data for all Indian mutual funds.

This is the production solution using browser automation.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from typing import List, Dict, Optional
from datetime import datetime
from pymongo import MongoClient


# MongoDB connection
MONGO_URI = "mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds"


class MorningstarScraper:
    """
    Scrapes real holdings data from Morningstar India using Selenium.
    """
    
    BASE_URL = "https://www.morningstar.in"
    
    # Fund codes from Morningstar India
    # Format: Fund Name -> Morningstar ID
    FUND_CODES = {
        "HDFC Top 100 Fund - Direct Plan": "F00000PR72",
        "ICICI Prudential Bluechip Fund - Direct Plan": "F00000PJRZ",
        "SBI Bluechip Fund - Direct Plan": "F00000N6R8",
        "Axis Bluechip Fund - Direct Plan": "F00000PJGQ",
        "Nippon India Large Cap Fund - Direct Plan": "F00000PJSV",
        "Kotak Bluechip Fund - Direct Plan": "F00000PJY2",
        "Mirae Asset Large Cap Fund - Direct Plan": "F00000SXSL",
        "UTI Large Cap Fund - Direct Plan": "F00000PQFX",
        
        "HDFC Flexi Cap Fund - Direct Plan": "F00000PJMQ",
        "Parag Parikh Flexi Cap Fund - Direct Plan": "F00000PWJL",
        "Quant Active Fund - Direct Plan": "F00000PJUO",
        "Motilal Oswal Flexi Cap Fund - Direct Plan": "F0GBR04OK9",
        
        "HDFC Mid-Cap Opportunities Fund - Direct Plan": "F00000PJMS",
        "Axis Midcap Fund - Direct Plan": "F00000PJGR",
        "Kotak Emerging Equity Fund - Direct Plan": "F00000PJY5",
        "Nippon India Growth Fund - Direct Plan": "F00000PJSW",
        
        "Nippon India Small Cap Fund - Direct Plan": "F00000PJT1",
        "Axis Small Cap Fund - Direct Plan": "F00000S9TM",
        "SBI Small Cap Fund - Direct Plan": "F00000N6RB",
        "Kotak Small Cap Fund - Direct Plan": "F0GBR04OKL",
    }
    
    def __init__(self, headless: bool = True):
        """Initialize the Selenium WebDriver"""
        self.headless = headless
        self.driver = None
        
    def _setup_driver(self):
        """Set up Chrome WebDriver"""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless=new")
        
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        # Use Chrome's user agent
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
    
    def _close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def get_fund_holdings(self, fund_code: str, fund_name: str) -> Optional[Dict]:
        """
        Get holdings for a fund from Morningstar India.
        
        Args:
            fund_code: Morningstar fund ID (e.g., "F00000PR72")
            fund_name: Fund name for logging
        """
        # Morningstar portfolio URL
        url = f"{self.BASE_URL}/mutualfunds/funds/portfolio/holdings?id={fund_code}"
        
        try:
            print(f"   Opening: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Try to find and close any cookie popups
            try:
                cookie_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accept')]")
                cookie_btn.click()
                time.sleep(1)
            except:
                pass
            
            # Extract holdings
            holdings = self._extract_holdings()
            
            # Extract sector allocation
            sectors = self._extract_sectors()
            
            # Extract NAV and other info
            nav = self._extract_nav()
            
            if holdings or sectors:
                return {
                    'holdings': holdings,
                    'sectorAllocation': sectors,
                    'nav': nav,
                    'source': 'Morningstar India',
                    'extractedAt': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:80]}")
            return None
    
    def _extract_holdings(self) -> List[Dict]:
        """Extract stock holdings from the page"""
        holdings = []
        
        try:
            # Wait for holdings table
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table, .holdings, .portfolio"))
            )
            
            # Try various selectors for holdings table
            selectors = [
                "table.holdings tbody tr",
                "table tbody tr",
                ".stock-holdings tr",
                ".portfolio-holdings tr",
            ]
            
            for selector in selectors:
                rows = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if rows:
                    for row in rows[:15]:  # Top 15 rows
                        try:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 2:
                                name = cells[0].text.strip()
                                
                                # Find percentage
                                for cell in cells[1:]:
                                    text = cell.text.strip()
                                    pct_match = re.search(r'(\d+\.?\d*)%?', text)
                                    if pct_match:
                                        pct = float(pct_match.group(1))
                                        if 0.5 < pct < 15 and name and len(name) > 3:
                                            holdings.append({
                                                'company': name[:60],
                                                'percentage': pct,
                                                'sector': ''
                                            })
                                            break
                        except:
                            continue
                    
                    if holdings:
                        break
            
            # Alternative: look for any text with percentages
            if not holdings:
                page_text = self.driver.page_source
                # Find patterns like "HDFC Bank 9.5%"
                matches = re.findall(r'([A-Za-z][A-Za-z\s\.&\-]+?)\s+(\d+\.?\d*)%', page_text)
                for name, pct_str in matches[:15]:
                    pct = float(pct_str)
                    if 0.5 < pct < 15 and len(name.strip()) > 3:
                        holdings.append({
                            'company': name.strip()[:60],
                            'percentage': pct,
                            'sector': ''
                        })
            
        except Exception as e:
            print(f"   ⚠️ Holdings extraction error: {str(e)[:50]}")
        
        return holdings[:10]
    
    def _extract_sectors(self) -> List[Dict]:
        """Extract sector allocation from the page"""
        sectors = []
        
        try:
            # Try to find sector allocation section
            page_text = self.driver.page_source
            
            # Common sector names in Indian mutual funds
            sector_patterns = [
                (r'Financial(?:\s+Services)?\s+(\d+\.?\d*)%', 'Financial Services'),
                (r'Technology\s+(\d+\.?\d*)%', 'Information Technology'),
                (r'Information\s+Technology\s+(\d+\.?\d*)%', 'Information Technology'),
                (r'Oil\s*[&]\s*Gas\s+(\d+\.?\d*)%', 'Oil & Gas'),
                (r'Energy\s+(\d+\.?\d*)%', 'Oil & Gas'),
                (r'Consumer\s+(?:Goods|Staples)\s+(\d+\.?\d*)%', 'Consumer Goods'),
                (r'Healthcare\s+(\d+\.?\d*)%', 'Healthcare'),
                (r'Capital\s+Goods\s+(\d+\.?\d*)%', 'Capital Goods'),
                (r'Auto(?:mobile)?\s+(\d+\.?\d*)%', 'Automobile'),
                (r'Telecom\s+(\d+\.?\d*)%', 'Telecommunication'),
            ]
            
            for pattern, sector_name in sector_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    pct = float(match.group(1))
                    if 1 < pct < 50:
                        sectors.append({
                            'sector': sector_name,
                            'percentage': pct
                        })
        
        except Exception as e:
            print(f"   ⚠️ Sector extraction error: {str(e)[:50]}")
        
        return sectors[:10]
    
    def _extract_nav(self) -> Optional[float]:
        """Extract current NAV"""
        try:
            page_text = self.driver.page_source
            nav_match = re.search(r'NAV[:\s]+₹?\s*(\d+\.?\d*)', page_text, re.IGNORECASE)
            if nav_match:
                return float(nav_match.group(1))
        except:
            pass
        return None
    
    def scrape_all_funds(self) -> Dict[str, Dict]:
        """Scrape holdings for all known funds"""
        print("=" * 60)
        print("MORNINGSTAR INDIA SCRAPER")
        print("=" * 60)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print()
        
        # Setup driver
        print("🚀 Starting Chrome browser...")
        self._setup_driver()
        
        results = {}
        total = len(self.FUND_CODES)
        
        print(f"📊 Scraping {total} funds from Morningstar India...\n")
        
        try:
            for i, (fund_name, fund_code) in enumerate(self.FUND_CODES.items(), 1):
                print(f"[{i}/{total}] {fund_name[:50]}...")
                
                data = self.get_fund_holdings(fund_code, fund_name)
                
                if data:
                    results[fund_name] = data
                    h_count = len(data.get('holdings', []))
                    s_count = len(data.get('sectorAllocation', []))
                    print(f"   ✅ Holdings: {h_count}, Sectors: {s_count}")
                else:
                    print(f"   ⚠️ No data extracted")
                
                # Rate limiting
                time.sleep(2)
        
        finally:
            self._close_driver()
        
        return results
    
    def save_to_mongodb(self, results: Dict[str, Dict]):
        """Save extracted holdings to MongoDB"""
        print("\n💾 Saving to MongoDB...")
        
        client = MongoClient(MONGO_URI)
        db = client['mutualfunds']
        funds_col = db['funds']
        
        updated = 0
        
        for fund_name, data in results.items():
            # Find matching fund in database
            fund = funds_col.find_one({
                'schemeName': {'$regex': fund_name.replace(' - Direct Plan', ''), '$options': 'i'}
            })
            
            if not fund:
                # Try with Direct Plan
                fund = funds_col.find_one({
                    'schemeName': {'$regex': fund_name, '$options': 'i'}
                })
            
            if fund:
                update_data = {
                    'holdings': data.get('holdings', []),
                    'sectorAllocation': data.get('sectorAllocation', []),
                    'holdingsLastUpdated': datetime.now().isoformat(),
                    'holdingsSource': 'Morningstar India'
                }
                
                result = funds_col.update_one(
                    {'_id': fund['_id']},
                    {'$set': update_data}
                )
                
                if result.modified_count > 0:
                    updated += 1
                    print(f"   ✅ Updated: {fund['schemeName'][:50]}")
            else:
                print(f"   ⚠️ Fund not found: {fund_name[:50]}")
        
        print(f"\n✅ Updated {updated} funds in MongoDB")
        return updated


def main():
    """Main scraping function"""
    scraper = MorningstarScraper(headless=True)
    
    # Test with one fund first
    print("Testing Morningstar scraper...")
    print()
    
    try:
        scraper._setup_driver()
        
        # Test HDFC Top 100
        test_code = "F00000PR72"
        result = scraper.get_fund_holdings(test_code, "HDFC Top 100 Fund")
        
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
            print("   The page structure may have changed.")
    
    finally:
        scraper._close_driver()


if __name__ == "__main__":
    main()
