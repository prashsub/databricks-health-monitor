#!/usr/bin/env python3
"""
Fix MLflow Signature Issues in Training Scripts
================================================

Problem: Unity Catalog requires BOTH input AND output signatures.
DECIMAL types are not supported in MLflow signatures.

Fixes:
1. Add infer_signature import
2. Cast numeric data to float64
3. Return X from prepare_and_train
4. Add input_example and signature to fe.log_model
"""

import re
from pathlib import Path

ML_DIR = Path(__file__).parent.parent / "src" / "ml"


def fix_script(script_path: Path):
    """Apply all fixes to a training script."""
    content = script_path.read_text()
    original = content
    
    # Skip if already fixed
    if "infer_signature" in content and "input_example=" in content:
        return False, "Already fixed"
    
    # Fix 1: Add infer_signature import after "import mlflow"
    if "from mlflow.models.signature import infer_signature" not in content:
        content = content.replace(
            "import mlflow\n",
            "import mlflow\nfrom mlflow.models.signature import infer_signature\n"
        )
    
    # Fix 2: Add float64 casting in prepare_and_train
    # Look for X = ... fillna(0) pattern and add casting after
    if "astype('float64')" not in content:
        # Pattern: X = pdf[...].fillna(0)...
        content = re.sub(
            r"(X = pdf\[available_features\]\.fillna\(0\)\.replace\(\[np\.inf, -np\.inf\], 0\))",
            r'''\1
    
    # CRITICAL: Cast to float64 (MLflow doesn't support DECIMAL)
    for col in X.columns:
        X[col] = X[col].astype('float64')''',
            content
        )
    
    # Fix 3: Update prepare_and_train return to include X
    # Handle both supervised and unsupervised cases
    
    # For supervised models (return model, metrics, hyperparams)
    if "return model, metrics, hyperparams\n" in content and "return model, metrics, hyperparams, X" not in content:
        content = content.replace(
            "return model, metrics, hyperparams\n",
            "return model, metrics, hyperparams, X_train\n"
        )
    
    # For unsupervised models (return model, metrics, hyperparams at end of function)
    # Also add X variable for these
    if "return model, metrics, hyperparams\n" in content:
        # Check if it's anomaly detection (no train_test_split)
        if "X_train, X_test" not in content and "model.fit(X)" in content:
            content = content.replace(
                "return model, metrics, hyperparams\n",
                "return model, metrics, hyperparams, X\n"
            )
    
    # Fix 4: Update log_model_with_feature_engineering function signature
    # Add X_train parameter
    old_sig = "def log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, catalog, feature_schema, feature_table):"
    new_sig = "def log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, catalog, feature_schema, feature_table, X_train):"
    content = content.replace(old_sig, new_sig)
    
    # Fix 5: Update the fe.log_model call to include input_example and signature
    # Find the fe.log_model block and replace it
    old_fe_log = '''fe.log_model(
            model=model,
            artifact_path="model",
            flavor=mlflow.sklearn,
            training_set=training_set,
            registered_model_name=registered_name
        )'''
    
    new_fe_log = '''# Create input example and signature (REQUIRED for Unity Catalog)
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
        )'''
    
    content = content.replace(old_fe_log, new_fe_log)
    
    # Fix 6: Update function call in main() to pass X_train
    # Handle both supervised and unsupervised
    
    # Supervised case
    old_call = "model, metrics, hyperparams = prepare_and_train(training_df, feature_names, label_col)"
    new_call = "model, metrics, hyperparams, X_train = prepare_and_train(training_df, feature_names, label_col)"
    content = content.replace(old_call, new_call)
    
    # Unsupervised case (anomaly detection - no label_col)
    old_call2 = "model, metrics, hyperparams = prepare_and_train(training_df, feature_names)"
    new_call2 = "model, metrics, hyperparams, X_train = prepare_and_train(training_df, feature_names)"
    content = content.replace(old_call2, new_call2)
    
    # Fix 7: Update the log_model_with_feature_engineering call to pass X_train
    old_log_call = "fe, model, training_set, metrics, hyperparams, \n            catalog, feature_schema, feature_table\n        )"
    new_log_call = "fe, model, training_set, metrics, hyperparams, \n            catalog, feature_schema, feature_table, X_train\n        )"
    content = content.replace(old_log_call, new_log_call)
    
    # Alternative pattern
    old_log_call2 = "fe, model, training_set, metrics, hyperparams,\n            catalog, feature_schema, feature_table\n        )"
    new_log_call2 = "fe, model, training_set, metrics, hyperparams,\n            catalog, feature_schema, feature_table, X_train\n        )"
    content = content.replace(old_log_call2, new_log_call2)
    
    if content != original:
        script_path.write_text(content)
        return True, "Fixed"
    
    return False, "No changes"


def main():
    print("=" * 60)
    print("Fixing MLflow Signature Issues in Training Scripts")
    print("=" * 60)
    
    scripts = []
    for domain in ["cost", "security", "performance", "reliability", "quality"]:
        domain_dir = ML_DIR / domain
        if domain_dir.exists():
            scripts.extend(domain_dir.glob("train_*.py"))
    
    print(f"\nFound {len(scripts)} training scripts")
    
    fixed = 0
    for script in sorted(scripts):
        modified, status = fix_script(script)
        symbol = "✓" if modified else "·"
        print(f"  {symbol} {script.parent.name}/{script.name}: {status}")
        if modified:
            fixed += 1
    
    print(f"\n{'=' * 60}")
    print(f"Fixed {fixed}/{len(scripts)} scripts")
    print("=" * 60)


if __name__ == "__main__":
    main()

