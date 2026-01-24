#!/usr/bin/env python3
"""
Simple test to isolate GUI import issues.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing GUI imports step by step...")

try:
    print("1. Testing basic imports...")
    import streamlit as st
    import pandas as pd
    import io
    import time
    from pathlib import Path
    from typing import Optional, Dict, Any, List
    print("   ✅ Basic imports successful")
except Exception as e:
    print(f"   ❌ Basic imports failed: {e}")
    sys.exit(1)

try:
    print("2. Testing core imports...")
    from dedupe_system.core.loader import DataLoader
    from dedupe_system.core.normalizer import DataNormalizer
    from dedupe_system.core.exact_matcher import ExactMatcher
    from dedupe_system.core.resolver import DuplicateResolver
    from dedupe_system.core.output_generator import OutputGenerator
    from dedupe_system.core.models import MatchingConfig, ValidationResult, DuplicateGroup
    from dedupe_system.core.exceptions import FileProcessingError, DataValidationError
    from dedupe_system.core.logging_config import get_logger
    print("   ✅ Core imports successful")
except Exception as e:
    print(f"   ❌ Core imports failed: {e}")
    sys.exit(1)

try:
    print("3. Testing GUI module import...")
    from dedupe_system.gui import app
    print("   ✅ GUI module import successful")
    
    print("4. Testing function availability...")
    functions = [name for name in dir(app) if not name.startswith('_')]
    print(f"   Available names: {functions}")
    
    # Check for specific functions
    expected_functions = ['main', 'initialize_session_state', 'render_file_upload_section']
    for func_name in expected_functions:
        if hasattr(app, func_name):
            print(f"   ✅ {func_name} found")
        else:
            print(f"   ❌ {func_name} not found")
    
except Exception as e:
    print(f"   ❌ GUI import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All tests passed!")