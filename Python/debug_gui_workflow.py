#!/usr/bin/env python3
"""
Debug script to simulate the exact GUI workflow and find where duplicates are lost.
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

def debug_gui_workflow():
    """Debug the exact GUI workflow step by step."""
    
    print("🔍 Debugging GUI Workflow")
    print("=" * 60)
    
    # Step 1: Load data exactly like GUI
    print("1️⃣ Loading data (GUI simulation)...")
    df = pd.read_csv('test_data/sample_customers.csv', dtype=str)
    print(f"   ✅ Loaded {len(df)} records")
    print(f"   📋 Columns: {list(df.columns)}")
    print(f"   📊 Data types: {df.dtypes.to_dict()}")
    
    # Show first few rows
    print("\n📋 First 3 rows:")
    for i, row in df.head(3).iterrows():
        print(f"   Row {i}: {dict(row)}")
    
    # Step 2: Test different GUI configurations
    test_configs = [
        {
            'name': 'Name Only (Exact)',
            'fields': ['name'],
            'types': {'name': 'text'},
            'exact': True,
            'fuzzy': False
        },
        {
            'name': 'Name Only (Fuzzy)',
            'fields': ['name'],
            'types': {'name': 'text'},
            'exact': False,
            'fuzzy': True,
            'threshold': 80.0,
            'algorithm': 'WRatio'
        },
        {
            'name': 'Name + Email (Both)',
            'fields': ['name', 'email'],
            'types': {'name': 'text', 'email': 'email'},
            'exact': True,
            'fuzzy': True,
            'threshold': 70.0,
            'algorithm': 'WRatio'
        }
    ]
    
    for config in test_configs:
        print(f"\n🧪 Testing: {config['name']}")
        print(f"   Fields: {config['fields']}")
        print(f"   Types: {config['types']}")
        
        try:
            # Step 3: Normalize data (GUI step)
            print("   📝 Normalizing data...")
            normalizer = DataNormalizer()
            df_normalized = normalizer.normalize_dataframe(df.copy(), config['types'])
            
            # Show normalization results
            for field in config['fields']:
                if field in df.columns:
                    original_sample = df[field].iloc[0]
                    normalized_sample = df_normalized[f"{field}_normalized"].iloc[0] if f"{field}_normalized" in df_normalized.columns else "Not found"
                    print(f"      {field}: '{original_sample}' → '{normalized_sample}'")
            
            # Step 4: Create MatchingConfig (GUI step)
            matching_config = MatchingConfig(
                exact_matching_enabled=config['exact'],
                fuzzy_matching_enabled=config['fuzzy'],
                fuzzy_threshold=config.get('threshold', 80.0),
                key_fields=config['fields'],
                fuzzy_fields=config['fields'],
                similarity_algorithm=config.get('algorithm', 'WRatio')
            )
            
            print(f"   ⚙️ Config: exact={matching_config.exact_matching_enabled}, fuzzy={matching_config.fuzzy_matching_enabled}")
            
            # Step 5: Run duplicate detection (GUI step)
            duplicate_groups = []
            
            if matching_config.exact_matching_enabled:
                print("   🎯 Running exact matching...")
                exact_matcher = ExactMatcher(normalizer)
                exact_groups = exact_matcher.find_exact_duplicates(
                    df_normalized,
                    matching_config.key_fields,
                    config['types'],
                    use_normalized=True
                )
                duplicate_groups.extend(exact_groups)
                print(f"      Found {len(exact_groups)} exact groups")
            
            if matching_config.fuzzy_matching_enabled:
                print("   🔍 Running fuzzy matching...")
                fuzzy_matcher = FuzzyMatcher(normalizer)
                fuzzy_groups = fuzzy_matcher.find_fuzzy_duplicates(
                    df_normalized,
                    matching_config.key_fields,
                    threshold=matching_config.fuzzy_threshold,
                    algorithm=matching_config.similarity_algorithm,
                    field_configs=config['types'],
                    use_normalized=True
                )
                duplicate_groups.extend(fuzzy_groups)
                print(f"      Found {len(fuzzy_groups)} fuzzy groups")
            
            # Step 6: Show results
            print(f"   📊 Total groups found: {len(duplicate_groups)}")
            
            if duplicate_groups:
                for i, group in enumerate(duplicate_groups):
                    print(f"      Group {i+1}: {len(group.records)} records, {group.similarity_score:.1f}% similarity")
                    for j, record in enumerate(group.records):
                        name = record.get('name', 'N/A')
                        email = record.get('email', 'N/A')
                        print(f"         Record {j+1}: {name} | {email}")
            else:
                print("      ❌ NO DUPLICATES FOUND")
                
                # Additional debugging for no results
                print("   🔍 Debugging why no duplicates found...")
                
                # Check if normalized data exists
                for field in config['fields']:
                    norm_field = f"{field}_normalized"
                    if norm_field in df_normalized.columns:
                        unique_values = df_normalized[norm_field].unique()
                        print(f"      {field} normalized unique values: {list(unique_values)}")
                        value_counts = df_normalized[norm_field].value_counts()
                        duplicates = value_counts[value_counts > 1]
                        if len(duplicates) > 0:
                            print(f"      {field} has duplicates: {duplicates.to_dict()}")
                        else:
                            print(f"      {field} has no duplicate values")
                    else:
                        print(f"      ❌ Normalized field {norm_field} not found!")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print("   " + "-" * 50)

if __name__ == "__main__":
    debug_gui_workflow()