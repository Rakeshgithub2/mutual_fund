"""
═══════════════════════════════════════════════════════════════════════════════
PDF DOWNLOADER
═══════════════════════════════════════════════════════════════════════════════
Downloads factsheet PDFs from AMC websites
"""

import os
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from tenacity import retry, stop_after_attempt, wait_exponential
from fake_useragent import UserAgent

from config import AMC_SOURCES, PDF_STORAGE_PATH

console = Console()

class PDFDownloader:
    """Downloads AMC factsheet PDFs"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/pdf,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        })
    
    def get_headers(self) -> Dict[str, str]:
        """Get randomized headers to avoid blocking"""
        return {
            'User-Agent': self.ua.random,
            'Referer': 'https://www.google.com/',
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def download_pdf(self, url: str, amc_code: str) -> Optional[str]:
        """
        Download a PDF from URL
        
        Args:
            url: PDF download URL
            amc_code: AMC identifier (e.g., 'HDFC', 'KOTAK')
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            console.print(f"[cyan]📥 Downloading {amc_code} factsheet...[/cyan]")
            
            # Create filename with date
            today = datetime.now().strftime('%Y-%m')
            filename = f"{amc_code.lower()}_factsheet_{today}.pdf"
            filepath = os.path.join(PDF_STORAGE_PATH, filename)
            
            # Skip if already downloaded this month
            if os.path.exists(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time.month == datetime.now().month:
                    console.print(f"[yellow]📄 {amc_code} already downloaded this month[/yellow]")
                    return filepath
            
            # Download
            response = self.session.get(
                url,
                headers=self.get_headers(),
                timeout=60,
                stream=True
            )
            response.raise_for_status()
            
            # Verify it's a PDF
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower() and not url.endswith('.pdf'):
                console.print(f"[red]❌ {amc_code}: Not a PDF file[/red]")
                return None
            
            # Save file
            total_size = int(response.headers.get('content-length', 0))
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            ) as progress:
                task = progress.add_task(f"Downloading {amc_code}...", total=total_size)
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))
            
            console.print(f"[green]✅ {amc_code} downloaded: {filepath}[/green]")
            return filepath
            
        except requests.exceptions.RequestException as e:
            console.print(f"[red]❌ Failed to download {amc_code}: {e}[/red]")
            return None
        except Exception as e:
            console.print(f"[red]❌ Error downloading {amc_code}: {e}[/red]")
            return None
    
    def download_all(self, amc_list: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Download all AMC factsheets
        
        Args:
            amc_list: Optional list of AMC codes to download. Downloads all if None.
            
        Returns:
            Dict mapping AMC code to downloaded file path
        """
        downloaded = {}
        
        sources = AMC_SOURCES
        if amc_list:
            sources = {k: v for k, v in AMC_SOURCES.items() if k in amc_list}
        
        console.print(f"\n[bold cyan]📦 Downloading {len(sources)} AMC factsheets[/bold cyan]\n")
        
        for amc_code, config in sources.items():
            url = config.get('factsheet_url')
            if url:
                filepath = self.download_pdf(url, amc_code)
                if filepath:
                    downloaded[amc_code] = filepath
        
        console.print(f"\n[bold green]✅ Downloaded {len(downloaded)}/{len(sources)} factsheets[/bold green]\n")
        return downloaded
    
    def cleanup_old_pdfs(self, keep_months: int = 3):
        """Remove PDFs older than specified months"""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=keep_months * 30)
        
        for file in Path(PDF_STORAGE_PATH).glob("*.pdf"):
            file_time = datetime.fromtimestamp(file.stat().st_mtime)
            if file_time < cutoff:
                file.unlink()
                console.print(f"[yellow]🗑️ Removed old file: {file.name}[/yellow]")


if __name__ == "__main__":
    downloader = PDFDownloader()
    
    # Download specific AMCs or all
    # downloaded = downloader.download_all(['HDFC', 'KOTAK', 'SBI'])
    downloaded = downloader.download_all()
    
    print("\nDownloaded files:")
    for amc, path in downloaded.items():
        print(f"  {amc}: {path}")
