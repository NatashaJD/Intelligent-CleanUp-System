#!/usr/bin/env python3
"""
Simple script to run the GUI directly.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the GUI
if __name__ == "__main__":
    try:
        from dedupe_system.gui.app import main
        print("✅ GUI main function imported successfully")
        print("🚀 Starting Streamlit GUI...")
        main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Trying alternative approach...")
        
        # Alternative: run the file directly
        import subprocess
        subprocess.run([sys.executable, "-m", "streamlit", "run", "Python/dedupe_system/gui/app.py"])
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)