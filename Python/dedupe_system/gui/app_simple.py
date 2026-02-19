# MIT License
# Copyright (c) 2026 Judy Natasha Wambui Gachanja

"""
Simple, User-Friendly GUI for Duplicate Detection & Data Cleaning.

This GUI takes users step-by-step through:
1. Upload your file
2. See the duplicates we found
3. Choose which records to keep
4. Download your cleaned data

Clear, simple, and actually cleans the data!
"""

import streamlit as st
import pandas as pd
import io
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dedupe_system.core.normalizer import DataNormalizer
from dedupe_system.core.exact_matcher import ExactMatcher
from dedupe_system.core.fuzzy_matcher import FuzzyMatcher


def initialize_session():
    """Initialize session state."""
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'df_original' not in st.session_state:
        st.session_state.df_original = None
    if 'duplicate_groups' not in st.session_state:
        st.session_state.duplicate_groups = []
    if 'user_decisions' not in st.session_state:
        st.session_state.user_decisions = {}
    if 'df_cleaned' not in st.session_state:
        st.session_state.df_cleaned = None


def step1_upload():
    """Step 1: Upload file."""
    st.title("🔍 Duplicate Detection & Data Cleaning")
    st.markdown("### Step 1: Upload Your Data File")
    
    st.info("📋 **What we'll do:**\n"
            "1. You upload your CSV file\n"
            "2. We'll find duplicate records\n"
            "3. You decide which ones to keep\n"
            "4. Download your cleaned data")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload a CSV file with your data"
    )
    
    if uploaded_file is not None:
        try:
            # Load the file
            df = pd.read_csv(io.StringIO(uploaded_file.getvalue().decode('utf-8')), dtype=str)
            
            st.success(f"✅ File loaded: {len(df)} records, {len(df.columns)} fields")
            
            # Show preview
            st.markdown("**Preview of your data:**")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Store in session
            st.session_state.df_original = df
            st.session_state.filename = uploaded_file.name
            
            if st.button("➡️ Find Duplicates", type="primary"):
                with st.spinner("🔍 Searching for duplicates..."):
                    find_duplicates(df)
                st.session_state.step = 2
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")


def find_duplicates(df):
    """Find duplicates in the data."""
    # Get all non-ID columns for matching
    columns = [col for col in df.columns if col.lower() not in ['id', 'index', 'key']]
    
    if not columns:
        st.session_state.duplicate_groups = []
        return
    
    # Prepare field types
    field_types = {}
    for col in columns:
        col_lower = col.lower()
        if 'name' in col_lower:
            field_types[col] = 'text_aggressive'
        elif 'email' in col_lower:
            field_types[col] = 'email'
        elif 'phone' in col_lower:
            field_types[col] = 'phone'
        else:
            field_types[col] = 'text'
    
    # Normalize data
    normalizer = DataNormalizer()
    df_normalized = normalizer.normalize_dataframe(df.copy(), field_types)
    
    # Find exact duplicates
    exact_matcher = ExactMatcher(normalizer)
    exact_groups = exact_matcher.find_exact_duplicates(
        df_normalized, columns, field_types, use_normalized=True
    )
    
    # Find fuzzy duplicates
    fuzzy_matcher = FuzzyMatcher(normalizer)
    fuzzy_groups = fuzzy_matcher.find_fuzzy_duplicates(
        df_normalized, columns, threshold=85.0, algorithm='WRatio',
        field_configs=field_types, use_normalized=True
    )
    
    # Combine and store
    all_groups = exact_groups + fuzzy_groups
    st.session_state.duplicate_groups = all_groups


def step2_review_duplicates():
    """Step 2: Review duplicates and make decisions."""
    st.title("🔍 Duplicate Detection & Data Cleaning")
    st.markdown("### Step 2: Review Duplicates")
    
    duplicate_groups = st.session_state.duplicate_groups
    df = st.session_state.df_original
    
    if not duplicate_groups:
        st.success("🎉 **Great news!** No duplicates found in your data.")
        st.info("Your data is already clean. You can download it as-is.")
        
        if st.button("⬇️ Download Data", type="primary"):
            st.session_state.df_cleaned = df
            st.session_state.step = 3
            st.rerun()
        return
    
    # Show summary
    total_duplicates = sum(len(group.records) for group in duplicate_groups)
    st.warning(f"⚠️ **Found {len(duplicate_groups)} duplicate groups** affecting {total_duplicates} records")
    
    st.markdown("---")
    st.markdown("**👇 Review each group and choose which record to KEEP:**")
    st.info("💡 The other records in each group will be removed from your data.")
    
    # Show each duplicate group
    for i, group in enumerate(duplicate_groups):
        with st.expander(f"📋 Duplicate Group {i+1} - {len(group.records)} similar records", expanded=(i==0)):
            
            st.markdown(f"**Similarity:** {group.similarity_score:.0f}%")
            
            # Show records side by side
            group_df = pd.DataFrame(group.records)
            
            # Remove internal columns
            display_cols = [col for col in group_df.columns if not col.startswith('_')]
            if display_cols:
                st.dataframe(group_df[display_cols], use_container_width=True)
            
            # Let user choose which record to keep
            st.markdown("**Which record do you want to KEEP?**")
            
            # Create radio options with record preview
            options = []
            for j, record in enumerate(group.records):
                # Create a preview of the record
                preview_fields = []
                for col in display_cols[:3]:  # Show first 3 fields
                    if col in record:
                        preview_fields.append(f"{col}: {record[col]}")
                preview = " | ".join(preview_fields)
                options.append(f"Record {j+1}: {preview}")
            
            # Add "Keep All" option
            options.append("Keep All (don't remove any)")
            
            choice = st.radio(
                f"Choice for Group {i+1}:",
                options,
                key=f"group_{i}",
                index=0
            )
            
            # Store decision
            if "Keep All" in choice:
                st.session_state.user_decisions[i] = "keep_all"
            else:
                # Extract record number
                record_num = int(choice.split(":")[0].replace("Record ", "")) - 1
                st.session_state.user_decisions[i] = record_num
    
    st.markdown("---")
    
    # Show summary of decisions
    keep_all_count = sum(1 for d in st.session_state.user_decisions.values() if d == "keep_all")
    remove_count = len(duplicate_groups) - keep_all_count
    
    if remove_count > 0:
        st.info(f"📊 **Your choices:** You'll keep {remove_count} groups (removing duplicates) and keep all records in {keep_all_count} groups")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Upload"):
            st.session_state.step = 1
            st.rerun()
    
    with col2:
        if st.button("✅ Clean My Data", type="primary"):
            clean_data()
            st.session_state.step = 3
            st.rerun()


def clean_data():
    """Actually clean the data based on user decisions."""
    df = st.session_state.df_original.copy()
    duplicate_groups = st.session_state.duplicate_groups
    decisions = st.session_state.user_decisions
    
    # Track which rows to remove
    rows_to_remove = set()
    
    for group_idx, group in enumerate(duplicate_groups):
        decision = decisions.get(group_idx, 0)
        
        if decision == "keep_all":
            # Don't remove anything from this group
            continue
        
        # Get the indices of records in this group
        record_indices = []
        for record in group.records:
            # Find this record in the original dataframe
            for idx, row in df.iterrows():
                if all(str(row[col]) == str(record.get(col, '')) for col in df.columns if not col.startswith('_')):
                    record_indices.append(idx)
                    break
        
        # Remove all except the chosen one
        for i, idx in enumerate(record_indices):
            if i != decision:
                rows_to_remove.add(idx)
    
    # Remove the duplicate rows
    df_cleaned = df.drop(index=list(rows_to_remove))
    df_cleaned = df_cleaned.reset_index(drop=True)
    
    st.session_state.df_cleaned = df_cleaned
    st.session_state.removed_count = len(rows_to_remove)


def step3_download():
    """Step 3: Download cleaned data."""
    st.title("🔍 Duplicate Detection & Data Cleaning")
    st.markdown("### Step 3: Download Your Cleaned Data")
    
    df_original = st.session_state.df_original
    df_cleaned = st.session_state.df_cleaned
    removed_count = st.session_state.get('removed_count', 0)
    
    st.success("✅ **Data cleaning complete!**")
    
    # Show before/after comparison
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Original Records", len(df_original))
    with col2:
        st.metric("Cleaned Records", len(df_cleaned), delta=f"-{removed_count}")
    
    if removed_count > 0:
        st.info(f"🗑️ Removed {removed_count} duplicate records")
    else:
        st.info("✨ No duplicates were removed")
    
    # Show preview of cleaned data
    st.markdown("**Preview of your cleaned data:**")
    st.dataframe(df_cleaned.head(10), use_container_width=True)
    
    # Download button
    csv_buffer = io.StringIO()
    df_cleaned.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    
    original_name = st.session_state.get('filename', 'data.csv')
    clean_name = original_name.replace('.csv', '_cleaned.csv')
    
    st.download_button(
        label="⬇️ Download Cleaned Data",
        data=csv_data,
        file_name=clean_name,
        mime="text/csv",
        type="primary"
    )
    
    st.markdown("---")
    
    if st.button("🔄 Start Over"):
        # Reset everything
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def main():
    """Main application."""
    st.set_page_config(
        page_title="Duplicate Detection & Cleaning",
        page_icon="🔍",
        layout="wide"
    )
    
    initialize_session()
    
    # Show progress indicator
    step = st.session_state.step
    st.progress(step / 3)
    
    # Route to appropriate step
    if step == 1:
        step1_upload()
    elif step == 2:
        step2_review_duplicates()
    elif step == 3:
        step3_download()


if __name__ == "__main__":
    main()
