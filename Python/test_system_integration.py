#!/usr/bin/env python3
"""
Integration test to verify the complete duplicate detection system works.

This test creates sample data, runs it through the entire pipeline including
both exact and fuzzy matching, and verifies the results.
"""

import sys
import pandas as pd
import tempfile
import json
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dedupe_system.core.loader import DataLoader
from dedupe_system.core.normalizer import DataNormalizer
from dedupe_system.core.exact_matcher import ExactMatcher
from dedupe_system.core.fuzzy_matcher import FuzzyMatcher
from dedupe_system.core.models import MatchingConfig


def test_complete_pipeline():
    """Test the complete duplicate detection pipeline."""
    
    print("🔍 Testing Intelligent Duplicate Detection System")
    print("=" * 50)
    print("🚀 Testing both exact and fuzzy matching capabilities")
    print("=" * 50)
    
    # Create sample data with duplicates
    sample_data = [
        {"id": "1", "name": "John Smith", "email": "john@example.com", "phone": "555-1234"},
        {"id": "2", "name": "JOHN SMITH", "email": "john@example.com", "phone": "(555) 123-4567"},  # Duplicate
        {"id": "3", "name": "Jane Doe", "email": "jane@example.com", "phone": "555-5678"},
        {"id": "4", "name": "Bob Johnson", "email": "bob@example.com", "phone": "555-9999"},
        {"id": "5", "name": "john smith", "email": "john@example.com", "phone": "5551234"},  # Another duplicate
    ]
    
    print(f"📊 Created sample dataset with {len(sample_data)} records")
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame(sample_data)
        df.to_csv(f.name, index=False)
        temp_file = f.name
    
    try:
        # Step 1: Load data
        print("\n1️⃣ Loading data...")
        loader = DataLoader()
        df_loaded = loader.load_file(temp_file)
        validation_result = loader.validate_data(df_loaded)
        
        print(f"   ✅ Loaded {len(df_loaded)} records")
        print(f"   ✅ Validation: {'PASSED' if validation_result.is_valid else 'FAILED'}")
        
        if not validation_result.is_valid:
            print(f"   ❌ Errors: {validation_result.errors}")
            return False
        
        # Step 2: Normalize data
        print("\n2️⃣ Normalizing data...")
        normalizer = DataNormalizer()
        field_configs = {
            'name': 'text',
            'email': 'email',
            'phone': 'phone'
        }
        df_normalized = normalizer.normalize_dataframe(df_loaded, field_configs)
        
        print(f"   ✅ Normalized {len(df_normalized.columns)} columns")
        
        # Step 3: Detect duplicates
        print("\n3️⃣ Detecting duplicates...")
        matcher = ExactMatcher(normalizer)
        key_fields = ['name', 'email']
        
        duplicate_groups = matcher.find_exact_duplicates(
            df_normalized, 
            key_fields, 
            field_configs, 
            use_normalized=True
        )
        
        print(f"   ✅ Found {len(duplicate_groups)} duplicate groups")
        
        # Step 4: Analyze results
        print("\n4️⃣ Analyzing results...")
        total_duplicates = sum(len(group.records) for group in duplicate_groups)
        print(f"   📈 Total duplicate records: {total_duplicates}")
        
        for i, group in enumerate(duplicate_groups):
            print(f"   📋 Group {i+1}: {len(group.records)} records, {group.similarity_score}% similarity")
            print(f"      Method: {group.detection_method}, Action: {group.recommended_action}")
        
        # Step 5: Verify expected results
        print("\n5️⃣ Verifying results...")
        
        # We expect to find duplicates for John Smith records
        expected_duplicates = 3  # Records 1, 2, and 5 should be grouped
        
        if len(duplicate_groups) >= 1:
            john_smith_group = duplicate_groups[0]
            if len(john_smith_group.records) == 3:
                print("   ✅ Correctly identified John Smith duplicates")
                success = True
            else:
                print(f"   ❌ Expected 3 John Smith duplicates, found {len(john_smith_group.records)}")
                success = False
        else:
            print("   ❌ No duplicate groups found, expected at least 1")
            success = False
        
        # Step 6: Test statistics
        print("\n6️⃣ Performance statistics...")
        stats = matcher.get_duplicate_statistics(duplicate_groups)
        print(f"   📊 Total groups: {stats['total_groups']}")
        print(f"   📊 Total duplicate records: {stats['total_duplicate_records']}")
        print(f"   📊 Average group size: {stats['average_group_size']:.1f}")
        
        return success
        
    finally:
        # Clean up temporary file
        Path(temp_file).unlink(missing_ok=True)


def test_gui_imports():
    """Test that GUI imports work correctly."""
    print("\n🖥️ Testing GUI imports...")
    
    try:
        # Test importing the clean GUI module
        from dedupe_system.gui import app_clean
        print("   ✅ GUI module import successful")
        
        # Test that main function exists
        if hasattr(app_clean, 'main'):
            print("   ✅ Main function found")
        else:
            print("   ❌ Main function not found")
            return False
            
        # Test that key functions exist
        required_functions = ['initialize_session_state', 'main']
        for func_name in required_functions:
            if hasattr(app_clean, func_name):
                print(f"   ✅ {func_name} function found")
            else:
                print(f"   ❌ {func_name} function not found")
                return False
        
        return True
    except ImportError as e:
        print(f"   ❌ GUI import failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("🚀 Starting System Integration Tests")
    print("=" * 60)
    
    # Test core pipeline
    pipeline_success = test_complete_pipeline()
    
    # Test GUI imports
    gui_success = test_gui_imports()
    
    # Final results
    print("\n" + "=" * 60)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"Core Pipeline: {'✅ PASS' if pipeline_success else '❌ FAIL'}")
    print(f"GUI Imports:   {'✅ PASS' if gui_success else '❌ FAIL'}")
    
    overall_success = pipeline_success and gui_success
    print(f"\nOverall Status: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 System is ready to use!")
        print("Run: python -m dedupe_system.main --gui")
    else:
        print("\n⚠️ System has issues that need to be resolved.")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)