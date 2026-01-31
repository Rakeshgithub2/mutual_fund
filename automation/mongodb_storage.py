"""
═══════════════════════════════════════════════════════════════════════════════
MONGODB STORAGE ENGINE
═══════════════════════════════════════════════════════════════════════════════
Stores extracted fund data in MongoDB
Handles: Upserts, linking, validation, no duplicates
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError
from rich.console import Console
from rich.table import Table

from config import MONGODB_URI
from pdf_parser import FundData

console = Console()


class MongoDBStorage:
    """
    MongoDB storage engine for mutual fund data
    
    Collections:
    - funds: Main fund master data
    - fund_holdings: Quarterly portfolio holdings
    - fund_managers: Fund manager information
    - fund_returns: Historical returns data
    """
    
    def __init__(self, uri: str = None):
        self.uri = uri or MONGODB_URI
        self.client = None
        self.db = None
        
    def connect(self):
        """Establish MongoDB connection"""
        try:
            self.client = MongoClient(self.uri)
            # Extract database name from URI
            db_name = self.uri.split('/')[-1].split('?')[0] or 'mutualfunds'
            self.db = self.client[db_name]
            
            # Test connection
            self.client.admin.command('ping')
            console.print(f"[green]✅ Connected to MongoDB: {db_name}[/green]")
            
        except Exception as e:
            console.print(f"[red]❌ MongoDB connection failed: {e}[/red]")
            raise
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            console.print("[dim]🔌 MongoDB disconnected[/dim]")
    
    def _generate_scheme_code(self, fund_name: str, amc: str) -> str:
        """Generate a unique scheme code from fund name and AMC"""
        import hashlib
        
        # Create a deterministic ID
        base = f"{amc.lower()}_{fund_name.lower()}"
        base = ''.join(c for c in base if c.isalnum() or c == '_')
        
        # Add short hash for uniqueness
        hash_suffix = hashlib.md5(base.encode()).hexdigest()[:6]
        
        return f"{base[:50]}_{hash_suffix}"
    
    def _clean_for_storage(self, data: Dict) -> Dict:
        """
        Clean data before storage
        - Remove None/null values
        - Validate percentages
        - Ensure no NA strings
        """
        cleaned = {}
        
        for key, value in data.items():
            # Skip None values
            if value is None:
                continue
            
            # Skip empty strings
            if isinstance(value, str) and not value.strip():
                continue
            
            # Skip "NA" or "N/A" strings
            if isinstance(value, str) and value.upper() in ['NA', 'N/A', 'NULL', 'NONE']:
                continue
            
            # Handle nested dicts
            if isinstance(value, dict):
                cleaned_nested = self._clean_for_storage(value)
                if cleaned_nested:  # Only add if not empty
                    cleaned[key] = cleaned_nested
            
            # Handle lists
            elif isinstance(value, list):
                cleaned_list = []
                for item in value:
                    if isinstance(item, dict):
                        cleaned_item = self._clean_for_storage(item)
                        if cleaned_item:
                            cleaned_list.append(cleaned_item)
                    elif item is not None:
                        cleaned_list.append(item)
                if cleaned_list:
                    cleaned[key] = cleaned_list
            
            else:
                cleaned[key] = value
        
        return cleaned
    
    def store_fund(self, fund_data: FundData) -> bool:
        """
        Store or update a single fund
        Uses upsert to avoid duplicates
        """
        if not self.db:
            self.connect()
        
        try:
            # Generate scheme code
            scheme_code = self._generate_scheme_code(fund_data.fund_name, fund_data.amc)
            
            # Prepare fund document
            fund_doc = fund_data.to_dict()
            fund_doc['schemeCode'] = scheme_code
            fund_doc['schemeName'] = fund_data.fund_name
            fund_doc['updatedAt'] = datetime.utcnow()
            
            # Clean data
            fund_doc = self._clean_for_storage(fund_doc)
            
            # Upsert into funds collection
            result = self.db.funds.update_one(
                {'schemeCode': scheme_code},
                {'$set': fund_doc, '$setOnInsert': {'createdAt': datetime.utcnow()}},
                upsert=True
            )
            
            # Store holdings separately if present
            if fund_data.top_holdings:
                self._store_holdings(scheme_code, fund_data)
            
            return result.acknowledged
            
        except Exception as e:
            console.print(f"[red]❌ Failed to store {fund_data.fund_name}: {e}[/red]")
            return False
    
    def _store_holdings(self, scheme_code: str, fund_data: FundData):
        """Store holdings in separate collection"""
        holdings_doc = {
            'schemeCode': scheme_code,
            'schemeName': fund_data.fund_name,
            'asOfDate': datetime.strptime(fund_data.as_of_date, '%d-%b-%Y') if fund_data.as_of_date else datetime.utcnow(),
            'quarter': self._get_quarter(),
            'year': datetime.now().year,
            'topHoldings': [
                {
                    'name': h['name'],
                    'percentage': h['percentage'],
                }
                for h in fund_data.top_holdings
            ],
            'sectorAllocation': [
                {
                    'sector': s['sector'],
                    'percentage': s['percentage'],
                }
                for s in fund_data.sector_allocation
            ],
            'marketCapDistribution': fund_data.market_cap,
            'numberOfHoldings': len(fund_data.top_holdings),
            'dataComplete': fund_data.data_complete,
            'updatedAt': datetime.utcnow(),
        }
        
        # Clean before storage
        holdings_doc = self._clean_for_storage(holdings_doc)
        
        # Upsert - one record per fund per quarter
        self.db.fund_holdings.update_one(
            {
                'schemeCode': scheme_code,
                'quarter': holdings_doc['quarter'],
                'year': holdings_doc['year'],
            },
            {'$set': holdings_doc, '$setOnInsert': {'createdAt': datetime.utcnow()}},
            upsert=True
        )
    
    def _get_quarter(self) -> str:
        """Get current quarter string"""
        month = datetime.now().month
        if month <= 3:
            return 'Q4'
        elif month <= 6:
            return 'Q1'
        elif month <= 9:
            return 'Q2'
        else:
            return 'Q3'
    
    def store_funds_bulk(self, funds: List[FundData]) -> Dict[str, int]:
        """
        Store multiple funds in bulk
        
        Returns:
            Dict with counts: inserted, updated, failed
        """
        if not self.db:
            self.connect()
        
        stats = {'inserted': 0, 'updated': 0, 'failed': 0}
        operations = []
        holdings_operations = []
        
        console.print(f"\n[cyan]💾 Storing {len(funds)} funds in MongoDB...[/cyan]")
        
        for fund_data in funds:
            try:
                scheme_code = self._generate_scheme_code(fund_data.fund_name, fund_data.amc)
                
                # Prepare fund document
                fund_doc = fund_data.to_dict()
                fund_doc['schemeCode'] = scheme_code
                fund_doc['schemeName'] = fund_data.fund_name
                fund_doc['updatedAt'] = datetime.utcnow()
                fund_doc = self._clean_for_storage(fund_doc)
                
                # Add to bulk operations
                operations.append(
                    UpdateOne(
                        {'schemeCode': scheme_code},
                        {'$set': fund_doc, '$setOnInsert': {'createdAt': datetime.utcnow()}},
                        upsert=True
                    )
                )
                
                # Prepare holdings
                if fund_data.top_holdings or fund_data.sector_allocation:
                    holdings_doc = {
                        'schemeCode': scheme_code,
                        'schemeName': fund_data.fund_name,
                        'asOfDate': datetime.utcnow(),
                        'quarter': self._get_quarter(),
                        'year': datetime.now().year,
                        'topHoldings': fund_data.top_holdings,
                        'sectorAllocation': fund_data.sector_allocation,
                        'marketCapDistribution': fund_data.market_cap,
                        'numberOfHoldings': len(fund_data.top_holdings),
                        'dataComplete': fund_data.data_complete,
                        'updatedAt': datetime.utcnow(),
                    }
                    holdings_doc = self._clean_for_storage(holdings_doc)
                    
                    holdings_operations.append(
                        UpdateOne(
                            {
                                'schemeCode': scheme_code,
                                'quarter': holdings_doc['quarter'],
                                'year': holdings_doc['year'],
                            },
                            {'$set': holdings_doc, '$setOnInsert': {'createdAt': datetime.utcnow()}},
                            upsert=True
                        )
                    )
                
            except Exception as e:
                console.print(f"[red]❌ Error preparing {fund_data.fund_name}: {e}[/red]")
                stats['failed'] += 1
        
        # Execute bulk operations
        if operations:
            try:
                result = self.db.funds.bulk_write(operations, ordered=False)
                stats['inserted'] = result.upserted_count
                stats['updated'] = result.modified_count
            except BulkWriteError as e:
                console.print(f"[yellow]⚠️ Some bulk writes failed: {e.details}[/yellow]")
                stats['failed'] += len(e.details.get('writeErrors', []))
        
        # Execute holdings bulk operations
        if holdings_operations:
            try:
                self.db.fund_holdings.bulk_write(holdings_operations, ordered=False)
            except BulkWriteError as e:
                console.print(f"[yellow]⚠️ Some holdings writes failed[/yellow]")
        
        console.print(f"[green]✅ Stored: {stats['inserted']} new, {stats['updated']} updated, {stats['failed']} failed[/green]")
        
        return stats
    
    def get_fund_by_name(self, name: str) -> Optional[Dict]:
        """Find a fund by name (fuzzy match)"""
        if not self.db:
            self.connect()
        
        return self.db.funds.find_one({
            'schemeName': {'$regex': name, '$options': 'i'}
        })
    
    def get_all_funds_by_amc(self, amc_name: str) -> List[Dict]:
        """Get all funds for an AMC"""
        if not self.db:
            self.connect()
        
        return list(self.db.funds.find({
            'amc.name': {'$regex': amc_name, '$options': 'i'}
        }))
    
    def get_fund_holdings(self, scheme_code: str) -> Optional[Dict]:
        """Get latest holdings for a fund"""
        if not self.db:
            self.connect()
        
        return self.db.fund_holdings.find_one(
            {'schemeCode': scheme_code},
            sort=[('asOfDate', -1)]
        )
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        if self.client is None:
            self.connect()
        
        return {
            'total_funds': self.db.funds.count_documents({}),
            'funds_with_holdings': self.db.funds.count_documents({'topHoldings.0': {'$exists': True}}),
            'funds_with_sectors': self.db.funds.count_documents({'sectorAllocation.0': {'$exists': True}}),
            'holdings_records': self.db.fund_holdings.count_documents({}),
            'complete_funds': self.db.funds.count_documents({'dataComplete': True}),
        }
    
    def print_stats(self):
        """Print database statistics"""
        if self.client is None:
            console.print("[yellow]⚠️ Not connected to database[/yellow]")
            return
        
        stats = self.get_stats()
        
        table = Table(title="Database Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", justify="right", style="green")
        
        table.add_row("Total Funds", f"{stats['total_funds']:,}")
        table.add_row("Funds with Holdings", f"{stats['funds_with_holdings']:,}")
        table.add_row("Funds with Sectors", f"{stats['funds_with_sectors']:,}")
        table.add_row("Holdings Records", f"{stats['holdings_records']:,}")
        table.add_row("Complete Funds", f"{stats['complete_funds']:,}")
        
        console.print(table)


if __name__ == "__main__":
    # Test storage
    storage = MongoDBStorage()
    storage.connect()
    storage.print_stats()
    storage.disconnect()
