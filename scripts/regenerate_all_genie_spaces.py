#!/usr/bin/env python3
"""
Regenerate ALL Genie Space JSON files from the asset inventory.

This script:
1. Reads the actual_assets_inventory.json for verified assets
2. Keeps existing sample_questions, text_instructions, benchmarks from current JSON
3. Regenerates tables, metric_views, sql_functions from inventory
4. Ensures all template variables (no hardcoded paths)
5. Validates JSON structure against Genie Space API requirements

API Limits:
- sql_functions (TVFs): Maximum 50
- benchmarks.questions: Maximum 50 (certified answer inputs)
- sample_questions: Recommended 15

Template Variables:
- ${catalog} - Unity Catalog name
- ${gold_schema} - Gold schema name
- ${feature_schema} - ML schema name
- ${gold_schema}_monitoring - Monitoring schema
"""

import json
import uuid
import re
from pathlib import Path
from typing import Dict, List, Optional, Any


def generate_id() -> str:
    """Generate a Genie Space compatible 32-char hex ID."""
    return uuid.uuid4().hex


def load_inventory(inventory_path: Path) -> Dict:
    """Load the actual assets inventory."""
    with open(inventory_path) as f:
        return json.load(f)


def load_existing_json(json_path: Path) -> Dict:
    """Load existing Genie Space JSON."""
    with open(json_path) as f:
        return json.load(f)


def clean_identifier(identifier: str) -> str:
    """
    Remove hardcoded paths and convert to template variables.
    
    Converts:
    - prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.xxx 
      → ${catalog}.${gold_schema}.xxx
    - prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_ml.xxx 
      → ${catalog}.${feature_schema}.xxx
    - prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_monitoring.xxx 
      → ${catalog}.${gold_schema}_monitoring.xxx
    """
    # Already has template variables
    if '${' in identifier:
        return identifier
    
    # Convert hardcoded paths
    identifier = re.sub(
        r'prashanth_subrahmanyam_catalog\.dev_prashanth_subrahmanyam_system_gold_monitoring\.',
        '${catalog}.${gold_schema}_monitoring.',
        identifier
    )
    identifier = re.sub(
        r'prashanth_subrahmanyam_catalog\.dev_prashanth_subrahmanyam_system_gold_ml\.',
        '${catalog}.${feature_schema}.',
        identifier
    )
    identifier = re.sub(
        r'prashanth_subrahmanyam_catalog\.dev_prashanth_subrahmanyam_system_gold\.',
        '${catalog}.${gold_schema}.',
        identifier
    )
    
    return identifier


def build_tables_section(domain_config: Dict) -> List[Dict]:
    """Build the data_sources.tables section from inventory."""
    tables = []
    
    # Add dimension tables
    for table in domain_config.get('tables', {}).get('dimensions', []):
        tables.append({
            "identifier": f"${{catalog}}.${{gold_schema}}.{table}"
        })
    
    # Add fact tables
    for table in domain_config.get('tables', {}).get('facts', []):
        tables.append({
            "identifier": f"${{catalog}}.${{gold_schema}}.{table}"
        })
    
    # Add ML tables
    for table in domain_config.get('ml_tables', []):
        tables.append({
            "identifier": f"${{catalog}}.${{feature_schema}}.{table}"
        })
    
    # Add monitoring tables
    for table in domain_config.get('monitoring_tables', []):
        tables.append({
            "identifier": f"${{catalog}}.${{gold_schema}}_monitoring.{table}"
        })
    
    return tables


def build_metric_views_section(domain_config: Dict) -> List[Dict]:
    """Build the data_sources.metric_views section from inventory."""
    views = []
    
    for mv in domain_config.get('metric_views', []):
        views.append({
            "identifier": f"${{catalog}}.${{gold_schema}}.{mv}"
        })
    
    return views


def build_sql_functions_section(domain_config: Dict, max_tvfs: int = 50) -> List[Dict]:
    """Build the instructions.sql_functions section (TVFs) from inventory."""
    functions = []
    
    tvfs = domain_config.get('tvfs', [])[:max_tvfs]
    
    for tvf in tvfs:
        functions.append({
            "id": generate_id(),
            "identifier": f"${{catalog}}.${{gold_schema}}.{tvf}"
        })
    
    return functions


def fix_sample_questions(sample_questions: List) -> List[Dict]:
    """
    Fix sample_questions to ensure correct format:
    - Must be array of objects with 'id' and 'question' (array of strings)
    """
    fixed = []
    
    for sq in sample_questions:
        if isinstance(sq, str):
            # Convert string to proper object
            fixed.append({
                "id": generate_id(),
                "question": [sq]
            })
        elif isinstance(sq, dict):
            # Ensure 'id' exists
            if 'id' not in sq or not sq['id']:
                sq['id'] = generate_id()
            
            # Ensure 'question' is an array
            if 'question' in sq and isinstance(sq['question'], str):
                sq['question'] = [sq['question']]
            
            fixed.append(sq)
    
    return fixed


def fix_text_instructions(text_instructions: List) -> List[Dict]:
    """
    Fix text_instructions to ensure correct format:
    - Must be array of objects with 'id' and 'content' (array of strings)
    """
    fixed = []
    
    for ti in text_instructions:
        if isinstance(ti, str):
            # Convert string to proper object
            fixed.append({
                "id": generate_id(),
                "content": [ti]
            })
        elif isinstance(ti, dict):
            # Ensure 'id' exists
            if 'id' not in ti or not ti['id']:
                ti['id'] = generate_id()
            
            # Ensure 'content' is an array
            if 'content' in ti and isinstance(ti['content'], str):
                ti['content'] = [ti['content']]
            
            fixed.append(ti)
    
    return fixed


def fix_benchmarks(benchmarks_questions: List, max_benchmarks: int = 50) -> List[Dict]:
    """
    Fix benchmarks.questions to ensure correct format and limit to max.
    - Must be array of objects with 'id', 'question' (array), 'answer' (array)
    """
    fixed = []
    
    for bq in benchmarks_questions[:max_benchmarks]:
        if isinstance(bq, dict):
            # Ensure 'id' exists
            if 'id' not in bq or not bq['id']:
                bq['id'] = generate_id()
            
            # Ensure 'question' is an array
            if 'question' in bq and isinstance(bq['question'], str):
                bq['question'] = [bq['question']]
            
            # Clean SQL in answers
            if 'answer' in bq:
                for answer in bq['answer']:
                    if 'content' in answer:
                        # Clean any hardcoded paths in SQL
                        cleaned_content = []
                        for line in answer['content']:
                            cleaned_content.append(clean_identifier(line))
                        answer['content'] = cleaned_content
            
            fixed.append(bq)
    
    return fixed


def regenerate_genie_space(
    domain: str,
    existing_json: Dict,
    inventory: Dict
) -> Dict:
    """
    Regenerate a Genie Space JSON using inventory for tables/views/TVFs.
    
    Preserves:
    - sample_questions (with format fixes)
    - text_instructions (with format fixes)
    - example_question_sqls
    - benchmarks (with format fixes, limited to 50)
    
    Replaces:
    - data_sources.tables (from inventory)
    - data_sources.metric_views (from inventory)
    - instructions.sql_functions (from inventory, limited to 50)
    """
    domain_config = inventory['domain_mapping'].get(domain)
    
    if not domain_config:
        raise ValueError(f"Domain '{domain}' not found in inventory")
    
    # Build new data sources and functions from inventory
    new_tables = build_tables_section(domain_config)
    new_metric_views = build_metric_views_section(domain_config)
    new_sql_functions = build_sql_functions_section(domain_config, max_tvfs=50)
    
    # Fix existing sections
    sample_questions = existing_json.get('config', {}).get('sample_questions', [])
    text_instructions = existing_json.get('instructions', {}).get('text_instructions', [])
    example_sqls = existing_json.get('instructions', {}).get('example_question_sqls', [])
    benchmarks = existing_json.get('benchmarks', {}).get('questions', [])
    
    fixed_sample_questions = fix_sample_questions(sample_questions)
    fixed_text_instructions = fix_text_instructions(text_instructions)
    fixed_benchmarks = fix_benchmarks(benchmarks, max_benchmarks=50)
    
    # Build the regenerated JSON
    regenerated = {
        "version": 1,
        "config": {
            "sample_questions": fixed_sample_questions
        },
        "data_sources": {
            "tables": new_tables,
            "metric_views": new_metric_views
        },
        "instructions": {
            "text_instructions": fixed_text_instructions
        },
        "benchmarks": {
            "questions": fixed_benchmarks
        }
    }
    
    # Add example_question_sqls if present
    if example_sqls:
        regenerated['instructions']['example_question_sqls'] = example_sqls
    
    # Add sql_functions
    regenerated['instructions']['sql_functions'] = new_sql_functions
    
    return regenerated


def main():
    base_path = Path(__file__).parent.parent
    genie_path = base_path / "src" / "genie"
    inventory_path = genie_path / "actual_assets_inventory.json"
    
    # Load inventory
    inventory = load_inventory(inventory_path)
    
    # Domain to JSON file mapping
    domain_files = {
        "cost_intelligence": "cost_intelligence_genie_export.json",
        "job_health_monitor": "job_health_monitor_genie_export.json",
        "performance": "performance_genie_export.json",
        "security_auditor": "security_auditor_genie_export.json",
        "data_quality_monitor": "data_quality_monitor_genie_export.json",
        "unified_health_monitor": "unified_health_monitor_genie_export.json",
    }
    
    print("=" * 80)
    print("REGENERATING ALL GENIE SPACE JSON FILES FROM INVENTORY")
    print("=" * 80)
    print(f"Inventory: {inventory_path}")
    print()
    
    stats = {
        "total": 0,
        "success": 0,
        "tables": 0,
        "metric_views": 0,
        "tvfs": 0,
        "benchmarks": 0
    }
    
    for domain, json_file in domain_files.items():
        stats['total'] += 1
        json_path = genie_path / json_file
        
        print(f"\n--- {domain.upper().replace('_', ' ')} ---")
        print(f"  File: {json_file}")
        
        try:
            # Load existing JSON
            existing = load_existing_json(json_path)
            
            # Get existing counts
            old_tables = len(existing.get('data_sources', {}).get('tables', []))
            old_mvs = len(existing.get('data_sources', {}).get('metric_views', []))
            old_tvfs = len(existing.get('instructions', {}).get('sql_functions', []))
            old_benchmarks = len(existing.get('benchmarks', {}).get('questions', []))
            
            # Regenerate
            regenerated = regenerate_genie_space(domain, existing, inventory)
            
            # Get new counts
            new_tables = len(regenerated['data_sources']['tables'])
            new_mvs = len(regenerated['data_sources']['metric_views'])
            new_tvfs = len(regenerated['instructions']['sql_functions'])
            new_benchmarks = len(regenerated['benchmarks']['questions'])
            
            # Update stats
            stats['tables'] += new_tables
            stats['metric_views'] += new_mvs
            stats['tvfs'] += new_tvfs
            stats['benchmarks'] += new_benchmarks
            
            print(f"  Tables: {old_tables} → {new_tables}")
            print(f"  Metric Views: {old_mvs} → {new_mvs}")
            print(f"  TVFs: {old_tvfs} → {new_tvfs}")
            print(f"  Benchmarks: {old_benchmarks} → {new_benchmarks}")
            
            # Write regenerated JSON
            with open(json_path, 'w') as f:
                json.dump(regenerated, f, indent=2)
            
            print(f"  ✅ Regenerated successfully!")
            stats['success'] += 1
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Processed: {stats['total']} Genie Spaces")
    print(f"  Successful: {stats['success']}")
    print(f"  Total Tables: {stats['tables']}")
    print(f"  Total Metric Views: {stats['metric_views']}")
    print(f"  Total TVFs: {stats['tvfs']}")
    print(f"  Total Benchmarks: {stats['benchmarks']}")
    print()
    
    if stats['success'] == stats['total']:
        print("✅ All Genie Spaces regenerated successfully!")
        print()
        print("Next steps:")
        print("  1. Review the generated JSON files")
        print("  2. Deploy: databricks bundle run -t dev genie_spaces_deployment_job")
        return 0
    else:
        print(f"❌ {stats['total'] - stats['success']} Genie Space(s) failed to regenerate")
        return 1


if __name__ == "__main__":
    exit(main())
