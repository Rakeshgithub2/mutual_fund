"""
═══════════════════════════════════════════════════════════════════════════════
PDF PARSER - MULTI-FUND EXTRACTION ENGINE
═══════════════════════════════════════════════════════════════════════════════
Parses factsheet PDFs that contain MULTIPLE funds (like Kotak, HDFC master PDFs)
Extracts: Holdings, Sectors, Fund Manager, AUM, Returns, Expense Ratio
"""

import re
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import pdfplumber
import pandas as pd
from rich.console import Console
from rich.table import Table

from config import (
    CATEGORY_MAPPING,
    SECTOR_MAPPING,
    EXTRACTION_PATTERNS,
    HOLDINGS_TABLE_KEYWORDS,
    SECTOR_TABLE_KEYWORDS,
    RETURNS_TABLE_KEYWORDS,
)

console = Console()


@dataclass
class FundData:
    """Extracted fund data structure"""
    fund_name: str
    amc: str
    category: str = ""
    sub_category: str = ""
    
    # Fund Details
    nav: Optional[float] = None
    aum_cr: Optional[float] = None
    expense_ratio: Optional[float] = None
    benchmark: Optional[str] = None
    launch_date: Optional[str] = None
    
    # Fund Manager
    fund_manager: Optional[str] = None
    fund_manager_since: Optional[str] = None
    
    # Returns (in %)
    returns_1y: Optional[float] = None
    returns_3y: Optional[float] = None
    returns_5y: Optional[float] = None
    returns_since_inception: Optional[float] = None
    
    # Holdings (top 10)
    top_holdings: List[Dict[str, Any]] = field(default_factory=list)
    
    # Sector Allocation
    sector_allocation: List[Dict[str, Any]] = field(default_factory=list)
    
    # Market Cap Distribution
    market_cap: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    as_of_date: Optional[str] = None
    extraction_date: str = field(default_factory=lambda: datetime.now().isoformat())
    data_complete: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for MongoDB storage"""
        return {
            'fundName': self.fund_name,
            'amc': {'name': self.amc},
            'category': self.category,
            'subCategory': self.sub_category,
            'nav': {'value': self.nav, 'date': self.as_of_date},
            'aum': {'value': self.aum_cr, 'date': self.as_of_date},
            'expenseRatio': self.expense_ratio,
            'benchmark': {'name': self.benchmark},
            'launchDate': self.launch_date,
            'fundManager': {
                'name': self.fund_manager,
                'managingSince': self.fund_manager_since,
            },
            'returns': {
                '1Y': self.returns_1y,
                '3Y': self.returns_3y,
                '5Y': self.returns_5y,
                'sinceInception': self.returns_since_inception,
            },
            'topHoldings': self.top_holdings,
            'sectorAllocation': self.sector_allocation,
            'marketCapDistribution': self.market_cap,
            'asOfDate': self.as_of_date,
            'extractionDate': self.extraction_date,
            'dataComplete': self.data_complete,
        }


class MultiFundPDFParser:
    """
    Parser for AMC factsheets containing MULTIPLE funds
    Handles: Kotak, HDFC, ICICI, SBI etc. master factsheets
    """
    
    def __init__(self, pdf_path: str, amc_code: str):
        self.pdf_path = pdf_path
        self.amc_code = amc_code
        self.amc_name = self._get_amc_name()
        self.funds: List[FundData] = []
        
    def _get_amc_name(self) -> str:
        """Get full AMC name from code"""
        amc_names = {
            'HDFC': 'HDFC Mutual Fund',
            'ICICI': 'ICICI Prudential Mutual Fund',
            'SBI': 'SBI Mutual Fund',
            'KOTAK': 'Kotak Mahindra Mutual Fund',
            'AXIS': 'Axis Mutual Fund',
            'NIPPON': 'Nippon India Mutual Fund',
            'ADITYA_BIRLA': 'Aditya Birla Sun Life Mutual Fund',
            'TATA': 'Tata Mutual Fund',
            'UTI': 'UTI Mutual Fund',
            'DSP': 'DSP Mutual Fund',
            'MIRAE': 'Mirae Asset Mutual Fund',
            'MOTILAL': 'Motilal Oswal Mutual Fund',
            'PARAG_PARIKH': 'PPFAS Mutual Fund',
        }
        return amc_names.get(self.amc_code, self.amc_code)
    
    def parse(self) -> List[FundData]:
        """
        Parse the entire PDF and extract all funds
        
        Returns:
            List of FundData objects
        """
        console.print(f"\n[bold cyan]📄 Parsing {self.amc_code} factsheet...[/bold cyan]")
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                console.print(f"[dim]   Total pages: {total_pages}[/dim]")
                
                # Step 1: Identify fund boundaries (which pages belong to which fund)
                fund_pages = self._identify_fund_pages(pdf)
                console.print(f"[green]   ✅ Found {len(fund_pages)} funds[/green]")
                
                # Step 2: Extract data for each fund
                for fund_name, page_range in fund_pages.items():
                    console.print(f"[dim]   📊 Extracting: {fund_name}[/dim]")
                    fund_data = self._extract_fund_data(pdf, fund_name, page_range)
                    if fund_data:
                        self.funds.append(fund_data)
                
                console.print(f"[bold green]✅ Extracted {len(self.funds)} funds from {self.amc_code}[/bold green]")
                
        except Exception as e:
            console.print(f"[red]❌ Error parsing PDF: {e}[/red]")
            import traceback
            traceback.print_exc()
        
        return self.funds
    
    def _identify_fund_pages(self, pdf) -> Dict[str, Tuple[int, int]]:
        """
        Identify page ranges for each fund in the PDF
        
        Returns:
            Dict mapping fund_name -> (start_page, end_page)
        """
        fund_pages = {}
        current_fund = None
        start_page = 0
        
        # Patterns to identify new fund sections
        fund_start_patterns = [
            # Generic patterns
            r"(?:Scheme|Fund)\s+Name\s*[:\-]?\s*(.+?(?:Fund|Plan|Scheme))",
            r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Fund|Plan))",
            
            # AMC-specific patterns
            rf"{self.amc_code.title()}\s+(.+?)\s+Fund",
            rf"{self.amc_code.title()}\s+(.+?)\s+Direct\s+Plan",
        ]
        
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            
            # Check for fund header
            for pattern in fund_start_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    fund_name = matches[0].strip() if isinstance(matches[0], str) else matches[0][0].strip()
                    
                    # Skip if too short or generic
                    if len(fund_name) < 5:
                        continue
                    
                    # Clean fund name
                    fund_name = self._clean_fund_name(fund_name)
                    
                    # Save previous fund's page range
                    if current_fund and current_fund not in fund_pages:
                        fund_pages[current_fund] = (start_page, page_num - 1)
                    
                    # Start new fund
                    if fund_name not in fund_pages:
                        current_fund = fund_name
                        start_page = page_num
                    break
        
        # Save last fund
        if current_fund and current_fund not in fund_pages:
            fund_pages[current_fund] = (start_page, len(pdf.pages) - 1)
        
        return fund_pages
    
    def _clean_fund_name(self, name: str) -> str:
        """Clean and standardize fund name"""
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Remove common suffixes that don't add value
        remove_patterns = [
            r'\s*-?\s*Direct\s*(?:Plan)?',
            r'\s*-?\s*Growth\s*(?:Option)?',
            r'\s*-?\s*Regular\s*(?:Plan)?',
            r'\s*\(.*?\)',  # Remove parenthetical content
        ]
        
        for pattern in remove_patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        return name.strip()
    
    def _extract_fund_data(self, pdf, fund_name: str, page_range: Tuple[int, int]) -> Optional[FundData]:
        """
        Extract all data for a specific fund
        """
        start_page, end_page = page_range
        
        # Combine text from all fund pages
        combined_text = ""
        tables = []
        
        for page_num in range(start_page, min(end_page + 1, len(pdf.pages))):
            page = pdf.pages[page_num]
            combined_text += (page.extract_text() or "") + "\n"
            
            # Extract tables
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
        
        # Create fund data object
        fund_data = FundData(
            fund_name=fund_name,
            amc=self.amc_name,
        )
        
        # Detect category
        category, sub_category = self._detect_category(fund_name + " " + combined_text[:500])
        fund_data.category = category
        fund_data.sub_category = sub_category
        
        # Extract structured data
        fund_data.nav = self._extract_pattern(combined_text, 'nav')
        fund_data.aum_cr = self._extract_pattern(combined_text, 'aum')
        fund_data.expense_ratio = self._extract_pattern(combined_text, 'expense_ratio')
        fund_data.benchmark = self._extract_text_pattern(combined_text, 'benchmark')
        fund_data.launch_date = self._extract_text_pattern(combined_text, 'launch_date')
        fund_data.fund_manager = self._extract_text_pattern(combined_text, 'fund_manager')
        
        # Extract returns
        fund_data.returns_1y = self._extract_pattern(combined_text, 'returns_1y')
        fund_data.returns_3y = self._extract_pattern(combined_text, 'returns_3y')
        fund_data.returns_5y = self._extract_pattern(combined_text, 'returns_5y')
        
        # Extract holdings from tables
        fund_data.top_holdings = self._extract_holdings(tables, combined_text)
        
        # Extract sector allocation
        fund_data.sector_allocation = self._extract_sectors(tables, combined_text)
        
        # Extract market cap distribution
        fund_data.market_cap = self._extract_market_cap(combined_text)
        
        # Extract as_of_date
        fund_data.as_of_date = self._extract_as_of_date(combined_text)
        
        # Check data completeness
        fund_data.data_complete = self._check_completeness(fund_data)
        
        return fund_data
    
    def _detect_category(self, text: str) -> Tuple[str, str]:
        """Detect fund category from text"""
        text_lower = text.lower()
        
        for keyword, (category, sub_category) in CATEGORY_MAPPING.items():
            if keyword in text_lower:
                return category, sub_category
        
        return "equity", "multi cap"  # Default
    
    def _extract_pattern(self, text: str, pattern_key: str) -> Optional[float]:
        """Extract numeric value using patterns"""
        patterns = EXTRACTION_PATTERNS.get(pattern_key, [])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = match.group(1)
                    # Clean value
                    value = value.replace(',', '').replace('₹', '').replace('Rs', '').strip()
                    return round(float(value), 2)
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _extract_text_pattern(self, text: str, pattern_key: str) -> Optional[str]:
        """Extract text value using patterns"""
        patterns = EXTRACTION_PATTERNS.get(pattern_key, [])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Clean and validate
                if len(value) > 2 and len(value) < 200:
                    return value
        
        return None
    
    def _extract_holdings(self, tables: List, text: str) -> List[Dict[str, Any]]:
        """Extract top 10 holdings from tables"""
        holdings = []
        
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            # Check if this is a holdings table
            header_row = ' '.join(str(cell) for cell in table[0] if cell).lower()
            
            is_holdings_table = any(
                keyword in header_row 
                for keyword in ['company', 'stock', 'holding', 'issuer', '% to net', 'percentage']
            )
            
            if not is_holdings_table:
                continue
            
            # Find column indices
            name_col = None
            percent_col = None
            
            for i, cell in enumerate(table[0]):
                if cell:
                    cell_lower = str(cell).lower()
                    if any(kw in cell_lower for kw in ['company', 'stock', 'name', 'issuer', 'holding']):
                        name_col = i
                    elif any(kw in cell_lower for kw in ['%', 'percent', 'weight', 'net asset']):
                        percent_col = i
            
            if name_col is None:
                name_col = 0
            if percent_col is None:
                percent_col = len(table[0]) - 1
            
            # Extract holdings
            for row in table[1:11]:  # Top 10 only
                try:
                    if not row or len(row) <= max(name_col, percent_col):
                        continue
                    
                    name = str(row[name_col] or '').strip()
                    percent = row[percent_col]
                    
                    if not name or len(name) < 2:
                        continue
                    
                    # Skip header-like rows
                    if any(skip in name.lower() for skip in ['total', 'cash', 'other', 'equity']):
                        continue
                    
                    # Parse percentage
                    if isinstance(percent, str):
                        percent = percent.replace('%', '').replace(',', '').strip()
                    
                    try:
                        percent_value = float(percent)
                        if 0 < percent_value <= 100:
                            holdings.append({
                                'name': name,
                                'percentage': round(percent_value, 2),
                            })
                    except (ValueError, TypeError):
                        continue
                        
                except (IndexError, TypeError):
                    continue
            
            if holdings:
                break  # Found holdings table
        
        # Sort by percentage descending and take top 10
        holdings.sort(key=lambda x: x['percentage'], reverse=True)
        return holdings[:10]
    
    def _extract_sectors(self, tables: List, text: str) -> List[Dict[str, Any]]:
        """Extract sector allocation"""
        sectors = []
        
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            # Check if this is a sector table
            header_row = ' '.join(str(cell) for cell in table[0] if cell).lower()
            
            is_sector_table = any(
                keyword in header_row 
                for keyword in SECTOR_TABLE_KEYWORDS
            )
            
            if not is_sector_table:
                # Also check for sector keywords in first column
                first_col_text = ' '.join(str(row[0]) for row in table if row and row[0]).lower()
                is_sector_table = any(
                    sector.lower() in first_col_text 
                    for sector in SECTOR_MAPPING.values()
                )
            
            if not is_sector_table:
                continue
            
            # Extract sectors
            for row in table[1:]:
                try:
                    if not row or len(row) < 2:
                        continue
                    
                    sector_name = str(row[0] or '').strip()
                    percent = row[-1]  # Usually last column
                    
                    if not sector_name or len(sector_name) < 2:
                        continue
                    
                    # Standardize sector name
                    standardized_sector = self._standardize_sector(sector_name)
                    if not standardized_sector:
                        continue
                    
                    # Parse percentage
                    if isinstance(percent, str):
                        percent = percent.replace('%', '').replace(',', '').strip()
                    
                    try:
                        percent_value = float(percent)
                        if 0 < percent_value <= 100:
                            sectors.append({
                                'sector': standardized_sector,
                                'percentage': round(percent_value, 2),
                            })
                    except (ValueError, TypeError):
                        continue
                        
                except (IndexError, TypeError):
                    continue
            
            if sectors:
                break
        
        # Sort by percentage and take top 10
        sectors.sort(key=lambda x: x['percentage'], reverse=True)
        
        # Group remaining into "Others" if more than 10
        if len(sectors) > 10:
            top_10 = sectors[:10]
            others_sum = sum(s['percentage'] for s in sectors[10:])
            if others_sum > 0:
                top_10.append({
                    'sector': 'Others',
                    'percentage': round(others_sum, 2),
                })
            sectors = top_10
        
        return sectors
    
    def _standardize_sector(self, sector_name: str) -> Optional[str]:
        """Standardize sector name"""
        sector_lower = sector_name.lower()
        
        for keyword, standard_name in SECTOR_MAPPING.items():
            if keyword in sector_lower:
                return standard_name
        
        # If no mapping found, capitalize properly
        if len(sector_name) > 2:
            return sector_name.title()
        
        return None
    
    def _extract_market_cap(self, text: str) -> Dict[str, float]:
        """Extract market cap distribution"""
        market_cap = {}
        
        patterns = [
            (r'large\s*cap[:\s]+([0-9\.]+)\s*%?', 'largeCap'),
            (r'mid\s*cap[:\s]+([0-9\.]+)\s*%?', 'midCap'),
            (r'small\s*cap[:\s]+([0-9\.]+)\s*%?', 'smallCap'),
        ]
        
        for pattern, key in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    if 0 <= value <= 100:
                        market_cap[key] = round(value, 2)
                except ValueError:
                    pass
        
        return market_cap
    
    def _extract_as_of_date(self, text: str) -> Optional[str]:
        """Extract the 'as of' date from the factsheet"""
        patterns = [
            r'as\s+(?:on|of)[:\s]+(\d{1,2}[-/]\w{3}[-/]\d{2,4})',
            r'data\s+as\s+(?:on|of)[:\s]+(\d{1,2}[-/]\w{3}[-/]\d{2,4})',
            r'(?:NAV|AUM)\s+as\s+(?:on|of)[:\s]+(\d{1,2}[-/]\w{3}[-/]\d{2,4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return datetime.now().strftime('%d-%b-%Y')
    
    def _check_completeness(self, fund: FundData) -> bool:
        """Check if fund data is complete enough to store"""
        required_fields = [
            fund.fund_name,
            fund.category,
        ]
        
        # Must have at least NAV or AUM
        has_financial = fund.nav is not None or fund.aum_cr is not None
        
        # Must have some holdings or sectors
        has_portfolio = len(fund.top_holdings) > 0 or len(fund.sector_allocation) > 0
        
        return all(required_fields) and (has_financial or has_portfolio)
    
    def print_summary(self):
        """Print extraction summary"""
        table = Table(title=f"{self.amc_code} Extraction Summary")
        
        table.add_column("Fund Name", style="cyan")
        table.add_column("Category", style="green")
        table.add_column("NAV", justify="right")
        table.add_column("AUM (Cr)", justify="right")
        table.add_column("Holdings", justify="right")
        table.add_column("Sectors", justify="right")
        table.add_column("Complete", justify="center")
        
        for fund in self.funds:
            table.add_row(
                fund.fund_name[:40],
                fund.sub_category or fund.category,
                f"₹{fund.nav:.2f}" if fund.nav else "N/A",
                f"₹{fund.aum_cr:,.0f}" if fund.aum_cr else "N/A",
                str(len(fund.top_holdings)),
                str(len(fund.sector_allocation)),
                "✅" if fund.data_complete else "❌",
            )
        
        console.print(table)


if __name__ == "__main__":
    # Test with a sample PDF
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        amc_code = sys.argv[2] if len(sys.argv) > 2 else "TEST"
        
        parser = MultiFundPDFParser(pdf_path, amc_code)
        funds = parser.parse()
        parser.print_summary()
        
        # Print first fund details
        if funds:
            console.print("\n[bold]Sample Fund Data:[/bold]")
            console.print(funds[0].to_dict())
