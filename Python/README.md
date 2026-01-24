# Intelligent Duplicate Detection & Cleanup System

A comprehensive Python-based system for detecting and resolving duplicate records in CSV and JSON datasets using exact matching algorithms with an intuitive Streamlit GUI interface.

## Features

- **File Support**: CSV and JSON file formats with automatic encoding detection
- **Data Validation**: Comprehensive input validation with detailed error reporting
- **Exact Matching**: Hash-based duplicate detection with O(n) time complexity
- **Data Normalization**: Text, numeric, date, phone, and email field normalization
- **Interactive GUI**: User-friendly Streamlit interface for configuration and results
- **Audit Trail**: Complete logging and audit trail for compliance
- **Export Options**: Download cleaned data and summary reports

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
- Configure matching settings (exact matching is available in MVP)

### 3. Duplicate Detection

- Click "Start Duplicate Detection" to begin processing
- View progress indicators and status updates
- Processing includes data normalization and exact matching

### 4. Results

- Review detected duplicate groups with similarity scores
- See recommended actions for each group
- Download cleaned data and summary reports

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

```
dedupe_system/
├── core/                   # Core processing components
│   ├── loader.py          # File loading and validation
│   ├── normalizer.py      # Data normalization
│   ├── exact_matcher.py   # Duplicate detection
│   ├── resolver.py        # Duplicate resolution
│   ├── output_generator.py # Results and reports
│   ├── models.py          # Data models
│   ├── exceptions.py      # Error handling
│   └── logging_config.py  # Logging setup
├── gui/                   # Streamlit GUI interface
│   └── app.py            # Main GUI application
├── logs/                  # System and audit logs
├── outputs/              # Generated reports and cleaned data
└── main.py               # Application entry point
```

## Data Processing Pipeline

1. **File Loading**: Parse CSV/JSON with encoding detection and validation
2. **Data Normalization**: Clean and standardize field values by type
3. **Duplicate Detection**: Hash-based exact matching with composite keys
4. **Results Generation**: Create duplicate groups with similarity scores
5. **Export**: Generate cleaned datasets and audit reports

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

- **Time Complexity**: O(n) for exact duplicate detection
- **Memory Usage**: Approximately 2-3x input file size during processing
- **Recommended Limits**:
  - File size: Up to 100MB
  - Records: Up to 1 million records
  - Fields: Up to 100 columns

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
# Run existing test files
python test_loader.py
python test_normalizer.py
python test_exact_matcher.py
python test_resolver.py
python test_output_generator.py
python test_error_handling.py
```

### Code Structure

The system follows a modular architecture with clear separation of concerns:

- Core processing logic is independent of the GUI
- All components use dependency injection for testability
- Comprehensive error handling and logging throughout

## Limitations (MVP Version)

- **Fuzzy Matching**: Not implemented (planned for Phase 2)
- **Batch Processing**: Single file processing only
- **Advanced Resolution**: Manual resolution interface not fully implemented
- **Performance Optimization**: Basic implementation without advanced optimizations

## Future Enhancements (Phase 2)

- Fuzzy string matching with configurable algorithms
- Batch processing for multiple files
- Advanced duplicate resolution interface
- Performance optimizations for large datasets
- Property-based testing suite
- Advanced visualization and reporting

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review log files in the `logs/` directory
3. Ensure all dependencies are properly installed
4. Verify file format requirements are met

## License

MIT License

© 2026 Natasha
