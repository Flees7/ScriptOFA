#!/usr/bin/env python3
"""
OpenFOAM GUI Wrapper - Main Entry Point
Initializes and runs the PyQt6 application.
"""

import sys
import os
import logging
import warnings
from pathlib import Path

# Configure environment to suppress VTK warnings before any imports
os.environ['VTK_SUPPRESS_WARNINGS'] = '1'

from PyQt6.QtWidgets import QApplication
from gui import OpenFOAMWrapperApp

# Suppress Python warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)


def setup_logging():
    """Configure logging for the application."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "foam_wrapper.log"
    
    # Create logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("OpenFOAM GUI Wrapper Started")
    logger.info("=" * 80)
    logger.info(f"Log file: {log_file}")
    
    return logger


def main():
    """Initialize and run the OpenFOAM wrapper application."""
    logger = setup_logging()
    
    logger.info("Initializing QApplication")
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("OpenFOAM GUI Wrapper")
    app.setApplicationVersion("1.0.0")
    
    logger.info("Creating main window")
    # Create and show main window
    window = OpenFOAMWrapperApp()
    window.show()
    
    logger.info("Running application")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
