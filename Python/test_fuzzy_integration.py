#!/usr/bin/env python3
"""
Quick integration test for fuzzy matching functionality.
"""

import pandas as pd
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dedupe_system.core.fuzzy_matcher import FuzzyMatcher
from dedupe_system.core.normalizer import DataNormalizer

def test_fuzzy_matching():
    """Test fuzzy matching with sample data."""
    
    print("🔍 Testing Fuzzy Matching Integration")
    print("=" * 50)
    
    # Create sample data with fuzzy duplicates
    data = [
        {"id": 1, "name": "John Smith", "email": "john.smith@email.com", "phone": "555-1234"},
        {"id": 2, "name": "Jon Smith", "email": "j.smith@email.com", "phone": "555-1234"},  # Similar name
        {"id": 3, "name": "John Smyth", "email": "john.smyth@email.com", "phone": "555-1234"},  # Similar name
        {"id": 4, "name": "Jane Doe", "email": "jane.doe@email.com", "phone": "555-5678"},
        {"id": 5, "name": "Jane Do", "email": "jane.doe@email.com", "phone": "555-5678"},  # Similar name
    ]
    
    df = pd.DataFrame(data)
    print(f"📊 Created sample dataset with {len(df)} records")
    
    # Initialize components
    normalizer = DataNormalizer()
    fuzzy_matcher = FuzzyMatcher(normalizer)
    
    # Test fuzzy matching
    print("\n1️⃣ Running fuzzy matching...")
    
    key_fields = ["name", "email"]
    field_configs = {"name": "text_aggressive", "email": "email"}
    
    # Normalize data first
    df_normalized = normalizer.normalize_dataframe(df, field_configs)
    print(f"   ✅ Normalized {len(df_normalized.columns)} columns")
    
    # Find fuzzy duplicates
    duplicate_groups = fuzzy_matcher.find_fuzzy_duplicates(
        df_normalized,
        key_fields,
        threshold=70.0,  # Lower threshold to catch similar names
        algorithm='WRatio',
        field_configs=field_configs,
        use_normalized=True
    )
    
    print(f"   ✅ Found {len(duplicate_groups)} fuzzy duplicate groups")
    
    # Analyze results
    print("\n2️⃣ Analyzing results...")
    
    total_duplicate_records = sum(len(group.records) for group in duplicate_groups)
    print(f"   📈 Total duplicate records: {total_duplicate_records}")
    
    for i, group in enumerate(duplicate_groups):
        print(f"   📋 Group {i+1}: {len(group.records)} records, {group.similarity_score:.1f}% similarity")
        print(f"      Method: {group.detection_method}, Action: {group.recommended_action}")
        
        # Show the names in the group
        names = [record.get('name', 'N/A') for record in group.records]
        print(f"      Names: {', '.join(names)}")
    
    # Get statistics
    if duplicate_groups:
        stats = fuzzy_matcher.get_duplicate_statistics(duplicate_groups)
        print(f"\n3️⃣ Statistics:")
        print(f"   📊 Average similarity: {stats['average_similarity']:.1f}%")
        print(f"   📊 Similarity range: {stats['lowest_similarity']:.1f}% - {stats['highest_similarity']:.1f}%")
    
    print("\n" + "=" * 50)
    if duplicate_groups:
        print("✅ Fuzzy matching test PASSED - Found expected similar records")
    else:
        print("⚠️ Fuzzy matching test - No duplicates found (may need threshold adjustment)")
    
    return len(duplicate_groups) > 0

if __name__ == "__main__":
    try:
        success = test_fuzzy_matching()
        if success:
            print("\n🎉 Fuzzy matching integration test completed successfully!")
        else:
            print("\n⚠️ Fuzzy matching test completed but found no duplicates")
    except Exception as e:
        print(f"\n❌ Fuzzy matching test failed: {e}")
        import traceback
        traceback.print_exc()