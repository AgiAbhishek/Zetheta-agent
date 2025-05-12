#!/usr/bin/env python3
"""
Update Vector Index

This simple wrapper script lets you update the vector database directly.
It processes all documents and creates/updates the FAISS index.

Usage:
    python update_index.py
"""

import sys
import os

# Add the project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Updating vector index...")
    # Just import and run the main function from vector_db.py
    import src.vector_db
    print("\nIndex update complete!")