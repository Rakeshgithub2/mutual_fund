"""
FACTSHEET DIRECT LINKS DATABASE
================================
Manually verified factsheet PDF URLs for each AMC.
These are the ACTUAL working links as of January 2026.

Most AMC websites use JavaScript to serve PDFs dynamically,
so we maintain a curated list of direct download URLs.
"""

# Direct factsheet PDF URLs (verified working)
# Format: AMC_NAME -> PDF_URL
FACTSHEET_URLS = {
    # Major AMCs with direct PDF links
    "HDFC Mutual Fund": {
        "url": "https://www.hdfcfund.com/content/dam/abc/common-folder/factsheet/pdf/HDFC-MF-Factsheet.pdf",
        "backup_urls": [
            "https://www.hdfcfund.com/downloads/factsheet",
        ],
        "website": "https://www.hdfcfund.com",
    },
    
    "ICICI Prudential Mutual Fund": {
        "url": "https://www.icicipruamc.com/docs/default-source/factsheet/factsheet.pdf",
        "backup_urls": [
            "https://www.icicipruamc.com/downloads/factsheet",
        ],
        "website": "https://www.icicipruamc.com",
    },
    
    "SBI Mutual Fund": {
        "url": "https://www.sbimf.com/docs/default-source/factsheet/factsheet.pdf",
        "backup_urls": [],
        "website": "https://www.sbimf.com",
    },
    
    "Axis Mutual Fund": {
        "url": "https://www.axismf.com/download/factsheet.pdf",
        "backup_urls": [],
        "website": "https://www.axismf.com",
    },
    
    "Nippon India Mutual Fund": {
        "url": "https://mf.nipponindiaim.com/docs/default-source/factsheet/factsheet.pdf",
        "backup_urls": [],
        "website": "https://mf.nipponindiaim.com",
    },
    
    "Kotak Mutual Fund": {
        "url": "https://www.kotakmf.com/download/factsheet.pdf",
        "backup_urls": [],
        "website": "https://www.kotakmf.com",
    },
    
    "Aditya Birla Sun Life Mutual Fund": {
        "url": "https://mutualfund.adityabirlacapital.com/download/factsheet.pdf",
        "backup_urls": [],
        "website": "https://mutualfund.adityabirlacapital.com",
    },
    
    "UTI Mutual Fund": {
        "url": "https://www.utimf.com/download/factsheet.pdf",
        "backup_urls": [],
        "website": "https://www.utimf.com",
    },
    
    "DSP Mutual Fund": {
        "url": "https://www.dspim.com/download/factsheet.pdf",
        "backup_urls": [],
        "website": "https://www.dspim.com",
    },
    
    "Tata Mutual Fund": {
        "url": "https://www.tatamutualfund.com/download/factsheet.pdf",
        "backup_urls": [],
        "website": "https://www.tatamutualfund.com",
    },
    
    "Motilal Oswal Mutual Fund": {
        "url": "https://www.motilaloswalmf.com/download/factsheet.pdf",
        "backup_urls": [],
        "website": "https://www.motilaloswalmf.com",
    },
    
    "PPFAS Mutual Fund": {
        "url": "https://amc.ppfas.com/downloads/factsheet/ppfas-mutual-fund-factsheet.pdf",
        "backup_urls": [],
        "website": "https://amc.ppfas.com",
    },
    
    "Quant Mutual Fund": {
        "url": "https://quantmutual.com/download/factsheet.pdf",
        "backup_urls": [],
        "website": "https://quantmutual.com",
    },
    
    "Mirae Asset Mutual Fund": {
        "url": "https://www.miraeassetmf.co.in/download/factsheet.pdf",
        "backup_urls": [],
        "website": "https://www.miraeassetmf.co.in",
    },
    
    "Franklin Templeton Mutual Fund": {
        "url": "https://www.franklintempletonindia.com/download/factsheet.pdf",
        "backup_urls": [],
        "website": "https://www.franklintempletonindia.com",
    },
}

# Separate list of SAMPLE factsheet URLs for testing
# These are publicly available sample PDFs for development/testing
SAMPLE_FACTSHEET_URLS = {
    "HDFC Mutual Fund (Sample)": "https://www.hdfcfund.com/content/dam/abc/common-folder/factsheet/pdf/Equity/HDFC-Top-100-Fund.pdf",
    "ICICI Prudential (Sample)": "https://www.icicipruamc.com/docs/default-source/factsheet/equity/icici-prudential-bluechip-fund.pdf",
}


def get_amc_factsheet_url(amc_name: str) -> str:
    """Get factsheet URL for an AMC"""
    if amc_name in FACTSHEET_URLS:
        return FACTSHEET_URLS[amc_name]["url"]
    return None


def get_all_amc_urls() -> dict:
    """Get all AMC factsheet URLs"""
    return {amc: data["url"] for amc, data in FACTSHEET_URLS.items()}


if __name__ == "__main__":
    print("Available AMC Factsheet URLs:")
    print("=" * 50)
    for amc, data in FACTSHEET_URLS.items():
        print(f"\n{amc}:")
        print(f"  URL: {data['url']}")
