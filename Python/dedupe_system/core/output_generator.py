"""
Output Generator component for the Intelligent Duplicate Detection & Cleanup System.

This module implements:
- Generation of cleaned datasets in same format as input (CSV/JSON)
- Creation of comprehensive audit logs with all required fields
- Production of summary reports with statistics and performance metrics
- Data integrity preservation throughout processing
- Validation that output file formats are parseable by standard libraries

The output generator ensures complete traceability and compliance-ready reporting.
"""

import pandas as pd
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import time
import tracemalloc

from .models import DuplicateGroup, ProcessingStats, AuditEntry
from .logging_config import get_logger
from .exceptions import ProcessingError, DataValidationError

logger = get_logger(__name__)


class OutputGenerator:
    """
    Generates cleaned datasets, audit logs, and summary reports.
    
    This class handles all output generation while maintaining data integrity
    and ensuring compliance-ready documentation.
    """
    
    def __init__(self, output_dir: str = "outputs", preserve_format: bool = True):
        """
        Initialize the OutputGenerator.
        
        Args:
            output_dir: Directory to store output files
            preserve_format: Whether to preserve original file format
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.preserve_format = preserve_format
        
        # Track generation session
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def generate_cleaned_dataset(self, df: pd.DataFrame, original_format: str = 'csv',
                               filename: Optional[str] = None) -> str:
        """
        Generate cleaned dataset in the same format as input.
        
        Args:
            df: DataFrame with resolution applied
            original_format: Original file format ('csv' or 'json')
            filename: Optional custom filename
            
        Returns:
            Path to the generated cleaned dataset file
            
        Raises:
            ProcessingError: If output generation fails
        """
        logger.info(f"Generating cleaned dataset in {original_format} format")
        
        try:
            # Create cleaned version by filtering out internal columns and applying resolution
            df_cleaned = self._prepare_cleaned_dataframe(df)
            
            # Generate filename if not provided
            if filename is None:
                filename = f"cleaned_data_{self.session_timestamp}"
            
            # Generate output based on format
            if original_format.lower() == 'csv':
                output_path = self.output_dir / f"{filename}.csv"
                self._write_csv(df_cleaned, output_path)
            elif original_format.lower() == 'json':
                output_path = self.output_dir / f"{filename}.json"
                self._write_json(df_cleaned, output_path)
            else:
                raise ProcessingError(f"Unsupported output format: {original_format}")
            
            # Validate the generated file
            self._validate_output_file(output_path, original_format)
            
            logger.info(f"Cleaned dataset generated: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to generate cleaned dataset: {e}")
            raise ProcessingError(f"Cleaned dataset generation failed: {e}")
    
    def generate_audit_log(self, audit_entries: List[AuditEntry], 
                          filename: Optional[str] = None) -> str:
        """
        Generate comprehensive audit log with all required fields.
        
        Args:
            audit_entries: List of audit entries to include
            filename: Optional custom filename
            
        Returns:
            Path to the generated audit log file
        """
        logger.info(f"Generating audit log with {len(audit_entries)} entries")
        
        try:
            # Generate filename if not provided
            if filename is None:
                filename = f"audit_log_{self.session_timestamp}"
            
            output_path = self.output_dir / f"{filename}.csv"
            
            # Convert audit entries to DataFrame
            audit_data = []
            for entry in audit_entries:
                audit_data.append({
                    'record_id': entry.record_id,
                    'action': entry.action,
                    'reason': entry.reason,
                    'similarity_score': entry.similarity_score,
                    'timestamp': entry.timestamp.isoformat(),
                    'user_decision': entry.user_decision
                })
            
            if audit_data:
                audit_df = pd.DataFrame(audit_data)
                
                # Write audit log as CSV
                audit_df.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)
                
                # Validate the audit log
                self._validate_audit_log(output_path)
                
                logger.info(f"Audit log generated: {output_path}")
            else:
                # Create empty audit log with headers
                empty_audit = pd.DataFrame(columns=[
                    'record_id', 'action', 'reason', 'similarity_score', 'timestamp', 'user_decision'
                ])
                empty_audit.to_csv(output_path, index=False)
                logger.info(f"Empty audit log generated: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to generate audit log: {e}")
            raise ProcessingError(f"Audit log generation failed: {e}")
    
    def generate_summary_report(self, stats: ProcessingStats, duplicate_groups: List[DuplicateGroup],
                              original_record_count: int, filename: Optional[str] = None) -> str:
        """
        Generate summary report with statistics and performance metrics.
        
        Args:
            stats: Processing statistics
            duplicate_groups: List of duplicate groups found
            original_record_count: Original number of records
            filename: Optional custom filename
            
        Returns:
            Path to the generated summary report file
        """
        logger.info("Generating summary report")
        
        try:
            # Generate filename if not provided
            if filename is None:
                filename = f"summary_report_{self.session_timestamp}"
            
            output_path = self.output_dir / f"{filename}.json"
            
            # Create comprehensive summary
            summary = {
                'session_info': {
                    'timestamp': self.session_timestamp,
                    'generation_time': datetime.now().isoformat()
                },
                'data_summary': {
                    'original_records': original_record_count,
                    'total_records_processed': stats.total_records,
                    'duplicate_groups_found': stats.duplicate_groups_found,
                    'exact_duplicates': stats.exact_duplicates,
                    'fuzzy_duplicates': stats.fuzzy_duplicates
                },
                'performance_metrics': {
                    'processing_time_seconds': stats.processing_time,
                    'memory_usage_mb': stats.memory_usage,
                    'records_per_second': stats.total_records / max(stats.processing_time, 0.001)
                },
                'duplicate_analysis': self._analyze_duplicate_groups(duplicate_groups),
                'data_quality_metrics': self._calculate_data_quality_metrics(
                    original_record_count, stats
                )
            }
            
            # Write summary as JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            # Validate the summary report
            self._validate_summary_report(output_path)
            
            logger.info(f"Summary report generated: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to generate summary report: {e}")
            raise ProcessingError(f"Summary report generation failed: {e}")
    
    def generate_all_outputs(self, df: pd.DataFrame, audit_entries: List[AuditEntry],
                           stats: ProcessingStats, duplicate_groups: List[DuplicateGroup],
                           original_format: str = 'csv', 
                           base_filename: Optional[str] = None) -> Dict[str, str]:
        """
        Generate all output files in one operation.
        
        Args:
            df: DataFrame with resolution applied
            audit_entries: List of audit entries
            stats: Processing statistics
            duplicate_groups: List of duplicate groups
            original_format: Original file format
            base_filename: Base filename for all outputs
            
        Returns:
            Dictionary mapping output type to file path
        """
        logger.info("Generating all output files")
        
        try:
            outputs = {}
            
            # Use base filename or generate one
            if base_filename is None:
                base_filename = f"dedupe_results_{self.session_timestamp}"
            
            # Generate cleaned dataset
            outputs['cleaned_data'] = self.generate_cleaned_dataset(
                df, original_format, f"{base_filename}_cleaned"
            )
            
            # Generate audit log
            outputs['audit_log'] = self.generate_audit_log(
                audit_entries, f"{base_filename}_audit"
            )
            
            # Generate summary report
            outputs['summary_report'] = self.generate_summary_report(
                stats, duplicate_groups, len(df), f"{base_filename}_summary"
            )
            
            logger.info(f"All outputs generated successfully: {list(outputs.keys())}")
            return outputs
            
        except Exception as e:
            logger.error(f"Failed to generate all outputs: {e}")
            raise ProcessingError(f"Output generation failed: {e}")
    
    def _prepare_cleaned_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare cleaned DataFrame by applying resolution and removing internal columns.
        
        Args:
            df: DataFrame with resolution applied
            
        Returns:
            Cleaned DataFrame ready for output
        """
        df_cleaned = df.copy()
        
        # Remove internal tracking columns
        internal_columns = [col for col in df_cleaned.columns if col.startswith('_')]
        df_cleaned = df_cleaned.drop(columns=internal_columns, errors='ignore')
        
        # Remove normalized columns (keep only original data)
        normalized_columns = [col for col in df_cleaned.columns if col.endswith('_normalized')]
        df_cleaned = df_cleaned.drop(columns=normalized_columns, errors='ignore')
        
        # Apply resolution logic to determine which records to include
        if '_resolution_status' in df.columns:
            # Include records based on resolution status
            # Keep: original, kept, merged_primary, flagged
            # Exclude: soft_deleted, hard_deleted, merged_secondary
            include_statuses = ['original', 'kept', 'merged_primary', 'flagged']
            
            # If no resolution status, include all records
            if df['_resolution_status'].notna().any():
                mask = df['_resolution_status'].isin(include_statuses) | df['_resolution_status'].isna()
                df_cleaned = df_cleaned[mask]
        
        logger.debug(f"Cleaned DataFrame prepared: {len(df_cleaned)} records, {len(df_cleaned.columns)} columns")
        return df_cleaned
    
    def _write_csv(self, df: pd.DataFrame, output_path: Path):
        """Write DataFrame to CSV file with proper formatting."""
        df.to_csv(output_path, index=False, encoding='utf-8', quoting=csv.QUOTE_MINIMAL)
    
    def _write_json(self, df: pd.DataFrame, output_path: Path):
        """Write DataFrame to JSON file with proper formatting."""
        # Convert DataFrame to list of dictionaries
        records = df.to_dict('records')
        
        # Write as JSON array
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False, default=str)
    
    def _validate_output_file(self, file_path: Path, format_type: str):
        """
        Validate that the output file is properly formatted and parseable.
        
        Args:
            file_path: Path to the file to validate
            format_type: Expected format ('csv' or 'json')
        """
        try:
            if format_type.lower() == 'csv':
                # Try to read the CSV file
                test_df = pd.read_csv(file_path)
                if test_df.empty:
                    logger.warning(f"Generated CSV file is empty: {file_path}")
                else:
                    logger.debug(f"CSV validation passed: {len(test_df)} records, {len(test_df.columns)} columns")
            
            elif format_type.lower() == 'json':
                # Try to read the JSON file
                with open(file_path, 'r', encoding='utf-8') as f:
                    test_data = json.load(f)
                if not test_data:
                    logger.warning(f"Generated JSON file is empty: {file_path}")
                else:
                    logger.debug(f"JSON validation passed: {len(test_data)} records")
            
        except Exception as e:
            raise ProcessingError(f"Output file validation failed for {file_path}: {e}")
    
    def _validate_audit_log(self, file_path: Path):
        """Validate that the audit log is properly formatted."""
        try:
            audit_df = pd.read_csv(file_path)
            
            # Check required columns
            required_columns = ['record_id', 'action', 'reason', 'timestamp', 'user_decision']
            missing_columns = [col for col in required_columns if col not in audit_df.columns]
            
            if missing_columns:
                raise ProcessingError(f"Audit log missing required columns: {missing_columns}")
            
            logger.debug(f"Audit log validation passed: {len(audit_df)} entries")
            
        except Exception as e:
            raise ProcessingError(f"Audit log validation failed for {file_path}: {e}")
    
    def _validate_summary_report(self, file_path: Path):
        """Validate that the summary report is properly formatted."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                summary = json.load(f)
            
            # Check required sections
            required_sections = ['session_info', 'data_summary', 'performance_metrics']
            missing_sections = [section for section in required_sections if section not in summary]
            
            if missing_sections:
                raise ProcessingError(f"Summary report missing required sections: {missing_sections}")
            
            logger.debug("Summary report validation passed")
            
        except Exception as e:
            raise ProcessingError(f"Summary report validation failed for {file_path}: {e}")
    
    def _analyze_duplicate_groups(self, duplicate_groups: List[DuplicateGroup]) -> Dict[str, Any]:
        """
        Analyze duplicate groups for summary reporting.
        
        Args:
            duplicate_groups: List of duplicate groups
            
        Returns:
            Dictionary containing duplicate group analysis
        """
        if not duplicate_groups:
            return {
                'total_groups': 0,
                'total_duplicate_records': 0,
                'group_size_distribution': {},
                'detection_methods': {},
                'recommended_actions': {}
            }
        
        # Calculate group size distribution
        group_sizes = [len(group.records) for group in duplicate_groups]
        size_distribution = {
            'pairs': len([size for size in group_sizes if size == 2]),
            'small_groups_3_5': len([size for size in group_sizes if 3 <= size <= 5]),
            'large_groups_6_plus': len([size for size in group_sizes if size >= 6]),
            'average_size': sum(group_sizes) / len(group_sizes),
            'largest_group': max(group_sizes),
            'smallest_group': min(group_sizes)
        }
        
        # Count detection methods
        detection_methods = {}
        for group in duplicate_groups:
            method = group.detection_method
            detection_methods[method] = detection_methods.get(method, 0) + 1
        
        # Count recommended actions
        recommended_actions = {}
        for group in duplicate_groups:
            action = group.recommended_action
            recommended_actions[action] = recommended_actions.get(action, 0) + 1
        
        return {
            'total_groups': len(duplicate_groups),
            'total_duplicate_records': sum(group_sizes),
            'group_size_distribution': size_distribution,
            'detection_methods': detection_methods,
            'recommended_actions': recommended_actions
        }
    
    def _calculate_data_quality_metrics(self, original_count: int, 
                                      stats: ProcessingStats) -> Dict[str, Any]:
        """
        Calculate data quality metrics for reporting.
        
        Args:
            original_count: Original number of records
            stats: Processing statistics
            
        Returns:
            Dictionary containing data quality metrics
        """
        duplicate_rate = (stats.duplicate_groups_found * 2) / max(original_count, 1) * 100
        
        return {
            'duplicate_rate_percent': round(duplicate_rate, 2),
            'data_completeness_score': self._calculate_completeness_score(stats),
            'processing_efficiency': {
                'records_per_second': round(stats.total_records / max(stats.processing_time, 0.001), 2),
                'memory_efficiency_mb_per_1k_records': round(
                    (stats.memory_usage / max(stats.total_records, 1)) * 1000, 2
                )
            }
        }
    
    def _calculate_completeness_score(self, stats: ProcessingStats) -> float:
        """
        Calculate a data completeness score based on processing statistics.
        
        Args:
            stats: Processing statistics
            
        Returns:
            Completeness score (0-100)
        """
        # This is a simplified completeness score
        # In a real implementation, you'd analyze field completeness
        base_score = 85.0  # Base score for processed data
        
        # Adjust based on duplicate rate (fewer duplicates = higher quality)
        if stats.total_records > 0:
            duplicate_ratio = stats.duplicate_groups_found / stats.total_records
            quality_adjustment = (1 - duplicate_ratio) * 15  # Up to 15 point bonus
            return min(100.0, base_score + quality_adjustment)
        
        return base_score


# Convenience functions
def generate_outputs_from_pipeline(df: pd.DataFrame, audit_entries: List[AuditEntry],
                                 duplicate_groups: List[DuplicateGroup], 
                                 processing_time: float, memory_usage: float,
                                 original_format: str = 'csv',
                                 output_dir: str = "outputs") -> Dict[str, str]:
    """
    Convenience function to generate all outputs from a complete pipeline run.
    
    Args:
        df: DataFrame with resolution applied
        audit_entries: List of audit entries
        duplicate_groups: List of duplicate groups
        processing_time: Total processing time in seconds
        memory_usage: Peak memory usage in MB
        original_format: Original file format
        output_dir: Output directory
        
    Returns:
        Dictionary mapping output type to file path
    """
    # Create processing stats
    stats = ProcessingStats(
        total_records=len(df),
        duplicate_groups_found=len(duplicate_groups),
        exact_duplicates=len([g for g in duplicate_groups if g.detection_method == 'exact']),
        fuzzy_duplicates=len([g for g in duplicate_groups if g.detection_method == 'fuzzy']),
        processing_time=processing_time,
        memory_usage=memory_usage
    )
    
    # Generate outputs
    generator = OutputGenerator(output_dir)
    return generator.generate_all_outputs(df, audit_entries, stats, duplicate_groups, original_format)


def create_audit_entries_from_log_file(log_file_path: str) -> List[AuditEntry]:
    """
    Create audit entries from a log file (for testing purposes).
    
    Args:
        log_file_path: Path to the log file
        
    Returns:
        List of AuditEntry objects
    """
    audit_entries = []
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '"action":' in line and '"record_id":' in line:
                    try:
                        log_data = json.loads(line.strip())
                        
                        entry = AuditEntry(
                            record_id=log_data.get('record_id', ''),
                            action=log_data.get('action', ''),
                            reason=log_data.get('reason', ''),
                            similarity_score=log_data.get('similarity_score'),
                            timestamp=datetime.fromisoformat(log_data.get('timestamp', datetime.now().isoformat())),
                            user_decision=log_data.get('user_decision', False)
                        )
                        
                        audit_entries.append(entry)
                        
                    except (json.JSONDecodeError, ValueError):
                        continue
    
    except FileNotFoundError:
        logger.warning(f"Log file not found: {log_file_path}")
    
    return audit_entries