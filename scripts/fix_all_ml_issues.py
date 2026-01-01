#!/usr/bin/env python3
"""
Comprehensive fix for all ML training script issues.
"""
import os
import re
from pathlib import Path

ML_DIR = Path("src/ml")
fixes_applied = []

def fix_log_model_signature(filepath):
    """Fix log_model_with_feature_engineering to include X_train parameter."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Pattern: def log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, ...) without X_train
    # But function body uses X_train
    if 'X_train.head' in content or 'input_example = X_train' in content:
        # Find the function definition
        pattern = r'def log_model_with_feature_engineering\(([^)]+)\):'
        match = re.search(pattern, content)
        if match:
            params = match.group(1)
            if 'X_train' not in params:
                # Add X_train as the 4th parameter (after training_set)
                # Common patterns:
                # 1. (fe, model, training_set, metrics, hyperparams, ...)
                # 2. (fe, model, training_set, X, feature_names, ...)
                
                # Replace training_set, metrics with training_set, X_train, metrics
                if ', metrics,' in params:
                    new_params = params.replace(', metrics,', ', X_train, metrics,')
                elif ', X,' in params:
                    new_params = params.replace(', X,', ', X_train,')
                else:
                    # Add after training_set
                    new_params = params.replace('training_set,', 'training_set, X_train,')
                
                if 'X_train' not in params:  # Double check
                    content = content.replace(
                        f'def log_model_with_feature_engineering({params}):',
                        f'def log_model_with_feature_engineering({new_params}):'
                    )
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False


def fix_fe_log_model_call(filepath):
    """Add input_example and signature to fe.log_model calls."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Check if fe.log_model is missing input_example or signature
    fe_log_pattern = r'fe\.log_model\(\s*\n([^)]+?)\n\s*\)'
    matches = list(re.finditer(fe_log_pattern, content, re.DOTALL))
    
    for match in reversed(matches):  # Reverse to not mess up offsets
        fe_log_call = match.group(0)
        if 'input_example' not in fe_log_call or 'signature' not in fe_log_call:
            # Find where to insert
            inner = match.group(1)
            lines = inner.split('\n')
            
            # Check what's missing
            has_input = 'input_example' in fe_log_call
            has_sig = 'signature' in fe_log_call
            
            if not has_input or not has_sig:
                # Need to add before the closing paren
                # Look for registered_model_name line
                new_lines = []
                for i, line in enumerate(lines):
                    new_lines.append(line)
                    if 'registered_model_name=' in line:
                        indent = len(line) - len(line.lstrip())
                        if not has_input:
                            new_lines.append(' ' * indent + 'input_example=input_example,')
                        if not has_sig:
                            new_lines.append(' ' * indent + 'signature=signature')
                
                new_inner = '\n'.join(new_lines)
                new_call = f'fe.log_model(\n{new_inner}\n        )'
                content = content[:match.start()] + new_call + content[match.end():]
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False


def fix_main_function_call(filepath):
    """Fix main() to pass X_train to log_model_with_feature_engineering."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Pattern: log_model_with_feature_engineering(fe, model, training_set, metrics, ...) without X_train
    call_pattern = r'(log_model_with_feature_engineering\(.*?)(,\s*metrics,)'
    
    # Only fix if function signature has X_train but call doesn't
    if 'def log_model_with_feature_engineering' in content and 'X_train' in content:
        # Check if any call is missing X_train
        calls = re.findall(r'log_model_with_feature_engineering\([^)]+\)', content, re.DOTALL)
        for call in calls:
            if 'X_train' not in call and ', metrics,' in call:
                new_call = call.replace(', metrics,', ', X_train, metrics,')
                content = content.replace(call, new_call)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False


def ensure_input_example_and_signature(filepath):
    """Ensure input_example and signature are computed before fe.log_model."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # If fe.log_model has input_example but it's not defined in the function
    if 'input_example=input_example' in content or 'input_example = X_train' in content:
        # Check if input_example is created
        if 'input_example = X_train.head' not in content and 'input_example=X_train.head' not in content:
            # Need to add the creation block before fe.log_model
            fe_log_pos = content.find('fe.log_model(')
            if fe_log_pos > 0:
                # Find the right indent
                line_start = content.rfind('\n', 0, fe_log_pos) + 1
                indent = fe_log_pos - line_start
                
                creation_block = f'''
{' ' * indent}# Create input example and signature (REQUIRED for Unity Catalog)
{' ' * indent}input_example = X_train.head(5).astype('float64')
{' ' * indent}sample_predictions = model.predict(input_example)
{' ' * indent}signature = infer_signature(input_example, sample_predictions)
{' ' * indent}
'''
                # Only add if not already there
                if 'Create input example and signature' not in content[fe_log_pos-500:fe_log_pos]:
                    content = content[:fe_log_pos] + creation_block.lstrip() + content[fe_log_pos:]
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False


# Find all training scripts
training_scripts = list(ML_DIR.glob("**/train_*.py"))
print(f"Processing {len(training_scripts)} training scripts...\n")

for script in sorted(training_scripts):
    fixed = []
    
    if fix_log_model_signature(script):
        fixed.append("signature")
    
    if fix_fe_log_model_call(script):
        fixed.append("fe.log_model")
    
    if fix_main_function_call(script):
        fixed.append("main call")
    
    if fixed:
        print(f"✓ {script}: Fixed {', '.join(fixed)}")
        fixes_applied.append(str(script))

print(f"\n{'=' * 60}")
print(f"Fixed {len(fixes_applied)} files")
print('=' * 60)
