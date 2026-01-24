# MIT License
# Copyright (c) 2026 Judy Natasha Wambui Gachanja

"""
Fuzzy Matcher component for the Intelligent Duplicate Detection & Cleanup System.

This module implements:
- RapidFuzz-based similarity calculation
- Threshold-based filtering for duplicate detection
- Blocking strategy for performance optimization
- Normalization integration for consistent comparison
- Similarity score validation (0-100 range)

The fuzzy matcher provides approximate duplicate detection for records that are
similar but not exactly identical.
"""

import pandas as pd
from rapidfuzz import fuzz, process
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
import time
import itertools

from .models import DuplicateGroup, MatchingConfig
from .normalizer import DataNormalizer
from .logging_config import get_logger
from .exceptions import ProcessingError, DataValidationError

logger = get_logger(__name__)


class FuzzyMatcher:
    """
    Performs fuzzy duplicate detection using RapidFuzz similarity algorithms.
    
    This class provides approximate duplicate detection with configurable
    similarity thresholds and blocking strategies for performance.
    """
    
    def __init__(self, normalizer: Optional[DataNormalizer] = None):
        """
        Initialize the FuzzyMatcher.
        
        Args:
            normalizer: Optional DataNormalizer instance for data preprocessing
        """
        self.normalizer = normalizer or DataNormalizer()
        
        # Available similarity algorithms
        self.algorithms = {
            'ratio': fuzz.ratio,
            'partial_ratio': fuzz.partial_ratio,
            'token_sort_ratio': fuzz.token_sort_ratio,
            'token_set_ratio': fuzz.token_set_ratio,
            'WRatio': fuzz.WRatio
        }
        
    def find_fuzzy_duplicates(self, df: pd.DataFrame, key_fields: List[str],
                            threshold: float = 80.0, algorithm: str = 'WRatio',
                            field_configs: Optional[Dict[str, str]] = None,
                            use_normalized: bool = True,
                            max_comparisons: int = 100000) -> List[DuplicateGroup]:
        """
        Find fuzzy duplicates in a DataFrame using similarity comparison.
        
        Args:
            df: Input DataFrame
            key_fields: List of field names to use for duplicate detection
            threshold: Similarity threshold (0-100) for considering records as duplicates
            algorithm: Similarity algorithm to use
            field_configs: Optional field normalization configurations
            use_normalized: Whether to use normalized data for comparison
            max_comparisons: Maximum number of comparisons to prevent performance issues
            
        Returns:
            List of DuplicateGroup objects containing fuzzy duplicate records
            
        Raises:
            ProcessingError: If fuzzy matching fails
            DataValidationError: If input parameters are invalid
        """
        if df.empty:
            logger.warning("Empty DataFrame provided for fuzzy duplicate detection")
            return []
        
        if not key_fields:
            raise DataValidationError("No key fields specified for fuzzy duplicate detection")
        
        if not (0 <= threshold <= 100):
            raise DataValidationError(f"Threshold must be between 0 and 100, got {threshold}")
        
        if algorithm not in self.algorithms:
            raise DataValidationError(f"Unknown algorithm '{algorithm}'. Available: {list(self.algorithms.keys())}")
        
        # Validate key fields exist in DataFrame
        missing_fields = [field for field in key_fields if field not in df.columns]
        if missing_fields:
            raise DataValidationError(f"Key fields not found in DataFrame: {missing_fields}")
        
        logger.info(f"Starting fuzzy duplicate detection on {len(df)} records using {algorithm} algorithm")
        logger.info(f"Threshold: {threshold}%, Fields: {key_fields}")
        start_time = time.time()
        
        try:
            # Prepare field configurations
            if field_configs is None:
                field_configs = {field: 'text_aggressive' for field in key_fields}
            
            # Normalize data if requested
            df_working = df.copy()
            if use_normalized:
                normalized_cols = [f"{field}_normalized" for field in key_fields]
                missing_normalized = [col for col in normalized_cols if col not in df.columns]
                
                if missing_normalized:
                    logger.debug("Normalizing data for fuzzy matching")
                    df_working = self.normalizer.normalize_dataframe(df_working, field_configs)
            
            # Create composite keys for comparison
            composite_keys = self._create_composite_keys(df_working, key_fields, field_configs, use_normalized)
            
            # Apply blocking strategy to reduce comparisons
            blocks = self._create_blocks(composite_keys, max_comparisons)
            
            # Find fuzzy duplicates within blocks
            duplicate_groups = []
            similarity_func = self.algorithms[algorithm]
            
            for block_id, block_indices in blocks.items():
                if len(block_indices) < 2:
                    continue
                
                block_groups = self._find_duplicates_in_block(
                    df_working, block_indices, composite_keys, 
                    similarity_func, threshold, key_fields
                )
                duplicate_groups.extend(block_groups)
            
            processing_time = time.time() - start_time
            logger.info(f"Fuzzy duplicate detection completed in {processing_time:.2f} seconds")
            logger.info(f"Found {len(duplicate_groups)} fuzzy duplicate groups from {len(df)} records")
            
            return duplicate_groups
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Fuzzy duplicate detection failed after {processing_time:.2f} seconds: {e}")
            raise ProcessingError(f"Fuzzy duplicate detection failed: {e}", "fuzzy_matching", len(df))
    
    def _create_composite_keys(self, df: pd.DataFrame, key_fields: List[str],
                             field_configs: Dict[str, str], use_normalized: bool) -> List[str]:
        """
        Create composite keys for fuzzy comparison.
        
        Args:
            df: DataFrame containing the data
            key_fields: Fields to use for key generation
            field_configs: Field normalization configurations
            use_normalized: Whether to use normalized columns
            
        Returns:
            List of composite key strings
        """
        composite_keys = []
        
        for idx, row in df.iterrows():
            key_parts = []
            
            for field in key_fields:
                if use_normalized:
                    normalized_field = f"{field}_normalized"
                    if normalized_field in row.index:
                        value = row[normalized_field]
                    else:
                        # Fall back to original field with on-the-fly normalization
                        original_value = row.get(field, "")
                        norm_type = field_configs.get(field, 'text_aggressive')
                        value = self._normalize_value(original_value, norm_type)
                else:
                    value = str(row.get(field, ""))
                
                key_parts.append(str(value))
            
            composite_key = " ".join(key_parts).strip()
            composite_keys.append(composite_key)
        
        return composite_keys
    
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
            return self.normalizer.normalize_text_aggressive(value)
    
    def _create_blocks(self, composite_keys: List[str], max_comparisons: int) -> Dict[str, List[int]]:
        """
        Create blocks to reduce the number of comparisons needed.
        
        Uses a simple blocking strategy based on first few characters
        and length to group potentially similar records.
        
        Args:
            composite_keys: List of composite key strings
            max_comparisons: Maximum number of comparisons allowed
            
        Returns:
            Dictionary mapping block IDs to lists of record indices
        """
        blocks = defaultdict(list)
        
        # Estimate total comparisons without blocking
        n = len(composite_keys)
        total_comparisons = n * (n - 1) // 2
        
        if total_comparisons <= max_comparisons:
            # No blocking needed
            blocks['all'] = list(range(n))
            logger.debug(f"No blocking needed: {total_comparisons} comparisons")
            return dict(blocks)
        
        # Apply blocking strategy
        logger.debug(f"Applying blocking strategy to reduce {total_comparisons} comparisons")
        
        for idx, key in enumerate(composite_keys):
            if not key.strip():
                continue
            
            # Create block ID based on:
            # 1. First 2 characters (or less if shorter)
            # 2. Length category
            prefix = key[:2].lower()
            length_category = len(key) // 10  # Group by length in buckets of 10
            
            block_id = f"{prefix}_{length_category}"
            blocks[block_id].append(idx)
        
        # Log blocking statistics
        block_sizes = [len(indices) for indices in blocks.values()]
        total_blocked_comparisons = sum(size * (size - 1) // 2 for size in block_sizes)
        
        logger.debug(f"Created {len(blocks)} blocks")
        logger.debug(f"Reduced comparisons from {total_comparisons} to {total_blocked_comparisons}")
        logger.debug(f"Average block size: {sum(block_sizes) / len(block_sizes):.1f}")
        
        return dict(blocks)
    
    def _find_duplicates_in_block(self, df: pd.DataFrame, block_indices: List[int],
                                composite_keys: List[str], similarity_func,
                                threshold: float, key_fields: List[str]) -> List[DuplicateGroup]:
        """
        Find duplicates within a single block.
        
        Args:
            df: DataFrame containing the data
            block_indices: Indices of records in this block
            composite_keys: List of composite keys
            similarity_func: Similarity function to use
            threshold: Similarity threshold
            key_fields: Fields used for matching
            
        Returns:
            List of DuplicateGroup objects for this block
        """
        if len(block_indices) < 2:
            return []
        
        # Find similar pairs within the block
        similar_pairs = []
        
        for i, idx1 in enumerate(block_indices):
            for idx2 in block_indices[i+1:]:
                key1 = composite_keys[idx1]
                key2 = composite_keys[idx2]
                
                if not key1.strip() or not key2.strip():
                    continue
                
                # Calculate similarity
                similarity = similarity_func(key1, key2)
                
                if similarity >= threshold:
                    similar_pairs.append((idx1, idx2, similarity))
        
        if not similar_pairs:
            return []
        
        # Group similar pairs into duplicate groups
        return self._group_similar_pairs(df, similar_pairs, key_fields)
    
    def _group_similar_pairs(self, df: pd.DataFrame, similar_pairs: List[Tuple[int, int, float]],
                           key_fields: List[str]) -> List[DuplicateGroup]:
        """
        Group similar pairs into duplicate groups using connected components.
        
        Args:
            df: DataFrame containing the data
            similar_pairs: List of (idx1, idx2, similarity) tuples
            key_fields: Fields used for matching
            
        Returns:
            List of DuplicateGroup objects
        """
        # Build a graph of similar records
        graph = defaultdict(set)
        similarities = {}
        
        for idx1, idx2, similarity in similar_pairs:
            graph[idx1].add(idx2)
            graph[idx2].add(idx1)
            similarities[(min(idx1, idx2), max(idx1, idx2))] = similarity
        
        # Find connected components (duplicate groups)
        visited = set()
        duplicate_groups = []
        group_counter = 1
        
        for start_idx in graph:
            if start_idx in visited:
                continue
            
            # BFS to find all connected records
            component = []
            queue = [start_idx]
            visited.add(start_idx)
            
            while queue:
                current = queue.pop(0)
                component.append(current)
                
                for neighbor in graph[current]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            
            if len(component) >= 2:
                # Create duplicate group
                records = []
                group_similarities = []
                
                for idx in component:
                    record = df.iloc[idx].to_dict()
                    record['_original_index'] = idx
                    records.append(record)
                
                # Calculate average similarity for the group
                for i, idx1 in enumerate(component):
                    for idx2 in component[i+1:]:
                        pair_key = (min(idx1, idx2), max(idx1, idx2))
                        if pair_key in similarities:
                            group_similarities.append(similarities[pair_key])
                
                avg_similarity = sum(group_similarities) / len(group_similarities) if group_similarities else 0
                
                group = DuplicateGroup(
                    group_id=f"fuzzy_group_{group_counter}",
                    records=records,
                    similarity_score=round(avg_similarity, 1),
                    detection_method='fuzzy',
                    recommended_action=self._recommend_action(records, key_fields)
                )
                
                duplicate_groups.append(group)
                group_counter += 1
        
        return duplicate_groups
    
    def _recommend_action(self, records: List[Dict[str, Any]], key_fields: List[str]) -> str:
        """
        Recommend an action for a fuzzy duplicate group.
        
        Args:
            records: List of duplicate records
            key_fields: Fields used for duplicate detection
            
        Returns:
            Recommended action string
        """
        if len(records) == 2:
            # For pairs, recommend manual review for fuzzy matches
            return 'flag'
        elif len(records) <= 3:
            # For small groups, recommend flagging for review
            return 'flag'
        else:
            # For large groups, definitely flag for manual review
            return 'flag'
    
    def get_duplicate_statistics(self, duplicate_groups: List[DuplicateGroup]) -> Dict[str, Any]:
        """
        Get statistics about the fuzzy duplicate detection results.
        
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
                'average_similarity': 0,
                'similarity_distribution': {}
            }
        
        total_records = sum(len(group.records) for group in duplicate_groups)
        group_sizes = [len(group.records) for group in duplicate_groups]
        similarities = [group.similarity_score for group in duplicate_groups]
        
        # Similarity distribution
        similarity_ranges = {
            '90-100%': len([s for s in similarities if 90 <= s <= 100]),
            '80-89%': len([s for s in similarities if 80 <= s < 90]),
            '70-79%': len([s for s in similarities if 70 <= s < 80]),
            '60-69%': len([s for s in similarities if 60 <= s < 70]),
            'Below 60%': len([s for s in similarities if s < 60])
        }
        
        stats = {
            'total_groups': len(duplicate_groups),
            'total_duplicate_records': total_records,
            'average_group_size': total_records / len(duplicate_groups),
            'largest_group_size': max(group_sizes),
            'smallest_group_size': min(group_sizes),
            'average_similarity': sum(similarities) / len(similarities),
            'highest_similarity': max(similarities),
            'lowest_similarity': min(similarities),
            'similarity_distribution': similarity_ranges
        }
        
        return stats


# Convenience functions
def find_fuzzy_duplicates_simple(df: pd.DataFrame, key_fields: List[str], 
                                threshold: float = 80.0) -> List[DuplicateGroup]:
    """
    Simple convenience function to find fuzzy duplicates.
    
    Args:
        df: Input DataFrame
        key_fields: List of field names to use for duplicate detection
        threshold: Similarity threshold (0-100)
        
    Returns:
        List of DuplicateGroup objects
    """
    matcher = FuzzyMatcher()
    return matcher.find_fuzzy_duplicates(df, key_fields, threshold)


def get_fuzzy_duplicate_summary(duplicate_groups: List[DuplicateGroup]) -> str:
    """
    Get a human-readable summary of fuzzy duplicate detection results.
    
    Args:
        duplicate_groups: List of duplicate groups
        
    Returns:
        Formatted summary string
    """
    if not duplicate_groups:
        return "No fuzzy duplicates found."
    
    matcher = FuzzyMatcher()
    stats = matcher.get_duplicate_statistics(duplicate_groups)
    
    summary = f"""Fuzzy Duplicate Detection Summary:
    • Found {stats['total_groups']} fuzzy duplicate groups
    • Total duplicate records: {stats['total_duplicate_records']}
    • Average group size: {stats['average_group_size']:.1f}
    • Average similarity: {stats['average_similarity']:.1f}%
    • Similarity range: {stats['lowest_similarity']:.1f}% - {stats['highest_similarity']:.1f}%
    
    Similarity Distribution:
    """
    
    for range_name, count in stats['similarity_distribution'].items():
        if count > 0:
            summary += f"    • {range_name}: {count} groups\n"
    
    return summary