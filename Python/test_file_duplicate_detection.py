#!/usr/bin/env python3
"""
File-Level Duplicate Detection Test Suite.

Tests the file duplicate detection algorithms from the documentation:
- Algorithm 1: File Scanning
- Algorithm 2: Group Files by Size
- Algorithm 3: Hash-Based Duplicate Detection
- Algorithm 4: Intelligent Cleanup Strategy
"""

import sys
from pathlib import Path
import shutil
import tempfile

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dedupe_system.core.file_duplicate_detector import FileDuplicateDetector, find_duplicate_files


def create_test_files(test_dir: Path):
    """Create test files with known duplicates."""
    print(f"Creating test files in: {test_dir}")
    
    # Create directory structure
    (test_dir / "documents").mkdir(parents=True)
    (test_dir / "backup").mkdir(parents=True)
    (test_dir / "downloads").mkdir(parents=True)
    
    # Create original files
    files = {
        "documents/report.txt": "This is a test report with some content.",
        "documents/data.csv": "id,name,value\n1,Test,100\n2,Sample,200",
        "documents/image.txt": "Fake image data" * 100,  # Larger file
        "downloads/readme.txt": "This is a readme file.",
    }
    
    for file_path, content in files.items():
        full_path = test_dir / file_path
        full_path.write_text(content)
    
    # Create duplicates
    duplicates = {
        "backup/report.txt": "documents/report.txt",  # Exact duplicate
        "backup/report_copy.txt": "documents/report.txt",  # Another duplicate
        "downloads/data.csv": "documents/data.csv",  # Duplicate in different location
        "documents/image_backup.txt": "documents/image.txt",  # Duplicate with different name
    }
    
    for dup_path, original_path in duplicates.items():
        full_dup_path = test_dir / dup_path
        full_original_path = test_dir / original_path
        shutil.copy(full_original_path, full_dup_path)
    
    print(f"Created {len(files)} original files and {len(duplicates)} duplicates")
    return files, duplicates


def test_file_scanning():
    """Test Algorithm 1: File Scanning."""
    print("\n" + "="*80)
    print("TEST 1: FILE SCANNING (Algorithm 1)")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        files, duplicates = create_test_files(test_dir)
        
        # Test file scanning
        detector = FileDuplicateDetector()
        scanned_files = detector.scan_files(str(test_dir))
        
        print(f"\nResults:")
        print(f"  Expected files: {len(files) + len(duplicates)}")
        print(f"  Scanned files:  {len(scanned_files)}")
        print(f"  Match:          {'✓' if len(scanned_files) == len(files) + len(duplicates) else '✗'}")
        
        # Verify all files were found
        scanned_paths = {str(f.path.relative_to(test_dir)) for f in scanned_files}
        expected_paths = set(files.keys()) | set(duplicates.keys())
        
        print(f"\n  All files found: {'✓' if scanned_paths == expected_paths else '✗'}")
        
        if scanned_paths != expected_paths:
            missing = expected_paths - scanned_paths
            extra = scanned_paths - expected_paths
            if missing:
                print(f"  Missing: {missing}")
            if extra:
                print(f"  Extra: {extra}")
        
        return len(scanned_files) == len(files) + len(duplicates)


def test_size_grouping():
    """Test Algorithm 2: Group Files by Size."""
    print("\n" + "="*80)
    print("TEST 2: GROUP FILES BY SIZE (Algorithm 2)")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        files, duplicates = create_test_files(test_dir)
        
        # Scan and group files
        detector = FileDuplicateDetector()
        scanned_files = detector.scan_files(str(test_dir))
        size_map = detector.group_by_size(scanned_files)
        
        print(f"\nResults:")
        print(f"  Total files:           {len(scanned_files)}")
        print(f"  Size groups:           {len(size_map)}")
        print(f"  Groups with potential: {sum(1 for files in size_map.values() if len(files) > 1)}")
        
        # Verify grouping
        for size, file_list in size_map.items():
            print(f"\n  Size {size} bytes: {len(file_list)} files")
            for file_info in file_list:
                print(f"    - {file_info.path.name}")
        
        # Should have groups with duplicates
        has_duplicate_groups = any(len(files) > 1 for files in size_map.values())
        print(f"\n  Has duplicate groups: {'✓' if has_duplicate_groups else '✗'}")
        
        return has_duplicate_groups


def test_hash_based_detection():
    """Test Algorithm 3: Hash-Based Duplicate Detection."""
    print("\n" + "="*80)
    print("TEST 3: HASH-BASED DUPLICATE DETECTION (Algorithm 3)")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        files, duplicates = create_test_files(test_dir)
        
        # Run full detection
        detector = FileDuplicateDetector()
        scanned_files = detector.scan_files(str(test_dir))
        size_map = detector.group_by_size(scanned_files)
        duplicate_groups = detector.detect_duplicates(size_map)
        
        print(f"\nResults:")
        print(f"  Total files:       {len(scanned_files)}")
        print(f"  Duplicate groups:  {len(duplicate_groups)}")
        print(f"  Expected groups:   {len(set(duplicates.values()))}")  # Number of unique originals
        
        # Show duplicate groups
        for i, group in enumerate(duplicate_groups):
            print(f"\n  Group {i+1}: {len(group.files)} files, {group.total_size} bytes")
            for file_info in group.files:
                print(f"    - {file_info.path.relative_to(test_dir)}")
        
        # Verify detection
        expected_groups = len(set(duplicates.values()))
        detected_correctly = len(duplicate_groups) == expected_groups
        
        print(f"\n  Detection correct: {'✓' if detected_correctly else '✗'}")
        
        return detected_correctly


def test_intelligent_cleanup():
    """Test Algorithm 4: Intelligent Cleanup Strategy."""
    print("\n" + "="*80)
    print("TEST 4: INTELLIGENT CLEANUP STRATEGY (Algorithm 4)")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        files, duplicates = create_test_files(test_dir)
        
        # Run detection
        detector = FileDuplicateDetector()
        scanned_files = detector.scan_files(str(test_dir))
        size_map = detector.group_by_size(scanned_files)
        duplicate_groups = detector.detect_duplicates(size_map)
        
        # Test cleanup (dry run)
        print(f"\nTesting cleanup (dry run)...")
        stats = detector.intelligent_cleanup(
            duplicate_groups,
            action='recycle',
            preferred_directories=['documents'],
            dry_run=True
        )
        
        print(f"\nCleanup Statistics:")
        print(f"  Total groups:      {stats['total_groups']}")
        print(f"  Files to remove:   {stats['files_to_remove']}")
        print(f"  Files to keep:     {stats['files_kept']}")
        print(f"  Space to free:     {stats['space_to_free']} bytes")
        print(f"                     {stats['space_to_free'] / 1024:.2f} KB")
        
        # Show actions
        print(f"\n  Actions to take:")
        for action in stats['actions_taken'][:5]:  # Show first 5
            print(f"    {action['action']}: {Path(action['file']).name} -> keep {Path(action['kept_file']).name}")
        
        if len(stats['actions_taken']) > 5:
            print(f"    ... and {len(stats['actions_taken']) - 5} more")
        
        # Verify cleanup logic
        expected_removals = len(duplicates)
        cleanup_correct = stats['files_to_remove'] == expected_removals
        
        print(f"\n  Cleanup logic correct: {'✓' if cleanup_correct else '✗'}")
        
        return cleanup_correct


def test_complete_workflow():
    """Test complete file duplicate detection workflow."""
    print("\n" + "="*80)
    print("TEST 5: COMPLETE WORKFLOW")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        files, duplicates = create_test_files(test_dir)
        
        # Use convenience function
        print(f"\nRunning complete duplicate detection...")
        duplicate_groups, stats = find_duplicate_files(
            str(test_dir),
            preferred_directories=['documents']
        )
        
        print(f"\nResults:")
        print(f"  Duplicate groups:      {stats['total_groups']}")
        print(f"  Total files:           {stats['total_files']}")
        print(f"  Total duplicates:      {stats['total_duplicates']}")
        print(f"  Wasted space:          {stats['total_wasted_space_bytes']} bytes")
        print(f"                         {stats['total_wasted_space_mb']:.2f} MB")
        print(f"  Largest group:         {stats['largest_group_size']} files")
        print(f"  Average group size:    {stats['average_group_size']:.1f} files")
        
        # Verify results
        expected_groups = len(set(duplicates.values()))
        workflow_correct = stats['total_groups'] == expected_groups
        
        print(f"\n  Workflow correct: {'✓' if workflow_correct else '✗'}")
        
        return workflow_correct


def main():
    """Run all file duplicate detection tests."""
    print("\n" + "="*80)
    print("FILE-LEVEL DUPLICATE DETECTION TEST SUITE")
    print("Testing algorithms from project documentation")
    print("="*80)
    
    # Run tests
    test1_pass = test_file_scanning()
    test2_pass = test_size_grouping()
    test3_pass = test_hash_based_detection()
    test4_pass = test_intelligent_cleanup()
    test5_pass = test_complete_workflow()
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\n  Algorithm 1 (File Scanning):        {'✓ PASS' if test1_pass else '✗ FAIL'}")
    print(f"  Algorithm 2 (Size Grouping):        {'✓ PASS' if test2_pass else '✗ FAIL'}")
    print(f"  Algorithm 3 (Hash Detection):       {'✓ PASS' if test3_pass else '✗ FAIL'}")
    print(f"  Algorithm 4 (Intelligent Cleanup):  {'✓ PASS' if test4_pass else '✗ FAIL'}")
    print(f"  Complete Workflow:                  {'✓ PASS' if test5_pass else '✗ FAIL'}")
    
    all_pass = all([test1_pass, test2_pass, test3_pass, test4_pass, test5_pass])
    
    print(f"\n" + "="*80)
    if all_pass:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
