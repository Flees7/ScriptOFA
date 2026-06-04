#!/usr/bin/env python3
"""
OpenFOAM GUI Wrapper - Main Entry Point
Initializes and runs the PyQt6 application.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from gui import OpenFOAMWrapperApp


def main():
    """Initialize and run the OpenFOAM wrapper application."""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("OpenFOAM GUI Wrapper")
    app.setApplicationVersion("1.0.0")
    
    # Create and show main window
    window = OpenFOAMWrapperApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
