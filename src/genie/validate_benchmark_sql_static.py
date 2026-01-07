"""
Static Genie Space Benchmark SQL Validator
==========================================

Performs static validation of SQL queries in Genie Space benchmark sections
without requiring a Spark session. Ideal for pre-deployment CI/CD checks.

Validation checks:
1. Template variable substitution completeness
2. Basic SQL syntax structure
3. Table/view reference consistency
4. TVF (Table-Valued Function) call syntax
5. MEASURE() function usage in metric views
6. Common SQL anti-patterns
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime


class SQLValidationResult:
    """Stores validation result for a single SQL query."""

    def __init__(self, genie_space: str, question_num: str, question_text: str, sql: str, benchmark_id: str):
        self.genie_space = genie_space
        self.question_num = question_num
        self.question_text = question_text
        self.sql = sql
        self.benchmark_id = benchmark_id
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, error_type: str, message: str, line: Optional[int] = None):
        self.errors.append({'type': error_type, 'message': message, 'line': line})

    def add_warning(self, warning_type: str, message: str, line: Optional[int] = None):
        self.warnings.append({'type': warning_type, 'message': message, 'line': line})


def extract_all_benchmark_queries(genie_dir: Path, catalog: str = 'health_monitor',
                                   gold_schema: str = 'gold',
                                   feature_schema: str = None) -> List[SQLValidationResult]:
    """Extract all benchmark SQL queries from all Genie Space JSON export files."""

    if feature_schema is None:
        feature_schema = f"{gold_schema}_ml"

    results = []
    json_files = list(genie_dir.glob("*_genie_export.json"))

    print(f"\n{'='*80}")
    print(f"GENIE SPACE BENCHMARK SQL STATIC VALIDATOR")
    print(f"{'='*80}")
    print(f"\nScanning directory: {genie_dir}")
    print(f"Found {len(json_files)} Genie Space JSON export files")
    print(f"Template variables: catalog={catalog}, gold_schema={gold_schema}, feature_schema={feature_schema}")
    print()

    for json_file in sorted(json_files):
        queries = extract_queries_from_file(json_file, catalog, gold_schema, feature_schema)
        results.extend(queries)
        print(f"  {json_file.name}: {len(queries)} benchmark queries")

    print(f"\nTotal benchmark queries to validate: {len(results)}")
    return results


def extract_queries_from_file(json_path: Path, catalog: str, gold_schema: str,
                               feature_schema: str) -> List[SQLValidationResult]:
    """Extract queries from a single Genie Space JSON export file."""

    with open(json_path, 'r') as f:
        data = json.load(f)

    results = []
    genie_space_name = json_path.stem.replace('_genie_export', '')

    def substitute_vars(sql: str) -> str:
        sql = sql.replace('${catalog}', catalog)
        sql = sql.replace('${gold_schema}', gold_schema)
        sql = sql.replace('${feature_schema}', feature_schema)
        sql = sql.replace('${ml_schema}', feature_schema)
        return sql

    def extract_sql(item: dict) -> Tuple[Optional[str], str]:
        """Extract SQL and question from a benchmark item."""
        q = item.get('question', '')
        question_text = ''.join(q) if isinstance(q, list) else q

        sql = None
        # Try different formats - join with newlines to preserve SQL structure
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

    # Process curated_questions (v2 format)
    for idx, item in enumerate(data.get('curated_questions', []), 1):
        sql, question_text = extract_sql(item)
        if sql:
            sql = substitute_vars(sql)
            results.append(SQLValidationResult(
                genie_space=genie_space_name,
                question_num=str(idx),
                question_text=question_text,
                sql=sql,
                benchmark_id=item.get('question_id', item.get('id', 'unknown'))
            ))

    # Process benchmarks.questions (v1 format)
    for idx, item in enumerate(data.get('benchmarks', {}).get('questions', []), 1):
        sql, question_text = extract_sql(item)
        if sql:
            sql = substitute_vars(sql)
            results.append(SQLValidationResult(
                genie_space=genie_space_name,
                question_num=str(idx),
                question_text=question_text,
                sql=sql,
                benchmark_id=item.get('id', 'unknown')
            ))

    return results


def validate_sql_static(result: SQLValidationResult) -> SQLValidationResult:
    """Perform static validation checks on a SQL query."""

    sql = result.sql.strip()
    sql_upper = sql.upper()

    # 1. Check for unsubstituted template variables
    unresolved = re.findall(r'\$\{[^}]+\}', sql)
    if unresolved:
        result.add_error('UNRESOLVED_VARIABLE', f"Unsubstituted variables: {', '.join(unresolved)}")

    # 2. Check basic SQL structure
    if not any(sql_upper.startswith(kw) for kw in ['SELECT', 'WITH']):
        result.add_error('INVALID_START', "SQL must start with SELECT or WITH")

    # 3. Check for unclosed parentheses
    open_parens = sql.count('(')
    close_parens = sql.count(')')
    if open_parens != close_parens:
        result.add_error('UNBALANCED_PARENS', f"Unbalanced parentheses: {open_parens} open, {close_parens} close")

    # 4. Check for unclosed quotes
    single_quotes = sql.count("'") - sql.count("\\'")
    if single_quotes % 2 != 0:
        result.add_error('UNCLOSED_QUOTES', "Unclosed single quotes detected")

    # 5. Check TABLE() wrapper for TVF calls
    tvf_patterns = [
        r'FROM\s+\$?\{?[a-z_]+\}?\.\$?\{?[a-z_]+\}?\.get_\w+\s*\(',
        r'JOIN\s+\$?\{?[a-z_]+\}?\.\$?\{?[a-z_]+\}?\.get_\w+\s*\('
    ]
    for pattern in tvf_patterns:
        matches = re.findall(pattern, sql, re.IGNORECASE)
        for match in matches:
            if 'TABLE(' not in sql_upper or not re.search(r'TABLE\s*\(\s*' + re.escape(match.split()[-1]), sql, re.IGNORECASE):
                # Check if the TVF is properly wrapped
                if not re.search(r'TABLE\s*\(\s*[^)]*get_\w+', sql, re.IGNORECASE):
                    result.add_warning('MISSING_TABLE_WRAPPER', f"TVF call may need TABLE() wrapper: {match.strip()}")

    # 6. Check for proper TVF TABLE() syntax
    tvf_calls = re.findall(r'TABLE\s*\(\s*([^)]+\.get_\w+\s*\([^)]*\))\s*\)', sql, re.IGNORECASE)
    if not tvf_calls and 'get_' in sql.lower():
        # Check if there's a TVF call without TABLE wrapper
        bare_tvf = re.findall(r'(?:FROM|JOIN)\s+([^\s(]+\.get_\w+)\s*\(', sql, re.IGNORECASE)
        for tvf in bare_tvf:
            result.add_error('TVF_NO_TABLE_WRAPPER', f"TVF call must be wrapped with TABLE(): {tvf}")

    # 7. Check MEASURE() function usage
    if 'MEASURE(' in sql_upper:
        # Verify it's used in SELECT clause
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_clause = select_match.group(1)
            if 'MEASURE(' not in select_clause.upper():
                result.add_warning('MEASURE_OUTSIDE_SELECT', "MEASURE() should be in SELECT clause")

    # 8. Check for common SQL mistakes (only in non-CTE contexts)
    # Note: Complex CTEs with multiple subqueries can legitimately have multiple WHERE/GROUP BY
    # So we only check for truly malformed patterns
    if not sql_upper.startswith('WITH'):
        # Only check for duplicates in non-CTE queries
        if re.search(r'GROUP\s+BY[^)]*GROUP\s+BY', sql_upper):
            result.add_warning('POSSIBLE_DUPLICATE_GROUP_BY', "Possible duplicate GROUP BY - verify structure")

        if re.search(r'WHERE[^)]*WHERE(?!\s+)', sql_upper):
            result.add_warning('POSSIBLE_DUPLICATE_WHERE', "Possible duplicate WHERE - verify structure")

    # 9. Check for dangerous patterns
    if re.search(r'DROP\s+(TABLE|VIEW|SCHEMA|DATABASE)', sql_upper):
        result.add_error('DANGEROUS_DDL', "DROP statements not allowed in benchmark queries")

    if re.search(r'DELETE\s+FROM', sql_upper):
        result.add_error('DANGEROUS_DML', "DELETE statements not allowed in benchmark queries")

    if re.search(r'TRUNCATE\s+TABLE', sql_upper):
        result.add_error('DANGEROUS_DML', "TRUNCATE statements not allowed in benchmark queries")

    # 10. Check for required filters on monitoring tables
    if '_profile_metrics' in sql.lower() or '_drift_metrics' in sql.lower():
        if "column_name = ':table'" not in sql and 'column_name = \':table\'' not in sql:
            result.add_warning('MISSING_MONITORING_FILTER',
                             "Lakehouse Monitoring tables require column_name = ':table' filter")

    # 11. Check for SELECT * without LIMIT in CTEs or main query
    if re.search(r'SELECT\s+\*\s+FROM(?!.*LIMIT)', sql_upper):
        result.add_warning('SELECT_STAR_NO_LIMIT', "SELECT * without LIMIT may return large result sets")

    # 12. Validate CTE structure
    # Note: We skip complex CTE validation as parenthesis counting is unreliable
    # due to function calls, string literals, etc. The balanced parens check at step 3 suffices.

    # 13. Check date function usage
    if 'CURRENT_DATE' in sql_upper:
        if not ('CURRENT_DATE()' in sql or 'CURRENT_DATE ()' in sql):
            # Databricks uses CURRENT_DATE() with parentheses
            if 'CURRENT_DATE -' in sql_upper or 'CURRENT_DATE-' in sql_upper:
                result.add_warning('DATE_FUNCTION_SYNTAX',
                                 "Use CURRENT_DATE() with parentheses in Databricks SQL")

    # 14. Check INTERVAL syntax
    interval_matches = re.findall(r'INTERVAL\s+(\d+)\s+(\w+)', sql, re.IGNORECASE)
    for value, unit in interval_matches:
        valid_units = ['DAY', 'DAYS', 'HOUR', 'HOURS', 'MINUTE', 'MINUTES', 'SECOND', 'SECONDS',
                       'WEEK', 'WEEKS', 'MONTH', 'MONTHS', 'YEAR', 'YEARS']
        if unit.upper() not in valid_units:
            result.add_error('INVALID_INTERVAL', f"Invalid INTERVAL unit: {unit}")

    # 15. Check for potential schema/table issues
    table_refs = re.findall(r'(?:FROM|JOIN)\s+([a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)*)', sql.lower())
    for ref in table_refs:
        parts = ref.split('.')
        if len(parts) < 3 and not ref.startswith('table('):
            # Not a fully qualified table reference
            if not any(cte_name.lower() == parts[-1] for cte_name in re.findall(r'(\w+)\s+AS\s*\(', sql, re.IGNORECASE)):
                result.add_warning('UNQUALIFIED_TABLE',
                                 f"Table reference may not be fully qualified: {ref}")

    return result


def generate_validation_report(results: List[SQLValidationResult], output_file: Optional[Path] = None) -> str:
    """Generate a comprehensive validation report."""

    valid_count = sum(1 for r in results if r.is_valid)
    invalid_count = len(results) - valid_count
    warning_count = sum(len(r.warnings) for r in results)

    lines = []
    lines.append(f"\n{'='*80}")
    lines.append("VALIDATION REPORT")
    lines.append(f"{'='*80}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"\nTotal benchmark queries: {len(results)}")
    lines.append(f"  ✓ Valid:   {valid_count}")
    lines.append(f"  ✗ Invalid: {invalid_count}")
    lines.append(f"  ⚠ Warnings: {warning_count}")
    lines.append("")

    if invalid_count == 0 and warning_count == 0:
        lines.append("🎉 All benchmark queries passed validation with no warnings!")
        report = "\n".join(lines)
        if output_file:
            output_file.write_text(report)
        return report

    # Summary by Genie Space
    lines.append(f"\n{'-'*80}")
    lines.append("SUMMARY BY GENIE SPACE")
    lines.append(f"{'-'*80}")

    by_space = {}
    for r in results:
        if r.genie_space not in by_space:
            by_space[r.genie_space] = {'total': 0, 'errors': 0, 'warnings': 0}
        by_space[r.genie_space]['total'] += 1
        if not r.is_valid:
            by_space[r.genie_space]['errors'] += 1
        by_space[r.genie_space]['warnings'] += len(r.warnings)

    for space, stats in sorted(by_space.items()):
        status = "✓" if stats['errors'] == 0 else "✗"
        warn_str = f" ({stats['warnings']} warnings)" if stats['warnings'] > 0 else ""
        lines.append(f"  {status} {space}: {stats['total']} queries, {stats['errors']} errors{warn_str}")

    # Detailed errors
    if invalid_count > 0:
        lines.append(f"\n{'-'*80}")
        lines.append("ERRORS (must fix before deployment)")
        lines.append(f"{'-'*80}")

        for r in results:
            if not r.is_valid:
                lines.append(f"\n❌ [{r.genie_space}] Q{r.question_num}: {r.question_text[:60]}...")
                for err in r.errors:
                    lines.append(f"   ERROR: [{err['type']}] {err['message']}")
                # Show first 200 chars of SQL
                lines.append(f"   SQL: {r.sql[:200]}...")

    # Warnings
    if warning_count > 0:
        lines.append(f"\n{'-'*80}")
        lines.append("WARNINGS (recommended to review)")
        lines.append(f"{'-'*80}")

        for r in results:
            if r.warnings:
                lines.append(f"\n⚠️ [{r.genie_space}] Q{r.question_num}: {r.question_text[:60]}...")
                for warn in r.warnings:
                    lines.append(f"   WARNING: [{warn['type']}] {warn['message']}")

    # Deployment readiness
    lines.append(f"\n{'='*80}")
    lines.append("DEPLOYMENT READINESS")
    lines.append(f"{'='*80}")

    if invalid_count == 0:
        lines.append("\n✅ READY FOR DEPLOYMENT")
        lines.append("   All benchmark queries passed validation.")
        if warning_count > 0:
            lines.append(f"   Note: {warning_count} warnings to review (non-blocking)")
    else:
        lines.append("\n❌ NOT READY FOR DEPLOYMENT")
        lines.append(f"   {invalid_count} queries have errors that must be fixed.")
        lines.append("\n   Errors by type:")
        error_types = {}
        for r in results:
            for err in r.errors:
                error_types[err['type']] = error_types.get(err['type'], 0) + 1
        for etype, count in sorted(error_types.items(), key=lambda x: -x[1]):
            lines.append(f"     - {etype}: {count}")

    lines.append("")

    report = "\n".join(lines)
    if output_file:
        output_file.write_text(report)
        print(f"\nReport saved to: {output_file}")

    return report


def validate_all_genie_spaces(genie_dir: Path, catalog: str = 'health_monitor',
                               gold_schema: str = 'gold',
                               feature_schema: str = None,
                               output_file: Optional[Path] = None) -> Tuple[bool, List[SQLValidationResult]]:
    """
    Main validation function - validates all benchmark SQL in all Genie Spaces.

    Args:
        genie_dir: Directory containing *_genie_export.json files
        catalog: Catalog name for variable substitution
        gold_schema: Gold schema name for variable substitution
        feature_schema: Feature schema name (defaults to gold_schema + "_ml")
        output_file: Optional path to save validation report

    Returns:
        (success: bool, results: List[SQLValidationResult])
    """

    # Extract all queries
    results = extract_all_benchmark_queries(genie_dir, catalog, gold_schema, feature_schema)

    if not results:
        print("\n⚠️ No benchmark queries found to validate!")
        return False, []

    # Validate each query
    print(f"\n{'-'*80}")
    print("VALIDATING SQL QUERIES")
    print(f"{'-'*80}")

    for i, result in enumerate(results, 1):
        validate_sql_static(result)
        status = "✓" if result.is_valid else "✗"
        warn = f" ({len(result.warnings)} warnings)" if result.warnings else ""
        print(f"  [{i}/{len(results)}] {status} {result.genie_space} Q{result.question_num}{warn}")

    # Generate report
    report = generate_validation_report(results, output_file)
    print(report)

    # Return success status
    success = all(r.is_valid for r in results)
    return success, results


# CLI entry point
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Validate Genie Space benchmark SQL queries')
    parser.add_argument('--genie-dir', type=Path, default=Path('.'),
                       help='Directory containing Genie Space JSON exports')
    parser.add_argument('--catalog', type=str, default='health_monitor',
                       help='Catalog name for variable substitution')
    parser.add_argument('--gold-schema', type=str, default='gold',
                       help='Gold schema name for variable substitution')
    parser.add_argument('--feature-schema', type=str, default=None,
                       help='Feature schema name (defaults to gold_schema + "_ml")')
    parser.add_argument('--output', type=Path, default=None,
                       help='Output file for validation report')

    args = parser.parse_args()

    success, _ = validate_all_genie_spaces(
        genie_dir=args.genie_dir,
        catalog=args.catalog,
        gold_schema=args.gold_schema,
        feature_schema=args.feature_schema,
        output_file=args.output
    )

    sys.exit(0 if success else 1)
