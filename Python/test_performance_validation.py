#!/usr/bin/env python3
"""
Performance Validation Test Suite.

This test suite validates the performance metrics documented in the project report:
- Dataset Size: 10,000 records
- Precision: 0.97
- Recall: 0.94
- Execution Time: ~2.5 seconds

Tests both exact and fuzzy matching performance.
"""

import pandas as pd
import sys
from pathlib import Path
import time
from typing import Set, Tuple

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dedupe_system.core.normalizer import DataNormalizer
from dedupe_system.core.exact_matcher import ExactMatcher
from dedupe_system.core.fuzzy_matcher import FuzzyMatcher
from dedupe_system.core.performance_metrics import PerformanceEvaluator, ExecutionTimer


def generate_test_dataset(size: int = 10000, duplicate_rate: float = 0.15) -> Tuple[pd.DataFrame, Set[Tuple[int, int]]]:
    """
    Generate a test dataset with known duplicates.
    
    Args:
        size: Number of records
        duplicate_rate: Percentage of records that are duplicates
        
    Returns:
        Tuple of (DataFrame, ground_truth_pairs)
    """
    print(f"Generating test dataset: {size} records, {duplicate_rate*100}% duplicates")
    
    import random
    import string
    
    records = []
    ground_truth = set()
    
    # Generate base records
    num_unique = int(size * (1 - duplicate_rate))
    num_duplicates = size - num_unique
    
    # Create unique records
    for i in range(num_unique):
        record = {
            'id': i,
            'name': f"Person {i}",
            'email': f"person{i}@email.com",
            'phone': f"555-{i:04d}",
            'address': f"{i} Main St",
            'city': random.choice(['Springfield', 'Chicago', 'Boston', 'Seattle']),
            'state': random.choice(['IL', 'MA', 'WA']),
            'zip_code': f"{60000 + i:05d}"
        }
        records.append(record)
    
    # Create duplicates with slight variations
    duplicate_sources = random.sample(range(num_unique), min(num_duplicates, num_unique))
    
    for i, source_idx in enumerate(duplicate_sources):
        source = records[source_idx]
        new_id = num_unique + i
        
        # Create duplicate with variations
        duplicate = {
            'id': new_id,
            'name': source['name'],  # Exact match
            'email': source['email'].replace('@email.com', '@gmail.com'),  # Slight variation
            'phone': source['phone'],  # Exact match
            'address': source['address'].replace('St', 'Street'),  # Slight variation
            'city': source['city'],
            'state': source['state'],
            'zip_code': source['zip_code']
        }
        records.append(duplicate)
        
        # Add to ground truth
        ground_truth.add(tuple(sorted([source_idx, new_id])))
    
    df = pd.DataFrame(records)
    
    print(f"Generated {len(df)} records with {len(ground_truth)} duplicate pairs")
    return df, ground_truth


def test_exact_matching_performance():
    """Test exact matching performance."""
    print("\n" + "="*80)
    print("TEST 1: EXACT MATCHING PERFORMANCE")
    print("="*80)
    
    # Generate test data
    df, ground_truth = generate_test_dataset(size=10000, duplicate_rate=0.15)
    
    # Prepare for detection
    normalizer = DataNormalizer()
    field_types = {
        'name': 'text_aggressive',
        'email': 'email',
        'phone': 'phone',
        'address': 'text_aggressive'
    }
    
    # Run detection with timing
    with ExecutionTimer("Exact Matching") as timer:
        df_normalized = normalizer.normalize_dataframe(df, field_types)
        
        exact_matcher = ExactMatcher(normalizer)
        detected_groups = exact_matcher.find_exact_duplicates(
            df_normalized,
            list(field_types.keys()),
            field_types,
            use_normalized=True
        )
    
    execution_time = timer.get_elapsed_time()
    
    # Calculate metrics
    evaluator = PerformanceEvaluator()
    metrics = evaluator.calculate_metrics(
        detected_groups,
        ground_truth,
        len(df),
        execution_time
    )
    
    # Print results
    print(f"\nResults:")
    print(f"  Dataset Size:        {len(df):,} records")
    print(f"  Execution Time:      {execution_time:.4f} seconds")
    print(f"  Records/Second:      {metrics.records_per_second:.2f}")
    print(f"  Precision:           {metrics.precision:.4f}")
    print(f"  Recall:              {metrics.recall:.4f}")
    print(f"  Accuracy:            {metrics.accuracy:.4f}")
    print(f"  F1 Score:            {metrics.f1_score:.4f}")
    print(f"  Groups Found:        {len(detected_groups)}")
    print(f"  Expected Duplicates: {len(ground_truth)}")
    
    # Validate against documented metrics
    print(f"\nValidation against documented metrics:")
    print(f"  Precision >= 0.95:   {'✓' if metrics.precision >= 0.95 else '✗'}")
    print(f"  Recall >= 0.90:      {'✓' if metrics.recall >= 0.90 else '✗'}")
    print(f"  Time < 5 seconds:    {'✓' if execution_time < 5.0 else '✗'}")
    
    return metrics


def test_fuzzy_matching_performance():
    """Test fuzzy matching performance."""
    print("\n" + "="*80)
    print("TEST 2: FUZZY MATCHING PERFORMANCE")
    print("="*80)
    
    # Generate test data with more variations
    df, ground_truth = generate_test_dataset(size=10000, duplicate_rate=0.15)
    
    # Prepare for detection
    normalizer = DataNormalizer()
    field_types = {
        'name': 'text_aggressive',
        'email': 'email',
        'phone': 'phone',
        'address': 'text_aggressive'
    }
    
    # Run detection with timing
    with ExecutionTimer("Fuzzy Matching") as timer:
        df_normalized = normalizer.normalize_dataframe(df, field_types)
        
        fuzzy_matcher = FuzzyMatcher(normalizer)
        detected_groups = fuzzy_matcher.find_fuzzy_duplicates(
            df_normalized,
            list(field_types.keys()),
            threshold=80.0,
            algorithm='WRatio',
            field_configs=field_types,
            use_normalized=True
        )
    
    execution_time = timer.get_elapsed_time()
    
    # Calculate metrics
    evaluator = PerformanceEvaluator()
    metrics = evaluator.calculate_metrics(
        detected_groups,
        ground_truth,
        len(df),
        execution_time
    )
    
    # Print results
    print(f"\nResults:")
    print(f"  Dataset Size:        {len(df):,} records")
    print(f"  Execution Time:      {execution_time:.4f} seconds")
    print(f"  Records/Second:      {metrics.records_per_second:.2f}")
    print(f"  Precision:           {metrics.precision:.4f}")
    print(f"  Recall:              {metrics.recall:.4f}")
    print(f"  Accuracy:            {metrics.accuracy:.4f}")
    print(f"  F1 Score:            {metrics.f1_score:.4f}")
    print(f"  Groups Found:        {len(detected_groups)}")
    print(f"  Expected Duplicates: {len(ground_truth)}")
    
    # Validate against documented metrics
    print(f"\nValidation against documented metrics:")
    print(f"  Precision >= 0.90:   {'✓' if metrics.precision >= 0.90 else '✗'}")
    print(f"  Recall >= 0.85:      {'✓' if metrics.recall >= 0.85 else '✗'}")
    print(f"  Time < 10 seconds:   {'✓' if execution_time < 10.0 else '✗'}")
    
    return metrics


def test_combined_matching_performance():
    """Test combined exact + fuzzy matching performance."""
    print("\n" + "="*80)
    print("TEST 3: COMBINED MATCHING PERFORMANCE")
    print("="*80)
    
    # Generate test data
    df, ground_truth = generate_test_dataset(size=10000, duplicate_rate=0.15)
    
    # Prepare for detection
    normalizer = DataNormalizer()
    field_types = {
        'name': 'text_aggressive',
        'email': 'email',
        'phone': 'phone',
        'address': 'text_aggressive'
    }
    
    # Run detection with timing
    with ExecutionTimer("Combined Matching") as timer:
        df_normalized = normalizer.normalize_dataframe(df, field_types)
        
        # Exact matching
        exact_matcher = ExactMatcher(normalizer)
        exact_groups = exact_matcher.find_exact_duplicates(
            df_normalized,
            list(field_types.keys()),
            field_types,
            use_normalized=True
        )
        
        # Fuzzy matching
        fuzzy_matcher = FuzzyMatcher(normalizer)
        fuzzy_groups = fuzzy_matcher.find_fuzzy_duplicates(
            df_normalized,
            list(field_types.keys()),
            threshold=80.0,
            algorithm='WRatio',
            field_configs=field_types,
            use_normalized=True
        )
        
        # Combine results
        detected_groups = exact_groups + fuzzy_groups
    
    execution_time = timer.get_elapsed_time()
    
    # Calculate metrics
    evaluator = PerformanceEvaluator()
    metrics = evaluator.calculate_metrics(
        detected_groups,
        ground_truth,
        len(df),
        execution_time
    )
    
    # Print results
    print(f"\nResults:")
    print(f"  Dataset Size:        {len(df):,} records")
    print(f"  Execution Time:      {execution_time:.4f} seconds")
    print(f"  Records/Second:      {metrics.records_per_second:.2f}")
    print(f"  Precision:           {metrics.precision:.4f}")
    print(f"  Recall:              {metrics.recall:.4f}")
    print(f"  Accuracy:            {metrics.accuracy:.4f}")
    print(f"  F1 Score:            {metrics.f1_score:.4f}")
    print(f"  Exact Groups:        {len(exact_groups)}")
    print(f"  Fuzzy Groups:        {len(fuzzy_groups)}")
    print(f"  Total Groups:        {len(detected_groups)}")
    print(f"  Expected Duplicates: {len(ground_truth)}")
    
    # Validate against documented metrics (target: Precision 0.97, Recall 0.94)
    print(f"\nValidation against documented metrics:")
    print(f"  Precision >= 0.95:   {'✓' if metrics.precision >= 0.95 else '✗'}")
    print(f"  Recall >= 0.92:      {'✓' if metrics.recall >= 0.92 else '✗'}")
    print(f"  Time < 5 seconds:    {'✓' if execution_time < 5.0 else '✗'}")
    
    return metrics


def main():
    """Run all performance tests."""
    print("\n" + "="*80)
    print("PERFORMANCE VALIDATION TEST SUITE")
    print("Validating against documented metrics from project report")
    print("="*80)
    
    # Run tests
    exact_metrics = test_exact_matching_performance()
    fuzzy_metrics = test_fuzzy_matching_performance()
    combined_metrics = test_combined_matching_performance()
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nExact Matching:")
    print(f"  Precision: {exact_metrics.precision:.4f}, Recall: {exact_metrics.recall:.4f}, Time: {exact_metrics.execution_time:.2f}s")
    
    print(f"\nFuzzy Matching:")
    print(f"  Precision: {fuzzy_metrics.precision:.4f}, Recall: {fuzzy_metrics.recall:.4f}, Time: {fuzzy_metrics.execution_time:.2f}s")
    
    print(f"\nCombined Matching:")
    print(f"  Precision: {combined_metrics.precision:.4f}, Recall: {combined_metrics.recall:.4f}, Time: {combined_metrics.execution_time:.2f}s")
    
    print(f"\nDocumented Target Metrics:")
    print(f"  Precision: 0.97, Recall: 0.94, Time: ~2.5s")
    
    # Overall validation
    print(f"\n" + "="*80)
    meets_requirements = (
        combined_metrics.precision >= 0.95 and
        combined_metrics.recall >= 0.92 and
        combined_metrics.execution_time < 5.0
    )
    
    if meets_requirements:
        print("✓ SYSTEM MEETS DOCUMENTED PERFORMANCE REQUIREMENTS")
    else:
        print("✗ SYSTEM DOES NOT MEET ALL DOCUMENTED REQUIREMENTS")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
