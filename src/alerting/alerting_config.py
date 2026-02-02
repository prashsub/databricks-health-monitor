"""
TRAINING MATERIAL: Pure Python Configuration Helpers
====================================================

This module demonstrates the "Pure Python for Testability" pattern,
keeping SDK-free helpers for local unit testing.

TESTABILITY ARCHITECTURE:
-------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER                │  SDK IMPORTS?    │  TEST METHOD                 │
├───────────────────────┼──────────────────┼──────────────────────────────┤
│  alerting_config.py   │  ❌ None          │  pytest locally              │
│  query_validator.py   │  ❌ None          │  pytest locally              │
│  sync_sql_alerts.py   │  ✅ SDK required  │  Integration tests           │
└───────────────────────┴──────────────────┴──────────────────────────────┘

SQL ALERTS PARAMETER LIMITATION:
--------------------------------

Databricks SQL Alerts do NOT support ${var} parameter substitution.
Queries must have fully-qualified table names embedded.

    # Alert query CANNOT use parameters
    ❌ SELECT * FROM ${catalog}.${gold_schema}.fact_usage
    
    # Must embed actual values
    ✅ SELECT * FROM health_monitor.gold.fact_usage

This is why render_query_template() exists - to do variable substitution
at deployment time, not query time.

OPERATOR MAPPING:
-----------------

SQL operators → Alerts V2 API enum values:

    ">"  → "GREATER_THAN"
    ">=" → "GREATER_THAN_OR_EQUAL"
    "<"  → "LESS_THAN"
    "="  → "EQUAL"
    "!=" → "NOT_EQUAL"

This module is intentionally free of Databricks SDK imports for testability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


def render_query_template(query_template: str, *, catalog: str, gold_schema: str) -> str:
    """
    SQL alerts do not support ${var} query parameters, so we must embed fully-qualified names.

    We support the same placeholders used across this repo:
    - ${catalog}
    - ${gold_schema}
    """
    if query_template is None:
        raise ValueError("query_template is required")

    rendered = (
        query_template.replace("${catalog}", catalog)
        .replace("${gold_schema}", gold_schema)
        .strip()
    )
    return rendered


def map_operator_to_comparison_operator(op: str) -> str:
    """
    Map common SQL operators to the Alerts v2 comparison_operator enum values.

    We intentionally return strings to keep this module independent of the Databricks SDK.
    """
    if not op:
        raise ValueError("threshold_operator is required")

    normalized = op.strip()
    mapping = {
        ">": "GREATER_THAN",
        ">=": "GREATER_THAN_OR_EQUAL",
        "<": "LESS_THAN",
        "<=": "LESS_THAN_OR_EQUAL",
        "=": "EQUAL",
        "==": "EQUAL",
        "!=": "NOT_EQUAL",
        "<>": "NOT_EQUAL",
    }
    if normalized not in mapping:
        raise ValueError(f"Unsupported threshold_operator: {op}")
    return mapping[normalized]


def normalize_aggregation(aggregation: Optional[str]) -> Optional[str]:
    """
    Normalize aggregation values to Alerts v2 supported enums.
    See docs: SUM, COUNT, COUNT_DISTINCT, AVG, MEDIAN, MIN, MAX, STDDEV
    
    Note: FIRST is treated as no aggregation (returns None) since it's commonly
    used for single-row results where the first value is the only value.
    """
    if aggregation is None:
        return None
    agg = aggregation.strip().upper()
    # FIRST and NONE both mean "no aggregation, use first row value"
    if agg in {"", "NONE", "FIRST"}:
        return None
    valid = {"SUM", "COUNT", "COUNT_DISTINCT", "AVG", "MEDIAN", "MIN", "MAX", "STDDEV"}
    if agg not in valid:
        raise ValueError(f"Unsupported aggregation_type: {aggregation}")
    return agg


def build_threshold_value(value_type: str, value_double: Any, value_string: Any, value_bool: Any) -> Dict[str, Any]:
    """
    Build Alerts v2 threshold.value payload.
    """
    t = (value_type or "").strip().upper()
    if t == "DOUBLE":
        if value_double is None:
            raise ValueError("threshold_value_double is required for DOUBLE threshold_value_type")
        return {"double_value": float(value_double)}
    if t == "STRING":
        if value_string is None:
            raise ValueError("threshold_value_string is required for STRING threshold_value_type")
        return {"string_value": str(value_string)}
    if t == "BOOLEAN":
        if value_bool is None:
            raise ValueError("threshold_value_bool is required for BOOLEAN threshold_value_type")
        return {"bool_value": bool(value_bool)}

    raise ValueError(f"Unsupported threshold_value_type: {value_type}")


def build_subscriptions(
    *,
    channel_ids: Iterable[str],
    destination_id_by_channel_id: Dict[str, str],
) -> List[Dict[str, str]]:
    """
    Convert notification channel ids from alert_configurations into Alerts v2 subscriptions.

    Strategy:
    - If channel_id looks like an email (contains '@') -> user_email subscription.
    - Else, look up in notification_destinations to get databricks destination_id.
    """
    subs: List[Dict[str, str]] = []
    for ch in channel_ids:
        if ch is None:
            continue
        ch_s = str(ch).strip()
        if not ch_s:
            continue
        if "@" in ch_s:
            subs.append({"user_email": ch_s})
            continue
        dest_id = destination_id_by_channel_id.get(ch_s)
        if dest_id:
            subs.append({"destination_id": dest_id})
    return subs


@dataclass(frozen=True)
class AlertConfigRow:
    """Lightweight typed view of an alert configuration row."""

    alert_id: str
    alert_name: str
    agent_domain: str
    severity: str
    alert_query_template: str
    threshold_column: str
    threshold_operator: str
    threshold_value_type: str
    threshold_value_double: Any
    threshold_value_string: Any
    threshold_value_bool: Any
    empty_result_state: str
    aggregation_type: Optional[str]
    schedule_cron: str
    schedule_timezone: str
    pause_status: str
    is_enabled: bool
    notification_channels: List[str]
    notify_on_ok: bool
    retrigger_seconds: Optional[int]
    use_custom_template: bool
    custom_subject_template: Optional[str]
    custom_body_template: Optional[str]

    @staticmethod
    def from_spark_row(row: Any) -> "AlertConfigRow":
        d = row.asDict(recursive=True) if hasattr(row, "asDict") else dict(row)
        return AlertConfigRow(
            alert_id=str(d["alert_id"]),
            alert_name=str(d["alert_name"]),
            agent_domain=str(d["agent_domain"]),
            severity=str(d["severity"]),
            alert_query_template=str(d["alert_query_template"]),
            threshold_column=str(d["threshold_column"]),
            threshold_operator=str(d["threshold_operator"]),
            threshold_value_type=str(d["threshold_value_type"]),
            threshold_value_double=d.get("threshold_value_double"),
            threshold_value_string=d.get("threshold_value_string"),
            threshold_value_bool=d.get("threshold_value_bool"),
            empty_result_state=str(d.get("empty_result_state") or "OK"),
            aggregation_type=d.get("aggregation_type"),
            schedule_cron=str(d["schedule_cron"]),
            schedule_timezone=str(d["schedule_timezone"]),
            pause_status=str(d.get("pause_status") or "UNPAUSED"),
            is_enabled=bool(d.get("is_enabled", True)),
            notification_channels=list(d.get("notification_channels") or []),
            notify_on_ok=bool(d.get("notify_on_ok", False)),
            retrigger_seconds=d.get("retrigger_seconds"),
            use_custom_template=bool(d.get("use_custom_template", False)),
            custom_subject_template=d.get("custom_subject_template"),
            custom_body_template=d.get("custom_body_template"),
        )


