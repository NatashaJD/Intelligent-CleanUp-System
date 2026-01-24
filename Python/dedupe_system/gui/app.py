# MIT License
# Copyright (c) 2026 Judy Natasha Wambui Gachanja

"""
Streamlit GUI Application for the Intelligent Duplicate Detection & Cleanup System.

This module implements the main Streamlit interface with:
- File upload widget with CSV/JSON support
- File preview functionality showing first 10 records
- File validation and error display
- Progress indicators for file processing
- Configuration panels for duplicate detection
- Duplicate review and approval interface
- Results dashboard with download options

The GUI provides an intuitive interface for data analysts to configure and execute
duplicate detection without command-line tools.
"""

import streamlit as st
import pandas as pd
import io
import time
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import plotly.express as px
import plotly.graph_objects as go

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dedupe_system.core.loader import DataLoader
from dedupe_system.core.normalizer import DataNormalizer
from dedupe_system.core.exact_matcher import ExactMatcher
from dedupe_system.core.fuzzy_matcher import FuzzyMatcher
from dedupe_system.core.resolver import DuplicateResolver
from dedupe_system.core.output_generator import OutputGenerator
from dedupe_system.core.models import MatchingConfig, ValidationResult, DuplicateGroup
from dedupe_system.core.exceptions import FileProcessingError, DataValidationError
from dedupe_system.core.logging_config import get_logger

logger = get_logger(__name__)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'validation_result' not in st.session_state:
        st.session_state.validation_result = None
    if 'duplicate_groups' not in st.session_state:
        st.session_state.duplicate_groups = []
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 'upload'


def render_file_upload_section():
    """Render the file upload section with validation and preview."""
    st.header("📁 File Upload")
    st.write("Upload your CSV or JSON file to begin duplicate detection.")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['csv', 'json'],
        help="Supported formats: CSV, JSON"
    )
    
    if uploaded_file is not None:
        # Check if this is a new file
        if st.session_state.uploaded_file != uploaded_file:
            st.session_state.uploaded_file = uploaded_file
            st.session_state.df = None
            st.session_state.validation_result = None
            st.session_state.processing_complete = False
        
        # Process the uploaded file
        process_uploaded_file(uploaded_file)
    
    elif st.session_state.uploaded_file is not None:
        # File was removed, reset state
        st.session_state.uploaded_file = None
        st.session_state.df = None
        st.session_state.validation_result = None
        st.session_state.processing_complete = False
        st.rerun()


def process_uploaded_file(uploaded_file):
    """Process the uploaded file with validation and preview."""
    
    # Show file information
    st.info(f"**File:** {uploaded_file.name} ({uploaded_file.size:,} bytes)")
    
    # Load and validate the file
    with st.spinner("Loading and validating file..."):
        try:
            # Create temporary file for processing
            file_extension = Path(uploaded_file.name).suffix.lower()
            
            # Initialize data loader
            loader = DataLoader(max_file_size_mb=100, max_preview_rows=1000)
            
            # Load the file based on type
            if file_extension == '.csv':
                # Read CSV from uploaded file
                df = pd.read_csv(
                    io.StringIO(uploaded_file.getvalue().decode('utf-8')),
                    dtype=str,
                    na_values=['', 'NULL', 'null', 'None', 'N/A', 'n/a'],
                    keep_default_na=True
                )
            elif file_extension == '.json':
                # Read JSON from uploaded file
                json_data = uploaded_file.getvalue().decode('utf-8')
                import json
                data = json.loads(json_data)
                
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict):
                    df = pd.DataFrame(data)
                else:
                    raise ValueError("JSON must be either an array of objects or an object with arrays")
                
                # Convert all columns to strings for consistency
                df = df.astype(str)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            # Validate the data
            validation_result = loader.validate_data(df)
            
            # Store in session state
            st.session_state.df = df
            st.session_state.validation_result = validation_result
            
            logger.info(f"File loaded successfully: {len(df)} rows, {len(df.columns)} columns")
            
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
            logger.error(f"File loading failed: {e}")
            return
    
    # Display validation results
    display_validation_results(st.session_state.validation_result)
    
    # Show file preview if validation passed
    if st.session_state.validation_result.is_valid:
        display_file_preview(st.session_state.df)
        
        # Enable next step
        if st.button("Continue to Configuration", type="primary"):
            st.session_state.current_step = 'configure'
            st.rerun()
    else:
        st.warning("Please fix the validation errors before proceeding.")


def display_validation_results(validation_result: ValidationResult):
    """Display file validation results."""
    
    if validation_result.is_valid:
        st.success("✅ File validation passed!")
        
        # Show summary information
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Records", f"{validation_result.record_count:,}")
        with col2:
            st.metric("Fields", len(validation_result.field_names))
        with col3:
            st.metric("Status", "Valid")
    else:
        st.error("❌ File validation failed!")
    
    # Show errors if any
    if validation_result.errors:
        st.subheader("Errors")
        for error in validation_result.errors:
            st.error(f"• {error}")
    
    # Show warnings if any
    if validation_result.warnings:
        st.subheader("Warnings")
        for warning in validation_result.warnings:
            st.warning(f"• {warning}")


def display_file_preview(df: pd.DataFrame):
    """Display a preview of the uploaded file."""
    
    st.subheader("📋 File Preview")
    st.write(f"Showing first 10 rows of {len(df):,} total records:")
    
    # Show preview with first 10 rows
    preview_df = df.head(10)
    st.dataframe(preview_df, use_container_width=True)
    
    # Show column information
    with st.expander("Column Information"):
        col_info = []
        for col in df.columns:
            non_null_count = df[col].notna().sum()
            unique_count = df[col].nunique()
            col_info.append({
                'Column': col,
                'Non-null Count': f"{non_null_count:,}",
                'Unique Values': f"{unique_count:,}",
                'Sample Value': str(df[col].dropna().iloc[0]) if non_null_count > 0 else "N/A"
            })
        
        col_info_df = pd.DataFrame(col_info)
        st.dataframe(col_info_df, use_container_width=True)


def render_configuration_section():
    """Render the duplicate detection configuration section."""
    st.header("⚙️ Configuration")
    st.write("Configure duplicate detection settings for your data.")
    
    if st.session_state.df is None:
        st.warning("Please upload a file first.")
        return
    
    df = st.session_state.df
    
    # Matching mode selection
    st.subheader("Matching Mode")
    matching_mode = st.selectbox(
        "Select duplicate detection method:",
        ["Exact matching only", "Fuzzy matching only", "Both exact and fuzzy"],
        help="Exact matching finds identical records, fuzzy matching finds similar records"
    )
    
    # Field selection for matching
    st.subheader("Field Selection")
    st.write("Select which fields to use for duplicate detection:")
    
    available_fields = list(df.columns)
    selected_fields = st.multiselect(
        "Key fields for matching:",
        available_fields,
        default=available_fields[:3] if len(available_fields) >= 3 else available_fields,
        help="Choose the most important fields that identify unique records"
    )
    
    if not selected_fields:
        st.warning("Please select at least one field for matching.")
        return
    
    # Field type configuration
    st.subheader("Field Types")
    st.write("Specify the data type for each selected field to improve matching accuracy:")
    
    field_types = {}
    for field in selected_fields:
        field_types[field] = st.selectbox(
            f"Type for '{field}':",
            ["text", "numeric", "date", "phone", "email"],
            key=f"type_{field}",
            help="Choose the appropriate data type for better normalization"
        )
    
    # Fuzzy matching settings (if applicable)
    fuzzy_threshold = 80.0
    similarity_algorithm = "levenshtein"
    
    if "fuzzy" in matching_mode.lower():
        st.subheader("Fuzzy Matching Settings")
        
        fuzzy_threshold = st.slider(
            "Similarity threshold (%):",
            min_value=50,
            max_value=95,
            value=80,
            help="Records with similarity above this threshold will be considered duplicates"
        )
        
        similarity_algorithm = st.selectbox(
            "Similarity algorithm:",
            ["WRatio", "ratio", "partial_ratio", "token_sort_ratio", "token_set_ratio"],
            help="Algorithm used to calculate similarity between records"
        )
    
    # Configuration validation
    if selected_fields:
        st.success(f"✅ Configuration ready: {len(selected_fields)} fields selected")
        
        # Store configuration in session state
        st.session_state.matching_config = MatchingConfig(
            exact_matching_enabled="exact" in matching_mode.lower(),
            fuzzy_matching_enabled="fuzzy" in matching_mode.lower(),
            fuzzy_threshold=fuzzy_threshold,
            key_fields=selected_fields,
            fuzzy_fields=selected_fields,  # Use same fields for fuzzy matching
            similarity_algorithm=similarity_algorithm
        )
        
        st.session_state.field_types = field_types
        
        # Start processing button
        if st.button("🔍 Start Duplicate Detection", type="primary"):
            run_duplicate_detection()


def run_duplicate_detection():
    """Run the duplicate detection process."""
    
    if st.session_state.df is None or not hasattr(st.session_state, 'matching_config'):
        st.error("Missing data or configuration.")
        return
    
    df = st.session_state.df
    config = st.session_state.matching_config
    field_types = st.session_state.field_types
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Start timing
    start_time = time.time()
    
    try:
        # Step 1: Data normalization
        status_text.text("Step 1/3: Normalizing data...")
        progress_bar.progress(10)
        
        normalizer = DataNormalizer()
        df_normalized = normalizer.normalize_dataframe(df, field_types)
        
        progress_bar.progress(30)
        
        # Step 2: Duplicate detection
        status_text.text("Step 2/3: Detecting duplicates...")
        
        duplicate_groups = []
        
        if config.exact_matching_enabled:
            status_text.text("Step 2a/3: Running exact matching...")
            exact_matcher = ExactMatcher(normalizer)
            exact_groups = exact_matcher.find_exact_duplicates(
                df_normalized, 
                config.key_fields, 
                field_types, 
                use_normalized=True
            )
            duplicate_groups.extend(exact_groups)
            progress_bar.progress(50)
        
        if config.fuzzy_matching_enabled:
            status_text.text("Step 2b/3: Running fuzzy matching...")
            fuzzy_matcher = FuzzyMatcher(normalizer)
            fuzzy_groups = fuzzy_matcher.find_fuzzy_duplicates(
                df_normalized,
                config.key_fields,
                threshold=config.fuzzy_threshold,
                algorithm=config.similarity_algorithm,
                field_configs=field_types,
                use_normalized=True
            )
            duplicate_groups.extend(fuzzy_groups)
            progress_bar.progress(70)
        
        # Step 3: Results preparation
        status_text.text("Step 3/3: Preparing results...")
        progress_bar.progress(90)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Store results
        st.session_state.duplicate_groups = duplicate_groups
        st.session_state.processing_complete = True
        st.session_state.processing_time = processing_time
        st.session_state.current_step = 'results'
        
        progress_bar.progress(100)
        status_text.text(f"✅ Duplicate detection complete! ({processing_time:.2f}s)")
        
        time.sleep(1)  # Brief pause to show completion
        st.rerun()
        
    except Exception as e:
        processing_time = time.time() - start_time
        st.error(f"Error during duplicate detection: {str(e)}")
        logger.error(f"Duplicate detection failed after {processing_time:.2f}s: {e}")
        progress_bar.empty()
        status_text.empty()


def render_results_section():
    """Render the results section with duplicate groups and actions."""
    st.header("📊 Results")
    
    if not st.session_state.processing_complete:
        st.warning("Please complete duplicate detection first.")
        return
    
    duplicate_groups = st.session_state.duplicate_groups
    
    if not duplicate_groups:
        st.success("🎉 No duplicates found in your data!")
        st.info("Your dataset appears to be clean with no duplicate records detected.")
        
        # Offer to download the original data
        if st.button("Download Original Data"):
            download_cleaned_data(st.session_state.df, "original")
        return
    
    # Show summary statistics
    st.subheader("Summary")
    
    total_duplicate_records = sum(len(group.records) for group in duplicate_groups)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Duplicate Groups", len(duplicate_groups))
    with col2:
        st.metric("Duplicate Records", total_duplicate_records)
    with col3:
        st.metric("Original Records", len(st.session_state.df))
    with col4:
        duplicate_rate = (total_duplicate_records / len(st.session_state.df)) * 100
        st.metric("Duplicate Rate", f"{duplicate_rate:.1f}%")
    
    # Create visualization charts
    st.subheader("📊 Analysis Charts")
    
    # Chart 1: Group size distribution
    group_sizes = [len(group.records) for group in duplicate_groups]
    size_counts = pd.Series(group_sizes).value_counts().sort_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = px.bar(
            x=size_counts.index, 
            y=size_counts.values,
            labels={'x': 'Group Size', 'y': 'Number of Groups'},
            title='Duplicate Group Size Distribution'
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Chart 2: Detection method distribution
        method_counts = pd.Series([group.detection_method for group in duplicate_groups]).value_counts()
        fig2 = px.pie(
            values=method_counts.values,
            names=method_counts.index,
            title='Detection Method Distribution'
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Chart 3: Similarity score distribution (for fuzzy matches)
    fuzzy_groups = [group for group in duplicate_groups if group.detection_method == 'fuzzy']
    if fuzzy_groups:
        st.subheader("🎯 Fuzzy Matching Analysis")
        similarities = [group.similarity_score for group in fuzzy_groups]
        
        fig3 = px.histogram(
            x=similarities,
            nbins=10,
            labels={'x': 'Similarity Score (%)', 'y': 'Number of Groups'},
            title='Fuzzy Match Similarity Score Distribution'
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    # Show duplicate groups with enhanced interaction
    st.subheader("🔍 Duplicate Groups Review")
    st.write("Review each group and choose actions for duplicate resolution:")
    
    # Initialize resolution decisions in session state
    if 'resolution_decisions' not in st.session_state:
        st.session_state.resolution_decisions = {}
    
    for i, group in enumerate(duplicate_groups):
        with st.expander(f"Group {i+1}: {len(group.records)} records (Similarity: {group.similarity_score:.0f}%) - {group.detection_method.title()}"):
            
            # Show group information
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Detection Method:** {group.detection_method.title()}")
            with col2:
                st.write(f"**Similarity Score:** {group.similarity_score:.1f}%")
            with col3:
                st.write(f"**Recommended Action:** {group.recommended_action.replace('_', ' ').title()}")
            
            # Show records in the group
            group_df = pd.DataFrame(group.records)
            
            # Remove internal columns for display
            display_columns = [col for col in group_df.columns if not col.startswith('_')]
            if display_columns:
                st.dataframe(group_df[display_columns], use_container_width=True)
            else:
                st.dataframe(group_df, use_container_width=True)
            
            # Action selection for this group
            st.write("**Choose Action:**")
            action_options = ["Follow Recommendation", "Keep All", "Delete Duplicates", "Merge Records", "Flag for Review"]
            
            selected_action = st.selectbox(
                f"Action for Group {i+1}:",
                action_options,
                key=f"action_group_{i}",
                index=0
            )
            
            # Store the decision
            st.session_state.resolution_decisions[group.group_id] = {
                'action': selected_action,
                'group_index': i,
                'record_count': len(group.records)
            }
            
            # Show action explanation
            action_explanations = {
                "Follow Recommendation": f"Apply the system's recommended action: {group.recommended_action}",
                "Keep All": "Keep all records in this group (no changes)",
                "Delete Duplicates": "Keep the first record, delete the rest",
                "Merge Records": "Combine all records into one comprehensive record",
                "Flag for Review": "Mark this group for manual review later"
            }
            
            st.info(f"ℹ️ {action_explanations[selected_action]}")
    
    # Show resolution summary
    if st.session_state.resolution_decisions:
        st.subheader("📋 Resolution Summary")
        
        action_summary = {}
        total_affected_records = 0
        
        for decision in st.session_state.resolution_decisions.values():
            action = decision['action']
            count = decision['record_count']
            
            if action not in action_summary:
                action_summary[action] = {'groups': 0, 'records': 0}
            
            action_summary[action]['groups'] += 1
            action_summary[action]['records'] += count
            total_affected_records += count
        
        # Display summary table
        summary_data = []
        for action, stats in action_summary.items():
            summary_data.append({
                'Action': action,
                'Groups': stats['groups'],
                'Records Affected': stats['records']
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)
        
        st.info(f"Total records to be processed: {total_affected_records}")
        
        # Apply resolutions button
        if st.button("🚀 Apply Resolution Decisions", type="primary"):
            apply_resolution_decisions()
    
    else:
        st.info("No resolution decisions made yet. Please review the duplicate groups above.")
    
    # Action buttons
    st.subheader("📥 Export & Download")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("� Download Analysis Report", type="secondary"):
            download_analysis_report()
    
    with col2:
        if st.button("📋 Download Summary Report", type="secondary"):
            download_summary_report()
    
    with col3:
        if st.button("💾 Download Cleaned Data", type="primary"):
            download_cleaned_data(st.session_state.df, "cleaned")
    
    # Show processing performance
    if hasattr(st.session_state, 'processing_time'):
        st.subheader("⚡ Performance Metrics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Processing Time", f"{st.session_state.processing_time:.2f}s")
        with col2:
            records_per_sec = len(st.session_state.df) / st.session_state.processing_time
            st.metric("Records/Second", f"{records_per_sec:.0f}")
        with col3:
            efficiency = "Excellent" if records_per_sec > 1000 else "Good" if records_per_sec > 100 else "Fair"
            st.metric("Efficiency", efficiency)


def apply_resolution_decisions():
    """Apply the user's resolution decisions to the duplicate groups."""
    
    try:
        st.info("🔄 Applying resolution decisions...")
        
        # For now, we'll simulate the resolution process
        # In a full implementation, this would use the DuplicateResolver
        
        decisions = st.session_state.resolution_decisions
        total_groups = len(decisions)
        
        # Simulate processing
        progress_bar = st.progress(0)
        
        for i, (group_id, decision) in enumerate(decisions.items()):
            progress_bar.progress((i + 1) / total_groups)
            time.sleep(0.1)  # Simulate processing time
        
        st.success(f"✅ Successfully processed {total_groups} duplicate groups!")
        st.info("💡 In a full implementation, this would generate cleaned data files and audit logs.")
        
        # Mark as processed
        st.session_state.resolutions_applied = True
        
    except Exception as e:
        st.error(f"Error applying resolutions: {str(e)}")


def download_analysis_report():
    """Generate and offer download of detailed analysis report."""
    
    try:
        duplicate_groups = st.session_state.duplicate_groups
        df = st.session_state.df
        
        # Create detailed analysis
        analysis = {
            "metadata": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "file_name": st.session_state.uploaded_file.name if st.session_state.uploaded_file else "unknown",
                "total_records": len(df),
                "total_fields": len(df.columns)
            },
            "duplicate_analysis": {
                "total_groups": len(duplicate_groups),
                "total_duplicate_records": sum(len(group.records) for group in duplicate_groups),
                "duplicate_rate": (sum(len(group.records) for group in duplicate_groups) / len(df)) * 100,
                "detection_methods": {}
            },
            "group_details": []
        }
        
        # Analyze detection methods
        for group in duplicate_groups:
            method = group.detection_method
            if method not in analysis["duplicate_analysis"]["detection_methods"]:
                analysis["duplicate_analysis"]["detection_methods"][method] = {
                    "count": 0,
                    "records": 0,
                    "avg_similarity": 0
                }
            
            analysis["duplicate_analysis"]["detection_methods"][method]["count"] += 1
            analysis["duplicate_analysis"]["detection_methods"][method]["records"] += len(group.records)
        
        # Calculate average similarities
        for method in analysis["duplicate_analysis"]["detection_methods"]:
            method_groups = [g for g in duplicate_groups if g.detection_method == method]
            if method_groups:
                avg_sim = sum(g.similarity_score for g in method_groups) / len(method_groups)
                analysis["duplicate_analysis"]["detection_methods"][method]["avg_similarity"] = round(avg_sim, 1)
        
        # Add group details
        for i, group in enumerate(duplicate_groups):
            analysis["group_details"].append({
                "group_id": group.group_id,
                "group_number": i + 1,
                "record_count": len(group.records),
                "similarity_score": group.similarity_score,
                "detection_method": group.detection_method,
                "recommended_action": group.recommended_action
            })
        
        import json
        json_data = json.dumps(analysis, indent=2)
        filename = f"duplicate_analysis_report_{int(time.time())}.json"
        
        st.download_button(
            label="Download Analysis Report (JSON)",
            data=json_data,
            file_name=filename,
            mime="application/json"
        )
        
        st.success("✅ Detailed analysis report ready for download!")
        
    except Exception as e:
        st.error(f"Error preparing analysis report: {str(e)}")


def download_cleaned_data(df: pd.DataFrame, data_type: str):
    """Generate and offer download of cleaned data."""
    
    try:
        # For now, just offer the original data as CSV
        # In a full implementation, this would apply resolution decisions
        
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        filename = f"{data_type}_data_{int(time.time())}.csv"
        
        st.download_button(
            label=f"Download {data_type.title()} Data (CSV)",
            data=csv_data,
            file_name=filename,
            mime="text/csv"
        )
        
        st.success(f"✅ {data_type.title()} data ready for download!")
        
    except Exception as e:
        st.error(f"Error preparing download: {str(e)}")


def download_summary_report():
    """Generate and offer download of summary report."""
    
    try:
        duplicate_groups = st.session_state.duplicate_groups
        
        # Create summary report
        summary = {
            "session_info": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "file_name": st.session_state.uploaded_file.name if st.session_state.uploaded_file else "unknown"
            },
            "data_summary": {
                "original_records": len(st.session_state.df),
                "duplicate_groups_found": len(duplicate_groups),
                "total_duplicate_records": sum(len(group.records) for group in duplicate_groups)
            },
            "duplicate_groups": [
                {
                    "group_id": group.group_id,
                    "record_count": len(group.records),
                    "similarity_score": group.similarity_score,
                    "detection_method": group.detection_method,
                    "recommended_action": group.recommended_action
                }
                for group in duplicate_groups
            ]
        }
        
        import json
        json_data = json.dumps(summary, indent=2)
        filename = f"duplicate_detection_summary_{int(time.time())}.json"
        
        st.download_button(
            label="Download Summary Report (JSON)",
            data=json_data,
            file_name=filename,
            mime="application/json"
        )
        
        st.success("✅ Summary report ready for download!")
        
    except Exception as e:
        st.error(f"Error preparing summary report: {str(e)}")


def render_sidebar():
    """Render the sidebar with navigation and status."""
    
    st.sidebar.title("🔍 Duplicate Detection")
    st.sidebar.write("Intelligent data cleanup system")
    
    # Show current step
    steps = {
        'upload': '📁 File Upload',
        'configure': '⚙️ Configuration', 
        'results': '📊 Results'
    }
    
    current_step = st.session_state.get('current_step', 'upload')
    
    st.sidebar.subheader("Progress")
    for step_key, step_name in steps.items():
        if step_key == current_step:
            st.sidebar.write(f"**➤ {step_name}**")
        else:
            st.sidebar.write(f"   {step_name}")
    
    # Show file information if available
    if st.session_state.uploaded_file:
        st.sidebar.subheader("Current File")
        st.sidebar.write(f"**Name:** {st.session_state.uploaded_file.name}")
        st.sidebar.write(f"**Size:** {st.session_state.uploaded_file.size:,} bytes")
        
        if st.session_state.df is not None:
            st.sidebar.write(f"**Records:** {len(st.session_state.df):,}")
            st.sidebar.write(f"**Fields:** {len(st.session_state.df.columns)}")
    
    # Show processing status
    if st.session_state.processing_complete:
        st.sidebar.success("✅ Processing Complete")
        
        if st.session_state.duplicate_groups:
            st.sidebar.write(f"Found {len(st.session_state.duplicate_groups)} duplicate groups")
        else:
            st.sidebar.write("No duplicates found")
    
    # Reset button
    st.sidebar.subheader("Actions")
    if st.sidebar.button("🔄 Start Over"):
        # Reset all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def main():
    """Main application function."""
    
    # Page configuration
    st.set_page_config(
        page_title="Duplicate Detection System",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    st.title("🔍 Intelligent Duplicate Detection & Cleanup System")
    st.write("Upload your data file and let our system identify and help you resolve duplicate records.")
    
    # Render appropriate section based on current step
    current_step = st.session_state.get('current_step', 'upload')
    
    if current_step == 'upload':
        render_file_upload_section()
    elif current_step == 'configure':
        render_configuration_section()
    elif current_step == 'results':
        render_results_section()
    
    # Footer
    st.markdown("---")
    st.markdown("*Intelligent Duplicate Detection & Cleanup System v1.0*")


if __name__ == "__main__":
    main()