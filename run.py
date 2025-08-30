#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Face Recognition System Launcher
Simple script to start the application
"""

import os
import sys
import subprocess
import webbrowser
import time
from threading import Timer

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'flask', 'flask_cors', 'cv2', 'face_recognition', 
        'numpy', 'PIL'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'cv2':
                import cv2
            elif package == 'PIL':
                from PIL import Image
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Please install missing packages:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def open_browser():
    """Open browser after a delay"""
    time.sleep(2)  # Wait for server to start
    webbrowser.open('http://localhost:5000')

def main():
    """Main launcher function"""
    print("🚀 Face Recognition System Launcher")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('backend.py'):
        print("❌ Error: backend.py not found!")
        print("   Please run this script from the project directory.")
        sys.exit(1)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    print("✅ All dependencies are installed!")
    
    # Check for emotion model
    if os.path.exists('emotion_model.h5'):
        print("✅ Emotion model found!")
    else:
        print("⚠️  Emotion model not found. Using simulation mode.")
    
    # Create users directory if it doesn't exist
    if not os.path.exists('users'):
        os.makedirs('users')
        print("📁 Created users directory")
    
    print("\n🌐 Starting web server...")
    print("   URL: http://localhost:5000")
    print("   Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Open browser in a separate thread
    Timer(2.0, open_browser).start()
    
    try:
        # Start the Flask application
        from backend import app, initialize_app
        initialize_app()
        app.run(debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()