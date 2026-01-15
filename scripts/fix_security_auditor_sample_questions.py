#!/usr/bin/env python3
"""
Fix security_auditor_genie_export.json sample_questions format.

Issue: sample_questions have "question": "string" but API expects "question": ["string"]
Error: Expected an array for question but found "Who accessed this table?"
"""

import json

def fix_security_sample_questions():
    """Convert sample question strings to arrays."""
    
    json_file = "src/genie/security_auditor_genie_export.json"
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Fix config.sample_questions
    if "config" in data and "sample_questions" in data["config"]:
        sample_qs = data["config"]["sample_questions"]
        
        fixed_count = 0
        for sq in sample_qs:
            if "question" in sq and isinstance(sq["question"], str):
                # Convert string to array
                sq["question"] = [sq["question"]]
                fixed_count += 1
        
        print(f"✓ Fixed {fixed_count} sample questions (string → array)")
    
    # Write back
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Updated: {json_file}")


if __name__ == "__main__":
    fix_security_sample_questions()
    print("\n✅ All fixes complete!")
    print("   Deploy: databricks bundle deploy -t dev")
