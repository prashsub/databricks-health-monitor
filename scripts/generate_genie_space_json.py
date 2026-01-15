#!/usr/bin/env python3
"""
Generate Genie Space JSON files from the inventory and YAML specifications.

This script generates compliant Genie Space export JSON files by:
1. Reading the actual_assets_inventory.json for available assets
2. Reading YAML specifications from the end of spec .md files
3. Validating all referenced assets exist
4. Generating properly formatted JSON for the Genie Space API

Usage:
    python scripts/generate_genie_space_json.py [--domain DOMAIN] [--all]

Template Variables (resolved at deployment time by deploy_genie_space.py):
    ${catalog} - Unity Catalog name
    ${gold_schema} - Gold schema name  
    ${feature_schema} - ML schema name (system_gold_ml)
"""

import json
import re
import uuid
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any


def generate_id() -> str:
    """Generate a Genie Space compatible 32-char hex ID."""
    return uuid.uuid4().hex


def load_inventory(inventory_path: Path) -> Dict:
    """Load the actual assets inventory."""
    with open(inventory_path) as f:
        return json.load(f)


def extract_yaml_from_spec(spec_path: Path) -> Optional[Dict]:
    """
    Extract YAML configuration from the end of a spec markdown file.
    
    Looks for a section starting with:
    ```yaml
    # GENIE_SPACE_CONFIG
    ...
    ```
    """
    import yaml
    
    content = spec_path.read_text()
    
    # Find YAML block at end of file
    yaml_match = re.search(r'```yaml\s*\n# GENIE_SPACE_CONFIG\n(.*?)```', content, re.DOTALL)
    
    if yaml_match:
        yaml_str = yaml_match.group(1)
        return yaml.safe_load(yaml_str)
    
    return None


def validate_assets(domain_config: Dict, inventory: Dict) -> List[str]:
    """Validate that all assets in the domain config actually exist."""
    errors = []
    
    # Check tables
    all_gold_tables = (
        inventory['tables']['gold']['dimensions'] + 
        inventory['tables']['gold']['facts'] + 
        inventory['tables']['gold']['other']
    )
    all_ml_tables = inventory['tables']['ml']
    all_monitoring_tables = inventory['tables']['monitoring']
    all_metric_views = inventory['metric_views']
    all_tvfs = inventory['tvfs']
    
    # Validate dimension tables
    for table in domain_config.get('tables', {}).get('dimensions', []):
        if table not in all_gold_tables:
            errors.append(f"Dimension table '{table}' does not exist in gold schema")
    
    # Validate fact tables
    for table in domain_config.get('tables', {}).get('facts', []):
        if table not in all_gold_tables:
            errors.append(f"Fact table '{table}' does not exist in gold schema")
    
    # Validate ML tables
    for table in domain_config.get('ml_tables', []):
        if table not in all_ml_tables:
            errors.append(f"ML table '{table}' does not exist in ml schema")
    
    # Validate monitoring tables
    for table in domain_config.get('monitoring_tables', []):
        if table not in all_monitoring_tables:
            errors.append(f"Monitoring table '{table}' does not exist in monitoring schema")
    
    # Validate metric views
    for mv in domain_config.get('metric_views', []):
        if mv not in all_metric_views:
            errors.append(f"Metric view '{mv}' does not exist")
    
    # Validate TVFs
    for tvf in domain_config.get('tvfs', []):
        if tvf not in all_tvfs:
            errors.append(f"TVF '{tvf}' does not exist")
    
    return errors


def build_tables_section(domain_config: Dict) -> List[Dict]:
    """Build the data_sources.tables section."""
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
    """Build the data_sources.metric_views section."""
    views = []
    
    for mv in domain_config.get('metric_views', []):
        views.append({
            "identifier": f"${{catalog}}.${{gold_schema}}.{mv}"
        })
    
    return views


def build_sql_functions_section(domain_config: Dict) -> List[Dict]:
    """Build the instructions.sql_functions section (TVFs)."""
    functions = []
    
    for tvf in domain_config.get('tvfs', []):
        functions.append({
            "id": generate_id(),
            "identifier": f"${{catalog}}.${{gold_schema}}.{tvf}"
        })
    
    return functions


def build_sample_questions(questions: List[str]) -> List[Dict]:
    """Build the config.sample_questions section."""
    return [
        {
            "id": generate_id(),
            "question": [q]
        }
        for q in questions
    ]


def build_text_instructions(instructions: List[str]) -> List[Dict]:
    """Build the instructions.text_instructions section."""
    return [
        {
            "id": generate_id(),
            "content": instructions
        }
    ]


def build_benchmarks(benchmarks: List[Dict]) -> List[Dict]:
    """Build the benchmarks.questions section."""
    result = []
    
    for b in benchmarks:
        result.append({
            "id": generate_id(),
            "question": [b['question']],
            "answer": [
                {
                    "format": "SQL",
                    "content": [b['sql']]
                }
            ]
        })
    
    return result


def generate_genie_space_json(
    domain: str,
    inventory: Dict,
    sample_questions: List[str],
    text_instructions: List[str],
    benchmarks: List[Dict],
    max_tvfs: int = 50
) -> Dict:
    """
    Generate a complete Genie Space JSON structure.
    
    Args:
        domain: Domain name (e.g., 'cost_intelligence')
        inventory: The loaded asset inventory
        sample_questions: List of sample question strings
        text_instructions: List of instruction text
        benchmarks: List of benchmark dicts with 'question' and 'sql' keys
        max_tvfs: Maximum number of TVFs (Genie API limit is 50)
    
    Returns:
        Complete Genie Space JSON structure
    """
    domain_config = inventory['domain_mapping'].get(domain)
    
    if not domain_config:
        raise ValueError(f"Domain '{domain}' not found in inventory")
    
    # Validate assets
    errors = validate_assets(domain_config, inventory)
    if errors:
        print(f"WARNING: {len(errors)} asset validation errors for {domain}:")
        for e in errors:
            print(f"  - {e}")
    
    # Limit TVFs to max_tvfs
    tvfs = domain_config.get('tvfs', [])[:max_tvfs]
    limited_config = {**domain_config, 'tvfs': tvfs}
    
    if len(domain_config.get('tvfs', [])) > max_tvfs:
        print(f"WARNING: Truncated TVFs from {len(domain_config['tvfs'])} to {max_tvfs} (API limit)")
    
    # Build the JSON structure
    genie_space = {
        "version": 1,
        "config": {
            "sample_questions": build_sample_questions(sample_questions[:15])  # Limit to 15
        },
        "data_sources": {
            "tables": build_tables_section(limited_config),
            "metric_views": build_metric_views_section(limited_config)
        },
        "instructions": {
            "text_instructions": build_text_instructions(text_instructions),
            "sql_functions": build_sql_functions_section(limited_config)
        },
        "benchmarks": {
            "questions": build_benchmarks(benchmarks[:50])  # Limit to 50
        }
    }
    
    return genie_space


def main():
    parser = argparse.ArgumentParser(description="Generate Genie Space JSON from inventory")
    parser.add_argument('--domain', type=str, help='Generate for specific domain')
    parser.add_argument('--all', action='store_true', help='Generate for all domains')
    parser.add_argument('--validate-only', action='store_true', help='Only validate, do not generate')
    args = parser.parse_args()
    
    # Load inventory
    base_path = Path(__file__).parent.parent
    inventory_path = base_path / "src" / "genie" / "actual_assets_inventory.json"
    inventory = load_inventory(inventory_path)
    
    domains = list(inventory['domain_mapping'].keys())
    
    if args.domain:
        if args.domain not in domains:
            print(f"ERROR: Domain '{args.domain}' not found. Available: {domains}")
            return 1
        domains = [args.domain]
    elif not args.all:
        print("Usage: --domain DOMAIN or --all")
        print(f"Available domains: {', '.join(domains)}")
        return 1
    
    print("=" * 80)
    print("GENIE SPACE JSON GENERATOR")
    print("=" * 80)
    print(f"Inventory: {inventory_path}")
    print(f"Domains: {', '.join(domains)}")
    print()
    
    for domain in domains:
        print(f"\n--- {domain.upper().replace('_', ' ')} ---")
        
        domain_config = inventory['domain_mapping'][domain]
        
        # Validate assets
        errors = validate_assets(domain_config, inventory)
        
        if errors:
            print(f"  ERRORS ({len(errors)}):")
            for e in errors:
                print(f"    - {e}")
        else:
            print("  All assets validated successfully!")
        
        # Count assets
        dim_count = len(domain_config.get('tables', {}).get('dimensions', []))
        fact_count = len(domain_config.get('tables', {}).get('facts', []))
        ml_count = len(domain_config.get('ml_tables', []))
        mon_count = len(domain_config.get('monitoring_tables', []))
        mv_count = len(domain_config.get('metric_views', []))
        tvf_count = len(domain_config.get('tvfs', []))
        
        print(f"  Assets: {dim_count} dim, {fact_count} fact, {ml_count} ML, {mon_count} monitoring, {mv_count} MV, {tvf_count} TVF")
        
        if tvf_count > 50:
            print(f"  WARNING: {tvf_count} TVFs exceeds 50 limit - will be truncated")
        
        if not args.validate_only:
            # For actual generation, we'd need to read sample questions/benchmarks from spec files
            # This is a placeholder showing the structure
            print(f"  JSON generation would require spec file with YAML config")
    
    print("\n" + "=" * 80)
    print("Validation complete!")
    
    return 0


if __name__ == "__main__":
    exit(main())
