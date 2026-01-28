#!/usr/bin/env python3
"""
Test script to verify the GUI field selection logic works correctly.
"""

import pandas as pd

def test_field_selection_logic():
    """Test the smart field selection logic."""
    
    print("🧪 Testing GUI Field Selection Logic")
    print("=" * 50)
    
    # Create test dataframe similar to sample data
    df = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['John Smith', 'Jane Doe', 'Bob Johnson'],
        'email': ['john@email.com', 'jane@email.com', 'bob@email.com'],
        'phone': ['555-0101', '555-0102', '555-0103'],
        'address': ['123 Main St', '456 Oak Ave', '789 Pine Rd']
    })
    
    print(f"📊 Test DataFrame columns: {list(df.columns)}")
    
    # Simulate the GUI logic
    available_fields = list(df.columns)
    
    # Smart default selection - exclude common ID field names
    id_field_names = ['id', 'ID', 'Id', 'index', 'INDEX', 'Index', 'key', 'KEY', 'Key', 
                      'record_id', 'recordid', 'row_id', 'rowid', 'pk', 'primary_key']
    
    # Filter out likely ID fields for default selection
    non_id_fields = [field for field in available_fields if field not in id_field_names]
    print(f"🚫 Non-ID fields: {non_id_fields}")
    
    # Smart default: prefer name, email, phone type fields
    preferred_fields = []
    for field in non_id_fields:
        field_lower = field.lower()
        if any(keyword in field_lower for keyword in ['name', 'email', 'phone', 'address', 'title']):
            preferred_fields.append(field)
    
    print(f"⭐ Preferred fields: {preferred_fields}")
    
    # Default selection: use preferred fields (up to 3) or first non-ID fields
    if preferred_fields:
        default_selection = preferred_fields[:3]
    else:
        default_selection = non_id_fields[:3] if len(non_id_fields) >= 3 else non_id_fields
    
    print(f"✅ Default selection: {default_selection}")
    
    # Test ID field warning
    test_selections = [
        ['name', 'email'],           # Good selection
        ['id', 'name', 'email'],     # Bad selection (includes ID)
        ['name', 'phone', 'address'] # Good selection
    ]
    
    for selection in test_selections:
        selected_id_fields = [field for field in selection if field in id_field_names]
        if selected_id_fields:
            print(f"⚠️  Selection {selection} includes ID fields: {selected_id_fields}")
        else:
            print(f"✅ Selection {selection} is good (no ID fields)")

if __name__ == "__main__":
    test_field_selection_logic()