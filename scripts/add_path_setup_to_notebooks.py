#!/usr/bin/env python3
"""
Add sys.path Setup to Training Notebooks
=========================================

This script adds the necessary sys.path setup to enable imports from
src.ml.config and src.ml.utils in Asset Bundle deployed notebooks.

According to Databricks documentation:
https://docs.databricks.com/aws/en/notebooks/share-code#import-a-file-from-another-folder-into-a-notebook

Notebooks can import from .py files, but need sys.path setup when the
files are in a different folder.
"""

import os
import re
from pathlib import Path

# Path setup block to add after "# Databricks notebook source"
PATH_SETUP_BLOCK = '''# Databricks notebook source
# ===========================================================================
# PATH SETUP FOR ASSET BUNDLE IMPORTS
# ===========================================================================
# This enables imports from src.ml.config and src.ml.utils when deployed
# via Databricks Asset Bundles. The bundle root is computed dynamically.
# Reference: https://docs.databricks.com/aws/en/notebooks/share-code
import sys
import os

try:
    # Get current notebook path and compute bundle root
    _notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    _bundle_root = "/Workspace" + str(_notebook_path).rsplit('/src/', 1)[0]
    if _bundle_root not in sys.path:
        sys.path.insert(0, _bundle_root)
        print(f"✓ Added bundle root to sys.path: {_bundle_root}")
except Exception as e:
    print(f"⚠ Path setup skipped (local execution): {e}")
# ===========================================================================

'''

def process_notebook(file_path: Path) -> bool:
    """Add path setup block to a notebook if not already present."""
    content = file_path.read_text()
    
    # Skip if already has path setup
    if "PATH SETUP FOR ASSET BUNDLE IMPORTS" in content:
        print(f"  ⏭ Skipped (already has setup): {file_path.name}")
        return False
    
    # Check if it's a Databricks notebook
    if not content.startswith("# Databricks notebook source"):
        print(f"  ⚠ Skipped (not a notebook): {file_path.name}")
        return False
    
    # Replace the header with header + path setup
    new_content = content.replace(
        "# Databricks notebook source",
        PATH_SETUP_BLOCK.rstrip(),
        1  # Only replace first occurrence
    )
    
    file_path.write_text(new_content)
    print(f"  ✓ Updated: {file_path.name}")
    return True


def main():
    print("=" * 60)
    print("ADD PATH SETUP TO TRAINING NOTEBOOKS")
    print("=" * 60)
    
    project_root = Path(__file__).parent.parent
    ml_dir = project_root / "src" / "ml"
    
    # Find all training scripts
    training_scripts = list(ml_dir.glob("**/train_*.py"))
    
    # Also include batch inference
    inference_scripts = list((ml_dir / "inference").glob("*.py"))
    
    # Also include feature creation scripts
    feature_scripts = list((ml_dir / "features").glob("*.py"))
    
    all_scripts = training_scripts + inference_scripts + feature_scripts
    
    print(f"\nFound {len(all_scripts)} scripts to process")
    print("-" * 60)
    
    updated = 0
    skipped = 0
    
    for script in sorted(all_scripts):
        if process_notebook(script):
            updated += 1
        else:
            skipped += 1
    
    print("-" * 60)
    print(f"SUMMARY: {updated} updated, {skipped} skipped")
    print("=" * 60)


if __name__ == "__main__":
    main()

