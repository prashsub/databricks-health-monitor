"""
Tests for TVF SQL Syntax Validation
====================================

These tests validate TVF SQL files for:
- Correct parameter ordering (required before DEFAULT)
- STRING type for date parameters
- No LIMIT with parameters (use WHERE rank <=)
- NULLIF for division safety
- LLM-friendly COMMENT metadata
"""

import pytest
import re
import os
from pathlib import Path


# Path to TVF SQL files
TVF_DIR = Path(__file__).parent.parent.parent / "src" / "tvfs"


def get_tvf_files():
    """Get all TVF SQL files."""
    return list(TVF_DIR.glob("*_tvfs.sql"))


def read_tvf_file(file_path):
    """Read and return TVF file contents."""
    with open(file_path, 'r') as f:
        return f.read()


def extract_function_definitions(sql_content):
    """Extract individual function definitions from SQL content."""
    # Split on CREATE OR REPLACE FUNCTION
    pattern = r'(CREATE\s+OR\s+REPLACE\s+FUNCTION\s+[^;]+;)'
    matches = re.findall(pattern, sql_content, re.IGNORECASE | re.DOTALL)
    return matches


class TestTVFSyntaxRules:
    """Test TVF syntax compliance with Genie requirements."""

    @pytest.mark.unit
    @pytest.mark.parametrize("tvf_file", get_tvf_files(), ids=lambda x: x.name)
    def test_no_date_type_parameters(self, tvf_file):
        """Verify no DATE type parameters (Genie requires STRING)."""
        content = read_tvf_file(tvf_file)

        # Extract only the parameter sections (between FUNCTION name( and ) RETURNS)
        # This avoids false positives from DATE columns in RETURNS TABLE definitions
        param_sections = re.findall(
            r'FUNCTION\s+\S+\s*\((.*?)\)\s*RETURNS',
            content,
            re.IGNORECASE | re.DOTALL
        )

        date_params = []
        for params in param_sections:
            # Remove DEFAULT clauses that contain DATE functions (like CURRENT_DATE())
            # to avoid false positives
            cleaned_params = re.sub(r'DEFAULT\s+[^\n,)]+', 'DEFAULT NULL', params, flags=re.IGNORECASE)

            # Look for DATE type parameters: param_name DATE COMMENT
            # This pattern requires COMMENT after DATE to ensure it's a type declaration
            matches = re.findall(
                r'^\s*(\w+)\s+DATE\s+COMMENT',
                cleaned_params,
                re.IGNORECASE | re.MULTILINE
            )
            date_params.extend(matches)

        assert len(date_params) == 0, (
            f"Found DATE type parameters in {tvf_file.name}: {date_params}. "
            "Use STRING type with CAST for Genie compatibility."
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("tvf_file", get_tvf_files(), ids=lambda x: x.name)
    def test_parameter_ordering(self, tvf_file):
        """Verify required parameters come before DEFAULT parameters."""
        content = read_tvf_file(tvf_file)

        # Extract function signatures
        functions = re.findall(
            r'FUNCTION\s+\S+\s*\((.*?)\)\s*RETURNS',
            content,
            re.IGNORECASE | re.DOTALL
        )

        for func_params in functions:
            # Remove COMMENT strings first to avoid false positives from text inside comments
            # Pattern matches COMMENT 'any text' or COMMENT "any text"
            cleaned_params = re.sub(r"COMMENT\s*'[^']*'", "COMMENT ''", func_params, flags=re.IGNORECASE)
            cleaned_params = re.sub(r'COMMENT\s*"[^"]*"', 'COMMENT ""', cleaned_params, flags=re.IGNORECASE)

            # Split on commas that start a new parameter (word at start)
            # Use a pattern that splits on comma followed by newline and word
            params = re.split(r',\s*\n\s*(?=[a-zA-Z_])', cleaned_params)

            found_default = False
            for param in params:
                param = param.strip()
                if not param:
                    continue

                # Check for DEFAULT keyword outside of strings
                has_default = bool(re.search(r'\bDEFAULT\b', param, re.IGNORECASE))

                if found_default and not has_default:
                    # Found a required param after a DEFAULT param
                    pytest.fail(
                        f"Parameter ordering error in {tvf_file.name}: "
                        f"Required parameter '{param[:50]}...' found after DEFAULT parameter. "
                        "Required parameters must come before optional (DEFAULT) parameters."
                    )

                if has_default:
                    found_default = True

    @pytest.mark.unit
    @pytest.mark.parametrize("tvf_file", get_tvf_files(), ids=lambda x: x.name)
    def test_no_limit_with_parameter(self, tvf_file):
        """Verify no LIMIT clauses use parameters (use WHERE rank <= instead)."""
        content = read_tvf_file(tvf_file)

        # Pattern for LIMIT with a variable (not a constant number)
        # Look for LIMIT followed by a word that's not a number
        limit_params = re.findall(
            r'LIMIT\s+([a-zA-Z_]\w*)',
            content,
            re.IGNORECASE
        )

        # Filter out numeric constants
        problematic = [p for p in limit_params if not p.isdigit()]

        assert len(problematic) == 0, (
            f"Found LIMIT with parameters in {tvf_file.name}: {problematic}. "
            "Use 'WHERE rank <= param' instead of 'LIMIT param' for Genie compatibility."
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("tvf_file", get_tvf_files(), ids=lambda x: x.name)
    def test_division_null_safety(self, tvf_file):
        """Check for division operations by variables without NULLIF protection."""
        content = read_tvf_file(tvf_file)

        # Find divisions by variables (not constants)
        # Pattern: / followed by a variable name (not a number)
        # This excludes safe operations like / 1000.0, / 1073741824.0
        variable_divisions = re.findall(
            r'/\s*([a-zA-Z_]\w*(?:\([^)]*\))?)',  # variable or function call
            content
        )

        # Filter out known safe patterns and false positives
        safe_patterns = {'NULLIF', 'CAST', 'COALESCE', 'DATE', 'TIMESTAMP'}
        potentially_unsafe = []

        for div in variable_divisions:
            # Extract just the function/variable name
            base_name = div.split('(')[0].strip().upper()
            if base_name not in safe_patterns:
                potentially_unsafe.append(div)

        # Check that risky divisions use NULLIF
        # Risky = aggregate functions like COUNT, SUM that could be zero
        risky_aggregates = {'COUNT', 'SUM', 'AVG'}
        risky_divisions = [d for d in potentially_unsafe
                          if d.upper().startswith(tuple(risky_aggregates))]

        if risky_divisions:
            # Check each risky division is wrapped in NULLIF
            for risky in risky_divisions:
                # Build a pattern to check if this division is inside NULLIF
                if f'NULLIF({risky}' not in content and f'NULLIF( {risky}' not in content:
                    # Check if it's actually a COUNT/SUM being divided
                    pattern = rf'/\s*{re.escape(risky)}'
                    if re.search(pattern, content) and f'NULLIF({risky}' not in content:
                        pytest.fail(
                            f"Potential division safety issue in {tvf_file.name}: "
                            f"Division by '{risky}' should use NULLIF({risky}, 0) to prevent divide-by-zero."
                        )

    @pytest.mark.unit
    @pytest.mark.parametrize("tvf_file", get_tvf_files(), ids=lambda x: x.name)
    def test_llm_friendly_comments(self, tvf_file):
        """Verify functions have LLM-friendly COMMENT metadata."""
        content = read_tvf_file(tvf_file)

        # Find all function COMMENTs
        function_comments = re.findall(
            r"COMMENT\s+'LLM:[^']+",
            content,
            re.IGNORECASE
        )

        # Count CREATE FUNCTION statements
        function_count = len(re.findall(
            r'CREATE\s+OR\s+REPLACE\s+FUNCTION',
            content,
            re.IGNORECASE
        ))

        # Should have LLM comment for each function
        assert len(function_comments) >= function_count * 0.8, (
            f"Missing LLM-friendly COMMENTs in {tvf_file.name}: "
            f"Found {len(function_comments)} LLM comments for {function_count} functions. "
            "Add COMMENT 'LLM: ...' with use cases and example questions."
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("tvf_file", get_tvf_files(), ids=lambda x: x.name)
    def test_column_comments_in_returns(self, tvf_file):
        """Verify RETURNS TABLE columns have COMMENTs."""
        content = read_tvf_file(tvf_file)

        # Find RETURNS TABLE blocks more carefully
        # First find each function, then extract its RETURNS TABLE section
        function_blocks = re.split(r'CREATE\s+OR\s+REPLACE\s+FUNCTION', content, flags=re.IGNORECASE)

        for block in function_blocks[1:]:  # Skip first empty split
            # Find RETURNS TABLE( and match to the closing ) before COMMENT 'LLM
            # Use a more robust approach: find RETURNS TABLE and look for balanced parens
            match = re.search(r'RETURNS\s+TABLE\s*\(', block, re.IGNORECASE)
            if not match:
                continue

            # Find the matching closing paren for RETURNS TABLE(
            start_pos = match.end() - 1  # Position of opening paren
            paren_depth = 0
            end_pos = start_pos

            for i, char in enumerate(block[start_pos:]):
                if char == '(':
                    paren_depth += 1
                elif char == ')':
                    paren_depth -= 1
                    if paren_depth == 0:
                        end_pos = start_pos + i
                        break

            if end_pos == start_pos:
                continue  # Couldn't find matching paren

            returns_def = block[start_pos+1:end_pos]

            # Count columns by counting lines with data types (STRING, INT, DOUBLE, etc.)
            column_lines = re.findall(
                r'^\s*\w+\s+(STRING|INT|DOUBLE|BIGINT|BOOLEAN|DATE|TIMESTAMP|ARRAY|MAP)',
                returns_def,
                re.IGNORECASE | re.MULTILINE
            )
            column_count = len(column_lines)

            # Count COMMENT keywords in the returns definition
            comment_count = len(re.findall(r'\bCOMMENT\b', returns_def, re.IGNORECASE))

            # All columns should have COMMENTs (allow 80% to be lenient)
            if column_count > 0 and comment_count < column_count * 0.8:
                pytest.fail(
                    f"Missing column COMMENTs in {tvf_file.name}: "
                    f"Found {comment_count} comments for {column_count} columns in RETURNS TABLE. "
                    "Add COMMENT for each column to help Genie understand the data."
                )


class TestTVFSchemaReferences:
    """Test TVF references to Gold layer tables use correct schema."""

    @pytest.mark.unit
    @pytest.mark.parametrize("tvf_file", get_tvf_files(), ids=lambda x: x.name)
    def test_no_system_table_references(self, tvf_file):
        """Verify TVFs don't query system tables directly."""
        content = read_tvf_file(tvf_file)

        # Pattern for system table references
        system_refs = re.findall(
            r'FROM\s+system\.\w+\.\w+',
            content,
            re.IGNORECASE
        )

        assert len(system_refs) == 0, (
            f"Found system table references in {tvf_file.name}: {system_refs}. "
            "TVFs should query Gold layer tables, not system tables directly."
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("tvf_file", get_tvf_files(), ids=lambda x: x.name)
    def test_uses_variable_substitution(self, tvf_file):
        """Verify TVFs use ${catalog}.${gold_schema} variable substitution."""
        content = read_tvf_file(tvf_file)

        # Should have variable references
        catalog_refs = content.count('${catalog}')
        schema_refs = content.count('${gold_schema}')

        # Each file should have multiple references
        assert catalog_refs > 0, (
            f"No ${{catalog}} references found in {tvf_file.name}. "
            "Use variable substitution for portable TVFs."
        )
        assert schema_refs > 0, (
            f"No ${{gold_schema}} references found in {tvf_file.name}. "
            "Use variable substitution for portable TVFs."
        )


class TestTVFFileStructure:
    """Test TVF file structure and organization."""

    @pytest.mark.unit
    def test_tvf_files_exist(self):
        """Verify expected TVF files exist."""
        expected_files = [
            'cost_tvfs.sql',
            'compute_tvfs.sql',
            'reliability_tvfs.sql',
            'performance_tvfs.sql',
            'security_tvfs.sql',
            'quality_tvfs.sql',
        ]

        for filename in expected_files:
            file_path = TVF_DIR / filename
            assert file_path.exists(), f"Missing TVF file: {filename}"

    @pytest.mark.unit
    def test_deploy_script_exists(self):
        """Verify TVF deployment script exists."""
        deploy_script = TVF_DIR / 'deploy_tvfs.py'
        assert deploy_script.exists(), "Missing deploy_tvfs.py script"

    @pytest.mark.unit
    @pytest.mark.parametrize("tvf_file", get_tvf_files(), ids=lambda x: x.name)
    def test_file_has_header_comment(self, tvf_file):
        """Verify each TVF file has a descriptive header comment."""
        content = read_tvf_file(tvf_file)

        # Should start with a comment block
        assert content.strip().startswith('--'), (
            f"TVF file {tvf_file.name} should start with a header comment block."
        )

        # Should have domain identification
        has_domain = any(
            domain in content[:500].upper()
            for domain in ['COST', 'SECURITY', 'PERFORMANCE', 'RELIABILITY', 'QUALITY']
        )
        assert has_domain, (
            f"TVF file {tvf_file.name} should identify its domain in the header."
        )
