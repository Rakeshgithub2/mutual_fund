"""
FACTSHEET PDF PARSER
=====================
Parses real AMC factsheet PDFs to extract holdings and sector allocation.
Uses pdfplumber to extract text and regex to parse data.
"""

import pdfplumber
import re
import os
from datetime import datetime
from pymongo import MongoClient
from typing import List, Dict, Optional


# MongoDB connection
MONGO_URI = "mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds"


class FactsheetParser:
    """Parse AMC factsheet PDFs to extract holdings data"""
    
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client['mutualfunds']
        self.funds_col = self.db['funds']
    
    def parse_pdf(self, pdf_path: str) -> Dict:
        """
        Parse a factsheet PDF and extract all fund data.
        Returns dict with fund name as key and holdings/sectors as value.
        """
        print(f"\n📄 Parsing: {os.path.basename(pdf_path)}")
        print("=" * 50)
        
        extracted_funds = {}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                
                # Extract text from all pages
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    full_text += text + "\n\n"
                
                print(f"   Pages: {len(pdf.pages)}")
                print(f"   Text length: {len(full_text):,} chars")
                
                # Detect fund type from filename
                filename = os.path.basename(pdf_path).lower()
                
                if 'kotak' in filename:
                    extracted_funds = self._parse_kotak_factsheet(full_text)
                elif 'hdfc' in filename:
                    extracted_funds = self._parse_hdfc_factsheet(full_text)
                elif 'icici' in filename:
                    extracted_funds = self._parse_icici_factsheet(full_text)
                elif 'axis' in filename:
                    extracted_funds = self._parse_axis_factsheet(full_text)
                elif 'mirae' in filename:
                    extracted_funds = self._parse_mirae_factsheet(full_text)
                elif 'dsp' in filename:
                    extracted_funds = self._parse_dsp_factsheet(full_text)
                else:
                    extracted_funds = self._parse_generic_factsheet(full_text)
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        return extracted_funds
    
    def _parse_kotak_factsheet(self, text: str) -> Dict:
        """Parse Kotak Mutual Fund factsheet"""
        funds = {}
        
        # Find fund sections - Kotak format
        # Look for fund names followed by holdings
        fund_patterns = [
            r'(Kotak\s+[\w\s]+Fund)',
            r'(Kotak\s+[\w\s]+Scheme)',
        ]
        
        # Extract holdings patterns
        # Kotak format: Company Name | Sector | % of Net Assets
        holdings_pattern = re.compile(
            r'^([A-Za-z][A-Za-z\s\.\&\-\(\)]+?)\s+(\d+\.?\d*)\s*%?\s*$',
            re.MULTILINE
        )
        
        # Find all holdings
        lines = text.split('\n')
        current_fund = "Kotak Fund"
        holdings = []
        sectors = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check if this is a fund name
            for pattern in fund_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    # Save previous fund
                    if holdings:
                        funds[current_fund] = {
                            'holdings': holdings[:10],
                            'sectorAllocation': sectors[:10]
                        }
                    current_fund = match.group(1).strip()
                    holdings = []
                    sectors = []
                    break
            
            # Check for holdings (company name + percentage)
            match = holdings_pattern.match(line)
            if match:
                name = match.group(1).strip()
                pct = float(match.group(2))
                
                # Filter valid holdings
                if len(name) > 3 and 0.5 < pct < 15:
                    # Check if it's a sector or company
                    if self._is_sector(name):
                        sectors.append({
                            'sector': self._normalize_sector(name),
                            'percentage': pct
                        })
                    else:
                        holdings.append({
                            'company': name,
                            'sector': '',
                            'percentage': pct
                        })
        
        # Save last fund
        if holdings:
            funds[current_fund] = {
                'holdings': holdings[:10],
                'sectorAllocation': sectors[:10]
            }
        
        # Also try table-based extraction
        self._extract_from_tables(text, funds)
        
        return funds
    
    def _parse_hdfc_factsheet(self, text: str) -> Dict:
        """Parse HDFC Mutual Fund factsheet"""
        funds = {}
        
        # HDFC Large Cap Fund specific parsing
        holdings = []
        sectors = []
        
        # Look for "Top 10 Holdings" section
        top10_match = re.search(r'Top\s*(?:10|Ten)?\s*Holdings?(.*?)(?:Sector|Asset|$)', text, re.IGNORECASE | re.DOTALL)
        
        if top10_match:
            holdings_text = top10_match.group(1)
            
            # Extract company names and percentages
            # Pattern: Company Name followed by percentage
            pattern = re.compile(r'([A-Za-z][A-Za-z\s\.\&\-]+?)\s+(\d+\.?\d*)\s*%', re.MULTILINE)
            matches = pattern.findall(holdings_text)
            
            for name, pct in matches[:10]:
                name = name.strip()
                if len(name) > 3:
                    holdings.append({
                        'company': name,
                        'sector': self._detect_sector(name),
                        'percentage': float(pct)
                    })
        
        # Look for "Sector Allocation" section
        sector_match = re.search(r'Sector\s*Allocation(.*?)(?:Asset|Portfolio|$)', text, re.IGNORECASE | re.DOTALL)
        
        if sector_match:
            sector_text = sector_match.group(1)
            
            pattern = re.compile(r'([A-Za-z][A-Za-z\s\&]+?)\s+(\d+\.?\d*)\s*%', re.MULTILINE)
            matches = pattern.findall(sector_text)
            
            for name, pct in matches[:10]:
                name = name.strip()
                if len(name) > 3 and self._is_sector(name):
                    sectors.append({
                        'sector': self._normalize_sector(name),
                        'percentage': float(pct)
                    })
        
        if holdings:
            funds['HDFC Large Cap Fund'] = {
                'holdings': holdings,
                'sectorAllocation': sectors
            }
        
        return funds
    
    def _parse_icici_factsheet(self, text: str) -> Dict:
        """Parse ICICI Prudential factsheet"""
        return self._parse_generic_factsheet(text, 'ICICI Prudential')
    
    def _parse_axis_factsheet(self, text: str) -> Dict:
        """Parse Axis Mutual Fund factsheet"""
        return self._parse_generic_factsheet(text, 'Axis')
    
    def _parse_mirae_factsheet(self, text: str) -> Dict:
        """Parse Mirae Asset factsheet"""
        return self._parse_generic_factsheet(text, 'Mirae Asset')
    
    def _parse_dsp_factsheet(self, text: str) -> Dict:
        """Parse DSP Mutual Fund factsheet"""
        return self._parse_generic_factsheet(text, 'DSP')
    
    def _parse_generic_factsheet(self, text: str, amc_name: str = "") -> Dict:
        """Generic factsheet parser for any AMC"""
        funds = {}
        holdings = []
        sectors = []
        
        lines = text.split('\n')
        
        # Common patterns for holdings
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and headers
            if not line or len(line) < 5:
                continue
            
            # Look for "Company Name ... XX.XX%" pattern
            match = re.search(r'^([A-Za-z][A-Za-z\s\.\&\-\(\)]+?)\s+(\d+\.?\d*)\s*%?\s*$', line)
            if match:
                name = match.group(1).strip()
                pct = float(match.group(2))
                
                if len(name) > 3 and 0.5 < pct < 20:
                    if self._is_sector(name):
                        sectors.append({
                            'sector': self._normalize_sector(name),
                            'percentage': pct
                        })
                    elif self._is_company(name):
                        holdings.append({
                            'company': name,
                            'sector': self._detect_sector(name),
                            'percentage': pct
                        })
        
        if holdings:
            fund_name = f"{amc_name} Fund" if amc_name else "Unknown Fund"
            funds[fund_name] = {
                'holdings': holdings[:10],
                'sectorAllocation': sectors[:10]
            }
        
        return funds
    
    def _extract_from_tables(self, text: str, funds: Dict):
        """Try to extract data from table-like structures"""
        # Look for table rows with | separators
        table_pattern = re.compile(r'([A-Za-z\s\.]+)\s*\|\s*(\d+\.?\d*)\s*%?')
        matches = table_pattern.findall(text)
        
        if matches and not funds:
            holdings = []
            for name, pct in matches[:15]:
                name = name.strip()
                if len(name) > 3 and self._is_company(name):
                    holdings.append({
                        'company': name,
                        'sector': self._detect_sector(name),
                        'percentage': float(pct)
                    })
            
            if holdings:
                funds['Extracted Fund'] = {
                    'holdings': holdings[:10],
                    'sectorAllocation': []
                }
    
    def _is_sector(self, name: str) -> bool:
        """Check if name is a sector"""
        sector_keywords = [
            'financial', 'banking', 'technology', 'it', 'software',
            'pharma', 'healthcare', 'consumer', 'fmcg', 'auto',
            'oil', 'gas', 'energy', 'power', 'telecom', 'metal',
            'capital goods', 'industrial', 'cement', 'real estate',
            'infrastructure', 'services', 'media', 'chemical'
        ]
        name_lower = name.lower()
        return any(kw in name_lower for kw in sector_keywords) and len(name) < 30
    
    def _is_company(self, name: str) -> bool:
        """Check if name is likely a company"""
        company_keywords = ['ltd', 'limited', 'inc', 'corp', 'bank', 'india']
        exclude_keywords = ['total', 'net', 'assets', 'portfolio', 'scheme', 'fund', 'nav']
        
        name_lower = name.lower()
        
        # Exclude if contains exclude keywords
        if any(kw in name_lower for kw in exclude_keywords):
            return False
        
        # Include if contains company keywords or is a known company
        if any(kw in name_lower for kw in company_keywords):
            return True
        
        # Include if it's a proper name (starts with capital, reasonable length)
        return len(name) > 5 and len(name) < 50
    
    def _detect_sector(self, company: str) -> str:
        """Detect sector from company name"""
        company_lower = company.lower()
        
        sector_map = {
            'Financial Services': ['bank', 'hdfc', 'icici', 'kotak', 'axis', 'sbi', 'finance', 'bajaj fin'],
            'Information Technology': ['infosys', 'tcs', 'wipro', 'tech', 'hcl', 'software', 'persistent'],
            'Oil & Gas': ['reliance', 'oil', 'ongc', 'petroleum', 'bpcl', 'ioc', 'gail'],
            'Healthcare': ['pharma', 'sun', 'cipla', 'dr reddy', 'lupin', 'divis', 'biocon'],
            'Telecommunication': ['bharti', 'airtel', 'jio', 'vodafone', 'idea'],
            'Automobile': ['tata motor', 'maruti', 'bajaj auto', 'hero', 'mahindra', 'eicher'],
            'Consumer Goods': ['itc', 'hindustan', 'nestle', 'dabur', 'britannia', 'godrej', 'titan'],
            'Capital Goods': ['larsen', 'l&t', 'abb', 'siemens', 'bhel', 'havells'],
            'Metals': ['tata steel', 'hindalco', 'vedanta', 'jsw', 'jindal'],
            'Power': ['ntpc', 'power grid', 'adani power', 'tata power'],
        }
        
        for sector, keywords in sector_map.items():
            if any(kw in company_lower for kw in keywords):
                return sector
        
        return 'Other'
    
    def _normalize_sector(self, sector: str) -> str:
        """Normalize sector name"""
        sector_map = {
            'financial': 'Financial Services',
            'banking': 'Financial Services',
            'it': 'Information Technology',
            'technology': 'Information Technology',
            'software': 'Information Technology',
            'pharma': 'Healthcare',
            'healthcare': 'Healthcare',
            'oil': 'Oil & Gas',
            'gas': 'Oil & Gas',
            'energy': 'Oil & Gas',
            'auto': 'Automobile',
            'consumer': 'Consumer Goods',
            'fmcg': 'Consumer Goods',
            'telecom': 'Telecommunication',
            'metal': 'Metals & Mining',
            'capital': 'Capital Goods',
            'power': 'Power',
            'real': 'Real Estate',
        }
        
        sector_lower = sector.lower()
        for key, value in sector_map.items():
            if key in sector_lower:
                return value
        
        return sector
    
    def update_database(self, extracted_funds: Dict, amc_name: str) -> int:
        """Update database with extracted holdings"""
        updated = 0
        
        for fund_name, data in extracted_funds.items():
            if not data.get('holdings'):
                continue
            
            # Find matching funds in database
            # Build regex pattern from fund name
            base_name = fund_name.replace(' Fund', '').replace(' Scheme', '')
            
            matching_funds = list(self.funds_col.find({
                '$or': [
                    {'schemeName': {'$regex': base_name, '$options': 'i'}},
                    {'schemeName': {'$regex': amc_name, '$options': 'i'}}
                ]
            }))
            
            print(f"\n   📌 {fund_name}: Found {len(matching_funds)} matching funds")
            
            for mf in matching_funds[:20]:  # Limit to 20 updates per fund
                result = self.funds_col.update_one(
                    {'_id': mf['_id']},
                    {
                        '$set': {
                            'holdings': data['holdings'],
                            'sectorAllocation': data.get('sectorAllocation', []),
                            'holdingsLastUpdated': datetime.now().isoformat(),
                            'holdingsSource': f'Factsheet PDF ({amc_name})'
                        }
                    }
                )
                if result.modified_count > 0:
                    updated += 1
        
        return updated


def main():
    """Main function to parse all factsheet PDFs"""
    print("=" * 60)
    print("FACTSHEET PDF PARSER")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    parser = FactsheetParser()
    
    # PDF files to parse
    pdf_files = [
        (r"c:\MF root folder\factsheet\KotakMFFactsheetDecember2025.pdf", "Kotak"),
        (r"c:\MF root folder\factsheet\Fund Facts - HDFC Large Cap Fund_December 25.pdf", "HDFC"),
    ]
    
    total_updated = 0
    
    for pdf_path, amc_name in pdf_files:
        if os.path.exists(pdf_path):
            extracted = parser.parse_pdf(pdf_path)
            
            if extracted:
                print(f"\n   📊 Extracted {len(extracted)} funds")
                for fund_name, data in extracted.items():
                    h = len(data.get('holdings', []))
                    s = len(data.get('sectorAllocation', []))
                    print(f"      - {fund_name}: {h} holdings, {s} sectors")
                
                # Update database
                print(f"\n   💾 Updating database...")
                updated = parser.update_database(extracted, amc_name)
                total_updated += updated
                print(f"   ✅ Updated {updated} funds")
            else:
                print(f"   ⚠️ No data extracted")
        else:
            print(f"   ❌ File not found: {pdf_path}")
    
    print()
    print("=" * 60)
    print(f"✅ TOTAL UPDATED: {total_updated} funds")
    print("=" * 60)


if __name__ == "__main__":
    main()
