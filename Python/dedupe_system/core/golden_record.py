# MIT License
# Copyright (c) 2026 Judy Natasha Wambui Gachanja

"""
Golden Record Creator for the Intelligent Duplicate Detection & Cleanup System.

This module implements:
- Survivorship rules for field-level conflict resolution
- Most recent value selection based on timestamps
- Highest completeness score calculation
- Consolidated record creation from duplicate groups
- Data quality preservation during merging

The golden record creator ensures maximum data quality post-cleanup.
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .models import DuplicateGroup
from .logging_config import get_logger

logger = get_logger(__name__)


class GoldenRecordCreator:
    """
    Creates consolidated 'golden records' from duplicate groups using survivorship rules.
    
    This class implements intelligent merging strategies to create the best possible
    record from a group of duplicates, maximizing data quality and completeness.
    """
    
    def __init__(self):
        """Initialize the Golden Record Creator."""
        self.survivorship_rules = {
            'most_recent': self._select_most_recent,
            'most_complete': self._select_most_complete,
            'longest_value': self._select_longest_value,
            'most_frequent': self._select_most_frequent,
            'first_non_null': self._select_first_non_null
        }
    
    def create_golden_record(self, duplicate_group: DuplicateGroup, 
                           timestamp_field: Optional[str] = None,
                           survivorship_strategy: str = 'most_complete') -> Dict[str, Any]:
        """
        Create a golden record from a duplicate group.
        
        Args:
            duplicate_group: Group of duplicate records
            timestamp_field: Field to use for recency-based survivorship
            survivorship_strategy: Strategy for field-level conflict resolution
            
        Returns:
            Dictionary representing the golden record
        """
        if not duplicate_group.records:
            raise ValueError("Cannot create golden record from empty group")
        
        if len(duplicate_group.records) == 1:
            return duplicate_group.records[0].copy()
        
        logger.info(f"Creating golden record from {len(duplicate_group.records)} duplicates")
        
        # Get all field names
        all_fields = set()
        for record in duplicate_group.records:
            all_fields.update(record.keys())
        
        golden_record = {}
        field_sources = {}  # Track which record each field came from
        
        # Apply survivorship rules for each field
        for field in all_fields:
            if field.startswith('_'):  # Skip internal fields
                continue
                
            field_values = []
            for i, record in enumerate(duplicate_group.records):
                if field in record and record[field] is not None and str(record[field]).strip():
                    field_values.append({
                        'value': record[field],
                        'record_index': i,
                        'record': record,
                        'completeness': self._calculate_completeness(record)
                    })
            
            if field_values:
                # Apply survivorship rule
                if survivorship_strategy in self.survivorship_rules:
                    selected = self.survivorship_rules[survivorship_strategy](
                        field_values, field, timestamp_field
                    )
                else:
                    selected = self._select_most_complete(field_values, field, timestamp_field)
                
                golden_record[field] = selected['value']
                field_sources[field] = selected['record_index']
            else:
                golden_record[field] = None
                field_sources[field] = -1
        
        # Add metadata
        golden_record['_golden_record'] = True
        golden_record['_source_count'] = len(duplicate_group.records)
        golden_record['_field_sources'] = field_sources
        golden_record['_created_timestamp'] = datetime.now().isoformat()
        golden_record['_group_id'] = duplicate_group.group_id
        
        logger.info(f"Golden record created with {len([f for f in golden_record if not f.startswith('_')])} fields")
        
        return golden_record
    
    def _calculate_completeness(self, record: Dict[str, Any]) -> float:
        """Calculate the completeness score of a record."""
        total_fields = len([f for f in record.keys() if not f.startswith('_')])
        if total_fields == 0:
            return 0.0
        
        non_empty_fields = len([
            f for f in record.keys() 
            if not f.startswith('_') and record[f] is not None and str(record[f]).strip()
        ])
        
        return non_empty_fields / total_fields
    
    def _select_most_recent(self, field_values: List[Dict], field: str, 
                          timestamp_field: Optional[str]) -> Dict:
        """Select the value from the most recent record."""
        if not timestamp_field:
            return self._select_most_complete(field_values, field, timestamp_field)
        
        # Sort by timestamp (most recent first)
        try:
            sorted_values = sorted(
                field_values,
                key=lambda x: pd.to_datetime(x['record'].get(timestamp_field, '1900-01-01')),
                reverse=True
            )
            return sorted_values[0]
        except:
            # Fall back to most complete if timestamp parsing fails
            return self._select_most_complete(field_values, field, timestamp_field)
    
    def _select_most_complete(self, field_values: List[Dict], field: str, 
                            timestamp_field: Optional[str]) -> Dict:
        """Select the value from the record with highest completeness."""
        return max(field_values, key=lambda x: x['completeness'])
    
    def _select_longest_value(self, field_values: List[Dict], field: str, 
                            timestamp_field: Optional[str]) -> Dict:
        """Select the longest non-null value."""
        return max(field_values, key=lambda x: len(str(x['value'])))
    
    def _select_most_frequent(self, field_values: List[Dict], field: str, 
                            timestamp_field: Optional[str]) -> Dict:
        """Select the most frequently occurring value."""
        value_counts = {}
        for fv in field_values:
            val = str(fv['value'])
            if val not in value_counts:
                value_counts[val] = []
            value_counts[val].append(fv)
        
        # Return the most frequent value (first occurrence if tie)
        most_frequent_val = max(value_counts.keys(), key=lambda x: len(value_counts[x]))
        return value_counts[most_frequent_val][0]
    
    def _select_first_non_null(self, field_values: List[Dict], field: str, 
                             timestamp_field: Optional[str]) -> Dict:
        """Select the first non-null value."""
        return field_values[0]
    
    def create_golden_records_batch(self, duplicate_groups: List[DuplicateGroup],
                                  timestamp_field: Optional[str] = None,
                                  survivorship_strategy: str = 'most_complete') -> List[Dict[str, Any]]:
        """
        Create golden records for multiple duplicate groups.
        
        Args:
            duplicate_groups: List of duplicate groups
            timestamp_field: Field to use for recency-based survivorship
            survivorship_strategy: Strategy for field-level conflict resolution
            
        Returns:
            List of golden records
        """
        golden_records = []
        
        for group in duplicate_groups:
            try:
                golden_record = self.create_golden_record(
                    group, timestamp_field, survivorship_strategy
                )
                golden_records.append(golden_record)
            except Exception as e:
                logger.error(f"Failed to create golden record for group {group.group_id}: {e}")
                # Fall back to first record in group
                if group.records:
                    fallback_record = group.records[0].copy()
                    fallback_record['_golden_record_error'] = str(e)
                    golden_records.append(fallback_record)
        
        logger.info(f"Created {len(golden_records)} golden records from {len(duplicate_groups)} groups")
        return golden_records
    
    def get_survivorship_statistics(self, golden_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about the golden record creation process.
        
        Args:
            golden_records: List of created golden records
            
        Returns:
            Dictionary containing statistics
        """
        if not golden_records:
            return {}
        
        total_records = len(golden_records)
        total_source_records = sum(
            record.get('_source_count', 1) for record in golden_records
        )
        
        # Field source distribution
        field_sources = {}
        for record in golden_records:
            sources = record.get('_field_sources', {})
            for field, source_idx in sources.items():
                if field not in field_sources:
                    field_sources[field] = {}
                if source_idx not in field_sources[field]:
                    field_sources[field][source_idx] = 0
                field_sources[field][source_idx] += 1
        
        # Completeness statistics
        completeness_scores = []
        for record in golden_records:
            completeness = self._calculate_completeness(record)
            completeness_scores.append(completeness)
        
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        
        return {
            'total_golden_records': total_records,
            'total_source_records': total_source_records,
            'consolidation_ratio': total_source_records / total_records if total_records > 0 else 0,
            'average_completeness': avg_completeness,
            'min_completeness': min(completeness_scores) if completeness_scores else 0,
            'max_completeness': max(completeness_scores) if completeness_scores else 0,
            'field_source_distribution': field_sources
        }


# Convenience functions
def create_golden_record_simple(duplicate_group: DuplicateGroup) -> Dict[str, Any]:
    """
    Simple convenience function to create a golden record.
    
    Args:
        duplicate_group: Group of duplicate records
        
    Returns:
        Golden record dictionary
    """
    creator = GoldenRecordCreator()
    return creator.create_golden_record(duplicate_group)


def merge_duplicate_groups(duplicate_groups: List[DuplicateGroup], 
                         timestamp_field: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Merge all duplicate groups into golden records.
    
    Args:
        duplicate_groups: List of duplicate groups
        timestamp_field: Optional timestamp field for recency-based merging
        
    Returns:
        List of golden records
    """
    creator = GoldenRecordCreator()
    return creator.create_golden_records_batch(duplicate_groups, timestamp_field)