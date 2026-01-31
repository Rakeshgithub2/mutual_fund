"""
═══════════════════════════════════════════════════════════════════════════════
DATA VALIDATOR & CLEANER
═══════════════════════════════════════════════════════════════════════════════
Ensures all extracted data meets quality standards:
- No null/NA/None values
- Proper data types
- Valid ranges for numeric fields
- Complete required fields
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    cleaned_data: Optional[Dict] = None


class DataCleaner:
    """
    Clean and validate mutual fund data
    
    Ensures:
    - No None, null, NA, N/A values
    - Proper numeric formats
    - Valid percentage ranges
    - Complete holdings data
    """
    
    # Values to treat as missing/invalid
    NA_VALUES = {
        'na', 'n/a', 'n.a.', 'n.a', '--', '-', '—', '–',
        'nil', 'null', 'none', 'nan', '#n/a', '#value!',
        'not available', 'not applicable', 'unavailable',
        'tbd', 'tba', '', ' '
    }
    
    # Required fields for a fund
    REQUIRED_FIELDS = {
        'fund_name',
        'amc_name',
        'category'
    }
    
    # Fields that should be numeric
    NUMERIC_FIELDS = {
        'aum', 'nav', 'expense_ratio',
        'return_1m', 'return_3m', 'return_6m',
        'return_1y', 'return_3y', 'return_5y',
        'return_since_inception'
    }
    
    # Valid percentage ranges
    PERCENTAGE_RANGES = {
        'expense_ratio': (0, 3),  # 0-3%
        'return_1m': (-30, 30),   # Monthly return -30% to +30%
        'return_3m': (-50, 50),
        'return_6m': (-60, 60),
        'return_1y': (-80, 100),
        'return_3y': (-50, 80),   # Annualized
        'return_5y': (-30, 60),
    }
    
    @classmethod
    def is_na(cls, value: Any) -> bool:
        """Check if value is considered NA/missing"""
        if value is None:
            return True
        
        if isinstance(value, float) and str(value).lower() == 'nan':
            return True
        
        if isinstance(value, str):
            return value.lower().strip() in cls.NA_VALUES
        
        return False
    
    @classmethod
    def clean_string(cls, value: Any, default: str = "") -> str:
        """Clean and normalize string value"""
        if cls.is_na(value):
            return default
        
        if not isinstance(value, str):
            value = str(value)
        
        # Remove extra whitespace
        value = ' '.join(value.split())
        
        # Remove special characters at start/end
        value = value.strip('*†‡§¶•·')
        
        return value.strip()
    
    @classmethod
    def clean_numeric(cls, value: Any, default: float = None) -> Optional[float]:
        """Clean and convert to numeric value"""
        if cls.is_na(value):
            return default
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove common non-numeric characters
            cleaned = value.strip()
            cleaned = cleaned.replace(',', '')
            cleaned = cleaned.replace('%', '')
            cleaned = cleaned.replace('₹', '')
            cleaned = cleaned.replace('Rs.', '')
            cleaned = cleaned.replace('Rs', '')
            cleaned = cleaned.replace('Cr', '')
            cleaned = cleaned.replace('Lakh', '')
            
            # Handle parentheses for negative
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]
            
            # Extract number using regex
            match = re.search(r'-?\d+\.?\d*', cleaned)
            if match:
                return float(match.group())
        
        return default
    
    @classmethod
    def clean_percentage(cls, value: Any, field_name: str = None) -> Optional[float]:
        """Clean percentage value and validate range"""
        num = cls.clean_numeric(value)
        
        if num is None:
            return None
        
        # Check valid range if specified
        if field_name and field_name in cls.PERCENTAGE_RANGES:
            min_val, max_val = cls.PERCENTAGE_RANGES[field_name]
            if not (min_val <= num <= max_val):
                return None  # Out of valid range
        
        return round(num, 2)
    
    @classmethod
    def clean_aum(cls, value: Any) -> Optional[float]:
        """
        Clean AUM value and convert to crores
        
        Handles:
        - "1234.56 Cr" -> 1234.56
        - "12,345.67 Crores" -> 12345.67
        - "123 Lakhs" -> 1.23
        """
        if cls.is_na(value):
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        value = str(value).lower().strip()
        
        # Check for lakhs (convert to crores)
        if 'lakh' in value:
            num = cls.clean_numeric(value)
            if num:
                return round(num / 100, 2)  # 100 lakhs = 1 crore
        
        # Already in crores
        return cls.clean_numeric(value)
    
    @classmethod
    def clean_holdings(cls, holdings: List[Dict]) -> List[Dict]:
        """
        Clean holdings data
        
        Removes entries with NA values
        Ensures percentage is valid
        """
        if not holdings:
            return []
        
        cleaned = []
        
        for holding in holdings:
            if not isinstance(holding, dict):
                continue
            
            name = cls.clean_string(holding.get('name', ''))
            weight = cls.clean_percentage(holding.get('weight', holding.get('percentage', '')))
            
            # Skip if name is empty or weight is invalid
            if not name or weight is None:
                continue
            
            # Skip if weight is outside valid range (0-100%)
            if not (0 <= weight <= 100):
                continue
            
            cleaned_holding = {
                'name': name,
                'weight': weight
            }
            
            # Add sector if available
            sector = cls.clean_string(holding.get('sector', ''))
            if sector:
                cleaned_holding['sector'] = sector
            
            # Add ISIN if available
            isin = cls.clean_string(holding.get('isin', ''))
            if isin and len(isin) == 12:  # Valid ISIN is 12 chars
                cleaned_holding['isin'] = isin
            
            cleaned.append(cleaned_holding)
        
        # Sort by weight descending
        cleaned.sort(key=lambda x: x['weight'], reverse=True)
        
        return cleaned
    
    @classmethod
    def clean_sectors(cls, sectors: List[Dict]) -> List[Dict]:
        """Clean sector allocation data"""
        if not sectors:
            return []
        
        cleaned = []
        
        for sector in sectors:
            if not isinstance(sector, dict):
                continue
            
            name = cls.clean_string(sector.get('name', sector.get('sector', '')))
            weight = cls.clean_percentage(sector.get('weight', sector.get('percentage', '')))
            
            if not name or weight is None:
                continue
            
            if not (0 <= weight <= 100):
                continue
            
            cleaned.append({
                'name': name,
                'weight': weight
            })
        
        cleaned.sort(key=lambda x: x['weight'], reverse=True)
        return cleaned
    
    @classmethod
    def validate_fund(cls, fund_data: Dict) -> ValidationResult:
        """
        Validate and clean fund data
        
        Returns ValidationResult with cleaned data if valid
        """
        errors = []
        warnings = []
        cleaned = {}
        
        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            value = fund_data.get(field)
            if cls.is_na(value):
                errors.append(f"Missing required field: {field}")
            else:
                cleaned[field] = cls.clean_string(value)
        
        # Clean numeric fields
        for field in cls.NUMERIC_FIELDS:
            value = fund_data.get(field)
            if value is not None:
                if field == 'aum':
                    cleaned_val = cls.clean_aum(value)
                elif field in cls.PERCENTAGE_RANGES:
                    cleaned_val = cls.clean_percentage(value, field)
                else:
                    cleaned_val = cls.clean_numeric(value)
                
                if cleaned_val is not None:
                    cleaned[field] = cleaned_val
                else:
                    warnings.append(f"Invalid value for {field}: {value}")
        
        # Clean holdings
        if 'holdings' in fund_data:
            cleaned['holdings'] = cls.clean_holdings(fund_data['holdings'])
            if not cleaned['holdings']:
                warnings.append("No valid holdings after cleaning")
        
        # Clean sectors
        if 'sectors' in fund_data:
            cleaned['sectors'] = cls.clean_sectors(fund_data['sectors'])
        
        # Clean string fields
        string_fields = [
            'fund_manager', 'benchmark', 'scheme_code', 
            'isin', 'plan', 'option'
        ]
        for field in string_fields:
            value = fund_data.get(field)
            if value is not None:
                cleaned_val = cls.clean_string(value)
                if cleaned_val:
                    cleaned[field] = cleaned_val
        
        # Dates
        if 'inception_date' in fund_data:
            # Keep as-is if valid date
            cleaned['inception_date'] = fund_data['inception_date']
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            cleaned_data=cleaned if is_valid else None
        )
    
    @classmethod
    def remove_nulls(cls, data: Dict) -> Dict:
        """
        Recursively remove all null/None/NA values from dict
        
        This is the final cleanup step before storage
        """
        if not isinstance(data, dict):
            return data
        
        cleaned = {}
        
        for key, value in data.items():
            if cls.is_na(value):
                continue
            
            if isinstance(value, dict):
                cleaned_nested = cls.remove_nulls(value)
                if cleaned_nested:  # Only add if not empty
                    cleaned[key] = cleaned_nested
            
            elif isinstance(value, list):
                cleaned_list = []
                for item in value:
                    if isinstance(item, dict):
                        cleaned_item = cls.remove_nulls(item)
                        if cleaned_item:
                            cleaned_list.append(cleaned_item)
                    elif not cls.is_na(item):
                        cleaned_list.append(item)
                
                if cleaned_list:  # Only add if not empty
                    cleaned[key] = cleaned_list
            
            else:
                cleaned[key] = value
        
        return cleaned


class HoldingsValidator:
    """
    Specialized validator for holdings data
    
    Ensures:
    - Total weight doesn't exceed 100%
    - No duplicate holdings
    - Proper stock names
    """
    
    @staticmethod
    def validate_weights(holdings: List[Dict]) -> Tuple[bool, List[str]]:
        """Check that weights sum to ~100% (with tolerance)"""
        warnings = []
        
        if not holdings:
            return True, []
        
        total_weight = sum(h.get('weight', 0) for h in holdings)
        
        if total_weight > 105:
            warnings.append(f"Total weight exceeds 100%: {total_weight:.1f}%")
        elif total_weight < 80:
            warnings.append(f"Total weight seems low: {total_weight:.1f}%")
        
        return len(warnings) == 0, warnings
    
    @staticmethod
    def remove_duplicates(holdings: List[Dict]) -> List[Dict]:
        """Remove duplicate holdings by name"""
        seen = set()
        unique = []
        
        for holding in holdings:
            name = holding.get('name', '').lower().strip()
            if name and name not in seen:
                seen.add(name)
                unique.append(holding)
        
        return unique
    
    @staticmethod
    def standardize_names(holdings: List[Dict]) -> List[Dict]:
        """
        Standardize company names
        
        Example:
        - "HDFC BANK LTD" -> "HDFC Bank Ltd"
        - "RELIANCE INDUSTRIES LIMITED" -> "Reliance Industries Ltd"
        """
        for holding in holdings:
            name = holding.get('name', '')
            if name:
                # Title case
                name = name.title()
                
                # Standardize common suffixes
                replacements = [
                    ('Limited', 'Ltd'),
                    ('Pvt Ltd', 'Pvt. Ltd.'),
                    ('Private Limited', 'Pvt. Ltd.'),
                ]
                for old, new in replacements:
                    name = name.replace(old, new)
                
                holding['name'] = name
        
        return holdings


# Convenience function
def clean_fund_data(data: Dict) -> Optional[Dict]:
    """
    Clean fund data and remove all null values
    
    Returns None if data is invalid
    """
    result = DataCleaner.validate_fund(data)
    
    if not result.is_valid:
        return None
    
    return DataCleaner.remove_nulls(result.cleaned_data)
