#!/usr/bin/env python3
"""
Minimal GUI test to isolate the issue.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

def test_function():
    """Test function."""
    return "Hello World"

def main():
    """Main function."""
    st.write("Test")

if __name__ == "__main__":
    main()