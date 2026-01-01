#!/usr/bin/env python3
"""
Comprehensive audit of all ML training scripts to identify common error patterns.
"""
import os
import re
from pathlib import Path
from collections import defaultdict

ML_DIR = Path("src/ml")
ISSUES = defaultdict(list)

def check_file(filepath):
    """Check a single file for common issues."""
    with open(filepath, 'r') as f:
        content = f.read()
        lines = content.split('\n')
    
    rel_path = str(filepath)
    
    # Pattern 1: Function calls with X instead of X_train (excluding function defs)
    matches = re.findall(r'[^a-zA-Z_],\s*X\s*,', content)
    if matches and 'def train_isolation_forest(X' not in content and 'X: pd.DataFrame' not in content:
        ISSUES["P1: X instead of X_train in function calls"].append(rel_path)
    
    # Pattern 2: X=X in function calls
    if re.search(r'X=X[,\)]', content):
        ISSUES["P2: X=X in function calls (should be X_train=X_train)"].append(rel_path)
    
    # Pattern 3: log_model function signature mismatch
    func_def_match = re.search(r'def log_model_with_feature_engineering\([^)]+\)', content)
    if func_def_match:
        func_def = func_def_match.group(0)
        if 'X_train' not in func_def:
            # Check if function body uses X_train
            func_start = content.find('def log_model_with_feature_engineering')
            func_body = content[func_start:func_start+2000]
            if 'X_train.head' in func_body or 'input_example = X_train' in func_body:
                ISSUES["P3: log_model func uses X_train but missing from signature"].append(rel_path)
    
    # Pattern 4: prepare_and_train doesn't return X_train but log_model needs it
    prep_match = re.search(r'def prepare_and_train.*?(?=\n# COMMAND|\ndef [a-z]|\Z)', content, re.DOTALL)
    if prep_match:
        prep_func = prep_match.group(0)
        returns = re.findall(r'return\s+(.+)', prep_func)
        for ret in returns:
            if 'X_train' not in ret and 'model' in ret and 'hyperparams' in ret:
                ISSUES["P4: prepare_and_train doesn't return X_train"].append(rel_path)
                break
    
    # Pattern 5: Main function unpacks wrong number of values
    if 'model, metrics, hyperparams = prepare_and_train' in content:
        ISSUES["P5: Main unpacks 3 vals, should be 4 (include X_train)"].append(rel_path)
    
    # Pattern 6: Missing input_example in fe.log_model
    fe_log_match = re.search(r'fe\.log_model\(\s*\n[^)]+\)', content, re.DOTALL)
    if fe_log_match:
        fe_log_call = fe_log_match.group(0)
        if 'input_example' not in fe_log_call:
            ISSUES["P6: fe.log_model missing input_example"].append(rel_path)
    
    # Pattern 7: Missing signature in fe.log_model  
    if fe_log_match:
        fe_log_call = fe_log_match.group(0)
        if 'signature=' not in fe_log_call and 'signature =' not in fe_log_call:
            ISSUES["P7: fe.log_model missing signature"].append(rel_path)
    
    # Pattern 8: infer_signature not imported but used
    if 'infer_signature(' in content and 'from mlflow.models.signature import infer_signature' not in content:
        ISSUES["P8: infer_signature used but not imported"].append(rel_path)
    
    # Pattern 9: Function call passes X_train but function doesn't accept it
    call_matches = re.findall(r'log_model_with_feature_engineering\([^)]+X_train[^)]+\)', content, re.DOTALL)
    if call_matches and func_def_match and 'X_train' not in func_def_match.group(0):
        ISSUES["P9: Call passes X_train but function signature missing it"].append(rel_path)

# Find all training scripts
training_scripts = list(ML_DIR.glob("**/train_*.py"))

print(f"Scanning {len(training_scripts)} training scripts...\n")

for script in sorted(training_scripts):
    try:
        check_file(script)
    except Exception as e:
        print(f"Error scanning {script}: {e}")

print("=" * 80)
print("COMPREHENSIVE ML SCRIPT AUDIT RESULTS")
print("=" * 80)

if not ISSUES:
    print("\n✓ No issues found!")
else:
    total_issues = sum(len(files) for files in ISSUES.values())
    print(f"\n❌ Found {total_issues} issues across {len(ISSUES)} patterns:\n")
    
    for pattern, files in sorted(ISSUES.items()):
        print(f"\n{pattern}")
        print("-" * 60)
        for f in sorted(set(files)):
            print(f"  - {f}")

print("\n" + "=" * 80)
