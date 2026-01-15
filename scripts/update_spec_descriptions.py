#!/usr/bin/env python3
"""
Update the description counts in Section B of each Genie Space spec file.
"""

import json
import re
from pathlib import Path
from typing import Dict

INVENTORY_PATH = Path("src/genie/actual_assets_inventory.json")
GENIE_DIR = Path("src/genie")

def load_inventory():
    with open(INVENTORY_PATH) as f:
        return json.load(f)

def update_description_counts(spec_path: Path, domain: Dict) -> bool:
    """Update the 'Powered by' section with correct counts."""
    with open(spec_path) as f:
        content = f.read()
    
    # Calculate counts
    metric_views = len(domain.get('metric_views', []))
    tvfs = len(domain.get('tvfs', []))
    ml_tables = len(domain.get('ml_tables', []))
    monitoring_tables = len(domain.get('monitoring_tables', []))
    tables = domain.get('tables', {})
    dimensions = len(tables.get('dimensions', []))
    facts = len(tables.get('facts', []))
    
    # Build new description block
    new_powered_by = f"""**Powered by:**
- {metric_views} Metric View{'s' if metric_views != 1 else ''} ({', '.join(domain.get('metric_views', []))})
- {tvfs} Table-Valued Functions (parameterized queries)
- {ml_tables} ML Prediction Table{'s' if ml_tables != 1 else ''} (predictions and recommendations)
- {monitoring_tables} Lakehouse Monitoring Table{'s' if monitoring_tables != 1 else ''} (drift and profile metrics)
- {dimensions} Dimension Table{'s' if dimensions != 1 else ''} (reference data)
- {facts} Fact Table{'s' if facts != 1 else ''} (transactional data)"""
    
    # Find and replace the "Powered by:" section
    pattern = r'\*\*Powered by:\*\*\s*\n(?:[-*] .*\n)+'
    
    if re.search(pattern, content):
        new_content = re.sub(pattern, new_powered_by + '\n', content)
        
        with open(spec_path, 'w') as f:
            f.write(new_content)
        return True
    
    return False

def main():
    print("Updating spec file descriptions...")
    
    inventory = load_inventory()
    
    genie_spaces = {
        'cost_intelligence': 'cost_intelligence_genie.md',
        'job_health_monitor': 'job_health_monitor_genie.md',
        'performance': 'performance_genie.md',
        'security_auditor': 'security_auditor_genie.md',
        'data_quality_monitor': 'data_quality_monitor_genie.md',
        'unified_health_monitor': 'unified_health_monitor_genie.md'
    }
    
    for space_key, md_file in genie_spaces.items():
        md_path = GENIE_DIR / md_file
        
        if not md_path.exists():
            continue
        
        domain = inventory.get('domain_mapping', {}).get(space_key, {})
        
        if domain and update_description_counts(md_path, domain):
            tables = domain.get('tables', {})
            print(f"  Updated: {md_file}")
        else:
            print(f"  Skipped: {md_file}")

if __name__ == "__main__":
    main()
