#!/usr/bin/env python3
"""
Run Python Scripts Directly

This script allows you to run Python scripts directly from any directory,
without dealing with import errors.

Usage:
    python run_directly.py src/integrate_pdfs.py
    python run_directly.py src/process_pdfs.py
    python run_directly.py src/vector_db.py
"""

import sys
import os
import importlib.util
import subprocess

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_directly.py <script_path>")
        sys.exit(1)
    
    script_path = sys.argv[1]
    
    if not os.path.exists(script_path):
        print(f"Error: Script '{script_path}' not found.")
        sys.exit(1)
    
    # Add the root directory to Python path
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Execute the script with PYTHONPATH set to include the root directory
    env = os.environ.copy()
    
    # Append to existing PYTHONPATH or create it
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{root_dir}:{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = root_dir
    
    print(f"Running script: {script_path}")
    print(f"With PYTHONPATH: {env['PYTHONPATH']}")
    
    # Run the script with the modified environment
    result = subprocess.run([sys.executable, script_path] + sys.argv[2:], env=env)
    sys.exit(result.returncode)