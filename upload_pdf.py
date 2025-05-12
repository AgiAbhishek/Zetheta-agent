#!/usr/bin/env python3
"""
PDF Upload Utility for Zetheta AI Assistant

This script helps you upload PDF files to the data/raw_files directory
and process them for use with the AI assistant.

Usage:
    python upload_pdf.py [file1.pdf file2.pdf ...]
"""

import os
import sys
import shutil
from pathlib import Path
import logging

from src.process_pdfs import process_all_pdfs
from src.integrate_pdfs import integrate_documents

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
RAW_FILES_DIR = Path('data/raw_files')
PROCESSED_FILES_DIR = Path('data/processed_files')

def ensure_directories():
    """Make sure the necessary directories exist."""
    RAW_FILES_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_FILES_DIR.mkdir(parents=True, exist_ok=True)
    
def copy_file(src_path, dest_dir):
    """
    Copy a file to the destination directory.
    
    Args:
        src_path (str or Path): Source file path
        dest_dir (Path): Destination directory
        
    Returns:
        Path: Path to the copied file or None if failed
    """
    src_path = Path(src_path)
    
    if not src_path.exists():
        logger.error(f"File not found: {src_path}")
        return None
    
    if not src_path.is_file():
        logger.error(f"Not a file: {src_path}")
        return None
    
    if src_path.suffix.lower() != '.pdf':
        logger.error(f"Not a PDF file: {src_path}")
        return None
    
    dest_path = dest_dir / src_path.name
    
    try:
        shutil.copy2(src_path, dest_path)
        logger.info(f"Copied {src_path} to {dest_path}")
        return dest_path
    except Exception as e:
        logger.error(f"Error copying file: {str(e)}")
        return None

def main():
    """Main entry point for the script."""
    # Check if files were specified
    if len(sys.argv) < 2:
        print(__doc__)
        print("Error: No PDF files specified.")
        print("Example: python upload_pdf.py document1.pdf document2.pdf")
        return 1
    
    # Ensure directories
    ensure_directories()
    
    # Copy each file
    success_count = 0
    for file_path in sys.argv[1:]:
        if copy_file(file_path, RAW_FILES_DIR):
            success_count += 1
    
    logger.info(f"Copied {success_count}/{len(sys.argv)-1} files to {RAW_FILES_DIR}")
    
    # Process the PDFs
    if success_count > 0:
        logger.info("Processing PDF files...")
        total, processed = process_all_pdfs()
        logger.info(f"Processed {processed}/{total} PDF files")
        
        if processed > 0:
            logger.info(f"PDF files processed and ready for use with the AI assistant")
            logger.info(f"Processed data stored in {PROCESSED_FILES_DIR}")
            
            # Integrate with vector database
            logger.info("Integrating documents with vector database...")
            if integrate_documents():
                logger.info("Successfully integrated documents into vector database")
            else:
                logger.error("Failed to integrate documents into vector database")
        else:
            logger.error("Failed to process any PDF files")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())