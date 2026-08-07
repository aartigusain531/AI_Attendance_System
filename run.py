#!/usr/bin/env python3
"""
AI Attendance System - Python Application Launcher
Run this script to start the complete application
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Ensure we're in the right directory
os.chdir(Path(__file__).parent)

def check_python_version():
    """Check if Python version is 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} detected")

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import flask
        import flask_sqlalchemy
        import cv2
        import face_recognition
        import numpy
        import scipy
        print("✓ All dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nRun: python3 -m pip install -r requirements.txt --break-system-packages")
        return False

def create_folders():
    """Create required folders if they don't exist"""
    folders = [
        "dataset/faces",
        "dataset/voices",
        "uploads",
        "reports",
        "templates",
        "static"
    ]
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
    print("✓ Folders created")

def initialize_database():
    """Initialize database if needed"""
    if not Path("attendance.db").exists():
        print("Initializing database...")
        from app import app, db
        with app.app_context():
            db.create_all()
        print("✓ Database initialized")
    else:
        print("✓ Database exists")

def show_welcome():
    """Display welcome message"""
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║        🤖 AI ATTENDANCE SYSTEM - PYTHON APPLICATION        ║
║                                                            ║
║              Starting Flask Server...                      ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)

def show_info():
    """Display application info"""
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║  Application started successfully!                         ║
║                                                            ║
║  WEB INTERFACE:                                           ║
║    Local:   http://localhost:5000                         ║
║    Network: http://192.168.29.117:5000                    ║
║                                                            ║
║  DEFAULT ADMIN:                                           ║
║    Username: admin                                         ║
║    Password: admin123                                      ║
║                                                            ║
║  PRESS CTRL+C TO STOP THE SERVER                          ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)

def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("   AI ATTENDANCE SYSTEM - APPLICATION LAUNCHER")
    print("="*60 + "\n")
    
    # Checks
    print("Starting checks...\n")
    check_python_version()
    
    if not check_dependencies():
        sys.exit(1)
    
    create_folders()
    
    try:
        initialize_database()
    except Exception as e:
        print(f"⚠ Warning: {e}")
    
    # Show welcome and start
    show_welcome()
    print("\nStarting Flask application...\n")
    
    time.sleep(1)
    
    # Run Flask app
    try:
        from app import app
        show_info()
        app.run(
            debug=True,
            host="0.0.0.0",
            port=5000,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
