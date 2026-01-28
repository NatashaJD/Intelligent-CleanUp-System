#!/usr/bin/env python3
"""
Simple test to replicate the exact GUI workflow and find the issue.
"""

import pandas as pd
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dedupe_system.core.normalizer import DataNormalizer
from dedupe_system.core.exact_matcher import ExactMatcher
from dedupe_system.core.fuzzy_matcher import FuzzyMatcher

def simple_gui_test():
    """Test the exact same workflow as the GUI."""
    
    print("🧪 Simple GUI Workflow Test")
    print("=" * 50)
    
    # Step 1: Load data exactly like GUI (with dtype=str)
    print("1️⃣ Loading data like GUI...")
    df = pd.read_csv('test_data/sample_customers.csv', dtype=str)
    print(f"   ✅ Loaded {len(df)} records")
    print(f"   📋 Columns: {list(df.columns)}")
    
    # Show the actual data
    print("\n📊 Actual data:")
    for i, row in df.iterrows():
        print(f"   Row {i}: name='{row['name']}', email='{row['email']}'")
    
    # Step 2: Test with just 'name' field (simplest case)
    print("\n2️⃣ Testing with 'name' field only...")
    
    # Simulate GUI field selection
    selected_fields = ['name']
    field_types = {'name': 'text'}
    
    print(f"   Selected fields: {selected_fields}")
    print(f"   Field types: {field_types}")
    
    # Step 3: Normalize data
    print("\n3️⃣ Normalizing data...")
    normalizer = DataNormalizer()
    df_normalized = normalizer.normalize_dataframe(df.copy(), field_types)
    
    print(f"   ✅ Normalized columns: {list(df_normalized.columns)}")
    
    # Check normalization results
    if 'name_normalized' in df_normalized.columns:
        print("   📝 Normalization results:")
        for i, row in df_normalized.iterrows():
            original = df.iloc[i]['name']
            normalized = row['name_normalized']
            print(f"      Row {i}: '{original}' → '{normalized}'")
        
        # Check for duplicates in normalized data
        name_counts = df_normalized['name_normalized'].value_counts()
        duplicates = name_counts[name_counts > 1]
        print(f"\n   🔍 Duplicate normalized names: {duplicates.to_dict()}")
    else:
        print("   ❌ name_normalized column not found!")
        return
    
    # Step 4: Test exact matching
    print("\n4️⃣ Testing exact matching...")
    exact_matcher = ExactMatcher(normalizer)
    
    try:
        exact_groups = exact_matcher.find_exact_duplicates(
            df_normalized,
            selected_fields,
            field_types,
            use_normalized=True
        )
        
        print(f"   ✅ Found {len(exact_groups)} exact duplicate groups")
        
        for i, group in enumerate(exact_groups):
            print(f"   📋 Group {i+1}: {len(group.records)} records")
            for j, record in enumerate(group.records):
                name = record.get('name', 'N/A')
                email = record.get('email', 'N/A')
                print(f"      Record {j+1}: {name} | {email}")
    
    except Exception as e:
        print(f"   ❌ Exact matching failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 5: Test fuzzy matching
    print("\n5️⃣ Testing fuzzy matching...")
    fuzzy_matcher = FuzzyMatcher(normalizer)
    
    try:
        fuzzy_groups = fuzzy_matcher.find_fuzzy_duplicates(
            df_normalized,
            selected_fields,
            threshold=70.0,
            algorithm='WRatio',
            field_configs=field_types,
            use_normalized=True
        )
        
        print(f"   ✅ Found {len(fuzzy_groups)} fuzzy duplicate groups")
        
        for i, group in enumerate(fuzzy_groups):
            print(f"   📋 Group {i+1}: {len(group.records)} records, {group.similarity_score:.1f}% similarity")
            for j, record in enumerate(group.records):
                name = record.get('name', 'N/A')
                email = record.get('email', 'N/A')
                print(f"      Record {j+1}: {name} | {email}")
    
    except Exception as e:
        print(f"   ❌ Fuzzy matching failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_gui_test()