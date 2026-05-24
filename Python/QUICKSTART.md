# Quickstart Guide - Intelligent Cleanup System

Get up and running in 5 minutes! 🚀

## Table of Contents
- [Installation](#installation)
- [Quick Start](#quick-start)
- [First Run](#first-run)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

---

## Installation

### Option 1: Pip Install (Recommended for Users)

```bash
# Install from PyPI
pip install intelligent-cleanup

# Verify installation
intelligent-cleanup --version
```

### Option 2: Docker (Recommended for Production)

```bash
# Run with Docker
docker run -p 8501:8501 natashjd/intelligent-cleanup:latest

# Or with Docker Compose (includes optional database)
docker-compose up -d
```

### Option 3: Development Setup

```bash
# Clone repository
git clone https://github.com/NatashaJD/Intelligent-CleanUp-System.git
cd Intelligent-CleanUp-System/Python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

---

## Quick Start

### Launch the GUI

```bash
intelligent-cleanup --gui
```

The application will open at `http://localhost:8501`

### Via Command Line

```bash
# Show help
intelligent-cleanup --help

# Show version
intelligent-cleanup --version

# Set log level
intelligent-cleanup --gui --log-level DEBUG

# Specify custom log directory
intelligent-cleanup --gui --log-dir /custom/logs
```

---

## First Run

### Step 1: Prepare Your Data

Supported formats:
- **CSV**: Standard CSV with headers
- **JSON**: Array of objects or object with arrays

Example CSV:
```csv
name,email,phone
John Doe,john@example.com,555-1234
Jon Doe,jon@example.com,555-1234
```

Example JSON:
```json
[
  {"name": "John Doe", "email": "john@example.com"},
  {"name": "Jon Doe", "email": "jon@example.com"}
]
```

### Step 2: Upload File

1. Open application at `http://localhost:8501`
2. Click "Browse files"
3. Select your CSV or JSON file
4. File preview will appear automatically

### Step 3: Configure Detection

1. **Select Fields**: Choose columns for duplicate detection
2. **Field Types**: Specify type (text, numeric, date, phone, email)
3. **Matching Method**: 
   - Exact: Identical values only
   - Fuzzy: Approximate matches (recommended)
   - Both: Most thorough
4. **Threshold**: Set similarity level (50-95%, higher = stricter)

### Step 4: Detect Duplicates

1. Click "Start Duplicate Detection"
2. Watch progress indicators
3. Results appear automatically

### Step 5: Review & Resolve

1. View detected duplicate groups
2. Each group shows similarity score
3. Review recommended actions
4. Click "Confirm" to mark duplicates
5. Download cleaned data

### Step 6: Export Results

Multiple export options:
- **Cleaned Data**: CSV/JSON with duplicates removed
- **Duplicate Report**: Detailed analysis
- **Summary Statistics**: Key metrics
- **Audit Log**: Complete compliance trail

---

## Common Tasks

### Task: Process Large File (100MB+)

```bash
# Recommended settings for large files
intelligent-cleanup --gui --log-level INFO

# In GUI:
# 1. Set threshold higher (0.95) for faster processing
# 2. Use exact matching only if possible
# 3. Process in batches if needed
```

### Task: Use with Database

```bash
# Set environment variable
export DATABASE_URL="postgresql://user:pass@localhost/db"

# Or create .env file
echo "DATABASE_URL=postgresql://user:pass@localhost/db" > .env

# Run application
intelligent-cleanup --gui
```

### Task: Integrate with Python Code

```python
from dedupe_system.core.loader import DataLoader
from dedupe_system.core.normalizer import Normalizer
from dedupe_system.core.exact_matcher import ExactMatcher

# Load data
loader = DataLoader()
df = loader.load_csv("data.csv")

# Normalize
normalizer = Normalizer()
df_normalized = normalizer.normalize_dataframe(df)

# Find exact matches
matcher = ExactMatcher()
duplicates = matcher.find_duplicates(df_normalized)

print(f"Found {len(duplicates)} duplicate groups")
```

### Task: Run Tests

```bash
# Run all tests
pytest -v

# Run specific test file
pytest test_loader.py -v

# Run with coverage
pytest --cov=dedupe_system -v

# Run specific test
pytest test_normalizer.py::TestNormalizer::test_normalize_text -v
```

### Task: Format & Lint Code

```bash
# Format code
black dedupe_system/

# Check with flake8
flake8 dedupe_system/

# Type check
mypy dedupe_system/
```

---

## Troubleshooting

### Problem: Port Already in Use

```bash
# Error: Address already in use

# Solution 1: Use different port
streamlit run dedupe_system/gui/app_simple.py --server.port 8502

# Solution 2: Kill existing process
# On Linux/Mac
lsof -i :8501
kill -9 <PID>

# On Windows
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

### Problem: Module Not Found

```bash
# Error: ModuleNotFoundError: No module named 'dedupe_system'

# Solution: Install in development mode
cd Intelligent-CleanUp-System/Python
pip install -e .
```

### Problem: Out of Memory

```bash
# Error: MemoryError

# Solution 1: Process smaller file
# Solution 2: Use exact matching only
# Solution 3: Close other applications
# Solution 4: Increase virtual memory / Docker memory limit
docker run -m 4g -p 8501:8501 intelligent-cleanup:latest
```

### Problem: Slow Processing

```bash
# Solution 1: Reduce fuzzy threshold
# Solution 2: Use exact matching only
# Solution 3: Check system resources
docker stats

# Solution 4: Check logs for errors
tail -f logs/system_$(date +%Y%m%d).log
```

### Problem: GUI Won't Load

```bash
# Error: localhost:8501 refused to connect

# Solution 1: Check if process is running
ps aux | grep streamlit

# Solution 2: Run with verbose output
intelligent-cleanup --gui --log-level DEBUG

# Solution 3: Try accessing different address
# Visit http://127.0.0.1:8501 instead of localhost

# Solution 4: Check firewall settings
# Ensure port 8501 is not blocked
```

### Problem: Database Connection Error

```bash
# Error: Unable to connect to database

# Solution 1: Verify connection string
echo $DATABASE_URL

# Solution 2: Test connection
psql $DATABASE_URL -c "SELECT 1;"

# Solution 3: Check if database is running
docker ps | grep postgres

# Solution 4: Check credentials
# Verify username, password, and database name
```

---

## Next Steps

### Learn More

- 📖 [Full Documentation](README.md)
- 🔧 [Configuration Guide](DEPLOYMENT.md)
- 👥 [Contributing Guidelines](CONTRIBUTING.md)
- 🚀 [Launch Checklist](LAUNCH_CHECKLIST.md)

### Get Help

- **GitHub Issues**: Report bugs or request features
- **GitHub Discussions**: Ask questions and share ideas
- **Documentation**: Check README and API docs

### Provide Feedback

We'd love to hear your feedback!
- Star us on GitHub ⭐
- Report issues and suggestions
- Share your experience on social media

---

## Common Commands Reference

```bash
# Installation & Setup
pip install intelligent-cleanup
intelligent-cleanup --version

# Running Application
intelligent-cleanup --gui
intelligent-cleanup --gui --log-level DEBUG

# Development
pip install -e ".[dev]"
pytest -v
black dedupe_system/
flake8 dedupe_system/

# Docker
docker build -t intelligent-cleanup:1.0.0 .
docker run -p 8501:8501 intelligent-cleanup:1.0.0
docker-compose up -d

# Help & Info
intelligent-cleanup --help
intelligent-cleanup --version
```

---

**Happy deduplicating!** 🎉

For more information, see [Full README](README.md)
