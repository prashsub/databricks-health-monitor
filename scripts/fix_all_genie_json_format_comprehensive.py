#!/usr/bin/env python3
"""
Comprehensive fix for ALL Genie Space JSON format issues.

Converts from custom/legacy format to Databricks API format:
1. sample_questions: array of strings → array of objects with id/question
2. metric_views: {id, name, full_name} → {identifier}
3. text_instructions: array of strings → array of objects with id/content
4. sql_functions: {id, name, signature, full_name} → {id, identifier}
5. tables: ensures {identifier} format
"""

import json
import uuid
from pathlib import Path

# Template variable mappings
CATALOG = "prashanth_subrahmanyam_catalog"
GOLD_SCHEMA = "dev_prashanth_subrahmanyam_system_gold"
FEATURE_SCHEMA = "dev_prashanth_subrahmanyam_system_gold_ml"
MONITORING_SCHEMA = "dev_prashanth_subrahmanyam_system_gold_monitoring"

def gen_id():
    return uuid.uuid4().hex

def fix_sample_questions(config: dict) -> int:
    """Fix sample_questions from array of strings to array of objects."""
    if 'sample_questions' not in config:
        return 0
    
    sq = config['sample_questions']
    if not sq:
        return 0
    
    # Check if already in correct format
    if isinstance(sq[0], dict) and 'id' in sq[0] and 'question' in sq[0]:
        return 0
    
    # Convert strings to objects
    fixed = []
    for q in sq:
        if isinstance(q, str):
            fixed.append({
                'id': gen_id(),
                'question': [q]
            })
        else:
            fixed.append(q)
    
    config['sample_questions'] = fixed
    return len(fixed)

def fix_metric_views(data_sources: dict) -> int:
    """Fix metric_views from {id, name, full_name} to {identifier}."""
    if 'metric_views' not in data_sources:
        return 0
    
    mvs = data_sources['metric_views']
    count = 0
    
    for mv in mvs:
        if 'full_name' in mv and 'identifier' not in mv:
            # Convert full_name to identifier
            mv['identifier'] = mv['full_name']
            # Remove old fields
            mv.pop('full_name', None)
            mv.pop('id', None)
            mv.pop('name', None)
            count += 1
    
    return count

def fix_text_instructions(instructions: dict) -> int:
    """Fix text_instructions from array of strings to array of objects."""
    if 'text_instructions' not in instructions:
        return 0
    
    ti = instructions['text_instructions']
    if not ti:
        return 0
    
    # Check if already in correct format
    if isinstance(ti[0], dict) and 'id' in ti[0] and 'content' in ti[0]:
        return 0
    
    # If array of strings, combine into single instruction
    if isinstance(ti[0], str):
        instructions['text_instructions'] = [{
            'id': gen_id(),
            'content': ti
        }]
        return 1
    
    return 0

def fix_sql_functions(instructions: dict) -> int:
    """Fix sql_functions from {id, name, full_name} to {id, identifier}."""
    if 'sql_functions' not in instructions:
        return 0
    
    funcs = instructions['sql_functions']
    count = 0
    
    for func in funcs:
        # Ensure id exists
        if 'id' not in func:
            func['id'] = gen_id()
            count += 1
        
        # Convert full_name/name to identifier
        if 'identifier' not in func:
            if 'full_name' in func:
                # full_name might just be function name, need to add schema
                name = func['full_name']
                if '.' not in name:
                    func['identifier'] = f"${{catalog}}.${{gold_schema}}.{name}"
                else:
                    func['identifier'] = name
            elif 'name' in func:
                func['identifier'] = f"${{catalog}}.${{gold_schema}}.{func['name']}"
            count += 1
        
        # Remove old fields
        func.pop('full_name', None)
        func.pop('name', None)
        func.pop('signature', None)
        func.pop('description', None)  # Not needed in API format
    
    return count

def fix_tables(data_sources: dict) -> int:
    """Ensure tables have identifier format."""
    if 'tables' not in data_sources:
        return 0
    
    tables = data_sources['tables']
    count = 0
    
    for table in tables:
        if 'identifier' not in table and 'full_name' in table:
            table['identifier'] = table['full_name']
            table.pop('full_name', None)
            count += 1
    
    return count

def fix_genie_space(json_file: Path) -> dict:
    """Fix a single Genie Space JSON file."""
    data = json.load(open(json_file))
    
    results = {
        'sample_questions': 0,
        'metric_views': 0,
        'text_instructions': 0,
        'sql_functions': 0,
        'tables': 0
    }
    
    # Fix config section
    if 'config' in data:
        results['sample_questions'] = fix_sample_questions(data['config'])
        # Remove name/description from config (they go in outer wrapper)
        data['config'].pop('name', None)
        data['config'].pop('description', None)
    
    # Fix data_sources section
    if 'data_sources' in data:
        results['metric_views'] = fix_metric_views(data['data_sources'])
        results['tables'] = fix_tables(data['data_sources'])
    
    # Fix instructions section
    if 'instructions' in data:
        results['text_instructions'] = fix_text_instructions(data['instructions'])
        results['sql_functions'] = fix_sql_functions(data['instructions'])
    
    # Save
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    return results

def main():
    genie_files = [
        Path("src/genie/cost_intelligence_genie_export.json"),
        Path("src/genie/security_auditor_genie_export.json"),
        Path("src/genie/performance_genie_export.json"),
        Path("src/genie/job_health_monitor_genie_export.json"),
        Path("src/genie/data_quality_monitor_genie_export.json"),
        Path("src/genie/unified_health_monitor_genie_export.json")
    ]
    
    print("=" * 80)
    print("COMPREHENSIVE GENIE SPACE JSON FORMAT FIX")
    print("=" * 80)
    print()
    
    total_fixes = {
        'sample_questions': 0,
        'metric_views': 0,
        'text_instructions': 0,
        'sql_functions': 0,
        'tables': 0
    }
    
    for json_file in genie_files:
        name = json_file.stem.replace('_export', '').replace('_genie', '').replace('_', ' ').title()
        print(f"Fixing: {name}")
        
        results = fix_genie_space(json_file)
        
        for key, count in results.items():
            total_fixes[key] += count
            if count > 0:
                print(f"  ✅ {key}: {count} fixed")
        
        print()
    
    print("=" * 80)
    print("TOTAL FIXES:")
    print("=" * 80)
    for key, count in total_fixes.items():
        if count > 0:
            print(f"  {key}: {count}")
    print(f"\n  TOTAL: {sum(total_fixes.values())}")

if __name__ == "__main__":
    main()
