"""
═══════════════════════════════════════════════════════════════════════════════
MASTER AUTOMATION ENGINE
═══════════════════════════════════════════════════════════════════════════════
Complete end-to-end automation for:
1. Downloading AMC factsheet PDFs
2. Parsing multi-fund PDFs
3. Extracting holdings, sectors, returns
4. Storing clean data in MongoDB

Run monthly via scheduler or manually
"""

import os
import sys
import argparse
from datetime import datetime
from typing import List, Optional, Dict
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
import schedule
import time

from config import AMC_SOURCES, PDF_STORAGE_PATH
from pdf_downloader import PDFDownloader
from pdf_parser import MultiFundPDFParser, FundData
from mongodb_storage import MongoDBStorage

console = Console()


class FactsheetAutomation:
    """
    Master automation engine for mutual fund data extraction
    
    Flow:
    1. Download PDFs from AMC websites
    2. Parse each PDF (handles multi-fund PDFs)
    3. Extract and clean data
    4. Store in MongoDB
    5. Generate report
    """
    
    def __init__(self):
        self.downloader = PDFDownloader()
        self.storage = MongoDBStorage()
        self.all_funds: List[FundData] = []
        self.stats = {
            'pdfs_downloaded': 0,
            'pdfs_parsed': 0,
            'funds_extracted': 0,
            'funds_stored': 0,
            'funds_failed': 0,
            'start_time': None,
            'end_time': None,
        }
    
    def run(self, amc_list: Optional[List[str]] = None, skip_download: bool = False):
        """
        Run the complete automation pipeline
        
        Args:
            amc_list: Optional list of AMC codes to process. Processes all if None.
            skip_download: Skip PDF download, use existing files
        """
        self.stats['start_time'] = datetime.now()
        
        console.print(Panel.fit(
            "[bold cyan]🚀 MUTUAL FUND FACTSHEET AUTOMATION[/bold cyan]\n"
            f"[dim]Started: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
            border_style="cyan"
        ))
        
        try:
            # Step 1: Download PDFs
            if not skip_download:
                downloaded_pdfs = self._download_pdfs(amc_list)
            else:
                downloaded_pdfs = self._get_existing_pdfs(amc_list)
            
            self.stats['pdfs_downloaded'] = len(downloaded_pdfs)
            
            if not downloaded_pdfs:
                console.print("[yellow]⚠️ No PDFs to process[/yellow]")
                return
            
            # Step 2: Parse PDFs and extract funds
            self._parse_pdfs(downloaded_pdfs)
            
            # Step 3: Store in MongoDB
            self._store_funds()
            
            # Step 4: Generate report
            self._generate_report()
            
        except Exception as e:
            console.print(f"[red]❌ Automation failed: {e}[/red]")
            import traceback
            traceback.print_exc()
        
        finally:
            self.stats['end_time'] = datetime.now()
            self.storage.disconnect()
    
    def _download_pdfs(self, amc_list: Optional[List[str]]) -> Dict[str, str]:
        """Download factsheet PDFs"""
        console.print("\n[bold]📥 Step 1: Downloading PDFs[/bold]")
        return self.downloader.download_all(amc_list)
    
    def _get_existing_pdfs(self, amc_list: Optional[List[str]]) -> Dict[str, str]:
        """Get existing PDF files instead of downloading"""
        console.print("\n[bold]📂 Step 1: Using existing PDFs[/bold]")
        
        existing = {}
        
        for amc_code in (amc_list or AMC_SOURCES.keys()):
            # Find most recent PDF for this AMC
            pattern = f"{amc_code.lower()}_factsheet_"
            
            matching_files = [
                f for f in os.listdir(PDF_STORAGE_PATH)
                if f.startswith(pattern) and f.endswith('.pdf')
            ]
            
            if matching_files:
                # Get most recent
                matching_files.sort(reverse=True)
                filepath = os.path.join(PDF_STORAGE_PATH, matching_files[0])
                existing[amc_code] = filepath
                console.print(f"[green]   ✅ Found: {matching_files[0]}[/green]")
            else:
                console.print(f"[yellow]   ⚠️ No PDF found for {amc_code}[/yellow]")
        
        return existing
    
    def _parse_pdfs(self, pdfs: Dict[str, str]):
        """Parse all downloaded PDFs"""
        console.print("\n[bold]📄 Step 2: Parsing PDFs[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task("Parsing PDFs...", total=len(pdfs))
            
            for amc_code, pdf_path in pdfs.items():
                try:
                    parser = MultiFundPDFParser(pdf_path, amc_code)
                    funds = parser.parse()
                    
                    if funds:
                        self.all_funds.extend(funds)
                        self.stats['pdfs_parsed'] += 1
                        console.print(f"[green]   ✅ {amc_code}: {len(funds)} funds extracted[/green]")
                    else:
                        console.print(f"[yellow]   ⚠️ {amc_code}: No funds extracted[/yellow]")
                    
                except Exception as e:
                    console.print(f"[red]   ❌ {amc_code}: Failed - {e}[/red]")
                
                progress.update(task, advance=1)
        
        self.stats['funds_extracted'] = len(self.all_funds)
        console.print(f"\n[bold green]📊 Total funds extracted: {len(self.all_funds)}[/bold green]")
    
    def _store_funds(self):
        """Store extracted funds in MongoDB"""
        console.print("\n[bold]💾 Step 3: Storing in MongoDB[/bold]")
        
        if not self.all_funds:
            console.print("[yellow]No funds to store[/yellow]")
            return
        
        self.storage.connect()
        
        # Filter only complete funds (no NA data)
        valid_funds = [f for f in self.all_funds if f.data_complete]
        
        console.print(f"[dim]   Valid funds (complete data): {len(valid_funds)}/{len(self.all_funds)}[/dim]")
        
        if valid_funds:
            result = self.storage.store_funds_bulk(valid_funds)
            self.stats['funds_stored'] = result['inserted'] + result['updated']
            self.stats['funds_failed'] = result['failed']
    
    def _generate_report(self):
        """Generate final report"""
        duration = (self.stats['end_time'] or datetime.now()) - self.stats['start_time']
        
        console.print(Panel.fit(
            f"""[bold green]✅ AUTOMATION COMPLETE[/bold green]
            
[cyan]Duration:[/cyan] {duration.total_seconds():.1f} seconds

[cyan]PDFs:[/cyan]
  • Downloaded: {self.stats['pdfs_downloaded']}
  • Parsed: {self.stats['pdfs_parsed']}

[cyan]Funds:[/cyan]
  • Extracted: {self.stats['funds_extracted']}
  • Stored: {self.stats['funds_stored']}
  • Failed: {self.stats['funds_failed']}
  
[cyan]Next Run:[/cyan] 1st of next month
""",
            title="📊 Automation Report",
            border_style="green"
        ))
        
        # Print database stats
        self.storage.print_stats()


def run_monthly_automation():
    """Scheduled monthly automation"""
    console.print("\n[bold cyan]⏰ Running scheduled monthly automation...[/bold cyan]")
    
    automation = FactsheetAutomation()
    automation.run()
    
    console.print("[green]✅ Monthly automation completed[/green]")


def setup_scheduler():
    """Setup monthly scheduler"""
    # Run on 1st of every month at 3 AM
    schedule.every().month.at("03:00").do(run_monthly_automation)
    
    console.print("[cyan]📅 Scheduler configured: 1st of every month at 3 AM[/cyan]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    
    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Mutual Fund Factsheet Automation Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run for all AMCs
  python main.py --amc HDFC KOTAK   # Run for specific AMCs
  python main.py --skip-download    # Use existing PDFs
  python main.py --scheduler        # Start monthly scheduler
  python main.py --stats            # Show database stats only
        """
    )
    
    parser.add_argument(
        '--amc',
        nargs='+',
        help='Specific AMC codes to process (e.g., HDFC KOTAK SBI)'
    )
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help='Skip downloading, use existing PDFs'
    )
    parser.add_argument(
        '--scheduler',
        action='store_true',
        help='Start the monthly scheduler'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show database statistics only'
    )
    parser.add_argument(
        '--list-amcs',
        action='store_true',
        help='List all configured AMCs'
    )
    
    args = parser.parse_args()
    
    # List AMCs
    if args.list_amcs:
        console.print("\n[bold]Configured AMCs:[/bold]")
        for code, config in AMC_SOURCES.items():
            console.print(f"  [cyan]{code}[/cyan]: {config['name']}")
        return
    
    # Show stats only
    if args.stats:
        storage = MongoDBStorage()
        storage.connect()
        storage.print_stats()
        storage.disconnect()
        return
    
    # Start scheduler
    if args.scheduler:
        setup_scheduler()
        return
    
    # Run automation
    automation = FactsheetAutomation()
    automation.run(
        amc_list=args.amc,
        skip_download=args.skip_download
    )


if __name__ == "__main__":
    main()
