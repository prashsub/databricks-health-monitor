#!/usr/bin/env python3
"""
Generate Genie Space Export JSON files from markdown documentation.

This script reads structured markdown files and generates corresponding
JSON exports following the GenieSpaceExport schema.
"""

import json
import re
import uuid
from pathlib import Path
from typing import List, Dict, Optional

def generate_id():
    """Generate a Genie Space compatible ID (32 hex chars without dashes)."""
    return uuid.uuid4().hex

def extract_space_info(content: str) -> Dict:
    """Extract basic space information from Section A."""
    info = {}
    
    # Extract title from Section A
    title_match = re.search(r'## ████ SECTION A: Space Name.*?\n([^\n]+)', content, re.DOTALL)
    if title_match:
        info['title'] = title_match.group(1).strip().replace('**', '')
    
    # Extract description from Section B
    desc_match = re.search(r'## ████ SECTION B: Description.*?\n([^\n]+)', content, re.DOTALL)
    if desc_match:
        info['description'] = desc_match.group(1).strip()
    
    return info

def extract_sample_questions(content: str) -> List[Dict]:
    """Extract sample questions from Section C."""
    questions = []
    
    section_match = re.search(r'## ████ SECTION C: Sample Questions.*?(?=## ████ SECTION D:)', content, re.DOTALL)
    if not section_match:
        return questions
    
    section = section_match.group(0)
    
    # Extract numbered questions
    for match in re.finditer(r'\d+\.\s+["\']([^"\']+)["\']', section):
        questions.append({
            "id": generate_id(),
            "question": [match.group(1)]
        })
    
    return questions

def extract_tables(content: str, catalog: str, schema: str) -> Dict[str, List[str]]:
    """Extract table references from Section D."""
    tables = {
        'metric_views': [],
        'fact_tables': [],
        'dimension_tables': [],
        'ml_tables': [],
        'monitoring_tables': []
    }
    
    section_match = re.search(r'## ████ SECTION D: Data Assets.*?(?=## ████ SECTION E:)', content, re.DOTALL)
    if not section_match:
        return tables
    
    section = section_match.group(0)
    
    # Extract metric views
    mv_match = re.search(r'### Metric Views.*?(?=###|\Z)', section, re.DOTALL)
    if mv_match:
        for match in re.finditer(r'-\s+`([^`]+)`', mv_match.group(0)):
            mv_name = match.group(1)
            if '_metrics' in mv_name or '_analytics' in mv_name:
                tables['metric_views'].append(f"{catalog}.{schema}.{mv_name}")
    
    # Extract fact tables
    fact_match = re.search(r'### Fact Tables.*?(?=###|\Z)', section, re.DOTALL)
    if fact_match:
        for match in re.finditer(r'-\s+`([^`]+)`', fact_match.group(0)):
            tables['fact_tables'].append(f"{catalog}.{schema}.{match.group(1)}")
    
    # Extract dimension tables
    dim_match = re.search(r'### Dimension Tables.*?(?=###|\Z)', section, re.DOTALL)
    if dim_match:
        for match in re.finditer(r'-\s+`([^`]+)`', dim_match.group(0)):
            tables['dimension_tables'].append(f"{catalog}.{schema}.{match.group(1)}")
    
    # Extract ML tables
    ml_match = re.search(r'### ML Prediction Tables.*?(?=###|\Z)', section, re.DOTALL)
    if ml_match:
        for match in re.finditer(r'-\s+`([^`]+)`', ml_match.group(0)):
            ml_name = match.group(1)
            tables['ml_tables'].append(f"{catalog}.${'{feature_schema}'}.{ml_name}")
    
    # Extract monitoring tables
    mon_match = re.search(r'### Lakehouse Monitoring Tables.*?(?=###|\Z)', section, re.DOTALL)
    if mon_match:
        for match in re.finditer(r'-\s+`([^`]+)`', mon_match.group(0)):
            tables['monitoring_tables'].append(f"{catalog}.{schema}.{match.group(1)}")
    
    return tables

def extract_tvfs(content: str) -> List[Dict]:
    """Extract TVF references from Section F."""
    tvfs = []
    
    section_match = re.search(r'## ████ SECTION F: Table-Valued Functions.*?(?=## ████ SECTION G:)', content, re.DOTALL)
    if not section_match:
        return tvfs
    
    section = section_match.group(0)
    
    # Extract TVF names
    for match in re.finditer(r'-\s+`([a-z_]+)\(([^)]*)\)`', section):
        tvfs.append({
            "id": generate_id(),
            "identifier": match.group(1),
            "parameters": match.group(2).strip()
        })
    
    return tvfs

def extract_benchmark_questions(content: str) -> List[Dict]:
    """Extract benchmark questions from Section G."""
    benchmarks = []
    
    section_match = re.search(r'## ████ SECTION G: Benchmark Questions.*', content, re.DOTALL)
    if not section_match:
        return benchmarks
    
    section = section_match.group(0)
    
    # Extract Q1, Q2, etc. blocks
    for match in re.finditer(r'Q(\d+):\s*([^\n]+)\n```sql\n(.*?)```', section, re.DOTALL):
        question_text = match.group(2).strip()
        query = match.group(3).strip()
        
        benchmarks.append({
            "id": generate_id(),
            "question": question_text,
            "query": query
        })
    
    return benchmarks

def generate_basic_column_configs(tables: List[str]) -> List[Dict]:
    """Generate minimal column configs for tables."""
    configs = []
    
    for table in tables:
        # For simplicity, add common columns - validation will catch issues
        table_name = table.split('.')[-1]
        
        if '_dim' in table_name or table_name.startswith('dim_'):
            # Dimension table common columns
            common_cols = ['is_current', 'effective_from', 'effective_to']
        elif '_fact' in table_name or table_name.startswith('fact_'):
            # Fact table common columns  
            common_cols = ['record_created_timestamp', 'record_updated_timestamp']
        elif '_metrics' in table_name:
            # Metric view - no column configs needed
            continue
        elif 'prediction' in table_name:
            # ML prediction table
            common_cols = ['prediction', 'prediction_timestamp']
        else:
            common_cols = []
        
        for col in common_cols:
            configs.append({
                "identifier": table,
                "column_name": col,
                "semantic_type": "attribute"
            })
    
    return sorted(configs, key=lambda x: (x['identifier'], x['column_name']))

def create_genie_space_json(
    markdown_file: Path,
    catalog: str = "${catalog}",
    schema: str = "${gold_schema}",
    warehouse_id: str = "${warehouse_id}"
) -> Dict:
    """Create a complete Genie Space JSON export from markdown."""
    
    content = markdown_file.read_text()
    
    # Extract sections
    space_info = extract_space_info(content)
    sample_questions = extract_sample_questions(content)
    tables = extract_tables(content, catalog, schema)
    tvfs = extract_tvfs(content)
    benchmarks = extract_benchmark_questions(content)
    
    # Build data sources
    all_tables = (
        tables['metric_views'] + 
        tables['fact_tables'] + 
        tables['dimension_tables'] + 
        tables['ml_tables'] + 
        tables['monitoring_tables']
    )
    
    data_sources_tables = []
    for table in sorted(set(all_tables)):
        data_sources_tables.append({
            "identifier": table,
            "column_configs": []  # Will be populated by validation if needed
        })
    
    # Build config
    config = {
        "title": space_info.get('title', markdown_file.stem.replace('_genie', '')),
        "description": space_info.get('description', f"Genie Space for {space_info.get('title', '')}"),
        "warehouse_id": warehouse_id,
        "sample_questions": sorted(sample_questions, key=lambda x: x['id'])
    }
    
    # Build instructions
    instructions = {
        "sql_functions": sorted(tvfs, key=lambda x: (x['id'], x['identifier'])),
        "text_instructions": [],
        "example_question_sqls": [],
        "join_specs": []
    }
    
    # Build benchmarks
    benchmarks_section = {
        "questions": sorted(benchmarks, key=lambda x: x['id'])
    }
    
    # Assemble final JSON
    export_json = {
        "version": 1,
        "config": config,
        "data_sources": {
            "tables": data_sources_tables,
            "metric_views": []
        },
        "instructions": instructions,
        "benchmarks": benchmarks_section
    }
    
    return export_json

def main():
    """Generate JSON exports for all Genie Space markdown files."""
    
    project_root = Path(__file__).parent.parent
    genie_dir = project_root / "src" / "genie"
    
    # Define which spaces need JSON generation
    spaces_to_generate = [
        "performance_genie.md",
        "security_auditor_genie.md",
        "unified_health_monitor_genie.md"
    ]
    
    for md_file_name in spaces_to_generate:
        md_file = genie_dir / md_file_name
        if not md_file.exists():
            print(f"⚠  Skipping {md_file_name} - file not found")
            continue
        
        print(f"Processing {md_file_name}...")
        
        # Generate JSON
        export_json = create_genie_space_json(md_file)
        
        # Write JSON
        json_file_name = md_file_name.replace('_genie.md', '_genie_export.json')
        json_file = genie_dir / json_file_name
        
        with open(json_file, 'w') as f:
            json.dump(export_json, f, indent=2)
        
        print(f"✅ Created {json_file_name}")
    
    print("\nDone! Generated JSON exports for:")
    for space in spaces_to_generate:
        json_name = space.replace('_genie.md', '_genie_export.json')
        print(f"  - {json_name}")

if __name__ == "__main__":
    main()

