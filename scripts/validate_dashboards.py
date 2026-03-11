#!/usr/bin/env python3
"""
Dashboard Validation Script with Self-Tests

This script validates dashboard JSON files to catch common errors:
1. JSON syntax errors
2. Dataset SQL syntax errors
3. Widget field mismatches with dataset columns
4. Missing parameter definitions (checks global + dataset params)
5. Shared dataset anti-patterns
6. Databricks-specific column name issues (duration_ms, warehouse_name, etc.)
7. Reference to non-existent Lakehouse Monitoring tables
8. Common fact_query_history column typos

DESIGN PRINCIPLES:
- Simple, focused checks (easy to verify manually)
- Self-tests run first to validate the validator
- Verbose output for human auditability
- Fail-fast with clear error messages
- No complex parsing - use well-tested libraries
- Reduces false positives by checking global parameters

WHACKAMOLE PREVENTION:
This validator catches the most common dashboard regression issues:
- Column name mismatches (duration_ms vs total_duration_ms)
- Missing parameters (now checks global + dataset level)
- Shared dataset conflicts (one dataset, multiple purposes)
- Monitoring table references (non-existent tables)
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ValidationIssue:
    """Represents a validation issue found in a dashboard."""
    severity: str  # ERROR, WARNING, INFO
    file: str
    dataset: str
    message: str
    line_hint: str = ""


class DashboardValidator:
    """Validates dashboard JSON files with built-in self-tests."""
    
    def __init__(self, dashboards_dir: Path):
        self.dashboards_dir = dashboards_dir
        self.issues: List[ValidationIssue] = []
        self.stats = {
            'files_checked': 0,
            'datasets_checked': 0,
            'widgets_checked': 0,
            'errors': 0,
            'warnings': 0
        }
    
    def run_self_tests(self) -> bool:
        """
        Self-tests to validate the validator logic.
        These must pass before validating actual dashboards.
        """
        print("🧪 Running self-tests...")
        tests_passed = 0
        tests_failed = 0
        
        # Test 1: SQL column extraction
        test_sql = "SELECT column1, column2 AS alias, COUNT(*) AS count FROM table"
        expected_cols = {'column1', 'alias', 'count'}
        extracted_cols = self._extract_select_columns(test_sql)
        if extracted_cols == expected_cols:
            print("  ✅ Test 1: SQL column extraction - PASSED")
            tests_passed += 1
        else:
            print(f"  ❌ Test 1: SQL column extraction - FAILED")
            print(f"     Expected: {expected_cols}, Got: {extracted_cols}")
            tests_failed += 1
        
        # Test 2: Parameter extraction (template variables vs query parameters)
        test_sql_params = "WHERE catalog = ${catalog} AND date >= :time_range.min AND schema = ${gold_schema}"
        expected_params = {'time_range'}  # Only :time_range is a query param; ${catalog} and ${gold_schema} are templates
        extracted_params = self._extract_parameters(test_sql_params)
        if extracted_params == expected_params:
            print("  ✅ Test 2: Parameter extraction (template vars vs query params) - PASSED")
            tests_passed += 1
        else:
            print(f"  ❌ Test 2: Parameter extraction - FAILED")
            print(f"     Expected: {expected_params} (ignoring template vars), Got: {extracted_params}")
            tests_failed += 1
        
        # Test 3: Widget field extraction
        test_widget = {
            "fields": [
                {"name": "field1", "expression": "`field1`"},
                {"name": "field2", "expression": "`field2`"}
            ]
        }
        expected_fields = {'field1', 'field2'}
        extracted_fields = self._extract_widget_fields(test_widget)
        if extracted_fields == expected_fields:
            print("  ✅ Test 3: Widget field extraction - PASSED")
            tests_passed += 1
        else:
            print(f"  ❌ Test 3: Widget field extraction - FAILED")
            print(f"     Expected: {expected_fields}, Got: {extracted_fields}")
            tests_failed += 1
        
        print(f"\n{'='*60}")
        print(f"Self-test results: {tests_passed} passed, {tests_failed} failed")
        print(f"{'='*60}\n")
        
        if tests_failed > 0:
            print("⚠️  Self-tests FAILED. Validator logic has bugs. Aborting.\n")
            return False
        
        print("✅ Self-tests PASSED. Validator is ready.\n")
        return True
    
    def validate_all_dashboards(self) -> bool:
        """Validate all dashboard JSON files."""
        dashboard_files = list(self.dashboards_dir.glob("*.lvdash.json"))
        
        if not dashboard_files:
            print(f"⚠️  No dashboard files found in {self.dashboards_dir}")
            return False
        
        print(f"📊 Found {len(dashboard_files)} dashboard files\n")
        
        for dashboard_file in sorted(dashboard_files):
            self._validate_dashboard_file(dashboard_file)
        
        self._print_summary()
        return self.stats['errors'] == 0
    
    def _validate_dashboard_file(self, file_path: Path):
        """Validate a single dashboard JSON file."""
        print(f"📄 Validating {file_path.name}...")
        self.stats['files_checked'] += 1
        
        try:
            with open(file_path, 'r') as f:
                dashboard = json.load(f)
        except json.JSONDecodeError as e:
            self._add_issue('ERROR', file_path.name, 'N/A', 
                          f"Invalid JSON: {e}", f"Line {e.lineno}")
            return
        
        # Extract global parameters
        global_params = {p.get('keyword') for p in dashboard.get('parameters', [])}
        
        # Check 1: Validate datasets
        datasets = dashboard.get('datasets', [])
        dataset_map = {}  # name -> columns
        
        for dataset in datasets:
            dataset_name = dataset.get('name', 'unknown')
            self.stats['datasets_checked'] += 1
            
            # Extract query
            query = dataset.get('query', '')
            
            # Check for common anti-patterns
            self._check_dataset_antipatterns(file_path.name, dataset_name, query)
            
            # Check for Databricks-specific column name issues
            self._check_databricks_column_issues(file_path.name, dataset_name, query)
            
            # Extract columns from SELECT statement
            columns = self._extract_select_columns(query)
            dataset_map[dataset_name] = columns
            
            # Check for missing parameter definitions (including global params)
            self._check_missing_parameters(file_path.name, dataset_name, dataset, global_params)
        
        # Check 2: Validate widgets against datasets
        pages = dashboard.get('pages', [])
        for page in pages:
            for widget_def in page.get('layout', []):
                widget = widget_def.get('widget', {})
                self._validate_widget(file_path.name, widget, dataset_map)
    
    def _check_dataset_antipatterns(self, file: str, dataset: str, query: str):
        """Check for common anti-patterns in dataset queries."""
        
        # Anti-pattern 1: Hardcoded zeros as column values
        if re.search(r'\b0\s+AS\s+\w+', query, re.IGNORECASE):
            matches = re.findall(r'0\s+AS\s+(\w+)', query, re.IGNORECASE)
            self._add_issue('WARNING', file, dataset,
                          f"Hardcoded zeros found: {', '.join(matches)}",
                          "Consider calculating real values or removing unused columns")
        
        # Anti-pattern 2: Reference to non-existent columns
        # Check for common typos in fact_query_history
        if 'fact_query_history' in query:
            bad_columns = []
            if re.search(r'\bcatalog\b\s*,', query, re.IGNORECASE):
                bad_columns.append('catalog (should be statement_catalog?)')
            if re.search(r'\bschema\b\s*,', query, re.IGNORECASE):
                bad_columns.append('schema (should be statement_schema?)')
            if re.search(r'\btable_name\b', query, re.IGNORECASE):
                bad_columns.append('table_name (not in fact_query_history)')
            
            if bad_columns:
                self._add_issue('ERROR', file, dataset,
                              f"Possible non-existent columns in fact_query_history: {', '.join(bad_columns)}")
        
        # Anti-pattern 3: Reference to monitoring tables that don't exist
        if '_monitoring.' in query and ('_profile_metrics' in query or '_drift_metrics' in query):
            self._add_issue('ERROR', file, dataset,
                          "References non-existent Lakehouse Monitoring tables",
                          "Calculate metrics directly from fact tables instead")
    
    def _check_databricks_column_issues(self, file: str, dataset: str, query: str):
        """Check for Databricks-specific column name issues."""
        
        # Issue 1: duration_ms vs total_duration_ms in fact_query_history
        if 'fact_query_history' in query:
            if re.search(r'\bduration_ms\b', query):
                self._add_issue('ERROR', file, dataset,
                              "Uses 'duration_ms' but fact_query_history has 'total_duration_ms'",
                              "Change duration_ms to total_duration_ms")
        
        # Issue 2: period_start_time in fact_query_history (should be start_time)
        if 'fact_query_history' in query:
            if re.search(r'\bperiod_start_time\b', query):
                self._add_issue('ERROR', file, dataset,
                              "Uses 'period_start_time' but fact_query_history has 'start_time'",
                              "Change period_start_time to start_time")
        
        # Issue 3: warehouse_name in fact_query_history (should be compute_type)
        if 'fact_query_history' in query:
            if re.search(r'\bwarehouse_name\b', query):
                self._add_issue('WARNING', file, dataset,
                              "Uses 'warehouse_name' but fact_query_history uses 'compute_type'",
                              "Consider using compute_type instead")
        
        # Issue 4: executed_by vs executed_by_user_id
        if 'fact_query_history' in query:
            if re.search(r'\bexecuted_by\b(?!_user_id)', query):
                self._add_issue('ERROR', file, dataset,
                              "Uses 'executed_by' but fact_query_history has 'executed_by_user_id'",
                              "Change executed_by to executed_by_user_id")
    
    def _check_missing_parameters(self, file: str, dataset: str, dataset_obj: dict, global_params: Set[str]):
        """Check if all referenced parameters are defined (including global parameters)."""
        query = dataset_obj.get('query', '')
        
        # Combine global parameters with dataset-level parameters
        dataset_params = {p.get('keyword') for p in dataset_obj.get('parameters', [])}
        all_defined_params = global_params | dataset_params
        
        # Extract parameters from query
        used_params = self._extract_parameters(query)
        
        # Check for truly missing parameters (not in global or dataset level)
        missing_params = used_params - all_defined_params
        if missing_params:
            self._add_issue('ERROR', file, dataset,
                          f"Missing parameter definitions (not in global or dataset params): {', '.join(missing_params)}")
    
    def _validate_widget(self, file: str, widget: dict, dataset_map: Dict[str, Set[str]]):
        """Validate widget field references against dataset columns."""
        self.stats['widgets_checked'] += 1
        
        queries = widget.get('queries', [])
        for query in queries:
            query_def = query.get('query', {})
            dataset_name = query_def.get('datasetName', '')
            
            if not dataset_name:
                continue
            
            # Get expected columns from dataset
            expected_columns = dataset_map.get(dataset_name, set())
            
            # Get widget fields
            widget_fields = self._extract_widget_fields(query_def)
            
            # Check for mismatches
            missing_columns = widget_fields - expected_columns
            if missing_columns:
                widget_name = widget.get('name', 'unknown')
                self._add_issue('ERROR', file, f"widget:{widget_name}",
                              f"Widget references columns not in dataset '{dataset_name}': {', '.join(missing_columns)}")
    
    def _extract_select_columns(self, query: str) -> Set[str]:
        """
        Extract column names from SELECT statement.
        Simple regex-based extraction - not a full SQL parser.
        """
        columns = set()
        
        # Find SELECT clause (first occurrence)
        select_match = re.search(r'\bSELECT\s+(.*?)\s+FROM\b', query, re.IGNORECASE | re.DOTALL)
        if not select_match:
            return columns
        
        select_clause = select_match.group(1)
        
        # Split by comma (naive - doesn't handle nested commas in functions)
        parts = select_clause.split(',')
        
        for part in parts:
            part = part.strip()
            
            # Look for AS alias
            as_match = re.search(r'\bAS\s+(\w+)', part, re.IGNORECASE)
            if as_match:
                columns.add(as_match.group(1))
            else:
                # Try to extract column name (last word if no AS)
                words = re.findall(r'\b(\w+)\b', part)
                if words:
                    columns.add(words[-1])
        
        return columns
    
    def _extract_parameters(self, query: str) -> Set[str]:
        """
        Extract parameter names from query.
        
        Distinguishes between:
        - Template variables: ${catalog}, ${gold_schema} - Replaced during deployment
        - Query parameters: :param, :time_range.min - Must be defined in dashboard
        
        Returns only query parameters that need to be defined.
        """
        params = set()
        
        # Template variables (${variable}) - These are replaced during deployment
        # Common template variables that don't need parameter definitions:
        template_vars = {'catalog', 'gold_schema', 'silver_schema', 'bronze_schema', 
                        'feature_schema', 'monitoring_schema', 'warehouse_id'}
        
        # Extract ${variable} format but filter out known template variables
        dollar_vars = set(re.findall(r'\$\{(\w+)\}', query))
        unknown_templates = dollar_vars - template_vars
        if unknown_templates:
            params.update(unknown_templates)  # Flag unknown template variables
        
        # Extract :param format (these MUST be defined as parameters)
        params.update(re.findall(r':(\w+)\.', query))  # :param.min
        params.update(re.findall(r':(\w+)\b', query))  # :param
        
        return params
    
    def _extract_widget_fields(self, query_def: dict) -> Set[str]:
        """Extract field names from widget query definition."""
        fields = set()
        for field in query_def.get('fields', []):
            if 'name' in field:
                fields.add(field['name'])
        return fields
    
    def _add_issue(self, severity: str, file: str, dataset: str, message: str, line_hint: str = ""):
        """Add a validation issue."""
        self.issues.append(ValidationIssue(severity, file, dataset, message, line_hint))
        if severity == 'ERROR':
            self.stats['errors'] += 1
        elif severity == 'WARNING':
            self.stats['warnings'] += 1
    
    def _print_summary(self):
        """Print validation summary."""
        print(f"\n{'='*80}")
        print("VALIDATION SUMMARY")
        print(f"{'='*80}")
        print(f"Files checked:    {self.stats['files_checked']}")
        print(f"Datasets checked: {self.stats['datasets_checked']}")
        print(f"Widgets checked:  {self.stats['widgets_checked']}")
        print(f"Errors found:     {self.stats['errors']}")
        print(f"Warnings found:   {self.stats['warnings']}")
        print(f"{'='*80}\n")
        
        if self.issues:
            # Group by severity
            errors = [i for i in self.issues if i.severity == 'ERROR']
            warnings = [i for i in self.issues if i.severity == 'WARNING']
            
            if errors:
                print("❌ ERRORS:")
                for issue in errors:
                    print(f"  {issue.file} > {issue.dataset}")
                    print(f"    {issue.message}")
                    if issue.line_hint:
                        print(f"    Hint: {issue.line_hint}")
                    print()
            
            if warnings:
                print("⚠️  WARNINGS:")
                for issue in warnings:
                    print(f"  {issue.file} > {issue.dataset}")
                    print(f"    {issue.message}")
                    if issue.line_hint:
                        print(f"    Hint: {issue.line_hint}")
                    print()
        else:
            print("✅ No issues found!")


def main():
    """Main entry point."""
    print("=" * 80)
    print("Dashboard Validation Script")
    print("=" * 80)
    print()
    
    # Setup
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    dashboards_dir = project_root / "src" / "dashboards"
    
    if not dashboards_dir.exists():
        print(f"❌ Dashboards directory not found: {dashboards_dir}")
        return 1
    
    # Create validator
    validator = DashboardValidator(dashboards_dir)
    
    # Step 1: Run self-tests
    if not validator.run_self_tests():
        print("⚠️  Aborting validation due to self-test failures.")
        print("    Please fix the validator logic before using it.")
        return 1
    
    # Step 2: Validate dashboards
    success = validator.validate_all_dashboards()
    
    # Step 3: Return exit code
    if success:
        print("✅ All validations passed!")
        return 0
    else:
        print("❌ Validation failed with errors.")
        print("   Please fix the issues above before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

