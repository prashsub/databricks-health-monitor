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


def extract_benchmark_queries_from_json(json_path: Path, catalog: str, gold_schema: str) -> List[Dict]:
    """Extract all benchmark SQL queries from a Genie Space JSON export file."""
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    queries = []
    genie_space_name = json_path.stem.replace('_genie_export', '')
    
    # Extract benchmarks section
    benchmarks = data.get('benchmarks', {})
    questions = benchmarks.get('questions', [])
    
    if not questions:
        print(f"⚠️  No benchmark questions found in {json_path.name}")
        return queries
    
    for idx, benchmark in enumerate(questions, 1):
        question_text = ''.join(benchmark.get('question', []))
        answers = benchmark.get('answer', [])
        
        if not answers:
            print(f"⚠️  No answer found for benchmark {idx} in {json_path.name}")
            continue
        
        # Get SQL from first answer (should only be one)
        answer = answers[0]
        if answer.get('format') != 'SQL':
            print(f"⚠️  Benchmark {idx} is not SQL format in {json_path.name}")
            continue
        
        # SQL is stored as array of lines - join them
        sql_lines = answer.get('content', [])
        sql_query = ''.join(sql_lines)
        
        # Substitute variables
        sql_query = sql_query.replace('${catalog}', catalog)
        sql_query = sql_query.replace('${gold_schema}', gold_schema)
        
        queries.append({
            'genie_space': genie_space_name,
            'question_num': str(idx),
            'question_text': question_text,
            'query': sql_query,
            'original_query': ''.join(sql_lines),
            'benchmark_id': benchmark.get('id', 'unknown')
        })
    
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
        
        # Handle queries that already have LIMIT - wrap in subquery
        if 'LIMIT' in original_query.upper():
            validation_query = f"SELECT * FROM ({original_query}) AS validation_subquery LIMIT 1"
        else:
            validation_query = f"{original_query} LIMIT 1"
        
        # Actually execute the query
        spark.sql(validation_query).collect()
        result['valid'] = True
        
    except Exception as e:
        error_str = str(e)
        result['error'] = error_str
        
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


def validate_all_genie_benchmarks(genie_dir: Path, catalog: str, gold_schema: str, spark: SparkSession) -> Tuple[bool, List[Dict]]:
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
        queries = extract_benchmark_queries_from_json(json_file, catalog, gold_schema)
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

