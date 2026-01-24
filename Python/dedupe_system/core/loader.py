"""
Data Loader component for the Intelligent Duplicate Detection & Cleanup System.

This module handles:
- CSV and JSON file parsing with pandas
- Comprehensive input validation and error handling
- Preview functionality for first N records
- Encoding detection and malformed file handling
- Memory-efficient processing for large files

The loader ensures data integrity and provides detailed error reporting
for troubleshooting file format issues.
"""

import pandas as pd
import json
import csv
import chardet
from pathlib import Path
from typing import Union, Optional, Dict, Any, List
from io import StringIO, BytesIO

from .models import ValidationResult
from .exceptions import FileProcessingError, DataValidationError
from .logging_config import get_logger

logger = get_logger(__name__)


class DataLoader:
    """
    Handles loading and validation of CSV and JSON files.
    
    This class provides robust file loading with automatic encoding detection,
    comprehensive validation, and detailed error reporting.
    """
    
    def __init__(self, max_file_size_mb: int = 100, max_preview_rows: int = 1000):
        """
        Initialize the DataLoader.
        
        Args:
            max_file_size_mb: Maximum file size in MB to prevent memory issues
            max_preview_rows: Maximum rows to load for preview functionality
        """
        self.max_file_size_mb = max_file_size_mb
        self.max_preview_rows = max_preview_rows
        self.supported_encodings = ['utf-8', 'utf-16', 'iso-8859-1', 'cp1252']
    
    def load_file(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """
        Load a file (CSV or JSON) and return as DataFrame.
        
        Args:
            file_path: Path to the file to load
            
        Returns:
            DataFrame containing the loaded data
            
        Raises:
            FileProcessingError: If file cannot be loaded or parsed
            DataValidationError: If data validation fails
        """
        file_path = Path(file_path)
        
        # Check if file exists
        if not file_path.exists():
            raise FileProcessingError(f"File not found: {file_path}", str(file_path))
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            raise FileProcessingError(
                f"File too large: {file_size_mb:.1f}MB (max: {self.max_file_size_mb}MB)",
                str(file_path)
            )
        
        logger.info(f"Loading file: {file_path} ({file_size_mb:.1f}MB)")
        
        # Determine file type and load accordingly
        file_extension = file_path.suffix.lower()
        
        try:
            if file_extension == '.csv':
                return self.load_csv(file_path)
            elif file_extension == '.json':
                return self.load_json(file_path)
            else:
                raise FileProcessingError(
                    f"Unsupported file format: {file_extension}. Supported formats: .csv, .json",
                    str(file_path)
                )
        except Exception as e:
            if isinstance(e, (FileProcessingError, DataValidationError)):
                raise
            else:
                raise FileProcessingError(f"Unexpected error loading file: {str(e)}", str(file_path))
    
    def load_csv(self, file_path: Path) -> pd.DataFrame:
        """
        Load a CSV file with automatic encoding detection.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            DataFrame containing the CSV data
            
        Raises:
            FileProcessingError: If CSV cannot be parsed
        """
        logger.debug(f"Loading CSV file: {file_path}")
        
        # Detect encoding
        encoding = self._detect_encoding(file_path)
        logger.debug(f"Detected encoding: {encoding}")
        
        try:
            # Try to load with detected encoding
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                dtype=str,  # Load all columns as strings initially
                na_values=['', 'NULL', 'null', 'None', 'N/A', 'n/a'],
                keep_default_na=True
            )
            
            logger.info(f"Successfully loaded CSV: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except UnicodeDecodeError as e:
            # Try alternative encodings
            for alt_encoding in self.supported_encodings:
                if alt_encoding != encoding:
                    try:
                        logger.debug(f"Trying alternative encoding: {alt_encoding}")
                        df = pd.read_csv(
                            file_path,
                            encoding=alt_encoding,
                            dtype=str,
                            na_values=['', 'NULL', 'null', 'None', 'N/A', 'n/a'],
                            keep_default_na=True
                        )
                        logger.info(f"Successfully loaded CSV with {alt_encoding}: {len(df)} rows")
                        return df
                    except:
                        continue
            
            raise FileProcessingError(
                f"Could not decode CSV file with any supported encoding: {e}",
                str(file_path)
            )
            
        except pd.errors.EmptyDataError:
            raise FileProcessingError("CSV file is empty", str(file_path))
            
        except pd.errors.ParserError as e:
            raise FileProcessingError(f"CSV parsing error: {e}", str(file_path))
            
        except Exception as e:
            raise FileProcessingError(f"Error loading CSV: {e}", str(file_path))
    
    def load_json(self, file_path: Path) -> pd.DataFrame:
        """
        Load a JSON file and convert to DataFrame.
        
        Supports both:
        - Array of objects: [{"field1": "value1"}, {"field2": "value2"}]
        - Single object with arrays: {"field1": ["val1", "val2"], "field2": ["val3", "val4"]}
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            DataFrame containing the JSON data
            
        Raises:
            FileProcessingError: If JSON cannot be parsed
        """
        logger.debug(f"Loading JSON file: {file_path}")
        
        # Detect encoding
        encoding = self._detect_encoding(file_path)
        logger.debug(f"Detected encoding: {encoding}")
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                data = json.load(f)
            
            # Convert to DataFrame based on JSON structure
            if isinstance(data, list):
                # Array of objects format
                if not data:
                    raise FileProcessingError("JSON file contains empty array", str(file_path))
                
                df = pd.DataFrame(data)
                
            elif isinstance(data, dict):
                # Object with arrays format
                df = pd.DataFrame(data)
                
            else:
                raise FileProcessingError(
                    "JSON must be either an array of objects or an object with arrays",
                    str(file_path)
                )
            
            # Convert all columns to strings for consistency
            df = df.astype(str)
            
            logger.info(f"Successfully loaded JSON: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except json.JSONDecodeError as e:
            raise FileProcessingError(f"Invalid JSON format: {e}", str(file_path), e.lineno)
            
        except UnicodeDecodeError as e:
            raise FileProcessingError(f"Could not decode JSON file: {e}", str(file_path))
            
        except Exception as e:
            raise FileProcessingError(f"Error loading JSON: {e}", str(file_path))
    
    def validate_data(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate the loaded DataFrame for common issues.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            ValidationResult with validation status and messages
        """
        logger.debug(f"Validating DataFrame: {len(df)} rows, {len(df.columns)} columns")
        
        errors = []
        warnings = []
        
        # Check if DataFrame is empty
        if df.empty:
            errors.append("Dataset is empty (no rows)")
        
        # Check if there are any columns
        if len(df.columns) == 0:
            errors.append("Dataset has no columns")
        
        # Check for duplicate column names
        if len(df.columns) != len(set(df.columns)):
            duplicate_cols = [col for col in df.columns if list(df.columns).count(col) > 1]
            errors.append(f"Duplicate column names found: {duplicate_cols}")
        
        # Check for completely empty columns
        empty_cols = [col for col in df.columns if df[col].isna().all()]
        if empty_cols:
            warnings.append(f"Columns with all missing values: {empty_cols}")
        
        # Check for columns with very high missing value percentage
        high_missing_cols = []
        for col in df.columns:
            missing_pct = (df[col].isna().sum() / len(df)) * 100
            if missing_pct > 90:
                high_missing_cols.append(f"{col} ({missing_pct:.1f}% missing)")
        
        if high_missing_cols:
            warnings.append(f"Columns with >90% missing values: {high_missing_cols}")
        
        # Check for suspicious column names
        suspicious_cols = [col for col in df.columns if not col.strip() or col.startswith('Unnamed:')]
        if suspicious_cols:
            warnings.append(f"Suspicious column names: {suspicious_cols}")
        
        # Check for very wide datasets (too many columns)
        if len(df.columns) > 100:
            warnings.append(f"Dataset has many columns ({len(df.columns)}). Consider selecting specific fields for duplicate detection.")
        
        # Check for very long datasets
        if len(df) > 100000:
            warnings.append(f"Large dataset ({len(df)} rows). Processing may take time.")
        
        is_valid = len(errors) == 0
        
        logger.info(f"Validation complete: {'PASSED' if is_valid else 'FAILED'}")
        if errors:
            logger.warning(f"Validation errors: {errors}")
        if warnings:
            logger.info(f"Validation warnings: {warnings}")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            record_count=len(df),
            field_names=list(df.columns)
        )
    
    def get_preview(self, df: pd.DataFrame, rows: int = 10) -> pd.DataFrame:
        """
        Get a preview of the first N rows of the DataFrame.
        
        Args:
            df: DataFrame to preview
            rows: Number of rows to include in preview
            
        Returns:
            DataFrame containing the preview rows
        """
        preview_rows = min(rows, len(df), self.max_preview_rows)
        logger.debug(f"Creating preview with {preview_rows} rows")
        
        return df.head(preview_rows)
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get a summary of the dataset characteristics.
        
        Args:
            df: DataFrame to summarize
            
        Returns:
            Dictionary containing dataset summary information
        """
        summary = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'column_names': list(df.columns),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
            'missing_value_counts': df.isna().sum().to_dict(),
            'data_types': df.dtypes.astype(str).to_dict()
        }
        
        # Add column statistics
        summary['column_stats'] = {}
        for col in df.columns:
            col_stats = {
                'non_null_count': df[col].notna().sum(),
                'null_count': df[col].isna().sum(),
                'unique_count': df[col].nunique(),
                'most_common_value': df[col].mode().iloc[0] if not df[col].mode().empty else None
            }
            summary['column_stats'][col] = col_stats
        
        return summary
    
    def _detect_encoding(self, file_path: Path) -> str:
        """
        Detect the encoding of a file using chardet.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected encoding string
        """
        try:
            with open(file_path, 'rb') as f:
                # Read first 10KB for encoding detection
                raw_data = f.read(10240)
                
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            confidence = result['confidence']
            
            logger.debug(f"Encoding detection: {encoding} (confidence: {confidence:.2f})")
            
            # Fall back to utf-8 if detection confidence is low
            if confidence < 0.7:
                logger.debug("Low confidence in encoding detection, using utf-8")
                encoding = 'utf-8'
            
            return encoding or 'utf-8'
            
        except Exception as e:
            logger.warning(f"Encoding detection failed: {e}, using utf-8")
            return 'utf-8'


# Convenience functions for direct file loading
def load_csv_file(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    Convenience function to load a CSV file.
    
    Args:
        file_path: Path to the CSV file
        **kwargs: Additional arguments for DataLoader
        
    Returns:
        DataFrame containing the CSV data
    """
    loader = DataLoader(**kwargs)
    return loader.load_csv(Path(file_path))


def load_json_file(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    Convenience function to load a JSON file.
    
    Args:
        file_path: Path to the JSON file
        **kwargs: Additional arguments for DataLoader
        
    Returns:
        DataFrame containing the JSON data
    """
    loader = DataLoader(**kwargs)
    return loader.load_json(Path(file_path))


def validate_dataframe(df: pd.DataFrame) -> ValidationResult:
    """
    Convenience function to validate a DataFrame.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        ValidationResult with validation status and messages
    """
    loader = DataLoader()
    return loader.validate_data(df)