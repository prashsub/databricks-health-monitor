"""
Fix Genie Space SQL References

Automatically fixes TVF names, column names, and SQL syntax issues
in Genie Space JSON export files based on the actual semantic layer definitions.

Fixes:
1. TVF name mismatches (e.g., get_stale_tables → get_table_freshness)
2. TVF signature mismatches (e.g., wrong parameters)
3. Column name mismatches (e.g., evaluation_date → query_date)
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple


# TVF Name Mapping: old_name -> new_name with signature notes
# Maps non-existent TVF names to their closest existing equivalents
TVF_REPLACEMENTS = {
    # Quality TVFs
    'get_stale_tables': 'get_table_freshness',
    'get_table_activity_summary': 'get_table_activity_status',
    'get_data_lineage_summary': 'get_pipeline_data_lineage',
    'get_table_lineage': 'get_pipeline_data_lineage',
    'get_pipeline_lineage_impact': 'get_pipeline_data_lineage',
    # Cost TVFs - map non-existent to existing equivalents
    'get_job_cost_breakdown': 'get_most_expensive_jobs',
    'get_cost_forecast': 'get_cost_forecast_summary',
    'get_serverless_vs_classic_cost': 'get_cost_trend_by_sku',  # SKU includes serverless/classic breakdown
    'get_daily_cost_summary': 'get_cost_mtd_summary',  # MTD summary provides daily breakdown
    'get_cost_by_cluster_type': 'get_all_purpose_cluster_cost',  # Cluster type cost analysis
    'get_warehouse_cost_analysis': 'get_warehouse_utilization',  # Warehouse metrics and utilization
    # Performance TVFs - map non-existent to existing equivalents
    'get_slowest_queries': 'get_slow_queries',  # Actual name is get_slow_queries
    'get_warehouse_performance': 'get_warehouse_utilization',  # Use utilization for performance
    'get_spill_analysis': 'get_high_spill_queries',  # Actual name is get_high_spill_queries
    'get_autoscaling_disabled_jobs': 'get_jobs_without_autoscaling',  # Actual name
    'get_cluster_rightsizing_recommendations': 'get_cluster_right_sizing_recommendations',  # Underscore difference
    # Job/Reliability TVFs
    'get_job_failures': 'get_failed_jobs',  # Actual name is get_failed_jobs
    'get_job_trends': 'get_job_failure_trends',  # Actual name
    # Security TVFs - map non-existent to existing equivalents
    'get_sensitive_data_access': 'get_sensitive_table_access',  # Actual name
    'get_failed_access_attempts': 'get_failed_actions',  # Actual name
    'get_service_account_activity': 'get_service_account_audit',  # Actual name
    'get_data_export_events': 'get_table_access_audit',  # Use table access audit for export events
    'get_unusual_access_patterns': 'get_off_hours_activity',  # Map to off-hours analysis
}

# TVF Signature Fixes: function_name -> (old_call_pattern, new_call_pattern)
TVF_SIGNATURE_FIXES = {
    # get_stale_tables(7, 24) → get_table_freshness(24)
    r'get_stale_tables\s*\(\s*\d+\s*,\s*(\d+)\s*\)': r'get_table_freshness(\1)',
    # get_stale_tables(7) → get_table_freshness(24)
    r'get_stale_tables\s*\(\s*(\d+)\s*\)': r'get_table_freshness(\1)',
    # get_table_activity_summary(7) → get_table_activity_status(7, 14)
    r'get_table_activity_summary\s*\(\s*(\d+)\s*\)': r'get_table_activity_status(\1, 14)',
    # get_data_lineage_summary('main', '%') → get_pipeline_data_lineage()
    r"get_data_lineage_summary\s*\(\s*'[^']*'\s*,\s*'[^']*'\s*\)": r'get_pipeline_data_lineage()',
    r"get_data_lineage_summary\s*\([^)]*\)": r'get_pipeline_data_lineage()',
    # get_table_lineage() → get_pipeline_data_lineage()
    r'get_table_lineage\s*\([^)]*\)': r'get_pipeline_data_lineage()',
    # get_pipeline_lineage_impact() → get_pipeline_data_lineage()
    r'get_pipeline_lineage_impact\s*\([^)]*\)': r'get_pipeline_data_lineage()',
}

# Column Name Fixes in metric views
# Note: Remove date filters if metric view doesn't have date columns
COLUMN_FIXES = {
    # Remove evaluation_date filters as metric views may not have this column
}

# Date filter patterns to remove from metric view queries
DATE_FILTER_PATTERNS_TO_REMOVE = [
    r"WHERE\s+evaluation_date\s*>=\s*CURRENT_DATE\(\)\s*-\s*INTERVAL\s+\d+\s+DAYS;?",
    r"WHERE\s+query_date\s*>=\s*CURRENT_DATE\(\)\s*-\s*INTERVAL\s+\d+\s+DAYS;?",
    r"AND\s+evaluation_date\s*>=\s*CURRENT_DATE\(\)\s*-\s*INTERVAL\s+\d+\s+DAYS",
    r"AND\s+query_date\s*>=\s*CURRENT_DATE\(\)\s*-\s*INTERVAL\s+\d+\s+DAYS",
]

# Full query replacements: pattern → replacement
# These handle fundamental SQL structure issues where columns don't exist
QUERY_REWRITES = {
    # get_table_activity_status doesn't have failed_check_count or quality_score
    # Replace with valid columns from that TVF
    r"ORDER BY\s+failed_check_count\s+DESC,\s*quality_score\s+ASC":
        "ORDER BY days_since_last_access DESC",
    r"WHERE\s+failed_check_count\s*>\s*0":
        "WHERE activity_status = 'INACTIVE'",
    r"ORDER BY\s+quality_score\s+ASC":
        "ORDER BY days_since_last_access DESC",

    # get_table_activity_status doesn't have domain, total_tables, stale_tables
    # These queries should use get_data_freshness_by_domain instead
    r"SELECT\s+domain,\s*total_tables,\s*stale_tables,\s*avg_hours_since_update\s+FROM\s+TABLE\(\$\{catalog\}\.\$\{gold_schema\}\.get_table_activity_status\([^)]+\)\)\s+GROUP BY domain":
        "SELECT domain, table_count as total_tables, freshness_threshold, avg_hours_since_update, max_hours_since_update FROM TABLE(${catalog}.${gold_schema}.get_data_freshness_by_domain(24))",
    r"ORDER BY\s+stale_tables\s+DESC":
        "ORDER BY max_hours_since_update DESC",

    # get_pipeline_data_lineage requires days_back parameter
    r"get_pipeline_data_lineage\(\)":
        "get_pipeline_data_lineage(7, 'ALL')",

    # depth column doesn't exist - use complexity_score
    r"ORDER BY\s+depth\s+ASC":
        "ORDER BY complexity_score DESC",
    r"ORDER BY\s+depth\s+DESC":
        "ORDER BY complexity_score DESC",

    # downstream_dependencies doesn't exist - use target_count
    r"ORDER BY\s+downstream_dependencies\s+DESC":
        "ORDER BY target_count DESC",

    # Metric view mv_data_quality has these actual measures:
    # freshness_rate, staleness_rate, stale_tables, fresh_tables, avg_hours_since_update, total_tables
    # Map non-existent columns to actual ones

    # quality_score → freshness_rate (closest available measure)
    r"MEASURE\(quality_score\)": "MEASURE(freshness_rate)",

    # completeness_rate → not available, use total_tables as proxy
    r"MEASURE\(completeness_rate\)": "MEASURE(total_tables)",

    # validity_rate → staleness_rate inverted conceptually
    r"MEASURE\(validity_rate\)": "MEASURE(staleness_rate)",

    # days_since_last_read doesn't exist - use days_since_last_access
    r"\bdays_since_last_read\b": "days_since_last_access",
}

# Column reference fixes for specific contexts (TVF outputs)
TVF_COLUMN_FIXES = {
    # get_table_freshness outputs
    'freshness_status': 'is_stale',
    'hours_since_update': 'hours_since_update',  # This one is correct
    'expected_update_frequency_hours': 'freshness_threshold_hours',
    # get_table_activity_status outputs
    'failed_checks': 'failed_check_count',
    'activity_status': 'activity_status',  # Correct
    'days_since_last_access': 'days_since_last_read',
    'daily_read_count': 'read_count',
    'daily_write_count': 'write_count',
    # get_pipeline_data_lineage outputs
    'dependency_depth': 'depth',
    'source_table': 'upstream_table',
    'target_table': 'downstream_table',
}


def fix_sql_content(sql_lines: List[str], genie_name: str, question_num: int) -> Tuple[List[str], List[str]]:
    """Fix SQL content and return fixed lines plus list of changes made."""

    # Join lines into single SQL string
    sql = '\n'.join(sql_lines)
    original_sql = sql
    changes = []

    # 1. Fix TVF signatures first (before name replacements)
    for pattern, replacement in TVF_SIGNATURE_FIXES.items():
        new_sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
        if new_sql != sql:
            changes.append(f"Fixed TVF signature: {pattern} → {replacement}")
            sql = new_sql

    # 1b. Apply QUERY_REWRITES for major SQL structure fixes
    for pattern, replacement in QUERY_REWRITES.items():
        new_sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE | re.DOTALL)
        if new_sql != sql:
            changes.append(f"Rewrote query: {pattern[:40]}...")
            sql = new_sql

    # 2. Fix TVF names (for any remaining simple name references)
    # Use word boundaries to avoid matching partial names (e.g., get_cost_forecast in get_cost_forecast_summary)
    for old_name, new_name in TVF_REPLACEMENTS.items():
        # Create pattern with word boundary to match exact function name
        # Word boundary before, and followed by '(' or end-of-word
        pattern = r'\b' + re.escape(old_name) + r'(?=\s*\()'
        if re.search(pattern, sql):
            sql = re.sub(pattern, new_name, sql)
            changes.append(f"Renamed TVF: {old_name} → {new_name}")

    # 3. REMOVE TABLE() wrapper for TVF calls - Databricks SQL UDTFs don't need it
    # The TABLE() wrapper is actually causing NOT_A_SCALAR_FUNCTION errors
    # Databricks SQL user-defined table functions use syntax: FROM function_name(args)
    table_wrapper_pattern = r'TABLE\s*\(\s*(\$\{catalog\}\.\$\{gold_schema\}\.get_\w+\s*\([^)]*\))\s*\)'
    for match in re.finditer(table_wrapper_pattern, sql, re.IGNORECASE):
        full_match = match.group(0)  # TABLE(catalog.schema.func(...))
        tvf_call = match.group(1)    # catalog.schema.func(...)
        sql = sql.replace(full_match, tvf_call)
        changes.append(f"Removed TABLE() wrapper: {tvf_call[:50]}...")

    # 4. Remove date filters from metric view queries (they may not have these columns)
    if 'mv_data_quality' in sql or 'mv_ml_intelligence' in sql or 'mv_cost_analytics' in sql:
        for pattern in DATE_FILTER_PATTERNS_TO_REMOVE:
            new_sql = re.sub(pattern, '', sql, flags=re.IGNORECASE)
            if new_sql != sql:
                changes.append(f"Removed date filter: {pattern[:30]}...")
                sql = new_sql

    # 5. Fix column names in metric view queries (if any remaining)
    if 'mv_data_quality' in sql or 'mv_ml_intelligence' in sql or 'mv_cost_analytics' in sql:
        for old_col, new_col in COLUMN_FIXES.items():
            if old_col in sql:
                sql = sql.replace(old_col, new_col)
                changes.append(f"Fixed column: {old_col} → {new_col}")

    # 6. Fix TVF output column references
    # Only in TVF contexts (FROM TABLE(...))
    if 'TABLE(' in sql:
        for old_col, new_col in TVF_COLUMN_FIXES.items():
            # Only replace when it's a column reference, not part of another word
            pattern = r'\b' + old_col + r'\b'
            if re.search(pattern, sql):
                sql = re.sub(pattern, new_col, sql)
                if old_col != new_col:
                    changes.append(f"Fixed TVF column: {old_col} → {new_col}")

    # 7. Fix specific freshness_status → is_stale comparison
    # Change WHERE freshness_status IN ('STALE', 'CRITICAL') to WHERE is_stale = TRUE
    # Also handle already-renamed is_stale column with string comparison
    new_sql = re.sub(
        r"WHERE\s+freshness_status\s+IN\s*\(\s*'STALE'\s*,\s*'CRITICAL'\s*\)",
        "WHERE is_stale = TRUE",
        sql,
        flags=re.IGNORECASE
    )
    if new_sql != sql:
        changes.append("Fixed: freshness_status IN ('STALE','CRITICAL') → is_stale = TRUE")
        sql = new_sql

    new_sql = re.sub(
        r"WHERE\s+is_stale\s+IN\s*\(\s*'STALE'\s*,\s*'CRITICAL'\s*\)",
        "WHERE is_stale = TRUE",
        sql,
        flags=re.IGNORECASE
    )
    if new_sql != sql:
        changes.append("Fixed: is_stale IN ('STALE','CRITICAL') → is_stale = TRUE")
        sql = new_sql

    # Also handle CASE WHEN is_stale IN (...) patterns
    new_sql = re.sub(
        r"is_stale\s+IN\s*\(\s*'STALE'\s*,\s*'CRITICAL'\s*\)",
        "is_stale = TRUE",
        sql,
        flags=re.IGNORECASE
    )
    if new_sql != sql:
        changes.append("Fixed: is_stale IN (...) → is_stale = TRUE")
        sql = new_sql

    # Also handle WHERE is_stale = 'FRESH' → WHERE is_stale = FALSE
    new_sql = re.sub(
        r"WHERE\s+is_stale\s*=\s*'FRESH'",
        "WHERE is_stale = FALSE",
        sql,
        flags=re.IGNORECASE
    )
    if new_sql != sql:
        changes.append("Fixed: is_stale = 'FRESH' → is_stale = FALSE")
        sql = new_sql

    # Handle WHERE freshness_status = 'FRESH'
    new_sql = re.sub(
        r"WHERE\s+freshness_status\s*=\s*'FRESH'",
        "WHERE is_stale = FALSE",
        sql,
        flags=re.IGNORECASE
    )
    if new_sql != sql:
        changes.append("Fixed: freshness_status = 'FRESH' → is_stale = FALSE")
        sql = new_sql

    # Split back to lines
    fixed_lines = sql.split('\n')

    # Only report if actual changes were made
    if sql != original_sql:
        return fixed_lines, changes

    return sql_lines, []


def fix_genie_space_file(file_path: Path, dry_run: bool = False) -> Dict:
    """Fix all SQL issues in a single Genie Space JSON export file."""

    with open(file_path, 'r') as f:
        data = json.load(f)

    genie_name = file_path.stem.replace('_genie_export', '')
    fixes_made = []

    # Fix benchmark questions
    benchmarks = data.get('benchmarks', {})
    questions = benchmarks.get('questions', [])

    for idx, question in enumerate(questions, 1):
        # Get SQL content
        if 'answer' in question:
            answers = question.get('answer', [])
            if answers and answers[0].get('format') == 'SQL':
                content = answers[0].get('content', [])
                if isinstance(content, list):
                    fixed_content, changes = fix_sql_content(content, genie_name, idx)
                    if changes:
                        answers[0]['content'] = fixed_content
                        fixes_made.append({
                            'question_num': idx,
                            'question_text': ''.join(question.get('question', []))[:60],
                            'changes': changes
                        })
        elif 'sql' in question:
            sql = question.get('sql', [])
            if isinstance(sql, list):
                fixed_sql, changes = fix_sql_content(sql, genie_name, idx)
                if changes:
                    question['sql'] = fixed_sql
                    fixes_made.append({
                        'question_num': idx,
                        'question_text': ''.join(question.get('question', []))[:60],
                        'changes': changes
                    })
        elif 'query' in question:
            query = question.get('query', [])
            if isinstance(query, list):
                fixed_query, changes = fix_sql_content(query, genie_name, idx)
                if changes:
                    question['query'] = fixed_query
                    fixes_made.append({
                        'question_num': idx,
                        'question_text': ''.join(question.get('question', []))[:60],
                        'changes': changes
                    })

    # Fix curated_questions (v2 format)
    curated = data.get('curated_questions', [])
    for idx, question in enumerate(curated, 1):
        if 'query' in question:
            query = question.get('query', [])
            # Handle both list and string formats
            if isinstance(query, str):
                query_lines = query.split('\n')
            else:
                query_lines = query

            fixed_query, changes = fix_sql_content(query_lines, genie_name, idx)
            if changes:
                # Preserve original format (string or list)
                if isinstance(question['query'], str):
                    question['query'] = '\n'.join(fixed_query)
                else:
                    question['query'] = fixed_query
                fixes_made.append({
                    'question_num': f"curated_{idx}",
                    'question_text': ''.join(question.get('question', []))[:60] if isinstance(question.get('question', ''), list) else question.get('question', '')[:60],
                    'changes': changes
                })

    # Fix example_question_sqls
    instructions = data.get('instructions', {})
    if not isinstance(instructions, dict):
        instructions = {}
    examples = instructions.get('example_question_sqls', [])
    for idx, example in enumerate(examples, 1):
        if 'sql' in example:
            sql = example.get('sql', [])
            if isinstance(sql, list):
                fixed_sql, changes = fix_sql_content(sql, genie_name, f"example_{idx}")
                if changes:
                    example['sql'] = fixed_sql
                    fixes_made.append({
                        'question_num': f"example_{idx}",
                        'question_text': ''.join(example.get('question', []))[:60],
                        'changes': changes
                    })

    # Fix sql_functions references
    sql_functions = instructions.get('sql_functions', [])
    for func in sql_functions:
        identifier = func.get('identifier', '')
        for old_name, new_name in TVF_REPLACEMENTS.items():
            if old_name in identifier:
                func['identifier'] = identifier.replace(old_name, new_name)
                fixes_made.append({
                    'question_num': 'sql_functions',
                    'question_text': f"TVF reference: {old_name}",
                    'changes': [f"Renamed: {old_name} → {new_name}"]
                })

    # Fix text_instructions
    text_instructions = instructions.get('text_instructions', [])
    for ti in text_instructions:
        if isinstance(ti, dict):
            content = ti.get('content', [])
            if isinstance(content, list):
                fixed_content = []
                for line in content:
                    if isinstance(line, str):
                        for old_name, new_name in TVF_REPLACEMENTS.items():
                            if old_name in line:
                                line = line.replace(old_name, new_name)
                    fixed_content.append(line)
                ti['content'] = fixed_content

    # Write fixed file (if not dry run)
    if not dry_run and fixes_made:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    return {
        'file': str(file_path.name),
        'genie_space': genie_name,
        'fixes_count': len(fixes_made),
        'fixes': fixes_made
    }


def fix_all_genie_spaces(genie_dir: Path, dry_run: bool = False) -> List[Dict]:
    """Fix all Genie Space JSON export files in a directory."""

    json_files = list(genie_dir.glob("*_genie_export.json"))

    print(f"{'='*80}")
    print(f"GENIE SPACE SQL FIX TOOL")
    print(f"{'='*80}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'APPLYING FIXES'}")
    print(f"Directory: {genie_dir}")
    print(f"Found {len(json_files)} Genie Space JSON files")
    print()

    results = []
    total_fixes = 0

    for json_file in sorted(json_files):
        print(f"Processing: {json_file.name}")
        result = fix_genie_space_file(json_file, dry_run)
        results.append(result)
        total_fixes += result['fixes_count']

        if result['fixes_count'] > 0:
            print(f"  ✓ Fixed {result['fixes_count']} items")
            for fix in result['fixes'][:3]:  # Show first 3 fixes
                print(f"    - Q{fix['question_num']}: {', '.join(fix['changes'][:2])}")
            if len(result['fixes']) > 3:
                print(f"    ... and {len(result['fixes']) - 3} more")
        else:
            print(f"  - No changes needed")

    print()
    print(f"{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total files processed: {len(json_files)}")
    print(f"Total fixes applied: {total_fixes}")

    if dry_run:
        print("\n⚠️ DRY RUN - No files were modified")
        print("Run with dry_run=False to apply changes")
    else:
        print("\n✓ All fixes have been applied")

    return results


if __name__ == '__main__':
    import sys

    genie_dir = Path('.')
    dry_run = '--dry-run' in sys.argv

    fix_all_genie_spaces(genie_dir, dry_run)
