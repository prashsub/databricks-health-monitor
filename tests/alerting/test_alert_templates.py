"""
Unit tests for alert_templates module.

Run with: pytest -m unit tests/alerting/test_alert_templates.py -v
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest

from alerting.alert_templates import (
    ALERT_TEMPLATES,
    AlertTemplate,
    create_alert_from_template,
    generate_alert_id,
    get_template,
    list_templates,
    list_templates_by_domain,
    render_template,
)


class TestAlertTemplates:
    """Tests for alert template catalog."""

    @pytest.mark.unit
    def test_templates_exist(self):
        """Verify all expected templates are in catalog."""
        expected = [
            "COST_SPIKE",
            "UNTAGGED_RESOURCES",
            "COST_WEEK_OVER_WEEK",
            "JOB_FAILURE_RATE",
            "LONG_RUNNING_JOBS",
            "FAILED_ACCESS_ATTEMPTS",
            "SENSITIVE_DATA_ACCESS",
            "DATA_FRESHNESS",
            "NULL_RATE_SPIKE",
            "QUERY_DURATION_SPIKE",
        ]
        for template_id in expected:
            assert template_id in ALERT_TEMPLATES, f"Missing template: {template_id}"

    @pytest.mark.unit
    def test_list_templates(self):
        """Verify list_templates returns all templates."""
        templates = list_templates()
        assert len(templates) == len(ALERT_TEMPLATES)
        assert all(isinstance(t, AlertTemplate) for t in templates)

    @pytest.mark.unit
    def test_get_template_valid(self):
        """Test getting a valid template."""
        template = get_template("COST_SPIKE")
        assert template.template_id == "COST_SPIKE"
        assert template.domain == "COST"

    @pytest.mark.unit
    def test_get_template_invalid(self):
        """Test getting an invalid template raises error."""
        with pytest.raises(ValueError, match="Unknown template"):
            get_template("INVALID_TEMPLATE")

    @pytest.mark.unit
    def test_get_template_case_insensitive(self):
        """Test template lookup is case insensitive."""
        template = get_template("cost_spike")
        assert template.template_id == "COST_SPIKE"


class TestListTemplatesByDomain:
    """Tests for list_templates_by_domain function."""

    @pytest.mark.unit
    def test_cost_domain(self):
        templates = list_templates_by_domain("COST")
        assert len(templates) >= 3
        assert all(t.domain == "COST" for t in templates)

    @pytest.mark.unit
    def test_reliability_domain(self):
        templates = list_templates_by_domain("RELIABILITY")
        assert len(templates) >= 2
        assert all(t.domain == "RELIABILITY" for t in templates)

    @pytest.mark.unit
    def test_case_insensitive(self):
        templates = list_templates_by_domain("cost")
        assert len(templates) >= 3

    @pytest.mark.unit
    def test_unknown_domain(self):
        templates = list_templates_by_domain("UNKNOWN")
        assert templates == []


class TestRenderTemplate:
    """Tests for render_template function."""

    @pytest.mark.unit
    def test_render_cost_spike(self):
        """Test rendering COST_SPIKE template."""
        template = get_template("COST_SPIKE")
        rendered = render_template(
            template,
            params={"threshold_usd": 10000},
            catalog="my_catalog",
            gold_schema="gold",
        )
        
        assert "alert_query_template" in rendered
        assert "threshold_column" in rendered
        assert "my_catalog.gold.fact_usage" in rendered["alert_query_template"]
        assert "10000" in rendered["alert_query_template"]

    @pytest.mark.unit
    def test_render_missing_required_param(self):
        """Test rendering with missing required param raises error."""
        template = get_template("COST_SPIKE")
        with pytest.raises(ValueError, match="Missing required parameter"):
            render_template(
                template,
                params={},  # Missing threshold_usd
                catalog="my_catalog",
                gold_schema="gold",
            )

    @pytest.mark.unit
    def test_render_with_optional_param(self):
        """Test rendering with optional param override."""
        template = get_template("COST_SPIKE")
        rendered = render_template(
            template,
            params={"threshold_usd": 5000, "lookback_days": 7},
            catalog="cat",
            gold_schema="gold",
        )
        
        assert "7 DAYS" in rendered["alert_query_template"]


class TestGenerateAlertId:
    """Tests for generate_alert_id function."""

    @pytest.mark.unit
    def test_cost_domain(self):
        template = get_template("COST_SPIKE")
        alert_id = generate_alert_id(template, 1)
        assert alert_id == "COST-001"

    @pytest.mark.unit
    def test_reliability_domain(self):
        template = get_template("JOB_FAILURE_RATE")
        alert_id = generate_alert_id(template, 42)
        assert alert_id == "RELI-042"

    @pytest.mark.unit
    def test_security_domain(self):
        template = get_template("FAILED_ACCESS_ATTEMPTS")
        alert_id = generate_alert_id(template, 100)
        assert alert_id == "SECU-100"


class TestCreateAlertFromTemplate:
    """Tests for create_alert_from_template function."""

    @pytest.mark.unit
    def test_create_full_alert(self):
        """Test creating a complete alert configuration."""
        alert = create_alert_from_template(
            template_id="COST_SPIKE",
            alert_name="Daily Cost Alert",
            params={"threshold_usd": 5000},
            catalog="my_catalog",
            gold_schema="gold",
            sequence_number=1,
            owner="finops@company.com",
            description="Custom description",
        )
        
        assert alert["alert_id"] == "COST-001"
        assert alert["alert_name"] == "Daily Cost Alert"
        assert alert["alert_description"] == "Custom description"
        assert alert["owner"] == "finops@company.com"
        assert alert["agent_domain"] == "COST"
        assert alert["severity"] == "WARNING"
        assert alert["is_enabled"] is True
        assert alert["pause_status"] == "PAUSED"  # Starts paused

    @pytest.mark.unit
    def test_create_uses_template_description_by_default(self):
        """Test default description comes from template."""
        alert = create_alert_from_template(
            template_id="COST_SPIKE",
            alert_name="My Alert",
            params={"threshold_usd": 1000},
            catalog="cat",
            gold_schema="gold",
            sequence_number=2,
            owner="owner@company.com",
        )
        
        # Should use template description
        template = get_template("COST_SPIKE")
        assert alert["alert_description"] == template.description

    @pytest.mark.unit
    def test_create_with_tags(self):
        """Test tags are merged from template and params."""
        alert = create_alert_from_template(
            template_id="COST_SPIKE",
            alert_name="Tagged Alert",
            params={
                "threshold_usd": 1000,
                "tags": {"custom": "tag", "team": "finops"},
            },
            catalog="cat",
            gold_schema="gold",
            sequence_number=3,
            owner="owner@company.com",
        )
        
        # Should have template tags + custom tags
        assert "pattern" in alert["tags"]  # From template
        assert alert["tags"]["custom"] == "tag"  # Custom
        assert alert["tags"]["team"] == "finops"  # Custom


class TestTemplateDataIntegrity:
    """Tests for template data integrity."""

    @pytest.mark.unit
    def test_all_templates_have_required_fields(self):
        """Verify all templates have required fields."""
        for template_id, template in ALERT_TEMPLATES.items():
            assert template.template_id, f"{template_id} missing template_id"
            assert template.template_name, f"{template_id} missing template_name"
            assert template.description, f"{template_id} missing description"
            assert template.domain in ["COST", "SECURITY", "PERFORMANCE", "RELIABILITY", "QUALITY"], \
                f"{template_id} has invalid domain"
            assert template.severity in ["CRITICAL", "WARNING", "INFO"], \
                f"{template_id} has invalid severity"
            assert template.query_template, f"{template_id} missing query_template"
            assert template.threshold_column, f"{template_id} missing threshold_column"

    @pytest.mark.unit
    def test_templates_have_valid_cron(self):
        """Verify all templates have valid cron expressions."""
        import re
        cron_pattern = re.compile(r"^\d+\s+[\d\*\/]+\s+[\d\*\/]+\s+[\d\*\?\/]+\s+[\d\*\/]+\s+[\d\*\?\/]+$")
        
        for template_id, template in ALERT_TEMPLATES.items():
            # Basic cron validation (6 fields)
            parts = template.schedule_cron.split()
            assert len(parts) == 6, f"{template_id} has invalid cron: {template.schedule_cron}"

    @pytest.mark.unit
    def test_query_templates_use_placeholders(self):
        """Verify query templates use ${catalog} and ${gold_schema}."""
        for template_id, template in ALERT_TEMPLATES.items():
            assert "${catalog}" in template.query_template or "{catalog}" in template.query_template, \
                f"{template_id} missing catalog placeholder"
            assert "${gold_schema}" in template.query_template or "{gold_schema}" in template.query_template, \
                f"{template_id} missing gold_schema placeholder"

