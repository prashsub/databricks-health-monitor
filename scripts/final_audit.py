#!/usr/bin/env python3
"""Final comprehensive audit."""
import re
from pathlib import Path
from collections import defaultdict

ML_DIR = Path("src/ml")
ISSUES = defaultdict(list)

def check_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    rel_path = str(filepath)
    
    # Check 1: log_model function uses X_train but missing from signature
    func_match = re.search(r'def log_model_with_feature_engineering\(([^)]+)\)', content)
    if func_match:
        params = func_match.group(1)
        func_start = content.find('def log_model_with_feature_engineering')
        func_body = content[func_start:func_start+2000]
        if 'X_train.head' in func_body and 'X_train' not in params:
            ISSUES["Function uses X_train but missing from signature"].append(rel_path)
    
    # Check 2: fe.log_model missing input_example
    fe_log = re.search(r'fe\.log_model\([^)]+\)', content, re.DOTALL)
    if fe_log:
        call = fe_log.group(0)
        if 'input_example' not in call:
            ISSUES["fe.log_model missing input_example"].append(rel_path)
        if 'signature' not in call:
            ISSUES["fe.log_model missing signature"].append(rel_path)
    
    # Check 3: X=X patterns
    if re.search(r'[^_a-zA-Z]X=X[,\)]', content):
        ISSUES["X=X should be X_train=X_train"].append(rel_path)
    
    # Check 4: Passing X_train to function that doesn't accept it
    call_matches = re.findall(r'log_model_with_feature_engineering\([^)]+\)', content, re.DOTALL)
    for call in call_matches:
        if 'X_train' in call and func_match and 'X_train' not in func_match.group(1):
            ISSUES["Call passes X_train but function doesn't accept it"].append(rel_path)

for script in sorted(ML_DIR.glob("**/train_*.py")):
    check_file(script)

print("=" * 70)
print("FINAL AUDIT RESULTS")
print("=" * 70)

if not ISSUES:
    print("\n✅ ALL CHECKS PASSED - No issues found!")
else:
    total = sum(len(v) for v in ISSUES.values())
    print(f"\n❌ Found {total} remaining issues:\n")
    for issue, files in sorted(ISSUES.items()):
        print(f"\n{issue}:")
        for f in sorted(set(files)):
            print(f"  - {f}")

print("\n" + "=" * 70)
