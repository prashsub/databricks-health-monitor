#!/usr/bin/env python3
"""
Local validation script for Genie Space benchmarks.
Connects to Databricks and validates SQL using EXPLAIN.

Usage:
    python scripts/local_validate_genie.py cost_intelligence_genie
"""

import sys
import json
from pathlib import Path
from databricks import sql
import os

def get_databricks_connection():
    """Get Databricks SQL connection."""
    # Get credentials from environment or config
    host = os.getenv("DATABRICKS_HOST", "https://e2-demo-field-eng.cloud.databricks.com")
    token = os.getenv("DATABRICKS_TOKEN")
    http_path = os.getenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/300bd24ba7780573")
    
    if not token:
        # Try to read from .databrickscfg
        config_path = Path.home() / ".databrickscfg"
        if config_path.exists():
            with open(config_path, 'r') as f:
                lines = f.readlines()
                in_health_monitor = False
                for line in lines:
                    if '[health_monitor]' in line:
                        in_health_monitor = True
                    elif in_health_monitor and 'token' in line:
                        token = line.split('=')[1].strip()
                        break
    
    if not token:
        raise Exception("DATABRICKS_TOKEN not found. Set it or configure .databrickscfg")
    
    return sql.connect(
        server_hostname=host.replace('https://', ''),
        http_path=http_path,
        access_token=token
    )

def substitute_variables(sql_query, catalog, gold_schema, feature_schema):
    """Substitute variables in SQL."""
    sql_query = sql_query.replace("${catalog}", catalog)
    sql_query = sql_query.replace("${gold_schema}", gold_schema)
    sql_query = sql_query.replace("${feature_schema}", feature_schema)
    return sql_query

def validate_sql(cursor, sql_query, question_id):
    """Validate SQL using EXPLAIN."""
    try:
        cursor.execute(f"EXPLAIN {sql_query}")
        return True, None
    except Exception as e:
        error_msg = str(e)
        
        # Categorize error
        if "UNRESOLVED_COLUMN" in error_msg or "cannot be resolved" in error_msg:
            error_type = "COLUMN_NOT_FOUND"
        elif "TABLE_OR_VIEW_NOT_FOUND" in error_msg or "cannot be found" in error_msg:
            error_type = "TABLE_NOT_FOUND"
        elif "UNRESOLVABLE_TABLE_VALUED_FUNCTION" in error_msg or "table-valued function" in error_msg:
            error_type = "TVF_NOT_FOUND"
        elif "WRONG_NUM_ARGS" in error_msg:
            error_type = "WRONG_NUM_ARGS"
        elif "PARSE_SYNTAX_ERROR" in error_msg:
            error_type = "SYNTAX_ERROR"
        else:
            error_type = "OTHER"
        
        # Extract first line of error
        error_summary = error_msg.split('\n')[0][:300]
        
        return False, {
            'question_id': question_id,
            'error_type': error_type,
            'error_message': error_summary
        }

def validate_genie_space(genie_space):
    """Validate all benchmarks for a Genie Space."""
    
    catalog = "prashanth_subrahmanyam_catalog"
    gold_schema = "dev_prashanth_subrahmanyam_system_gold"
    feature_schema = "dev_prashanth_subrahmanyam_system_gold_ml"
    
    # Load JSON
    json_path = Path(f"src/genie/{genie_space}_export.json")
    if not json_path.exists():
        print(f"❌ File not found: {json_path}")
        return False
    
    with open(json_path, 'r') as f:
        export_data = json.load(f)
    
    questions = export_data.get('benchmarks', {}).get('questions', [])
    if not questions:
        print(f"❌ No benchmark questions found")
        return False
    
    print(f"\n{'='*80}")
    print(f"Validating: {genie_space} ({len(questions)} questions)")
    print(f"{'='*80}\n")
    
    # Connect to Databricks
    print("Connecting to Databricks SQL Warehouse...")
    conn = get_databricks_connection()
    cursor = conn.cursor()
    
    valid_count = 0
    invalid_count = 0
    errors = []
    
    try:
        for idx, q in enumerate(questions, 1):
            question_text = q.get('question', ['Unknown'])[0] if isinstance(q.get('question'), list) else 'Unknown'
            
            if 'answer' not in q:
                print(f"⚠️  Q{idx}: Missing answer field")
                invalid_count += 1
                continue
            
            answers = q['answer'] if isinstance(q['answer'], list) else [q['answer']]
            if not answers:
                print(f"⚠️  Q{idx}: Empty answer")
                invalid_count += 1
                continue
            
            answer = answers[0]
            if answer.get('format') != 'SQL':
                print(f"⚠️  Q{idx}: Not SQL format")
                invalid_count += 1
                continue
            
            content = answer.get('content', [])
            if isinstance(content, list):
                sql_query = '\n'.join(content)
            else:
                sql_query = content
            
            # Substitute variables
            sql_query = substitute_variables(sql_query, catalog, gold_schema, feature_schema)
            
            # Validate
            is_valid, error = validate_sql(cursor, sql_query, f"Q{idx}")
            
            if is_valid:
                print(f"✅ Q{idx}: {question_text[:60]}...")
                valid_count += 1
            else:
                print(f"❌ Q{idx}: {error['error_type']} - {question_text[:60]}...")
                print(f"   {error['error_message']}")
                invalid_count += 1
                errors.append(error)
        
    finally:
        cursor.close()
        conn.close()
    
    print(f"\n{'='*80}")
    print(f"Validation Summary for {genie_space}")
    print(f"{'='*80}")
    print(f"✅ Valid: {valid_count}/{len(questions)}")
    print(f"❌ Invalid: {invalid_count}/{len(questions)}")
    
    if errors:
        print(f"\nError Breakdown:")
        error_types = {}
        for err in errors:
            error_types[err['error_type']] = error_types.get(err['error_type'], 0) + 1
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {error_type}: {count}")
        
        print(f"\nFirst 10 errors:")
        for err in errors[:10]:
            print(f"  - {err['question_id']}: {err['error_type']}")
            print(f"    {err['error_message'][:200]}")
    
    return invalid_count == 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/local_validate_genie.py <genie_space_name>")
        print("\nAvailable Genie Spaces:")
        print("  - cost_intelligence_genie")
        print("  - job_health_monitor_genie")
        print("  - performance_genie")
        print("  - security_auditor_genie")
        print("  - data_quality_monitor_genie")
        print("  - unified_health_monitor_genie")
        sys.exit(1)
    
    genie_name = sys.argv[1]
    success = validate_genie_space(genie_name)
    sys.exit(0 if success else 1)
