# MIT License
# Copyright (c) 2026 Judy Natasha Wambui Gachanja

"""
Performance Metrics & Evaluation Module.

This module implements:
- Precision, Recall, Accuracy calculations
- Execution time tracking
- Performance reporting
- Test result validation

Metrics from documentation:
- Precision: True Positives / (True Positives + False Positives)
- Recall: True Positives / (True Positives + False Negatives)
- Accuracy: (True Positives + True Negatives) / Total
- F1 Score: 2 * (Precision * Recall) / (Precision + Recall)
"""

import time
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

from .models import DuplicateGroup
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for duplicate detection."""
    precision: float
    recall: float
    accuracy: float
    f1_score: float
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    execution_time: float
    records_processed: int
    records_per_second: float


@dataclass
class TestResult:
    """Test result with ground truth comparison."""
    dataset_name: str
    dataset_size: int
    metrics: PerformanceMetrics
    duplicate_groups_found: int
    expected_duplicates: int
    timestamp: datetime


class PerformanceEvaluator:
    """
    Evaluates performance of duplicate detection system.
    
    Calculates precision, recall, accuracy, and other metrics
    by comparing detected duplicates against ground truth.
    """
    
    def __init__(self):
        """Initialize the performance evaluator."""
        self.test_results = []
    
    def calculate_metrics(self,
                         detected_groups: List[DuplicateGroup],
                         ground_truth_pairs: Set[Tuple[int, int]],
                         total_records: int,
                         execution_time: float) -> PerformanceMetrics:
        """
        Calculate performance metrics.
        
        Args:
            detected_groups: List of detected duplicate groups
            ground_truth_pairs: Set of (record_id1, record_id2) tuples representing true duplicates
            total_records: Total number of records in dataset
            execution_time: Time taken for detection (seconds)
            
        Returns:
            PerformanceMetrics object
        """
        logger.info("Calculating performance metrics...")
        
        # Convert detected groups to pairs
        detected_pairs = self._groups_to_pairs(detected_groups)
        
        # Calculate confusion matrix
        true_positives = len(detected_pairs & ground_truth_pairs)
        false_positives = len(detected_pairs - ground_truth_pairs)
        false_negatives = len(ground_truth_pairs - detected_pairs)
        
        # Calculate total possible pairs
        total_possible_pairs = (total_records * (total_records - 1)) // 2
        true_negatives = total_possible_pairs - true_positives - false_positives - false_negatives
        
        # Calculate metrics
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        accuracy = (true_positives + true_negatives) / total_possible_pairs if total_possible_pairs > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        records_per_second = total_records / execution_time if execution_time > 0 else 0.0
        
        metrics = PerformanceMetrics(
            precision=precision,
            recall=recall,
            accuracy=accuracy,
            f1_score=f1_score,
            true_positives=true_positives,
            false_positives=false_positives,
            true_negatives=true_negatives,
            false_negatives=false_negatives,
            execution_time=execution_time,
            records_processed=total_records,
            records_per_second=records_per_second
        )
        
        logger.info(f"Metrics calculated - Precision: {precision:.4f}, Recall: {recall:.4f}, "
                   f"Accuracy: {accuracy:.4f}, F1: {f1_score:.4f}")
        
        return metrics
    
    def _groups_to_pairs(self, groups: List[DuplicateGroup]) -> Set[Tuple[int, int]]:
        """
        Convert duplicate groups to pairs of record indices.
        
        Args:
            groups: List of duplicate groups
            
        Returns:
            Set of (record_id1, record_id2) tuples
        """
        pairs = set()
        
        for group in groups:
            # Get record indices
            indices = []
            for record in group.records:
                # Try to get original index
                idx = record.get('_original_index')
                if idx is None:
                    # Try to get from id field
                    idx = record.get('id')
                if idx is not None:
                    indices.append(int(idx))
            
            # Create all pairs within this group
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    pair = tuple(sorted([indices[i], indices[j]]))
                    pairs.add(pair)
        
        return pairs
    
    def run_test(self,
                dataset_name: str,
                detection_function,
                dataset,
                ground_truth_pairs: Set[Tuple[int, int]],
                **detection_kwargs) -> TestResult:
        """
        Run a test with timing and metric calculation.
        
        Args:
            dataset_name: Name of the test dataset
            detection_function: Function that performs duplicate detection
            dataset: The dataset to test on
            ground_truth_pairs: Set of true duplicate pairs
            **detection_kwargs: Additional arguments for detection function
            
        Returns:
            TestResult object
        """
        logger.info(f"Running test: {dataset_name}")
        
        # Time the detection
        start_time = time.time()
        detected_groups = detection_function(dataset, **detection_kwargs)
        execution_time = time.time() - start_time
        
        # Calculate metrics
        total_records = len(dataset) if hasattr(dataset, '__len__') else 0
        metrics = self.calculate_metrics(
            detected_groups,
            ground_truth_pairs,
            total_records,
            execution_time
        )
        
        # Create test result
        result = TestResult(
            dataset_name=dataset_name,
            dataset_size=total_records,
            metrics=metrics,
            duplicate_groups_found=len(detected_groups),
            expected_duplicates=len(ground_truth_pairs),
            timestamp=datetime.now()
        )
        
        self.test_results.append(result)
        
        logger.info(f"Test complete: {dataset_name} - "
                   f"Precision: {metrics.precision:.4f}, "
                   f"Recall: {metrics.recall:.4f}, "
                   f"Time: {execution_time:.2f}s")
        
        return result
    
    def generate_report(self, test_results: Optional[List[TestResult]] = None) -> Dict:
        """
        Generate a comprehensive performance report.
        
        Args:
            test_results: Optional list of test results (uses stored results if None)
            
        Returns:
            Dictionary containing the report
        """
        if test_results is None:
            test_results = self.test_results
        
        if not test_results:
            return {"error": "No test results available"}
        
        # Calculate aggregate metrics
        avg_precision = sum(r.metrics.precision for r in test_results) / len(test_results)
        avg_recall = sum(r.metrics.recall for r in test_results) / len(test_results)
        avg_accuracy = sum(r.metrics.accuracy for r in test_results) / len(test_results)
        avg_f1 = sum(r.metrics.f1_score for r in test_results) / len(test_results)
        avg_time = sum(r.metrics.execution_time for r in test_results) / len(test_results)
        avg_speed = sum(r.metrics.records_per_second for r in test_results) / len(test_results)
        
        report = {
            "summary": {
                "total_tests": len(test_results),
                "average_precision": round(avg_precision, 4),
                "average_recall": round(avg_recall, 4),
                "average_accuracy": round(avg_accuracy, 4),
                "average_f1_score": round(avg_f1, 4),
                "average_execution_time": round(avg_time, 4),
                "average_records_per_second": round(avg_speed, 2)
            },
            "individual_tests": []
        }
        
        for result in test_results:
            test_info = {
                "dataset_name": result.dataset_name,
                "dataset_size": result.dataset_size,
                "timestamp": result.timestamp.isoformat(),
                "metrics": {
                    "precision": round(result.metrics.precision, 4),
                    "recall": round(result.metrics.recall, 4),
                    "accuracy": round(result.metrics.accuracy, 4),
                    "f1_score": round(result.metrics.f1_score, 4),
                    "execution_time": round(result.metrics.execution_time, 4),
                    "records_per_second": round(result.metrics.records_per_second, 2)
                },
                "confusion_matrix": {
                    "true_positives": result.metrics.true_positives,
                    "false_positives": result.metrics.false_positives,
                    "true_negatives": result.metrics.true_negatives,
                    "false_negatives": result.metrics.false_negatives
                },
                "detection_results": {
                    "groups_found": result.duplicate_groups_found,
                    "expected_duplicates": result.expected_duplicates
                }
            }
            report["individual_tests"].append(test_info)
        
        return report
    
    def print_report(self, test_results: Optional[List[TestResult]] = None):
        """
        Print a formatted performance report.
        
        Args:
            test_results: Optional list of test results
        """
        report = self.generate_report(test_results)
        
        if "error" in report:
            print(report["error"])
            return
        
        print("\n" + "="*80)
        print("PERFORMANCE EVALUATION REPORT")
        print("="*80)
        
        summary = report["summary"]
        print(f"\nSummary ({summary['total_tests']} tests):")
        print(f"  Average Precision:  {summary['average_precision']:.4f}")
        print(f"  Average Recall:     {summary['average_recall']:.4f}")
        print(f"  Average Accuracy:   {summary['average_accuracy']:.4f}")
        print(f"  Average F1 Score:   {summary['average_f1_score']:.4f}")
        print(f"  Average Time:       {summary['average_execution_time']:.4f}s")
        print(f"  Average Speed:      {summary['average_records_per_second']:.2f} records/sec")
        
        print("\n" + "-"*80)
        print("Individual Test Results:")
        print("-"*80)
        
        for test in report["individual_tests"]:
            print(f"\nDataset: {test['dataset_name']}")
            print(f"  Size: {test['dataset_size']} records")
            print(f"  Precision: {test['metrics']['precision']:.4f}")
            print(f"  Recall:    {test['metrics']['recall']:.4f}")
            print(f"  Accuracy:  {test['metrics']['accuracy']:.4f}")
            print(f"  F1 Score:  {test['metrics']['f1_score']:.4f}")
            print(f"  Time:      {test['metrics']['execution_time']:.4f}s")
            print(f"  Speed:     {test['metrics']['records_per_second']:.2f} records/sec")
            
            cm = test['confusion_matrix']
            print(f"  Confusion Matrix:")
            print(f"    TP: {cm['true_positives']}, FP: {cm['false_positives']}")
            print(f"    TN: {cm['true_negatives']}, FN: {cm['false_negatives']}")
        
        print("\n" + "="*80)


class ExecutionTimer:
    """Context manager for timing code execution."""
    
    def __init__(self, name: str = "Operation"):
        """
        Initialize the timer.
        
        Args:
            name: Name of the operation being timed
        """
        self.name = name
        self.start_time = None
        self.end_time = None
        self.elapsed_time = None
    
    def __enter__(self):
        """Start the timer."""
        self.start_time = time.time()
        logger.debug(f"Starting timer: {self.name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the timer."""
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time
        logger.info(f"{self.name} completed in {self.elapsed_time:.4f} seconds")
        return False
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        if self.elapsed_time is None:
            if self.start_time is not None:
                return time.time() - self.start_time
            return 0.0
        return self.elapsed_time


# Convenience functions
def calculate_precision_recall(detected_groups: List[DuplicateGroup],
                               ground_truth_pairs: Set[Tuple[int, int]]) -> Tuple[float, float]:
    """
    Calculate precision and recall.
    
    Args:
        detected_groups: Detected duplicate groups
        ground_truth_pairs: True duplicate pairs
        
    Returns:
        Tuple of (precision, recall)
    """
    evaluator = PerformanceEvaluator()
    detected_pairs = evaluator._groups_to_pairs(detected_groups)
    
    true_positives = len(detected_pairs & ground_truth_pairs)
    false_positives = len(detected_pairs - ground_truth_pairs)
    false_negatives = len(ground_truth_pairs - detected_pairs)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    
    return precision, recall
