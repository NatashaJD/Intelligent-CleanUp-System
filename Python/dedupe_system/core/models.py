"""
Core data models for the Intelligent Duplicate Detection & Cleanup System.

This module defines all the data structures used throughout the system:
- DuplicateGroup: Represents a group of duplicate records
- ResolutionDecision: User's decision for resolving duplicates
- AuditEntry: Single entry in the audit log
- ValidationResult: Result of data validation
- ProcessingStats: Statistics from duplicate detection
- Configuration models for matching and resolution
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class DuplicateGroup:
    """
    Represents a group of duplicate records detected by the system.
    
    Attributes:
        group_id: Unique identifier for this duplicate group
        records: List of duplicate records (as dictionaries)
        similarity_score: Similarity score (0-100, where 100 = exact match)
        detection_method: How duplicates were found ('exact' or 'fuzzy')
        recommended_action: System's recommended action ('keep_first', 'merge', 'flag')
    """
    group_id: str
    records: List[Dict[str, Any]]
    similarity_score: float
    detection_method: str  # 'exact' or 'fuzzy'
    recommended_action: str  # 'keep_first', 'merge', 'flag'


@dataclass
class ResolutionDecision:
    """
    User's decision for resolving a duplicate group.
    
    Attributes:
        group_id: ID of the duplicate group being resolved
        action: User's chosen action ('KEEP', 'DELETE', 'MERGE', 'FLAG')
        selected_records: Record IDs to keep/merge (empty for FLAG)
        user_notes: Optional notes from the user
        timestamp: When the decision was made
    """
    group_id: str
    action: str  # 'KEEP', 'DELETE', 'MERGE', 'FLAG'
    selected_records: List[int]  # Record IDs to keep/merge
    user_notes: Optional[str]
    timestamp: datetime


@dataclass
class AuditEntry:
    """
    Single entry in the audit log for compliance and traceability.
    
    Attributes:
        record_id: Original record identifier
        action: Action taken ('KEPT', 'DELETED', 'MERGED', 'FLAGGED')
        reason: Reason for the action ('exact_duplicate', 'fuzzy_match', etc.)
        similarity_score: Similarity score if applicable
        timestamp: When the action was performed
        user_decision: True if user-approved, False if automatic
    """
    record_id: str
    action: str
    reason: str
    similarity_score: Optional[float]
    timestamp: datetime
    user_decision: bool  # True if user-approved, False if automatic


@dataclass
class ValidationResult:
    """
    Result of data validation for input files.
    
    Attributes:
        is_valid: Whether the data passed validation
        errors: List of error messages (blocking issues)
        warnings: List of warning messages (non-blocking issues)
        record_count: Number of records in the dataset
        field_names: List of field/column names
    """
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    record_count: int
    field_names: List[str]


@dataclass
class ProcessingStats:
    """
    Statistics from the duplicate detection process.
    
    Attributes:
        total_records: Total number of input records
        duplicate_groups_found: Number of duplicate groups detected
        exact_duplicates: Number of exact duplicate groups
        fuzzy_duplicates: Number of fuzzy duplicate groups
        processing_time: Total processing time in seconds
        memory_usage: Peak memory usage in MB
    """
    total_records: int
    duplicate_groups_found: int
    exact_duplicates: int
    fuzzy_duplicates: int
    processing_time: float
    memory_usage: float


@dataclass
class MatchingConfig:
    """
    Configuration for duplicate detection algorithms.
    
    Attributes:
        exact_matching_enabled: Whether to perform exact matching
        fuzzy_matching_enabled: Whether to perform fuzzy matching
        fuzzy_threshold: Similarity threshold for fuzzy matching (0-100)
        key_fields: Fields to use for exact matching
        fuzzy_fields: Fields to use for fuzzy matching
        similarity_algorithm: Algorithm for fuzzy matching ('levenshtein', 'jaro_winkler', etc.)
    """
    exact_matching_enabled: bool
    fuzzy_matching_enabled: bool
    fuzzy_threshold: float  # 0-100
    key_fields: List[str]
    fuzzy_fields: List[str]
    similarity_algorithm: str  # 'levenshtein', 'jaro_winkler', etc.


@dataclass
class ResolutionConfig:
    """
    Configuration for duplicate resolution behavior.
    
    Attributes:
        default_action: Default action for duplicate groups ('merge', 'flag', 'manual')
        require_confirmation_for_hard_delete: Whether hard deletes need confirmation
        merge_strategy: Strategy for merging records ('most_complete', 'latest_timestamp', 'manual')
        preserve_original_ids: Whether to preserve original record IDs in audit trail
    """
    default_action: str
    require_confirmation_for_hard_delete: bool
    merge_strategy: str  # 'most_complete', 'latest_timestamp', 'manual'
    preserve_original_ids: bool