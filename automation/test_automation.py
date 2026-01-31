"""
═══════════════════════════════════════════════════════════════════════════════
TEST SCRIPT - Quick test of automation components
═══════════════════════════════════════════════════════════════════════════════
Run this to verify all components work correctly
"""

import sys
import os
from datetime import datetime

# Test imports
print("Testing imports...")

try:
    from config import AMC_SOURCES, PDF_STORAGE_PATH, MONGODB_URI
    print("✅ config.py imported successfully")
except Exception as e:
    print(f"❌ config.py import failed: {e}")

try:
    from data_validator import DataCleaner, clean_fund_data, ValidationResult
    print("✅ data_validator.py imported successfully")
except Exception as e:
    print(f"❌ data_validator.py import failed: {e}")

try:
    from pdf_parser import MultiFundPDFParser, FundData
    print("✅ pdf_parser.py imported successfully")
except Exception as e:
    print(f"❌ pdf_parser.py import failed: {e}")

try:
    from pdf_downloader import PDFDownloader
    print("✅ pdf_downloader.py imported successfully")
except Exception as e:
    print(f"❌ pdf_downloader.py import failed: {e}")

try:
    from mongodb_storage import MongoDBStorage
    print("✅ mongodb_storage.py imported successfully")
except Exception as e:
    print(f"❌ mongodb_storage.py import failed: {e}")

print("\n" + "="*60)


# Test DataCleaner
print("\n📊 Testing DataCleaner...")

# Test NA detection
na_values = ['N/A', 'NA', 'n/a', '--', '', None, 'nil']
for val in na_values:
    result = DataCleaner.is_na(val)
    status = "✅" if result else "❌"
    print(f"  {status} is_na('{val}'): {result}")

# Test numeric cleaning
numeric_tests = [
    ("1,234.56", 1234.56),
    ("5.25%", 5.25),
    ("₹500 Cr", 500.0),
    ("(25.50)", -25.50),
    ("N/A", None),
]
print("\n  Numeric cleaning:")
for input_val, expected in numeric_tests:
    result = DataCleaner.clean_numeric(input_val)
    status = "✅" if result == expected else "❌"
    print(f"    {status} clean_numeric('{input_val}'): {result} (expected: {expected})")

# Test holdings cleaning
print("\n  Holdings cleaning:")
test_holdings = [
    {"name": "HDFC BANK LTD", "weight": "8.5%"},
    {"name": "N/A", "weight": "5.0%"},  # Should be removed
    {"name": "Reliance Industries", "weight": "NA"},  # Should be removed
    {"name": "ICICI Bank", "weight": "7.25"},
]
cleaned = DataCleaner.clean_holdings(test_holdings)
print(f"    Input: {len(test_holdings)} holdings")
print(f"    Output: {len(cleaned)} valid holdings")
for h in cleaned:
    print(f"      - {h['name']}: {h['weight']}%")

# Test fund validation
print("\n  Fund validation:")
test_fund = {
    "fund_name": "HDFC Mid-Cap Opportunities Fund",
    "amc_name": "HDFC AMC",
    "category": "Mid Cap",
    "aum": "50,000 Cr",
    "expense_ratio": "1.75%",
    "return_1y": "25.5%",
    "return_3y": "NA",  # This should be filtered out
    "holdings": test_holdings,
}
result = DataCleaner.validate_fund(test_fund)
print(f"    Valid: {result.is_valid}")
print(f"    Errors: {result.errors}")
print(f"    Warnings: {result.warnings}")

print("\n" + "="*60)


# Test MongoDB connection (optional)
print("\n💾 Testing MongoDB connection...")
try:
    storage = MongoDBStorage()
    storage.connect()
    print("✅ MongoDB connected successfully")
    if storage.client is not None:
        storage.print_stats()
    storage.disconnect()
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")

print("\n" + "="*60)


# Test configuration
print("\n⚙️ Configuration Summary:")
print(f"  PDF Storage Path: {PDF_STORAGE_PATH}")
print(f"  AMCs Configured: {len(AMC_SOURCES)}")
for code in list(AMC_SOURCES.keys())[:5]:
    print(f"    - {code}: {AMC_SOURCES[code]['name']}")
if len(AMC_SOURCES) > 5:
    print(f"    ... and {len(AMC_SOURCES) - 5} more")

print("\n" + "="*60)
print("\n✨ All tests completed!")
print("\nTo run the full automation:")
print("  python main.py --list-amcs    # List all AMCs")
print("  python main.py --amc HDFC     # Run for HDFC only")
print("  python main.py                # Run for all AMCs")
