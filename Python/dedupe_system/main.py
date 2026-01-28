# MIT License
# Copyright (c) 2026 Judy Natasha Wambui Gachanja

"""
Main entry point for the Intelligent Duplicate Detection & Cleanup System.

This module provides the command-line interface and coordinates between
the GUI and core processing components.
"""

import argparse
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dedupe_system.core.logging_config import setup_logging, get_logger
from dedupe_system.core.exceptions import handle_error


def main():
    """Main entry point for the application."""
    
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Intelligent Duplicate Detection & Cleanup System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --gui                    # Launch Streamlit GUI
  python main.py --version               # Show version information
  python main.py --log-level DEBUG       # Enable debug logging
        """
    )
    
    parser.add_argument(
        '--gui', 
        action='store_true',
        help='Launch the Streamlit GUI interface'
    )
    
    parser.add_argument(
        '--version',
        action='store_true',
        help='Show version information'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--log-dir',
        default='logs',
        help='Directory for log files (default: logs)'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    try:
        logger = setup_logging(args.log_level, args.log_dir)
        logger.info("Starting Intelligent Duplicate Detection & Cleanup System")
        
        if args.version:
            from dedupe_system import __version__
            print(f"Intelligent Duplicate Detection & Cleanup System v{__version__}")
            return
        
        if args.gui:
            logger.info("Launching Streamlit GUI")
            launch_gui()
        else:
            # Default to GUI if no specific mode is requested
            logger.info("No mode specified, launching GUI by default")
            launch_gui()
            
    except Exception as e:
        if 'logger' in locals():
            error_msg = handle_error(logger, e, "main application")
            print(f"Error: {error_msg}")
        else:
            print(f"Failed to initialize application: {e}")
        sys.exit(1)


def launch_gui():
    """Launch the Streamlit GUI interface."""
    import subprocess
    import os
    
    # Get the path to the simple GUI app (user-friendly version)
    gui_app_path = Path(__file__).parent / "gui" / "app_simple.py"
    
    # Launch Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(gui_app_path),
            "--server.headless", "false",
            "--server.port", "8501",
            "--server.address", "localhost"
        ], check=True)
    except subprocess.CalledProcessError as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to launch Streamlit GUI: {e}")
        print("Error: Failed to launch GUI. Make sure Streamlit is installed.")
        print("Run: pip install streamlit")
        sys.exit(1)
    except KeyboardInterrupt:
        logger = get_logger(__name__)
        logger.info("Application terminated by user")
        print("\nApplication terminated.")


if __name__ == "__main__":
    main()