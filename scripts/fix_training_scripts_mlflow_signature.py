#!/usr/bin/env python3
"""
Fix MLflow Signature Issues in All Training Scripts
===================================================

Problem: MLflow requires both input AND output signatures for Unity Catalog models.
DECIMAL types are not supported in MLflow signatures.

Fixes Applied:
1. Cast all numeric columns to float64 in prepare_and_train
2. Return X_train from prepare_and_train
3. Add input_example and signature to fe.log_model

Reference: https://mlflow.org/docs/latest/model/signatures.html
"""

import os
import re
from pathlib import Path

# Find all training scripts
ML_DIR = Path(__file__).parent.parent / "src" / "ml"

def find_training_scripts():
    """Find all train_*.py files."""
    scripts = []
    for domain in ["cost", "security", "performance", "reliability", "quality"]:
        domain_dir = ML_DIR / domain
        if domain_dir.exists():
            scripts.extend(domain_dir.glob("train_*.py"))
    return sorted(scripts)


def fix_script(script_path: Path) -> tuple:
    """
    Apply fixes to a training script.
    
    Returns: (modified, changes_made)
    """
    content = script_path.read_text()
    original_content = content
    changes = []
    
    # Fix 1: Add float64 casting and return X_train in prepare_and_train
    # Look for pattern where we split data and train
    if "X_train, X_test, y_train, y_test = train_test_split" in content:
        if "astype('float64')" not in content:
            # Add float64 casting before train_test_split
            old_pattern = r"(X_train, X_test, y_train, y_test = train_test_split\(X, y,)"
            new_pattern = r'''# CRITICAL: Cast to float64 (MLflow doesn't support Decimal)
    for col in X.columns:
        X[col] = X[col].astype('float64')
    y = y.astype('float64')
    
    \1'''
            content = re.sub(old_pattern, new_pattern, content)
            changes.append("Added float64 casting")
    
    # Fix 2: Update prepare_and_train return to include X_train
    # Pattern: return model, metrics, hyperparams
    if "return model, metrics, hyperparams" in content and "return model, metrics, hyperparams, X_train" not in content:
        content = content.replace(
            "return model, metrics, hyperparams",
            "return model, metrics, hyperparams, X_train"
        )
        changes.append("Updated prepare_and_train return")
    
    # Fix 3: Add signature import if not present
    if "from mlflow.models.signature import infer_signature" not in content:
        # Add import after mlflow import
        if "import mlflow" in content:
            content = content.replace(
                "import mlflow",
                "import mlflow\nfrom mlflow.models.signature import infer_signature"
            )
            changes.append("Added signature import")
    
    # Fix 4: Add input_example and signature to fe.log_model
    if "fe.log_model(" in content:
        # Check if input_example is missing
        if "input_example=" not in content and "fe.log_model(" in content:
            # Find fe.log_model call and add parameters
            # This is a bit tricky - look for the pattern
            old_fe_log = r"""fe\.log_model\(
            model=model,
            artifact_path="model",
            flavor=mlflow\.sklearn,
            training_set=training_set,.*?
            registered_model_name=registered_name
        \)"""
            
            new_fe_log = """# Create input example and signature (REQUIRED for Unity Catalog)
        input_example = X_train.head(5).astype('float64')
        sample_predictions = model.predict(input_example)
        signature = infer_signature(input_example, sample_predictions)
        
        fe.log_model(
            model=model,
            artifact_path="model",
            flavor=mlflow.sklearn,
            training_set=training_set,
            registered_model_name=registered_name,
            input_example=input_example,
            signature=signature
        )"""
            
            content = re.sub(old_fe_log, new_fe_log, content, flags=re.MULTILINE | re.DOTALL)
            changes.append("Added input_example and signature to fe.log_model")
    
    # Fix 5: Update main() to receive X_train and pass it
    # Pattern: model, metrics, hyperparams = prepare_and_train(...)
    if "model, metrics, hyperparams = prepare_and_train" in content and "model, metrics, hyperparams, X_train = prepare_and_train" not in content:
        content = content.replace(
            "model, metrics, hyperparams = prepare_and_train",
            "model, metrics, hyperparams, X_train = prepare_and_train"
        )
        changes.append("Updated main() to receive X_train")
    
    # Fix 6: Add X_train parameter to log_model_with_feature_engineering call
    # This is more complex - need to find the function call and add X_train
    if ", X_train)" not in content and "log_model_with_feature_engineering(" in content:
        # Find the call pattern
        pattern = r"(log_model_with_feature_engineering\([^)]+)(feature_table\))"
        if re.search(pattern, content):
            content = re.sub(pattern, r"\1feature_table, X_train)", content)
            changes.append("Added X_train to log_model_with_feature_engineering call")
    
    # Fix 7: Update function signature of log_model_with_feature_engineering
    if "def log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, catalog, feature_schema, feature_table):" in content:
        content = content.replace(
            "def log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, catalog, feature_schema, feature_table):",
            "def log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, catalog, feature_schema, feature_table, X_train):"
        )
        changes.append("Updated log_model_with_feature_engineering signature")
    
    if content != original_content:
        script_path.write_text(content)
        return True, changes
    
    return False, changes


def main():
    scripts = find_training_scripts()
    print(f"Found {len(scripts)} training scripts")
    print("=" * 60)
    
    modified_count = 0
    for script in scripts:
        modified, changes = fix_script(script)
        if modified:
            modified_count += 1
            print(f"\n✓ {script.name}")
            for change in changes:
                print(f"  - {change}")
        else:
            print(f"  {script.name} (no changes needed or already fixed)")
    
    print("\n" + "=" * 60)
    print(f"Modified {modified_count}/{len(scripts)} scripts")
    print("=" * 60)


if __name__ == "__main__":
    main()

