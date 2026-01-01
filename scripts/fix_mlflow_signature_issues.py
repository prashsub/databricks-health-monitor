#!/usr/bin/env python3
"""
Fix MLflow Signature Issues in Training Scripts
================================================

This script fixes the following issues that cause Unity Catalog model registration to fail:

1. DECIMAL types in features - must be cast to float64
2. DECIMAL types in labels (y) - must be cast to float64 (regression) or int (classification)
3. Missing input_example - must be defined before fe.log_model()
4. Missing signature - must be inferred with BOTH input AND output
5. Variable naming issues (X vs X_train)

Reference: https://mlflow.org/docs/latest/ml/model/signatures/#model-input-example
"""

import os
import re
from pathlib import Path

PROJECT_ROOT = Path("/Users/prashanth.subrahmanyam/Library/CloudStorage/GoogleDrive-prashanth.subrahmanyam@databricks.com/My Drive/DSA/DatabricksHealthMonitor")
ML_DIR = PROJECT_ROOT / "src" / "ml"

# Classification models (need y.astype(int))
CLASSIFICATION_MODELS = [
    "cache_hit_predictor",
    "job_failure_predictor",
    "permission_recommender",
    "compliance_risk_classifier",
    "retry_success_predictor",
    "pipeline_health_classifier",
    "failure_root_cause_analyzer",
    "schema_evolution_predictor",
    "schema_change_predictor",
    "cluster_sizing_recommender",
    "query_optimization_recommender",
    "threat_detector",
    "security_threat_detector",
    "exfiltration_detector",
    "privilege_escalation",
    "user_behavior_baseline",
    "tag_recommender",
    "access_pattern_analyzer",
]

# Regression models (need y.astype('float64'))
REGRESSION_MODELS = [
    "budget_forecaster",
    "cost_anomaly",
    "cost_anomaly_detector",
    "chargeback_attribution",
    "commitment_recommender",
    "job_cost_optimizer",
    "recovery_time_predictor",
    "job_duration_forecaster",
    "duration_forecaster",
    "dependency_impact_predictor",
    "freshness_predictor",
    "pipeline_health_scorer",
    "warehouse_optimizer",
    "resource_rightsizer",
    "query_performance_forecaster",
    "query_forecaster",
    "dbr_migration_risk_scorer",
    "cluster_efficiency_optimizer",
    "cluster_capacity_planner",
    "data_drift_detector",
    "drift_detector",
    "sla_breach_predictor",
    "failure_predictor",
    "regression_detector",
]

def is_classification_model(filepath):
    """Check if this is a classification model based on filename."""
    filename = filepath.name.lower()
    for model in CLASSIFICATION_MODELS:
        if model in filename:
            return True
    return False

def fix_y_casting(content, filepath):
    """Add proper type casting to y variable."""
    is_classification = is_classification_model(filepath)
    
    # Pattern: y = pdf[...].fillna(0) or y = pdf[...].fillna(0.5)
    # Need to add .astype() if not present
    
    if is_classification:
        # For classification, ensure y is int
        # Only fix if not already cast to int
        if re.search(r'y = pdf\[.*?\]\.fillna\(\d+\.?\d*\)(?!\s*\.astype)', content):
            # Add .astype(int) after fillna
            content = re.sub(
                r'(y = pdf\[.*?\]\.fillna\(\d+\.?\d*\))(?!\s*\.astype)',
                r'\1.astype(int)',
                content
            )
    else:
        # For regression, ensure y is float64
        # Check if y is assigned but not cast to float64
        # Look for patterns like: y = pdf["label"].fillna(0)
        # And add: y = y.astype('float64') after X_train casting
        
        # Check if already has y.astype('float64')
        if "y = y.astype('float64')" not in content and "y.astype('float64')" not in content:
            # Add y = y.astype('float64') after the y = assignment
            # Find the pattern: y = pdf[...].fillna(...)\n
            match = re.search(r"(y = pdf\[.*?\]\.fillna\([^)]+\)[^\n]*\n)", content)
            if match:
                old = match.group(1)
                new = old.rstrip() + "\n    y = y.astype('float64')  # CRITICAL: Cast to float64 for MLflow\n"
                content = content.replace(old, new, 1)
    
    return content

def fix_x_train_in_log_model(content):
    """Fix X vs X_train naming issues in log_model functions."""
    # Fix input_example=X.head(5) -> input_example=X_train.head(5)
    content = re.sub(
        r'input_example=X\.head\(5\)',
        'input_example=X_train.head(5).astype(\'float64\')',
        content
    )
    
    # Ensure X_train is used consistently
    content = re.sub(
        r'(\s+)X = pdf\[',
        r'\1X_train = pdf[',
        content
    )
    
    return content

def ensure_signature_defined(content):
    """Ensure input_example and signature are defined before fe.log_model()."""
    # Check if fe.log_model exists but input_example is not defined before it
    if 'fe.log_model(' in content:
        # Check if there's already input_example definition
        fe_log_match = re.search(r'(        fe\.log_model\()', content)
        if fe_log_match:
            # Check if input_example is defined in the same function
            func_match = re.search(r'def log_model_with_feature_engineering.*?(?=\ndef |$)', content, re.DOTALL)
            if func_match:
                func_content = func_match.group(0)
                if 'input_example = X_train.head' not in func_content:
                    # Need to add input_example and signature before fe.log_model
                    signature_code = '''        # Create input example and signature (REQUIRED for Unity Catalog)
        input_example = X_train.head(5).astype('float64')
        sample_predictions = model.predict(input_example)
        signature = infer_signature(input_example, sample_predictions)
        
'''
                    content = content.replace(
                        '        fe.log_model(',
                        signature_code + '        fe.log_model('
                    )
    
    return content

def fix_script(filepath):
    """Fix a single training script."""
    content = filepath.read_text()
    original = content
    
    # Apply fixes
    content = fix_y_casting(content, filepath)
    content = fix_x_train_in_log_model(content)
    content = ensure_signature_defined(content)
    
    if content != original:
        filepath.write_text(content)
        return True
    return False

def main():
    print("=" * 70)
    print("Fixing MLflow Signature Issues in Training Scripts")
    print("=" * 70)
    
    # Find all training scripts
    scripts = list(ML_DIR.glob("**/train_*.py"))
    print(f"\nFound {len(scripts)} training scripts")
    
    fixed = []
    for script in scripts:
        rel_path = script.relative_to(PROJECT_ROOT)
        try:
            if fix_script(script):
                fixed.append(rel_path)
                print(f"  ✓ {rel_path}")
            else:
                print(f"  · {rel_path} (no changes)")
        except Exception as e:
            print(f"  ❌ {rel_path}: {e}")
    
    print("\n" + "=" * 70)
    print(f"Fixed {len(fixed)} scripts")
    print("=" * 70)
    
    if fixed:
        print("\nFixed scripts:")
        for s in fixed:
            print(f"  - {s}")

if __name__ == "__main__":
    main()

