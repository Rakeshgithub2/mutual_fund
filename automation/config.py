"""
═══════════════════════════════════════════════════════════════════════════════
MUTUAL FUND FACTSHEET AUTOMATION ENGINE - CONFIGURATION
═══════════════════════════════════════════════════════════════════════════════
AMC Factsheet URLs and Configuration
"""

import os
from dotenv import load_dotenv

# Load from parent directory's .env (mutual-funds-backend/.env)
parent_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(parent_env)

# MongoDB Configuration - Use same DB as backend
MONGODB_URI = os.getenv('DATABASE_URL', 'mongodb://localhost:27017/mutualfunds')

# PDF Storage
PDF_STORAGE_PATH = os.path.join(os.path.dirname(__file__), 'pdfs')
EXTRACTED_DATA_PATH = os.path.join(os.path.dirname(__file__), 'extracted')

# Create directories
os.makedirs(PDF_STORAGE_PATH, exist_ok=True)
os.makedirs(EXTRACTED_DATA_PATH, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# AMC FACTSHEET SOURCES
# Each AMC has ONE master PDF containing ALL their funds
# ═══════════════════════════════════════════════════════════════════════════════

AMC_SOURCES = {
    "HDFC": {
        "name": "HDFC Mutual Fund",
        "factsheet_url": "https://www.hdfcfund.com/content/dam/abc/investor/investor-factsheet/HDFC_MF_Factsheet.pdf",
        "website": "https://www.hdfcfund.com",
        "multi_fund_pdf": True,
        "fund_separator_pattern": r"(?:Scheme Name|Fund Name)\s*[:\-]?\s*(.+?)(?:Direct|Regular)",
    },
    "ICICI": {
        "name": "ICICI Prudential Mutual Fund",
        "factsheet_url": "https://www.icicipruamc.com/downloads/others/Monthly-Factsheet.pdf",
        "website": "https://www.icicipruamc.com",
        "multi_fund_pdf": True,
        "fund_separator_pattern": r"ICICI\s+Prudential\s+(.+?)\s+Fund",
    },
    "SBI": {
        "name": "SBI Mutual Fund",
        "factsheet_url": "https://www.sbimf.com/docs/default-source/default-document-library/factsheet.pdf",
        "website": "https://www.sbimf.com",
        "multi_fund_pdf": True,
        "fund_separator_pattern": r"SBI\s+(.+?)\s+Fund",
    },
    "KOTAK": {
        "name": "Kotak Mahindra Mutual Fund",
        "factsheet_url": "https://www.kotakmf.com/Factsheet/MFFactSheet.pdf",
        "website": "https://www.kotakmf.com",
        "multi_fund_pdf": True,
        "fund_separator_pattern": r"Kotak\s+(.+?)\s+(?:Fund|Plan)",
    },
    "AXIS": {
        "name": "Axis Mutual Fund",
        "factsheet_url": "https://www.axismf.com/documents/factsheet/Axis-MF-Factsheet.pdf",
        "website": "https://www.axismf.com",
        "multi_fund_pdf": True,
        "fund_separator_pattern": r"Axis\s+(.+?)\s+Fund",
    },
    "NIPPON": {
        "name": "Nippon India Mutual Fund",
        "factsheet_url": "https://www.nipponindiamf.com/InvestorReports/Factsheet.pdf",
        "website": "https://www.nipponindiamf.com",
        "multi_fund_pdf": True,
        "fund_separator_pattern": r"Nippon\s+India\s+(.+?)\s+Fund",
    },
    "ADITYA_BIRLA": {
        "name": "Aditya Birla Sun Life Mutual Fund",
        "factsheet_url": "https://www.adityabirlacapital.com/mf/downloads/factsheet",
        "website": "https://www.adityabirlacapital.com",
        "multi_fund_pdf": True,
        "fund_separator_pattern": r"Aditya\s+Birla\s+Sun\s+Life\s+(.+?)\s+Fund",
    },
    "TATA": {
        "name": "Tata Mutual Fund",
        "factsheet_url": "https://www.tatamutualfund.com/documents/factsheet",
        "website": "https://www.tatamutualfund.com",
        "multi_fund_pdf": True,
        "fund_separator_pattern": r"Tata\s+(.+?)\s+Fund",
    },
    "UTI": {
        "name": "UTI Mutual Fund",
        "factsheet_url": "https://www.utimf.com/forms-and-downloads/factsheet",
        "website": "https://www.utimf.com",
        "multi_fund_pdf": True,
        "fund_separator_pattern": r"UTI\s+(.+?)\s+Fund",
    },
    "DSP": {
        "name": "DSP Mutual Fund",
        "factsheet_url": "https://www.dspim.com/literature/factsheet",
        "website": "https://www.dspim.com",
        "multi_fund_pdf": True,
        "fund_separator_pattern": r"DSP\s+(.+?)\s+Fund",
    },
    "MIRAE": {
        "name": "Mirae Asset Mutual Fund",
        "factsheet_url": "https://www.miraeassetmf.co.in/docs/factsheet",
        "website": "https://www.miraeassetmf.co.in",
        "multi_fund_pdf": True,
        "fund_separator_pattern": r"Mirae\s+Asset\s+(.+?)\s+Fund",
    },
    "MOTILAL": {
        "name": "Motilal Oswal Mutual Fund",
        "factsheet_url": "https://www.motilaloswalmf.com/downloads/factsheet",
        "website": "https://www.motilaloswalmf.com",
        "multi_fund_pdf": True,
        "fund_separator_pattern": r"Motilal\s+Oswal\s+(.+?)\s+Fund",
    },
    "PARAG_PARIKH": {
        "name": "PPFAS Mutual Fund",
        "factsheet_url": "https://amc.ppfas.com/downloads/factsheet",
        "website": "https://amc.ppfas.com",
        "multi_fund_pdf": True,
        "fund_separator_pattern": r"Parag\s+Parikh\s+(.+?)\s+Fund",
    },
    "CANARA": {
        "name": "Canara Robeco Mutual Fund",
        "factsheet_url": "https://www.canararobeco.com/downloads/factsheet",
        "website": "https://www.canararobeco.com",
        "multi_fund_pdf": True,
        "fund_separator_pattern": r"Canara\s+Robeco\s+(.+?)\s+Fund",
    },
    "FRANKLIN": {
        "name": "Franklin Templeton Mutual Fund",
        "factsheet_url": "https://www.franklintempletonindia.com/downloads/factsheet",
        "website": "https://www.franklintempletonindia.com",
        "multi_fund_pdf": True,
        "fund_separator_pattern": r"Franklin\s+India\s+(.+?)\s+Fund",
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUND CATEGORY MAPPING
# ═══════════════════════════════════════════════════════════════════════════════

CATEGORY_MAPPING = {
    # Keywords -> (category, subCategory)
    "large cap": ("equity", "large cap"),
    "largecap": ("equity", "large cap"),
    "large-cap": ("equity", "large cap"),
    "mid cap": ("equity", "mid cap"),
    "midcap": ("equity", "mid cap"),
    "mid-cap": ("equity", "mid cap"),
    "small cap": ("equity", "small cap"),
    "smallcap": ("equity", "small cap"),
    "small-cap": ("equity", "small cap"),
    "flexi cap": ("equity", "flexi cap"),
    "flexicap": ("equity", "flexi cap"),
    "flexi-cap": ("equity", "flexi cap"),
    "multi cap": ("equity", "multi cap"),
    "multicap": ("equity", "multi cap"),
    "multi-cap": ("equity", "multi cap"),
    "focused": ("equity", "focused fund"),
    "elss": ("equity", "elss"),
    "tax saver": ("equity", "elss"),
    "dividend yield": ("equity", "dividend yield"),
    "value": ("equity", "value fund"),
    "contra": ("equity", "contra fund"),
    "banking": ("equity", "sectoral - banking"),
    "technology": ("equity", "sectoral - technology"),
    "pharma": ("equity", "sectoral - pharma"),
    "infrastructure": ("equity", "sectoral - infrastructure"),
    "consumption": ("equity", "sectoral - consumption"),
    "liquid": ("debt", "liquid"),
    "overnight": ("debt", "overnight"),
    "ultra short": ("debt", "ultra short duration"),
    "money market": ("debt", "money market"),
    "short duration": ("debt", "short duration"),
    "medium duration": ("debt", "medium duration"),
    "long duration": ("debt", "long duration"),
    "corporate bond": ("debt", "corporate bond"),
    "credit risk": ("debt", "credit risk"),
    "gilt": ("debt", "gilt"),
    "dynamic bond": ("debt", "dynamic bond"),
    "banking psu": ("debt", "banking and psu"),
    "floating rate": ("debt", "floater"),
    "aggressive hybrid": ("hybrid", "aggressive hybrid"),
    "balanced advantage": ("hybrid", "balanced advantage"),
    "conservative hybrid": ("hybrid", "conservative hybrid"),
    "equity savings": ("hybrid", "equity savings"),
    "multi asset": ("hybrid", "multi asset allocation"),
    "arbitrage": ("hybrid", "arbitrage"),
    "retirement": ("solution oriented", "retirement fund"),
    "children": ("solution oriented", "children's fund"),
    "gold": ("commodity", "gold"),
    "silver": ("commodity", "silver"),
    "commodity": ("commodity", "commodity"),
    "index fund": ("equity", "index fund"),
    "index": ("equity", "index fund"),
    "nifty 50": ("equity", "index fund - nifty 50"),
    "sensex": ("equity", "index fund - sensex"),
    "nifty next 50": ("equity", "index fund - nifty next 50"),
}

# ═══════════════════════════════════════════════════════════════════════════════
# SECTOR STANDARDIZATION
# ═══════════════════════════════════════════════════════════════════════════════

SECTOR_MAPPING = {
    # Raw sector name patterns -> Standardized name
    "financial": "Financial Services",
    "banking": "Financial Services",
    "bank": "Financial Services",
    "nbfc": "Financial Services",
    "insurance": "Financial Services",
    "information technology": "Information Technology",
    "it": "Information Technology",
    "software": "Information Technology",
    "technology": "Information Technology",
    "consumer goods": "Consumer Goods",
    "fmcg": "Consumer Goods",
    "consumer staples": "Consumer Goods",
    "automobile": "Automobile",
    "auto": "Automobile",
    "automotive": "Automobile",
    "healthcare": "Healthcare",
    "pharma": "Healthcare",
    "pharmaceutical": "Healthcare",
    "oil": "Oil & Gas",
    "gas": "Oil & Gas",
    "energy": "Oil & Gas",
    "petroleum": "Oil & Gas",
    "metal": "Metals & Mining",
    "mining": "Metals & Mining",
    "steel": "Metals & Mining",
    "cement": "Construction Materials",
    "construction material": "Construction Materials",
    "construction": "Construction",
    "infrastructure": "Construction",
    "real estate": "Real Estate",
    "realty": "Real Estate",
    "telecom": "Telecommunication",
    "telecommunication": "Telecommunication",
    "power": "Power",
    "utilities": "Power",
    "capital goods": "Capital Goods",
    "industrial": "Capital Goods",
    "chemical": "Chemicals",
    "chemicals": "Chemicals",
    "textile": "Textiles",
    "consumer durables": "Consumer Durables",
    "media": "Media & Entertainment",
    "entertainment": "Media & Entertainment",
    "agriculture": "Agriculture",
    "fertilizer": "Agriculture",
    "services": "Services",
    "logistics": "Services",
    "retail": "Retail",
    "others": "Others",
    "miscellaneous": "Others",
    "diversified": "Diversified",
}

# ═══════════════════════════════════════════════════════════════════════════════
# EXTRACTION PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════

EXTRACTION_PATTERNS = {
    # Fund Manager extraction
    "fund_manager": [
        r"Fund\s+Manager[:\s]+([A-Za-z\s\.]+?)(?:Managing|Experience|Since|\n)",
        r"Managed\s+by[:\s]+([A-Za-z\s\.]+?)(?:\n|,)",
        r"Fund\s+Manager\s*:\s*([A-Za-z\s\.]+)",
    ],
    
    # AUM extraction
    "aum": [
        r"AUM[:\s]+(?:Rs\.?|₹|INR)?\s*([0-9,\.]+)\s*(?:Cr|Crore|Lakh)",
        r"Assets\s+Under\s+Management[:\s]+(?:Rs\.?|₹)?\s*([0-9,\.]+)",
        r"Net\s+Assets[:\s]+(?:Rs\.?|₹)?\s*([0-9,\.]+)",
    ],
    
    # Expense Ratio extraction
    "expense_ratio": [
        r"Expense\s+Ratio[:\s]+([0-9\.]+)\s*%",
        r"Total\s+Expense\s+Ratio[:\s]+([0-9\.]+)\s*%",
        r"TER[:\s]+([0-9\.]+)\s*%",
        r"Direct[:\s]+([0-9\.]+)\s*%",
    ],
    
    # NAV extraction
    "nav": [
        r"NAV[:\s]+(?:Rs\.?|₹)?\s*([0-9,\.]+)",
        r"Net\s+Asset\s+Value[:\s]+(?:Rs\.?|₹)?\s*([0-9,\.]+)",
    ],
    
    # Benchmark extraction
    "benchmark": [
        r"Benchmark[:\s]+(.+?)(?:\n|Scheme)",
        r"Index[:\s]+(.+?)(?:\n|TRI)",
    ],
    
    # Launch Date extraction
    "launch_date": [
        r"(?:Inception|Launch)\s+Date[:\s]+(\d{1,2}[-/]\w{3}[-/]\d{2,4})",
        r"(?:Inception|Launch)\s+Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        r"(?:Started|Launched)[:\s]+(\d{1,2}[-/]\w{3}[-/]\d{2,4})",
    ],
    
    # Returns extraction (table format)
    "returns_1y": [
        r"1\s*(?:Yr|Year|Y)[:\s]+(-?[0-9\.]+)\s*%?",
        r"1Y[:\s]+(-?[0-9\.]+)",
    ],
    "returns_3y": [
        r"3\s*(?:Yr|Year|Y)[:\s]+(-?[0-9\.]+)\s*%?",
        r"3Y[:\s]+(-?[0-9\.]+)",
    ],
    "returns_5y": [
        r"5\s*(?:Yr|Year|Y)[:\s]+(-?[0-9\.]+)\s*%?",
        r"5Y[:\s]+(-?[0-9\.]+)",
    ],
}

# ═══════════════════════════════════════════════════════════════════════════════
# TABLE DETECTION KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════════

HOLDINGS_TABLE_KEYWORDS = [
    "top holdings",
    "portfolio holdings",
    "top 10 holdings",
    "stock holdings",
    "company name",
    "% to net assets",
    "% of net assets",
    "percentage",
    "holding",
]

SECTOR_TABLE_KEYWORDS = [
    "sector allocation",
    "sector wise",
    "sector distribution",
    "industry allocation",
    "sectoral allocation",
]

RETURNS_TABLE_KEYWORDS = [
    "performance",
    "returns",
    "cagr",
    "scheme returns",
    "absolute returns",
    "1 year",
    "3 year",
    "5 year",
]
