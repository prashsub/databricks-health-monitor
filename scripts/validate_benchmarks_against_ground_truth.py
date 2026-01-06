#!/usr/bin/env python3
"""
Validate that benchmark questions reference actual deployed assets.

Checks against ground truth documentation:
- TVFs from appendices/A-quick-reference.md
- Metric Views from 24-metric-views-reference.md
- Lakehouse Monitors from 04-monitor-catalog.md
- ML Models from 07-model-catalog.md
- Fact/Dim tables from gold_layer_design/yaml/
"""

import json
import re
from pathlib import Path
from typing import Dict, Set, List, Tuple

# ============================================================================
# Extract Ground Truth from Documentation
# ============================================================================

def extract_tvf_names() -> Set[str]:
    """Extract all deployed TVF names from quick reference."""
    tvf_ref_path = Path("docs/semantic-framework/appendices/A-quick-reference.md")
    
    if not tvf_ref_path.exists():
        print(f"⚠️  TVF reference not found: {tvf_ref_path}")
        return set()
    
    content = tvf_ref_path.read_text()
    
    # Pattern: ## Function Name: `get_xxx`
    tvf_pattern = r'## Function Name: `(get_[a-z_]+)`'
    tvfs = set(re.findall(tvf_pattern, content))
    
    print(f"✓ Found {len(tvfs)} TVFs: {sorted(tvfs)[:5]}...")
    return tvfs

def extract_metric_views() -> Set[str]:
    """Extract all deployed metric view names."""
    mv_ref_path = Path("docs/semantic-framework/24-metric-views-reference.md")
    
    if not mv_ref_path.exists():
        print(f"⚠️  Metric view reference not found: {mv_ref_path}")
        return set()
    
    content = mv_ref_path.read_text()
    
    # Pattern: ## `mv_xxx`
    mv_pattern = r'## `(mv_[a-z_]+)`'
    metric_views = set(re.findall(mv_pattern, content))
    
    print(f"✓ Found {len(metric_views)} Metric Views: {sorted(metric_views)[:5]}...")
    return metric_views

def extract_monitor_tables() -> Set[str]:
    """Extract all Lakehouse Monitor output tables."""
    monitor_catalog = Path("docs/lakehouse-monitoring-design/04-monitor-catalog.md")
    
    if not monitor_catalog.exists():
        print(f"⚠️  Monitor catalog not found: {monitor_catalog}")
        return set()
    
    content = monitor_catalog.read_text()
    
    # Monitors create two tables: {table}_profile_metrics and {table}_drift_metrics
    # Extract source tables from "Source Table" column
    source_pattern = r'\*\*Source Table\*\* \| `\{catalog\}\.\{gold_schema\}\.([a-z_]+)`'
    source_tables = set(re.findall(source_pattern, content))
    
    # Generate monitor output table names
    monitor_tables = set()
    for table in source_tables:
        monitor_tables.add(f"{table}_profile_metrics")
        monitor_tables.add(f"{table}_drift_metrics")
    
    print(f"✓ Found {len(monitor_tables)} Monitor Tables: {sorted(monitor_tables)[:5]}...")
    return monitor_tables

def extract_ml_tables() -> Set[str]:
    """Extract all ML prediction table names from model catalog."""
    ml_catalog = Path("docs/ml-framework-design/07-model-catalog.md")
    
    if not ml_catalog.exists():
        print(f"⚠️  ML model catalog not found: {ml_catalog}")
        return set()
    
    content = ml_catalog.read_text()
    
    # Pattern: | **xxx_predictions** | ... |
    # or | **xxx_scores** | ... |
    ml_pattern = r'\| \*\*([a-z_]+(?:predictions|scores|recommendations))\*\* \|'
    ml_tables = set(re.findall(ml_pattern, content))
    
    print(f"✓ Found {len(ml_tables)} ML Tables: {sorted(ml_tables)[:5]}...")
    return ml_tables

def extract_gold_tables() -> Tuple[Set[str], Set[str]]:
    """Extract fact and dimension table names from gold layer YAML."""
    yaml_dir = Path("gold_layer_design/yaml")
    
    if not yaml_dir.exists():
        print(f"⚠️  Gold layer YAML directory not found: {yaml_dir}")
        return set(), set()
    
    fact_tables = set()
    dim_tables = set()
    
    # Recursively find all YAML files
    for yaml_file in yaml_dir.rglob("*.yaml"):
        table_name = yaml_file.stem
        
        if table_name.startswith("fact_"):
            fact_tables.add(table_name)
        elif table_name.startswith("dim_"):
            dim_tables.add(table_name)
    
    print(f"✓ Found {len(fact_tables)} Fact Tables: {sorted(fact_tables)[:5]}...")
    print(f"✓ Found {len(dim_tables)} Dim Tables: {sorted(dim_tables)[:5]}...")
    
    return fact_tables, dim_tables

# ============================================================================
# Validate Benchmark Questions Against Ground Truth
# ============================================================================

def extract_referenced_assets(sql: str) -> Dict[str, List[str]]:
    """Extract all asset references from SQL query."""
    
    assets = {
        'tvfs': [],
        'metric_views': [],
        'monitor_tables': [],
        'ml_tables': [],
        'fact_tables': [],
        'dim_tables': []
    }
    
    # Extract TVF calls
    tvf_pattern = r'(?:TABLE\()?(?:\$\{catalog\}\.\$\{gold_schema\}\.|[a-z_]+\.)?(get_[a-z_]+)\('
    assets['tvfs'] = list(set(re.findall(tvf_pattern, sql)))
    
    # Extract metric view references
    mv_pattern = r'FROM (?:\$\{catalog\}\.\$\{gold_schema\}\.|[a-z_]+\.)?(mv_[a-z_]+)'
    assets['metric_views'] = list(set(re.findall(mv_pattern, sql)))
    
    # Extract monitor table references
    monitor_pattern = r'FROM (?:\$\{catalog\}\.\$\{gold_schema\}\.|[a-z_]+\.)?(fact_[a-z_]+_(?:profile_metrics|drift_metrics))'
    assets['monitor_tables'] = list(set(re.findall(monitor_pattern, sql)))
    
    # Extract ML table references
    ml_pattern = r'FROM (?:\$\{catalog\}\.\$\{feature_schema\}\.|[a-z_]+\.|[a-z_]+_ml\.)?((?:[a-z_]+_)?(?:predictions|scores|recommendations))'
    assets['ml_tables'] = list(set(re.findall(ml_pattern, sql)))
    
    # Extract fact table references
    fact_pattern = r'FROM (?:\$\{catalog\}\.\$\{gold_schema\}\.|[a-z_]+\.)?(fact_[a-z_]+)(?:\s|$|;|,)'
    assets['fact_tables'] = list(set(re.findall(fact_pattern, sql)))
    
    # Extract dim table references
    dim_pattern = r'(?:FROM|JOIN) (?:\$\{catalog\}\.\$\{gold_schema\}\.|[a-z_]+\.)?(dim_[a-z_]+)(?:\s|$|;|,)'
    assets['dim_tables'] = list(set(re.findall(dim_pattern, sql)))
    
    return assets

def validate_benchmark(question_id: str, sql: str, ground_truth: Dict) -> List[str]:
    """
    Validate a benchmark question against ground truth.
    Returns list of validation errors.
    """
    errors = []
    
    referenced = extract_referenced_assets(sql)
    
    # Check TVFs
    for tvf in referenced['tvfs']:
        if tvf not in ground_truth['tvfs']:
            errors.append(f"TVF not found: {tvf}")
    
    # Check Metric Views
    for mv in referenced['metric_views']:
        if mv not in ground_truth['metric_views']:
            errors.append(f"Metric View not found: {mv}")
    
    # Check Monitor Tables
    for monitor in referenced['monitor_tables']:
        if monitor not in ground_truth['monitor_tables']:
            errors.append(f"Monitor Table not found: {monitor}")
    
    # Check ML Tables
    for ml in referenced['ml_tables']:
        if ml not in ground_truth['ml_tables']:
            errors.append(f"ML Table not found: {ml}")
    
    # Check Fact Tables
    for fact in referenced['fact_tables']:
        if fact not in ground_truth['fact_tables']:
            errors.append(f"Fact Table not found: {fact}")
    
    # Check Dim Tables
    for dim in referenced['dim_tables']:
        if dim not in ground_truth['dim_tables']:
            errors.append(f"Dim Table not found: {dim}")
    
    return errors

def validate_genie_space(genie_space: str, ground_truth: Dict) -> Tuple[int, int, List]:
    """
    Validate all benchmarks in a Genie Space.
    Returns: (valid_count, invalid_count, errors)
    """
    
    json_path = Path(f"src/genie/{genie_space}_export.json")
    
    if not json_path.exists():
        print(f"⚠️  JSON not found: {json_path}")
        return 0, 0, []
    
    with open(json_path, 'r') as f:
        export_data = json.load(f)
    
    questions = export_data.get('benchmarks', {}).get('questions', [])
    
    print(f"\n{'='*80}")
    print(f"Validating: {genie_space} ({len(questions)} questions)")
    print(f"{'='*80}\n")
    
    valid_count = 0
    invalid_count = 0
    all_errors = []
    
    for idx, q in enumerate(questions, 1):
        question_text = q.get('question', ['Unknown'])[0] if isinstance(q.get('question'), list) else 'Unknown'
        
        if 'answer' not in q:
            continue
        
        answers = q['answer'] if isinstance(q['answer'], list) else [q['answer']]
        if not answers:
            continue
        
        answer = answers[0]
        if answer.get('format') != 'SQL':
            continue
        
        content = answer.get('content', [])
        if isinstance(content, list):
            sql = '\n'.join(content)
        else:
            sql = content
        
        # Validate against ground truth
        errors = validate_benchmark(f"Q{idx}", sql, ground_truth)
        
        if errors:
            print(f"❌ Q{idx}: {question_text[:60]}...")
            for error in errors:
                print(f"   - {error}")
            invalid_count += 1
            all_errors.append({
                'question_id': f"Q{idx}",
                'question': question_text,
                'errors': errors
            })
        else:
            print(f"✅ Q{idx}: {question_text[:60]}...")
            valid_count += 1
    
    print(f"\n✅ Valid: {valid_count}/{len(questions)}")
    print(f"❌ Invalid: {invalid_count}/{len(questions)}")
    
    return valid_count, invalid_count, all_errors

# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    
    print("="*80)
    print("Benchmark Ground Truth Validation")
    print("="*80)
    
    # Step 1: Extract ground truth
    print("\n📚 Step 1: Extracting ground truth from documentation...")
    
    ground_truth = {
        'tvfs': extract_tvf_names(),
        'metric_views': extract_metric_views(),
        'monitor_tables': extract_monitor_tables(),
        'ml_tables': extract_ml_tables(),
        'fact_tables': set(),
        'dim_tables': set()
    }
    
    fact_tables, dim_tables = extract_gold_tables()
    ground_truth['fact_tables'] = fact_tables
    ground_truth['dim_tables'] = dim_tables
    
    # Step 2: Validate each Genie Space
    print("\n🔍 Step 2: Validating benchmarks against ground truth...")
    
    genie_spaces = [
        "cost_intelligence_genie",
        "data_quality_monitor_genie",
        "job_health_monitor_genie",
        "performance_genie",
        "security_auditor_genie",
        "unified_health_monitor_genie"
    ]
    
    total_valid = 0
    total_invalid = 0
    all_space_errors = {}
    
    for genie_space in genie_spaces:
        valid, invalid, errors = validate_genie_space(genie_space, ground_truth)
        total_valid += valid
        total_invalid += invalid
        if errors:
            all_space_errors[genie_space] = errors
    
    # Step 3: Summary
    print(f"\n{'='*80}")
    print(f"Summary")
    print(f"{'='*80}")
    print(f"✅ Questions referencing valid assets: {total_valid}")
    print(f"❌ Questions referencing invalid assets: {total_invalid}")
    
    if all_space_errors:
        print(f"\n📋 Error Breakdown by Genie Space:")
        for space, errors in all_space_errors.items():
            print(f"\n  {space}: {len(errors)} errors")
            # Count error types
            error_types = {}
            for err in errors:
                for e in err['errors']:
                    error_type = e.split(':')[0]
                    error_types[error_type] = error_types.get(error_type, 0) + 1
            for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                print(f"    - {error_type}: {count}")
    
    print(f"\n{'='*80}")

if __name__ == "__main__":
    main()
