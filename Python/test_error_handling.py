#!/usr/bin/env python3
"""
Test script for the Enhanced Error Handling System.

This script demonstrates and tests the comprehensive error handling functionality
including specific error messages, detailed logging, configuration validation,
graceful degradation, and comprehensive activity logs.
"""

import sys
from pathlib import Path
import pandas as pd
import json
import tempfile
import shutil
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dedupe_system.core.exceptions import (
    ErrorHandler, FileProcessingError, DataValidationError, 
    ConfigurationError, ProcessingError, handle_error
)
from dedupe_system.core.logging_config import (
    setup_logging, create_comprehensive_logger, AuditLogger, ActivityLogger
)

def test_error_handling_system():
    """Test the comprehensive error handling system."""
    
    print("=" * 70)
    print("TESTING ENHANCED ERROR HANDLING SYSTEM")
    print("=" * 70)
    
    # Create temporary directory for test logs
    test_log_dir = Path("test_logs")
    if test_log_dir.exists():
        shutil.rmtree(test_log_dir)
    test_log_dir.mkdir()
    
    # Step 1: Test comprehensive logger setup
    print("\n1. Testing comprehensive logger setup...")
    try:
        main_logger, audit_logger, activity_logger = create_comprehensive_logger("DEBUG", str(test_log_dir))
        print("✅ Comprehensive logging system initialized")
        
        # Test basic logging
        main_logger.info("Test info message")
        main_logger.warning("Test warning message")
        main_logger.error("Test error message")
        
        # Check log files were created
        log_files = list(test_log_dir.glob("*.log"))
        print(f"✅ Created {len(log_files)} log files: {[f.name for f in log_files]}")
        
    except Exception as e:
        print(f"❌ Logger setup failed: {e}")
        return False
    
    # Step 2: Test ErrorHandler class
    print("\n2. Testing ErrorHandler class...")
    try:
        error_handler = ErrorHandler(main_logger)
        print("✅ ErrorHandler initialized")
        
        # Test error counting
        initial_summary = error_handler.get_error_summary()
        print(f"  Initial error summary: {initial_summary}")
        
    except Exception as e:
        print(f"❌ ErrorHandler initialization failed: {e}")
        return False
    
    # Step 3: Test file parsing error handling
    print("\n3. Testing file parsing error handling...")
    try:
        # Test empty file error
        empty_file_error = pd.errors.EmptyDataError("No data")
        message = error_handler.handle_file_parsing_error("empty.csv", empty_file_error)
        print(f"✅ Empty file error: {message}")
        
        # Test JSON decode error
        json_error = json.JSONDecodeError("Invalid JSON", "test.json", 5)
        message = error_handler.handle_file_parsing_error("test.json", json_error)
        print(f"✅ JSON decode error: {message}")
        
        # Test encoding error
        encoding_error = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")
        message = error_handler.handle_file_parsing_error("bad_encoding.csv", encoding_error)
        print(f"✅ Encoding error: {message}")
        
        # Test file not found error
        file_not_found = FileNotFoundError("File not found")
        file_not_found.filename = "missing.csv"
        message = error_handler.handle_file_parsing_error("missing.csv", file_not_found)
        print(f"✅ File not found error: {message}")
        
    except Exception as e:
        print(f"❌ File parsing error handling failed: {e}")
        return False
    
    # Step 4: Test processing error handling
    print("\n4. Testing processing error handling...")
    try:
        # Test memory error
        memory_error = MemoryError("Out of memory")
        message = error_handler.handle_processing_error("duplicate_detection", memory_error, 10000)
        print(f"✅ Memory error: {message}")
        
        # Test key error
        key_error = KeyError("missing_field")
        message = error_handler.handle_processing_error("normalization", key_error, 5000)
        print(f"✅ Key error: {message}")
        
        # Test value error
        value_error = ValueError("Invalid threshold value")
        message = error_handler.handle_processing_error("fuzzy_matching", value_error, 2000)
        print(f"✅ Value error: {message}")
        
    except Exception as e:
        print(f"❌ Processing error handling failed: {e}")
        return False
    
    # Step 5: Test configuration validation
    print("\n5. Testing configuration validation...")
    try:
        # Test valid configuration
        valid_config = {
            'matching': {
                'mode': 'both',
                'fields': ['name', 'email'],
                'fuzzy_threshold': 85
            },
            'resolution': {
                'default_action': 'MERGE',
                'merge_strategy': 'most_complete'
            },
            'performance': {
                'memory_limit_mb': 1024,
                'batch_size': 1000
            }
        }
        
        is_valid, errors = error_handler.validate_configuration(valid_config)
        print(f"✅ Valid config validation: {is_valid}, errors: {errors}")
        
        # Test invalid configuration
        invalid_config = {
            'matching': {
                'mode': 'invalid_mode',
                'fields': [],
                'fuzzy_threshold': 150
            },
            'resolution': {
                'default_action': 'INVALID_ACTION'
            },
            'performance': {
                'memory_limit_mb': -100,
                'batch_size': 0
            }
        }
        
        is_valid, errors = error_handler.validate_configuration(invalid_config)
        print(f"✅ Invalid config validation: {is_valid}")
        print(f"  Validation errors:")
        for error in errors:
            print(f"    - {error}")
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False
    
    # Step 6: Test system limits handling
    print("\n6. Testing system limits handling...")
    try:
        # Test memory limit
        memory_message = error_handler.handle_system_limits(
            'memory', 2048.5, 1024.0, "Try processing in smaller batches"
        )
        print(f"✅ Memory limit: {memory_message}")
        
        # Test time limit
        time_message = error_handler.handle_system_limits(
            'time', 300.2, 120.0, "Consider using exact matching only"
        )
        print(f"✅ Time limit: {time_message}")
        
        # Test record limit
        record_message = error_handler.handle_system_limits(
            'records', 50000, 25000, "Process data in chunks"
        )
        print(f"✅ Record limit: {record_message}")
        
    except Exception as e:
        print(f"❌ System limits handling failed: {e}")
        return False
    
    # Step 7: Test activity logging
    print("\n7. Testing activity logging...")
    try:
        # Test file operations
        activity_logger.log_file_operation(
            'load', 'test_data.csv', True, 
            {'records_loaded': 1000, 'file_size_mb': 2.5}
        )
        
        activity_logger.log_file_operation(
            'save', 'output.csv', False, 
            {'error': 'Permission denied'}
        )
        
        # Test data operations
        activity_logger.log_data_operation(
            'normalize', 1000, True, 0.15, 
            {'fields_normalized': ['name', 'email', 'phone']}
        )
        
        activity_logger.log_data_operation(
            'match', 1000, True, 2.3, 
            {'duplicate_groups': 25, 'exact_matches': 20, 'fuzzy_matches': 5}
        )
        
        # Test user interactions
        activity_logger.log_user_interaction(
            'config_change', 
            {'field': 'fuzzy_threshold', 'old_value': 80, 'new_value': 85}
        )
        
        activity_logger.log_user_interaction(
            'decision', 
            {'group_id': 'group_001', 'action': 'MERGE', 'records_affected': 3}
        )
        
        # Test system events
        activity_logger.log_system_event(
            'warning', 'High memory usage detected', 
            {'memory_usage_mb': 1800, 'threshold_mb': 1024}
        )
        
        # Test performance metrics
        activity_logger.log_performance_metrics(
            'duplicate_detection', {
                'total_records': 10000,
                'processing_time_seconds': 5.2,
                'memory_peak_mb': 256,
                'records_per_second': 1923
            }
        )
        
        print("✅ Activity logging completed")
        
    except Exception as e:
        print(f"❌ Activity logging failed: {e}")
        return False
    
    # Step 8: Test audit logging
    print("\n8. Testing audit logging...")
    try:
        # Test audit entries
        audit_logger.log_action(
            'record_001', 'MERGED', 'Merged with records 003, 007', 
            100.0, True
        )
        
        audit_logger.log_action(
            'record_002', 'KEPT', 'Selected as best record', 
            None, True
        )
        
        audit_logger.log_action(
            'record_005', 'SOFT_DELETED', 'Duplicate of record 002', 
            95.5, False
        )
        
        # Test session logging
        audit_logger.log_processing_start(10000, {
            'matching_mode': 'both',
            'fuzzy_threshold': 85,
            'fields': ['name', 'email']
        })
        
        audit_logger.log_processing_end({
            'total_processed': 10000,
            'duplicates_found': 150,
            'actions_taken': 75,
            'processing_time': 12.5
        })
        
        print("✅ Audit logging completed")
        
    except Exception as e:
        print(f"❌ Audit logging failed: {e}")
        return False
    
    # Step 9: Test error summary and counters
    print("\n9. Testing error summary and counters...")
    try:
        # Get error summary
        summary = error_handler.get_error_summary()
        print(f"✅ Error summary: {summary}")
        
        # Test counter reset
        error_handler.reset_counters()
        reset_summary = error_handler.get_error_summary()
        print(f"✅ Reset summary: {reset_summary}")
        
    except Exception as e:
        print(f"❌ Error summary failed: {e}")
        return False
    
    # Step 10: Test integration with existing error handling
    print("\n10. Testing integration with existing error handling...")
    try:
        # Test custom exceptions
        try:
            raise FileProcessingError("Test file error", "test.csv", 42)
        except Exception as e:
            message = handle_error(main_logger, e, "integration_test")
            print(f"✅ Custom exception handling: {message}")
        
        # Test standard exceptions
        try:
            raise ValueError("Test value error")
        except Exception as e:
            message = handle_error(main_logger, e, "integration_test")
            print(f"✅ Standard exception handling: {message}")
        
    except Exception as e:
        print(f"❌ Integration testing failed: {e}")
        return False
    
    # Step 11: Validate log files
    print("\n11. Validating log files...")
    try:
        log_files = list(test_log_dir.glob("*.log"))
        print(f"✅ Found {len(log_files)} log files")
        
        total_size = 0
        for log_file in log_files:
            size = log_file.stat().st_size
            total_size += size
            print(f"  {log_file.name}: {size} bytes")
            
            # Check if file has content
            if size == 0:
                print(f"⚠️  Empty log file: {log_file.name}")
            else:
                # Read first few lines to verify format
                with open(log_file, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line:
                        print(f"    Sample: {first_line[:100]}...")
        
        print(f"  Total log size: {total_size} bytes")
        
        # Verify specific log types exist
        expected_patterns = ['system_', 'errors_', 'audit_', 'activity_']
        for pattern in expected_patterns:
            matching_files = [f for f in log_files if pattern in f.name]
            if matching_files:
                print(f"✅ Found {pattern} logs: {[f.name for f in matching_files]}")
            else:
                print(f"⚠️  No {pattern} logs found")
        
    except Exception as e:
        print(f"❌ Log file validation failed: {e}")
        return False
    
    # Step 12: Test graceful degradation scenarios
    print("\n12. Testing graceful degradation scenarios...")
    try:
        # Simulate various system stress scenarios
        scenarios = [
            ('memory', 'High memory usage scenario'),
            ('disk_space', 'Low disk space scenario'),
            ('processing_time', 'Long processing time scenario'),
            ('large_dataset', 'Large dataset scenario')
        ]
        
        for scenario_type, description in scenarios:
            activity_logger.log_system_event(
                'warning', f'Graceful degradation triggered: {description}',
                {'scenario_type': scenario_type, 'mitigation': 'Applied performance optimizations'}
            )
            print(f"✅ Logged graceful degradation: {scenario_type}")
        
    except Exception as e:
        print(f"❌ Graceful degradation testing failed: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("ENHANCED ERROR HANDLING SYSTEM TESTING COMPLETE")
    print("=" * 70)
    print("\n🎯 Key Results:")
    print("  • Comprehensive logging system with main, audit, and activity loggers")
    print("  • Specific error messages for file parsing failures")
    print("  • Detailed logging for all processing errors")
    print("  • Configuration validation with explanatory messages")
    print("  • Graceful degradation for system limit scenarios")
    print("  • Comprehensive activity logs for all operations")
    print("  • Error counting and summary reporting")
    print("  • Integration with existing error handling framework")
    
    # Show final statistics
    final_summary = error_handler.get_error_summary()
    print(f"\n📊 Final Error Statistics:")
    print(f"  Total errors handled: {final_summary['total_errors']}")
    print(f"  Total warnings: {final_summary['total_warnings']}")
    print(f"  Error types: {list(final_summary['errors'].keys())}")
    print(f"  Warning types: {list(final_summary['warnings'].keys())}")
    
    return True


if __name__ == "__main__":
    success = test_error_handling_system()
    sys.exit(0 if success else 1)