# Alerting Framework API Reference

**Version:** 2.0  
**Last Updated:** December 30, 2025

---

## Overview

This document provides API reference for the alerting framework Python modules.

---

## Module: alerting_config

**Location:** `src/alerting/alerting_config.py`

### Classes

#### AlertConfigRow

Dataclass representing a single alert configuration row.

```python
@dataclass
class AlertConfigRow:
    """Represents a single alert configuration from the Delta table."""
    
    alert_id: str
    alert_name: str
    alert_description: Optional[str]
    agent_domain: str
    severity: str
    alert_query_template: str
    query_source: Optional[str]
    source_artifact_name: Optional[str]
    threshold_column: str
    threshold_operator: str
    threshold_value_type: str
    threshold_value_double: Optional[float]
    threshold_value_string: Optional[str]
    threshold_value_bool: Optional[bool]
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
    owner: str
    created_by: str
    created_at: datetime
    updated_by: Optional[str]
    updated_at: Optional[datetime]
    tags: Optional[Dict[str, str]]
    databricks_alert_id: Optional[str]
    databricks_display_name: Optional[str]
    last_synced_at: Optional[datetime]
    last_sync_status: Optional[str]
    last_sync_error: Optional[str]
    
    @classmethod
    def from_spark_row(cls, row: Row) -> "AlertConfigRow":
        """Create AlertConfigRow from Spark Row."""
        pass
```

### Functions

#### render_query_template

Renders SQL template with catalog and schema placeholders.

```python
def render_query_template(
    template: str,
    catalog: str,
    gold_schema: str
) -> str:
    """
    Render a SQL query template by substituting placeholders.
    
    Args:
        template: SQL query with ${catalog} and ${gold_schema} placeholders
        catalog: Target catalog name
        gold_schema: Target schema name
    
    Returns:
        Rendered SQL query string
    
    Example:
        >>> render_query_template(
        ...     "SELECT * FROM ${catalog}.${gold_schema}.my_table",
        ...     "prod_catalog",
        ...     "gold"
        ... )
        'SELECT * FROM prod_catalog.gold.my_table'
    """
```

#### map_operator

Maps operator string to Alerts API enum.

```python
def map_operator(op: str) -> str:
    """
    Map threshold operator to Alerts v2 API enum value.
    
    Args:
        op: Operator string (>, <, >=, <=, =, !=)
    
    Returns:
        API enum string (GREATER_THAN, LESS_THAN, etc.)
    
    Raises:
        ValueError: If operator is not supported
    
    Mapping:
        '>'  -> 'GREATER_THAN'
        '<'  -> 'LESS_THAN'
        '>=' -> 'GREATER_THAN_OR_EQUAL'
        '<=' -> 'LESS_THAN_OR_EQUAL'
        '='  -> 'EQUAL'
        '!=' -> 'NOT_EQUAL'
    """
```

#### normalize_aggregation

Validates and normalizes aggregation type.

```python
def normalize_aggregation(aggregation: Optional[str]) -> Optional[str]:
    """
    Normalize aggregation values to Alerts v2 supported enums.
    
    Args:
        aggregation: Raw aggregation string or None
    
    Returns:
        Normalized uppercase aggregation or None
    
    Raises:
        ValueError: If aggregation is not supported
    
    Supported values:
        SUM, COUNT, COUNT_DISTINCT, AVG, MEDIAN, MIN, MAX, STDDEV, FIRST
    """
```

#### build_threshold_value

Builds threshold value for API payload.

```python
def build_threshold_value(cfg: AlertConfigRow) -> Dict[str, Any]:
    """
    Build the threshold value object for the Alerts API.
    
    Args:
        cfg: Alert configuration row
    
    Returns:
        Dict with appropriate threshold value field
    
    Example:
        >>> build_threshold_value(cfg)  # DOUBLE type
        {'double_value': 5000.0}
        
        >>> build_threshold_value(cfg)  # STRING type
        {'string_value': 'FAILED'}
    """
```

#### build_subscriptions

Builds notification subscriptions for API payload.

```python
def build_subscriptions(
    channels: List[str],
    destination_map: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Build notification subscriptions from channel list.
    
    Args:
        channels: List of channel IDs or email addresses
        destination_map: Mapping of channel IDs to Databricks destination UUIDs
    
    Returns:
        List of subscription dicts for API payload
    
    Example:
        >>> build_subscriptions(
        ...     ['finops@company.com', 'slack_channel'],
        ...     {'slack_channel': 'uuid-123'}
        ... )
        [
            {'user_email': 'finops@company.com'},
            {'destination_id': 'uuid-123'}
        ]
    """
```

---

## Module: sync_sql_alerts

**Location:** `src/alerting/sync_sql_alerts.py`

### Main Function

#### sync_alerts

Synchronizes alert configurations to Databricks SQL Alerts.

```python
def sync_alerts(
    spark: SparkSession,
    *,
    catalog: str,
    gold_schema: str,
    warehouse_id: str,
    dry_run: bool,
    # api_base parameter removed - SDK handles endpoint automatically
    delete_disabled: bool = True,
    parallel: bool = False,
    max_workers: int = 5
) -> None:
    """
    Synchronize alert configurations from Delta table to Databricks SQL Alerts.
    
    Args:
        spark: SparkSession
        catalog: Unity Catalog name
        gold_schema: Schema containing config tables
        warehouse_id: SQL Warehouse ID for alert execution
        dry_run: If True, skip API calls (validation only)
        api_base: Alerts API base path
        delete_disabled: If True, delete alerts not in enabled config
        parallel: If True, use parallel API calls
        max_workers: Number of parallel workers (if parallel=True)
    
    Raises:
        RuntimeError: If any alerts fail to sync
    
    Side Effects:
        - Creates/updates/deletes Databricks SQL Alerts
        - Updates alert_configurations table with sync status
        - Inserts metrics into alert_sync_metrics table
    """
```

### Helper Functions

#### create_alert

Creates a new SQL Alert via API.

```python
def create_alert(
    host: str,
    token: str,
    api_base: str,
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a new SQL Alert.
    
    Args:
        host: Databricks workspace URL
        token: Authentication token
        api_base: API base path
        payload: Alert configuration payload
    
    Returns:
        Created alert response with ID
    
    Raises:
        Exception: If API call fails after retries
    """
```

#### update_alert

Updates an existing SQL Alert.

```python
def update_alert(
    host: str,
    token: str,
    api_base: str,
    alert_id: str,
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update an existing SQL Alert.
    
    Args:
        host: Databricks workspace URL
        token: Authentication token
        api_base: API base path
        alert_id: Existing alert UUID
        payload: Updated alert configuration
    
    Returns:
        Updated alert response
    
    Raises:
        Exception: If API call fails after retries
    """
```

#### delete_alert

Deletes a SQL Alert.

```python
def delete_alert(
    host: str,
    token: str,
    api_base: str,
    alert_id: str
) -> None:
    """
    Delete a SQL Alert.
    
    Args:
        host: Databricks workspace URL
        token: Authentication token
        api_base: API base path
        alert_id: Alert UUID to delete
    
    Raises:
        Exception: If API call fails after retries
    """
```

#### list_alerts

Lists all existing SQL Alerts.

```python
def list_alerts(
    host: str,
    token: str,
    api_base: str
) -> Dict[str, Dict[str, Any]]:
    """
    List all SQL Alerts in the workspace.
    
    Args:
        host: Databricks workspace URL
        token: Authentication token
        api_base: API base path
    
    Returns:
        Dict mapping display_name to alert data
    """
```

---

## Module: query_validator

**Location:** `src/alerting/query_validator.py`

### Classes

#### ValidationResult

```python
@dataclass
class ValidationResult:
    """Result of query validation."""
    
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    tables_referenced: Set[str]
    validation_time_ms: float
```

### Functions

#### validate_alert_query

Validates a single alert query.

```python
def validate_alert_query(
    spark: SparkSession,
    query_template: str,
    catalog: str,
    gold_schema: str,
    alert_id: str = "UNKNOWN"
) -> ValidationResult:
    """
    Validate an alert query for syntax and security.
    
    Args:
        spark: SparkSession
        query_template: SQL query with placeholders
        catalog: Target catalog
        gold_schema: Target schema
        alert_id: Alert identifier for logging
    
    Returns:
        ValidationResult with validity status and details
    
    Validation Steps:
        1. Render template
        2. Security pattern check (DROP, DELETE, etc.)
        3. SQL syntax validation (EXPLAIN)
        4. Table reference validation (DESCRIBE)
    """
```

#### validate_all_enabled_alerts

Validates all enabled alerts in the config table.

```python
def validate_all_enabled_alerts(
    spark: SparkSession,
    catalog: str,
    gold_schema: str
) -> Tuple[int, int, List[Tuple[str, str]]]:
    """
    Validate all enabled alert queries.
    
    Args:
        spark: SparkSession
        catalog: Unity Catalog name
        gold_schema: Schema name
    
    Returns:
        Tuple of (valid_count, invalid_count, errors_list)
        errors_list contains (alert_id, error_message) tuples
    """
```

#### check_security_patterns

Checks for dangerous SQL patterns.

```python
def check_security_patterns(query: str) -> Tuple[List[str], List[str]]:
    """
    Check query for security-sensitive patterns.
    
    Args:
        query: SQL query to check
    
    Returns:
        Tuple of (errors, warnings)
    
    Blocked Patterns (errors):
        - DROP TABLE/VIEW/SCHEMA
        - DELETE FROM
        - TRUNCATE TABLE
    
    Warning Patterns:
        - UPDATE ... SET
        - ALTER TABLE
        - INSERT INTO
    """
```

---

## Module: alert_templates

**Location:** `src/alerting/alert_templates.py`

### Classes

#### TemplateParameter

```python
@dataclass
class TemplateParameter:
    """Parameter definition for an alert template."""
    
    name: str
    param_type: str  # DOUBLE, STRING, INT, BOOLEAN
    description: str
    default_value: Any
    required: bool = True
```

#### AlertTemplate

```python
@dataclass
class AlertTemplate:
    """Alert template definition."""
    
    template_id: str
    name: str
    description: str
    domain: str
    default_severity: str
    parameters: List[TemplateParameter]
    query_template: str
    threshold_column: str
    threshold_operator: str
    threshold_value_type: str
    recommended_schedule: str
    recommended_timezone: str
```

### Functions

#### get_template

Gets a template by ID.

```python
def get_template(template_id: str) -> AlertTemplate:
    """
    Get an alert template by ID.
    
    Args:
        template_id: Template identifier
    
    Returns:
        AlertTemplate object
    
    Raises:
        KeyError: If template not found
    """
```

#### list_templates

Lists all available templates.

```python
def list_templates() -> List[AlertTemplate]:
    """
    List all available alert templates.
    
    Returns:
        List of AlertTemplate objects
    """
```

#### create_alert_from_template

Creates an alert configuration from a template.

```python
def create_alert_from_template(
    template_id: str,
    alert_name: str,
    params: Dict[str, Any],
    catalog: str,
    gold_schema: str,
    sequence_number: int,
    owner: str,
    notification_channels: List[str] = None,
    severity: str = None,
    schedule_cron: str = None,
    schedule_timezone: str = None,
    tags: Dict[str, str] = None
) -> AlertConfigRow:
    """
    Create an alert configuration from a template.
    
    Args:
        template_id: Template to use
        alert_name: Display name for the alert
        params: Parameter values to substitute
        catalog: Unity Catalog name
        gold_schema: Schema name
        sequence_number: Sequence for alert_id (e.g., COST-001)
        owner: Alert owner email
        notification_channels: Override notification channels
        severity: Override default severity
        schedule_cron: Override schedule
        schedule_timezone: Override timezone
        tags: Additional tags
    
    Returns:
        AlertConfigRow ready for insertion
    
    Example:
        >>> create_alert_from_template(
        ...     template_id="COST_DAILY_SPIKE",
        ...     alert_name="My Daily Cost Alert",
        ...     params={"threshold_usd": 3000.0},
        ...     catalog="my_catalog",
        ...     gold_schema="gold",
        ...     sequence_number=1,
        ...     owner="finops@company.com"
        ... )
    """
```

---

## Module: alerting_metrics

**Location:** `src/alerting/alerting_metrics.py`

### Classes

#### SyncMetrics

```python
@dataclass
class SyncMetrics:
    """Metrics collected during a sync operation."""
    
    sync_run_id: str
    sync_started_at: datetime
    sync_ended_at: datetime
    total_alerts: int
    success_count: int
    error_count: int
    created_count: int
    updated_count: int
    deleted_count: int
    skipped_count: int
    api_latencies_ms: List[float]
    dry_run: bool
    catalog: str
    gold_schema: str
    error_summary: Optional[str]
    
    @property
    def avg_api_latency_ms(self) -> float:
        """Calculate average API latency."""
        pass
    
    @property
    def max_api_latency_ms(self) -> float:
        """Calculate max API latency."""
        pass
    
    @property
    def min_api_latency_ms(self) -> float:
        """Calculate min API latency."""
        pass
    
    @property
    def p95_api_latency_ms(self) -> float:
        """Calculate P95 API latency."""
        pass
    
    @property
    def total_duration_seconds(self) -> float:
        """Calculate total sync duration."""
        pass
```

### Functions

#### log_sync_metrics

Logs sync metrics to Delta table.

```python
def log_sync_metrics(
    spark: SparkSession,
    metrics: SyncMetrics,
    catalog: str,
    gold_schema: str
) -> None:
    """
    Log sync metrics to alert_sync_metrics table.
    
    Args:
        spark: SparkSession
        metrics: SyncMetrics object
        catalog: Unity Catalog name
        gold_schema: Schema name
    """
```

---

## Databricks SQL Alerts v2 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/2.0/alerts` | List all alerts (paginated) |
| POST | `/api/2.0/alerts` | Create alert |
| GET | `/api/2.0/alerts/{id}` | Get alert by ID |
| PATCH | `/api/2.0/alerts/{id}?update_mask=...` | Update alert (requires update_mask) |
| DELETE | `/api/2.0/alerts/{id}` | Trash alert (soft delete, 30-day recovery) |

### Alert Payload Schema

```json
{
  "display_name": "string",
  "query_text": "string",
  "warehouse_id": "string",
  "schedule": {
    "quartz_cron_schedule": "string",
    "timezone_id": "string",
    "pause_status": "UNPAUSED | PAUSED"
  },
  "evaluation": {
    "source": {
      "type": "QUERY_RESULT",
      "column_name": "string",
      "aggregation": "SUM | COUNT | AVG | MIN | MAX | FIRST | ...",
      "empty_result_state": "OK | TRIGGERED | ERROR"
    },
    "comparison": {
      "operator": "GREATER_THAN | LESS_THAN | EQUAL | ...",
      "threshold": {
        "double_value": 0.0
      }
    }
  },
  "notification": {
    "subscriptions": [
      {"user_email": "string"},
      {"destination_id": "string"}
    ],
    "notify_on_ok": false,
    "retrigger_seconds": 0
  }
}
```

---

## Error Handling

### Exception Classes

```python
class AlertSyncError(Exception):
    """Base exception for alert sync errors."""
    pass

class AlertValidationError(AlertSyncError):
    """Raised when alert validation fails."""
    pass

class AlertAPIError(AlertSyncError):
    """Raised when API call fails."""
    pass
```

### Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| 400 | Bad Request | Check payload format |
| 401 | Unauthorized | Refresh token |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Alert ID incorrect |
| 429 | Rate Limited | Wait and retry |
| 500 | Server Error | Retry later |

