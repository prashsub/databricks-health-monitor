# Databricks notebook source
# MAGIC %md
# MAGIC # Genie Space Benchmark SQL Pre-Deployment Validation
# MAGIC
# MAGIC This notebook validates all 150 benchmark SQL queries across all 6 Genie Spaces
# MAGIC by executing each query with LIMIT 1 to catch:
# MAGIC - Column resolution errors
# MAGIC - Table/view not found errors
# MAGIC - Function not found errors
# MAGIC - Type mismatches
# MAGIC - Runtime errors
# MAGIC
# MAGIC **Run this notebook before deploying Genie Spaces to production.**

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# DBTITLE 1,Configuration Parameters
# Catalog and schema configuration - update these for your environment
CATALOG = "health_monitor"
GOLD_SCHEMA = "gold"
FEATURE_SCHEMA = "gold_ml"

# Path to Genie Space JSON exports
GENIE_EXPORTS_PATH = "/Workspace/Shared/DatabricksHealthMonitor/src/genie"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validation Functions

# COMMAND ----------

import json
import re
from pathlib import Path
from datetime import datetime
from pyspark.sql import SparkSession

def extract_benchmark_queries(json_data: dict, genie_name: str, catalog: str, gold_schema: str, feature_schema: str) -> list:
    """Extract all benchmark SQL queries from a Genie Space JSON export."""

    def substitute_vars(sql: str) -> str:
        sql = sql.replace('${catalog}', catalog)
        sql = sql.replace('${gold_schema}', gold_schema)
        sql = sql.replace('${feature_schema}', feature_schema)
        sql = sql.replace('${ml_schema}', feature_schema)
        return sql

    def extract_sql(item: dict) -> tuple:
        q = item.get('question', '')
        question_text = '\n'.join(q) if isinstance(q, list) else q

        sql = None
        if 'answer' in item:
            answers = item['answer']
            if answers and answers[0].get('format') == 'SQL':
                content = answers[0].get('content', [])
                sql = '\n'.join(content) if isinstance(content, list) else content
        elif 'sql' in item:
            s = item['sql']
            sql = '\n'.join(s) if isinstance(s, list) else s
        elif 'query' in item:
            q = item['query']
            sql = '\n'.join(q) if isinstance(q, list) else q

        return sql, question_text

    queries = []

    # Process curated_questions (v2 format)
    for idx, item in enumerate(json_data.get('curated_questions', []), 1):
        sql, question = extract_sql(item)
        if sql:
            queries.append({
                'genie_space': genie_name,
                'question_num': idx,
                'question_text': question[:100],
                'sql': substitute_vars(sql),
                'benchmark_id': item.get('question_id', item.get('id', 'unknown'))
            })

    # Process benchmarks.questions (v1 format)
    for idx, item in enumerate(json_data.get('benchmarks', {}).get('questions', []), 1):
        sql, question = extract_sql(item)
        if sql:
            queries.append({
                'genie_space': genie_name,
                'question_num': idx,
                'question_text': question[:100],
                'sql': substitute_vars(sql),
                'benchmark_id': item.get('id', 'unknown')
            })

    return queries


def validate_query(spark: SparkSession, query_info: dict) -> dict:
    """Validate a single SQL query by executing it with LIMIT 1."""

    result = {
        'genie_space': query_info['genie_space'],
        'question_num': query_info['question_num'],
        'question_text': query_info['question_text'],
        'valid': False,
        'error': None,
        'error_type': None,
        'row_count': 0
    }

    try:
        original_query = query_info['sql'].strip().rstrip(';')

        # Wrap with LIMIT 1 for fast validation
        if 'LIMIT' in original_query.upper():
            validation_query = f"SELECT * FROM ({original_query}) AS validation_subquery LIMIT 1"
        else:
            validation_query = f"{original_query} LIMIT 1"

        # Execute and collect results
        df = spark.sql(validation_query)
        rows = df.collect()
        result['valid'] = True
        result['row_count'] = len(rows)

    except Exception as e:
        error_str = str(e)
        result['error'] = error_str[:500]

        # Categorize error
        if 'UNRESOLVED_COLUMN' in error_str:
            result['error_type'] = 'COLUMN_NOT_FOUND'
        elif 'TABLE_OR_VIEW_NOT_FOUND' in error_str:
            result['error_type'] = 'TABLE_NOT_FOUND'
        elif 'UNRESOLVED_ROUTINE' in error_str:
            result['error_type'] = 'FUNCTION_NOT_FOUND'
        elif 'PARSE_SYNTAX_ERROR' in error_str:
            result['error_type'] = 'SYNTAX_ERROR'
        elif 'AMBIGUOUS_REFERENCE' in error_str:
            result['error_type'] = 'AMBIGUOUS_COLUMN'
        else:
            result['error_type'] = 'RUNTIME_ERROR'

    return result

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load and Validate All Genie Spaces

# COMMAND ----------

# DBTITLE 1,Load Genie Space JSON Exports
import os

# List all Genie Space JSON export files
genie_files = [
    "cost_intelligence_genie_export.json",
    "data_quality_monitor_genie_export.json",
    "job_health_monitor_genie_export.json",
    "performance_genie_export.json",
    "security_auditor_genie_export.json",
    "unified_health_monitor_genie_export.json"
]

all_queries = []

print(f"Loading benchmark queries from {len(genie_files)} Genie Spaces...")
print(f"Catalog: {CATALOG}, Gold Schema: {GOLD_SCHEMA}, Feature Schema: {FEATURE_SCHEMA}")
print("-" * 80)

for filename in genie_files:
    filepath = f"{GENIE_EXPORTS_PATH}/{filename}"
    genie_name = filename.replace('_genie_export.json', '')

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        queries = extract_benchmark_queries(data, genie_name, CATALOG, GOLD_SCHEMA, FEATURE_SCHEMA)
        all_queries.extend(queries)
        print(f"  ✓ {genie_name}: {len(queries)} benchmark queries")
    except Exception as e:
        print(f"  ✗ {genie_name}: Failed to load - {str(e)[:50]}")

print("-" * 80)
print(f"Total benchmark queries to validate: {len(all_queries)}")

# COMMAND ----------

# DBTITLE 1,Execute Validation
print(f"\n{'='*80}")
print("EXECUTING BENCHMARK SQL VALIDATION")
print(f"{'='*80}")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("-" * 80)

results = []
for i, query_info in enumerate(all_queries, 1):
    result = validate_query(spark, query_info)
    results.append(result)

    status = "✓" if result['valid'] else "✗"
    print(f"  [{i:3d}/{len(all_queries)}] {status} {query_info['genie_space']} Q{query_info['question_num']}")

print("-" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validation Report

# COMMAND ----------

# DBTITLE 1,Generate Summary Report
valid_count = sum(1 for r in results if r['valid'])
invalid_count = len(results) - valid_count

print(f"\n{'='*80}")
print("VALIDATION SUMMARY")
print(f"{'='*80}")
print(f"Total queries validated: {len(results)}")
print(f"  ✓ Valid:   {valid_count}")
print(f"  ✗ Invalid: {invalid_count}")
print()

# Summary by Genie Space
print("BY GENIE SPACE:")
by_space = {}
for r in results:
    if r['genie_space'] not in by_space:
        by_space[r['genie_space']] = {'total': 0, 'valid': 0}
    by_space[r['genie_space']]['total'] += 1
    if r['valid']:
        by_space[r['genie_space']]['valid'] += 1

for space, stats in sorted(by_space.items()):
    status = "✓" if stats['valid'] == stats['total'] else "✗"
    print(f"  {status} {space}: {stats['valid']}/{stats['total']} valid")

# COMMAND ----------

# DBTITLE 1,Show Errors (if any)
if invalid_count > 0:
    print(f"\n{'='*80}")
    print("ERRORS REQUIRING FIX")
    print(f"{'='*80}")

    for r in results:
        if not r['valid']:
            print(f"\n❌ [{r['genie_space']}] Q{r['question_num']}")
            print(f"   Question: {r['question_text'][:80]}...")
            print(f"   Error Type: {r['error_type']}")
            print(f"   Error: {r['error'][:200]}...")
else:
    print(f"\n{'='*80}")
    print("🎉 ALL BENCHMARK QUERIES PASSED VALIDATION!")
    print("   Genie Spaces are ready for deployment.")
    print(f"{'='*80}")

# COMMAND ----------

# DBTITLE 1,Create Results DataFrame
# Create DataFrame for analysis
results_df = spark.createDataFrame(results)
display(results_df)

# COMMAND ----------

# DBTITLE 1,Save Validation Results
# Save results to table for tracking
results_df.write.mode("overwrite").saveAsTable(f"{CATALOG}.{GOLD_SCHEMA}_validation.genie_benchmark_validation_results")
print(f"Results saved to {CATALOG}.{GOLD_SCHEMA}_validation.genie_benchmark_validation_results")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deployment Readiness Check

# COMMAND ----------

# DBTITLE 1,Final Deployment Status
if invalid_count == 0:
    print("=" * 80)
    print("✅ READY FOR DEPLOYMENT")
    print("=" * 80)
    print(f"""
All {len(results)} benchmark queries across {len(genie_files)} Genie Spaces passed validation.

Genie Spaces ready for deployment:
  - Cost Intelligence Genie Space
  - Data Quality Monitor Genie Space
  - Job Health Monitor Genie Space
  - Performance Genie Space
  - Security Auditor Genie Space
  - Unified Health Monitor Genie Space

Next steps:
1. Deploy Genie Space JSON exports to Databricks Genie
2. Configure workspace permissions
3. Share with users
""")
else:
    print("=" * 80)
    print("❌ NOT READY FOR DEPLOYMENT")
    print("=" * 80)
    print(f"""
{invalid_count} queries failed validation and must be fixed before deployment.

Error summary by type:
""")
    error_types = {}
    for r in results:
        if not r['valid']:
            et = r['error_type']
            error_types[et] = error_types.get(et, 0) + 1

    for et, count in sorted(error_types.items(), key=lambda x: -x[1]):
        print(f"  - {et}: {count} queries")

    print("\nPlease fix the errors listed above and re-run this validation notebook.")

# COMMAND ----------

# Assert all passed for CI/CD pipeline integration
assert invalid_count == 0, f"Validation failed: {invalid_count} queries have errors"
