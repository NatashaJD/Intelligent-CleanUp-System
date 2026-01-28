#!/usr/bin/env python3
"""
Debug script to test duplicate detection on sample data.
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

def debug_duplicate_detection():
    """Debug the duplicate detection process step by step."""
    
    print("🔍 Debugging Duplicate Detection")
    print("=" * 50)
    
    # Load sample data
    print("1️⃣ Loading sample data...")
    df = pd.read_csv('test_data/sample_customers.csv')
    print(f"   ✅ Loaded {len(df)} records")
    print(f"   📋 Columns: {list(df.columns)}")
    print("\n📊 Sample data preview:")
    print(df.head())
    
    # Test different field combinations
    test_scenarios = [
        {
            'name': 'Name + Email',
            'fields': ['name', 'email'],
            'types': {'name': 'text_aggressive', 'email': 'email'}
        },
        {
            'name': 'Name + Phone',
            'fields': ['name', 'phone'],
            'types': {'name': 'text_aggressive', 'phone': 'phone'}
        },
        {
            'name': 'Name Only',
            'fields': ['name'],
            'types': {'name': 'text_aggressive'}
        },
        {
            'name': 'Email Only',
            'fields': ['email'],
            'types': {'email': 'email'}
        }
    ]
    
    normalizer = DataNormalizer()
    
    for scenario in test_scenarios:
        print(f"\n🧪 Testing scenario: {scenario['name']}")
        print(f"   Fields: {scenario['fields']}")
        
        # Normalize data
        df_normalized = normalizer.normalize_dataframe(df.copy(), scenario['types'])
        
        # Test exact matching
        print("   🎯 Exact matching...")
        exact_matcher = ExactMatcher(normalizer)
        exact_groups = exact_matcher.find_exact_duplicates(
            df_normalized, 
            scenario['fields'], 
            scenario['types'], 
            use_normalized=True
        )
        print(f"      Found {len(exact_groups)} exact duplicate groups")
        
        # Test fuzzy matching
        print("   🔍 Fuzzy matching...")
        fuzzy_matcher = FuzzyMatcher(normalizer)
        fuzzy_groups = fuzzy_matcher.find_fuzzy_duplicates(
            df_normalized,
            scenario['fields'],
            threshold=70.0,  # Lower threshold
            algorithm='WRatio',
            field_configs=scenario['types'],
            use_normalized=True
        )
        print(f"      Found {len(fuzzy_groups)} fuzzy duplicate groups")
        
        # Show details if duplicates found
        all_groups = exact_groups + fuzzy_groups
        if all_groups:
            for i, group in enumerate(all_groups):
                print(f"      📋 Group {i+1}: {len(group.records)} records, {group.similarity_score:.1f}% similarity")
                for record in group.records:
                    name = record.get('name', 'N/A')
                    email = record.get('email', 'N/A')
                    print(f"         - {name} | {email}")
        
        print("   " + "-" * 40)
    
    # Test normalization effects
    print(f"\n🔧 Testing normalization effects...")
    test_fields = ['name', 'email', 'phone', 'address']
    
    for field in test_fields:
        if field in df.columns:
            print(f"\n   📝 Field: {field}")
            original_values = df[field].head(3).tolist()
            
            # Apply normalization
            if field == 'name':
                normalized = [normalizer.normalize_text_aggressive(val) for val in original_values]
            elif field == 'email':
                normalized = [normalizer.normalize_email(val) for val in original_values]
            elif field == 'phone':
                normalized = [normalizer.normalize_phone(val) for val in original_values]
            else:
                normalized = [normalizer.normalize_text(val) for val in original_values]
            
            for orig, norm in zip(original_values, normalized):
                print(f"      Original: '{orig}' → Normalized: '{norm}'")

if __name__ == "__main__":
    debug_duplicate_detection()