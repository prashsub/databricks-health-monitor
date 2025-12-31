"""
Alert Query Validator

Validates SQL queries before deployment to catch:
1. Syntax errors (via EXPLAIN)
2. Security risks (DROP, DELETE, etc.)
3. Missing table references
4. Invalid column references

This module is intentionally free of Databricks SDK imports for testability.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple


@dataclass
class ValidationResult:
    """Result of query validation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    tables_referenced: Set[str]

    @staticmethod
    def success(tables: Set[str] = None, warnings: List[str] = None) -> "ValidationResult":
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=warnings or [],
            tables_referenced=tables or set(),
        )

    @staticmethod
    def failure(errors: List[str], tables: Set[str] = None) -> "ValidationResult":
        return ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=[],
            tables_referenced=tables or set(),
        )


# Dangerous SQL patterns that should trigger warnings or errors
DANGEROUS_PATTERNS = [
    (r"\bDROP\s+TABLE\b", "DROP TABLE detected - data loss risk", True),
    (r"\bDROP\s+SCHEMA\b", "DROP SCHEMA detected - data loss risk", True),
    (r"\bDROP\s+DATABASE\b", "DROP DATABASE detected - data loss risk", True),
    (r"\bDELETE\s+FROM\b", "DELETE FROM detected - data modification", True),
    (r"\bTRUNCATE\b", "TRUNCATE detected - data loss risk", True),
    (r"\bALTER\s+TABLE\b", "ALTER TABLE detected - schema modification", False),
    (r"\bCREATE\s+OR\s+REPLACE\b", "CREATE OR REPLACE detected", False),
    (r"\bINSERT\s+INTO\b", "INSERT INTO detected - data modification", False),
    (r"\bUPDATE\s+\w+\s+SET\b", "UPDATE SET detected - data modification", True),
    (r"\bMERGE\s+INTO\b", "MERGE INTO detected - data modification", False),
]

# Valid table name pattern: catalog.schema.table or schema.table
TABLE_REF_PATTERN = re.compile(
    r"(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*){1,2})",
    re.IGNORECASE,
)


def validate_query_security(query_text: str) -> Tuple[bool, List[str], List[str]]:
    """
    Check for potentially dangerous SQL patterns.

    Returns:
        (is_safe, errors, warnings)
    """
    if not query_text:
        return False, ["Query text is empty"], []

    query_upper = query_text.upper()
    errors = []
    warnings = []

    for pattern, message, is_error in DANGEROUS_PATTERNS:
        if re.search(pattern, query_upper, re.IGNORECASE):
            if is_error:
                errors.append(f"Security violation: {message}")
            else:
                warnings.append(f"Warning: {message}")

    is_safe = len(errors) == 0
    return is_safe, errors, warnings


def extract_table_references(query_text: str) -> Set[str]:
    """
    Extract table references from SQL query.

    Returns:
        Set of fully qualified table names (catalog.schema.table)
    """
    if not query_text:
        return set()

    matches = TABLE_REF_PATTERN.findall(query_text)
    return set(matches)


def validate_query_syntax_spark(spark, query_text: str) -> Tuple[bool, Optional[str]]:
    """
    Validate SQL query syntax using Spark EXPLAIN.

    Args:
        spark: SparkSession
        query_text: SQL query to validate

    Returns:
        (is_valid, error_message)
    """
    if not query_text:
        return False, "Query text is empty"

    try:
        # EXPLAIN validates syntax without executing
        spark.sql(f"EXPLAIN {query_text}").collect()
        return True, None
    except Exception as e:
        return False, str(e)


def validate_table_exists_spark(spark, table_fqn: str) -> bool:
    """
    Check if a table exists in Unity Catalog.

    Args:
        spark: SparkSession
        table_fqn: Fully qualified table name (catalog.schema.table)

    Returns:
        True if table exists
    """
    try:
        spark.sql(f"DESCRIBE TABLE {table_fqn}").collect()
        return True
    except Exception:
        return False


def validate_query_references_spark(
    spark, query_text: str
) -> Tuple[bool, List[str], List[str]]:
    """
    Validate all table references in query exist.

    Args:
        spark: SparkSession
        query_text: SQL query to validate

    Returns:
        (all_exist, missing_tables, found_tables)
    """
    tables = extract_table_references(query_text)
    missing = []
    found = []

    for table in tables:
        if validate_table_exists_spark(spark, table):
            found.append(table)
        else:
            missing.append(table)

    return len(missing) == 0, missing, found


def validate_alert_query(
    spark,
    query_text: str,
    catalog: str,
    gold_schema: str,
    check_syntax: bool = True,
    check_references: bool = True,
) -> ValidationResult:
    """
    Comprehensive alert query validation.

    Args:
        spark: SparkSession
        query_text: SQL query template
        catalog: Catalog for variable substitution
        gold_schema: Schema for variable substitution
        check_syntax: Whether to validate SQL syntax
        check_references: Whether to validate table references exist

    Returns:
        ValidationResult with is_valid, errors, warnings, tables_referenced
    """
    if not query_text:
        return ValidationResult.failure(["Query text is required"])

    # Step 1: Render template with catalog/schema
    rendered = (
        query_text.replace("${catalog}", catalog)
        .replace("${gold_schema}", gold_schema)
        .strip()
    )

    all_errors = []
    all_warnings = []
    tables_found = set()

    # Step 2: Security check (no Spark required)
    is_safe, sec_errors, sec_warnings = validate_query_security(rendered)
    all_errors.extend(sec_errors)
    all_warnings.extend(sec_warnings)

    # Step 3: Extract table references
    tables_found = extract_table_references(rendered)

    # Step 4: Syntax validation (requires Spark)
    if check_syntax:
        is_valid_syntax, syntax_error = validate_query_syntax_spark(spark, rendered)
        if not is_valid_syntax:
            all_errors.append(f"Syntax error: {syntax_error}")

    # Step 5: Reference validation (requires Spark)
    if check_references:
        all_exist, missing, found = validate_query_references_spark(spark, rendered)
        if not all_exist:
            all_errors.append(f"Missing tables: {', '.join(missing)}")
        tables_found = set(found)

    # Build result
    if all_errors:
        return ValidationResult.failure(all_errors, tables_found)
    else:
        return ValidationResult.success(tables_found, all_warnings)


def validate_template_placeholders(template: str) -> Tuple[bool, List[str]]:
    """
    Validate custom notification template placeholders.

    Valid placeholders:
        {{ALERT_ID}}, {{ALERT_NAME}}, {{SEVERITY}}, {{QUERY_RESULT_VALUE}},
        {{THRESHOLD_VALUE}}, {{OPERATOR}}, {{TIMESTAMP}}, {{ALERT_MESSAGE}}

    Returns:
        (is_valid, invalid_placeholders)
    """
    valid_placeholders = {
        "{{ALERT_ID}}",
        "{{ALERT_NAME}}",
        "{{SEVERITY}}",
        "{{QUERY_RESULT_VALUE}}",
        "{{THRESHOLD_VALUE}}",
        "{{OPERATOR}}",
        "{{TIMESTAMP}}",
        "{{ALERT_MESSAGE}}",
        "{{DOMAIN}}",
        "{{OWNER}}",
    }

    # Find all placeholders in template
    found = set(re.findall(r"\{\{[A-Z_]+\}\}", template or ""))
    invalid = found - valid_placeholders

    return len(invalid) == 0, list(invalid)


def render_test_template(template: str) -> str:
    """
    Render notification template with test values.

    Useful for previewing how notifications will look.
    """
    if not template:
        return ""

    test_values = {
        "{{ALERT_ID}}": "TEST-001",
        "{{ALERT_NAME}}": "Test Alert",
        "{{SEVERITY}}": "WARNING",
        "{{QUERY_RESULT_VALUE}}": "42.5",
        "{{THRESHOLD_VALUE}}": "40.0",
        "{{OPERATOR}}": "GREATER_THAN",
        "{{TIMESTAMP}}": "2025-12-30 12:00:00",
        "{{ALERT_MESSAGE}}": "Test alert triggered",
        "{{DOMAIN}}": "COST",
        "{{OWNER}}": "test@company.com",
    }

    rendered = template
    for placeholder, value in test_values.items():
        rendered = rendered.replace(placeholder, value)

    return rendered

