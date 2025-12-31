"""
Alert Template Library

Pre-built alert templates for common monitoring patterns.
Templates can be customized with parameters and deployed to alert_configurations.

Templates are organized by domain:
- COST: Cost monitoring and FinOps
- SECURITY: Security and compliance
- PERFORMANCE: Job and query performance
- RELIABILITY: Job reliability and SLA
- QUALITY: Data quality monitoring
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AlertTemplate:
    """
    Template for a common alert pattern.

    Attributes:
        template_id: Unique identifier (e.g., 'COST_SPIKE')
        template_name: Human-readable name
        description: What this alert monitors
        domain: Agent domain (COST, SECURITY, PERFORMANCE, RELIABILITY, QUALITY)
        severity: Default severity (CRITICAL, WARNING, INFO)
        required_params: Parameters that must be provided
        optional_params: Parameters with defaults
        query_template: SQL query with {param} placeholders
        threshold_column: Column to evaluate
        threshold_operator: Comparison operator
        default_threshold: Default threshold value
        schedule_cron: Default schedule
        notification_channels: Default channels
        tags: Default tags
    """

    template_id: str
    template_name: str
    description: str
    domain: str
    severity: str
    required_params: List[str]
    optional_params: Dict[str, Any] = field(default_factory=dict)
    query_template: str = ""
    threshold_column: str = ""
    threshold_operator: str = ">"
    default_threshold: float = 0.0
    schedule_cron: str = "0 0 8 * * ?"  # Daily at 8 AM
    schedule_timezone: str = "America/Los_Angeles"
    notification_channels: List[str] = field(default_factory=lambda: ["default_email"])
    tags: Dict[str, str] = field(default_factory=dict)


# ============================================================================
# COST DOMAIN TEMPLATES
# ============================================================================

COST_SPIKE = AlertTemplate(
    template_id="COST_SPIKE",
    template_name="Daily Cost Spike Detection",
    description="Alerts when daily cost exceeds a threshold. Use for budget monitoring.",
    domain="COST",
    severity="WARNING",
    required_params=["threshold_usd"],
    optional_params={"lookback_days": 1},
    query_template="""
SELECT 
    usage_date,
    SUM(list_cost) as daily_cost,
    {threshold_usd} as threshold,
    'WARNING: Daily cost $' || ROUND(SUM(list_cost), 2) || 
        ' exceeds threshold $' || {threshold_usd} as alert_message
FROM ${{catalog}}.${{gold_schema}}.fact_usage
WHERE usage_date >= CURRENT_DATE() - INTERVAL {lookback_days} DAYS
  AND usage_date < CURRENT_DATE()
GROUP BY usage_date
HAVING SUM(list_cost) > {threshold_usd}
""",
    threshold_column="daily_cost",
    threshold_operator=">",
    default_threshold=5000.0,
    schedule_cron="0 0 6 * * ?",  # 6 AM daily
    tags={"pattern": "cost_spike", "category": "budget"},
)

UNTAGGED_RESOURCES = AlertTemplate(
    template_id="UNTAGGED_RESOURCES",
    template_name="Untagged Resources Alert",
    description="Alerts when percentage of untagged cost exceeds threshold. For FinOps hygiene.",
    domain="COST",
    severity="WARNING",
    required_params=["threshold_pct"],
    optional_params={"lookback_days": 7},
    query_template="""
WITH tagged_analysis AS (
    SELECT
        CASE 
            WHEN custom_tags IS NULL OR cardinality(custom_tags) = 0 THEN 'UNTAGGED'
            ELSE 'TAGGED'
        END AS tag_status,
        SUM(list_cost) AS cost
    FROM ${{catalog}}.${{gold_schema}}.fact_usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL {lookback_days} DAYS
    GROUP BY 1
)
SELECT 
    ROUND(SUM(CASE WHEN tag_status = 'UNTAGGED' THEN cost ELSE 0 END) / 
          NULLIF(SUM(cost), 0) * 100, 1) AS untagged_pct,
    {threshold_pct} as threshold,
    'WARNING: ' || 
        ROUND(SUM(CASE WHEN tag_status = 'UNTAGGED' THEN cost ELSE 0 END) / 
              NULLIF(SUM(cost), 0) * 100, 1) || 
        '% of cost is untagged (threshold: ' || {threshold_pct} || '%)' as alert_message
FROM tagged_analysis
HAVING SUM(CASE WHEN tag_status = 'UNTAGGED' THEN cost ELSE 0 END) / 
       NULLIF(SUM(cost), 0) * 100 > {threshold_pct}
""",
    threshold_column="untagged_pct",
    threshold_operator=">",
    default_threshold=20.0,
    tags={"pattern": "tag_coverage", "category": "governance"},
)

COST_WEEK_OVER_WEEK = AlertTemplate(
    template_id="COST_WEEK_OVER_WEEK",
    template_name="Week-over-Week Cost Increase",
    description="Alerts when weekly cost increases by more than threshold percentage.",
    domain="COST",
    severity="WARNING",
    required_params=["threshold_pct"],
    optional_params={},
    query_template="""
WITH weekly AS (
    SELECT
        DATE_TRUNC('week', usage_date) as week_start,
        SUM(list_cost) as weekly_cost
    FROM ${{catalog}}.${{gold_schema}}.fact_usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS
    GROUP BY 1
),
comparison AS (
    SELECT
        current.weekly_cost as current_week,
        previous.weekly_cost as previous_week,
        ROUND((current.weekly_cost - previous.weekly_cost) / 
              NULLIF(previous.weekly_cost, 0) * 100, 1) as pct_change
    FROM weekly current
    JOIN weekly previous ON previous.week_start = current.week_start - INTERVAL 7 DAYS
    WHERE current.week_start = DATE_TRUNC('week', CURRENT_DATE() - INTERVAL 7 DAYS)
)
SELECT
    pct_change,
    {threshold_pct} as threshold,
    'WARNING: Weekly cost increased by ' || pct_change || 
        '% ($' || ROUND(current_week, 2) || ' vs $' || ROUND(previous_week, 2) || ')' as alert_message
FROM comparison
WHERE pct_change > {threshold_pct}
""",
    threshold_column="pct_change",
    threshold_operator=">",
    default_threshold=25.0,
    schedule_cron="0 0 9 ? * MON",  # Monday 9 AM
    tags={"pattern": "wow_change", "category": "trending"},
)


# ============================================================================
# RELIABILITY DOMAIN TEMPLATES
# ============================================================================

JOB_FAILURE_RATE = AlertTemplate(
    template_id="JOB_FAILURE_RATE",
    template_name="Job Failure Rate Alert",
    description="Alerts when job failure rate exceeds threshold in lookback period.",
    domain="RELIABILITY",
    severity="CRITICAL",
    required_params=["threshold_pct"],
    optional_params={"lookback_hours": 24},
    query_template="""
SELECT 
    COUNT(*) as total_jobs,
    SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) as failed_jobs,
    ROUND(SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / 
          NULLIF(COUNT(*), 0), 1) AS failure_rate_pct,
    'CRITICAL: Job failure rate at ' || 
        ROUND(SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / 
              NULLIF(COUNT(*), 0), 1) || 
        '% (' || SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) || 
        ' of ' || COUNT(*) || ' jobs)' as alert_message
FROM ${{catalog}}.${{gold_schema}}.fact_job_run_timeline
WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL {lookback_hours} HOURS
HAVING SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / 
       NULLIF(COUNT(*), 0) > {threshold_pct}
""",
    threshold_column="failure_rate_pct",
    threshold_operator=">",
    default_threshold=10.0,
    schedule_cron="0 */30 * * * ?",  # Every 30 minutes
    tags={"pattern": "failure_rate", "category": "reliability"},
)

LONG_RUNNING_JOBS = AlertTemplate(
    template_id="LONG_RUNNING_JOBS",
    template_name="Long Running Jobs Alert",
    description="Alerts when jobs exceed duration threshold.",
    domain="RELIABILITY",
    severity="WARNING",
    required_params=["threshold_minutes"],
    optional_params={"lookback_hours": 24},
    query_template="""
SELECT 
    COUNT(*) as long_running_count,
    CONCAT_WS(', ', COLLECT_LIST(job_name)) as job_names,
    'WARNING: ' || COUNT(*) || ' jobs running longer than ' || 
        {threshold_minutes} || ' minutes' as alert_message
FROM ${{catalog}}.${{gold_schema}}.fact_job_run_timeline
WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL {lookback_hours} HOURS
  AND duration_seconds > ({threshold_minutes} * 60)
  AND result_state = 'RUNNING'
HAVING COUNT(*) > 0
""",
    threshold_column="long_running_count",
    threshold_operator=">",
    default_threshold=0,
    schedule_cron="0 */15 * * * ?",  # Every 15 minutes
    tags={"pattern": "long_running", "category": "performance"},
)


# ============================================================================
# SECURITY DOMAIN TEMPLATES
# ============================================================================

FAILED_ACCESS_ATTEMPTS = AlertTemplate(
    template_id="FAILED_ACCESS_ATTEMPTS",
    template_name="Failed Access Attempts Alert",
    description="Alerts on spike in failed access attempts for security monitoring.",
    domain="SECURITY",
    severity="CRITICAL",
    required_params=["threshold_count"],
    optional_params={"lookback_hours": 24},
    query_template="""
SELECT 
    COUNT(*) as failed_attempts,
    COUNT(DISTINCT user_identity) as unique_users,
    'CRITICAL: ' || COUNT(*) || ' failed access attempts from ' || 
        COUNT(DISTINCT user_identity) || ' users in last ' || 
        {lookback_hours} || ' hours' as alert_message
FROM ${{catalog}}.${{gold_schema}}.fact_audit_logs
WHERE event_date >= CURRENT_DATE() - INTERVAL {lookback_hours} HOURS
  AND response_status_code >= 400
  AND action_name IN ('accessTable', 'accessCatalog', 'accessSchema', 'query')
HAVING COUNT(*) > {threshold_count}
""",
    threshold_column="failed_attempts",
    threshold_operator=">",
    default_threshold=50,
    schedule_cron="0 0 * * * ?",  # Hourly
    tags={"pattern": "failed_access", "category": "security"},
)

SENSITIVE_DATA_ACCESS = AlertTemplate(
    template_id="SENSITIVE_DATA_ACCESS",
    template_name="Sensitive Data Access Alert",
    description="Alerts when sensitive/PII tables are accessed outside business hours.",
    domain="SECURITY",
    severity="WARNING",
    required_params=["sensitive_schema"],
    optional_params={"start_hour": 6, "end_hour": 20},
    query_template="""
SELECT 
    COUNT(*) as access_count,
    COUNT(DISTINCT user_identity) as unique_users,
    'WARNING: ' || COUNT(*) || ' sensitive data accesses outside business hours' as alert_message
FROM ${{catalog}}.${{gold_schema}}.fact_audit_logs
WHERE event_date = CURRENT_DATE()
  AND (HOUR(event_time) < {start_hour} OR HOUR(event_time) > {end_hour})
  AND request_params LIKE '%{sensitive_schema}%'
  AND action_name IN ('accessTable', 'query')
HAVING COUNT(*) > 0
""",
    threshold_column="access_count",
    threshold_operator=">",
    default_threshold=0,
    schedule_cron="0 0 * * * ?",  # Hourly
    tags={"pattern": "sensitive_access", "category": "compliance"},
)


# ============================================================================
# QUALITY DOMAIN TEMPLATES
# ============================================================================

DATA_FRESHNESS = AlertTemplate(
    template_id="DATA_FRESHNESS",
    template_name="Data Freshness Alert",
    description="Alerts when table hasn't been updated within threshold hours.",
    domain="QUALITY",
    severity="WARNING",
    required_params=["table_name", "threshold_hours"],
    optional_params={},
    query_template="""
SELECT 
    '{table_name}' as table_name,
    TIMESTAMPDIFF(HOUR, MAX(record_updated_timestamp), CURRENT_TIMESTAMP()) as hours_since_update,
    'WARNING: Table {table_name} not updated in ' || 
        TIMESTAMPDIFF(HOUR, MAX(record_updated_timestamp), CURRENT_TIMESTAMP()) || 
        ' hours (threshold: ' || {threshold_hours} || 'h)' as alert_message
FROM ${{catalog}}.${{gold_schema}}.{table_name}
HAVING TIMESTAMPDIFF(HOUR, MAX(record_updated_timestamp), CURRENT_TIMESTAMP()) > {threshold_hours}
""",
    threshold_column="hours_since_update",
    threshold_operator=">",
    default_threshold=24,
    schedule_cron="0 0 * * * ?",  # Hourly
    tags={"pattern": "freshness", "category": "quality"},
)

NULL_RATE_SPIKE = AlertTemplate(
    template_id="NULL_RATE_SPIKE",
    template_name="NULL Rate Spike Alert",
    description="Alerts when NULL rate for a column exceeds threshold.",
    domain="QUALITY",
    severity="WARNING",
    required_params=["table_name", "column_name", "threshold_pct"],
    optional_params={},
    query_template="""
SELECT 
    '{column_name}' as column_name,
    ROUND(SUM(CASE WHEN {column_name} IS NULL THEN 1 ELSE 0 END) * 100.0 / 
          COUNT(*), 2) as null_rate_pct,
    'WARNING: NULL rate for {column_name} is ' || 
        ROUND(SUM(CASE WHEN {column_name} IS NULL THEN 1 ELSE 0 END) * 100.0 / 
              COUNT(*), 2) || 
        '% (threshold: ' || {threshold_pct} || '%)' as alert_message
FROM ${{catalog}}.${{gold_schema}}.{table_name}
WHERE record_updated_timestamp >= CURRENT_DATE() - INTERVAL 1 DAY
HAVING SUM(CASE WHEN {column_name} IS NULL THEN 1 ELSE 0 END) * 100.0 / 
       COUNT(*) > {threshold_pct}
""",
    threshold_column="null_rate_pct",
    threshold_operator=">",
    default_threshold=5.0,
    schedule_cron="0 0 7 * * ?",  # Daily at 7 AM
    tags={"pattern": "null_rate", "category": "quality"},
)


# ============================================================================
# PERFORMANCE DOMAIN TEMPLATES
# ============================================================================

QUERY_DURATION_SPIKE = AlertTemplate(
    template_id="QUERY_DURATION_SPIKE",
    template_name="Query Duration Spike Alert",
    description="Alerts when average query duration exceeds threshold.",
    domain="PERFORMANCE",
    severity="WARNING",
    required_params=["threshold_seconds"],
    optional_params={"lookback_hours": 1},
    query_template="""
SELECT 
    COUNT(*) as query_count,
    ROUND(AVG(duration_ms) / 1000, 2) as avg_duration_seconds,
    ROUND(MAX(duration_ms) / 1000, 2) as max_duration_seconds,
    'WARNING: Avg query duration ' || ROUND(AVG(duration_ms) / 1000, 2) || 
        's exceeds threshold ' || {threshold_seconds} || 's' as alert_message
FROM ${{catalog}}.${{gold_schema}}.fact_query_history
WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL {lookback_hours} HOURS
HAVING AVG(duration_ms) / 1000 > {threshold_seconds}
""",
    threshold_column="avg_duration_seconds",
    threshold_operator=">",
    default_threshold=30.0,
    schedule_cron="0 */15 * * * ?",  # Every 15 minutes
    tags={"pattern": "query_duration", "category": "performance"},
)


# ============================================================================
# TEMPLATE CATALOG
# ============================================================================

ALERT_TEMPLATES: Dict[str, AlertTemplate] = {
    # Cost
    "COST_SPIKE": COST_SPIKE,
    "UNTAGGED_RESOURCES": UNTAGGED_RESOURCES,
    "COST_WEEK_OVER_WEEK": COST_WEEK_OVER_WEEK,
    # Reliability
    "JOB_FAILURE_RATE": JOB_FAILURE_RATE,
    "LONG_RUNNING_JOBS": LONG_RUNNING_JOBS,
    # Security
    "FAILED_ACCESS_ATTEMPTS": FAILED_ACCESS_ATTEMPTS,
    "SENSITIVE_DATA_ACCESS": SENSITIVE_DATA_ACCESS,
    # Quality
    "DATA_FRESHNESS": DATA_FRESHNESS,
    "NULL_RATE_SPIKE": NULL_RATE_SPIKE,
    # Performance
    "QUERY_DURATION_SPIKE": QUERY_DURATION_SPIKE,
}


# ============================================================================
# TEMPLATE FUNCTIONS
# ============================================================================


def list_templates() -> List[AlertTemplate]:
    """List all available alert templates."""
    return list(ALERT_TEMPLATES.values())


def list_templates_by_domain(domain: str) -> List[AlertTemplate]:
    """List templates for a specific domain."""
    return [t for t in ALERT_TEMPLATES.values() if t.domain.upper() == domain.upper()]


def get_template(template_id: str) -> AlertTemplate:
    """Get template by ID."""
    template_id_upper = template_id.upper()
    if template_id_upper not in ALERT_TEMPLATES:
        available = ", ".join(ALERT_TEMPLATES.keys())
        raise ValueError(f"Unknown template: {template_id}. Available: {available}")
    return ALERT_TEMPLATES[template_id_upper]


def render_template(
    template: AlertTemplate,
    params: Dict[str, Any],
    catalog: str,
    gold_schema: str,
) -> Dict[str, Any]:
    """
    Render alert template with user-provided parameters.

    Args:
        template: AlertTemplate to render
        params: User-provided parameter values
        catalog: Target catalog
        gold_schema: Target schema

    Returns:
        Dict suitable for inserting into alert_configurations table
    """
    # Validate required params
    for param in template.required_params:
        if param not in params:
            raise ValueError(f"Missing required parameter: {param}")

    # Merge with defaults
    all_params = {**template.optional_params, **params}

    # Render query with params
    query = template.query_template
    for param, value in all_params.items():
        query = query.replace(f"{{{param}}}", str(value))

    # Render catalog/schema
    query = query.replace("${catalog}", catalog)
    query = query.replace("${gold_schema}", gold_schema)

    return {
        "alert_query_template": query.strip(),
        "threshold_column": template.threshold_column,
        "threshold_operator": template.threshold_operator,
        "threshold_value_type": "DOUBLE",
        "threshold_value_double": params.get("threshold_value", template.default_threshold),
        "agent_domain": template.domain,
        "severity": params.get("severity", template.severity),
        "schedule_cron": params.get("schedule_cron", template.schedule_cron),
        "schedule_timezone": params.get("schedule_timezone", template.schedule_timezone),
        "notification_channels": params.get(
            "notification_channels", template.notification_channels
        ),
        "tags": {**template.tags, **params.get("tags", {})},
    }


def generate_alert_id(template: AlertTemplate, sequence_number: int) -> str:
    """
    Generate alert ID from template.

    Format: DOMAIN-NNN-SEVERITY_PREFIX
    Example: COST-001
    """
    domain_prefix = template.domain[:4].upper()
    return f"{domain_prefix}-{sequence_number:03d}"


def create_alert_from_template(
    template_id: str,
    alert_name: str,
    params: Dict[str, Any],
    catalog: str,
    gold_schema: str,
    sequence_number: int,
    owner: str,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a complete alert configuration from a template.

    Args:
        template_id: Template to use
        alert_name: Custom name for this alert
        params: Template parameters
        catalog: Target catalog
        gold_schema: Target schema
        sequence_number: Sequence number for ID generation
        owner: Alert owner email
        description: Custom description (optional)

    Returns:
        Complete dict for alert_configurations table
    """
    template = get_template(template_id)
    rendered = render_template(template, params, catalog, gold_schema)

    return {
        "alert_id": generate_alert_id(template, sequence_number),
        "alert_name": alert_name,
        "alert_description": description or template.description,
        **rendered,
        "owner": owner,
        "is_enabled": True,
        "pause_status": "PAUSED",  # Start paused for review
        "notify_on_ok": False,
        "use_custom_template": False,
    }

