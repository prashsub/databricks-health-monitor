#!/usr/bin/env python3
"""
Fix security_auditor sql_functions missing ID fields.

Issue: sql_functions only have {identifier}, missing required {id} field
Reference: context/genie/genie_space_export.json shows correct format with both id and identifier
"""

import json
import uuid

def fix_sql_functions():
    """Add missing id field to sql_functions."""
    
    json_file = "src/genie/security_auditor_genie_export.json"
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Fix instructions.sql_functions
    if "instructions" in data and "sql_functions" in data["instructions"]:
        sf = data["instructions"]["sql_functions"]
        
        fixed_count = 0
        for i, func in enumerate(sf):
            if "id" not in func:
                # Add missing id field
                func["id"] = uuid.uuid4().hex
                fixed_count += 1
                print(f"  sql_functions[{i}]: Added id field")
        
        if fixed_count > 0:
            print(f"\n✓ Fixed {fixed_count} sql_functions")
            print(f"\n❌ BEFORE: {{'identifier': 'catalog.schema.function'}}")
            print(f"✅ AFTER: {{'id': '...', 'identifier': 'catalog.schema.function'}}")
        else:
            print("✓ sql_functions already have id field")
    
    # Write back
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Updated: {json_file}")


if __name__ == "__main__":
    fix_sql_functions()
    print("\n✅ Fix complete!")
    print("   Reference: context/genie/genie_space_export.json")
