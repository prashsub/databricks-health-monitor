# SQL Alerts V2 Implementation Prompt

Use this prompt to create a config-driven SQL alerting framework using Databricks SQL Alerts V2 API.

---

## Prompt

```
I need to implement a config-driven SQL alerting framework for Databricks using SQL Alerts V2.

Requirements:
1. Store alert configurations in a Delta table (alert_configurations)
2. Use Databricks SDK with AlertV2 types for deployment
3. Support CRITICAL, WARNING, and INFO severity levels
4. Enable runtime enable/disable without code changes
5. Track sync status (created, updated, error) in the config table

Technical Requirements:
- API: SQL Alerts V2 (/api/2.0/alerts endpoint)
- SDK: databricks-sdk>=0.40.0 (requires %pip install --upgrade at runtime)
- Queries: Fully qualified table names (no parameters supported)
- Authentication: Auto via WorkspaceClient() in notebook context

Please follow @.cursor/rules/monitoring/19-sql-alerting-patterns.mdc for:
- Alert ID convention: {DOMAIN}-{NUMBER}-{SEVERITY}
- Config table schema
- SDK integration patterns
- V2 API payload structure
```

---

## Quick Reference

### Alert ID Convention
```
{DOMAIN}-{NUMBER}-{SEVERITY}
Examples:
- COST-001-CRIT
- SECURITY-003-WARN
- PERF-005-INFO
```

### SDK Setup (Critical!)
```python
# Databricks notebook source
# MAGIC %pip install --upgrade databricks-sdk>=0.40.0 --quiet

# COMMAND ----------

# MAGIC %restart_python

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import AlertV2
```

### V2 API Payload Structure
```python
alert_dict = {
    "display_name": "[CRITICAL] Alert Name",
    "query_text": "SELECT column FROM catalog.schema.table WHERE condition",
    "warehouse_id": "warehouse-id",
    "schedule": {
        "quartz_cron_schedule": "0 0 * * * ?",  # Every hour
        "timezone_id": "America/Los_Angeles",
        "pause_status": "UNPAUSED"
    },
    "evaluation": {
        "source": {"name": "column_name", "aggregation": "SUM"},
        "comparison_operator": "GREATER_THAN",
        "threshold": {"value": {"double_value": 1000}},
        "empty_result_state": "OK",
        "notification": {
            "notify_on_ok": False,
            "subscriptions": [{"user_email": "user@company.com"}]
        }
    }
}

alert_v2 = AlertV2.from_dict(alert_dict)
ws.alerts_v2.create_alert(alert_v2)
```

### Comparison Operators
| Operator | API Value |
|----------|-----------|
| `>` | `GREATER_THAN` |
| `>=` | `GREATER_THAN_OR_EQUAL` |
| `<` | `LESS_THAN` |
| `<=` | `LESS_THAN_OR_EQUAL` |
| `=` | `EQUAL` |
| `!=` | `NOT_EQUAL` |
| `IS NULL` | `IS_NULL` |

### Aggregation Types
`SUM`, `COUNT`, `COUNT_DISTINCT`, `AVG`, `MEDIAN`, `MIN`, `MAX`, `STDDEV`, `FIRST` (null in API)

---

## Key Learnings

1. **API Endpoint**: Use `/api/2.0/alerts` (NOT `/api/2.0/sql/alerts-v2`)
2. **SDK Version**: Requires `%pip install --upgrade databricks-sdk>=0.40.0` + `%restart_python`
3. **List Response**: V2 API returns `alerts` key (NOT `results`)
4. **Update Mask**: PATCH requests require `update_mask` parameter
5. **RESOURCE_ALREADY_EXISTS**: Handle by refreshing alert list and updating instead
6. **Fully Qualified Names**: Alerts don't support query parameters

---

## File Structure

```
src/alerting/
├── alerting_config.py       # Config helpers, dataclasses
├── alerting_metrics.py      # Metrics collection
├── setup_alerting_tables.py # Creates Delta config tables
├── seed_all_alerts.py       # Seeds all alert configurations
└── sync_sql_alerts.py       # SDK-based sync engine

resources/alerting/
├── alerting_setup_orchestrator_job.yml
├── alerting_seed_job.yml
└── alerting_deploy_job.yml
```

---

## References

- [Cursor Rule](../.cursor/rules/monitoring/19-sql-alerting-patterns.mdc)
- [SDK Docs](https://databricks-sdk-py.readthedocs.io/en/latest/workspace/sql/alerts_v2.html)
- [V2 API Docs](https://docs.databricks.com/api/workspace/alertsv2/createalert)
- [SQL Alerts UI](https://docs.databricks.com/aws/en/sql/user/alerts/)

