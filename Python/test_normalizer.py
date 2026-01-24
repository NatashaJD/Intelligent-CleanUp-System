#!/usr/bin/env python3
"""
Test script for the Data Normalizer component.

This script demonstrates and tests the data normalization functionality
with various data types and edge cases.
"""

import sys
from pathlib import Path
import pandas as pd

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dedupe_system.core.normalizer import DataNormalizer
from dedupe_system.core.logging_config import setup_logging
from dedupe_system.core.exceptions import handle_error

def test_normalizer():
    """Test the DataNormalizer with various data types."""
    
    # Set up logging
    logger = setup_logging("INFO", "logs")
    
    # Initialize the normalizer
    normalizer = DataNormalizer()
    
    print("=" * 60)
    print("TESTING DATA NORMALIZER COMPONENT")
    print("=" * 60)
    
    # Test text normalization
    print("\n1. Testing text normalization...")
    test_texts = [
        "John Smith",
        "  JANE DOE  ",
        "Bob O'Connor",
        "María García",
        "Jean-Pierre Dupont",
        "李小明",  # Chinese characters
        "",
        None,
        "  Multiple   Spaces   Here  "
    ]
    
    print("Text normalization results:")
    for text in test_texts:
        normalized = normalizer.normalize_text(text)
        print(f"  '{text}' -> '{normalized}'")
    
    # Test aggressive text normalization
    print("\n2. Testing aggressive text normalization...")
    aggressive_texts = [
        "John Smith Jr.",
        "ABC Corp., Inc.",
        "123 Main St. #456",
        "Phone: (555) 123-4567",
        "Price: $99.99"
    ]
    
    print("Aggressive text normalization results:")
    for text in aggressive_texts:
        normal = normalizer.normalize_text(text)
        aggressive = normalizer.normalize_text_aggressive(text)
        print(f"  '{text}'")
        print(f"    Normal: '{normal}'")
        print(f"    Aggressive: '{aggressive}'")
    
    # Test date normalization
    print("\n3. Testing date normalization...")
    test_dates = [
        "2023-01-15",
        "01/15/2023",
        "15/01/2023",
        "January 15, 2023",
        "Jan 15, 2023",
        "15 Jan 2023",
        "20230115",
        "01-15-23",
        "invalid date",
        "",
        None
    ]
    
    print("Date normalization results:")
    for date in test_dates:
        normalized = normalizer.normalize_date(date)
        print(f"  '{date}' -> '{normalized}'")
    
    # Test numeric normalization
    print("\n4. Testing numeric normalization...")
    test_numbers = [
        "123.45",
        "$99.99",
        "1,234.56",
        "€50.00",
        "25%",
        "  42  ",
        "-123.45",
        "abc123",
        "12.34.56",
        "",
        None
    ]
    
    print("Numeric normalization results:")
    for number in test_numbers:
        normalized = normalizer.normalize_numeric(number)
        print(f"  '{number}' -> '{normalized}'")
    
    # Test phone normalization
    print("\n5. Testing phone normalization...")
    test_phones = [
        "555-123-4567",
        "(555) 123-4567",
        "555.123.4567",
        "15551234567",
        "1-555-123-4567",
        "+1 555 123 4567",
        "555 123 4567",
        "invalid phone",
        "",
        None
    ]
    
    print("Phone normalization results:")
    for phone in test_phones:
        normalized = normalizer.normalize_phone(phone)
        print(f"  '{phone}' -> '{normalized}'")
    
    # Test email normalization
    print("\n6. Testing email normalization...")
    test_emails = [
        "john.smith@email.com",
        "JANE.DOE@EMAIL.COM",
        "  bob@company.org  ",
        "invalid-email",
        "user@domain",
        "",
        None
    ]
    
    print("Email normalization results:")
    for email in test_emails:
        normalized = normalizer.normalize_email(email)
        print(f"  '{email}' -> '{normalized}'")
    
    # Test composite key generation
    print("\n7. Testing composite key generation...")
    test_records = [
        {
            "name": "John Smith",
            "email": "john.smith@email.com",
            "phone": "555-123-4567",
            "date": "2023-01-15"
        },
        {
            "name": "  JOHN SMITH  ",
            "email": "JOHN.SMITH@EMAIL.COM",
            "phone": "(555) 123-4567",
            "date": "01/15/2023"
        },
        {
            "name": "Jane Doe",
            "email": "jane.doe@email.com",
            "phone": "555-987-6543",
            "date": "2023-02-20"
        }
    ]
    
    key_fields = ["name", "email"]
    field_configs = {"name": "text", "email": "email"}
    
    print("Composite key generation results:")
    for i, record in enumerate(test_records):
        composite_key = normalizer.create_composite_key(record, key_fields, field_configs)
        print(f"  Record {i+1}: '{composite_key}'")
    
    # Test DataFrame normalization
    print("\n8. Testing DataFrame normalization...")
    
    # Create test DataFrame
    test_data = {
        'id': [1, 2, 3, 4],
        'name': ['John Smith', '  JANE DOE  ', 'Bob O\'Connor', 'María García'],
        'email': ['john@email.com', 'JANE@EMAIL.COM', 'bob@company.org', 'maria@test.com'],
        'phone': ['555-123-4567', '(555) 987-6543', '555.111.2222', '1-555-333-4444'],
        'price': ['$99.99', '149.50', '€75.00', '25.99'],
        'date': ['2023-01-15', '01/20/2023', 'Feb 15, 2023', '2023-03-01']
    }
    
    df = pd.DataFrame(test_data)
    print("Original DataFrame:")
    print(df.to_string(index=False))
    
    # Configure normalization
    field_configs = {
        'name': 'text',
        'email': 'email',
        'phone': 'phone',
        'price': 'numeric',
        'date': 'date'
    }
    
    # Normalize DataFrame
    df_normalized = normalizer.normalize_dataframe(df, field_configs)
    
    print("\nNormalized DataFrame (showing normalized columns):")
    normalized_cols = [col for col in df_normalized.columns if col.endswith('_normalized')]
    print(df_normalized[['name', 'name_normalized', 'email', 'email_normalized', 
                        'phone', 'phone_normalized', 'price', 'price_normalized',
                        'date', 'date_normalized']].to_string(index=False))
    
    # Get normalization stats
    stats = normalizer.get_normalization_stats(df_normalized, field_configs)
    print(f"\nNormalization Statistics:")
    print(f"  Total fields normalized: {stats['total_fields_normalized']}")
    print(f"  Normalization types used: {stats['normalization_types']}")
    
    for field, field_stats in stats['field_stats'].items():
        print(f"  {field}:")
        print(f"    Original unique values: {field_stats['original_unique_count']}")
        print(f"    Normalized unique values: {field_stats['normalized_unique_count']}")
        print(f"    Reduction ratio: {field_stats['reduction_ratio']:.2f}")
    
    print("\n" + "=" * 60)
    print("DATA NORMALIZER TESTING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_normalizer()