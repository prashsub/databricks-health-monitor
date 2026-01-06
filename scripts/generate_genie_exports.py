#!/usr/bin/env python3
"""
Generate Genie Space Export JSON files from markdown documentation.

This script reads the structured markdown files and generates corresponding
JSON export files following the GenieSpaceExport schema.
"""

import json
import re
import uuid
from pathlib import Path
from typing import List, Dict, Tuple

def generate_id():
    """Generate a Genie Space compatible ID (32 hex chars without dashes)."""
    return uuid.uuid4().hex

def extract_sample_questions(content: str) -> List[Dict]:
    """Extract sample questions from SECTION C."""
    pattern = r'## ████ SECTION C:.*?(?=## ████ SECTION D:)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return []
    
    section = match.group(0)
    questions = []
    
    # Extract numbered questions
    lines = section.split('\n')
    for line in lines:
        # Match pattern like: 1. "What is our total spend this month?"
        q_match = re.match(r'^\d+\.\s+"([^"]+)"', line.strip())
        if q_match:
            questions.append({
                "id": generate_id(),
                "question": [q_match.group(1)]
            })
    
    return questions[:15]  # Limit to first 15 for sample questions

def extract_tvf_identifiers(content: str, catalog: str, schema: str) -> List[Dict]:
    """Extract TVF identifiers from markdown."""
    pattern = r'\|\s+`([^`]+)`\s+\|'
    matches = re.findall(pattern, content)
    
    tvfs = []
    for match in matches:
        if match.startswith('get_'):
            tvfs.append({
                "id": generate_id(),
                "identifier": f"{catalog}.{schema}.{match}"
            })
    
    return sorted(tvfs, key=lambda x: x['identifier'])

def extract_metric_views(content: str, catalog: str, schema: str) -> List[Dict]:
    """Extract metric view identifiers from markdown."""
    pattern = r'\|\s+`([^`]+)`\s+\|.*?\|.*?\|'
    section_pattern = r'### Metric Views \(PRIMARY.*?(?=###)'
    
    match = re.search(section_pattern, content, re.DOTALL)
    if not match:
        return []
    
    section = match.group(0)
    metric_views = []
    
    for line in section.split('\n'):
        if line.strip().startswith('|') and '`' in line:
            parts = [p.strip() for p in line.split('|')]
            for part in parts:
                m = re.search(r'`([^`]+)`', part)
                if m and not m.group(1).startswith('get_'):
                    mv_name = m.group(1)
                    metric_views.append({
                        "identifier": f"{catalog}.{schema}.{mv_name}",
                        "column_configs": []
                    })
                    break
    
    return sorted(metric_views, key=lambda x: x['identifier'])

def extract_ml_tables(content: str, catalog: str, ml_schema: str) -> List[Dict]:
    """Extract ML prediction table identifiers from markdown."""
    pattern = r'### ML Prediction Tables.*?(?=###|\n## )'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return []
    
    section = match.group(0)
    ml_tables = []
    
    # Extract table names from markdown table rows
    for line in section.split('\n'):
        if line.strip().startswith('|') and '`' in line and not line.strip().startswith('| Table'):
            parts = [p.strip() for p in line.split('|')]
            for part in parts[:2]:  # Check first two columns
                m = re.search(r'`([^`]+)`', part)
                if m:
                    table_name = m.group(1)
                    ml_tables.append({
                        "identifier": f"{catalog}.{ml_schema}.{table_name}",
                        "description": ["ML prediction table"],
                        "column_configs": [
                            {"column_name": "prediction", "description": ["Predicted value"]},
                            {"column_name": "prediction_date", "description": ["Date of prediction"]},
                            {"column_name": "workspace_id", "description": ["Workspace identifier"]}
                        ]
                    })
                    break
    
    return sorted(ml_tables, key=lambda x: x['identifier'])

def extract_monitoring_tables(content: str, catalog: str, schema: str) -> List[Dict]:
    """Extract Lakehouse Monitoring table identifiers from markdown."""
    pattern = r'### Lakehouse Monitoring Tables.*?(?=###|\n## )'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return []
    
    section = match.group(0)
    monitoring_tables = []
    
    for line in section.split('\n'):
        if line.strip().startswith('|') and '`' in line and '_profile_metrics' in line or '_drift_metrics' in line:
            parts = [p.strip() for p in line.split('|')]
            for part in parts[:2]:
                m = re.search(r'`([^`]+)`', part)
                if m:
                    table_name = m.group(1)
                    monitoring_tables.append({
                        "identifier": f"{catalog}.{schema}.{table_name}",
                        "description": ["Lakehouse monitoring metrics"],
                        "column_configs": []
                    })
                    break
    
    return sorted(monitoring_tables, key=lambda x: x['identifier'])

def extract_dimension_fact_tables(content: str, catalog: str, schema: str) -> Tuple[List[Dict], List[Dict]]:
    """Extract dimension and fact tables from markdown."""
    dim_tables = []
    fact_tables = []
    
    # Extract dimension tables
    dim_pattern = r'### Dimension Tables.*?(?=###)'
    dim_match = re.search(dim_pattern, content, re.DOTALL)
    if dim_match:
        section = dim_match.group(0)
        for line in section.split('\n'):
            if line.strip().startswith('|') and '`' in line and 'dim_' in line:
                parts = [p.strip() for p in line.split('|')]
                for part in parts[:2]:
                    m = re.search(r'`([^`]+)`', part)
                    if m:
                        table_name = m.group(1)
                        dim_tables.append({
                            "identifier": f"{catalog}.{schema}.{table_name}",
                            "description": ["Dimension table"],
                            "column_configs": []
                        })
                        break
    
    # Extract fact tables
    fact_pattern = r'### Fact Tables.*?(?=###)'
    fact_match = re.search(fact_pattern, content, re.DOTALL)
    if fact_match:
        section = fact_match.group(0)
        for line in section.split('\n'):
            if line.strip().startswith('|') and '`' in line and 'fact_' in line:
                parts = [p.strip() for p in line.split('|')]
                for part in parts[:2]:
                    m = re.search(r'`([^`]+)`', part)
                    if m:
                        table_name = m.group(1)
                        fact_tables.append({
                            "identifier": f"{catalog}.{schema}.{table_name}",
                            "description": ["Fact table"],
                            "column_configs": []
                        })
                        break
    
    return (
        sorted(dim_tables, key=lambda x: x['identifier']),
        sorted(fact_tables, key=lambda x: x['identifier'])
    )

def extract_benchmark_questions(content: str, catalog: str, schema: str) -> List[Dict]:
    """Extract benchmark questions with SQL from SECTION G/H."""
    benchmarks = []
    
    # Extract all benchmark questions
    pattern = r'### Question \d+:.*?```sql\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    # Also extract questions
    q_pattern = r'### Question \d+: "([^"]+)"'
    questions = re.findall(q_pattern, content)
    
    for i, (sql, question) in enumerate(zip(matches, questions)):
        # Split SQL into lines and add newline markers
        sql_lines = [line + "\n" for line in sql.strip().split('\n')]
        
        benchmarks.append({
            "id": generate_id(),
            "question": [question],
            "answer": [{
                "format": "SQL",
                "content": sql_lines
            }]
        })
    
    return benchmarks

def generate_text_instructions(content: str) -> str:
    """Generate text instructions from SECTION F."""
    pattern = r'## ████ SECTION F:.*?```\n(.*?)```'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return ""
    
    return match.group(1).strip()

def generate_genie_export(
    md_file: Path,
    catalog: str = "${catalog}",
    gold_schema: str = "${gold_schema}",
    feature_schema: str = "${feature_schema}"
) -> Dict:
    """Generate a complete Genie Space export JSON from markdown."""
    
    with open(md_file, 'r') as f:
        content = f.read()
    
    # Extract all sections
    sample_questions = extract_sample_questions(content)
    metric_views = extract_metric_views(content, catalog, gold_schema)
    tvfs = extract_tvf_identifiers(content, catalog, gold_schema)
    ml_tables = extract_ml_tables(content, catalog, feature_schema)
    monitoring_tables = extract_monitoring_tables(content, catalog, gold_schema)
    dim_tables, fact_tables = extract_dimension_fact_tables(content, catalog, gold_schema)
    benchmarks = extract_benchmark_questions(content, catalog, gold_schema)
    text_instructions = generate_text_instructions(content)
    
    # Combine all tables
    all_tables = ml_tables + monitoring_tables + dim_tables + fact_tables
    all_tables = sorted(all_tables, key=lambda x: x['identifier'])
    
    # Build the export structure
    export = {
        "version": 1,
        "config": {
            "sample_questions": sample_questions
        },
        "data_sources": {
            "tables": all_tables,
            "metric_views": metric_views
        },
        "instructions": {
            "sql_functions": tvfs,
            "text_instructions": [{
                "id": generate_id(),
                "content": [text_instructions + "\n"]
            }]
        },
        "benchmarks": {
            "questions": benchmarks
        }
    }
    
    return export

def main():
    """Generate all Genie Space exports."""
    src_dir = Path(__file__).parent.parent / "src" / "genie"
    
    # Genie Space markdown files
    spaces = [
        "data_quality_monitor_genie.md",
        "performance_genie.md",
        "security_auditor_genie.md",
        "unified_health_monitor_genie.md"
    ]
    
    for space_md in spaces:
        md_path = src_dir / space_md
        json_path = src_dir / space_md.replace('.md', '_export.json')
        
        print(f"Generating {json_path.name}...")
        
        try:
            export = generate_genie_export(md_path)
            
            with open(json_path, 'w') as f:
                json.dump(export, f, indent=2)
            
            print(f"  ✓ Created {json_path.name} ({len(json.dumps(export))} bytes)")
            print(f"    - {len(export['config']['sample_questions'])} sample questions")
            print(f"    - {len(export['data_sources']['tables'])} tables")
            print(f"    - {len(export['data_sources']['metric_views'])} metric views")
            print(f"    - {len(export['instructions']['sql_functions'])} TVFs")
            print(f"    - {len(export['benchmarks']['questions'])} benchmarks")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n✓ Generation complete!")

if __name__ == "__main__":
    main()


