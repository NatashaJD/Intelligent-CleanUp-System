# MIT License
# Copyright (c) 2026 Judy Natasha Wambui Gachanja

"""
Exact Matcher component for the Intelligent Duplicate Detection & Cleanup System.

This module implements:
- Hash-based duplicate detection with O(n) time complexity
- Field-based matching on user-selected columns
- Composite key duplicate detection functionality
- Grouping of exact duplicates with 100% similarity scores
- Efficient processing for large datasets

The exact matcher uses Python's built-in hash functions with composite key
generation for multi-field matching, ensuring optimal performance.
"""

import pandas as pd
import hashlib
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
import time

from .models import DuplicateGroup, MatchingConfig
from .normalizer import DataNormalizer
from .logging_config import get_logger
from .exceptions import ProcessingError, DataValidationError

logger = get_logger(__name__)


class ExactMatcher:
    """
    Performs hash-based exact duplicate detection with O(n) complexity.
    
    This class provides efficient exact duplicate detection using hash-based
    comparison with support for single-field and composite key matching.
    """
    
    def __init__(self, normalizer: Optional[DataNormalizer] = None):
        """
        Initialize the ExactMatcher.
        
        Args:
            normalizer: Optional DataNormalizer instance for data preprocessing
        """
        self.normalizer = normalizer or DataNormalizer()
        self.hash_algorithm = 'sha256'  # Consistent hashing algorithm
        
    def find_exact_duplicates(self, df: pd.DataFrame, key_fields: List[str], 
                            field_configs: Optional[Dict[str, str]] = None,
                            use_normalized: bool = True) -> List[DuplicateGroup]:
        """
        Find exact duplicates in a DataFrame using hash-based comparison.
        
        Args:
            df: Input DataFrame
            key_fields: List of field names to use for duplicate detection
            field_configs: Optional field normalization configurations
            use_normalized: Whether to use normalized data for comparison
            
        Returns:
            List of DuplicateGroup objects containing duplicate records
            
        Raises:
            ProcessingError: If duplicate detection fails
            DataValidationError: If input parameters are invalid
        """
        if df.empty:
            logger.warning("Empty DataFrame provided for duplicate detection")
            return []
        
        if not key_fields:
            raise DataValidationError("No key fields specified for duplicate detection")
        
        # Validate key fields exist in DataFrame
        missing_fields = [field for field in key_fields if field not in df.columns]
        if missing_fields:
            raise DataValidationError(f"Key fields not found in DataFrame: {missing_fields}")
        
        logger.info(f"Starting exact duplicate detection on {len(df)} records using fields: {key_fields}")
        start_time = time.time()
        
        try:
            # Prepare field configurations
            if field_configs is None:
                field_configs = {field: 'text' for field in key_fields}
            
            # Normalize data if requested and not already normalized
            df_working = df.copy()
            if use_normalized:
                # Check if normalized columns already exist
                normalized_cols = [f"{field}_normalized" for field in key_fields]
                missing_normalized = [col for col in normalized_cols if col not in df.columns]
                
                if missing_normalized:
                    logger.debug("Normalizing data for exact matching")
                    df_working = self.normalizer.normalize_dataframe(df_working, field_configs)
            
            # Create hash keys for all records
            hash_to_indices = self._create_hash_index(df_working, key_fields, field_configs, use_normalized)
            
            # Group duplicates
            duplicate_groups = self._group_duplicates(df_working, hash_to_indices, key_fields)
            
            processing_time = time.time() - start_time
            logger.info(f"Exact duplicate detection completed in {processing_time:.2f} seconds")
            logger.info(f"Found {len(duplicate_groups)} duplicate groups from {len(df)} records")
            
            return duplicate_groups
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Exact duplicate detection failed after {processing_time:.2f} seconds: {e}")
            raise ProcessingError(f"Exact duplicate detection failed: {e}", "exact_matching", len(df))
    
    def _create_hash_index(self, df: pd.DataFrame, key_fields: List[str], 
                          field_configs: Dict[str, str], use_normalized: bool) -> Dict[str, List[int]]:
        """
        Create a hash index mapping hash keys to record indices.
        
        Args:
            df: DataFrame containing the data
            key_fields: Fields to use for hash key generation
            field_configs: Field normalization configurations
            use_normalized: Whether to use normalized columns
            
        Returns:
            Dictionary mapping hash keys to lists of record indices
        """
        hash_to_indices = defaultdict(list)
        
        logger.debug(f"Creating hash index for {len(df)} records")
        
        for idx, row in df.iterrows():
            try:
                # Create hash key for this record
                hash_key = self._create_hash_key(row, key_fields, field_configs, use_normalized)
                hash_to_indices[hash_key].append(idx)
                
            except Exception as e:
                logger.warning(f"Failed to create hash key for record {idx}: {e}")
                # Skip this record but continue processing
                continue
        
        logger.debug(f"Created hash index with {len(hash_to_indices)} unique keys")
        return dict(hash_to_indices)
    
    def _create_hash_key(self, record: pd.Series, key_fields: List[str], 
                        field_configs: Dict[str, str], use_normalized: bool) -> str:
        """
        Create a hash key for a single record.
        
        Args:
            record: Pandas Series representing a single record
            key_fields: Fields to include in the hash key
            field_configs: Field normalization configurations
            use_normalized: Whether to use normalized columns
            
        Returns:
            Hash key string
        """
        # Extract values for key fields
        key_values = []
        
        for field in key_fields:
            if use_normalized:
                # Use normalized column if available
                normalized_field = f"{field}_normalized"
                if normalized_field in record.index:
                    value = record[normalized_field]
                else:
                    # Fall back to original field with on-the-fly normalization
                    original_value = record.get(field, "")
                    norm_type = field_configs.get(field, 'text')
                    value = self._normalize_value(original_value, norm_type)
            else:
                # Use original field value
                value = str(record.get(field, ""))
            
            key_values.append(str(value))
        
        # Create composite key string
        composite_key = "||".join(key_values)
        
        # Create hash for consistent key length and collision resistance
        hash_object = hashlib.new(self.hash_algorithm)
        hash_object.update(composite_key.encode('utf-8'))
        hash_key = hash_object.hexdigest()
        
        return hash_key
    
    def _normalize_value(self, value: Any, norm_type: str) -> str:
        """
        Normalize a single value based on its type.
        
        Args:
            value: Value to normalize
            norm_type: Type of normalization to apply
            
        Returns:
            Normalized value string
        """
        if norm_type == 'text':
            return self.normalizer.normalize_text(value)
        elif norm_type == 'text_aggressive':
            return self.normalizer.normalize_text_aggressive(value)
        elif norm_type == 'date':
            return self.normalizer.normalize_date(value)
        elif norm_type == 'numeric':
            return self.normalizer.normalize_numeric(value)
        elif norm_type == 'phone':
            return self.normalizer.normalize_phone(value)
        elif norm_type == 'email':
            return self.normalizer.normalize_email(value)
        else:
            return self.normalizer.normalize_text(value)
    
    def _group_duplicates(self, df: pd.DataFrame, hash_to_indices: Dict[str, List[int]], 
                         key_fields: List[str]) -> List[DuplicateGroup]:
        """
        Group duplicate records based on hash index.
        
        Args:
            df: DataFrame containing the data
            hash_to_indices: Hash index mapping
            key_fields: Fields used for duplicate detection
            
        Returns:
            List of DuplicateGroup objects
        """
        duplicate_groups = []
        group_counter = 1
        
        for hash_key, indices in hash_to_indices.items():
            # Only create groups for actual duplicates (more than 1 record)
            if len(indices) > 1:
                # Extract records for this duplicate group
                records = []
                for idx in indices:
                    record = df.iloc[idx].to_dict()
                    # Add original index for tracking
                    record['_original_index'] = idx
                    records.append(record)
                
                # Create duplicate group
                group = DuplicateGroup(
                    group_id=f"exact_group_{group_counter}",
                    records=records,
                    similarity_score=100.0,  # Exact matches are 100% similar
                    detection_method='exact',
                    recommended_action=self._recommend_action(records, key_fields)
                )
                
                duplicate_groups.append(group)
                group_counter += 1
                
                logger.debug(f"Created duplicate group {group.group_id} with {len(records)} records")
        
        return duplicate_groups
    
    def _recommend_action(self, records: List[Dict[str, Any]], key_fields: List[str]) -> str:
        """
        Recommend an action for a duplicate group based on record characteristics.
        
        Args:
            records: List of duplicate records
            key_fields: Fields used for duplicate detection
            
        Returns:
            Recommended action string
        """
        if len(records) == 2:
            # For pairs, recommend merge if records have complementary data
            if self._have_complementary_data(records):
                return 'merge'
            else:
                return 'keep_first'
        elif len(records) <= 5:
            # For small groups, recommend merge
            return 'merge'
        else:
            # For large groups, flag for manual review
            return 'flag'
    
    def _have_complementary_data(self, records: List[Dict[str, Any]]) -> bool:
        """
        Check if records have complementary data that would benefit from merging.
        
        Args:
            records: List of records to check
            
        Returns:
            True if records have complementary data
        """
        if len(records) != 2:
            return False
        
        record1, record2 = records
        
        # Count non-null fields in each record
        non_null_1 = sum(1 for v in record1.values() if pd.notna(v) and str(v).strip())
        non_null_2 = sum(1 for v in record2.values() if pd.notna(v) and str(v).strip())
        
        # If one record has significantly more data, they're complementary
        total_fields = len(record1)
        if abs(non_null_1 - non_null_2) > total_fields * 0.2:
            return True
        
        # Check for fields where one record has data and the other doesn't
        complementary_fields = 0
        for key in record1.keys():
            if key.startswith('_'):  # Skip internal fields
                continue
            
            val1 = record1.get(key)
            val2 = record2.get(key)
            
            # One has data, other doesn't
            if (pd.notna(val1) and str(val1).strip()) and (pd.isna(val2) or not str(val2).strip()):
                complementary_fields += 1
            elif (pd.isna(val1) or not str(val1).strip()) and (pd.notna(val2) and str(val2).strip()):
                complementary_fields += 1
        
        # If more than 20% of fields are complementary, recommend merge
        return complementary_fields > len(record1) * 0.2
    
    def get_duplicate_statistics(self, duplicate_groups: List[DuplicateGroup]) -> Dict[str, Any]:
        """
        Get statistics about the duplicate detection results.
        
        Args:
            duplicate_groups: List of duplicate groups found
            
        Returns:
            Dictionary containing statistics
        """
        if not duplicate_groups:
            return {
                'total_groups': 0,
                'total_duplicate_records': 0,
                'average_group_size': 0,
                'largest_group_size': 0,
                'recommended_actions': {}
            }
        
        total_records = sum(len(group.records) for group in duplicate_groups)
        group_sizes = [len(group.records) for group in duplicate_groups]
        
        # Count recommended actions
        action_counts = defaultdict(int)
        for group in duplicate_groups:
            action_counts[group.recommended_action] += 1
        
        stats = {
            'total_groups': len(duplicate_groups),
            'total_duplicate_records': total_records,
            'average_group_size': total_records / len(duplicate_groups),
            'largest_group_size': max(group_sizes),
            'smallest_group_size': min(group_sizes),
            'recommended_actions': dict(action_counts),
            'group_size_distribution': {
                'pairs': len([g for g in duplicate_groups if len(g.records) == 2]),
                'small_groups_3_5': len([g for g in duplicate_groups if 3 <= len(g.records) <= 5]),
                'large_groups_6_plus': len([g for g in duplicate_groups if len(g.records) >= 6])
            }
        }
        
        return stats
    
    def find_duplicates_by_single_field(self, df: pd.DataFrame, field_name: str, 
                                      normalize: bool = True) -> List[DuplicateGroup]:
        """
        Convenience method to find duplicates based on a single field.
        
        Args:
            df: Input DataFrame
            field_name: Single field name to use for duplicate detection
            normalize: Whether to normalize the field before comparison
            
        Returns:
            List of DuplicateGroup objects
        """
        field_config = {field_name: 'text'}  # Default to text normalization
        
        return self.find_exact_duplicates(
            df=df,
            key_fields=[field_name],
            field_configs=field_config,
            use_normalized=normalize
        )
    
    def find_duplicates_by_composite_key(self, df: pd.DataFrame, key_fields: List[str],
                                       field_types: Optional[List[str]] = None) -> List[DuplicateGroup]:
        """
        Convenience method to find duplicates using a composite key.
        
        Args:
            df: Input DataFrame
            key_fields: List of field names for the composite key
            field_types: Optional list of normalization types for each field
            
        Returns:
            List of DuplicateGroup objects
        """
        if field_types is None:
            field_types = ['text'] * len(key_fields)
        
        if len(field_types) != len(key_fields):
            raise DataValidationError("Number of field types must match number of key fields")
        
        field_configs = dict(zip(key_fields, field_types))
        
        return self.find_exact_duplicates(
            df=df,
            key_fields=key_fields,
            field_configs=field_configs,
            use_normalized=True
        )


# Convenience functions
def find_exact_duplicates_simple(df: pd.DataFrame, key_fields: List[str]) -> List[DuplicateGroup]:
    """
    Simple convenience function to find exact duplicates.
    
    Args:
        df: Input DataFrame
        key_fields: List of field names to use for duplicate detection
        
    Returns:
        List of DuplicateGroup objects
    """
    matcher = ExactMatcher()
    return matcher.find_exact_duplicates(df, key_fields)


def get_duplicate_summary(duplicate_groups: List[DuplicateGroup]) -> str:
    """
    Get a human-readable summary of duplicate detection results.
    
    Args:
        duplicate_groups: List of duplicate groups
        
    Returns:
        Formatted summary string
    """
    if not duplicate_groups:
        return "No duplicates found."
    
    matcher = ExactMatcher()
    stats = matcher.get_duplicate_statistics(duplicate_groups)
    
    summary = f"""Duplicate Detection Summary:
    • Found {stats['total_groups']} duplicate groups
    • Total duplicate records: {stats['total_duplicate_records']}
    • Average group size: {stats['average_group_size']:.1f}
    • Largest group: {stats['largest_group_size']} records
    
    Group Size Distribution:
    • Pairs (2 records): {stats['group_size_distribution']['pairs']}
    • Small groups (3-5): {stats['group_size_distribution']['small_groups_3_5']}
    • Large groups (6+): {stats['group_size_distribution']['large_groups_6_plus']}
    
    Recommended Actions:
    """
    
    for action, count in stats['recommended_actions'].items():
        summary += f"    • {action}: {count} groups\n"
    
    return summary