#!/usr/bin/env python3
"""
Test script showing how the normalizer helps with duplicate detection.

This script demonstrates how normalization makes duplicate detection more effective
by standardizing variations in the same data.
"""

import sys
from pathlib import Path
import pandas as pd

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dedupe_system.core.normalizer import DataNormalizer
from dedupe_system.core.loader import DataLoader
from dedupe_system.core.logging_config import setup_logging

def test_duplicate_detection_with_normalization():
    """Test how normalization improves duplicate detection."""
    
    # Set up logging
    logger = setup_logging("INFO", "logs")
    
    # Initialize components
    loader = DataLoader()
    normalizer = DataNormalizer()
    
    print("=" * 70)
    print("TESTING NORMALIZATION FOR DUPLICATE DETECTION")
    print("=" * 70)
    
    # Load our sample customer data
    print("\n1. Loading sample customer data...")
    try:
        df = loader.load_file("test_data/sample_customers.csv")
        print(f"✅ Loaded {len(df)} customer records")
        
        # Show original data
        print("\nOriginal customer data:")
        print(df[['name', 'email', 'phone', 'address', 'city', 'state']].to_string(index=False))
        
    except Exception as e:
        print(f"❌ Failed to load data: {e}")
        return
    
    # Configure normalization for duplicate detection
    print("\n2. Configuring normalization for duplicate detection...")
    field_configs = {
        'name': 'text',
        'email': 'email', 
        'phone': 'phone',
        'address': 'text_aggressive',  # More aggressive for address variations
        'city': 'text',
        'state': 'text'
    }
    
    # Normalize the data
    df_normalized = normalizer.normalize_dataframe(df, field_configs)
    
    print("\nNormalized data (key fields):")
    normalized_display = df_normalized[['name', 'name_normalized', 'email', 'email_normalized', 
                                      'phone', 'phone_normalized', 'address', 'address_normalized']]
    print(normalized_display.to_string(index=False))
    
    # Test composite key generation for exact matching
    print("\n3. Testing composite key generation for exact duplicate detection...")
    
    # Test different key combinations
    key_combinations = [
        (['name', 'email'], "Name + Email"),
        (['name', 'phone'], "Name + Phone"), 
        (['email', 'phone'], "Email + Phone"),
        (['name', 'address', 'city'], "Name + Address + City")
    ]
    
    for key_fields, description in key_combinations:
        print(f"\n{description} composite keys:")
        
        # Create composite keys for each record
        composite_keys = []
        for idx, row in df.iterrows():
            record = row.to_dict()
            composite_key = normalizer.create_composite_key(record, key_fields, field_configs)
            composite_keys.append(composite_key)
        
        # Show composite keys and identify duplicates
        df_with_keys = df.copy()
        df_with_keys['composite_key'] = composite_keys
        
        # Find duplicates based on composite keys
        duplicate_groups = df_with_keys.groupby('composite_key').size()
        duplicates = duplicate_groups[duplicate_groups > 1]
        
        if len(duplicates) > 0:
            print(f"  🔍 Found {len(duplicates)} duplicate groups:")
            for key, count in duplicates.items():
                print(f"    Key: '{key}' -> {count} records")
                duplicate_records = df_with_keys[df_with_keys['composite_key'] == key]
                for _, record in duplicate_records.iterrows():
                    print(f"      ID {record['id']}: {record['name']} | {record['email']} | {record['phone']}")
        else:
            print(f"  ✅ No exact duplicates found with this key combination")
    
    # Demonstrate the power of normalization
    print("\n4. Demonstrating normalization effectiveness...")
    
    # Show how normalization catches variations that would be missed otherwise
    print("\nBefore normalization - these look different:")
    variations = [
        ("John Smith", "  JOHN SMITH  "),
        ("john.smith@email.com", "JOHN.SMITH@EMAIL.COM"),
        ("555-0101", "(555) 0101"),
        ("123 Main St", "123 Main Street"),
        ("Springfield", "springfield"),
        ("Illinois", "IL")
    ]
    
    for original, variation in variations:
        print(f"  '{original}' vs '{variation}'")
    
    print("\nAfter normalization - these are identical:")
    for original, variation in variations:
        norm_original = normalizer.normalize_text(original)
        norm_variation = normalizer.normalize_text(variation)
        match = "✅ MATCH" if norm_original == norm_variation else "❌ NO MATCH"
        print(f"  '{norm_original}' vs '{norm_variation}' -> {match}")
    
    # Show specific examples from our data
    print("\n5. Real duplicate examples from our sample data...")
    
    # Records 1 and 3 are the same person with slight variations
    record1 = df.iloc[0].to_dict()  # John Smith
    record3 = df.iloc[2].to_dict()  # John Smith with variations
    
    print("Comparing records 1 and 3 (same person, different formatting):")
    print(f"Record 1: {record1['name']} | {record1['email']} | {record1['address']}")
    print(f"Record 3: {record3['name']} | {record3['email']} | {record3['address']}")
    
    # Generate composite keys
    key_fields = ['name', 'phone', 'city', 'state', 'zip_code']
    key1 = normalizer.create_composite_key(record1, key_fields, field_configs)
    key3 = normalizer.create_composite_key(record3, key_fields, field_configs)
    
    print(f"\nComposite keys:")
    print(f"Record 1: '{key1}'")
    print(f"Record 3: '{key3}'")
    print(f"Match: {'✅ YES' if key1 == key3 else '❌ NO'}")
    
    # Records 2 and 5 are also the same person
    record2 = df.iloc[1].to_dict()  # Jane Doe
    record5 = df.iloc[4].to_dict()  # Jane Doe with variations
    
    print(f"\nComparing records 2 and 5 (same person, different formatting):")
    print(f"Record 2: {record2['name']} | {record2['email']} | {record2['address']}")
    print(f"Record 5: {record5['name']} | {record5['email']} | {record5['address']}")
    
    key2 = normalizer.create_composite_key(record2, key_fields, field_configs)
    key5 = normalizer.create_composite_key(record5, key_fields, field_configs)
    
    print(f"\nComposite keys:")
    print(f"Record 2: '{key2}'")
    print(f"Record 5: '{key5}'")
    print(f"Match: {'✅ YES' if key2 == key5 else '❌ NO'}")
    
    print("\n" + "=" * 70)
    print("NORMALIZATION FOR DUPLICATE DETECTION TESTING COMPLETE")
    print("=" * 70)
    print("\n🎯 Key Takeaways:")
    print("  • Normalization standardizes data variations")
    print("  • Composite keys combine multiple fields for better matching")
    print("  • Different normalization types handle different data formats")
    print("  • This enables accurate duplicate detection despite formatting differences")


if __name__ == "__main__":
    test_duplicate_detection_with_normalization()