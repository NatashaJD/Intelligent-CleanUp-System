# MIT License
# Copyright (c) 2026 Judy Natasha Wambui Gachanja

"""
Simple, User-Friendly Duplicate Detection & Cleanup Tool

This tool helps you find and remove duplicate records from your data files.
It guides you step-by-step through the process and actually cleans your data.

Steps:
1. Upload your file
2. Preview your data
3. Choose which fields to check for duplicates
4. Review the duplicates we found
5. Decide what to do with each group
6. Download your cleaned data

Designed for non-technical users who need clean data quickly.
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
from dedupe_system.core.fuzzy_matcher import FuzzyMatcher
from dedupe_system.core.golden_record import GoldenRecordCreator
from dedupe_system.core.models import MatchingConfig, ValidationResult, DuplicateGroup
from dedupe_system.core.logging_config import get_logger

logger = get_logger(__name__)


def initialize_session_state():
    """Initialize session state variables."""
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'selected_fields' not in st.session_state:
        st.session_state.selected_fields = []
    if 'duplicate_groups' not in st.session_state:
        st.session_state.duplicate_groups = []
    if 'user_decisions' not in st.session_state:
        st.session_state.user_decisions = {}
    if 'cleaned_df' not in st.session_state:
        st.session_state.cleaned_df = None


def show_progress_bar():
    """Show progress through the steps."""
    steps = [
        "📁 Upload File",
        "👀 Preview Data", 
        "⚙️ Choose Fields",
        "🔍 Find Duplicates",
        "✋ Make Decisions",
        "✅ Get Clean Data"
    ]
    
    current_step = st.session_state.step
    
    # Create progress bar
    progress = (current_step - 1) / (len(steps) - 1)
    st.progress(progress)
    
    # Show steps
    cols = st.columns(len(steps))
    for i, (col, step_name) in enumerate(zip(cols, steps)):
        with col:
            if i + 1 == current_step:
                st.markdown(f"**{step_name}** ⬅️")
            elif i + 1 < current_step:
                st.markdown(f"~~{step_name}~~ ✅")
            else:
                st.markdown(f"{step_name}")


def step1_upload_file():
    """Step 1: Upload and validate file."""
    st.header("📁 Step 1: Upload Your Data File")
    st.write("Upload a CSV or JSON file that contains duplicate records you want to clean.")
    
    uploaded_file = st.file_uploader(
        "Choose your file",
        type=['csv', 'json'],
        help="We support CSV and JSON files up to 100MB"
    )
    
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
        
        # Load the file
        with st.spinner("Loading your file..."):
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(
                        io.StringIO(uploaded_file.getvalue().decode('utf-8')),
                        dtype=str
                    )
                else:  # JSON
                    import json
                    data = json.loads(uploaded_file.getvalue().decode('utf-8'))
                    if isinstance(data, list):
                        df = pd.DataFrame(data)
                    else:
                        df = pd.DataFrame(data)
                    df = df.astype(str)
                
                st.session_state.df = df
                
                # Show file info
                st.success(f"✅ File loaded successfully!")
                st.info(f"📊 Your file has **{len(df):,} records** and **{len(df.columns)} fields**")
                
                # Show first few rows
                st.write("**Preview of your data:**")
                st.dataframe(df.head(), use_container_width=True)
                
                if st.button("Continue to Next Step →", type="primary"):
                    st.session_state.step = 2
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error loading file: {str(e)}")
                st.write("Please make sure your file is a valid CSV or JSON file.")
    
    else:
        st.info("👆 Please upload a file to get started")


def step2_preview_data():
    """Step 2: Preview and understand the data."""
    st.header("👀 Step 2: Preview Your Data")
    st.write("Let's take a closer look at your data to understand what we're working with.")
    
    df = st.session_state.df
    
    # Show summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records", f"{len(df):,}")
    with col2:
        st.metric("Fields/Columns", len(df.columns))
    with col3:
        # Estimate potential duplicates by looking for repeated values
        potential_duplicates = 0
        for col in df.columns:
            if df[col].nunique() < len(df):
                potential_duplicates += len(df) - df[col].nunique()
        st.metric("Potential Issues", f"{potential_duplicates:,}")
    
    # Show data preview
    st.write("**Your data looks like this:**")
    st.dataframe(df.head(10), use_container_width=True)
    
    # Show column information
    st.write("**Information about each field:**")
    col_info = []
    for col in df.columns:
        unique_count = df[col].nunique()
        sample_values = df[col].dropna().head(3).tolist()
        col_info.append({
            'Field Name': col,
            'Unique Values': f"{unique_count:,}",
            'Sample Values': ', '.join(str(v) for v in sample_values)
        })
    
    col_info_df = pd.DataFrame(col_info)
    st.dataframe(col_info_df, use_container_width=True)
    
    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Upload"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("Continue to Choose Fields →", type="primary"):
            st.session_state.step = 3
            st.rerun()


def step3_choose_fields():
    """Step 3: Choose which fields to check for duplicates."""
    st.header("⚙️ Step 3: Choose Fields to Check")
    st.write("Select which fields we should compare to find duplicate records.")
    
    df = st.session_state.df
    
    # Helpful guidance
    st.info("""
    💡 **Tips for choosing fields:**
    - Choose fields like **name, email, phone, address** that should be similar for duplicates
    - **Avoid ID fields** (id, record_id, etc.) as they are usually unique
    - **More fields = more precise** but might miss some duplicates
    - **Fewer fields = more matches** but might catch non-duplicates
    """)
    
    # Show field options with smart suggestions
    st.write("**Available fields in your data:**")
    
    suggested_fields = []
    avoid_fields = []
    
    for col in df.columns:
        col_lower = col.lower()
        # Suggest good fields for duplicate detection
        if any(word in col_lower for word in ['name', 'email', 'phone', 'address', 'title', 'company']):
            suggested_fields.append(col)
        # Flag fields to avoid
        elif any(word in col_lower for word in ['id', 'index', 'key', 'created', 'updated', 'date', 'time']):
            avoid_fields.append(col)
    
    # Show suggestions
    if suggested_fields:
        st.success(f"✅ **Recommended fields:** {', '.join(suggested_fields)}")
    if avoid_fields:
        st.warning(f"⚠️ **Avoid these fields:** {', '.join(avoid_fields)} (usually unique)")
    
    # Let user select fields
    selected_fields = st.multiselect(
        "Select fields to check for duplicates:",
        options=list(df.columns),
        default=suggested_fields[:3] if suggested_fields else [],  # Default to first 3 suggestions
        help="Choose the fields that should be similar for records to be considered duplicates"
    )
    
    if selected_fields:
        st.session_state.selected_fields = selected_fields
        
        # Show what we'll compare
        st.write("**We'll compare these fields:**")
        for field in selected_fields:
            sample_values = df[field].dropna().head(5).tolist()
            st.write(f"- **{field}**: {', '.join(str(v) for v in sample_values)}...")
        
        # Show matching strategy
        st.write("**How we'll find duplicates:**")
        st.write("1. **Exact matches**: Records with identical values in all selected fields")
        st.write("2. **Similar matches**: Records with very similar values (like 'John Smith' and 'J. Smith')")
        
        # Navigation
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to Preview"):
                st.session_state.step = 2
                st.rerun()
        with col2:
            if st.button("Find Duplicates →", type="primary"):
                st.session_state.step = 4
                st.rerun()
    else:
        st.warning("Please select at least one field to check for duplicates.")
        
        # Navigation
        if st.button("← Back to Preview"):
            st.session_state.step = 2
            st.rerun()


def step4_find_duplicates():
    """Step 4: Find and show duplicates."""
    st.header("🔍 Step 4: Finding Duplicates...")
    st.write("We're analyzing your data to find duplicate records.")
    
    df = st.session_state.df
    selected_fields = st.session_state.selected_fields
    
    # Progress indicator
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Prepare data
        status_text.text("Preparing data for comparison...")
        progress_bar.progress(20)
        
        # Create field type mapping (smart defaults)
        field_types = {}
        for field in selected_fields:
            field_lower = field.lower()
            if 'email' in field_lower:
                field_types[field] = 'email'
            elif any(word in field_lower for word in ['phone', 'tel', 'mobile']):
                field_types[field] = 'phone'
            elif any(word in field_lower for word in ['name', 'title', 'address']):
                field_types[field] = 'text_aggressive'
            else:
                field_types[field] = 'text'
        
        # Step 2: Normalize data
        status_text.text("Cleaning and standardizing data...")
        progress_bar.progress(40)
        
        normalizer = DataNormalizer()
        df_normalized = normalizer.normalize_dataframe(df.copy(), field_types)
        
        # Step 3: Find exact duplicates
        status_text.text("Finding exact duplicates...")
        progress_bar.progress(60)
        
        exact_matcher = ExactMatcher(normalizer)
        exact_groups = exact_matcher.find_exact_duplicates(
            df_normalized, selected_fields, field_types, use_normalized=True
        )
        
        # Step 4: Find similar duplicates
        status_text.text("Finding similar duplicates...")
        progress_bar.progress(80)
        
        fuzzy_matcher = FuzzyMatcher(normalizer)
        fuzzy_groups = fuzzy_matcher.find_fuzzy_duplicates(
            df_normalized, selected_fields, threshold=85.0, 
            algorithm='WRatio', field_configs=field_types, use_normalized=True
        )
        
        # Combine results
        all_groups = exact_groups + fuzzy_groups
        st.session_state.duplicate_groups = all_groups
        
        # Complete
        progress_bar.progress(100)
        status_text.text("Analysis complete!")
        
        time.sleep(1)  # Brief pause
        
        # Show results
        st.success(f"✅ **Analysis Complete!**")
        
        if all_groups:
            total_duplicates = sum(len(group.records) for group in all_groups)
            st.info(f"🎯 **Found {len(all_groups)} groups** containing **{total_duplicates} duplicate records**")
            
            # Show summary
            exact_count = len(exact_groups)
            fuzzy_count = len(fuzzy_groups)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Exact Duplicates", f"{exact_count} groups")
            with col2:
                st.metric("Similar Duplicates", f"{fuzzy_count} groups")
            
            if st.button("Review Duplicates →", type="primary"):
                st.session_state.step = 5
                st.rerun()
        else:
            st.success("🎉 **No duplicates found!**")
            st.write("Your data appears to be clean. You can download it as-is.")
            
            # Offer download of original data
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="📥 Download Your Clean Data",
                data=csv_data,
                file_name=f"clean_{st.session_state.uploaded_file.name}",
                mime="text/csv",
                type="primary"
            )
        
        # Navigation
        if st.button("← Back to Choose Fields"):
            st.session_state.step = 3
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error during analysis: {str(e)}")
        if st.button("← Back to Choose Fields"):
            st.session_state.step = 3
            st.rerun()


def step5_make_decisions():
    """Step 5: Review duplicates and make decisions."""
    st.header("✋ Step 5: Review Duplicates & Make Decisions")
    st.write("Here are the duplicate groups we found. For each group, decide what you want to do.")
    
    duplicate_groups = st.session_state.duplicate_groups
    
    if not duplicate_groups:
        st.error("No duplicates found. Please go back and try different fields.")
        if st.button("← Back to Choose Fields"):
            st.session_state.step = 3
            st.rerun()
        return
    
    # Show summary
    total_duplicates = sum(len(group.records) for group in duplicate_groups)
    st.info(f"📊 **{len(duplicate_groups)} groups** with **{total_duplicates} duplicate records** total")
    
    # Decision options explanation
    st.write("**Your options for each group:**")
    st.write("- **Keep Best**: Keep the most complete record, remove others")
    st.write("- **Keep First**: Keep the first record, remove others") 
    st.write("- **Keep All**: Don't remove anything (skip this group)")
    
    # Review each group
    user_decisions = st.session_state.user_decisions
    
    for i, group in enumerate(duplicate_groups):
        with st.expander(f"📋 Group {i+1}: {len(group.records)} records ({group.similarity_score:.0f}% similar)", expanded=i<3):
            
            # Show the records
            st.write("**These records look like duplicates:**")
            group_df = pd.DataFrame(group.records)
            
            # Only show the fields we used for matching + a few others
            display_cols = st.session_state.selected_fields.copy()
            for col in ['id', 'name', 'email', 'phone']:
                if col in group_df.columns and col not in display_cols:
                    display_cols.append(col)
            
            display_cols = [col for col in display_cols if col in group_df.columns]
            st.dataframe(group_df[display_cols], use_container_width=True)
            
            # Decision for this group
            decision = st.radio(
                f"What should we do with Group {i+1}?",
                ["Keep Best", "Keep First", "Keep All"],
                key=f"decision_{group.group_id}",
                help="Keep Best = most complete record, Keep First = first in list, Keep All = no changes"
            )
            
            user_decisions[group.group_id] = {
                'action': decision,
                'group': group
            }
    
    st.session_state.user_decisions = user_decisions
    
    # Show summary of decisions
    if user_decisions:
        st.write("**Summary of your decisions:**")
        keep_best = sum(1 for d in user_decisions.values() if d['action'] == 'Keep Best')
        keep_first = sum(1 for d in user_decisions.values() if d['action'] == 'Keep First')
        keep_all = sum(1 for d in user_decisions.values() if d['action'] == 'Keep All')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Keep Best", keep_best)
        with col2:
            st.metric("Keep First", keep_first)
        with col3:
            st.metric("Keep All", keep_all)
        
        # Navigation
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to Find Duplicates"):
                st.session_state.step = 4
                st.rerun()
        with col2:
            if st.button("Apply Changes →", type="primary"):
                st.session_state.step = 6
                st.rerun()


def step6_get_clean_data():
    """Step 6: Apply decisions and provide clean data."""
    st.header("✅ Step 6: Your Clean Data is Ready!")
    st.write("We've applied your decisions and cleaned your data.")
    
    df = st.session_state.df
    user_decisions = st.session_state.user_decisions
    
    # Apply the cleaning decisions
    with st.spinner("Applying your decisions and cleaning data..."):
        cleaned_df = df.copy()
        records_to_remove = []
        golden_record_creator = GoldenRecordCreator()
        
        for group_id, decision in user_decisions.items():
            group = decision['group']
            action = decision['action']
            
            if action == "Keep All":
                continue  # No changes
            
            # Get the indices of records in this group
            group_indices = []
            for record in group.records:
                # Find the index in the original dataframe
                for idx, row in df.iterrows():
                    if all(str(row[field]) == str(record[field]) for field in st.session_state.selected_fields if field in row.index and field in record):
                        group_indices.append(idx)
                        break
            
            if action == "Keep First":
                # Remove all but the first record
                records_to_remove.extend(group_indices[1:])
            
            elif action == "Keep Best":
                # Create a golden record and replace the first, remove others
                try:
                    golden_record = golden_record_creator.create_golden_record(group)
                    # Update the first record with golden record data
                    if group_indices:
                        first_idx = group_indices[0]
                        for field, value in golden_record.items():
                            if not field.startswith('_') and field in cleaned_df.columns:
                                cleaned_df.at[first_idx, field] = value
                        # Remove the other records
                        records_to_remove.extend(group_indices[1:])
                except Exception as e:
                    st.warning(f"Could not create best record for group {group_id}, keeping first instead")
                    records_to_remove.extend(group_indices[1:])
        
        # Remove the duplicate records
        cleaned_df = cleaned_df.drop(records_to_remove).reset_index(drop=True)
        st.session_state.cleaned_df = cleaned_df
    
    # Show results
    original_count = len(df)
    cleaned_count = len(cleaned_df)
    removed_count = original_count - cleaned_count
    
    st.success(f"🎉 **Cleaning Complete!**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Original Records", f"{original_count:,}")
    with col2:
        st.metric("Removed Duplicates", f"{removed_count:,}")
    with col3:
        st.metric("Clean Records", f"{cleaned_count:,}")
    
    # Show preview of clean data
    st.write("**Preview of your clean data:**")
    st.dataframe(cleaned_df.head(10), use_container_width=True)
    
    # Download button
    csv_buffer = io.StringIO()
    cleaned_df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    
    original_name = st.session_state.uploaded_file.name
    clean_name = f"clean_{original_name}"
    
    st.download_button(
        label="📥 Download Your Clean Data",
        data=csv_data,
        file_name=clean_name,
        mime="text/csv",
        type="primary",
        help=f"This will download {clean_name} with {removed_count} duplicates removed"
    )
    
    st.success(f"✅ Click the button above to download **{clean_name}** with all duplicates removed!")
    
    # Option to start over
    if st.button("🔄 Clean Another File"):
        # Reset everything
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def main():
    """Main application."""
    st.set_page_config(
        page_title="Duplicate Cleaner",
        page_icon="🧹",
        layout="wide"
    )
    
    # Initialize
    initialize_session_state()
    
    # Header
    st.title("🧹 Duplicate Data Cleaner")
    st.write("**Simple tool to find and remove duplicate records from your data files**")
    
    # Progress bar
    show_progress_bar()
    st.markdown("---")
    
    # Show appropriate step
    step = st.session_state.step
    
    if step == 1:
        step1_upload_file()
    elif step == 2:
        step2_preview_data()
    elif step == 3:
        step3_choose_fields()
    elif step == 4:
        step4_find_duplicates()
    elif step == 5:
        step5_make_decisions()
    elif step == 6:
        step6_get_clean_data()
    
    # Footer
    st.markdown("---")
    st.markdown("*Simple Duplicate Cleaner - Made for non-technical users*")


if __name__ == "__main__":
    main()