"""
Custom exceptions for the Intelligent Duplicate Detection & Cleanup System.

This module defines specific exception types for different error scenarios:
- File processing errors
- Data validation errors
- Configuration errors
- Processing errors

Each exception provides detailed context for debugging and user feedback.
"""


class DedupeSystemError(Exception):
    """Base exception for all duplicate detection system errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class FileProcessingError(DedupeSystemError):
    """Raised when file loading or parsing fails."""
    
    def __init__(self, message: str, file_path: str = None, line_number: int = None):
        details = {}
        if file_path:
            details['file_path'] = file_path
        if line_number:
            details['line_number'] = line_number
        
        super().__init__(message, details)
        self.file_path = file_path
        self.line_number = line_number


class DataValidationError(DedupeSystemError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field_name: str = None, invalid_value: str = None):
        details = {}
        if field_name:
            details['field_name'] = field_name
        if invalid_value:
            details['invalid_value'] = str(invalid_value)
        
        super().__init__(message, details)
        self.field_name = field_name
        self.invalid_value = invalid_value


class ConfigurationError(DedupeSystemError):
    """Raised when system configuration is invalid."""
    
    def __init__(self, message: str, config_key: str = None, config_value: str = None):
        details = {}
        if config_key:
            details['config_key'] = config_key
        if config_value:
            details['config_value'] = str(config_value)
        
        super().__init__(message, details)
        self.config_key = config_key
        self.config_value = config_value


class ProcessingError(DedupeSystemError):
    """Raised when duplicate detection or resolution processing fails."""
    
    def __init__(self, message: str, operation: str = None, record_count: int = None):
        details = {}
        if operation:
            details['operation'] = operation
        if record_count:
            details['record_count'] = record_count
        
        super().__init__(message, details)
        self.operation = operation
        self.record_count = record_count


class MemoryError(DedupeSystemError):
    """Raised when system runs out of memory during processing."""
    
    def __init__(self, message: str, memory_usage: float = None, record_count: int = None):
        details = {}
        if memory_usage:
            details['memory_usage_mb'] = memory_usage
        if record_count:
            details['record_count'] = record_count
        
        super().__init__(message, details)
        self.memory_usage = memory_usage
        self.record_count = record_count


class ResolutionError(DedupeSystemError):
    """Raised when duplicate resolution fails."""
    
    def __init__(self, message: str, group_id: str = None, action: str = None):
        details = {}
        if group_id:
            details['group_id'] = group_id
        if action:
            details['action'] = action
        
        super().__init__(message, details)
        self.group_id = group_id
        self.action = action


def handle_error(logger, error: Exception, context: str = None) -> str:
    """
    Handle and log errors with appropriate detail level.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Additional context about where the error occurred
        
    Returns:
        User-friendly error message
    """
    if isinstance(error, DedupeSystemError):
        # Our custom errors have detailed information
        logger.error(f"System error in {context}: {error}")
        return f"Error: {error.message}"
    
    elif isinstance(error, FileNotFoundError):
        logger.error(f"File not found in {context}: {error}")
        return f"File not found: {error.filename}"
    
    elif isinstance(error, PermissionError):
        logger.error(f"Permission error in {context}: {error}")
        return f"Permission denied: {error.filename}"
    
    elif isinstance(error, ValueError):
        logger.error(f"Value error in {context}: {error}")
        return f"Invalid value: {str(error)}"
    
    elif isinstance(error, KeyError):
        logger.error(f"Key error in {context}: {error}")
        return f"Missing required field: {str(error)}"
    
    else:
        # Unexpected errors
        logger.exception(f"Unexpected error in {context}: {error}")
        return f"An unexpected error occurred. Please check the logs for details."


class ErrorHandler:
    """
    Comprehensive error handling system for the duplicate detection system.
    
    This class provides centralized error handling with specific error messages,
    detailed logging, configuration validation, and graceful degradation.
    """
    
    def __init__(self, logger):
        self.logger = logger
        self.error_counts = {}
        self.warning_counts = {}
    
    def handle_file_parsing_error(self, file_path: str, error: Exception, 
                                line_number: int = None) -> str:
        """
        Handle file parsing errors with specific error messages.
        
        Args:
            file_path: Path to the file that failed to parse
            error: The parsing error that occurred
            line_number: Line number where error occurred (if known)
            
        Returns:
            User-friendly error message
        """
        error_key = f"file_parsing_{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        if isinstance(error, pd.errors.EmptyDataError):
            message = f"File '{file_path}' is empty or contains no data"
            self.logger.error(f"Empty file error: {file_path}")
            
        elif isinstance(error, pd.errors.ParserError):
            if line_number:
                message = f"File '{file_path}' has parsing error at line {line_number}: {str(error)}"
            else:
                message = f"File '{file_path}' has parsing error: {str(error)}"
            self.logger.error(f"Parser error in {file_path}: {error}")
            
        elif isinstance(error, UnicodeDecodeError):
            message = f"File '{file_path}' has encoding issues. Try saving as UTF-8 format."
            self.logger.error(f"Encoding error in {file_path}: {error}")
            
        elif isinstance(error, json.JSONDecodeError):
            message = f"File '{file_path}' is not valid JSON. Error at line {error.lineno}, column {error.colno}: {error.msg}"
            self.logger.error(f"JSON decode error in {file_path}: {error}")
            
        elif isinstance(error, FileNotFoundError):
            message = f"File '{file_path}' not found. Please check the file path."
            self.logger.error(f"File not found: {file_path}")
            
        elif isinstance(error, PermissionError):
            message = f"Permission denied accessing file '{file_path}'. Check file permissions."
            self.logger.error(f"Permission error for {file_path}: {error}")
            
        else:
            message = f"Failed to parse file '{file_path}': {str(error)}"
            self.logger.error(f"Unexpected parsing error in {file_path}: {error}")
        
        return message
    
    def handle_processing_error(self, operation: str, error: Exception, 
                              record_count: int = None, details: dict = None) -> str:
        """
        Handle processing errors with detailed logging.
        
        Args:
            operation: The operation that failed
            error: The processing error that occurred
            record_count: Number of records being processed
            details: Additional error details
            
        Returns:
            User-friendly error message
        """
        error_key = f"processing_{operation}_{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Log detailed information for debugging
        log_details = {
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'record_count': record_count
        }
        if details:
            log_details.update(details)
        
        self.logger.error(f"Processing error in {operation}: {log_details}")
        
        # Provide user-friendly messages based on error type
        if isinstance(error, MemoryError):
            message = f"Out of memory during {operation}. Try processing smaller batches or reducing data size."
            
        elif isinstance(error, KeyError):
            missing_field = str(error).strip("'\"")
            message = f"Missing required field '{missing_field}' during {operation}. Please check your data format."
            
        elif isinstance(error, ValueError):
            message = f"Invalid data encountered during {operation}: {str(error)}"
            
        elif isinstance(error, TypeError):
            message = f"Data type error during {operation}: {str(error)}"
            
        else:
            message = f"Processing failed during {operation}: {str(error)}"
        
        return message
    
    def validate_configuration(self, config: dict) -> tuple[bool, list[str]]:
        """
        Validate system configuration with explanatory messages.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []
        
        # Validate matching configuration
        if 'matching' in config:
            matching_config = config['matching']
            
            # Check matching mode
            if 'mode' not in matching_config:
                errors.append("Matching mode is required. Please specify 'exact', 'fuzzy', or 'both'.")
            elif matching_config['mode'] not in ['exact', 'fuzzy', 'both']:
                errors.append(f"Invalid matching mode '{matching_config['mode']}'. Must be 'exact', 'fuzzy', or 'both'.")
            
            # Check field selection
            if 'fields' not in matching_config or not matching_config['fields']:
                errors.append("At least one field must be selected for matching.")
            elif not isinstance(matching_config['fields'], list):
                errors.append("Matching fields must be provided as a list.")
            
            # Check fuzzy threshold if fuzzy matching is enabled
            if matching_config.get('mode') in ['fuzzy', 'both']:
                threshold = matching_config.get('fuzzy_threshold')
                if threshold is None:
                    errors.append("Fuzzy threshold is required when fuzzy matching is enabled.")
                elif not isinstance(threshold, (int, float)) or not (0 <= threshold <= 100):
                    errors.append("Fuzzy threshold must be a number between 0 and 100.")
        
        # Validate resolution configuration
        if 'resolution' in config:
            resolution_config = config['resolution']
            
            # Check default action
            if 'default_action' in resolution_config:
                valid_actions = ['KEEP', 'DELETE', 'MERGE', 'FLAG']
                if resolution_config['default_action'] not in valid_actions:
                    errors.append(f"Invalid default action '{resolution_config['default_action']}'. Must be one of: {valid_actions}")
            
            # Check merge strategy
            if 'merge_strategy' in resolution_config:
                valid_strategies = ['most_complete', 'most_recent', 'first_record']
                if resolution_config['merge_strategy'] not in valid_strategies:
                    errors.append(f"Invalid merge strategy '{resolution_config['merge_strategy']}'. Must be one of: {valid_strategies}")
        
        # Validate performance settings
        if 'performance' in config:
            perf_config = config['performance']
            
            # Check memory limit
            if 'memory_limit_mb' in perf_config:
                memory_limit = perf_config['memory_limit_mb']
                if not isinstance(memory_limit, (int, float)) or memory_limit <= 0:
                    errors.append("Memory limit must be a positive number.")
            
            # Check batch size
            if 'batch_size' in perf_config:
                batch_size = perf_config['batch_size']
                if not isinstance(batch_size, int) or batch_size <= 0:
                    errors.append("Batch size must be a positive integer.")
        
        # Log validation results
        if errors:
            self.logger.warning(f"Configuration validation failed: {errors}")
        else:
            self.logger.info("Configuration validation passed")
        
        return len(errors) == 0, errors
    
    def handle_system_limits(self, limit_type: str, current_value: float, 
                           limit_value: float, suggested_action: str = None) -> str:
        """
        Handle system limit scenarios with graceful degradation.
        
        Args:
            limit_type: Type of limit exceeded ('memory', 'time', 'records')
            current_value: Current value that exceeded the limit
            limit_value: The limit that was exceeded
            suggested_action: Suggested action to resolve the issue
            
        Returns:
            User-friendly message with suggested resolution
        """
        warning_key = f"system_limit_{limit_type}"
        self.warning_counts[warning_key] = self.warning_counts.get(warning_key, 0) + 1
        
        # Log the limit warning
        self.logger.warning(f"System limit exceeded - {limit_type}: {current_value} > {limit_value}")
        
        if limit_type == 'memory':
            message = f"Memory usage ({current_value:.1f} MB) exceeded limit ({limit_value:.1f} MB). "
            if suggested_action:
                message += suggested_action
            else:
                message += "Consider processing smaller batches or reducing data size."
                
        elif limit_type == 'time':
            message = f"Processing time ({current_value:.1f} seconds) exceeded limit ({limit_value:.1f} seconds). "
            if suggested_action:
                message += suggested_action
            else:
                message += "Consider using exact matching only or reducing data size."
                
        elif limit_type == 'records':
            message = f"Record count ({int(current_value)}) exceeded limit ({int(limit_value)}). "
            if suggested_action:
                message += suggested_action
            else:
                message += "Consider processing data in smaller chunks."
                
        else:
            message = f"System limit exceeded for {limit_type}: {current_value} > {limit_value}. "
            if suggested_action:
                message += suggested_action
        
        return message
    
    def get_error_summary(self) -> dict:
        """
        Get a summary of all errors and warnings encountered.
        
        Returns:
            Dictionary with error and warning counts
        """
        return {
            'errors': dict(self.error_counts),
            'warnings': dict(self.warning_counts),
            'total_errors': sum(self.error_counts.values()),
            'total_warnings': sum(self.warning_counts.values())
        }
    
    def reset_counters(self):
        """Reset error and warning counters."""
        self.error_counts.clear()
        self.warning_counts.clear()


# Import pandas and json for error handling
import pandas as pd
import json