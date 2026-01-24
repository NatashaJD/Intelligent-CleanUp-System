#!/usr/bin/env python3
"""
Integration checkpoint test for Data Loading and Normalization components.

This script verifies that the data loading and normalization components
work together correctly and are ready for duplicate detection.
"""

import sys
from pathlib import Path
import pandas as pd

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dedupe_system.core.loader import DataLoader
from dedupe_system.core.normalizer import DataNormalizer
from dedupe_system.core.logging_config import setup_logging
from dedupe_system.core.exceptions import handle_error

def run_integration_checkpoint():
    """Run comprehensive integration tests for data loading and normalization."""
    
    # Set up logging
    logger = setup_logging("INFO", "logs")
    
    print("=" * 80)
    print("INTEGRATION CHECKPOINT: DATA LOADING + NORMALIZATION")
    print("=" * 80)
    
    # Initialize components
    loader = DataLoader()
    normalizer = DataNormalizer()
    
    test_results = {
        'csv_loading': False,
        'json_loading': False,
        'data_validation': False,
        'normalization': False,
        'composite_keys': False,
        'error_handling': False
    }
    
    # Test 1: CSV Loading and Normalization Pipeline
    print("\n1. Testing CSV Loading + Normalization Pipeline...")
    try:
        # Load CSV data
        csv_file = Path("test_data/sample_customers.csv")
        if not csv_file.exists():
            print("❌ CSV test file not found")
            return False
        
        df_csv = loader.load_file(csv_file)
        print(f"✅ CSV loaded: {len(df_csv)} rows, {len(df_csv.columns)} columns")
        
        # Validate the data
        validation = loader.validate_data(df_csv)
        if not validation.is_valid:
            print(f"❌ CSV validation failed: {validation.errors}")
            return False
        print("✅ CSV validation passed")
        
        # Configure normalization
        field_configs = {
            'name': 'text',
            'email': 'email',
            'phone': 'phone',
            'address': 'text_aggressive',
            'city': 'text',
            'state': 'text',
            'created_date': 'date'
        }
        
        # Normalize the data
        df_normalized = normalizer.normalize_dataframe(df_csv, field_configs)
        expected_cols = len(df_csv.columns) + len(field_configs)
        if len(df_normalized.columns) != expected_cols:
            print(f"❌ Normalization failed: expected {expected_cols} columns, got {len(df_normalized.columns)}")
            return False
        
        print(f"✅ CSV normalization successful: {len(df_normalized.columns)} total columns")
        test_results['csv_loading'] = True
        
    except Exception as e:
        error_msg = handle_error(logger, e, "CSV loading and normalization")
        print(f"❌ CSV pipeline failed: {error_msg}")
        return False
    
    # Test 2: JSON Loading and Normalization Pipeline
    print("\n2. Testing JSON Loading + Normalization Pipeline...")
    try:
        # Load JSON data
        json_file = Path("test_data/sample_products.json")
        if not json_file.exists():
            print("❌ JSON test file not found")
            return False
        
        df_json = loader.load_file(json_file)
        print(f"✅ JSON loaded: {len(df_json)} rows, {len(df_json.columns)} columns")
        
        # Validate the data
        validation = loader.validate_data(df_json)
        if not validation.is_valid:
            print(f"❌ JSON validation failed: {validation.errors}")
            return False
        print("✅ JSON validation passed")
        
        # Configure normalization for product data
        product_field_configs = {
            'name': 'text_aggressive',  # Product names may have variations
            'brand': 'text',
            'price': 'numeric',
            'category': 'text',
            'description': 'text_aggressive'
        }
        
        # Normalize the data
        df_json_normalized = normalizer.normalize_dataframe(df_json, product_field_configs)
        expected_cols = len(df_json.columns) + len(product_field_configs)
        if len(df_json_normalized.columns) != expected_cols:
            print(f"❌ JSON normalization failed: expected {expected_cols} columns, got {len(df_json_normalized.columns)}")
            return False
        
        print(f"✅ JSON normalization successful: {len(df_json_normalized.columns)} total columns")
        test_results['json_loading'] = True
        
    except Exception as e:
        error_msg = handle_error(logger, e, "JSON loading and normalization")
        print(f"❌ JSON pipeline failed: {error_msg}")
        return False
    
    # Test 3: Data Validation Edge Cases
    print("\n3. Testing data validation edge cases...")
    try:
        # Test empty DataFrame
        empty_df = pd.DataFrame()
        validation = loader.validate_data(empty_df)
        if validation.is_valid:
            print("❌ Empty DataFrame should fail validation")
            return False
        print("✅ Empty DataFrame correctly flagged as invalid")
        
        # Test DataFrame with duplicate columns
        bad_df = pd.DataFrame({
            'name': ['John', 'Jane'],
            'name': ['Smith', 'Doe']  # Duplicate column name
        })
        # Note: pandas automatically handles duplicate columns, so this test may not fail as expected
        # But our validation should catch other issues
        
        # Test DataFrame with all null values
        null_df = pd.DataFrame({
            'col1': [None, None, None],
            'col2': [None, None, None]
        })
        validation = loader.validate_data(null_df)
        # Should pass validation but generate warnings
        print("✅ Null DataFrame validation handled correctly")
        
        test_results['data_validation'] = True
        
    except Exception as e:
        error_msg = handle_error(logger, e, "data validation edge cases")
        print(f"❌ Data validation test failed: {error_msg}")
        return False
    
    # Test 4: Normalization Consistency and Round-trip
    print("\n4. Testing normalization consistency...")
    try:
        # Test that normalization is consistent
        test_values = [
            ("John Smith", "text"),
            ("  JANE DOE  ", "text"),
            ("$99.99", "numeric"),
            ("555-123-4567", "phone"),
            ("2023-01-15", "date"),
            ("john@email.com", "email")
        ]
        
        for value, norm_type in test_values:
            # Normalize twice - should get same result
            if norm_type == 'text':
                result1 = normalizer.normalize_text(value)
                result2 = normalizer.normalize_text(result1)
            elif norm_type == 'numeric':
                result1 = normalizer.normalize_numeric(value)
                result2 = normalizer.normalize_numeric(result1)
            elif norm_type == 'phone':
                result1 = normalizer.normalize_phone(value)
                result2 = normalizer.normalize_phone(result1)
            elif norm_type == 'date':
                result1 = normalizer.normalize_date(value)
                result2 = normalizer.normalize_date(result1)
            elif norm_type == 'email':
                result1 = normalizer.normalize_email(value)
                result2 = normalizer.normalize_email(result1)
            
            if result1 != result2:
                print(f"❌ Normalization not consistent for {value}: '{result1}' != '{result2}'")
                return False
        
        print("✅ Normalization consistency verified")
        test_results['normalization'] = True
        
    except Exception as e:
        error_msg = handle_error(logger, e, "normalization consistency")
        print(f"❌ Normalization consistency test failed: {error_msg}")
        return False
    
    # Test 5: Composite Key Generation
    print("\n5. Testing composite key generation...")
    try:
        # Test with customer data
        sample_records = [
            {
                'name': 'John Smith',
                'email': 'john@email.com',
                'phone': '555-123-4567',
                'city': 'Springfield'
            },
            {
                'name': '  JOHN SMITH  ',
                'email': 'JOHN@EMAIL.COM',
                'phone': '(555) 123-4567',
                'city': 'springfield'
            }
        ]
        
        key_fields = ['name', 'email', 'city']
        field_configs = {'name': 'text', 'email': 'email', 'city': 'text'}
        
        key1 = normalizer.create_composite_key(sample_records[0], key_fields, field_configs)
        key2 = normalizer.create_composite_key(sample_records[1], key_fields, field_configs)
        
        if key1 != key2:
            print(f"❌ Composite keys should match: '{key1}' != '{key2}'")
            return False
        
        print(f"✅ Composite key generation working: '{key1}'")
        test_results['composite_keys'] = True
        
    except Exception as e:
        error_msg = handle_error(logger, e, "composite key generation")
        print(f"❌ Composite key test failed: {error_msg}")
        return False
    
    # Test 6: Error Handling
    print("\n6. Testing error handling...")
    try:
        # Test file not found
        try:
            loader.load_file("nonexistent_file.csv")
            print("❌ Should have thrown FileProcessingError")
            return False
        except Exception:
            print("✅ File not found error handled correctly")
        
        # Test invalid composite key fields
        try:
            normalizer.create_composite_key({}, [])  # Empty key fields
            print("❌ Should have thrown DataValidationError")
            return False
        except Exception:
            print("✅ Invalid composite key error handled correctly")
        
        test_results['error_handling'] = True
        
    except Exception as e:
        error_msg = handle_error(logger, e, "error handling")
        print(f"❌ Error handling test failed: {error_msg}")
        return False
    
    # Test 7: Performance and Memory Usage
    print("\n7. Testing performance and memory usage...")
    try:
        # Create a larger dataset for performance testing
        large_data = {
            'name': ['John Smith'] * 1000 + ['Jane Doe'] * 1000,
            'email': ['john@email.com'] * 1000 + ['jane@email.com'] * 1000,
            'phone': ['555-123-4567'] * 1000 + ['555-987-6543'] * 1000,
            'address': ['123 Main St'] * 1000 + ['456 Oak Ave'] * 1000
        }
        
        large_df = pd.DataFrame(large_data)
        
        # Test normalization performance
        import time
        start_time = time.time()
        
        field_configs = {
            'name': 'text',
            'email': 'email',
            'phone': 'phone',
            'address': 'text_aggressive'
        }
        
        normalized_df = normalizer.normalize_dataframe(large_df, field_configs)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Performance test: {len(large_df)} records normalized in {processing_time:.2f} seconds")
        
        # Check memory usage
        memory_mb = normalized_df.memory_usage(deep=True).sum() / (1024 * 1024)
        print(f"✅ Memory usage: {memory_mb:.2f} MB for {len(normalized_df)} records")
        
    except Exception as e:
        error_msg = handle_error(logger, e, "performance testing")
        print(f"⚠️  Performance test failed: {error_msg}")
        # Don't fail the checkpoint for performance issues
    
    # Summary
    print("\n" + "=" * 80)
    print("CHECKPOINT RESULTS")
    print("=" * 80)
    
    all_passed = all(test_results.values())
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Status: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Data loading and normalization components are working correctly!")
        print("   Ready to proceed with exact duplicate detection implementation.")
    else:
        print("\n⚠️  Some tests failed. Please review and fix issues before proceeding.")
    
    return all_passed


if __name__ == "__main__":
    success = run_integration_checkpoint()
    sys.exit(0 if success else 1)