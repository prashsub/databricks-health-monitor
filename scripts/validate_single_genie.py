"""
Validate SQL queries for a single Genie Space.
Usage: python validate_single_genie.py <genie_space_name>
"""

import sys
import json
from pathlib import Path

# Import validation logic from main validation script
sys.path.append('src/genie')

def validate_single_genie_space(genie_name):
    """Validate SQL for a single Genie Space JSON export."""
    
    json_file = Path(f'src/genie/{genie_name}_export.json')
    
    if not json_file.exists():
        print(f"❌ File not found: {json_file}")
        return False
    
    with open(json_file, 'r') as f:
        export_data = json.load(f)
    
    if 'benchmarks' not in export_data or 'questions' not in export_data['benchmarks']:
        print(f"❌ No benchmark questions found in {json_file}")
        return False
    
    questions = export_data['benchmarks']['questions']
    print(f"\n{'='*80}")
    print(f"Validating: {genie_name} ({len(questions)} questions)")
    print(f"{'='*80}\n")
    
    # Extract SQL queries
    queries = []
    for idx, q in enumerate(questions, 1):
        question_text = q.get('question', ['Unknown'])[0] if isinstance(q.get('question'), list) else 'Unknown'
        
        if 'answer' not in q:
            print(f"⚠️  Q{idx}: Missing answer field")
            continue
        
        answers = q['answer'] if isinstance(q['answer'], list) else [q['answer']]
        
        if not answers:
            print(f"⚠️  Q{idx}: Empty answer")
            continue
        
        answer = answers[0]
        if answer.get('format') != 'SQL':
            print(f"⚠️  Q{idx}: Not SQL format")
            continue
        
        content = answer.get('content', [])
        if isinstance(content, list):
            sql = '\n'.join(content)
        else:
            sql = content
        
        queries.append({
            'num': idx,
            'question': question_text[:80],
            'sql': sql
        })
    
    print(f"📊 Extracted {len(queries)} SQL queries\n")
    
    # Print queries for manual inspection
    for q in queries:
        print(f"\nQ{q['num']}: {q['question']}...")
        print(f"SQL Preview: {q['sql'][:200]}...")
    
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python validate_single_genie.py <genie_space_name>")
        print("\nAvailable Genie Spaces:")
        print("  - cost_intelligence_genie")
        print("  - job_health_monitor_genie")
        print("  - performance_genie")
        print("  - security_auditor_genie")
        print("  - data_quality_monitor_genie")
        print("  - unified_health_monitor_genie")
        sys.exit(1)
    
    genie_name = sys.argv[1]
    validate_single_genie_space(genie_name)
