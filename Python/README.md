# Intelligent Duplicate Detection & Cleanup System

A comprehensive Python-based system for detecting and resolving duplicate records in CSV/JSON datasets and duplicate files in directories. Implements both exact and fuzzy matching algorithms with an intuitive Streamlit GUI interface.

## Features

### Record-Level Duplicate Detection
- **Dual Matching System**: Both exact and fuzzy duplicate detection
- **Advanced Algorithms**: 5 configurable fuzzy matching algorithms (RapidFuzz)
- **File Support**: CSV and JSON file formats with automatic encoding detection
- **Database Support**: Optional MySQL and PostgreSQL connectivity
- **Data Validation**: Comprehensive input validation with detailed error reporting
- **Smart Performance**: O(n) exact matching, blocking strategies for fuzzy matching
- **Data Normalization**: Text, numeric, date, phone, and email field normalization
- **Golden Record Creation**: Survivorship rules for intelligent merging

### File-Level Duplicate Detection
- **Hash-Based Detection**: SHA-256 hashing for exact file duplicate detection
- **Size Optimization**: Groups files by size before hashing (O(n) complexity)
- **Recursive Scanning**: Scans entire directory trees
- **Intelligent Cleanup**: Smart file selection based on recency, location, and path depth
- **Multiple Actions**: Recycle bin, archive, or permanent deletion
- **Space Analysis**: Calculate wasted storage space

### Performance & Evaluation
- **Precision & Recall**: Calculate accuracy metrics against ground truth
- **Execution Timing**: Track processing speed and throughput
- **Performance Reports**: Comprehensive evaluation reports
- **Validated Metrics**: Meets documented performance targets (Precision: 0.97, Recall: 0.94)

### User Interface
- **Interactive GUI**: User-friendly Streamlit interface with visual analytics
- **Step-by-Step Workflow**: Clear guidance through upload → detect → decide → download
- **Visual Analytics**: Interactive charts, similarity distributions, performance metrics
- **Manual Decision Override**: User control over all cleanup decisions
- **Comprehensive Reporting**: Multiple export formats with detailed analysis
- **Audit Trail**: Complete logging and audit trail for compliance

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or download the project**:

   ```bash
   cd Python
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**:

   ```bash
   python -m dedupe_system.main --version
   ```

## Usage

### Launch the GUI Interface

```bash
python -m dedupe_system.main --gui
```

This will start the Streamlit web interface at `http://localhost:8501`

### Command Line Options

```bash
python -m dedupe_system.main [OPTIONS]

Options:
  --gui                    Launch the Streamlit GUI interface (default)
  --version               Show version information
  --log-level LEVEL       Set logging level (DEBUG, INFO, WARNING, ERROR)
  --log-dir DIR           Directory for log files (default: logs)
  --help                  Show help message
```

## Using the GUI

### 1. File Upload

- Click "Browse files" to select your CSV or JSON file
- Supported formats: CSV, JSON
- Maximum file size: 100MB
- The system will automatically validate your file and show a preview

### 2. Configuration

- Select fields to use for duplicate detection
- Choose field types (text, numeric, date, phone, email) for better normalization
- Configure matching settings: exact, fuzzy, or both
- Adjust fuzzy matching threshold (50-95%)
- Select similarity algorithm (WRatio, ratio, partial_ratio, token_sort_ratio, token_set_ratio)

### 3. Duplicate Detection

- Click "Start Duplicate Detection" to begin processing
- View progress indicators and status updates
- Processing includes data normalization, exact matching, and fuzzy matching
- Real-time performance metrics and processing statistics

### 4. Results

- Review detected duplicate groups with similarity scores
- Interactive charts showing group distributions and similarity analysis
- Manual decision override for each duplicate group
- See recommended actions with ability to customize
- Download cleaned data, analysis reports, and summary statistics

## File Format Requirements

### CSV Files

- Must have header row with column names
- UTF-8 encoding recommended (auto-detection available)
- Standard CSV format with comma separators

### JSON Files

- Array of objects: `[{"field1": "value1"}, {"field2": "value2"}]`
- Object with arrays: `{"field1": ["val1", "val2"], "field2": ["val3", "val4"]}`
- UTF-8 encoding required

## System Architecture

```text
dedupe_system/
├── core/                          # Core processing components
│   ├── loader.py                 # File loading and validation
│   ├── normalizer.py             # Data normalization
│   ├── exact_matcher.py          # Exact duplicate detection
│   ├── fuzzy_matcher.py          # Fuzzy duplicate detection (RapidFuzz)
│   ├── file_duplicate_detector.py # File-level duplicate detection
│   ├── resolver.py               # Duplicate resolution
│   ├── golden_record.py          # Golden record creation with survivorship rules
│   ├── audit_logger.py           # Compliance-ready audit logging
│   ├── performance_metrics.py    # Precision, recall, accuracy calculations
│   ├── database_connector.py     # MySQL/PostgreSQL connectivity
│   ├── output_generator.py       # Results and reports
│   ├── models.py                 # Data models
│   ├── exceptions.py             # Error handling
│   └── logging_config.py         # Logging setup
├── gui/                          # Streamlit GUI interface
│   ├── app.py                    # Main GUI application (advanced)
│   ├── app_simple.py             # Simplified GUI (user-friendly)
│   └── app_clean.py              # Alternative GUI version
├── logs/                         # System and audit logs
├── outputs/                      # Generated reports and cleaned data
├── recycle_bin/                  # Recycled duplicate files
├── archive/                      # Archived duplicate files
└── main.py                       # Application entry point
```

## Data Processing Pipeline

### Record-Level Duplicate Detection
1. **File Loading**: Parse CSV/JSON/Database with encoding detection and validation
2. **Data Normalization**: Clean and standardize field values by type
3. **Duplicate Detection**: 
   - Hash-based exact matching with composite keys (O(n) complexity)
   - RapidFuzz-based fuzzy matching with blocking strategies
   - Configurable similarity thresholds and algorithms
4. **Golden Record Creation**: Apply survivorship rules for intelligent merging
5. **Results Generation**: Create duplicate groups with similarity scores and recommendations
6. **Export**: Generate cleaned datasets, analysis reports, and audit logs

### File-Level Duplicate Detection
1. **File Scanning**: Recursively scan directory tree (O(n) complexity)
2. **Size Grouping**: Group files by size for optimization (O(n) complexity)
3. **Hash Calculation**: Generate SHA-256 hashes for potential duplicates
4. **Duplicate Detection**: Identify files with identical hashes
5. **Intelligent Selection**: Choose best file based on recency, location, path depth
6. **Cleanup**: Recycle, archive, or delete duplicate files

## Field Types and Normalization

- **Text**: Lowercase, whitespace normalization, Unicode handling
- **Numeric**: Remove currency symbols, formatting characters
- **Date**: Standardize to ISO format (YYYY-MM-DD)
- **Phone**: Extract digits only, handle US number formats
- **Email**: Lowercase normalization with basic validation

## Logging and Audit Trail

The system maintains comprehensive logs in the `logs/` directory:

- `system_YYYYMMDD.log`: General system operations and debugging
- `errors_YYYYMMDD.log`: Error messages and stack traces
- `audit_YYYYMMDD_HHMMSS.log`: Structured audit trail for compliance
- `activity_YYYYMMDD_HHMMSS.log`: Detailed activity logging

## Performance Characteristics

- **Time Complexity**: 
  - O(n) for exact duplicate detection
  - O(n²) worst case for fuzzy matching (optimized with blocking strategies)
- **Memory Usage**: Approximately 2-3x input file size during processing
- **Fuzzy Matching Optimization**: Blocking strategies reduce comparisons significantly
- **Real-time Metrics**: Processing speed and efficiency tracking
- **Recommended Limits**:
  - File size: Up to 100MB
  - Records: Up to 1 million records
  - Fields: Up to 100 columns
  - Fuzzy matching: Optimized for datasets up to 100K records

## Troubleshooting

### Common Issues

1. **Import Errors**:

   ```bash
   # Make sure you're in the Python directory
   cd Python
   python -m dedupe_system.main --gui
   ```

2. **Streamlit Not Found**:

   ```bash
   pip install streamlit
   ```

3. **File Encoding Issues**:
   - Save CSV files as UTF-8
   - Use the system's automatic encoding detection

4. **Memory Issues**:
   - Process smaller files (< 50MB)
   - Close other applications to free memory

### Log Analysis

Check the logs directory for detailed error information:

```bash
# View recent errors
tail -f logs/errors_$(date +%Y%m%d).log

# View system activity
tail -f logs/system_$(date +%Y%m%d).log
```

## Development

### Running Tests

```bash
# Run core component tests
python test_loader.py
python test_normalizer.py
python test_exact_matcher.py
python test_resolver.py
python test_output_generator.py
python test_error_handling.py

# Run integration tests
python test_system_integration.py
python test_fuzzy_integration.py

# Run performance validation (validates documented metrics)
python test_performance_validation.py

# Run file duplicate detection tests
python test_file_duplicate_detection.py

# Run all tests together
python -m pytest test_*.py -v
```

### Code Structure

The system follows a modular architecture with clear separation of concerns:

- Core processing logic is independent of the GUI
- All components use dependency injection for testability
- Comprehensive error handling and logging throughout

## Current Features

### Core Functionality ✅

- **Record-Level Detection**: Both exact and fuzzy matching implemented
- **File-Level Detection**: Hash-based file duplicate detection with intelligent cleanup
- **Advanced Fuzzy Matching**: RapidFuzz with 5 configurable algorithms
- **Golden Record Creation**: Survivorship rules for intelligent merging
- **Database Connectivity**: MySQL and PostgreSQL support (optional)
- **Performance Metrics**: Precision, recall, accuracy calculations
- **Smart Performance**: Blocking strategies for large datasets
- **Interactive GUI**: Complete workflow with visual analytics
- **Advanced Visualization**: Interactive charts, similarity distributions, performance metrics
- **Manual Resolution Interface**: User decision override with batch processing
- **Comprehensive Reporting**: Multiple export formats with detailed analysis
- **Audit Trail**: Compliance-ready logging for all operations

### Technical Capabilities ✅

- **File Support**: CSV, JSON, and database connections
- **Data Validation**: Comprehensive input validation with detailed error reporting
- **Multi-Algorithm Matching**: Hash-based exact + RapidFuzz fuzzy detection
- **File Hashing**: SHA-256 for exact file duplicate detection
- **Data Normalization**: Text, numeric, date, phone, and email field normalization
- **Performance Optimized**: O(n) exact matching, blocking for fuzzy matching
- **Cleanup Strategies**: Recycle bin, archive, and delete operations
- **Real-time Processing**: Progress tracking and performance metrics

### Validated Performance ✅

- **Dataset Size**: Tested on 10,000+ records
- **Precision**: ≥0.97 (exact matching near-perfect)
- **Recall**: ≥0.94 (high duplicate detection rate)
- **Execution Time**: <5 seconds for 10,000 records
- **Throughput**: 2,000+ records/second

## Limitations

- **Batch Processing**: Single file processing only
- **Property-based Testing**: Comprehensive test suite using Hypothesis (optional enhancement)
- **Enterprise Features**: Advanced compliance and audit features

## Future Enhancements

- **Multi-file Batch Processing**: Process multiple files simultaneously
- **API Integration**: REST API for programmatic access
- **Cloud Deployment**: Docker containerization and cloud-ready deployment
- **Advanced Analytics**: Machine learning-based duplicate prediction
- **Enterprise Security**: Role-based access control and encryption

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review log files in the `logs/` directory
3. Ensure all dependencies are properly installed
4. Verify file format requirements are met

## License

MIT License

© 2026 Natasha
