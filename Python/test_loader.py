#!/usr/bin/env python3
"""
Test script for the Data Loader component.

This script demonstrates and tests the data loading functionality
with sample CSV and JSON files.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dedupe_system.core.loader import DataLoader
from dedupe_system.core.logging_config import setup_logging
from dedupe_system.core.exceptions import handle_error

def test_data_loader():
    """Test the DataLoader with sample files."""
    
    # Set up logging
    logger = setup_logging("INFO", "logs")
    
    # Initialize the data loader
    loader = DataLoader()
    
    print("=" * 60)
    print("TESTING DATA LOADER COMPONENT")
    print("=" * 60)
    
    # Test CSV loading
    print("\n1. Testing CSV file loading...")
    try:
        csv_file = Path("test_data/sample_customers.csv")
        if csv_file.exists():
            df_csv = loader.load_file(csv_file)
            print(f"✅ CSV loaded successfully: {len(df_csv)} rows, {len(df_csv.columns)} columns")
            
            # Validate the data
            validation = loader.validate_data(df_csv)
            print(f"✅ Validation: {'PASSED' if validation.is_valid else 'FAILED'}")
            if validation.warnings:
                print(f"⚠️  Warnings: {validation.warnings}")
            
            # Show preview
            preview = loader.get_preview(df_csv, 3)
            print(f"📋 Preview (first 3 rows):")
            print(preview.to_string(index=False))
            
            # Show summary
            summary = loader.get_data_summary(df_csv)
            print(f"📊 Summary: {summary['total_rows']} rows, {summary['total_columns']} columns")
            print(f"💾 Memory usage: {summary['memory_usage_mb']:.2f} MB")
            
        else:
            print("❌ CSV test file not found")
    
    except Exception as e:
        error_msg = handle_error(logger, e, "CSV loading test")
        print(f"❌ CSV loading failed: {error_msg}")
    
    # Test JSON loading
    print("\n2. Testing JSON file loading...")
    try:
        json_file = Path("test_data/sample_products.json")
        if json_file.exists():
            df_json = loader.load_file(json_file)
            print(f"✅ JSON loaded successfully: {len(df_json)} rows, {len(df_json.columns)} columns")
            
            # Validate the data
            validation = loader.validate_data(df_json)
            print(f"✅ Validation: {'PASSED' if validation.is_valid else 'FAILED'}")
            if validation.warnings:
                print(f"⚠️  Warnings: {validation.warnings}")
            
            # Show preview
            preview = loader.get_preview(df_json, 2)
            print(f"📋 Preview (first 2 rows):")
            print(preview.to_string(index=False))
            
            # Show summary
            summary = loader.get_data_summary(df_json)
            print(f"📊 Summary: {summary['total_rows']} rows, {summary['total_columns']} columns")
            
        else:
            print("❌ JSON test file not found")
    
    except Exception as e:
        error_msg = handle_error(logger, e, "JSON loading test")
        print(f"❌ JSON loading failed: {error_msg}")
    
    # Test error handling
    print("\n3. Testing error handling...")
    try:
        # Try to load non-existent file
        loader.load_file("nonexistent_file.csv")
    except Exception as e:
        error_msg = handle_error(logger, e, "error handling test")
        print(f"✅ Error handling works: {error_msg}")
    
    print("\n" + "=" * 60)
    print("DATA LOADER TESTING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_data_loader()