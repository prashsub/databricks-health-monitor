#!/usr/bin/env python3
"""
Fix cost_intelligence instructions format to match API spec.

Issues:
1. text_instructions is array of strings, should be array of objects with id/content
2. sql_functions has extra fields (name, signature, full_name, description)
   Should only have id and identifier
"""

import json
import uuid

def fix_instructions_format():
    """Fix instructions format in cost_intelligence."""
    
    json_file = "src/genie/cost_intelligence_genie_export.json"
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    if "instructions" not in data:
        print("⚠ No instructions section found")
        return
    
    instructions = data["instructions"]
    fixed_count = 0
    
    # Fix text_instructions format
    if "text_instructions" in instructions:
        text_inst = instructions["text_instructions"]
        
        if text_inst and isinstance(text_inst[0], str):
            # Convert array of strings to array of objects
            print(f"✓ Converting {len(text_inst)} text_instructions from strings to objects")
            
            # Combine all strings into a single instruction
            combined_text = "\n".join(text_inst)
            
            instructions["text_instructions"] = [
                {
                    "id": uuid.uuid4().hex,
                    "content": [combined_text]
                }
            ]
            fixed_count += 1
        else:
            print("  text_instructions already in correct format")
    
    # Fix sql_functions format
    if "sql_functions" in instructions:
        sql_funcs = instructions["sql_functions"]
        
        if sql_funcs and len(sql_funcs) > 0:
            # Check if they have extra fields
            first_func = sql_funcs[0]
            extra_fields = [f for f in first_func.keys() if f not in ["id", "identifier"]]
            
            if extra_fields:
                print(f"✓ Removing extra fields from sql_functions: {extra_fields}")
                
                cleaned_funcs = []
                for func in sql_funcs:
                    cleaned = {
                        "id": func.get("id", uuid.uuid4().hex),
                        "identifier": func.get("identifier") or func.get("full_name") or func.get("name")
                    }
                    cleaned_funcs.append(cleaned)
                
                instructions["sql_functions"] = cleaned_funcs
                fixed_count += 1
            else:
                print("  sql_functions already in correct format")
    
    # Write back
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Updated: {json_file}")
    print(f"   Fixed {fixed_count} section(s)")


if __name__ == "__main__":
    fix_instructions_format()
    print("\n✅ All fixes complete!")
    print("   Deploy: databricks bundle deploy -t dev")
