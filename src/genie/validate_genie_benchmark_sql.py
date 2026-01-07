"""
Genie Space Benchmark SQL Validator
====================================

Validates SQL queries in Genie Space JSON export benchmark sections.
Catches syntax, column resolution, table reference, and runtime errors before deployment.

Extracts SQL from JSON export files' benchmarks.questions section and validates using SELECT LIMIT 1.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
from pyspark.sql import SparkSession


def extract_benchmark_queries_from_json(json_path: Path, catalog: str, gold_schema: str, feature_schema: str = None) -> List[Dict]:
    """Extract all benchmark SQL queries from a Genie Space JSON export file.

    Handles multiple JSON structures:
    - v1 format with benchmarks.questions[].answer[].content (data_quality, job_health, unified)
    - v1 format with benchmarks.questions[].sql (cost_intelligence)
    - v1 format with benchmarks.questions[].query (security_auditor)
    - v2 format with curated_questions[].query (performance)
    """

    with open(json_path, 'r') as f:
        data = json.load(f)

    queries = []
    genie_space_name = json_path.stem.replace('_genie_export', '')

    # Default feature_schema to gold_schema + "_ml" if not provided
    if feature_schema is None:
        feature_schema = f"{gold_schema}_ml"

    def substitute_variables(sql: str) -> str:
        """Substitute template variables in SQL."""
        sql = sql.replace('${catalog}', catalog)
        sql = sql.replace('${gold_schema}', gold_schema)
        sql = sql.replace('${feature_schema}', feature_schema)
        sql = sql.replace('${ml_schema}', feature_schema)  # Legacy alias
        return sql

    def extract_sql_from_item(item: dict, format_type: str) -> tuple:
        """Extract SQL query and question text from a benchmark item based on format type."""
        sql_query = None
        question_text = None

        # Get question text (may be string or array)
        q = item.get('question', '')
        if isinstance(q, list):
            question_text = ''.join(q)
        else:
            question_text = q

        # Try different SQL field names based on format
        # Join with newlines to preserve SQL structure
        if format_type == 'answer':
            # Format: answer[].content (array of strings)
            answers = item.get('answer', [])
            if answers:
                answer = answers[0]
                if answer.get('format') == 'SQL':
                    content = answer.get('content', [])
                    sql_query = '\n'.join(content) if isinstance(content, list) else content
        elif format_type == 'sql':
            # Format: sql (array of strings or string)
            sql = item.get('sql', [])
            sql_query = '\n'.join(sql) if isinstance(sql, list) else sql
        elif format_type == 'query':
            # Format: query (array of strings or string)
            query = item.get('query', [])
            sql_query = '\n'.join(query) if isinstance(query, list) else query

        return sql_query, question_text

    def detect_format_type(questions_list: list) -> str:
        """Detect which format the benchmark questions use."""
        if not questions_list:
            return 'unknown'

        sample = questions_list[0]
        if 'answer' in sample:
            return 'answer'
        elif 'sql' in sample:
            return 'sql'
        elif 'query' in sample:
            return 'query'
        return 'unknown'

    # Check for v2 format (curated_questions)
    curated_questions = data.get('curated_questions', [])
    if curated_questions:
        print(f"   📋 Detected v2 format (curated_questions) in {json_path.name}")
        format_type = detect_format_type(curated_questions)

        for idx, item in enumerate(curated_questions, 1):
            sql_query, question_text = extract_sql_from_item(item, format_type)

            if not sql_query:
                # print(f"⚠️  No SQL found for curated question {idx} in {json_path.name}")
                continue

            sql_query = substitute_variables(sql_query)

            queries.append({
                'genie_space': genie_space_name,
                'question_num': str(idx),
                'question_text': question_text,
                'query': sql_query,
                'original_query': sql_query,
                'benchmark_id': item.get('question_id', item.get('id', 'unknown'))
            })

    # Check for v1 format (benchmarks.questions)
    benchmarks = data.get('benchmarks', {})
    benchmark_questions = benchmarks.get('questions', [])

    if benchmark_questions:
        format_type = detect_format_type(benchmark_questions)
        print(f"   📋 Detected v1 format ({format_type}) in {json_path.name}")

        for idx, item in enumerate(benchmark_questions, 1):
            sql_query, question_text = extract_sql_from_item(item, format_type)

            if not sql_query:
                print(f"⚠️  No SQL found for benchmark {idx} in {json_path.name}")
                continue

            sql_query = substitute_variables(sql_query)

            queries.append({
                'genie_space': genie_space_name,
                'question_num': str(idx),
                'question_text': question_text,
                'query': sql_query,
                'original_query': sql_query,
                'benchmark_id': item.get('id', 'unknown')
            })

    if not queries:
        print(f"⚠️  No benchmark queries found in {json_path.name}")

    return queries


def validate_query(spark: SparkSession, query_info: Dict) -> Dict:
    """Validate a single SQL query by executing it with LIMIT 1.
    
    Using SELECT LIMIT 1 instead of EXPLAIN because:
    - EXPLAIN may not catch all column resolution errors
    - EXPLAIN may not catch type mismatches
    - SELECT LIMIT 1 validates the full execution path
    - Only returns 1 row, so it's still fast
    """
    
    result = {
        'genie_space': query_info['genie_space'],
        'question_num': query_info['question_num'],
        'question_text': query_info['question_text'],
        'valid': False,
        'error': None,
        'error_type': None
    }
    
    try:
        # Wrap query with LIMIT 1 for fast validation
        # This catches ALL errors - syntax, columns, types, runtime
        original_query = query_info['query'].strip().rstrip(';')

        # DEBUG: Print first 200 chars of query for troubleshooting
        if query_info['genie_space'] == 'performance' and str(query_info['question_num']) == '5':
            print(f"\n=== DEBUG Q5 ===")
            print(f"Question num: {query_info['question_num']} (type: {type(query_info['question_num'])})")
            print(f"Query type: {type(original_query)}")
            print(f"Query (first 300 chars): {repr(original_query[:300])}")
            print(f"Has TABLE(: {'TABLE(' in original_query}")
            print(f"=== END DEBUG ===\n")

        # Handle queries - for TVF queries or queries with LIMIT, replace LIMIT value
        # For other queries, just add LIMIT 1
        if 'LIMIT' in original_query.upper():
            # Replace existing LIMIT with LIMIT 1
            validation_query = re.sub(r'LIMIT\s+\d+', 'LIMIT 1', original_query, flags=re.IGNORECASE)
        else:
            validation_query = f"{original_query} LIMIT 1"

        # DEBUG: Show full validation query for Q5
        if query_info['genie_space'] == 'performance' and str(query_info['question_num']) == '5':
            print(f"\n=== DEBUG Q5 FULL VALIDATION QUERY ===")
            print(f"{validation_query}")
            print(f"=== END DEBUG ===\n")

        # Actually execute the query
        spark.sql(validation_query).collect()
        result['valid'] = True
        
    except Exception as e:
        error_str = str(e)
        result['error'] = error_str

        # DEBUG: Show SQL for NOT_A_SCALAR_FUNCTION errors
        if 'NOT_A_SCALAR_FUNCTION' in error_str:
            print(f"\n=== NOT_A_SCALAR_FUNCTION ERROR ===")
            print(f"Genie Space: {query_info['genie_space']}")
            print(f"Question: {query_info['question_num']}")
            print(f"Original Query:\n{original_query[:500]}")
            print(f"Validation Query:\n{validation_query[:500]}")
            print(f"=== END ===\n")

        # Categorize the error
        if 'UNRESOLVED_COLUMN' in error_str:
            result['error_type'] = 'COLUMN_NOT_FOUND'
            match = re.search(r"name `([^`]+)`", error_str)
            if match:
                result['error_column'] = match.group(1)
            match = re.search(r"Did you mean one of the following\? \[([^\]]+)\]", error_str)
            if match:
                result['suggestions'] = match.group(1)
                
        elif 'AMBIGUOUS_REFERENCE' in error_str:
            result['error_type'] = 'AMBIGUOUS_COLUMN'
            match = re.search(r"Reference `([^`]+)`", error_str)
            if match:
                result['error_column'] = match.group(1)
                
        elif 'PARSE_SYNTAX_ERROR' in error_str:
            result['error_type'] = 'SYNTAX_ERROR'
            match = re.search(r"at or near '([^']+)'", error_str)
            if match:
                result['error_near'] = match.group(1)
                
        elif 'TABLE_OR_VIEW_NOT_FOUND' in error_str:
            result['error_type'] = 'TABLE_NOT_FOUND'
            match = re.search(r"table or view `([^`]+)`", error_str)
            if match:
                result['missing_table'] = match.group(1)
                
        elif 'UNRESOLVED_ROUTINE' in error_str:
            result['error_type'] = 'FUNCTION_NOT_FOUND'
            match = re.search(r"routine `([^`]+)`", error_str)
            if match:
                result['missing_function'] = match.group(1)
        else:
            result['error_type'] = 'OTHER'
    
    return result


def generate_validation_report(results: List[Dict]) -> str:
    """Generate a detailed validation report."""
    
    valid_count = sum(1 for r in results if r['valid'])
    invalid_count = len(results) - valid_count
    
    report = []
    report.append("=" * 80)
    report.append("GENIE SPACE BENCHMARK SQL VALIDATION REPORT")
    report.append("=" * 80)
    report.append(f"\nTotal benchmark queries validated: {len(results)}")
    report.append(f"✓ Valid: {valid_count}")
    report.append(f"✗ Invalid: {invalid_count}")
    report.append("")
    
    if invalid_count == 0:
        report.append("🎉 All benchmark queries passed validation!")
        return "\n".join(report)
    
    # Group errors by Genie Space
    errors_by_space = {}
    for r in results:
        if not r['valid']:
            space = r['genie_space']
            if space not in errors_by_space:
                errors_by_space[space] = []
            errors_by_space[space].append(r)
    
    # Report errors by Genie Space
    report.append("\n" + "-" * 80)
    report.append("ERRORS BY GENIE SPACE")
    report.append("-" * 80)
    
    for space, errors in sorted(errors_by_space.items()):
        report.append(f"\n### {space.upper()} ({len(errors)} errors)")
        report.append("")
        
        for err in errors:
            report.append(f"  ❌ Question {err['question_num']}: \"{err['question_text']}\"")
            report.append(f"     Error Type: {err.get('error_type', 'UNKNOWN')}")
            
            if err.get('error_type') == 'COLUMN_NOT_FOUND':
                report.append(f"     Column: `{err.get('error_column', 'unknown')}`")
                if 'suggestions' in err:
                    report.append(f"     Suggestions: {err['suggestions']}")
                    
            elif err.get('error_type') == 'AMBIGUOUS_COLUMN':
                report.append(f"     Column: `{err.get('error_column', 'unknown')}`")
                report.append(f"     Fix: Qualify with table alias")
                
            elif err.get('error_type') == 'SYNTAX_ERROR':
                report.append(f"     Error near: '{err.get('error_near', 'unknown')}'")
                
            elif err.get('error_type') == 'TABLE_NOT_FOUND':
                report.append(f"     Missing table: {err.get('missing_table', 'unknown')}")
                
            elif err.get('error_type') == 'FUNCTION_NOT_FOUND':
                report.append(f"     Missing function: {err.get('missing_function', 'unknown')}")
            
            report.append("")
    
    # Detailed error list
    report.append("\n" + "-" * 80)
    report.append("DETAILED ERRORS (for debugging)")
    report.append("-" * 80)
    
    for r in results:
        if not r['valid']:
            report.append(f"\n❌ {r['genie_space']} - Question {r['question_num']}")
            report.append(f"   Question: \"{r['question_text']}\"")
            report.append(f"   Error: {r['error'][:500]}...")
            report.append("")
    
    return "\n".join(report)


def validate_all_genie_benchmarks(genie_dir: Path, catalog: str, gold_schema: str, spark: SparkSession, feature_schema: str = None) -> Tuple[bool, List[Dict]]:
    """
    Validate all benchmark queries in all Genie Space JSON export files.
    
    Returns:
        (success: bool, results: List[Dict])
    """
    
    # Find all Genie Space JSON export files
    json_files = list(genie_dir.glob("*_genie_export.json"))
    
    if not json_files:
        print(f"⚠️  No Genie Space JSON export files found in {genie_dir}")
        print(f"    Expected files matching pattern: *_genie_export.json")
        return False, []
    
    print(f"📋 Found {len(json_files)} Genie Space JSON export files")
    
    # Extract all benchmark queries from JSON exports
    all_queries = []
    for json_file in json_files:
        queries = extract_benchmark_queries_from_json(json_file, catalog, gold_schema, feature_schema)
        all_queries.extend(queries)
        print(f"   {json_file.name}: {len(queries)} benchmark queries")
    
    if not all_queries:
        print("⚠️  No benchmark queries found in JSON exports!")
        print("    Check that JSON files have 'benchmarks.questions' section")
        return False, []
    
    print(f"\n🔍 Validating {len(all_queries)} benchmark queries from JSON exports using SELECT LIMIT 1...")
    print("   (This executes each query to catch ALL errors)")
    print("-" * 80)
    
    # Validate each query
    results = []
    for i, query_info in enumerate(all_queries):
        result = validate_query(spark, query_info)
        results.append(result)
        
        status = "✓" if result['valid'] else "✗"
        print(f"  [{i+1}/{len(all_queries)}] {status} {query_info['genie_space']} Q{query_info['question_num']}")
    
    # Generate report
    report = generate_validation_report(results)
    print("\n" + report)
    
    # Check if all passed
    invalid_count = sum(1 for r in results if not r['valid'])
    success = (invalid_count == 0)
    
    return success, results

