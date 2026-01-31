"""
AMC FACTSHEET AUTO-DISCOVERY SYSTEM
====================================
Automatically discovers and downloads the latest factsheet PDFs from AMC websites.
No hardcoded URLs - scrapes landing pages to find current month's factsheet.

This is how production platforms (Groww, ET Money, ValueResearch) operate.
"""

import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import os

# ============================================================
# AMC MASTER SOURCE PAGES (STABLE - These rarely change)
# ============================================================

AMC_SOURCES = {
    'HDFC': {
        'name': 'HDFC Mutual Fund',
        'landing_page': 'https://www.hdfcfund.com/investor-services/literature',
        'alt_pages': [
            'https://www.hdfcfund.com/investor-desk/fact-sheets'
        ],
        'patterns': [r'factsheet.*\.pdf', r'portfolio.*\.pdf', r'monthly.*disclosure.*\.pdf']
    },
    'ICICI': {
        'name': 'ICICI Prudential Mutual Fund',
        'landing_page': 'https://www.icicipruamc.com/downloads/factsheet',
        'alt_pages': [
            'https://www.icicipruamc.com/mutual-fund/downloads'
        ],
        'patterns': [r'factsheet.*\.pdf', r'scheme.*information.*\.pdf']
    },
    'SBI': {
        'name': 'SBI Mutual Fund',
        'landing_page': 'https://www.sbimf.com/downloads/factsheet',
        'alt_pages': [
            'https://www.sbimf.com/downloads'
        ],
        'patterns': [r'factsheet.*\.pdf', r'portfolio.*\.pdf']
    },
    'Axis': {
        'name': 'Axis Mutual Fund',
        'landing_page': 'https://www.axismf.com/downloads',
        'alt_pages': [
            'https://www.axismf.com/investor-corner/downloads'
        ],
        'patterns': [r'factsheet.*\.pdf', r'scheme.*\.pdf']
    },
    'Nippon': {
        'name': 'Nippon India Mutual Fund',
        'landing_page': 'https://mf.nipponindiaim.com/investor-service/downloads',
        'alt_pages': [
            'https://mf.nipponindiaim.com/FundsAndPerformance/Factsheets'
        ],
        'patterns': [r'factsheet.*\.pdf', r'portfolio.*\.pdf']
    },
    'Kotak': {
        'name': 'Kotak Mahindra Mutual Fund',
        'landing_page': 'https://www.kotakmf.com/downloads',
        'alt_pages': [
            'https://www.kotakmf.com/Information/Downloads'
        ],
        'patterns': [r'factsheet.*\.pdf', r'monthly.*\.pdf']
    },
    'Aditya_Birla': {
        'name': 'Aditya Birla Sun Life Mutual Fund',
        'landing_page': 'https://mutualfund.adityabirlacapital.com/downloads/factsheets',
        'alt_pages': [
            'https://mutualfund.adityabirlacapital.com/investor-services/downloads'
        ],
        'patterns': [r'factsheet.*\.pdf', r'portfolio.*\.pdf']
    },
    'UTI': {
        'name': 'UTI Mutual Fund',
        'landing_page': 'https://www.utimf.com/downloads/factsheets',
        'alt_pages': [
            'https://www.utimf.com/investor-services/downloads'
        ],
        'patterns': [r'factsheet.*\.pdf']
    },
    'DSP': {
        'name': 'DSP Mutual Fund',
        'landing_page': 'https://www.dspim.com/investor-centre/downloads',
        'alt_pages': [],
        'patterns': [r'factsheet.*\.pdf', r'portfolio.*\.pdf']
    },
    'Tata': {
        'name': 'Tata Mutual Fund',
        'landing_page': 'https://www.tatamutualfund.com/investor-services/downloads',
        'alt_pages': [],
        'patterns': [r'factsheet.*\.pdf']
    },
    'Motilal_Oswal': {
        'name': 'Motilal Oswal Mutual Fund',
        'landing_page': 'https://www.motilaloswalmf.com/downloads/factsheet',
        'alt_pages': [],
        'patterns': [r'factsheet.*\.pdf', r'portfolio.*\.pdf']
    },
    'PPFAS': {
        'name': 'PPFAS Mutual Fund',
        'landing_page': 'https://amc.ppfas.com/downloads/',
        'alt_pages': [],
        'patterns': [r'factsheet.*\.pdf', r'portfolio.*\.pdf']
    },
    'Quant': {
        'name': 'Quant Mutual Fund',
        'landing_page': 'https://quantmutual.com/downloads',
        'alt_pages': [],
        'patterns': [r'factsheet.*\.pdf']
    },
    'Mirae': {
        'name': 'Mirae Asset Mutual Fund',
        'landing_page': 'https://www.miraeassetmf.co.in/downloads/factsheet',
        'alt_pages': [],
        'patterns': [r'factsheet.*\.pdf', r'monthly.*\.pdf']
    },
    'Franklin': {
        'name': 'Franklin Templeton Mutual Fund',
        'landing_page': 'https://www.franklintempletonindia.com/investor/literature',
        'alt_pages': [],
        'patterns': [r'factsheet.*\.pdf']
    }
}

# Month patterns to identify current/latest factsheet
MONTH_PATTERNS = [
    r'january|jan', r'february|feb', r'march|mar', r'april|apr',
    r'may', r'june|jun', r'july|jul', r'august|aug',
    r'september|sep', r'october|oct', r'november|nov', r'december|dec',
    r'2026', r'2025', r'2024'
]


class FactsheetDiscovery:
    """Auto-discovers latest factsheet PDFs from AMC websites"""
    
    def __init__(self, download_dir='downloads/factsheets'):
        self.download_dir = download_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        os.makedirs(download_dir, exist_ok=True)
    
    def discover_factsheet_urls(self, amc_key: str) -> list:
        """
        Discover factsheet PDF URLs from AMC landing page
        Returns list of (url, confidence_score) tuples
        """
        if amc_key not in AMC_SOURCES:
            print(f"  ❌ Unknown AMC: {amc_key}")
            return []
        
        amc = AMC_SOURCES[amc_key]
        pdf_urls = []
        
        # Try landing page first, then alternatives
        pages_to_try = [amc['landing_page']] + amc.get('alt_pages', [])
        
        for page_url in pages_to_try:
            try:
                print(f"  🔍 Scanning: {page_url}")
                response = self.session.get(page_url, timeout=30)
                
                if response.status_code != 200:
                    print(f"    ⚠️ Status {response.status_code}")
                    continue
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    link_text = link.get_text(strip=True).lower()
                    
                    # Check if it's a PDF link
                    if '.pdf' in href.lower():
                        full_url = urljoin(page_url, href)
                        
                        # Calculate confidence score
                        score = self._calculate_confidence(href, link_text, amc['patterns'])
                        
                        if score > 0:
                            pdf_urls.append({
                                'url': full_url,
                                'score': score,
                                'text': link_text[:50]
                            })
                
                if pdf_urls:
                    break  # Found PDFs, no need to try alt pages
                    
            except Exception as e:
                print(f"    ❌ Error: {str(e)[:50]}")
                continue
        
        # Sort by confidence score
        pdf_urls.sort(key=lambda x: -x['score'])
        
        return pdf_urls
    
    def _calculate_confidence(self, href: str, link_text: str, patterns: list) -> int:
        """Calculate confidence that this is the correct factsheet"""
        score = 0
        combined = (href + ' ' + link_text).lower()
        
        # Pattern matches
        for pattern in patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                score += 30
        
        # Contains 'factsheet'
        if 'factsheet' in combined:
            score += 50
        
        # Contains 'portfolio'
        if 'portfolio' in combined:
            score += 20
        
        # Contains current year
        current_year = str(datetime.now().year)
        if current_year in combined:
            score += 40
        
        # Contains current or recent month
        current_month = datetime.now().strftime('%B').lower()
        prev_month = datetime(datetime.now().year, max(1, datetime.now().month - 1), 1).strftime('%B').lower()
        
        if current_month in combined or current_month[:3] in combined:
            score += 50
        elif prev_month in combined or prev_month[:3] in combined:
            score += 40
        
        # Contains 'monthly'
        if 'monthly' in combined:
            score += 20
        
        # Penalize old years
        for year in ['2020', '2021', '2022', '2023']:
            if year in combined:
                score -= 50
        
        return max(0, score)
    
    def download_factsheet(self, url: str, amc_key: str) -> str:
        """Download factsheet PDF and return local path"""
        try:
            print(f"  📥 Downloading: {url[:60]}...")
            response = self.session.get(url, timeout=60, stream=True)
            
            if response.status_code != 200:
                print(f"    ❌ Download failed: {response.status_code}")
                return None
            
            # Generate filename
            filename = f"{amc_key}_{datetime.now().strftime('%Y%m')}_factsheet.pdf"
            filepath = os.path.join(self.download_dir, filename)
            
            # Save file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(filepath) / (1024 * 1024)
            print(f"    ✅ Saved: {filename} ({file_size:.1f} MB)")
            
            return filepath
            
        except Exception as e:
            print(f"    ❌ Download error: {str(e)[:50]}")
            return None
    
    def discover_all_amcs(self) -> dict:
        """Discover factsheet URLs for all AMCs"""
        results = {}
        
        print('='*60)
        print('AUTO-DISCOVERING FACTSHEET URLs')
        print('='*60)
        
        for amc_key, amc_info in AMC_SOURCES.items():
            print(f"\n📊 {amc_info['name']}")
            
            urls = self.discover_factsheet_urls(amc_key)
            
            if urls:
                print(f"  ✅ Found {len(urls)} potential factsheet(s)")
                for i, u in enumerate(urls[:3]):
                    print(f"    {i+1}. Score: {u['score']} | {u['text'][:40]}")
                results[amc_key] = urls
            else:
                print(f"  ⚠️ No factsheets found")
                results[amc_key] = []
        
        return results


def main():
    """Test the discovery system"""
    discovery = FactsheetDiscovery()
    
    # Test with a few AMCs
    test_amcs = ['HDFC', 'ICICI', 'SBI', 'Axis', 'Nippon']
    
    print('='*60)
    print('FACTSHEET URL DISCOVERY TEST')
    print('='*60)
    print(f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print()
    
    for amc in test_amcs:
        print(f'\n📊 Testing: {AMC_SOURCES[amc]["name"]}')
        print(f'   Landing: {AMC_SOURCES[amc]["landing_page"]}')
        
        urls = discovery.discover_factsheet_urls(amc)
        
        if urls:
            print(f'   ✅ Found {len(urls)} factsheet URL(s)')
            top = urls[0]
            print(f'   Top: {top["url"][:60]}...')
            print(f'   Score: {top["score"]}')
        else:
            print(f'   ⚠️ No factsheets discovered')
    
    print('\n' + '='*60)
    print('Discovery test complete!')
    print('='*60)


if __name__ == '__main__':
    main()
