# 🚀 Mutual Fund Factsheet Automation Engine

Fully automated system to extract mutual fund data from AMC factsheet PDFs and store in MongoDB.

## Features

- 📥 **Auto-download** factsheet PDFs from 15+ AMC websites
- 📄 **Multi-fund PDF parsing** - Extract all funds from single PDF (like Kotak, HDFC)
- 🧹 **Data cleaning** - No null/NA values, proper data types
- 💾 **MongoDB storage** - Bulk upsert, no duplicates
- ⏰ **Scheduled runs** - Monthly automation on 1st of each month

## Quick Start

### 1. Install Dependencies

```powershell
cd automation
pip install -r requirements.txt
```

### 2. Test Setup

```powershell
python test_automation.py
```

### 3. Run Automation

```powershell
# List all configured AMCs
python main.py --list-amcs

# Run for specific AMC
python main.py --amc HDFC

# Run for all AMCs
python main.py

# Use existing PDFs (skip download)
python main.py --skip-download
```

## File Structure

```
automation/
├── main.py              # Master orchestrator
├── config.py            # AMC sources, patterns, settings
├── pdf_downloader.py    # Downloads factsheets from AMC websites
├── pdf_parser.py        # Parses multi-fund PDFs
├── mongodb_storage.py   # Stores clean data in MongoDB
├── data_validator.py    # Cleans & validates data (no nulls)
├── test_automation.py   # Test script
├── requirements.txt     # Python dependencies
└── pdfs/               # Downloaded PDFs stored here
```

## Configuration

### Add New AMC

Edit `config.py` and add to `AMC_SOURCES`:

```python
"NEW_AMC": {
    "name": "New AMC Mutual Fund",
    "factsheet_url": "https://example.com/factsheet.pdf",
    "website": "https://example.com",
    "multi_fund_pdf": True,
    "fund_separator_pattern": r"(?:Scheme Name|Fund Name)\s*[:\-]?\s*(.+?)(?:Direct|Regular)",
}
```

### MongoDB

Uses same database as backend (reads from `../mutual-funds-backend/.env`):

- Database: `mutualfunds`
- Collection: `funds`

## Data Extracted

For each fund:

| Field            | Description                              |
| ---------------- | ---------------------------------------- |
| `fund_name`      | Full scheme name                         |
| `amc_name`       | AMC name                                 |
| `category`       | Fund category (Large Cap, Mid Cap, etc.) |
| `sub_category`   | Sub-category                             |
| `aum`            | Assets Under Management (in Crores)      |
| `nav`            | Latest NAV                               |
| `expense_ratio`  | Expense ratio %                          |
| `fund_manager`   | Fund manager name                        |
| `inception_date` | Fund launch date                         |
| `benchmark`      | Benchmark index                          |
| `return_1m`      | 1-month return %                         |
| `return_3m`      | 3-month return %                         |
| `return_6m`      | 6-month return %                         |
| `return_1y`      | 1-year return %                          |
| `return_3y`      | 3-year return % (CAGR)                   |
| `return_5y`      | 5-year return % (CAGR)                   |
| `holdings`       | Top holdings with weights                |
| `sectors`        | Sector allocation                        |

## Holdings Structure

```json
{
  "holdings": [
    { "name": "HDFC Bank Ltd", "weight": 8.5 },
    { "name": "Reliance Industries Ltd", "weight": 7.2 },
    { "name": "ICICI Bank Ltd", "weight": 6.8 }
  ]
}
```

## Monthly Scheduler

Start the scheduler to run on 1st of every month at 3 AM:

```powershell
python main.py --scheduler
```

Or use Windows Task Scheduler:

```powershell
schtasks /create /tn "MF Factsheet Update" /tr "python C:\MF root folder\mutual-funds-backend\automation\main.py" /sc monthly /d 1 /st 03:00
```

## Troubleshooting

### PDF Download Fails

- Check if AMC changed their URL
- Some AMCs require headers/cookies
- Update URL in `config.py`

### Parsing Issues

- PDFs may change format
- Adjust `fund_separator_pattern` in config
- Check `EXTRACTION_PATTERNS` for regex

### MongoDB Connection

- Verify `DATABASE_URL` in `../.env`
- Check network connectivity to MongoDB Atlas

## Zero-API Approach

This system uses **zero external APIs** for fund data:

1. **Official AMC PDFs** - Source of truth, published monthly
2. **Direct parsing** - Extract data from PDF tables
3. **No rate limits** - Download once per month
4. **Complete data** - Holdings, returns, AUM all from one source

## Contributing

1. Add new AMC to `config.py`
2. Test with `python main.py --amc NEW_AMC`
3. Verify data in MongoDB
4. Submit PR
