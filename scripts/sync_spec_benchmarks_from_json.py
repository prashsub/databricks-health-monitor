#!/usr/bin/env python3
"""
Sync spec file Section H (Benchmark Questions) from JSON files.

JSON is the source of truth. This script updates the human-readable
spec files (.md) to match the JSON benchmark questions.
"""

import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
GENIE_DIR = PROJECT_ROOT / "src/genie"

# Mapping of domain names to file names
GENIE_SPACES = {
    'cost_intelligence': {
        'json': 'cost_intelligence_genie_export.json',
        'spec': 'cost_intelligence_genie.md',
        'title': 'Cost Intelligence'
    },
    'job_health_monitor': {
        'json': 'job_health_monitor_genie_export.json',
        'spec': 'job_health_monitor_genie.md',
        'title': 'Job Health Monitor'
    },
    'performance': {
        'json': 'performance_genie_export.json',
        'spec': 'performance_genie.md',
        'title': 'Performance'
    },
    'security_auditor': {
        'json': 'security_auditor_genie_export.json',
        'spec': 'security_auditor_genie.md',
        'title': 'Security Auditor'
    },
    'data_quality_monitor': {
        'json': 'data_quality_monitor_genie_export.json',
        'spec': 'data_quality_monitor_genie.md',
        'title': 'Data Quality Monitor'
    },
    'unified_health_monitor': {
        'json': 'unified_health_monitor_genie_export.json',
        'spec': 'unified_health_monitor_genie.md',
        'title': 'Unified Health Monitor'
    },
}


def load_benchmarks_from_json(json_path: Path) -> list:
    """Load benchmark questions from JSON file."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    return data.get('benchmarks', {}).get('questions', [])


def categorize_benchmarks(benchmarks: list) -> dict:
    """Categorize benchmarks by type based on SQL content."""
    categories = {
        'tvf': [],
        'metric_view': [],
        'ml': [],
        'monitoring': [],
        'fact': [],
        'dim': [],
        'deep_research': []
    }
    
    for bm in benchmarks:
        question = bm.get('question', [''])[0]
        sql = ''.join(bm.get('answer', [{}])[0].get('content', []))
        
        # Categorize based on question prefix or SQL content
        if question.startswith('🔬 DEEP RESEARCH'):
            categories['deep_research'].append(bm)
        elif 'TABLE(' in sql or 'get_' in sql:
            categories['tvf'].append(bm)
        elif 'mv_' in sql.lower():
            categories['metric_view'].append(bm)
        elif '_predictions' in sql:
            categories['ml'].append(bm)
        elif '_drift_metrics' in sql or '_profile_metrics' in sql:
            categories['monitoring'].append(bm)
        elif 'fact_' in sql:
            categories['fact'].append(bm)
        elif 'dim_' in sql:
            categories['dim'].append(bm)
        else:
            # Default to TVF if has function call pattern
            if 'FROM TABLE(' in sql:
                categories['tvf'].append(bm)
            else:
                categories['metric_view'].append(bm)
    
    return categories


def format_benchmark_markdown(bm: dict, index: int) -> str:
    """Format a single benchmark as markdown."""
    question = bm.get('question', [''])[0]
    sql = ''.join(bm.get('answer', [{}])[0].get('content', []))
    
    # Clean up SQL formatting
    sql = sql.strip()
    if not sql.endswith(';'):
        sql += ';'
    
    return f"""**Q{index}: {question}**
```sql
{sql}
```
"""


def generate_section_h(benchmarks: list, title: str) -> str:
    """Generate the complete Section H markdown content."""
    
    categories = categorize_benchmarks(benchmarks)
    
    # Count by category
    counts = {k: len(v) for k, v in categories.items()}
    total = sum(counts.values())
    
    md = f"""## H. Benchmark Questions with SQL

**Total Benchmarks: {total}**
- TVF Questions: {counts['tvf']}
- Metric View Questions: {counts['metric_view']}
- ML Table Questions: {counts['ml']}
- Monitoring Table Questions: {counts['monitoring']}
- Fact Table Questions: {counts['fact']}
- Dimension Table Questions: {counts['dim']}
- Deep Research Questions: {counts['deep_research']}

---

"""
    
    # Add each category
    idx = 1
    
    if categories['tvf']:
        md += "### TVF Questions\n\n"
        for bm in categories['tvf']:
            md += format_benchmark_markdown(bm, idx)
            md += "\n"
            idx += 1
    
    if categories['metric_view']:
        md += "### Metric View Questions\n\n"
        for bm in categories['metric_view']:
            md += format_benchmark_markdown(bm, idx)
            md += "\n"
            idx += 1
    
    if categories['ml']:
        md += "### ML Prediction Questions\n\n"
        for bm in categories['ml']:
            md += format_benchmark_markdown(bm, idx)
            md += "\n"
            idx += 1
    
    if categories['monitoring']:
        md += "### Lakehouse Monitoring Questions\n\n"
        for bm in categories['monitoring']:
            md += format_benchmark_markdown(bm, idx)
            md += "\n"
            idx += 1
    
    if categories['fact']:
        md += "### Fact Table Questions\n\n"
        for bm in categories['fact']:
            md += format_benchmark_markdown(bm, idx)
            md += "\n"
            idx += 1
    
    if categories['dim']:
        md += "### Dimension Table Questions\n\n"
        for bm in categories['dim']:
            md += format_benchmark_markdown(bm, idx)
            md += "\n"
            idx += 1
    
    if categories['deep_research']:
        md += "### Deep Research Questions\n\n"
        for bm in categories['deep_research']:
            md += format_benchmark_markdown(bm, idx)
            md += "\n"
            idx += 1
    
    md += """---

*Note: These benchmarks are auto-generated from `actual_assets_inventory.json` to ensure all referenced assets exist. JSON file is the source of truth.*
"""
    
    return md


def update_spec_file(spec_path: Path, new_section_h: str) -> bool:
    """Update the spec file's Section H with new content."""
    
    with open(spec_path, 'r') as f:
        content = f.read()
    
    # Pattern to find Section H - from "## H." to next "## " or end of file
    # Also handle variations like "## H. Benchmark" or "## Section H"
    pattern = r'(## H\..*?(?=\n## [A-GI-Z]\.|\n---\n\*Note:|\Z))'
    
    # Check if Section H exists
    if re.search(r'## H\.', content):
        # Replace existing Section H
        new_content = re.sub(pattern, new_section_h.strip(), content, flags=re.DOTALL)
    else:
        # Append Section H at the end (before final ---)
        if content.rstrip().endswith('---'):
            new_content = content.rstrip()[:-3] + '\n\n' + new_section_h
        else:
            new_content = content.rstrip() + '\n\n' + new_section_h
    
    with open(spec_path, 'w') as f:
        f.write(new_content)
    
    return True


def sync_genie_space(domain_name: str) -> bool:
    """Sync a single Genie Space spec file from its JSON."""
    
    config = GENIE_SPACES.get(domain_name)
    if not config:
        print(f"⚠️ Unknown domain: {domain_name}")
        return False
    
    json_path = GENIE_DIR / config['json']
    spec_path = GENIE_DIR / config['spec']
    
    if not json_path.exists():
        print(f"⚠️ JSON not found: {json_path}")
        return False
    
    if not spec_path.exists():
        print(f"⚠️ Spec not found: {spec_path}")
        return False
    
    # Load benchmarks from JSON
    benchmarks = load_benchmarks_from_json(json_path)
    
    if not benchmarks:
        print(f"⚠️ No benchmarks in {json_path.name}")
        return False
    
    # Generate Section H
    section_h = generate_section_h(benchmarks, config['title'])
    
    # Update spec file
    update_spec_file(spec_path, section_h)
    
    # Categorize for summary
    categories = categorize_benchmarks(benchmarks)
    counts = {k: len(v) for k, v in categories.items()}
    
    print(f"✅ {domain_name}: {len(benchmarks)} benchmarks synced")
    print(f"   TVF: {counts['tvf']}, MV: {counts['metric_view']}, ML: {counts['ml']}, "
          f"Mon: {counts['monitoring']}, Fact: {counts['fact']}, Dim: {counts['dim']}, "
          f"Deep: {counts['deep_research']}")
    
    return True


def main():
    print("=" * 70)
    print("SYNCING SPEC FILES FROM JSON (JSON IS SOURCE OF TRUTH)")
    print("=" * 70)
    
    success = 0
    failed = 0
    
    for domain in GENIE_SPACES.keys():
        if sync_genie_space(domain):
            success += 1
        else:
            failed += 1
    
    print("\n" + "=" * 70)
    if failed == 0:
        print(f"✅ ALL {success} SPEC FILES SYNCED SUCCESSFULLY")
    else:
        print(f"⚠️ {success} synced, {failed} failed")
    print("=" * 70)


if __name__ == "__main__":
    main()
