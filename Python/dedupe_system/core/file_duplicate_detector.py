# MIT License
# Copyright (c) 2026 Judy Natasha Wambui Gachanja

"""
File-Level Duplicate Detection Module.

This module implements:
- File scanning across directories
- Size-based grouping for optimization
- Hash-based duplicate detection (SHA-256)
- Intelligent cleanup strategies
- Recycle bin operations

Algorithms from documentation:
- Algorithm 1: File Scanning - O(n)
- Algorithm 2: Group Files by Size - O(n)
- Algorithm 3: Hash-Based Duplicate Detection
- Algorithm 4: Intelligent Cleanup Strategy
"""

import hashlib
import os
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import shutil

from .logging_config import get_logger
from .exceptions import FileProcessingError

logger = get_logger(__name__)


@dataclass
class FileInfo:
    """Information about a file."""
    path: Path
    size: int
    modified_time: datetime
    hash: Optional[str] = None


@dataclass
class DuplicateFileGroup:
    """Group of duplicate files."""
    files: List[FileInfo]
    total_size: int
    hash: str
    best_file: Optional[FileInfo] = None


class FileDuplicateDetector:
    """
    Detects duplicate files using hash-based comparison.
    
    Implements the algorithms from the project documentation:
    - File scanning with O(n) complexity
    - Size-based grouping for optimization
    - SHA-256 hashing for exact duplicate detection
    """
    
    def __init__(self, chunk_size: int = 8192):
        """
        Initialize the file duplicate detector.
        
        Args:
            chunk_size: Size of chunks for reading files (default: 8KB)
        """
        self.chunk_size = chunk_size
        self.recycle_bin_path = Path("recycle_bin")
        self.archive_path = Path("archive")
    
    def scan_files(self, root_directory: str, extensions: Optional[List[str]] = None) -> List[FileInfo]:
        """
        Algorithm 1: File Scanning
        
        Recursively scan directory and collect file information.
        Time Complexity: O(n) where n is number of files
        
        Args:
            root_directory: Root directory to scan
            extensions: Optional list of file extensions to include (e.g., ['.txt', '.pdf'])
            
        Returns:
            List of FileInfo objects
        """
        logger.info(f"Scanning files in: {root_directory}")
        
        root_path = Path(root_directory)
        if not root_path.exists():
            raise FileProcessingError(f"Directory does not exist: {root_directory}")
        
        if not root_path.is_dir():
            raise FileProcessingError(f"Path is not a directory: {root_directory}")
        
        files = []
        
        try:
            for file_path in root_path.rglob('*'):
                if file_path.is_file():
                    # Filter by extension if specified
                    if extensions and file_path.suffix.lower() not in extensions:
                        continue
                    
                    try:
                        stat = file_path.stat()
                        file_info = FileInfo(
                            path=file_path,
                            size=stat.st_size,
                            modified_time=datetime.fromtimestamp(stat.st_mtime)
                        )
                        files.append(file_info)
                    except (OSError, PermissionError) as e:
                        logger.warning(f"Cannot access file {file_path}: {e}")
                        continue
            
            logger.info(f"Found {len(files)} files")
            return files
            
        except Exception as e:
            raise FileProcessingError(f"Error scanning directory: {e}")
    
    def group_by_size(self, files: List[FileInfo]) -> Dict[int, List[FileInfo]]:
        """
        Algorithm 2: Group Files by Size
        
        Group files by size for optimization.
        Files with different sizes cannot be duplicates.
        
        Time Complexity: O(n)
        Space Complexity: O(n)
        
        Args:
            files: List of FileInfo objects
            
        Returns:
            Dictionary mapping file size to list of files
        """
        logger.info("Grouping files by size...")
        
        size_map = {}
        
        for file_info in files:
            size = file_info.size
            if size not in size_map:
                size_map[size] = []
            size_map[size].append(file_info)
        
        # Filter to only groups with potential duplicates
        potential_duplicates = {
            size: file_list 
            for size, file_list in size_map.items() 
            if len(file_list) > 1
        }
        
        logger.info(f"Found {len(potential_duplicates)} size groups with potential duplicates")
        return potential_duplicates
    
    def generate_hash(self, file_path: Path) -> str:
        """
        Algorithm 4: Hash Function
        
        Generate SHA-256 hash of file contents.
        Reads file in chunks to handle large files efficiently.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA-256 hash as hexadecimal string
        """
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks
                while chunk := f.read(self.chunk_size):
                    sha256_hash.update(chunk)
            
            return sha256_hash.hexdigest()
            
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            raise FileProcessingError(f"Cannot hash file: {e}")
    
    def detect_duplicates(self, size_map: Dict[int, List[FileInfo]]) -> List[DuplicateFileGroup]:
        """
        Algorithm 3: Hash-Based Duplicate Detection
        
        Detect duplicate files using hash comparison.
        Only compares files with the same size.
        
        Args:
            size_map: Dictionary of files grouped by size
            
        Returns:
            List of duplicate file groups
        """
        logger.info("Detecting duplicates using hash comparison...")
        
        hash_map = {}
        total_files_to_hash = sum(len(files) for files in size_map.values())
        processed = 0
        
        for size, file_list in size_map.items():
            if len(file_list) > 1:
                # Hash each file in this size group
                for file_info in file_list:
                    try:
                        file_hash = self.generate_hash(file_info.path)
                        file_info.hash = file_hash
                        
                        if file_hash not in hash_map:
                            hash_map[file_hash] = []
                        hash_map[file_hash].append(file_info)
                        
                        processed += 1
                        if processed % 100 == 0:
                            logger.info(f"Hashed {processed}/{total_files_to_hash} files")
                            
                    except Exception as e:
                        logger.warning(f"Skipping file {file_info.path}: {e}")
                        continue
        
        # Create duplicate groups (only groups with > 1 file)
        duplicate_groups = []
        for file_hash, file_list in hash_map.items():
            if len(file_list) > 1:
                total_size = sum(f.size for f in file_list)
                group = DuplicateFileGroup(
                    files=file_list,
                    total_size=total_size,
                    hash=file_hash
                )
                duplicate_groups.append(group)
        
        logger.info(f"Found {len(duplicate_groups)} duplicate file groups")
        return duplicate_groups
    
    def select_best_file(self, group: DuplicateFileGroup, 
                        preferred_directories: Optional[List[str]] = None) -> FileInfo:
        """
        Algorithm 5: Intelligent Cleanup Strategy - Select Best File
        
        Selection criteria (in order of priority):
        1. File in preferred directory
        2. Most recent modification date
        3. Shortest path depth
        4. First file (if all else equal)
        
        Args:
            group: Duplicate file group
            preferred_directories: List of preferred directory names
            
        Returns:
            Best file to keep
        """
        files = group.files
        
        if not files:
            raise ValueError("Cannot select best file from empty group")
        
        if len(files) == 1:
            return files[0]
        
        # Criterion 1: Preferred directory
        if preferred_directories:
            for pref_dir in preferred_directories:
                for file_info in files:
                    if pref_dir in str(file_info.path):
                        logger.debug(f"Selected {file_info.path} (preferred directory)")
                        return file_info
        
        # Criterion 2: Most recent modification date
        most_recent = max(files, key=lambda f: f.modified_time)
        
        # Criterion 3: Shortest path depth (if multiple files have same modification time)
        same_time_files = [f for f in files if f.modified_time == most_recent.modified_time]
        
        if len(same_time_files) > 1:
            shortest_path = min(same_time_files, key=lambda f: len(f.path.parts))
            logger.debug(f"Selected {shortest_path.path} (shortest path)")
            return shortest_path
        
        logger.debug(f"Selected {most_recent.path} (most recent)")
        return most_recent
    
    def intelligent_cleanup(self, duplicate_groups: List[DuplicateFileGroup],
                          action: str = "recycle",
                          preferred_directories: Optional[List[str]] = None,
                          dry_run: bool = True) -> Dict[str, any]:
        """
        Algorithm 5: Intelligent Cleanup Strategy
        
        Clean up duplicate files using intelligent selection.
        
        Args:
            duplicate_groups: List of duplicate file groups
            action: Cleanup action ('recycle', 'delete', 'archive')
            preferred_directories: List of preferred directory names
            dry_run: If True, only simulate cleanup without actual changes
            
        Returns:
            Dictionary with cleanup statistics
        """
        logger.info(f"Starting intelligent cleanup (action={action}, dry_run={dry_run})")
        
        stats = {
            'total_groups': len(duplicate_groups),
            'files_to_remove': 0,
            'space_to_free': 0,
            'files_kept': 0,
            'actions_taken': []
        }
        
        for group in duplicate_groups:
            # Select best file to keep
            best_file = self.select_best_file(group, preferred_directories)
            group.best_file = best_file
            
            stats['files_kept'] += 1
            
            # Process other files in group
            for file_info in group.files:
                if file_info.path == best_file.path:
                    continue
                
                stats['files_to_remove'] += 1
                stats['space_to_free'] += file_info.size
                
                action_result = {
                    'file': str(file_info.path),
                    'size': file_info.size,
                    'action': action,
                    'kept_file': str(best_file.path)
                }
                
                if not dry_run:
                    try:
                        if action == 'recycle':
                            self._move_to_recycle_bin(file_info.path)
                            action_result['status'] = 'recycled'
                        elif action == 'archive':
                            self._move_to_archive(file_info.path)
                            action_result['status'] = 'archived'
                        elif action == 'delete':
                            file_info.path.unlink()
                            action_result['status'] = 'deleted'
                        else:
                            raise ValueError(f"Unknown action: {action}")
                    except Exception as e:
                        logger.error(f"Error processing {file_info.path}: {e}")
                        action_result['status'] = 'error'
                        action_result['error'] = str(e)
                else:
                    action_result['status'] = 'simulated'
                
                stats['actions_taken'].append(action_result)
        
        logger.info(f"Cleanup complete: {stats['files_to_remove']} files, "
                   f"{stats['space_to_free'] / (1024*1024):.2f} MB to free")
        
        return stats
    
    def _move_to_recycle_bin(self, file_path: Path):
        """Move file to recycle bin."""
        self.recycle_bin_path.mkdir(exist_ok=True)
        
        # Preserve directory structure in recycle bin
        relative_path = file_path.relative_to(file_path.anchor) if file_path.is_absolute() else file_path
        dest_path = self.recycle_bin_path / relative_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add timestamp to avoid conflicts
        if dest_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = dest_path.with_name(f"{dest_path.stem}_{timestamp}{dest_path.suffix}")
        
        shutil.move(str(file_path), str(dest_path))
        logger.debug(f"Moved to recycle bin: {file_path} -> {dest_path}")
    
    def _move_to_archive(self, file_path: Path):
        """Move file to archive."""
        self.archive_path.mkdir(exist_ok=True)
        
        # Preserve directory structure in archive
        relative_path = file_path.relative_to(file_path.anchor) if file_path.is_absolute() else file_path
        dest_path = self.archive_path / relative_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add timestamp to avoid conflicts
        if dest_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = dest_path.with_name(f"{dest_path.stem}_{timestamp}{dest_path.suffix}")
        
        shutil.move(str(file_path), str(dest_path))
        logger.debug(f"Moved to archive: {file_path} -> {dest_path}")
    
    def get_statistics(self, duplicate_groups: List[DuplicateFileGroup]) -> Dict[str, any]:
        """
        Get statistics about duplicate files.
        
        Args:
            duplicate_groups: List of duplicate file groups
            
        Returns:
            Dictionary with statistics
        """
        total_files = sum(len(group.files) for group in duplicate_groups)
        total_duplicates = total_files - len(duplicate_groups)  # Subtract one kept file per group
        total_wasted_space = sum(
            sum(f.size for f in group.files[1:])  # All files except the first
            for group in duplicate_groups
        )
        
        return {
            'total_groups': len(duplicate_groups),
            'total_files': total_files,
            'total_duplicates': total_duplicates,
            'total_wasted_space_bytes': total_wasted_space,
            'total_wasted_space_mb': total_wasted_space / (1024 * 1024),
            'total_wasted_space_gb': total_wasted_space / (1024 * 1024 * 1024),
            'largest_group_size': max((len(g.files) for g in duplicate_groups), default=0),
            'average_group_size': total_files / len(duplicate_groups) if duplicate_groups else 0
        }


# Convenience function
def find_duplicate_files(directory: str, 
                        extensions: Optional[List[str]] = None,
                        preferred_directories: Optional[List[str]] = None) -> Tuple[List[DuplicateFileGroup], Dict]:
    """
    Convenience function to find duplicate files in a directory.
    
    Args:
        directory: Directory to scan
        extensions: Optional list of file extensions to include
        preferred_directories: Optional list of preferred directory names
        
    Returns:
        Tuple of (duplicate_groups, statistics)
    """
    detector = FileDuplicateDetector()
    
    # Scan files
    files = detector.scan_files(directory, extensions)
    
    # Group by size
    size_map = detector.group_by_size(files)
    
    # Detect duplicates
    duplicate_groups = detector.detect_duplicates(size_map)
    
    # Select best files
    for group in duplicate_groups:
        group.best_file = detector.select_best_file(group, preferred_directories)
    
    # Get statistics
    stats = detector.get_statistics(duplicate_groups)
    
    return duplicate_groups, stats
