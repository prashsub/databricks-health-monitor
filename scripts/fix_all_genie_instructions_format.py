#!/usr/bin/env python3
"""
Fix instructions format in ALL Genie Space JSON files.

Issues:
1. text_instructions is array of strings, should be array of objects with id/content
2. sql_functions has extra fields (name, signature, full_name, description)
   Should only have id and identifier
3. Missing data_sources.tables array (should be empty array if no tables)
"""

import json
import uuid
import glob

def fix_instructions_format(json_file):
    """Fix instructions format in a single Genie Space JSON file."""
    
    print(f"\n{'='*80}")
    print(f"Processing: {json_file}")
    print(f"{'='*80}")
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    fixed_count = 0
    
    # Fix data_sources.tables (add if missing)
    if "data_sources" in data:
        ds = data["data_sources"]
        if "tables" not in ds:
            print(f"✓ Adding missing data_sources.tables array")
            ds["tables"] = []
            fixed_count += 1
    
    # Fix instructions
    if "instructions" not in data:
        print("⚠ No instructions section found")
        return fixed_count
    
    instructions = data["instructions"]
    
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
    
    print(f"\n✓ Fixed {fixed_count} section(s)")
    return fixed_count


def main():
    """Fix all Genie Space JSON files."""
    
    json_files = glob.glob("src/genie/*_genie_export.json")
    
    print(f"Found {len(json_files)} Genie Space JSON files\n")
    
    total_fixed = 0
    for json_file in sorted(json_files):
        count = fix_instructions_format(json_file)
        total_fixed += count
    
    print(f"\n{'='*80}")
    print(f"✅ All fixes complete! Total sections fixed: {total_fixed}")
    print(f"{'='*80}")
    print("   Deploy: databricks bundle deploy -t dev")
    print("   Test: databricks bundle run -t dev genie_spaces_deployment_job")


if __name__ == "__main__":
    main()
