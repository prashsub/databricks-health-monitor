#!/usr/bin/env python3
"""
Extract benchmark questions from Genie Space markdown files and add them to JSON exports.
"""

import json
import re
import uuid
from pathlib import Path
from typing import List, Dict, Tuple

def generate_id():
    """Generate a Genie Space compatible ID (32 hex chars without dashes)."""
    return uuid.uuid4().hex

def extract_benchmark_questions(markdown_content: str) -> List[Dict]:
    """
    Extract benchmark questions from Section G of markdown.
    
    Format:
    ### Question N: "Question text"
    **Expected SQL:**
    ```sql
    SELECT ...
    ```
    """
    benchmarks = []
    
    # Find Section H (Benchmark Questions)
    section_match = re.search(
        r'## ████ SECTION H: BENCHMARK QUESTIONS.*',
        markdown_content,
        re.DOTALL
    )
    
    if not section_match:
        print("  ⚠️  No Section H (Benchmark Questions) found")
        return benchmarks
    
    section = section_match.group(0)
    
    # Extract Q1, Q2, etc. blocks
    # Pattern: ### Question N: "Question text"
    #          **Expected SQL:**
    #          ```sql
    #          query
    #          ```
    pattern = r'### Question (\d+):\s*["\']([^"\']+)["\'].*?```sql\n(.*?)```'
    
    matches = re.finditer(pattern, section, re.DOTALL)
    
    for match in matches:
        question_num = match.group(1)
        question_text = match.group(2).strip()
        query = match.group(3).strip()
        
        # Split SQL into lines, keeping newlines at end of each line (except last)
        sql_lines = query.split('\n')
        sql_content = [line + '\n' for line in sql_lines[:-1]] + [sql_lines[-1]] if sql_lines else []
        
        benchmarks.append({
            "id": generate_id(),
            "question": [question_text],  # Array format
            "answer": [
                {
                    "format": "SQL",
                    "content": sql_content  # Lines with newlines preserved
                }
            ]
        })
        
        print(f"  ✓ Extracted Q{question_num}: {question_text[:50]}...")
    
    return benchmarks

def update_json_with_benchmarks(json_file: Path, benchmarks: List[Dict]):
    """Update JSON export file with benchmark questions."""
    with open(json_file) as f:
        data = json.load(f)
    
    # Sort benchmarks by ID
    benchmarks_sorted = sorted(benchmarks, key=lambda x: x['id'])
    
    data['benchmarks'] = {
        'questions': benchmarks_sorted
    }
    
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"  ✅ Added {len(benchmarks)} benchmark questions to {json_file.name}")

def main():
    project_root = Path(__file__).parent.parent
    genie_dir = project_root / "src" / "genie"
    
    # Define which spaces need benchmarks extracted (ALL 6 Genie Spaces)
    spaces = [
        ("cost_intelligence_genie.md", "cost_intelligence_genie_export.json"),
        ("data_quality_monitor_genie.md", "data_quality_monitor_genie_export.json"),
        ("job_health_monitor_genie.md", "job_health_monitor_genie_export.json"),
        ("performance_genie.md", "performance_genie_export.json"),
        ("security_auditor_genie.md", "security_auditor_genie_export.json"),
        ("unified_health_monitor_genie.md", "unified_health_monitor_genie_export.json")
    ]
    
    for md_name, json_name in spaces:
        print(f"\n📝 Processing {md_name}...")
        
        md_file = genie_dir / md_name
        json_file = genie_dir / json_name
        
        if not md_file.exists():
            print(f"  ⚠️  Markdown file not found: {md_file}")
            continue
        
        if not json_file.exists():
            print(f"  ⚠️  JSON file not found: {json_file}")
            continue
        
        # Extract benchmarks from markdown
        markdown_content = md_file.read_text()
        benchmarks = extract_benchmark_questions(markdown_content)
        
        if benchmarks:
            # Update JSON with benchmarks
            update_json_with_benchmarks(json_file, benchmarks)
        else:
            print(f"  ⚠️  No benchmarks found in {md_name}")
    
    print("\n✅ Benchmark extraction complete!")
    print("\n📋 Next step: Validate SQL with:")
    print("  DATABRICKS_CONFIG_PROFILE=health_monitor databricks bundle run -t dev genie_spaces_deployment_job")

if __name__ == "__main__":
    main()

