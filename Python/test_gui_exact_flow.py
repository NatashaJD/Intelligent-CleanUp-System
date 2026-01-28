#!/usr/bin/env python3
"""
Test the exact GUI flow step by step to identify the issue.
"""

import pandas as pd
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dedupe_system.core.loader import DataLoader
from dedupe_system.core.normalizer import DataNormalizer
from dedupe_system.core.exact_matcher import ExactMatcher
from dedupe_system.core.fuzzy_matcher import FuzzyMatcher
from dedupe_system.core.models import MatchingConfig

def test_exact_gui_flow():
    """Test the exact same flow as the GUI."""
    
    print("🔍 Testing Exact GUI Flow")
    print("=" * 50)
    
    # Step 1: Load CSV exactly like GUI (with dtype=str)
    print("1️⃣ Loading CSV file...")
    df = pd.read_csv('test_data/sample_customers.csv', 
                     dtype=str,
                     na_values=['', 'NULL', 'null', 'None', 'N/A', 'n/a'],
                     keep_default_na=True)
    
    print(f"   ✅ Loaded {len(df)} records")
    print(f"   📋 Columns: {list(df.columns)}")
    
    # Step 2: Validate data using DataLoader
    print("\n2️⃣ Validating data...")
    loader = DataLoader(max_file_size_mb=100, max_preview_rows=1000)
    validation_result = loader.validate_data(df)
    
    print(f"   ✅ Validation result: {validation_result.is_valid}")
    if validation_result.errors:
        print(f"   ❌ Errors: {validation_result.errors}")
    if validation_result.warnings:
        print(f"   ⚠️ Warnings: {validation_result.warnings}")
    
    # Step 3: Test simple field selection (name only)
    print("\n3️⃣ Testing field selection: ['name']")
    selected_fields = ['name']
    field_types = {'name': 'text'}
    
    # Step 4: Create MatchingConfig
    print("\n4️⃣ Creating matching configuration...")
    matching_config = MatchingConfig(
        exact_matching_enabled=True,
        fuzzy_matching_enabled=False,
        fuzzy_threshold=80.0,
        key_fields=selected_fields,
        fuzzy_fields=selected_fields,
        similarity_algorithm='WRatio'
    )
    
    print(f"   ✅ Config created: exact={matching_config.exact_matching_enabled}")
    
    # Step 5: Normalize data
    print("\n5️⃣ Normalizing data...")
    normalizer = DataNormalizer()
    df_normalized = normalizer.normalize_dataframe(df, field_types)
    
    print(f"   ✅ Normalized columns: {list(df_normalized.columns)}")
    
    # Check normalization results
    if 'name_normalized' in df_normalized.columns:
        print("   📝 Name normalization samples:")
        for i in range(min(5, len(df_normalized))):
            original = df.iloc[i]['name']
            normalized = df_normalized.iloc[i]['name_normalized']
            print(f"      '{original}' → '{normalized}'")
    else:
        print("   ❌ name_normalized column not found!")
        return
    
    # Step 6: Run exact matching
    print("\n6️⃣ Running exact duplicate detection...")
    duplicate_groups = []
    
    exact_matcher = ExactMatcher(normalizer)
    exact_groups = exact_matcher.find_exact_duplicates(
        df_normalized,
        matching_config.key_fields,
        field_types,
        use_normalized=True
    )
    
    duplicate_groups.extend(exact_groups)
    
    print(f"   ✅ Found {len(exact_groups)} exact duplicate groups")
    print(f"   📊 Total duplicate groups: {len(duplicate_groups)}")
    
    # Step 7: Show detailed results
    if duplicate_groups:
        print("\n7️⃣ Duplicate groups found:")
        for i, group in enumerate(duplicate_groups):
            print(f"   📋 Group {i+1}:")
            print(f"      - Records: {len(group.records)}")
            print(f"      - Similarity: {group.similarity_score:.1f}%")
            print(f"      - Method: {group.detection_method}")
            print(f"      - Action: {group.recommended_action}")
            
            print("      - Records in group:")
            for j, record in enumerate(group.records):
                name = record.get('name', 'N/A')
                email = record.get('email', 'N/A')
                original_index = record.get('_original_index', 'N/A')
                print(f"        {j+1}. {name} | {email} (index: {original_index})")
    else:
        print("\n7️⃣ ❌ NO DUPLICATE GROUPS FOUND")
        
        # Debug why no duplicates found
        print("\n🔍 Debugging why no duplicates found...")
        
        # Check normalized values
        if 'name_normalized' in df_normalized.columns:
            name_values = df_normalized['name_normalized'].tolist()
            print(f"   📝 All normalized names: {name_values}")
            
            # Check for duplicates manually
            from collections import Counter
            name_counts = Counter(name_values)
            duplicates = {name: count for name, count in name_counts.items() if count > 1}
            
            if duplicates:
                print(f"   ✅ Found duplicate names: {duplicates}")
            else:
                print(f"   ❌ No duplicate names found in normalized data")
        
        # Check original values
        original_names = df['name'].tolist()
        print(f"   📝 Original names: {original_names}")
        
        original_counts = Counter(original_names)
        original_duplicates = {name: count for name, count in original_counts.items() if count > 1}
        
        if original_duplicates:
            print(f"   ✅ Original data has duplicates: {original_duplicates}")
        else:
            print(f"   ❌ No duplicates in original data either")

if __name__ == "__main__":
    test_exact_gui_flow()