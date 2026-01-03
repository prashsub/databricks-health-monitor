"""
Genie Space Pre-Deployment Validation Script

Validates JSON export files before deployment:
1. Schema structure completeness
2. SQL benchmark question syntax
3. Table/view/function references
4. MEASURE() function usage
5. Variable substitution patterns

Usage:
    python validate_genie_space.py cost_intelligence_genie_export.json
    python validate_genie_space.py job_health_monitor_genie_export.json
    python validate_genie_space.py --all  # Validate all *_export.json files
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple


class GenieSpaceValidator:
    """Validates Genie Space JSON export files."""
    
    def __init__(self, json_path: str):
        self.json_path = Path(json_path)
        self.errors = []
        self.warnings = []
        self.data = None
        
    def load_json(self) -> bool:
        """Load and parse JSON file."""
        try:
            with open(self.json_path, 'r') as f:
                self.data = json.load(f)
            return True
        except Exception as e:
            self.errors.append(f"Failed to load JSON: {str(e)}")
            return False
    
    def validate_structure(self) -> bool:
        """Validate top-level JSON structure."""
        required_fields = ['version', 'config', 'data_sources', 'instructions', 'benchmarks']
        
        for field in required_fields:
            if field not in self.data:
                self.errors.append(f"Missing required field: {field}")
        
        return len(self.errors) == 0
    
    def validate_sample_questions(self) -> bool:
        """Validate sample questions structure."""
        if 'sample_questions' not in self.data.get('config', {}):
            self.errors.append("Missing config.sample_questions")
            return False
        
        questions = self.data['config']['sample_questions']
        
        for i, q in enumerate(questions):
            if 'id' not in q:
                self.errors.append(f"Sample question {i} missing 'id'")
            elif len(q['id']) != 32:
                self.errors.append(f"Sample question {i} id must be 32 chars (UUID without dashes)")
            
            if 'question' not in q:
                self.errors.append(f"Sample question {i} missing 'question'")
            elif not isinstance(q['question'], list):
                self.errors.append(f"Sample question {i} 'question' must be array")
        
        return len(self.errors) == 0
    
    def validate_data_sources(self) -> List[str]:
        """Validate data sources and collect table identifiers."""
        table_ids = []
        
        if 'tables' in self.data.get('data_sources', {}):
            for i, table in enumerate(self.data['data_sources']['tables']):
                if 'identifier' not in table:
                    self.errors.append(f"Table {i} missing 'identifier'")
                else:
                    identifier = table['identifier']
                    table_ids.append(identifier)
                    
                    # Validate 3-part name pattern
                    if not self._is_valid_identifier(identifier):
                        self.errors.append(f"Invalid table identifier: {identifier}")
        
        if 'metric_views' in self.data.get('data_sources', {}):
            for i, mv in enumerate(self.data['data_sources']['metric_views']):
                if 'identifier' not in mv:
                    self.errors.append(f"Metric view {i} missing 'identifier'")
                else:
                    identifier = mv['identifier']
                    table_ids.append(identifier)
                    
                    if not self._is_valid_identifier(identifier):
                        self.errors.append(f"Invalid metric view identifier: {identifier}")
        
        return table_ids
    
    def validate_sql_functions(self) -> List[str]:
        """Validate SQL functions and collect function identifiers."""
        func_ids = []
        
        if 'sql_functions' in self.data.get('instructions', {}):
            for i, func in enumerate(self.data['instructions']['sql_functions']):
                if 'id' not in func:
                    self.errors.append(f"SQL function {i} missing 'id'")
                elif len(func['id']) != 32:
                    self.errors.append(f"SQL function {i} id must be 32 chars")
                
                if 'identifier' not in func:
                    self.errors.append(f"SQL function {i} missing 'identifier'")
                else:
                    identifier = func['identifier']
                    func_ids.append(identifier)
                    
                    if not self._is_valid_identifier(identifier):
                        self.errors.append(f"Invalid function identifier: {identifier}")
        
        return func_ids
    
    def validate_benchmark_questions(self, table_ids: List[str], func_ids: List[str]) -> bool:
        """Validate benchmark questions SQL syntax."""
        if 'questions' not in self.data.get('benchmarks', {}):
            self.errors.append("Missing benchmarks.questions")
            return False
        
        questions = self.data['benchmarks']['questions']
        
        for i, q in enumerate(questions):
            # Validate structure
            if 'id' not in q:
                self.errors.append(f"Benchmark {i} missing 'id'")
            elif len(q['id']) != 32:
                self.errors.append(f"Benchmark {i} id must be 32 chars")
            
            if 'question' not in q:
                self.errors.append(f"Benchmark {i} missing 'question'")
            
            if 'answer' not in q or not q['answer']:
                self.errors.append(f"Benchmark {i} missing 'answer'")
                continue
            
            # Validate SQL
            answer = q['answer'][0]
            if answer.get('format') != 'SQL':
                self.warnings.append(f"Benchmark {i} answer format is not 'SQL'")
                continue
            
            if 'content' not in answer:
                self.errors.append(f"Benchmark {i} answer missing 'content'")
                continue
            
            sql = ''.join(answer['content'])
            
            # Check MEASURE() usage
            self._validate_measure_syntax(sql, i)
            
            # Check table references
            self._validate_table_references(sql, table_ids, i)
            
            # Check function references
            self._validate_function_references(sql, func_ids, i)
            
            # Check variable substitution
            self._validate_variable_substitution(sql, i)
        
        return len(self.errors) == 0
    
    def _is_valid_identifier(self, identifier: str) -> bool:
        """Check if identifier follows 3-part naming or uses variables."""
        # Allow variable substitution patterns
        if '${catalog}' in identifier or '${gold_schema}' in identifier:
            return True
        
        # Check 3-part name: catalog.schema.object
        parts = identifier.split('.')
        return len(parts) == 3
    
    def _validate_measure_syntax(self, sql: str, question_num: int):
        """Validate MEASURE() function usage in SQL."""
        # Find all MEASURE() calls
        measure_pattern = r'MEASURE\s*\(\s*([^)]+)\s*\)'
        matches = re.findall(measure_pattern, sql, re.IGNORECASE)
        
        for match in matches:
            # Check for backticks (display names) - should use column names instead
            if '`' in match:
                self.warnings.append(
                    f"Benchmark {question_num}: MEASURE() uses backticks (display name). "
                    f"Use column name instead: {match}"
                )
            
            # Check for spaces in column name (likely display name)
            if ' ' in match.strip():
                self.warnings.append(
                    f"Benchmark {question_num}: MEASURE() argument has spaces (likely display name). "
                    f"Use column name instead: {match}"
                )
    
    def _validate_table_references(self, sql: str, table_ids: List[str], question_num: int):
        """Validate table/view references in SQL."""
        # Extract FROM/JOIN clauses
        from_pattern = r'FROM\s+([^\s,;\n]+)'
        join_pattern = r'JOIN\s+([^\s,;\n]+)'
        
        from_matches = re.findall(from_pattern, sql, re.IGNORECASE)
        join_matches = re.findall(join_pattern, sql, re.IGNORECASE)
        
        all_refs = from_matches + join_matches
        
        for ref in all_refs:
            # Skip subqueries and CTEs
            if '(' in ref or ref.upper() in ['LATERAL', 'UNNEST']:
                continue
            
            # Check if reference uses variables
            if '${' in ref:
                # Validate variable pattern
                if not re.match(r'\$\{catalog\}\.\$\{gold_schema(_monitoring)?\}\.\w+', ref):
                    self.warnings.append(
                        f"Benchmark {question_num}: Unusual variable pattern in table ref: {ref}"
                    )
            else:
                # Check if it's a defined table/view
                # For now, just warn if it's not in our list (could be a CTE)
                if ref not in table_ids and not any(tid.endswith(ref.split('.')[-1]) for tid in table_ids):
                    self.warnings.append(
                        f"Benchmark {question_num}: Table reference not in data_sources: {ref}"
                    )
    
    def _validate_function_references(self, sql: str, func_ids: List[str], question_num: int):
        """Validate TVF references in SQL."""
        # Pattern: catalog.schema.function_name(...)
        func_pattern = r'([a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*)\s*\('
        
        matches = re.findall(func_pattern, sql, re.IGNORECASE)
        
        for match in matches:
            # Check if it's a defined function
            if match not in func_ids and not any(fid.endswith(match.split('.')[-1]) for fid in func_ids):
                # Could be a variable-based reference
                if '${' not in sql:  # Only warn if not using variables
                    self.warnings.append(
                        f"Benchmark {question_num}: Function not in sql_functions: {match}"
                    )
    
    def _validate_variable_substitution(self, sql: str, question_num: int):
        """Validate variable substitution patterns."""
        # Check for ${catalog} and ${gold_schema}
        var_pattern = r'\$\{([^}]+)\}'
        matches = re.findall(var_pattern, sql)
        
        valid_vars = ['catalog', 'gold_schema', 'gold_schema_monitoring']
        
        for match in matches:
            if match not in valid_vars:
                self.errors.append(
                    f"Benchmark {question_num}: Invalid variable: ${{{match}}}. "
                    f"Use: {', '.join(valid_vars)}"
                )
    
    def validate(self) -> bool:
        """Run all validations."""
        print(f"\n{'='*80}")
        print(f"Validating: {self.json_path.name}")
        print(f"{'='*80}")
        
        if not self.load_json():
            return False
        
        self.validate_structure()
        self.validate_sample_questions()
        
        table_ids = self.validate_data_sources()
        func_ids = self.validate_sql_functions()
        
        self.validate_benchmark_questions(table_ids, func_ids)
        
        # Print results
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   - {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        if not self.errors and not self.warnings:
            print(f"\n✅ VALIDATION PASSED - No issues found!")
        elif not self.errors:
            print(f"\n✅ VALIDATION PASSED - {len(self.warnings)} warnings (non-blocking)")
        else:
            print(f"\n❌ VALIDATION FAILED - {len(self.errors)} errors, {len(self.warnings)} warnings")
        
        return len(self.errors) == 0


def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate Genie Space JSON exports')
    parser.add_argument('files', nargs='*', help='JSON export files to validate')
    parser.add_argument('--all', action='store_true', help='Validate all *_export.json files')
    
    args = parser.parse_args()
    
    # Find files to validate
    if args.all:
        script_dir = Path(__file__).parent
        files = list(script_dir.glob('*_export.json'))
    else:
        files = [Path(f) for f in args.files]
    
    if not files:
        print("❌ No files specified. Use --all or provide file names.")
        sys.exit(1)
    
    # Validate each file
    all_passed = True
    
    for file_path in files:
        validator = GenieSpaceValidator(str(file_path))
        passed = validator.validate()
        
        if not passed:
            all_passed = False
    
    # Summary
    print(f"\n{'='*80}")
    print("VALIDATION SUMMARY")
    print(f"{'='*80}")
    
    if all_passed:
        print(f"✅ All {len(files)} file(s) passed validation!")
        sys.exit(0)
    else:
        print(f"❌ Some files failed validation. Fix errors before deployment.")
        sys.exit(1)


if __name__ == '__main__':
    main()

