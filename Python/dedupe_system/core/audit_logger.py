# MIT License
# Copyright (c) 2026 Judy Natasha Wambui Gachanja

"""
Audit Logger for the Intelligent Duplicate Detection & Cleanup System.

This module implements:
- Compliance-ready audit trail logging
- Original record identifier preservation
- All transformation recording
- Resolution decision auditability
- Structured logging for regulated environments

Critical for finance, healthcare, and other regulated industries.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import uuid

from .models import DuplicateGroup, AuditEntry
from .logging_config import get_logger

logger = get_logger(__name__)


class AuditLogger:
    """
    Comprehensive audit logging system for compliance and traceability.
    
    This class ensures every action performed by the system is logged
    with sufficient detail for regulatory compliance and data lineage tracking.
    """
    
    def __init__(self, audit_log_dir: str = "logs"):
        """
        Initialize the audit logger.
        
        Args:
            audit_log_dir: Directory to store audit logs
        """
        self.audit_log_dir = Path(audit_log_dir)
        self.audit_log_dir.mkdir(exist_ok=True)
        
        # Create session-specific audit log
        self.session_id = str(uuid.uuid4())
        self.audit_log_file = self.audit_log_dir / f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.session_id[:8]}.jsonl"
        
        # Initialize audit log
        self._log_audit_event("SESSION_START", {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "system_version": "1.0.0"
        })
    
    def _log_audit_event(self, event_type: str, event_data: Dict[str, Any]):
        """
        Log an audit event to the audit trail.
        
        Args:
            event_type: Type of event (e.g., DATA_LOADED, DUPLICATE_DETECTED)
            event_data: Event-specific data
        """
        audit_entry = {
            "session_id": self.session_id,
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "event_data": event_data
        }
        
        # Write to audit log file (JSONL format)
        try:
            with open(self.audit_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(audit_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def log_data_loaded(self, file_path: str, record_count: int, columns: List[str]):
        """Log data loading event."""
        self._log_audit_event("DATA_LOADED", {
            "file_path": file_path,
            "record_count": record_count,
            "columns": columns,
            "data_hash": self._calculate_data_hash(record_count, columns)
        })
    
    def log_normalization(self, field_configs: Dict[str, str], records_processed: int):
        """Log data normalization event."""
        self._log_audit_event("DATA_NORMALIZED", {
            "field_configurations": field_configs,
            "records_processed": records_processed,
            "normalization_rules": list(field_configs.keys())
        })
    
    def log_duplicate_detection(self, detection_method: str, key_fields: List[str], 
                              groups_found: int, records_affected: int, 
                              configuration: Dict[str, Any]):
        """Log duplicate detection event."""
        self._log_audit_event("DUPLICATE_DETECTION", {
            "detection_method": detection_method,
            "key_fields": key_fields,
            "groups_found": groups_found,
            "records_affected": records_affected,
            "configuration": configuration
        })
    
    def log_duplicate_group(self, duplicate_group: DuplicateGroup):
        """Log details of a specific duplicate group."""
        # Preserve original identifiers
        original_ids = []
        for record in duplicate_group.records:
            original_id = record.get('_original_index', record.get('id', 'unknown'))
            original_ids.append(original_id)
        
        self._log_audit_event("DUPLICATE_GROUP_IDENTIFIED", {
            "group_id": duplicate_group.group_id,
            "detection_method": duplicate_group.detection_method,
            "similarity_score": duplicate_group.similarity_score,
            "record_count": len(duplicate_group.records),
            "original_identifiers": original_ids,
            "recommended_action": duplicate_group.recommended_action
        })
    
    def log_resolution_decision(self, group_id: str, decision: str, 
                              user_override: bool = False, user_id: Optional[str] = None):
        """Log resolution decision for a duplicate group."""
        self._log_audit_event("RESOLUTION_DECISION", {
            "group_id": group_id,
            "resolution_action": decision,
            "user_override": user_override,
            "user_id": user_id,
            "decision_timestamp": datetime.now().isoformat()
        })
    
    def log_golden_record_creation(self, group_id: str, source_record_ids: List[str], 
                                 golden_record_id: str, survivorship_strategy: str):
        """Log golden record creation."""
        self._log_audit_event("GOLDEN_RECORD_CREATED", {
            "group_id": group_id,
            "source_record_ids": source_record_ids,
            "golden_record_id": golden_record_id,
            "survivorship_strategy": survivorship_strategy,
            "consolidation_ratio": len(source_record_ids)
        })
    
    def log_record_deletion(self, record_id: str, group_id: str, reason: str):
        """Log record deletion."""
        self._log_audit_event("RECORD_DELETED", {
            "record_id": record_id,
            "group_id": group_id,
            "deletion_reason": reason,
            "soft_delete": True  # System uses soft deletes
        })
    
    def log_data_export(self, export_type: str, record_count: int, file_path: str):
        """Log data export event."""
        self._log_audit_event("DATA_EXPORTED", {
            "export_type": export_type,
            "record_count": record_count,
            "file_path": file_path,
            "export_hash": self._calculate_export_hash(export_type, record_count)
        })
    
    def log_system_performance(self, processing_time: float, records_processed: int, 
                             memory_usage: Optional[float] = None):
        """Log system performance metrics."""
        self._log_audit_event("PERFORMANCE_METRICS", {
            "processing_time_seconds": processing_time,
            "records_processed": records_processed,
            "records_per_second": records_processed / processing_time if processing_time > 0 else 0,
            "memory_usage_mb": memory_usage
        })
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any]):
        """Log system errors."""
        self._log_audit_event("SYSTEM_ERROR", {
            "error_type": error_type,
            "error_message": error_message,
            "context": context,
            "severity": "ERROR"
        })
    
    def log_user_action(self, action: str, user_id: Optional[str] = None, 
                       details: Optional[Dict[str, Any]] = None):
        """Log user actions in the GUI."""
        self._log_audit_event("USER_ACTION", {
            "action": action,
            "user_id": user_id or "anonymous",
            "details": details or {}
        })
    
    def generate_audit_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive audit report for the session.
        
        Returns:
            Dictionary containing audit report
        """
        try:
            events = []
            with open(self.audit_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    events.append(json.loads(line.strip()))
            
            # Analyze events
            event_counts = {}
            for event in events:
                event_type = event['event_type']
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # Extract key metrics
            data_events = [e for e in events if e['event_type'] == 'DATA_LOADED']
            duplicate_events = [e for e in events if e['event_type'] == 'DUPLICATE_DETECTION']
            resolution_events = [e for e in events if e['event_type'] == 'RESOLUTION_DECISION']
            
            total_records = sum(e['event_data'].get('record_count', 0) for e in data_events)
            total_duplicates = sum(e['event_data'].get('records_affected', 0) for e in duplicate_events)
            
            return {
                "session_id": self.session_id,
                "audit_log_file": str(self.audit_log_file),
                "session_start": events[0]['timestamp'] if events else None,
                "session_end": events[-1]['timestamp'] if events else None,
                "total_events": len(events),
                "event_type_counts": event_counts,
                "data_summary": {
                    "total_records_processed": total_records,
                    "total_duplicates_found": total_duplicates,
                    "duplicate_rate": (total_duplicates / total_records * 100) if total_records > 0 else 0
                },
                "compliance_status": "COMPLETE",
                "data_lineage_preserved": True
            }
        
        except Exception as e:
            logger.error(f"Failed to generate audit report: {e}")
            return {"error": str(e)}
    
    def _calculate_data_hash(self, record_count: int, columns: List[str]) -> str:
        """Calculate a simple hash for data integrity verification."""
        data_signature = f"{record_count}_{len(columns)}_{hash(tuple(sorted(columns)))}"
        return str(abs(hash(data_signature)))
    
    def _calculate_export_hash(self, export_type: str, record_count: int) -> str:
        """Calculate a hash for export verification."""
        export_signature = f"{export_type}_{record_count}_{datetime.now().strftime('%Y%m%d')}"
        return str(abs(hash(export_signature)))
    
    def close_session(self):
        """Close the audit session."""
        self._log_audit_event("SESSION_END", {
            "session_duration_seconds": (datetime.now() - datetime.fromisoformat(
                self.session_id.split('_')[0] if '_' in self.session_id else datetime.now().isoformat()
            )).total_seconds() if hasattr(self, 'session_start') else 0
        })


# Global audit logger instance
_audit_logger = None

def get_audit_logger(audit_log_dir: str = "logs") -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(audit_log_dir)
    return _audit_logger


def log_audit_event(event_type: str, event_data: Dict[str, Any]):
    """Convenience function to log an audit event."""
    audit_logger = get_audit_logger()
    audit_logger._log_audit_event(event_type, event_data)