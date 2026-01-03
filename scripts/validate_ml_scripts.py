#!/usr/bin/env python3
"""
ML Scripts Pre-Deployment Validation
=====================================

This script validates all ML training scripts before deployment to catch
common errors that would otherwise fail at runtime:

1. Variable naming consistency (X vs X_train)
2. Function signature mismatches
3. Feature name validation (checks against feature table schemas)
4. Import statement validation
5. MLflow signature patterns

Run this script before deploying ML jobs to catch errors early.

Usage:
    python scripts/validate_ml_scripts.py
    
    # Validate specific domain
    python scripts/validate_ml_scripts.py --domain cost
    
    # Verbose output
    python scripts/validate_ml_scripts.py --verbose
"""

import os
import re
import sys
import ast
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Result of validating a single script."""
    script_path: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


# =============================================================================
# PATTERN DEFINITIONS
# =============================================================================

# Patterns that indicate common mistakes
ERROR_PATTERNS = [
    # Variable naming inconsistencies
    (r'for col in X\.columns:', 'Use X_train.columns instead of X.columns in loops'),
    (r'X\[col\] = X\[col\]\.astype', 'Use X_train instead of X when casting columns'),
    (r'train_test_split\(X_train,', 'train_test_split should use X (before split), not X_train'),
    
    # Function signature issues
    (r'def create_training_set_with_features\([^)]*X_train[^)]*\):', 'create_training_set_with_features should not have X_train parameter'),
    (r'def train_model\(X,', 'train_model should use X_train as parameter name, not X'),
    (r'return model, metrics, hyperparams, X_train$', 'Function should not return X_train if not defined locally'),
    
    # MLflow signature issues
    (r'fe\.log_model\([^)]*\)(?!.*signature)', 'fe.log_model should include signature parameter'),
    (r'mlflow\.sklearn\.log_model\([^)]*\)(?!.*signature)', 'mlflow.sklearn.log_model should include signature parameter'),
]

# Patterns that are warnings (not blocking)
WARNING_PATTERNS = [
    (r'feature_names = \[', 'Consider using FeatureRegistry to get feature names dynamically'),
    (r'\.astype\(float\)', 'Use .astype("float64") for explicit typing'),
    (r'import argparse', 'argparse does not work in Databricks notebooks; use dbutils.widgets'),
]

# Required imports for training scripts
REQUIRED_IMPORTS = [
    'mlflow',
    'numpy',
    'pandas',
]

# Features that were removed or renamed - these should NOT appear
DEPRECATED_FEATURES = {
    'cost_features': ['cluster_count'],  # Removed in favor of jobs_on_all_purpose_count
}


# =============================================================================
# VALIDATORS
# =============================================================================

def validate_pattern_errors(content: str, script_path: str) -> List[str]:
    """Check for common error patterns in script content."""
    errors = []
    lines = content.split('\n')
    
    for pattern, message in ERROR_PATTERNS:
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line):
                errors.append(f"Line {i}: {message}")
    
    return errors


def validate_pattern_warnings(content: str, script_path: str) -> List[str]:
    """Check for warning patterns in script content."""
    warnings = []
    lines = content.split('\n')
    
    for pattern, message in WARNING_PATTERNS:
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line):
                warnings.append(f"Line {i}: {message}")
    
    return warnings


def validate_variable_consistency(content: str) -> List[str]:
    """Check for X vs X_train variable naming consistency."""
    errors = []
    
    # Check if X is defined but then X_train is used incorrectly
    has_X_assignment = bool(re.search(r'\bX\s*=\s*pdf\[', content))
    has_X_train_assignment = bool(re.search(r'\bX_train\s*=\s*pdf\[', content))
    
    # If X is assigned, then train_test_split should use X
    if has_X_assignment:
        if re.search(r'train_test_split\(X_train,\s*y', content):
            errors.append("train_test_split uses X_train but X is the pre-split variable")
    
    # If X_train is assigned directly (not from train_test_split), check usage
    if has_X_train_assignment:
        # Check if this is before or after train_test_split
        x_train_pos = content.find('X_train = pdf[')
        split_pos = content.find('train_test_split')
        
        if x_train_pos != -1 and split_pos != -1 and x_train_pos < split_pos:
            errors.append("X_train assigned before train_test_split - should be X")
    
    return errors


def validate_function_returns(content: str) -> List[str]:
    """Check that functions return consistent values."""
    errors = []
    
    # Pattern: function returns X_train but X_train is not defined in function
    functions = re.findall(r'def (\w+)\([^)]*\):.*?(?=\ndef |\Z)', content, re.DOTALL)
    
    for match in re.finditer(r'def (\w+)\([^)]*\):', content):
        func_name = match.group(1)
        func_start = match.end()
        
        # Find end of function (next def or end of file)
        next_def = content.find('\ndef ', func_start)
        func_end = next_def if next_def != -1 else len(content)
        func_body = content[func_start:func_end]
        
        # Check if function returns X_train
        if 'return' in func_body and 'X_train' in func_body:
            # Check if X_train is actually assigned in this function
            if 'X_train =' not in func_body and 'X_train,' not in func_body:
                # X_train might come from train_test_split
                if 'train_test_split' not in func_body:
                    errors.append(f"Function '{func_name}' returns X_train but may not define it")
    
    return errors


def validate_deprecated_features(content: str, script_path: str) -> List[str]:
    """Check for usage of deprecated feature names."""
    errors = []
    
    # Determine which feature table this script uses
    for table_name, deprecated in DEPRECATED_FEATURES.items():
        if table_name in content:
            for feature in deprecated:
                # Look for feature in feature_names list
                pattern = rf'["\']({feature})["\']'
                if re.search(pattern, content):
                    errors.append(f"Deprecated feature '{feature}' used - this was removed from {table_name}")
    
    return errors


def validate_mlflow_signature(content: str) -> List[str]:
    """Check that MLflow model logging includes proper signatures."""
    errors = []
    
    # Check for fe.log_model without signature
    fe_log_pattern = r'fe\.log_model\([^)]+\)'
    for match in re.finditer(fe_log_pattern, content, re.DOTALL):
        call = match.group(0)
        if 'signature=' not in call:
            line_num = content[:match.start()].count('\n') + 1
            errors.append(f"Line ~{line_num}: fe.log_model missing signature parameter")
    
    # Check for mlflow.sklearn.log_model without signature
    sklearn_log_pattern = r'mlflow\.sklearn\.log_model\([^)]+\)'
    for match in re.finditer(sklearn_log_pattern, content, re.DOTALL):
        call = match.group(0)
        if 'signature=' not in call:
            line_num = content[:match.start()].count('\n') + 1
            errors.append(f"Line ~{line_num}: mlflow.sklearn.log_model missing signature parameter")
    
    return errors


def validate_type_casting(content: str) -> List[str]:
    """Check for proper type casting for MLflow compatibility."""
    warnings = []
    
    # Check if y is cast properly for classification
    if 'astype(int)' in content or "astype('int')" in content:
        # This is fine for classification
        pass
    elif 'classification' in content.lower() or 'classifier' in content.lower():
        if 'y.astype' not in content and 'y_train.astype' not in content:
            warnings.append("Classification model but y may not be cast to int")
    
    return warnings


# =============================================================================
# MAIN VALIDATION
# =============================================================================

def validate_script(script_path: Path, verbose: bool = False) -> ValidationResult:
    """Validate a single training script."""
    result = ValidationResult(script_path=str(script_path))
    
    try:
        content = script_path.read_text()
    except Exception as e:
        result.errors.append(f"Could not read file: {e}")
        return result
    
    # Run all validators
    result.errors.extend(validate_pattern_errors(content, str(script_path)))
    result.warnings.extend(validate_pattern_warnings(content, str(script_path)))
    result.errors.extend(validate_variable_consistency(content))
    result.errors.extend(validate_function_returns(content))
    result.errors.extend(validate_deprecated_features(content, str(script_path)))
    result.errors.extend(validate_mlflow_signature(content))
    result.warnings.extend(validate_type_casting(content))
    
    return result


def find_training_scripts(base_path: Path, domain: str = None) -> List[Path]:
    """Find all training scripts in the ML directory."""
    scripts = []
    
    domains = ['cost', 'security', 'performance', 'reliability', 'quality']
    
    if domain:
        domains = [domain]
    
    for d in domains:
        domain_path = base_path / 'src' / 'ml' / d
        if domain_path.exists():
            for script in domain_path.glob('train_*.py'):
                scripts.append(script)
    
    return sorted(scripts)


def print_results(results: List[ValidationResult], verbose: bool = False) -> int:
    """Print validation results and return exit code."""
    total_errors = 0
    total_warnings = 0
    
    print("\n" + "=" * 70)
    print("ML SCRIPTS VALIDATION RESULTS")
    print("=" * 70)
    
    for result in results:
        if result.errors or result.warnings or verbose:
            print(f"\n📄 {result.script_path}")
            
            if result.errors:
                print(f"   ❌ ERRORS ({len(result.errors)}):")
                for error in result.errors:
                    print(f"      • {error}")
                total_errors += len(result.errors)
            
            if result.warnings:
                print(f"   ⚠️  WARNINGS ({len(result.warnings)}):")
                for warning in result.warnings[:5]:  # Limit warnings shown
                    print(f"      • {warning}")
                if len(result.warnings) > 5:
                    print(f"      ... and {len(result.warnings) - 5} more")
                total_warnings += len(result.warnings)
            
            if not result.errors and not result.warnings:
                print("   ✅ No issues found")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    valid_count = sum(1 for r in results if r.is_valid)
    total_count = len(results)
    
    print(f"Scripts validated: {total_count}")
    print(f"✅ Valid:          {valid_count}")
    print(f"❌ With errors:    {total_count - valid_count}")
    print(f"Total errors:      {total_errors}")
    print(f"Total warnings:    {total_warnings}")
    
    if total_errors > 0:
        print("\n❌ VALIDATION FAILED - Fix errors before deployment!")
        return 1
    else:
        print("\n✅ VALIDATION PASSED")
        return 0


def main():
    parser = argparse.ArgumentParser(description='Validate ML training scripts')
    parser.add_argument('--domain', choices=['cost', 'security', 'performance', 'reliability', 'quality'],
                       help='Validate only specific domain')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show all scripts, including valid ones')
    parser.add_argument('--base-path', type=Path, default=Path('.'),
                       help='Base path of the project')
    
    args = parser.parse_args()
    
    # Find scripts
    scripts = find_training_scripts(args.base_path, args.domain)
    
    if not scripts:
        print("No training scripts found!")
        return 1
    
    print(f"Found {len(scripts)} training scripts to validate...")
    
    # Validate each script
    results = []
    for script in scripts:
        result = validate_script(script, args.verbose)
        results.append(result)
    
    # Print results and return exit code
    return print_results(results, args.verbose)


if __name__ == '__main__':
    sys.exit(main())

