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


def validate_query(spark: SparkSession, query_info: Dict, catalog: str, gold_schema: str) -> Dict:
    """Validate a single SQL query by EXECUTING it with LIMIT 1.
    
    Why execute instead of EXPLAIN:
    - EXPLAIN may miss runtime errors (type mismatches, NULL handling, etc.)
    - LIMIT 1 catches ALL errors while being fast (returns only 1 row)
    - Full execution path validation ensures queries work in production
    
    Catalog/Schema Context:
    - Sets USE CATALOG and USE SCHEMA before each query
    - This allows TVFs to use simple names (get_slow_queries) instead of
      three-part names (catalog.schema.get_slow_queries)
    - Works around Spark SQL bug with TABLE() wrapper and three-part names
    """
    
    result = {
        'genie_space': query_info['genie_space'],
        'question_num': query_info['question_num'],
        'question_text': query_info['question_text'],
        'query': query_info['query'][:200] + '...' if len(query_info['query']) > 200 else query_info['query'],
        'valid': False,
        'error': None,
        'error_type': None
    }
    
    try:
        # Set catalog/schema context BEFORE executing query
        # This enables simple TVF names without three-part identifiers
        spark.sql(f"USE CATALOG {catalog}").collect()
        spark.sql(f"USE SCHEMA {gold_schema}").collect()
        
        # Wrap query with LIMIT 1 for fast but complete validation
        # This catches ALL errors: syntax, columns, types, runtime logic
        original_query = query_info['query'].strip().rstrip(';')

        # Determine if we need to wrap with SELECT * FROM ()
        # CTEs and complex queries need wrapping, simple SELECT can append LIMIT 1
        needs_wrapping = (
            'WITH ' in original_query.upper()[:50] or
            original_query.upper().strip().startswith('SELECT') is False
        )
        
        if needs_wrapping:
            # Wrap complex queries (CTEs, etc.) to add LIMIT 1
            validation_query = f"SELECT * FROM ({original_query}) LIMIT 1"
        else:
            # Simple SELECT - just append LIMIT 1
            # Remove existing LIMIT clause if present
            validation_query = re.sub(r'\s+LIMIT\s+\d+\s*$', '', original_query, flags=re.IGNORECASE)
            validation_query = f"{validation_query} LIMIT 1"

        # EXECUTE the query (not just EXPLAIN)
        result_df = spark.sql(validation_query)
        
        # Force execution by calling collect() - catches all runtime errors
        result_df.collect()
        
        result['valid'] = True
        
    except Exception as e:
        error_str = str(e)
        result['error'] = error_str
        result['sql_query'] = original_query  # Store full query for debugging

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


def validate_all_genie_benchmarks(genie_dir: Path, catalog: str, gold_schema: str, spark: SparkSession, feature_schema: str = None, genie_space_filter: str = None) -> Tuple[bool, List[Dict]]:
    """
    Validate all benchmark queries in all Genie Space JSON export files.
    
    Args:
        genie_dir: Directory containing Genie Space JSON files
        catalog: Unity Catalog name
        gold_schema: Gold layer schema name
        spark: SparkSession
        feature_schema: Feature/ML schema name (optional)
        genie_space_filter: Optional filename to validate only one space (e.g., "cost_intelligence_genie_export.json")
    
    Returns:
        (success: bool, results: List[Dict])
    """
    
    # Find all Genie Space JSON export files
    if genie_space_filter:
        # Validate only the specified file
        json_files = [genie_dir / genie_space_filter]
        if not json_files[0].exists():
            print(f"⚠️  Genie Space file not found: {genie_space_filter}")
            print(f"    Searched in: {genie_dir}")
            return False, []
    else:
        # Validate all files
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
    
    # Validate each query with timing and immediate error reporting
    import time
    results = []
    error_count = 0
    start_time = time.time()
    
    for i, query_info in enumerate(all_queries):
        query_start = time.time()
        result = validate_query(spark, query_info, catalog, gold_schema)
        query_duration = time.time() - query_start
        results.append(result)
        
        status = "✓" if result['valid'] else "✗"
        
        # Show timing for slow queries or errors
        timing_str = f" ({query_duration:.1f}s)" if (query_duration > 5.0 or not result['valid']) else ""
        print(f"  [{i+1}/{len(all_queries)}] {status} {query_info['genie_space']} Q{query_info['question_num']}{timing_str}")
        
        # Print error details IMMEDIATELY
        if not result['valid']:
            error_count += 1
            error_type = result.get('error_type', 'UNKNOWN')
            error_msg = result.get('error', 'No error message')[:300]
            
            print(f"      ❌ {error_type}: {error_msg}")
            
            # Print question text for context
            question_text = query_info.get('question_text', '')[:100]
            if question_text:
                print(f"      💬 Question: {question_text}...")
            
            # Print specific error details based on type
            if error_type == 'COLUMN_NOT_FOUND':
                column = result.get('error_column', 'unknown')
                suggestions = result.get('suggestions', '')
                print(f"      🔎 Missing column: {column}")
                if suggestions:
                    print(f"      💡 Did you mean: {suggestions}")
            elif error_type == 'TABLE_NOT_FOUND':
                table = result.get('missing_table', 'unknown')
                print(f"      🔎 Missing table: {table}")
            elif error_type == 'FUNCTION_NOT_FOUND':
                func = result.get('missing_function', 'unknown')
                print(f"      🔎 Missing function: {func}")
            
            # Print running summary every 10 errors
            if error_count % 10 == 0:
                elapsed = time.time() - start_time
                valid_count = (i + 1) - error_count
                print(f"      📊 Running Total: {error_count} errors / {valid_count} passed in {elapsed:.0f}s ({i+1}/{len(all_queries)} done)\n")
    
    # Generate report
    report = generate_validation_report(results)
    print("\n" + report)
    
    # Check if all passed
    invalid_count = sum(1 for r in results if not r['valid'])
    success = (invalid_count == 0)
    
    return success, results

