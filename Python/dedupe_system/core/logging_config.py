"""
Logging configuration for the Intelligent Duplicate Detection & Cleanup System.

This module sets up structured logging for:
- System operations and debugging
- Error handling and troubleshooting
- Performance monitoring
- Audit trail generation

The logging system supports multiple output formats and destinations.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> logging.Logger:
    """
    Set up comprehensive logging for the duplicate detection system.
    
    Args:
        log_level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        log_dir: Directory to store log files
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('dedupe_system')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler for detailed system logs
    system_log_file = log_path / f"system_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        system_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Error handler for critical issues
    error_log_file = log_path / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.FileHandler(error_log_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    logger.info("Logging system initialized")
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f'dedupe_system.{name}')
    return logging.getLogger('dedupe_system')


class AuditLogger:
    """
    Specialized logger for audit trail generation.
    
    This logger creates structured audit entries for compliance
    and traceability requirements.
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create audit-specific logger
        self.logger = logging.getLogger('dedupe_system.audit')
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Audit log file with timestamp
        audit_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # JSON-like formatter for structured audit entries
        audit_formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
        )
        
        audit_handler = logging.FileHandler(audit_file)
        audit_handler.setFormatter(audit_formatter)
        self.logger.addHandler(audit_handler)
    
    def log_action(self, record_id: str, action: str, reason: str, 
                   similarity_score: float = None, user_decision: bool = False):
        """
        Log an audit entry for a duplicate resolution action.
        
        Args:
            record_id: Original record identifier
            action: Action taken ('KEPT', 'DELETED', 'MERGED', 'FLAGGED')
            reason: Reason for the action
            similarity_score: Similarity score if applicable
            user_decision: Whether this was a user decision
        """
        audit_data = {
            "record_id": record_id,
            "action": action,
            "reason": reason,
            "similarity_score": similarity_score,
            "user_decision": user_decision,
            "timestamp": datetime.now().isoformat()
        }
        
        # Log as JSON string
        self.logger.info(str(audit_data).replace("'", '"'))
    
    def log_processing_start(self, total_records: int, config: dict):
        """Log the start of a processing session."""
        session_data = {
            "event": "processing_start",
            "total_records": total_records,
            "config": config
        }
        self.logger.info(str(session_data).replace("'", '"'))
    
    def log_processing_end(self, stats: dict):
        """Log the end of a processing session with statistics."""
        session_data = {
            "event": "processing_end",
            "stats": stats
        }
        self.logger.info(str(session_data).replace("'", '"'))


class ActivityLogger:
    """
    Comprehensive activity logger for system operations.
    
    This logger maintains detailed logs of all system activities
    for debugging, monitoring, and compliance purposes.
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create activity-specific logger
        self.logger = logging.getLogger('dedupe_system.activity')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Activity log file with timestamp
        activity_file = self.log_dir / f"activity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Detailed formatter for activity entries
        activity_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        )
        
        activity_handler = logging.FileHandler(activity_file)
        activity_handler.setFormatter(activity_formatter)
        self.logger.addHandler(activity_handler)
        
        # Track session information
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.operation_counter = 0
    
    def log_file_operation(self, operation: str, file_path: str, 
                          success: bool, details: dict = None):
        """
        Log file operations (load, save, etc.).
        
        Args:
            operation: Type of operation ('load', 'save', 'validate')
            file_path: Path to the file
            success: Whether the operation succeeded
            details: Additional operation details
        """
        self.operation_counter += 1
        
        log_data = {
            'session_id': self.session_id,
            'operation_id': self.operation_counter,
            'operation': operation,
            'file_path': file_path,
            'success': success
        }
        
        if details:
            log_data.update(details)
        
        level = logging.INFO if success else logging.ERROR
        self.logger.log(level, f"File operation: {log_data}")
    
    def log_data_operation(self, operation: str, record_count: int, 
                          success: bool, duration: float = None, details: dict = None):
        """
        Log data processing operations.
        
        Args:
            operation: Type of operation ('normalize', 'match', 'resolve')
            record_count: Number of records processed
            success: Whether the operation succeeded
            duration: Operation duration in seconds
            details: Additional operation details
        """
        self.operation_counter += 1
        
        log_data = {
            'session_id': self.session_id,
            'operation_id': self.operation_counter,
            'operation': operation,
            'record_count': record_count,
            'success': success
        }
        
        if duration is not None:
            log_data['duration_seconds'] = round(duration, 3)
            log_data['records_per_second'] = round(record_count / max(duration, 0.001), 1)
        
        if details:
            log_data.update(details)
        
        level = logging.INFO if success else logging.ERROR
        self.logger.log(level, f"Data operation: {log_data}")
    
    def log_user_interaction(self, interaction_type: str, details: dict = None):
        """
        Log user interactions with the system.
        
        Args:
            interaction_type: Type of interaction ('config_change', 'decision', 'download')
            details: Interaction details
        """
        self.operation_counter += 1
        
        log_data = {
            'session_id': self.session_id,
            'operation_id': self.operation_counter,
            'interaction_type': interaction_type,
            'timestamp': datetime.now().isoformat()
        }
        
        if details:
            log_data.update(details)
        
        self.logger.info(f"User interaction: {log_data}")
    
    def log_system_event(self, event_type: str, message: str, details: dict = None):
        """
        Log system events and status changes.
        
        Args:
            event_type: Type of event ('startup', 'shutdown', 'error', 'warning')
            message: Event message
            details: Additional event details
        """
        self.operation_counter += 1
        
        log_data = {
            'session_id': self.session_id,
            'operation_id': self.operation_counter,
            'event_type': event_type,
            'message': message
        }
        
        if details:
            log_data.update(details)
        
        # Choose appropriate log level
        level_map = {
            'startup': logging.INFO,
            'shutdown': logging.INFO,
            'error': logging.ERROR,
            'warning': logging.WARNING,
            'info': logging.INFO,
            'debug': logging.DEBUG
        }
        level = level_map.get(event_type, logging.INFO)
        
        self.logger.log(level, f"System event: {log_data}")
    
    def log_performance_metrics(self, operation: str, metrics: dict):
        """
        Log performance metrics for operations.
        
        Args:
            operation: Operation name
            metrics: Dictionary of performance metrics
        """
        self.operation_counter += 1
        
        log_data = {
            'session_id': self.session_id,
            'operation_id': self.operation_counter,
            'operation': operation,
            'metrics': metrics
        }
        
        self.logger.info(f"Performance metrics: {log_data}")


def create_comprehensive_logger(log_level: str = "INFO", log_dir: str = "logs") -> tuple:
    """
    Create a comprehensive logging setup with all logger types.
    
    Args:
        log_level: Logging level for the main logger
        log_dir: Directory to store log files
        
    Returns:
        Tuple of (main_logger, audit_logger, activity_logger)
    """
    # Set up main system logger
    main_logger = setup_logging(log_level, log_dir)
    
    # Create specialized loggers
    audit_logger = AuditLogger(log_dir)
    activity_logger = ActivityLogger(log_dir)
    
    # Log the initialization
    activity_logger.log_system_event('startup', 'Comprehensive logging system initialized', {
        'log_level': log_level,
        'log_dir': log_dir
    })
    
    return main_logger, audit_logger, activity_logger