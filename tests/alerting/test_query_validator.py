"""
Unit tests for query_validator module.

Run with: pytest -m unit tests/alerting/test_query_validator.py -v
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest

from alerting.query_validator import (
    ValidationResult,
    extract_table_references,
    validate_query_security,
    validate_template_placeholders,
    render_test_template,
)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    @pytest.mark.unit
    def test_success_no_warnings(self):
        result = ValidationResult.success()
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

    @pytest.mark.unit
    def test_success_with_warnings(self):
        result = ValidationResult.success(
            tables={"catalog.schema.table"},
            warnings=["Warning 1"]
        )
        assert result.is_valid is True
        assert result.warnings == ["Warning 1"]
        assert "catalog.schema.table" in result.tables_referenced

    @pytest.mark.unit
    def test_failure(self):
        result = ValidationResult.failure(["Error 1", "Error 2"])
        assert result.is_valid is False
        assert len(result.errors) == 2


class TestQuerySecurity:
    """Tests for validate_query_security function."""

    @pytest.mark.unit
    def test_safe_select_query(self):
        query = "SELECT * FROM catalog.schema.table WHERE x > 1"
        is_safe, errors, warnings = validate_query_security(query)
        assert is_safe is True
        assert errors == []

    @pytest.mark.unit
    def test_drop_table_detected(self):
        query = "DROP TABLE catalog.schema.table"
        is_safe, errors, warnings = validate_query_security(query)
        assert is_safe is False
        assert any("DROP TABLE" in e for e in errors)

    @pytest.mark.unit
    def test_delete_from_detected(self):
        query = "DELETE FROM catalog.schema.table WHERE id = 1"
        is_safe, errors, warnings = validate_query_security(query)
        assert is_safe is False
        assert any("DELETE FROM" in e for e in errors)

    @pytest.mark.unit
    def test_truncate_detected(self):
        query = "TRUNCATE TABLE catalog.schema.table"
        is_safe, errors, warnings = validate_query_security(query)
        assert is_safe is False
        assert any("TRUNCATE" in e for e in errors)

    @pytest.mark.unit
    def test_update_set_detected(self):
        query = "UPDATE catalog.schema.table SET x = 1"
        is_safe, errors, warnings = validate_query_security(query)
        assert is_safe is False
        assert any("UPDATE SET" in e for e in errors)

    @pytest.mark.unit
    def test_alter_table_warning(self):
        query = "ALTER TABLE catalog.schema.table ADD COLUMN x INT"
        is_safe, errors, warnings = validate_query_security(query)
        assert is_safe is True  # Warning, not error
        assert any("ALTER TABLE" in w for w in warnings)

    @pytest.mark.unit
    def test_empty_query(self):
        is_safe, errors, warnings = validate_query_security("")
        assert is_safe is False
        assert any("empty" in e.lower() for e in errors)

    @pytest.mark.unit
    def test_case_insensitive(self):
        query = "drop table catalog.schema.table"
        is_safe, errors, warnings = validate_query_security(query)
        assert is_safe is False


class TestTableReferences:
    """Tests for extract_table_references function."""

    @pytest.mark.unit
    def test_three_part_name(self):
        query = "SELECT * FROM catalog.schema.table"
        tables = extract_table_references(query)
        assert "catalog.schema.table" in tables

    @pytest.mark.unit
    def test_two_part_name(self):
        query = "SELECT * FROM schema.table"
        tables = extract_table_references(query)
        assert "schema.table" in tables

    @pytest.mark.unit
    def test_multiple_tables(self):
        query = """
        SELECT * FROM catalog.schema.table1
        JOIN catalog.schema.table2 ON t1.id = t2.id
        """
        tables = extract_table_references(query)
        assert "catalog.schema.table1" in tables
        assert "catalog.schema.table2" in tables

    @pytest.mark.unit
    def test_empty_query(self):
        tables = extract_table_references("")
        assert tables == set()

    @pytest.mark.unit
    def test_subquery(self):
        query = """
        SELECT * FROM (
            SELECT * FROM catalog.schema.inner_table
        ) sub
        """
        tables = extract_table_references(query)
        assert "catalog.schema.inner_table" in tables


class TestTemplatePlaceholders:
    """Tests for validate_template_placeholders function."""

    @pytest.mark.unit
    def test_valid_placeholders(self):
        template = "Alert {{ALERT_NAME}} triggered at {{TIMESTAMP}}"
        is_valid, invalid = validate_template_placeholders(template)
        assert is_valid is True
        assert invalid == []

    @pytest.mark.unit
    def test_invalid_placeholder(self):
        template = "Alert {{INVALID_PLACEHOLDER}} triggered"
        is_valid, invalid = validate_template_placeholders(template)
        assert is_valid is False
        assert "{{INVALID_PLACEHOLDER}}" in invalid

    @pytest.mark.unit
    def test_mixed_placeholders(self):
        template = "{{ALERT_NAME}} - {{UNKNOWN}}"
        is_valid, invalid = validate_template_placeholders(template)
        assert is_valid is False
        assert "{{UNKNOWN}}" in invalid

    @pytest.mark.unit
    def test_all_valid_placeholders(self):
        template = """
        Alert: {{ALERT_ID}}
        Name: {{ALERT_NAME}}
        Severity: {{SEVERITY}}
        Value: {{QUERY_RESULT_VALUE}}
        Threshold: {{THRESHOLD_VALUE}}
        Operator: {{OPERATOR}}
        Time: {{TIMESTAMP}}
        Message: {{ALERT_MESSAGE}}
        Domain: {{DOMAIN}}
        Owner: {{OWNER}}
        """
        is_valid, invalid = validate_template_placeholders(template)
        assert is_valid is True

    @pytest.mark.unit
    def test_empty_template(self):
        is_valid, invalid = validate_template_placeholders("")
        assert is_valid is True
        assert invalid == []

    @pytest.mark.unit
    def test_none_template(self):
        is_valid, invalid = validate_template_placeholders(None)
        assert is_valid is True


class TestRenderTestTemplate:
    """Tests for render_test_template function."""

    @pytest.mark.unit
    def test_render_template(self):
        template = "Alert {{ALERT_NAME}} at {{TIMESTAMP}}"
        rendered = render_test_template(template)
        assert "Test Alert" in rendered  # Default test value
        assert "{{ALERT_NAME}}" not in rendered

    @pytest.mark.unit
    def test_render_empty(self):
        rendered = render_test_template("")
        assert rendered == ""

    @pytest.mark.unit
    def test_render_none(self):
        rendered = render_test_template(None)
        assert rendered == ""

