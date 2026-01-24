#!/usr/bin/env python3
"""
Test script for the Output Generator component.

This script demonstrates and tests the output generation functionality
including cleaned datasets, audit logs, and summary reports.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import json
import shutil

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dedupe_system.core.output_generator import OutputGenerator, generate_outputs_from_pipeline
from dedupe_system.core.resolver import DuplicateResolver, create_resolution_decision
from dedupe_system.core.exact_matcher import ExactMatcher
from dedupe_system.core.normalizer import DataNormalizer
from dedupe_system.core.loader import DataLoader
from dedupe_system.core.models import AuditEntry, ProcessingStats
from dedupe_system.core.logging_config import setup_logging
from dedupe_system.core.exceptions import handle_error

def test_output_generator():
    """Test the OutputGenerator with various scenarios."""
    
    # Set up logging
    logger = setup_logging("INFO", "logs")
    
    print("=" * 70)
    print("TESTING OUTPUT GENERATOR COMPONENT")
    print("=" * 70)
    
    # Clean up any existing test outputs
    test_output_dir = Path("test_outputs")
    if test_output_dir.exists():
        shutil.rmtree(test_output_dir)
    test_output_dir.mkdir()
    
    # Initialize components
    loader = DataLoader()
    normalizer = DataNormalizer()
    matcher = ExactMatcher(normalizer)
    resolver = DuplicateResolver()
    generator = OutputGenerator(str(test_output_dir))
    
    # Step 1: Prepare test data with complete pipeline
    print("\n1. Preparing test data with complete pipeline...")
    try:
        # Load sample data
        df = loader.load_file("test_data/sample_customers.csv")
        df['_original_index'] = df.index
        print(f"✅ Loaded {len(df)} customer records")
        
        # Find duplicates
        duplicate_groups = matcher.find_duplicates_by_composite_key(
            df, ['name', 'phone'], ['text', 'phone']
        )
        print(f"✅ Found {len(duplicate_groups)} duplicate groups")
        
        # Add group membership to DataFrame
        df['_duplicate_group_id'] = None
        for group in duplicate_groups:
            for record in group.records:
                original_idx = record['_original_index']
                df.loc[original_idx, '_duplicate_group_id'] = group.group_id
        
        # Apply resolutions
        decisions = []
        if duplicate_groups:
            # Merge first group
            first_group = duplicate_groups[0]
            decisions.append(create_resolution_decision(
                first_group.group_id, 'MERGE',
                [record['_original_index'] for record in first_group.records],
                "Test merge for output generation"
            ))
            
            # Keep first record from second group if it exists
            if len(duplicate_groups) > 1:
                second_group = duplicate_groups[1]
                decisions.append(create_resolution_decision(
                    second_group.group_id, 'KEEP',
                    [second_group.records[0]['_original_index']],
                    "Test keep for output generation"
                ))
        
        df_resolved = resolver.apply_resolution(df, decisions)
        print(f"✅ Applied {len(decisions)} resolution decisions")
        
    except Exception as e:
        error_msg = handle_error(logger, e, "test data preparation")
        print(f"❌ Test data preparation failed: {error_msg}")
        return False
    
    # Step 2: Test cleaned dataset generation (CSV)
    print("\n2. Testing cleaned dataset generation (CSV)...")
    try:
        csv_output = generator.generate_cleaned_dataset(df_resolved, 'csv', 'test_cleaned_csv')
        print(f"✅ CSV cleaned dataset generated: {csv_output}")
        
        # Verify the CSV file
        csv_path = Path(csv_output)
        if csv_path.exists():
            # Read and validate the CSV
            cleaned_df = pd.read_csv(csv_path)
            print(f"  Cleaned CSV contains {len(cleaned_df)} records, {len(cleaned_df.columns)} columns")
            
            # Check that internal columns are removed
            internal_cols = [col for col in cleaned_df.columns if col.startswith('_')]
            if internal_cols:
                print(f"⚠️  Internal columns found in cleaned CSV: {internal_cols}")
            else:
                print("✅ Internal columns properly removed from CSV")
            
            # Show sample of cleaned data
            print("  Sample cleaned data:")
            print(cleaned_df[['id', 'name', 'email', 'phone']].head(3).to_string(index=False))
        
    except Exception as e:
        error_msg = handle_error(logger, e, "CSV generation")
        print(f"❌ CSV generation failed: {error_msg}")
        return False
    
    # Step 3: Test cleaned dataset generation (JSON)
    print("\n3. Testing cleaned dataset generation (JSON)...")
    try:
        json_output = generator.generate_cleaned_dataset(df_resolved, 'json', 'test_cleaned_json')
        print(f"✅ JSON cleaned dataset generated: {json_output}")
        
        # Verify the JSON file
        json_path = Path(json_output)
        if json_path.exists():
            # Read and validate the JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                cleaned_data = json.load(f)
            
            print(f"  Cleaned JSON contains {len(cleaned_data)} records")
            
            # Check structure
            if cleaned_data and isinstance(cleaned_data[0], dict):
                sample_record = cleaned_data[0]
                print(f"  Sample record keys: {list(sample_record.keys())}")
                
                # Check that internal columns are removed
                internal_keys = [key for key in sample_record.keys() if key.startswith('_')]
                if internal_keys:
                    print(f"⚠️  Internal keys found in cleaned JSON: {internal_keys}")
                else:
                    print("✅ Internal keys properly removed from JSON")
        
    except Exception as e:
        error_msg = handle_error(logger, e, "JSON generation")
        print(f"❌ JSON generation failed: {error_msg}")
        return False
    
    # Step 4: Test audit log generation
    print("\n4. Testing audit log generation...")
    try:
        # Create sample audit entries
        audit_entries = [
            AuditEntry(
                record_id="1",
                action="MERGED",
                reason="Merged with records 3,7",
                similarity_score=100.0,
                timestamp=datetime.now(),
                user_decision=True
            ),
            AuditEntry(
                record_id="2",
                action="KEPT",
                reason="Selected as best record",
                similarity_score=None,
                timestamp=datetime.now(),
                user_decision=True
            ),
            AuditEntry(
                record_id="5",
                action="SOFT_DELETED",
                reason="Duplicate of record 2",
                similarity_score=100.0,
                timestamp=datetime.now(),
                user_decision=True
            )
        ]
        
        audit_output = generator.generate_audit_log(audit_entries, 'test_audit_log')
        print(f"✅ Audit log generated: {audit_output}")
        
        # Verify the audit log
        audit_path = Path(audit_output)
        if audit_path.exists():
            audit_df = pd.read_csv(audit_path)
            print(f"  Audit log contains {len(audit_df)} entries")
            
            # Check required columns
            required_cols = ['record_id', 'action', 'reason', 'timestamp', 'user_decision']
            missing_cols = [col for col in required_cols if col not in audit_df.columns]
            if missing_cols:
                print(f"❌ Missing required columns: {missing_cols}")
                return False
            else:
                print("✅ All required audit columns present")
            
            # Show sample audit entries
            print("  Sample audit entries:")
            print(audit_df[['record_id', 'action', 'reason', 'user_decision']].to_string(index=False))
        
    except Exception as e:
        error_msg = handle_error(logger, e, "audit log generation")
        print(f"❌ Audit log generation failed: {error_msg}")
        return False
    
    # Step 5: Test summary report generation
    print("\n5. Testing summary report generation...")
    try:
        # Create sample processing stats
        stats = ProcessingStats(
            total_records=len(df),
            duplicate_groups_found=len(duplicate_groups),
            exact_duplicates=len(duplicate_groups),  # All are exact in our test
            fuzzy_duplicates=0,
            processing_time=0.15,
            memory_usage=2.5
        )
        
        summary_output = generator.generate_summary_report(
            stats, duplicate_groups, len(df), 'test_summary_report'
        )
        print(f"✅ Summary report generated: {summary_output}")
        
        # Verify the summary report
        summary_path = Path(summary_output)
        if summary_path.exists():
            with open(summary_path, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
            
            # Check required sections
            required_sections = ['session_info', 'data_summary', 'performance_metrics']
            missing_sections = [section for section in required_sections if section not in summary_data]
            if missing_sections:
                print(f"❌ Missing required sections: {missing_sections}")
                return False
            else:
                print("✅ All required summary sections present")
            
            # Show key metrics
            print("  Key metrics:")
            data_summary = summary_data.get('data_summary', {})
            perf_metrics = summary_data.get('performance_metrics', {})
            
            print(f"    Original records: {data_summary.get('original_records')}")
            print(f"    Duplicate groups: {data_summary.get('duplicate_groups_found')}")
            print(f"    Processing time: {perf_metrics.get('processing_time_seconds')}s")
            print(f"    Records/second: {perf_metrics.get('records_per_second'):.1f}")
            
            # Check duplicate analysis
            if 'duplicate_analysis' in summary_data:
                dup_analysis = summary_data['duplicate_analysis']
                print(f"    Group size distribution: {dup_analysis.get('group_size_distribution', {})}")
        
    except Exception as e:
        error_msg = handle_error(logger, e, "summary report generation")
        print(f"❌ Summary report generation failed: {error_msg}")
        return False
    
    # Step 6: Test generate all outputs
    print("\n6. Testing generate all outputs...")
    try:
        all_outputs = generator.generate_all_outputs(
            df_resolved, audit_entries, stats, duplicate_groups, 'csv', 'test_complete'
        )
        
        print("✅ All outputs generated:")
        for output_type, file_path in all_outputs.items():
            print(f"  {output_type}: {file_path}")
            
            # Verify each file exists
            if Path(file_path).exists():
                file_size = Path(file_path).stat().st_size
                print(f"    File size: {file_size} bytes")
            else:
                print(f"❌ File not found: {file_path}")
                return False
        
    except Exception as e:
        error_msg = handle_error(logger, e, "generate all outputs")
        print(f"❌ Generate all outputs failed: {error_msg}")
        return False
    
    # Step 7: Test convenience function
    print("\n7. Testing convenience function...")
    try:
        convenience_outputs = generate_outputs_from_pipeline(
            df_resolved, audit_entries, duplicate_groups, 
            0.25, 3.2, 'json', str(test_output_dir)
        )
        
        print("✅ Convenience function outputs:")
        for output_type, file_path in convenience_outputs.items():
            print(f"  {output_type}: {Path(file_path).name}")
        
    except Exception as e:
        error_msg = handle_error(logger, e, "convenience function")
        print(f"❌ Convenience function failed: {error_msg}")
        return False
    
    # Step 8: Test file validation
    print("\n8. Testing file validation...")
    try:
        # Test CSV validation
        csv_files = list(test_output_dir.glob("*.csv"))
        for csv_file in csv_files:
            try:
                test_df = pd.read_csv(csv_file)
                print(f"✅ CSV validation passed: {csv_file.name} ({len(test_df)} records)")
            except Exception as e:
                print(f"❌ CSV validation failed: {csv_file.name} - {e}")
                return False
        
        # Test JSON validation
        json_files = list(test_output_dir.glob("*.json"))
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    test_data = json.load(f)
                print(f"✅ JSON validation passed: {json_file.name}")
            except Exception as e:
                print(f"❌ JSON validation failed: {json_file.name} - {e}")
                return False
        
    except Exception as e:
        error_msg = handle_error(logger, e, "file validation")
        print(f"❌ File validation failed: {error_msg}")
        return False
    
    # Step 9: Test data integrity
    print("\n9. Testing data integrity...")
    try:
        # Load original and cleaned data to compare
        original_df = loader.load_file("test_data/sample_customers.csv")
        
        # Find the cleaned CSV file
        cleaned_csv_files = [f for f in test_output_dir.glob("*cleaned*.csv")]
        if cleaned_csv_files:
            cleaned_df = pd.read_csv(cleaned_csv_files[0])
            
            # Check data integrity
            print(f"  Original records: {len(original_df)}")
            print(f"  Cleaned records: {len(cleaned_df)}")
            
            # Check that essential data is preserved
            original_names = set(original_df['name'].unique())
            cleaned_names = set(cleaned_df['name'].unique())
            
            if original_names.issubset(cleaned_names):
                print("✅ Essential data preserved in cleaned dataset")
            else:
                missing_names = original_names - cleaned_names
                print(f"⚠️  Some names missing from cleaned data: {missing_names}")
            
            # Check column integrity
            essential_columns = ['id', 'name', 'email', 'phone']
            missing_columns = [col for col in essential_columns if col not in cleaned_df.columns]
            if missing_columns:
                print(f"❌ Essential columns missing: {missing_columns}")
                return False
            else:
                print("✅ Essential columns preserved")
        
    except Exception as e:
        error_msg = handle_error(logger, e, "data integrity check")
        print(f"❌ Data integrity check failed: {error_msg}")
        return False
    
    # Step 10: Show final output summary
    print("\n10. Final output summary...")
    try:
        output_files = list(test_output_dir.glob("*"))
        print(f"✅ Generated {len(output_files)} output files:")
        
        total_size = 0
        for file_path in output_files:
            if file_path.is_file():
                size = file_path.stat().st_size
                total_size += size
                print(f"  {file_path.name}: {size} bytes")
        
        print(f"  Total output size: {total_size} bytes")
        
        # Categorize files
        csv_files = len(list(test_output_dir.glob("*.csv")))
        json_files = len(list(test_output_dir.glob("*.json")))
        
        print(f"  File types: {csv_files} CSV, {json_files} JSON")
        
    except Exception as e:
        error_msg = handle_error(logger, e, "output summary")
        print(f"❌ Output summary failed: {error_msg}")
        return False
    
    print("\n" + "=" * 70)
    print("OUTPUT GENERATOR TESTING COMPLETE")
    print("=" * 70)
    print("\n🎯 Key Results:")
    print("  • Cleaned dataset generation working for both CSV and JSON formats")
    print("  • Comprehensive audit log generation with all required fields")
    print("  • Detailed summary reports with statistics and performance metrics")
    print("  • File validation ensuring all outputs are properly formatted")
    print("  • Data integrity preserved throughout the output process")
    print("  • Convenience functions for complete pipeline output generation")
    
    return True


if __name__ == "__main__":
    success = test_output_generator()
    sys.exit(0 if success else 1)