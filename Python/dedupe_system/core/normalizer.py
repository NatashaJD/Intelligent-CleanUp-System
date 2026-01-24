"""
Data Normalizer component for the Intelligent Duplicate Detection & Cleanup System.

This module handles:
- Text normalization (lowercase, whitespace trimming, special characters)
- Date format standardization to ISO format
- Numeric field normalization (remove formatting characters)
- Composite key generation for multi-field matching
- Preservation of original data while creating normalized versions

The normalizer ensures consistent data comparison while maintaining data integrity
for final output generation.
"""

import pandas as pd
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from dateutil import parser as date_parser
import unicodedata

from .logging_config import get_logger
from .exceptions import DataValidationError

logger = get_logger(__name__)


class DataNormalizer:
    """
    Handles data normalization for consistent duplicate detection.
    
    This class provides comprehensive normalization while preserving
    original data for final output generation.
    """
    
    def __init__(self):
        """Initialize the DataNormalizer with default settings."""
        # Common date formats to try parsing
        self.date_formats = [
            '%Y-%m-%d',           # 2023-01-15
            '%m/%d/%Y',           # 01/15/2023
            '%d/%m/%Y',           # 15/01/2023
            '%Y/%m/%d',           # 2023/01/15
            '%m-%d-%Y',           # 01-15-2023
            '%d-%m-%Y',           # 15-01-2023
            '%Y%m%d',             # 20230115
            '%m/%d/%y',           # 01/15/23
            '%d/%m/%y',           # 15/01/23
            '%B %d, %Y',          # January 15, 2023
            '%b %d, %Y',          # Jan 15, 2023
            '%d %B %Y',           # 15 January 2023
            '%d %b %Y',           # 15 Jan 2023
        ]
        
        # Regex patterns for cleaning
        self.phone_pattern = re.compile(r'[^\d]')  # Remove non-digits from phone numbers
        self.whitespace_pattern = re.compile(r'\s+')  # Multiple whitespace to single space
        self.punctuation_pattern = re.compile(r'[^\w\s]')  # Remove punctuation except word chars and spaces
        self.numeric_pattern = re.compile(r'[^\d.-]')  # Keep only digits, dots, and minus signs
        
    def normalize_text(self, value: Any) -> str:
        """
        Normalize text data for consistent comparison.
        
        Performs:
        - Convert to string
        - Unicode normalization
        - Lowercase conversion
        - Whitespace trimming and normalization
        - Special character handling
        
        Args:
            value: Input value to normalize
            
        Returns:
            Normalized text string
        """
        if pd.isna(value) or value is None:
            return ""
        
        # Convert to string
        text = str(value).strip()
        
        if not text:
            return ""
        
        try:
            # Unicode normalization (decompose accented characters)
            text = unicodedata.normalize('NFKD', text)
            
            # Convert to lowercase
            text = text.lower()
            
            # Normalize whitespace (multiple spaces to single space)
            text = self.whitespace_pattern.sub(' ', text)
            
            # Remove leading/trailing whitespace
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.warning(f"Text normalization failed for '{value}': {e}")
            return str(value).lower().strip()
    
    def normalize_text_aggressive(self, value: Any) -> str:
        """
        Aggressive text normalization for fuzzy matching.
        
        Additional processing:
        - Remove punctuation
        - Remove extra characters
        - More aggressive cleaning
        
        Args:
            value: Input value to normalize
            
        Returns:
            Aggressively normalized text string
        """
        # Start with basic normalization
        text = self.normalize_text(value)
        
        if not text:
            return ""
        
        try:
            # Remove punctuation except spaces
            text = self.punctuation_pattern.sub(' ', text)
            
            # Normalize whitespace again after punctuation removal
            text = self.whitespace_pattern.sub(' ', text).strip()
            
            return text
            
        except Exception as e:
            logger.warning(f"Aggressive text normalization failed for '{value}': {e}")
            return self.normalize_text(value)
    
    def normalize_date(self, value: Any) -> str:
        """
        Normalize date values to ISO format (YYYY-MM-DD).
        
        Args:
            value: Input date value (string, datetime, etc.)
            
        Returns:
            ISO formatted date string or empty string if parsing fails
        """
        if pd.isna(value) or value is None:
            return ""
        
        # If already a datetime object
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')
        
        # Convert to string and clean
        date_str = str(value).strip()
        if not date_str:
            return ""
        
        # Try parsing with dateutil first (most flexible)
        try:
            parsed_date = date_parser.parse(date_str, fuzzy=True)
            return parsed_date.strftime('%Y-%m-%d')
        except:
            pass
        
        # Try specific formats
        for fmt in self.date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except:
                continue
        
        # If all parsing fails, log warning and return original
        logger.debug(f"Could not parse date: '{date_str}'")
        return ""
    
    def normalize_numeric(self, value: Any) -> str:
        """
        Normalize numeric values by removing formatting characters.
        
        Handles:
        - Currency symbols ($, €, etc.)
        - Thousands separators (,)
        - Percentage signs (%)
        - Extra whitespace
        
        Args:
            value: Input numeric value
            
        Returns:
            Cleaned numeric string
        """
        if pd.isna(value) or value is None:
            return ""
        
        # Convert to string
        num_str = str(value).strip()
        if not num_str:
            return ""
        
        try:
            # Remove currency symbols and other non-numeric characters
            # Keep digits, decimal points, and minus signs
            cleaned = self.numeric_pattern.sub('', num_str)
            
            # Handle multiple decimal points (keep only the last one)
            if cleaned.count('.') > 1:
                parts = cleaned.split('.')
                cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
            
            # Remove leading/trailing dots
            cleaned = cleaned.strip('.')
            
            # Validate the result is a valid number
            if cleaned and cleaned != '-':
                try:
                    float(cleaned)
                    return cleaned
                except ValueError:
                    pass
            
            return ""
            
        except Exception as e:
            logger.warning(f"Numeric normalization failed for '{value}': {e}")
            return ""
    
    def normalize_phone(self, value: Any) -> str:
        """
        Normalize phone numbers by extracting digits only.
        
        Args:
            value: Input phone number
            
        Returns:
            Digits-only phone number string
        """
        if pd.isna(value) or value is None:
            return ""
        
        phone_str = str(value).strip()
        if not phone_str:
            return ""
        
        # Extract digits only
        digits_only = self.phone_pattern.sub('', phone_str)
        
        # Remove leading 1 for US numbers if 11 digits
        if len(digits_only) == 11 and digits_only.startswith('1'):
            digits_only = digits_only[1:]
        
        return digits_only
    
    def normalize_email(self, value: Any) -> str:
        """
        Normalize email addresses.
        
        Args:
            value: Input email address
            
        Returns:
            Normalized email address
        """
        if pd.isna(value) or value is None:
            return ""
        
        email = str(value).strip().lower()
        
        # Basic email validation pattern
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        if email_pattern.match(email):
            return email
        else:
            logger.debug(f"Invalid email format: '{value}'")
            return email  # Return as-is even if invalid
    
    def normalize_record(self, record: Dict[str, Any], field_configs: Dict[str, str]) -> Dict[str, str]:
        """
        Normalize a single record based on field configuration.
        
        Args:
            record: Dictionary containing record data
            field_configs: Dictionary mapping field names to normalization types
                          ('text', 'date', 'numeric', 'phone', 'email', 'text_aggressive')
            
        Returns:
            Dictionary with normalized values
        """
        normalized = {}
        
        for field_name, norm_type in field_configs.items():
            if field_name not in record:
                normalized[field_name] = ""
                continue
            
            value = record[field_name]
            
            try:
                if norm_type == 'text':
                    normalized[field_name] = self.normalize_text(value)
                elif norm_type == 'text_aggressive':
                    normalized[field_name] = self.normalize_text_aggressive(value)
                elif norm_type == 'date':
                    normalized[field_name] = self.normalize_date(value)
                elif norm_type == 'numeric':
                    normalized[field_name] = self.normalize_numeric(value)
                elif norm_type == 'phone':
                    normalized[field_name] = self.normalize_phone(value)
                elif norm_type == 'email':
                    normalized[field_name] = self.normalize_email(value)
                else:
                    # Default to text normalization
                    normalized[field_name] = self.normalize_text(value)
                    
            except Exception as e:
                logger.warning(f"Normalization failed for field '{field_name}' with value '{value}': {e}")
                normalized[field_name] = self.normalize_text(value)
        
        return normalized
    
    def create_composite_key(self, record: Dict[str, Any], key_fields: List[str], 
                           field_configs: Optional[Dict[str, str]] = None) -> str:
        """
        Create a composite key from multiple fields for duplicate detection.
        
        Args:
            record: Dictionary containing record data
            key_fields: List of field names to include in the composite key
            field_configs: Optional field normalization configurations
            
        Returns:
            Composite key string
        """
        if not key_fields:
            raise DataValidationError("No key fields specified for composite key generation")
        
        # Use default text normalization if no config provided
        if field_configs is None:
            field_configs = {field: 'text' for field in key_fields}
        
        # Normalize the specified fields
        normalized_values = []
        for field in key_fields:
            if field not in record:
                logger.warning(f"Key field '{field}' not found in record")
                normalized_values.append("")
                continue
            
            norm_type = field_configs.get(field, 'text')
            
            try:
                if norm_type == 'text':
                    normalized_val = self.normalize_text(record[field])
                elif norm_type == 'text_aggressive':
                    normalized_val = self.normalize_text_aggressive(record[field])
                elif norm_type == 'date':
                    normalized_val = self.normalize_date(record[field])
                elif norm_type == 'numeric':
                    normalized_val = self.normalize_numeric(record[field])
                elif norm_type == 'phone':
                    normalized_val = self.normalize_phone(record[field])
                elif norm_type == 'email':
                    normalized_val = self.normalize_email(record[field])
                else:
                    normalized_val = self.normalize_text(record[field])
                
                normalized_values.append(normalized_val)
                
            except Exception as e:
                logger.warning(f"Failed to normalize field '{field}' for composite key: {e}")
                normalized_values.append(self.normalize_text(record[field]))
        
        # Join with a delimiter that won't appear in normalized data
        composite_key = "||".join(normalized_values)
        return composite_key
    
    def normalize_dataframe(self, df: pd.DataFrame, field_configs: Dict[str, str]) -> pd.DataFrame:
        """
        Normalize an entire DataFrame while preserving original data.
        
        Creates new columns with '_normalized' suffix containing normalized values.
        
        Args:
            df: Input DataFrame
            field_configs: Dictionary mapping field names to normalization types
            
        Returns:
            DataFrame with additional normalized columns
        """
        logger.info(f"Normalizing DataFrame with {len(df)} rows and {len(field_configs)} configured fields")
        
        df_normalized = df.copy()
        
        for field_name, norm_type in field_configs.items():
            if field_name not in df.columns:
                logger.warning(f"Field '{field_name}' not found in DataFrame columns")
                continue
            
            normalized_col_name = f"{field_name}_normalized"
            
            try:
                if norm_type == 'text':
                    df_normalized[normalized_col_name] = df[field_name].apply(self.normalize_text)
                elif norm_type == 'text_aggressive':
                    df_normalized[normalized_col_name] = df[field_name].apply(self.normalize_text_aggressive)
                elif norm_type == 'date':
                    df_normalized[normalized_col_name] = df[field_name].apply(self.normalize_date)
                elif norm_type == 'numeric':
                    df_normalized[normalized_col_name] = df[field_name].apply(self.normalize_numeric)
                elif norm_type == 'phone':
                    df_normalized[normalized_col_name] = df[field_name].apply(self.normalize_phone)
                elif norm_type == 'email':
                    df_normalized[normalized_col_name] = df[field_name].apply(self.normalize_email)
                else:
                    # Default to text normalization
                    df_normalized[normalized_col_name] = df[field_name].apply(self.normalize_text)
                
                logger.debug(f"Normalized field '{field_name}' using '{norm_type}' method")
                
            except Exception as e:
                logger.error(f"Failed to normalize field '{field_name}': {e}")
                # Create empty normalized column as fallback
                df_normalized[normalized_col_name] = ""
        
        logger.info(f"Normalization complete: {len(df_normalized.columns)} total columns")
        return df_normalized
    
    def get_normalization_stats(self, df: pd.DataFrame, field_configs: Dict[str, str]) -> Dict[str, Any]:
        """
        Get statistics about the normalization process.
        
        Args:
            df: DataFrame with normalized columns
            field_configs: Field configuration used for normalization
            
        Returns:
            Dictionary containing normalization statistics
        """
        stats = {
            'total_fields_normalized': len(field_configs),
            'normalization_types': {},
            'field_stats': {}
        }
        
        # Count normalization types
        for norm_type in field_configs.values():
            stats['normalization_types'][norm_type] = stats['normalization_types'].get(norm_type, 0) + 1
        
        # Field-specific stats
        for field_name, norm_type in field_configs.items():
            if field_name not in df.columns:
                continue
            
            normalized_col = f"{field_name}_normalized"
            if normalized_col not in df.columns:
                continue
            
            original_values = df[field_name].dropna()
            normalized_values = df[normalized_col].dropna()
            
            field_stat = {
                'normalization_type': norm_type,
                'original_unique_count': original_values.nunique(),
                'normalized_unique_count': normalized_values.nunique(),
                'empty_after_normalization': (df[normalized_col] == "").sum(),
                'reduction_ratio': 1 - (normalized_values.nunique() / max(original_values.nunique(), 1))
            }
            
            stats['field_stats'][field_name] = field_stat
        
        return stats


# Convenience functions
def normalize_text_value(value: Any) -> str:
    """Convenience function to normalize a single text value."""
    normalizer = DataNormalizer()
    return normalizer.normalize_text(value)


def normalize_date_value(value: Any) -> str:
    """Convenience function to normalize a single date value."""
    normalizer = DataNormalizer()
    return normalizer.normalize_date(value)


def normalize_numeric_value(value: Any) -> str:
    """Convenience function to normalize a single numeric value."""
    normalizer = DataNormalizer()
    return normalizer.normalize_numeric(value)


def create_composite_key_from_values(values: List[Any], norm_types: List[str] = None) -> str:
    """
    Convenience function to create a composite key from a list of values.
    
    Args:
        values: List of values to combine
        norm_types: List of normalization types (defaults to 'text' for all)
        
    Returns:
        Composite key string
    """
    normalizer = DataNormalizer()
    
    if norm_types is None:
        norm_types = ['text'] * len(values)
    
    if len(values) != len(norm_types):
        raise DataValidationError("Number of values must match number of normalization types")
    
    # Create a temporary record
    record = {f"field_{i}": val for i, val in enumerate(values)}
    key_fields = list(record.keys())
    field_configs = {f"field_{i}": norm_type for i, norm_type in enumerate(norm_types)}
    
    return normalizer.create_composite_key(record, key_fields, field_configs)