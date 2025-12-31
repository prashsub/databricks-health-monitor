"""
Unit tests for alerting configuration helpers.

These tests can run locally without Databricks dependencies.
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from alerting.alerting_config import (
    AlertConfigRow,
    build_subscriptions,
    build_threshold_value,
    map_operator_to_comparison_operator,
    normalize_aggregation,
    render_query_template,
)


# ==============================================================================
# render_query_template tests
# ==============================================================================


@pytest.mark.unit
def test_render_query_template_replaces_placeholders():
    """Test that ${catalog} and ${gold_schema} are replaced."""
    q = "SELECT * FROM ${catalog}.${gold_schema}.fact_usage"
    rendered = render_query_template(q, catalog="c1", gold_schema="s1")
    assert rendered == "SELECT * FROM c1.s1.fact_usage"


@pytest.mark.unit
def test_render_query_template_multiple_placeholders():
    """Test multiple occurrences of placeholders are replaced."""
    q = """
    SELECT *
    FROM ${catalog}.${gold_schema}.table1
    JOIN ${catalog}.${gold_schema}.table2
    """
    rendered = render_query_template(q, catalog="mycat", gold_schema="mygold")
    assert "${catalog}" not in rendered
    assert "${gold_schema}" not in rendered
    assert "mycat.mygold.table1" in rendered
    assert "mycat.mygold.table2" in rendered


@pytest.mark.unit
def test_render_query_template_strips_whitespace():
    """Test that leading/trailing whitespace is stripped."""
    q = "   SELECT 1   "
    rendered = render_query_template(q, catalog="c", gold_schema="s")
    assert rendered == "SELECT 1"


@pytest.mark.unit
def test_render_query_template_none_raises():
    """Test that None query template raises ValueError."""
    with pytest.raises(ValueError, match="query_template is required"):
        render_query_template(None, catalog="c", gold_schema="s")


# ==============================================================================
# map_operator_to_comparison_operator tests
# ==============================================================================


@pytest.mark.unit
def test_operator_mapping_greater_than():
    assert map_operator_to_comparison_operator(">") == "GREATER_THAN"


@pytest.mark.unit
def test_operator_mapping_greater_than_or_equal():
    assert map_operator_to_comparison_operator(">=") == "GREATER_THAN_OR_EQUAL"


@pytest.mark.unit
def test_operator_mapping_less_than():
    assert map_operator_to_comparison_operator("<") == "LESS_THAN"


@pytest.mark.unit
def test_operator_mapping_less_than_or_equal():
    assert map_operator_to_comparison_operator("<=") == "LESS_THAN_OR_EQUAL"


@pytest.mark.unit
def test_operator_mapping_equal_single():
    assert map_operator_to_comparison_operator("=") == "EQUAL"


@pytest.mark.unit
def test_operator_mapping_equal_double():
    assert map_operator_to_comparison_operator("==") == "EQUAL"


@pytest.mark.unit
def test_operator_mapping_not_equal_exclamation():
    assert map_operator_to_comparison_operator("!=") == "NOT_EQUAL"


@pytest.mark.unit
def test_operator_mapping_not_equal_angle():
    assert map_operator_to_comparison_operator("<>") == "NOT_EQUAL"


@pytest.mark.unit
def test_operator_mapping_rejects_unknown():
    """Test that unsupported operators raise ValueError."""
    with pytest.raises(ValueError, match="Unsupported threshold_operator"):
        map_operator_to_comparison_operator("LIKE")


@pytest.mark.unit
def test_operator_mapping_rejects_empty():
    """Test that empty operator raises ValueError."""
    with pytest.raises(ValueError, match="threshold_operator is required"):
        map_operator_to_comparison_operator("")


@pytest.mark.unit
def test_operator_mapping_rejects_none():
    """Test that None operator raises ValueError."""
    with pytest.raises(ValueError, match="threshold_operator is required"):
        map_operator_to_comparison_operator(None)


# ==============================================================================
# normalize_aggregation tests
# ==============================================================================


@pytest.mark.unit
def test_normalize_aggregation_none():
    """Test that None returns None."""
    assert normalize_aggregation(None) is None


@pytest.mark.unit
def test_normalize_aggregation_empty_string():
    """Test that empty string returns None."""
    assert normalize_aggregation("") is None


@pytest.mark.unit
def test_normalize_aggregation_none_string():
    """Test that 'NONE' string returns None."""
    assert normalize_aggregation("none") is None
    assert normalize_aggregation("NONE") is None


@pytest.mark.unit
def test_normalize_aggregation_valid_types():
    """Test all valid aggregation types are normalized to uppercase."""
    valid = ["SUM", "COUNT", "COUNT_DISTINCT", "AVG", "MEDIAN", "MIN", "MAX", "STDDEV"]
    for agg in valid:
        assert normalize_aggregation(agg.lower()) == agg
        assert normalize_aggregation(agg) == agg


@pytest.mark.unit
def test_normalize_aggregation_rejects_first():
    """Test that FIRST raises ValueError (not supported in Alerts v2)."""
    # Note: While the cursor rule mentions FIRST, the Alerts v2 API only supports:
    # SUM, COUNT, COUNT_DISTINCT, AVG, MEDIAN, MIN, MAX, STDDEV
    with pytest.raises(ValueError, match="Unsupported aggregation_type"):
        normalize_aggregation("FIRST")


@pytest.mark.unit
def test_normalize_aggregation_rejects_unknown():
    """Test that unknown aggregation raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported aggregation_type"):
        normalize_aggregation("CUSTOM_AGG")


# ==============================================================================
# build_threshold_value tests
# ==============================================================================


@pytest.mark.unit
def test_build_threshold_value_double():
    """Test DOUBLE threshold value."""
    v = build_threshold_value("DOUBLE", 1.25, None, None)
    assert v == {"double_value": 1.25}


@pytest.mark.unit
def test_build_threshold_value_double_int():
    """Test DOUBLE threshold with int value (should convert)."""
    v = build_threshold_value("DOUBLE", 100, None, None)
    assert v == {"double_value": 100.0}


@pytest.mark.unit
def test_build_threshold_value_string():
    """Test STRING threshold value."""
    v = build_threshold_value("STRING", None, "TRIGGER", None)
    assert v == {"string_value": "TRIGGER"}


@pytest.mark.unit
def test_build_threshold_value_boolean_true():
    """Test BOOLEAN threshold value (True)."""
    v = build_threshold_value("BOOLEAN", None, None, True)
    assert v == {"bool_value": True}


@pytest.mark.unit
def test_build_threshold_value_boolean_false():
    """Test BOOLEAN threshold value (False)."""
    v = build_threshold_value("BOOLEAN", None, None, False)
    assert v == {"bool_value": False}


@pytest.mark.unit
def test_build_threshold_value_double_missing():
    """Test DOUBLE without value raises."""
    with pytest.raises(ValueError, match="threshold_value_double is required"):
        build_threshold_value("DOUBLE", None, None, None)


@pytest.mark.unit
def test_build_threshold_value_string_missing():
    """Test STRING without value raises."""
    with pytest.raises(ValueError, match="threshold_value_string is required"):
        build_threshold_value("STRING", None, None, None)


@pytest.mark.unit
def test_build_threshold_value_boolean_missing():
    """Test BOOLEAN without value raises."""
    with pytest.raises(ValueError, match="threshold_value_bool is required"):
        build_threshold_value("BOOLEAN", None, None, None)


@pytest.mark.unit
def test_build_threshold_value_unknown_type():
    """Test unknown type raises."""
    with pytest.raises(ValueError, match="Unsupported threshold_value_type"):
        build_threshold_value("UNKNOWN", 1.0, "x", True)


# ==============================================================================
# build_subscriptions tests
# ==============================================================================


@pytest.mark.unit
def test_build_subscriptions_email_only():
    """Test email subscriptions."""
    subs = build_subscriptions(
        channel_ids=["user@example.com", "admin@example.com"],
        destination_id_by_channel_id={},
    )
    assert len(subs) == 2
    assert {"user_email": "user@example.com"} in subs
    assert {"user_email": "admin@example.com"} in subs


@pytest.mark.unit
def test_build_subscriptions_destination_id():
    """Test destination_id subscriptions."""
    subs = build_subscriptions(
        channel_ids=["default_email", "slack_channel"],
        destination_id_by_channel_id={
            "default_email": "uuid-123",
            "slack_channel": "uuid-456",
        },
    )
    assert len(subs) == 2
    assert {"destination_id": "uuid-123"} in subs
    assert {"destination_id": "uuid-456"} in subs


@pytest.mark.unit
def test_build_subscriptions_mixed():
    """Test mixed email and destination_id subscriptions."""
    subs = build_subscriptions(
        channel_ids=["default_email", "user@example.com", "unknown_channel"],
        destination_id_by_channel_id={"default_email": "uuid-123"},
    )
    assert len(subs) == 2  # unknown_channel is dropped
    assert {"destination_id": "uuid-123"} in subs
    assert {"user_email": "user@example.com"} in subs


@pytest.mark.unit
def test_build_subscriptions_empty():
    """Test empty channel list."""
    subs = build_subscriptions(
        channel_ids=[],
        destination_id_by_channel_id={},
    )
    assert subs == []


@pytest.mark.unit
def test_build_subscriptions_none_values():
    """Test None values in channel list are skipped."""
    subs = build_subscriptions(
        channel_ids=[None, "user@example.com", None],
        destination_id_by_channel_id={},
    )
    assert len(subs) == 1
    assert {"user_email": "user@example.com"} in subs


@pytest.mark.unit
def test_build_subscriptions_empty_strings():
    """Test empty strings in channel list are skipped."""
    subs = build_subscriptions(
        channel_ids=["", "user@example.com", "   "],
        destination_id_by_channel_id={},
    )
    assert len(subs) == 1


# ==============================================================================
# AlertConfigRow tests
# ==============================================================================


@pytest.mark.unit
def test_alert_config_row_from_dict():
    """Test AlertConfigRow construction from dict."""
    d = {
        "alert_id": "COST-001",
        "alert_name": "Test Alert",
        "agent_domain": "COST",
        "severity": "WARNING",
        "alert_query_template": "SELECT 1",
        "threshold_column": "value",
        "threshold_operator": ">",
        "threshold_value_type": "DOUBLE",
        "threshold_value_double": 100.0,
        "threshold_value_string": None,
        "threshold_value_bool": None,
        "empty_result_state": "OK",
        "aggregation_type": "NONE",
        "schedule_cron": "0 0 * * * ?",
        "schedule_timezone": "America/Los_Angeles",
        "pause_status": "UNPAUSED",
        "is_enabled": True,
        "notification_channels": ["default_email"],
        "notify_on_ok": False,
        "retrigger_seconds": 3600,
        "use_custom_template": False,
        "custom_subject_template": None,
        "custom_body_template": None,
    }

    class MockRow:
        def asDict(self, recursive=False):
            return d

    row = AlertConfigRow.from_spark_row(MockRow())
    assert row.alert_id == "COST-001"
    assert row.alert_name == "Test Alert"
    assert row.severity == "WARNING"
    assert row.threshold_value_double == 100.0
    assert row.notification_channels == ["default_email"]
    assert row.is_enabled is True


@pytest.mark.unit
def test_alert_config_row_defaults():
    """Test AlertConfigRow handles missing optional fields."""
    d = {
        "alert_id": "COST-002",
        "alert_name": "Minimal Alert",
        "agent_domain": "COST",
        "severity": "INFO",
        "alert_query_template": "SELECT 1",
        "threshold_column": "val",
        "threshold_operator": "=",
        "threshold_value_type": "DOUBLE",
        "schedule_cron": "0 0 * * * ?",
        "schedule_timezone": "UTC",
        # Missing optional fields
    }

    class MockRow:
        def asDict(self, recursive=False):
            return d

    row = AlertConfigRow.from_spark_row(MockRow())
    assert row.empty_result_state == "OK"  # default
    assert row.pause_status == "UNPAUSED"  # default
    assert row.is_enabled is True  # default
    assert row.notification_channels == []  # default empty
    assert row.notify_on_ok is False  # default
    assert row.retrigger_seconds is None
    assert row.use_custom_template is False
