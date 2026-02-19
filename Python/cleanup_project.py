#!/usr/bin/env python3
"""
Project Cleanup Script
Removes unnecessary files and keeps only essential project files.
"""

import os
import shutil
from pathlib import Path

def cleanup_project():
    """Remove unnecessary files from the project."""
    
    base_dir = Path(__file__).parent
    
    print("🧹 Cleaning up project...")
    print("=" * 60)
    
    # Files and directories to remove
    items_to_remove = [
        # Cache directories
        "__pycache__",
        "dedupe_system/__pycache__",
        "dedupe_system/core/__pycache__",
        "dedupe_system/gui/__pycache__",
        
        # Old log files (keep directories, remove contents)
        "logs/*.log",
        "logs/*.jsonl",
        "test_logs/*.log",
        "test_outputs/*",
        "dedupe_system/logs/*",
        "dedupe_system/outputs/*",
    ]
    
    removed_count = 0
    
    # Remove cache directories
    for cache_dir in ["__pycache__", "dedupe_system/__pycache__", 
                      "dedupe_system/core/__pycache__", "dedupe_system/gui/__pycache__"]:
        cache_path = base_dir / cache_dir
        if cache_path.exists():
            try:
                shutil.rmtree(cache_path)
                print(f"✓ Removed: {cache_dir}")
                removed_count += 1
            except Exception as e:
                print(f"✗ Failed to remove {cache_dir}: {e}")
    
    # Clean log directories (keep the directories, remove files)
    log_dirs = [
        "logs",
        "test_logs", 
        "test_outputs",
        "dedupe_system/logs",
        "dedupe_system/outputs"
    ]
    
    for log_dir in log_dirs:
        log_path = base_dir / log_dir
        if log_path.exists() and log_path.is_dir():
            for file in log_path.iterdir():
                if file.is_file():
                    try:
                        file.unlink()
                        removed_count += 1
                    except Exception as e:
                        print(f"✗ Failed to remove {file.name}: {e}")
            print(f"✓ Cleaned: {log_dir}/")
    
    print("=" * 60)
    print(f"✅ Cleanup complete! Removed {removed_count} items")
    print("\n📁 Project structure is now clean and organized")
    
    # Show final structure
    print("\n📋 Essential files retained:")
    essential_files = [
        "✓ Core modules (dedupe_system/core/*.py)",
        "✓ GUI (dedupe_system/gui/app_simple.py)",
        "✓ Main entry point (dedupe_system/main.py)",
        "✓ Test suite (test_*.py)",
        "✓ Documentation (README.md, PROJECT_ALIGNMENT.md)",
        "✓ Sample data (test_data/)",
        "✓ Requirements (requirements.txt)",
        "✓ License (LICENSE)"
    ]
    
    for item in essential_files:
        print(f"  {item}")

if __name__ == "__main__":
    cleanup_project()
