"""
Setup configuration for Intelligent Duplicate Detection & Cleanup System.
This enables pip installation and proper package distribution.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").split("\n")
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="intelligent-cleanup",
    version="1.0.0",
    author="Natasha",
    author_email="",
    description="Intelligent Duplicate Detection & Cleanup System for CSV, JSON, and file-level data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NatashaJD/Intelligent-CleanUp-System",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Systems Administration",
        "Topic :: Database",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "database": [
            "pymysql>=1.1.0",
            "psycopg2-binary>=2.9.0",
            "sqlalchemy>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "intelligent-cleanup=dedupe_system.main:main",
        ],
    },
)
