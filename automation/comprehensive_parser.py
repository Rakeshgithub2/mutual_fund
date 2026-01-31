"""
COMPREHENSIVE FACTSHEET PARSER
===============================
Parses ALL factsheet PDFs from the factsheet folder and updates MongoDB.

Supported AMCs:
- HDFC, ICICI, SBI, Axis, Kotak, Nippon, Aditya Birla, DSP, Mirae
- Canara Robeco, Bajaj Finserv, Angel One, Bandhan, etc.

This script:
1. Parses each PDF to extract fund data
2. Matches funds in the database
3. Updates holdings, sectors, NAV, AUM
4. Removes any mock/sample data
"""

import pdfplumber
import re
import os
from datetime import datetime
from pymongo import MongoClient
from typing import List, Dict, Optional, Tuple
import traceback


# MongoDB connection
MONGO_URI = "mongodb+srv://rakeshd01042024_db_user:Rakesh1234@mutualfunds.l7zeno9.mongodb.net/mutualfunds"

# Factsheet folder path
FACTSHEET_FOLDER = r"c:\MF root folder\factsheet"


class FactsheetParser:
    """Universal factsheet PDF parser for Indian mutual funds"""
    
    # Common patterns for data extraction
    PATTERNS = {
        'nav': [
            r'NAV[:\s]+(?:Rs\.?|₹)?\s*(\d+\.?\d*)',
            r'Net\s*Asset\s*Value[:\s]+(\d+\.?\d*)',
            r'NAV\s*\(₹\)[:\s]*(\d+\.?\d*)',
        ],
        'aum': [
            r'AUM[:\s]+(?:Rs\.?|₹)?\s*([\d,]+\.?\d*)\s*(?:Cr|Crore)',
            r'Assets\s*Under\s*Management[:\s]+([\d,]+\.?\d*)',
            r'Fund\s*Size[:\s]+([\d,]+\.?\d*)',
            r'AUM\s*\(₹\s*Cr\.\)[:\s]*([\d,]+\.?\d*)',
        ],
        'expense_ratio': [
            r'Expense\s*Ratio[:\s]+(\d+\.?\d*)\s*%?',
            r'TER[:\s]+(\d+\.?\d*)\s*%?',
            r'Total\s*Expense\s*Ratio[:\s]+(\d+\.?\d*)',
        ],
        'benchmark': [
            r'Benchmark[:\s]+([A-Za-z\s\d\-]+?)(?:\n|$)',
            r'Benchmark\s*Index[:\s]+([A-Za-z\s\d\-]+)',
        ],
        'fund_manager': [
            r'Fund\s*Manager[s]?\s*:?\s*([A-Za-z\s\.]+?)(?:\n|,|$)',
            r'Managed\s*[Bb]y[:\s]+([A-Za-z\s\.]+)',
        ],
    }
    
    # Known sectors in Indian markets
    SECTORS = [
        'Financial Services', 'Banks', 'Banking', 'NBFC',
        'Information Technology', 'IT', 'Technology', 'Software',
        'Oil & Gas', 'Energy', 'Petroleum',
        'Healthcare', 'Pharmaceuticals', 'Pharma',
        'Consumer Goods', 'FMCG', 'Consumer Staples',
        'Automobile', 'Auto', 'Automotive',
        'Capital Goods', 'Industrial', 'Engineering',
        'Telecommunication', 'Telecom', 'Communication',
        'Metals & Mining', 'Metals', 'Steel',
        'Power', 'Utilities', 'Electricity',
        'Cement', 'Construction Materials',
        'Real Estate', 'Realty',
        'Chemicals', 'Specialty Chemicals',
        'Textiles', 'Apparel',
        'Media', 'Entertainment',
        'Services', 'Others'
    ]
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text = ""
        self.pages = []
        self.amc_name = self._detect_amc()
    
    def _detect_amc(self) -> str:
        """Detect AMC from filename"""
        filename = os.path.basename(self.pdf_path).lower()
        
        amc_patterns = {
            'hdfc': 'HDFC Mutual Fund',
            'icici': 'ICICI Prudential Mutual Fund',
            'sbi': 'SBI Mutual Fund',
            'axis': 'Axis Mutual Fund',
            'kotak': 'Kotak Mahindra Mutual Fund',
            'nippon': 'Nippon India Mutual Fund',
            'aditya': 'Aditya Birla Sun Life Mutual Fund',
            'absl': 'Aditya Birla Sun Life Mutual Fund',
            'dsp': 'DSP Mutual Fund',
            'mirae': 'Mirae Asset Mutual Fund',
            'canara': 'Canara Robeco Mutual Fund',
            'bajaj': 'Bajaj Finserv Mutual Fund',
            'angel': 'Angel One Mutual Fund',
            'bandhan': 'Bandhan Mutual Fund',
            'uti': 'UTI Mutual Fund',
            'tata': 'Tata Mutual Fund',
            'franklin': 'Franklin Templeton Mutual Fund',
            'motilal': 'Motilal Oswal Mutual Fund',
            'ppfas': 'PPFAS Mutual Fund',
            'quant': 'Quant Mutual Fund',
        }
        
        for key, name in amc_patterns.items():
            if key in filename:
                return name
        
        return 'Unknown AMC'
    
    def parse(self) -> List[Dict]:
        """Parse the PDF and extract all fund data"""
        print(f"📄 Parsing: {os.path.basename(self.pdf_path)}")
        print(f"   AMC: {self.amc_name}")
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                self.pages = []
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    self.pages.append(text)
                    self.text += text + "\n\n"
            
            # Extract fund sections
            funds = self._extract_funds()
            print(f"   Found {len(funds)} funds")
            
            return funds
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:60]}")
            traceback.print_exc()
            return []
    
    def _extract_funds(self) -> List[Dict]:
        """Extract individual fund data from the PDF"""
        funds = []
        
        # Split text into fund sections
        # Common patterns that indicate a new fund section
        fund_patterns = [
            r'(?:^|\n)([A-Z][A-Za-z\s]+(?:Fund|Scheme)(?:\s*-\s*(?:Direct|Regular))?(?:\s*(?:Plan|Growth|IDCW))?)',
            r'Scheme\s*Name[:\s]+([A-Za-z\s\-]+(?:Fund|Scheme))',
        ]
        
        lines = self.text.split('\n')
        current_fund = None
        current_section = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line starts a new fund
            is_fund_header = False
            for pattern in fund_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    fund_name = match.group(1).strip()
                    # Validate it's a real fund name
                    if self._is_valid_fund_name(fund_name):
                        # Save previous fund
                        if current_fund and current_section:
                            fund_data = self._parse_fund_section(current_fund, '\n'.join(current_section))
                            if fund_data:
                                funds.append(fund_data)
                        
                        current_fund = fund_name
                        current_section = [line]
                        is_fund_header = True
                        break
            
            if not is_fund_header and current_fund:
                current_section.append(line)
        
        # Save last fund
        if current_fund and current_section:
            fund_data = self._parse_fund_section(current_fund, '\n'.join(current_section))
            if fund_data:
                funds.append(fund_data)
        
        # If no funds found with pattern matching, try table extraction
        if not funds:
            funds = self._extract_from_tables()
        
        return funds
    
    def _is_valid_fund_name(self, name: str) -> bool:
        """Check if a string is a valid fund name"""
        if len(name) < 10 or len(name) > 100:
            return False
        
        # Must contain 'Fund' or 'Scheme'
        if not re.search(r'Fund|Scheme', name, re.IGNORECASE):
            return False
        
        # Should not be just a header
        invalid = ['Investment', 'Objective', 'Strategy', 'Performance', 'Portfolio']
        for inv in invalid:
            if name.strip() == inv:
                return False
        
        return True
    
    def _parse_fund_section(self, fund_name: str, section_text: str) -> Optional[Dict]:
        """Parse a single fund's section"""
        # Extract holdings
        holdings = self._extract_holdings(section_text)
        
        # Extract sector allocation
        sectors = self._extract_sectors(section_text)
        
        # Extract other details
        nav = self._extract_value(section_text, self.PATTERNS['nav'])
        aum = self._extract_value(section_text, self.PATTERNS['aum'])
        expense = self._extract_value(section_text, self.PATTERNS['expense_ratio'])
        manager = self._extract_text(section_text, self.PATTERNS['fund_manager'])
        benchmark = self._extract_text(section_text, self.PATTERNS['benchmark'])
        
        # Detect category
        category = self._detect_category(fund_name)
        
        return {
            'schemeName': fund_name,
            'fundHouse': self.amc_name,
            'category': category['category'],
            'subCategory': category['sub_category'],
            'holdings': holdings,
            'sectorAllocation': sectors,
            'nav': float(nav) if nav else None,
            'aum': float(str(aum).replace(',', '')) if aum else None,
            'expenseRatio': float(expense) if expense else None,
            'fundManager': manager,
            'benchmark': benchmark,
            'dataSource': 'AMC Factsheet',
            'lastUpdated': datetime.now().isoformat()
        }
    
    def _extract_holdings(self, text: str) -> List[Dict]:
        """Extract stock holdings from text"""
        holdings = []
        
        # Pattern: Company name followed by percentage
        patterns = [
            r'([A-Z][A-Za-z\s\.\&\-\(\)]+?)\s+(\d+\.?\d*)\s*%',
            r'([A-Z][A-Za-z\s\.\&]+Ltd\.?)\s+(\d+\.?\d*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                company = match[0].strip()
                pct = float(match[1])
                
                # Filter valid holdings
                if self._is_valid_holding(company, pct):
                    # Detect sector
                    sector = self._detect_sector_for_company(company)
                    
                    holdings.append({
                        'company': company,
                        'sector': sector,
                        'percentage': pct
                    })
        
        # Remove duplicates and sort by percentage
        seen = set()
        unique_holdings = []
        for h in sorted(holdings, key=lambda x: x['percentage'], reverse=True):
            if h['company'] not in seen:
                seen.add(h['company'])
                unique_holdings.append(h)
        
        return unique_holdings[:10]  # Top 10
    
    def _is_valid_holding(self, company: str, percentage: float) -> bool:
        """Validate a holding entry"""
        if len(company) < 4 or len(company) > 60:
            return False
        if percentage < 0.5 or percentage > 20:
            return False
        
        # Skip common non-company text
        invalid = ['Total', 'Cash', 'Net', 'Gross', 'Others', 'Other', 'Equity', 'Debt']
        for inv in invalid:
            if company.strip().lower() == inv.lower():
                return False
        
        return True
    
    def _extract_sectors(self, text: str) -> List[Dict]:
        """Extract sector allocation from text"""
        sectors = []
        
        for sector in self.SECTORS:
            # Look for sector with percentage
            pattern = rf'{re.escape(sector)}\s*[:\s]+(\d+\.?\d*)\s*%?'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                pct = float(match.group(1))
                if 1 < pct < 60:
                    sectors.append({
                        'sector': self._normalize_sector(sector),
                        'percentage': pct
                    })
        
        return sorted(sectors, key=lambda x: x['percentage'], reverse=True)[:10]
    
    def _normalize_sector(self, sector: str) -> str:
        """Normalize sector names"""
        mapping = {
            'banks': 'Financial Services',
            'banking': 'Financial Services',
            'nbfc': 'Financial Services',
            'it': 'Information Technology',
            'software': 'Information Technology',
            'technology': 'Information Technology',
            'pharma': 'Healthcare',
            'pharmaceuticals': 'Healthcare',
            'fmcg': 'Consumer Goods',
            'consumer staples': 'Consumer Goods',
            'auto': 'Automobile',
            'automotive': 'Automobile',
            'industrial': 'Capital Goods',
            'engineering': 'Capital Goods',
            'telecom': 'Telecommunication',
            'communication': 'Telecommunication',
            'metals': 'Metals & Mining',
            'steel': 'Metals & Mining',
            'power': 'Utilities',
            'electricity': 'Utilities',
            'realty': 'Real Estate',
        }
        
        lower = sector.lower()
        return mapping.get(lower, sector)
    
    def _detect_sector_for_company(self, company: str) -> str:
        """Detect sector from company name"""
        company_lower = company.lower()
        
        sector_keywords = {
            'Financial Services': ['bank', 'hdfc', 'icici', 'kotak', 'axis', 'sbi', 'finance', 'bajaj fin'],
            'Information Technology': ['infosys', 'tcs', 'wipro', 'hcl', 'tech mahindra', 'mphasis', 'ltimindtree'],
            'Oil & Gas': ['reliance', 'ongc', 'ioc', 'bpcl', 'hpcl', 'oil', 'petroleum', 'gail'],
            'Healthcare': ['sun pharma', 'cipla', 'dr. reddy', 'lupin', 'divi', 'pharma', 'apollo'],
            'Automobile': ['tata motors', 'maruti', 'bajaj auto', 'hero', 'mahindra', 'eicher'],
            'Consumer Goods': ['itc', 'hindustan unilever', 'nestle', 'dabur', 'britannia', 'godrej'],
            'Telecommunication': ['bharti', 'airtel', 'jio', 'vodafone', 'indus towers'],
            'Capital Goods': ['larsen', 'l&t', 'siemens', 'abb', 'bhel', 'thermax'],
            'Metals & Mining': ['tata steel', 'hindalco', 'jsw', 'vedanta', 'coal india', 'nmdc'],
            'Power': ['ntpc', 'power grid', 'tata power', 'adani power', 'nhpc'],
            'Cement': ['ultratech', 'ambuja', 'acc', 'shree cement', 'dalmia'],
        }
        
        for sector, keywords in sector_keywords.items():
            for keyword in keywords:
                if keyword in company_lower:
                    return sector
        
        return 'Others'
    
    def _detect_category(self, fund_name: str) -> Dict:
        """Detect fund category from name"""
        name_lower = fund_name.lower()
        
        if any(x in name_lower for x in ['large cap', 'largecap', 'bluechip', 'top 100', 'top100']):
            return {'category': 'equity', 'sub_category': 'largecap'}
        elif any(x in name_lower for x in ['mid cap', 'midcap']):
            return {'category': 'equity', 'sub_category': 'midcap'}
        elif any(x in name_lower for x in ['small cap', 'smallcap']):
            return {'category': 'equity', 'sub_category': 'smallcap'}
        elif any(x in name_lower for x in ['flexi', 'flexicap', 'multi cap', 'multicap']):
            return {'category': 'equity', 'sub_category': 'flexicap'}
        elif any(x in name_lower for x in ['elss', 'tax saver', 'tax saving', 'long term equity']):
            return {'category': 'equity', 'sub_category': 'elss'}
        elif any(x in name_lower for x in ['index', 'nifty', 'sensex', 'etf']):
            return {'category': 'equity', 'sub_category': 'index'}
        elif any(x in name_lower for x in ['focused', 'concentrated']):
            return {'category': 'equity', 'sub_category': 'focused'}
        elif any(x in name_lower for x in ['value', 'contra', 'dividend yield']):
            return {'category': 'equity', 'sub_category': 'value'}
        elif any(x in name_lower for x in ['liquid', 'overnight', 'money market']):
            return {'category': 'debt', 'sub_category': 'liquid'}
        elif any(x in name_lower for x in ['gilt', 'government', 'g-sec']):
            return {'category': 'debt', 'sub_category': 'gilt'}
        elif any(x in name_lower for x in ['corporate bond', 'credit risk']):
            return {'category': 'debt', 'sub_category': 'corporate'}
        elif any(x in name_lower for x in ['short', 'ultra short', 'low duration']):
            return {'category': 'debt', 'sub_category': 'short_duration'}
        elif any(x in name_lower for x in ['dynamic', 'strategic']):
            return {'category': 'debt', 'sub_category': 'dynamic'}
        elif any(x in name_lower for x in ['gold', 'silver', 'commodity']):
            return {'category': 'commodity', 'sub_category': 'precious_metals'}
        elif any(x in name_lower for x in ['hybrid', 'balanced', 'advantage', 'aggressive']):
            return {'category': 'hybrid', 'sub_category': 'balanced'}
        elif any(x in name_lower for x in ['arbitrage']):
            return {'category': 'hybrid', 'sub_category': 'arbitrage'}
        elif any(x in name_lower for x in ['solution', 'retirement', 'children']):
            return {'category': 'solution', 'sub_category': 'retirement'}
        else:
            return {'category': 'equity', 'sub_category': 'diversified'}
    
    def _extract_value(self, text: str, patterns: List[str]) -> Optional[str]:
        """Extract numeric value using patterns"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_text(self, text: str, patterns: List[str]) -> Optional[str]:
        """Extract text using patterns"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:50]
        return None
    
    def _extract_from_tables(self) -> List[Dict]:
        """Extract funds from PDF tables"""
        funds = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if not table:
                            continue
                        
                        # Check if this is a holdings table
                        for row in table:
                            if not row or len(row) < 2:
                                continue
                            
                            # Try to identify fund/holding data
                            first_cell = str(row[0] or '').strip()
                            if 'Fund' in first_cell and len(first_cell) > 10:
                                # This might be a fund row
                                pass
        except:
            pass
        
        return funds


class DatabaseUpdater:
    """Updates MongoDB with parsed fund data"""
    
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client['mutualfunds']
        self.funds_col = self.db['funds']
    
    def clean_mock_data(self):
        """Remove mock/sample data from database"""
        print("🧹 Cleaning mock/sample data...")
        
        # Remove entries with mock data indicators
        mock_indicators = [
            {'holdingsSource': 'Sample Data'},
            {'holdingsSource': 'Mock Data'},
            {'holdingsSource': 'AI Generated'},
            {'dataSource': 'Sample'},
        ]
        
        cleaned = 0
        for indicator in mock_indicators:
            result = self.funds_col.update_many(
                indicator,
                {'$unset': {'holdings': '', 'sectorAllocation': '', 'holdingsSource': ''}}
            )
            cleaned += result.modified_count
        
        print(f"   Cleaned {cleaned} funds with mock data")
        return cleaned
    
    def update_fund(self, fund_data: Dict) -> bool:
        """Update a fund in the database"""
        if not fund_data.get('schemeName'):
            return False
        
        # Find matching fund
        fund_name = fund_data['schemeName']
        
        # Try exact match first
        query = {'schemeName': {'$regex': f'^{re.escape(fund_name)}', '$options': 'i'}}
        existing = self.funds_col.find_one(query)
        
        if not existing:
            # Try partial match
            base_name = self._get_base_name(fund_name)
            query = {'schemeName': {'$regex': base_name, '$options': 'i'}}
            existing = self.funds_col.find_one(query)
        
        if existing:
            # Update existing fund
            update_data = {}
            
            if fund_data.get('holdings'):
                update_data['holdings'] = fund_data['holdings']
            if fund_data.get('sectorAllocation'):
                update_data['sectorAllocation'] = fund_data['sectorAllocation']
            if fund_data.get('nav'):
                update_data['nav'] = fund_data['nav']
            if fund_data.get('aum'):
                update_data['aum'] = fund_data['aum']
            if fund_data.get('expenseRatio'):
                update_data['expenseRatio'] = fund_data['expenseRatio']
            if fund_data.get('fundManager'):
                update_data['fundManager'] = fund_data['fundManager']
            if fund_data.get('benchmark'):
                update_data['benchmark'] = fund_data['benchmark']
            if fund_data.get('category'):
                update_data['category'] = fund_data['category']
            if fund_data.get('subCategory'):
                update_data['subCategory'] = fund_data['subCategory']
            
            update_data['holdingsLastUpdated'] = datetime.now().isoformat()
            update_data['holdingsSource'] = 'AMC Factsheet'
            
            if update_data:
                self.funds_col.update_one(
                    {'_id': existing['_id']},
                    {'$set': update_data}
                )
                return True
        
        return False
    
    def update_fund_variants(self, base_name: str, holdings: List[Dict], sectors: List[Dict]) -> int:
        """Update all variants of a fund with the same holdings"""
        # Find all variants
        variants = list(self.funds_col.find({
            'schemeName': {'$regex': re.escape(base_name), '$options': 'i'}
        }))
        
        updated = 0
        for fund in variants:
            result = self.funds_col.update_one(
                {'_id': fund['_id']},
                {
                    '$set': {
                        'holdings': holdings,
                        'sectorAllocation': sectors,
                        'holdingsLastUpdated': datetime.now().isoformat(),
                        'holdingsSource': 'AMC Factsheet'
                    }
                }
            )
            if result.modified_count:
                updated += 1
        
        return updated
    
    def _get_base_name(self, fund_name: str) -> str:
        """Get base fund name without variants"""
        base = fund_name
        patterns = [
            r'\s*-\s*(Direct|Regular)\s*(Plan)?',
            r'\s*-\s*(Growth|IDCW|Dividend)',
            r'\s*-\s*(Daily|Weekly|Monthly|Quarterly)',
            r'\s*\(.*?\)',
        ]
        
        for pattern in patterns:
            base = re.sub(pattern, '', base, flags=re.IGNORECASE)
        
        return base.strip()
    
    def get_status(self) -> Dict:
        """Get database status"""
        total = self.funds_col.count_documents({})
        with_holdings = self.funds_col.count_documents({
            'holdings': {'$exists': True, '$ne': [], '$ne': None, '$not': {'$size': 0}}
        })
        with_sectors = self.funds_col.count_documents({
            'sectorAllocation': {'$exists': True, '$ne': [], '$ne': None}
        })
        
        return {
            'total': total,
            'with_holdings': with_holdings,
            'with_sectors': with_sectors,
            'coverage': with_holdings / total * 100 if total > 0 else 0
        }


def process_all_factsheets():
    """Process all factsheet PDFs and update database"""
    print("=" * 70)
    print("COMPREHENSIVE FACTSHEET PROCESSOR")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # Initialize
    updater = DatabaseUpdater()
    
    # Show initial status
    status = updater.get_status()
    print("📊 Initial Database Status:")
    print(f"   Total Funds: {status['total']:,}")
    print(f"   With Holdings: {status['with_holdings']:,} ({status['coverage']:.1f}%)")
    print()
    
    # Clean mock data first
    updater.clean_mock_data()
    print()
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(FACTSHEET_FOLDER) if f.endswith('.pdf')]
    print(f"📁 Found {len(pdf_files)} PDF files to process")
    print()
    
    total_funds_extracted = 0
    total_funds_updated = 0
    
    for i, pdf_file in enumerate(pdf_files, 1):
        pdf_path = os.path.join(FACTSHEET_FOLDER, pdf_file)
        print(f"\n[{i}/{len(pdf_files)}] {pdf_file}")
        print("-" * 50)
        
        try:
            parser = FactsheetParser(pdf_path)
            funds = parser.parse()
            
            funds_updated = 0
            for fund_data in funds:
                if fund_data.get('holdings') or fund_data.get('sectorAllocation'):
                    if updater.update_fund(fund_data):
                        funds_updated += 1
                    
                    # Also update variants
                    if fund_data.get('holdings'):
                        base = updater._get_base_name(fund_data['schemeName'])
                        variants = updater.update_fund_variants(
                            base,
                            fund_data.get('holdings', []),
                            fund_data.get('sectorAllocation', [])
                        )
                        funds_updated += variants
            
            total_funds_extracted += len(funds)
            total_funds_updated += funds_updated
            
            if funds_updated > 0:
                print(f"   ✅ Updated {funds_updated} funds in database")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:60]}")
    
    # Final status
    print()
    print("=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)
    print(f"   PDFs Processed: {len(pdf_files)}")
    print(f"   Funds Extracted: {total_funds_extracted}")
    print(f"   Funds Updated: {total_funds_updated}")
    print()
    
    # Show final status
    status = updater.get_status()
    print("📊 Final Database Status:")
    print(f"   Total Funds: {status['total']:,}")
    print(f"   With Holdings: {status['with_holdings']:,} ({status['coverage']:.1f}%)")
    print(f"   With Sectors: {status['with_sectors']:,}")
    
    return {
        'pdfs_processed': len(pdf_files),
        'funds_extracted': total_funds_extracted,
        'funds_updated': total_funds_updated,
        'final_coverage': status['coverage']
    }


if __name__ == "__main__":
    process_all_factsheets()
