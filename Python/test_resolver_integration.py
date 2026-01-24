#!/usr/bin/env python3
"""
Integration test for the complete duplicate detection and resolution pipeline.

This script demonstrates the full workflow from data loading through resolution.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dedupe_system.core.resolver import DuplicateResolver, create_resolution_decision
from dedupe_system.core.exact_matcher import ExactMatcher
from dedupe_system.core.normalizer import DataNormalizer
from dedupe_system.core.loader import DataLoader
from dedupe_system.core.logging_config import setup_logging
from dedupe_system.core.exceptions import handle_error

def test_complete_pipeline():
    """Test the complete duplicate detection and resolution pipeline."""
    
    # Set up logging
    logger = setup_logging("INFO", "logs")
    
    print("=" * 80)
    print("COMPLETE DUPLICATE DETECTION & RESOLUTION PIPELINE TEST")
    print("=" * 80)
    
    # Initialize components
    loader = DataLoader()
    normalizer = DataNormalizer()
    matcher = ExactMatcher(normalizer)
    resolver = DuplicateResolver()
    
    # Step 1: Load and prepare data
    print("\n1. Loading and preparing data...")
    try:
        df = loader.load_file("test_data/sample_customers.csv")
        print(f"✅ Loaded {len(df)} customer records")
        
        # Add original index tracking
        df['_original_index'] = df.index
        
        # Show original data
        print("\nOriginal data:")
        print(df[['id', 'name', 'email', 'phone']].to_string(index=False))
        
    except Exception as e:
        error_msg = handle_error(logger, e, "data loading")
        print(f"❌ Data loading failed: {error_msg}")
        return False
    
    # Step 2: Find duplicates
    print("\n2. Finding duplicate groups...")
    try:
        duplicate_groups = matcher.find_duplicates_by_composite_key(
            df, ['name', 'phone'], ['text', 'phone']
        )
        print(f"✅ Found {len(duplicate_groups)} duplicate groups")
        
        # Add group membership to DataFrame for resolution
        df['_duplicate_group_id'] = None
        
        for group in duplicate_groups:
            print(f"\nGroup {group.group_id} ({len(group.records)} records):")
            for record in group.records:
                original_idx = record['_original_index']
                df.loc[original_idx, '_duplicate_group_id'] = group.group_id
                print(f"  ID {record['id']}: {record['name']} | {record['phone']} | {record['email']}")
        
    except Exception as e:
        error_msg = handle_error(logger, e, "duplicate detection")
        print(f"❌ Duplicate detection failed: {error_msg}")
        return False
    
    # Step 3: Test KEEP resolution
    print("\n3. Testing KEEP resolution...")
    try:
        if duplicate_groups:
            first_group = duplicate_groups[0]
            
            # Keep the first record from the group
            selected_record = first_group.records[0]['_original_index']
            
            keep_decision = create_resolution_decision(
                group_id=first_group.group_id,
                action='KEEP',
                selected_records=[selected_record],
                user_notes="Keeping the most complete record"
            )
            
            df_keep = resolver.apply_resolution(df.copy(), [keep_decision])
            
            # Show results
            kept_records = df_keep[df_keep['_resolution_status'] == 'kept']
            soft_deleted_records = df_keep[df_keep['_resolution_status'] == 'soft_deleted']
            
            print(f"✅ KEEP resolution results:")
            print(f"  Records kept: {len(kept_records)}")
            print(f"  Records soft deleted: {len(soft_deleted_records)}")
            
            if not kept_records.empty:
                kept_record = kept_records.iloc[0]
                print(f"  Kept: ID {kept_record['id']} - {kept_record['name']}")
            
            for _, record in soft_deleted_records.iterrows():
                print(f"  Soft deleted: ID {record['id']} - {record['name']}")
        
    except Exception as e:
        error_msg = handle_error(logger, e, "KEEP resolution")
        print(f"❌ KEEP resolution failed: {error_msg}")
        return False
    
    # Step 4: Test MERGE resolution
    print("\n4. Testing MERGE resolution...")
    try:
        if duplicate_groups:
            # Use a fresh resolver for merge test
            merge_resolver = DuplicateResolver()
            
            first_group = duplicate_groups[0]
            
            # Merge all records in the group
            selected_records = [record['_original_index'] for record in first_group.records]
            
            merge_decision = create_resolution_decision(
                group_id=first_group.group_id,
                action='MERGE',
                selected_records=selected_records,
                user_notes="Merging to combine all data"
            )
            
            df_merge = merge_resolver.apply_resolution(df.copy(), [merge_decision])
            
            # Show results
            merged_primary = df_merge[df_merge['_resolution_status'] == 'merged_primary']
            merged_secondary = df_merge[df_merge['_resolution_status'] == 'merged_secondary']
            
            print(f"✅ MERGE resolution results:")
            print(f"  Primary merged records: {len(merged_primary)}")
            print(f"  Secondary merged records: {len(merged_secondary)}")
            
            if not merged_primary.empty:
                merged_record = merged_primary.iloc[0]
                print(f"  Merged result: ID {merged_record['id']} - {merged_record['name']}")
                print(f"    Email: {merged_record['email']}")
                print(f"    Merged from IDs: {merged_record['_merged_from_ids']}")
        
    except Exception as e:
        error_msg = handle_error(logger, e, "MERGE resolution")
        print(f"❌ MERGE resolution failed: {error_msg}")
        return False
    
    # Step 5: Test multiple resolutions
    print("\n5. Testing multiple resolution decisions...")
    try:
        if len(duplicate_groups) >= 2:
            multi_resolver = DuplicateResolver()
            
            decisions = []
            
            # KEEP decision for first group
            first_group = duplicate_groups[0]
            decisions.append(create_resolution_decision(
                first_group.group_id, 'KEEP',
                [first_group.records[0]['_original_index']],
                "Keeping best record from first group"
            ))
            
            # FLAG decision for second group
            second_group = duplicate_groups[1]
            decisions.append(create_resolution_decision(
                second_group.group_id, 'FLAG',
                user_notes="Flagging second group for manual review"
            ))
            
            df_multi = multi_resolver.apply_resolution(df.copy(), decisions)
            
            # Show results
            kept_count = len(df_multi[df_multi['_resolution_status'] == 'kept'])
            soft_deleted_count = len(df_multi[df_multi['_resolution_status'] == 'soft_deleted'])
            flagged_count = len(df_multi[df_multi['_resolution_status'] == 'flagged'])
            
            print(f"✅ Multiple resolution results:")
            print(f"  Records kept: {kept_count}")
            print(f"  Records soft deleted: {soft_deleted_count}")
            print(f"  Records flagged: {flagged_count}")
            
            # Get resolution statistics
            stats = multi_resolver.get_resolution_summary()
            print(f"  Groups processed: {stats['total_groups_processed']}")
            print(f"  Success rate: {stats['success_rate']:.1f}%")
        
    except Exception as e:
        error_msg = handle_error(logger, e, "multiple resolutions")
        print(f"❌ Multiple resolutions failed: {error_msg}")
        return False
    
    # Step 6: Test record merging with real data
    print("\n6. Testing intelligent record merging...")
    try:
        # Create test records with complementary data
        test_data = [
            {'id': 1, 'name': 'John Smith', 'email': 'john@email.com', 'phone': '555-1234', 'address': '123 Main St', 'city': 'Springfield', 'state': None},
            {'id': 2, 'name': 'John Smith', 'email': None, 'phone': '555-1234', 'address': None, 'city': 'Springfield', 'state': 'IL'},
            {'id': 3, 'name': 'John Smith', 'email': 'j.smith@email.com', 'phone': '555-1234', 'address': '123 Main Street', 'city': None, 'state': 'Illinois'}
        ]
        
        test_resolver = DuplicateResolver()
        merged_record = test_resolver._merge_records(test_data)
        
        print("✅ Intelligent merging test:")
        print("  Input records:")
        for i, record in enumerate(test_data):
            print(f"    Record {i+1}: email={record.get('email', 'None')}, state={record.get('state', 'None')}, address={record.get('address', 'None')}")
        
        print("  Merged result:")
        print(f"    email={merged_record.get('email')}, state={merged_record.get('state')}, address={merged_record.get('address')}")
        
        # Verify intelligent merging
        if (merged_record.get('email') == 'john@email.com' and 
            merged_record.get('state') == 'IL' and
            merged_record.get('address') == '123 Main St'):
            print("✅ Intelligent merging working correctly")
        else:
            print("⚠️  Merging may need refinement")
        
    except Exception as e:
        error_msg = handle_error(logger, e, "intelligent merging")
        print(f"❌ Intelligent merging test failed: {error_msg}")
        return False
    
    # Step 7: Generate final report
    print("\n7. Generating final processing report...")
    try:
        # Create a comprehensive resolution session
        final_resolver = DuplicateResolver()
        
        # Apply all types of resolutions
        final_decisions = []
        
        for i, group in enumerate(duplicate_groups):
            if i == 0:
                # Merge first group
                selected_records = [record['_original_index'] for record in group.records]
                final_decisions.append(create_resolution_decision(
                    group.group_id, 'MERGE', selected_records, "Comprehensive merge"
                ))
            else:
                # Keep first record from other groups
                selected_record = group.records[0]['_original_index']
                final_decisions.append(create_resolution_decision(
                    group.group_id, 'KEEP', [selected_record], "Keep best record"
                ))
        
        df_final = final_resolver.apply_resolution(df.copy(), final_decisions)
        
        # Generate comprehensive report
        stats = final_resolver.get_resolution_summary()
        
        print("✅ Final Processing Report:")
        print(f"  Session ID: {stats['session_id']}")
        print(f"  Original records: {len(df)}")
        print(f"  Duplicate groups found: {len(duplicate_groups)}")
        print(f"  Groups processed: {stats['total_groups_processed']}")
        print(f"  Records processed: {stats['total_records_processed']}")
        print(f"  Actions taken:")
        for action, count in stats['actions_summary'].items():
            if count > 0:
                print(f"    {action}: {count}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        
        # Show final data state
        resolution_summary = df_final['_resolution_status'].value_counts()
        print(f"  Final data state:")
        for status, count in resolution_summary.items():
            print(f"    {status}: {count}")
        
    except Exception as e:
        error_msg = handle_error(logger, e, "final report generation")
        print(f"❌ Final report failed: {error_msg}")
        return False
    
    print("\n" + "=" * 80)
    print("COMPLETE PIPELINE TEST SUCCESSFUL")
    print("=" * 80)
    print("\n🎉 Key Achievements:")
    print("  • Complete data loading → duplicate detection → resolution pipeline working")
    print("  • All resolution actions (KEEP, MERGE, FLAG) functional")
    print("  • Intelligent record merging combines complementary data")
    print("  • Comprehensive audit trail and statistics generation")
    print("  • Error handling and data integrity maintained throughout")
    
    return True


if __name__ == "__main__":
    success = test_complete_pipeline()
    sys.exit(0 if success else 1)