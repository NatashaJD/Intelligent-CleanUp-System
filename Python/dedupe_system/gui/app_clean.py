"""
Clean Streamlit GUI Application for the Intelligent Duplicate Detection & Cleanup System.
"""

import streamlit as st
import pandas as pd
import io
import time
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dedupe_system.core.loader import DataLoader
from dedupe_system.core.normalizer import DataNormalizer
from dedupe_system.core.exact_matcher import ExactMatcher
from dedupe_system.core.models import MatchingConfig, ValidationResult, DuplicateGroup
from dedupe_system.core.logging_config import get_logger

logger = get_logger(__name__)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 'upload'


def main():
    """Main application function."""
    
    # Page configuration
    st.set_page_config(
        page_title="Duplicate Detection System",
        page_icon="🔍",
        layout="wide"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Main content
    st.title("🔍 Intelligent Duplicate Detection & Cleanup System")
    st.write("Upload your data file and let our system identify and help you resolve duplicate records.")
    
    # Simple file upload
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['csv', 'json'],
        help="Supported formats: CSV, JSON"
    )
    
    if uploaded_file is not None:
        st.success(f"File uploaded: {uploaded_file.name}")
        
        # Load and display basic info
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(io.StringIO(uploaded_file.getvalue().decode('utf-8')))
            else:
                import json
                data = json.loads(uploaded_file.getvalue().decode('utf-8'))
                df = pd.DataFrame(data)
            
            st.write(f"Loaded {len(df)} records with {len(df.columns)} columns")
            st.dataframe(df.head())
            
        except Exception as e:
            st.error(f"Error loading file: {e}")


if __name__ == "__main__":
    main()