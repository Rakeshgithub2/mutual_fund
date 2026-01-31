"""
MULTI-FUND PDF PARSER
======================
Parses AMC factsheet PDFs that contain multiple funds in a single document.

One PDF (e.g., HDFC_Factsheet.pdf) contains 40-80 funds.
This parser:
1. Detects fund boundaries using scheme name patterns
2. Extracts holdings, sectors, managers per fund
3. Returns structured data for each fund separately
"""

import pdfplumber
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FundData:
    """Extracted data for a single fund"""
    scheme_name: str
    category: str
    sub_category: str
    fund_manager: str
    benchmark: str
    aum: float
    nav: float
    expense_ratio: float
    holdings: List[Dict]  # [{company, sector, percentage}, ...]
    sector_allocation: List[Dict]  # [{sector, percentage}, ...]
    returns: Dict  # {1Y, 3Y, 5Y, SI}
    risk_level: str
    launch_date: str


class MultiFundPDFParser:
    """
    Parses factsheet PDFs containing multiple funds.
    Each AMC publishes one PDF with all their schemes.
    """
    
    # Patterns to detect fund name headers
    FUND_NAME_PATTERNS = [
        r'^([A-Z][A-Za-z\s]+(?:Fund|Scheme)(?:\s*-\s*(?:Direct|Regular))?\s*(?:Plan)?(?:\s*-\s*(?:Growth|Dividend))?)$',
        r'^([A-Z][A-Z\s]+(?:FUND|SCHEME))',
        r'Scheme Name[:\s]+([A-Za-z\s\-]+(?:Fund|Scheme))',
    ]
    
    # Patterns to detect section headers
    SECTION_PATTERNS = {
        'holdings': [
            r'Top\s*(?:10|Ten)?\s*(?:Equity\s*)?Holdings',
            r'Portfolio\s*Holdings',
            r'Top\s*Holdings\s*\(%\s*of\s*Net\s*Assets\)',
            r'Stock\s*Holdings',
        ],
        'sector_allocation': [
            r'Sector\s*Allocation',
            r'Sector\s*Wise\s*Allocation',
            r'Industry\s*Allocation',
            r'Sectoral\s*Allocation',
        ],
        'fund_manager': [
            r'Fund\s*Manager[s]?\s*:?',
            r'Managed\s*By',
            r'Portfolio\s*Manager',
        ],
        'returns': [
            r'Returns\s*\(%\)',
            r'Performance',
            r'Scheme\s*Returns',
            r'Historical\s*Returns',
        ],
        'fund_details': [
            r'Scheme\s*Details',
            r'Fund\s*Details',
            r'Key\s*Information',
        ]
    }
    
    # Patterns to extract data
    HOLDING_PATTERN = re.compile(
        r'([A-Za-z][A-Za-z\s\.\&\-\(\)]+?)[\s\|]+(\d+\.?\d*)\s*%?',
        re.IGNORECASE
    )
    
    SECTOR_PATTERN = re.compile(
        r'([A-Za-z][A-Za-z\s\&\-]+?)[\s\|]+(\d+\.?\d*)\s*%?',
        re.IGNORECASE
    )
    
    RETURNS_PATTERN = re.compile(
        r'(\d+\.?\d*)\s*%?\s*(?:\||,|\s)\s*(\d+\.?\d*)\s*%?\s*(?:\||,|\s)\s*(\d+\.?\d*)\s*%?',
        re.IGNORECASE
    )
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.full_text = ""
        self.pages = []
        
    def parse(self) -> List[FundData]:
        """
        Parse the PDF and extract data for all funds.
        Returns list of FundData objects.
        """
        print(f"📄 Parsing: {self.pdf_path}")
        
        # Extract text from PDF
        self._extract_text()
        
        # Detect fund boundaries
        fund_sections = self._detect_fund_sections()
        print(f"   Found {len(fund_sections)} fund sections")
        
        # Parse each fund section
        funds = []
        for section in fund_sections:
            try:
                fund_data = self._parse_fund_section(section)
                if fund_data and fund_data.scheme_name:
                    funds.append(fund_data)
            except Exception as e:
                print(f"   ⚠️ Error parsing section: {str(e)[:50]}")
        
        print(f"   ✅ Extracted {len(funds)} funds")
        return funds
    
    def _extract_text(self):
        """Extract text from all pages"""
        with pdfplumber.open(self.pdf_path) as pdf:
            self.pages = []
            for page in pdf.pages:
                text = page.extract_text() or ""
                self.pages.append(text)
                self.full_text += text + "\n\n"
    
    def _detect_fund_sections(self) -> List[Dict]:
        """
        Detect where each fund's data starts and ends in the PDF.
        Returns list of {start_idx, end_idx, name} dicts.
        """
        sections = []
        lines = self.full_text.split('\n')
        
        current_fund = None
        current_start = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check if this line is a fund name header
            for pattern in self.FUND_NAME_PATTERNS:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    # Save previous fund section
                    if current_fund:
                        sections.append({
                            'name': current_fund,
                            'start': current_start,
                            'end': i,
                            'text': '\n'.join(lines[current_start:i])
                        })
                    
                    # Start new fund section
                    current_fund = match.group(1).strip()
                    current_start = i
                    break
        
        # Add last fund
        if current_fund:
            sections.append({
                'name': current_fund,
                'start': current_start,
                'end': len(lines),
                'text': '\n'.join(lines[current_start:])
            })
        
        return sections
    
    def _parse_fund_section(self, section: Dict) -> Optional[FundData]:
        """Parse a single fund's section and extract all data"""
        text = section['text']
        name = section['name']
        
        # Extract holdings
        holdings = self._extract_holdings(text)
        
        # Extract sector allocation
        sectors = self._extract_sectors(text)
        
        # Extract fund manager
        fund_manager = self._extract_fund_manager(text)
        
        # Extract returns
        returns = self._extract_returns(text)
        
        # Extract other details
        aum = self._extract_aum(text)
        nav = self._extract_nav(text)
        expense_ratio = self._extract_expense_ratio(text)
        benchmark = self._extract_benchmark(text)
        category = self._detect_category(name, text)
        
        return FundData(
            scheme_name=name,
            category=category.get('category', 'equity'),
            sub_category=category.get('sub_category', 'flexicap'),
            fund_manager=fund_manager,
            benchmark=benchmark,
            aum=aum,
            nav=nav,
            expense_ratio=expense_ratio,
            holdings=holdings,
            sector_allocation=sectors,
            returns=returns,
            risk_level=self._detect_risk_level(category.get('category', '')),
            launch_date=self._extract_launch_date(text)
        )
    
    def _extract_holdings(self, text: str) -> List[Dict]:
        """Extract top 10 holdings from fund section"""
        holdings = []
        
        # Find holdings section
        holdings_match = None
        for pattern in self.SECTION_PATTERNS['holdings']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                holdings_match = match
                break
        
        if not holdings_match:
            return []
        
        # Get text after holdings header
        start = holdings_match.end()
        section_text = text[start:start+2000]  # Next 2000 chars
        
        # Extract company names and percentages
        lines = section_text.split('\n')
        for line in lines[:15]:  # Top 15 lines
            match = self.HOLDING_PATTERN.search(line)
            if match:
                company = match.group(1).strip()
                percentage = float(match.group(2))
                
                # Filter out non-company names
                if len(company) > 3 and percentage > 0.1 and percentage < 50:
                    holdings.append({
                        'company': company,
                        'sector': self._detect_sector(company),
                        'percentage': percentage
                    })
        
        return holdings[:10]  # Top 10 only
    
    def _extract_sectors(self, text: str) -> List[Dict]:
        """Extract sector allocation"""
        sectors = []
        
        # Find sector section
        sector_match = None
        for pattern in self.SECTION_PATTERNS['sector_allocation']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                sector_match = match
                break
        
        if not sector_match:
            return []
        
        # Get text after sector header
        start = sector_match.end()
        section_text = text[start:start+1500]
        
        # Extract sectors and percentages
        lines = section_text.split('\n')
        for line in lines[:12]:
            match = self.SECTOR_PATTERN.search(line)
            if match:
                sector = match.group(1).strip()
                percentage = float(match.group(2))
                
                if len(sector) > 3 and percentage > 0.5 and percentage < 60:
                    sectors.append({
                        'sector': self._normalize_sector(sector),
                        'percentage': percentage
                    })
        
        return sectors[:10]
    
    def _extract_fund_manager(self, text: str) -> str:
        """Extract fund manager name"""
        for pattern in self.SECTION_PATTERNS['fund_manager']:
            match = re.search(pattern + r'\s*:?\s*([A-Za-z\s\.]+)', text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 3 and len(name) < 50:
                    return name
        return "Fund Manager"
    
    def _extract_returns(self, text: str) -> Dict:
        """Extract return percentages"""
        returns = {'1Y': None, '3Y': None, '5Y': None, 'SI': None}
        
        # Look for return patterns
        patterns = [
            r'1\s*(?:Year|Y|Yr)[:\s]+(-?\d+\.?\d*)\s*%?',
            r'3\s*(?:Year|Y|Yr)[:\s]+(-?\d+\.?\d*)\s*%?',
            r'5\s*(?:Year|Y|Yr)[:\s]+(-?\d+\.?\d*)\s*%?',
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                key = ['1Y', '3Y', '5Y'][i]
                returns[key] = float(match.group(1))
        
        return returns
    
    def _extract_aum(self, text: str) -> float:
        """Extract AUM"""
        patterns = [
            r'AUM[:\s]+(?:Rs\.?|₹)?\s*(\d+[\d,\.]*)\s*(?:Cr|Crore)',
            r'Assets\s*Under\s*Management[:\s]+(\d+[\d,\.]*)',
            r'Fund\s*Size[:\s]+(\d+[\d,\.]*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(',', '')
                return float(value)
        return 0.0
    
    def _extract_nav(self, text: str) -> float:
        """Extract NAV"""
        patterns = [
            r'NAV[:\s]+(?:Rs\.?|₹)?\s*(\d+\.?\d*)',
            r'Net\s*Asset\s*Value[:\s]+(\d+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return 0.0
    
    def _extract_expense_ratio(self, text: str) -> float:
        """Extract expense ratio"""
        patterns = [
            r'Expense\s*Ratio[:\s]+(\d+\.?\d*)\s*%?',
            r'TER[:\s]+(\d+\.?\d*)\s*%?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return 0.0
    
    def _extract_benchmark(self, text: str) -> str:
        """Extract benchmark"""
        patterns = [
            r'Benchmark[:\s]+([A-Za-z\s\d\-]+?)(?:\n|$)',
            r'Index[:\s]+([A-Za-z\s\d\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:50]
        return ""
    
    def _extract_launch_date(self, text: str) -> str:
        """Extract fund launch date"""
        patterns = [
            r'Launch\s*Date[:\s]+(\d{1,2}[-/]\w+[-/]\d{2,4})',
            r'Inception\s*Date[:\s]+(\d{1,2}[-/]\w+[-/]\d{2,4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return ""
    
    def _detect_category(self, name: str, text: str) -> Dict:
        """Detect fund category from name and content"""
        name_lower = name.lower()
        
        # Category detection
        if any(x in name_lower for x in ['large cap', 'largecap', 'bluechip', 'top 100']):
            return {'category': 'equity', 'sub_category': 'largecap'}
        elif any(x in name_lower for x in ['mid cap', 'midcap']):
            return {'category': 'equity', 'sub_category': 'midcap'}
        elif any(x in name_lower for x in ['small cap', 'smallcap']):
            return {'category': 'equity', 'sub_category': 'smallcap'}
        elif any(x in name_lower for x in ['flexi', 'multi cap', 'multicap']):
            return {'category': 'equity', 'sub_category': 'flexicap'}
        elif any(x in name_lower for x in ['elss', 'tax saver', 'tax saving']):
            return {'category': 'equity', 'sub_category': 'elss'}
        elif any(x in name_lower for x in ['index', 'nifty', 'sensex']):
            return {'category': 'equity', 'sub_category': 'indexfund'}
        elif any(x in name_lower for x in ['liquid', 'overnight', 'money market']):
            return {'category': 'debt', 'sub_category': 'liquid'}
        elif any(x in name_lower for x in ['gilt', 'government']):
            return {'category': 'debt', 'sub_category': 'gilt'}
        elif any(x in name_lower for x in ['debt', 'bond', 'corporate']):
            return {'category': 'debt', 'sub_category': 'debt'}
        elif any(x in name_lower for x in ['gold', 'silver', 'commodity']):
            return {'category': 'commodity', 'sub_category': 'gold'}
        elif any(x in name_lower for x in ['hybrid', 'balanced', 'advantage']):
            return {'category': 'hybrid', 'sub_category': 'balanced'}
        else:
            return {'category': 'equity', 'sub_category': 'flexicap'}
    
    def _detect_risk_level(self, category: str) -> str:
        """Detect risk level from category"""
        if category == 'debt':
            return 'low'
        elif category == 'hybrid':
            return 'moderate'
        elif category == 'commodity':
            return 'moderate'
        else:
            return 'high'
    
    def _detect_sector(self, company: str) -> str:
        """Detect sector from company name"""
        company_lower = company.lower()
        
        if any(x in company_lower for x in ['bank', 'hdfc', 'icici', 'kotak', 'axis', 'sbi', 'finance']):
            return 'Financial Services'
        elif any(x in company_lower for x in ['infosys', 'tcs', 'wipro', 'tech', 'hcl', 'software']):
            return 'Information Technology'
        elif any(x in company_lower for x in ['reliance', 'oil', 'ongc', 'petroleum', 'bpcl']):
            return 'Oil & Gas'
        elif any(x in company_lower for x in ['pharma', 'sun', 'cipla', 'dr reddy', 'lupin']):
            return 'Healthcare'
        elif any(x in company_lower for x in ['bharti', 'airtel', 'jio', 'vodafone']):
            return 'Telecom'
        elif any(x in company_lower for x in ['tata motor', 'maruti', 'bajaj', 'hero']):
            return 'Automobile'
        elif any(x in company_lower for x in ['itc', 'hindustan', 'nestle', 'dabur']):
            return 'Consumer Goods'
        elif any(x in company_lower for x in ['larsen', 'l&t', 'ultratech', 'cement']):
            return 'Capital Goods'
        else:
            return 'Other'
    
    def _normalize_sector(self, sector: str) -> str:
        """Normalize sector names"""
        sector_map = {
            'financial': 'Financial Services',
            'banking': 'Financial Services',
            'it': 'Information Technology',
            'technology': 'Information Technology',
            'oil': 'Oil & Gas',
            'energy': 'Oil & Gas',
            'pharma': 'Healthcare',
            'healthcare': 'Healthcare',
            'telecom': 'Telecommunication',
            'auto': 'Automobile',
            'consumer': 'Consumer Goods',
            'fmcg': 'Consumer Goods',
            'capital': 'Capital Goods',
            'industrial': 'Capital Goods',
        }
        
        sector_lower = sector.lower()
        for key, value in sector_map.items():
            if key in sector_lower:
                return value
        return sector


def main():
    """Test the parser"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python multi_fund_parser.py <pdf_path>")
        print("Example: python multi_fund_parser.py downloads/HDFC_factsheet.pdf")
        return
    
    pdf_path = sys.argv[1]
    parser = MultiFundPDFParser(pdf_path)
    funds = parser.parse()
    
    print(f"\n📊 Extracted {len(funds)} funds:")
    for fund in funds[:5]:
        print(f"\n  {fund.scheme_name}")
        print(f"    Category: {fund.category}/{fund.sub_category}")
        print(f"    Manager: {fund.fund_manager}")
        print(f"    Holdings: {len(fund.holdings)}")
        print(f"    Sectors: {len(fund.sector_allocation)}")


if __name__ == '__main__':
    main()
