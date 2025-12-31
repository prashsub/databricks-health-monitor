# Alerting Framework Documentation

**Version:** 2.0 (Phase 2 Complete)  
**Last Updated:** December 30, 2025

---

## Overview

The Databricks Health Monitor Alerting Framework provides a **config-driven SQL alerting system** that:

- Stores alert rules in a Delta configuration table
- Deploys alerts to Databricks SQL Alerts (v2) via REST API
- Supports multiple notification destinations (Email, Slack, Webhook, Teams, PagerDuty)
- Provides pre-deployment query validation
- Includes 10+ pre-built alert templates
- Collects comprehensive sync metrics for observability

---

## Quick Links

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System design and data flow |
| [Configuration Guide](configuration-guide.md) | How to configure alerts |
| [Alert Templates](alert-templates.md) | Pre-built alert templates |
| [Deployment Guide](deployment-guide.md) | How to deploy alerts |
| [Operations Guide](operations-guide.md) | Monitoring and troubleshooting |
| [API Reference](api-reference.md) | Function and class documentation |

---

## Quick Start

### 1. Deploy the Framework
```bash
# Deploy all alerting resources
databricks bundle deploy -t dev

# Run complete alerting setup
databricks bundle run -t dev alerting_layer_setup_job
```

### 2. Add an Alert Configuration
```sql
INSERT INTO catalog.gold.alert_configurations (
    alert_id, alert_name, alert_description, agent_domain, severity,
    alert_query_template, threshold_column, threshold_operator,
    threshold_value_type, threshold_value_double,
    schedule_cron, schedule_timezone, notification_channels,
    owner, created_by, is_enabled
) VALUES (
    'COST-001',
    'Daily Cost Spike',
    'Alerts when daily cost exceeds $5000',
    'COST',
    'WARNING',
    'SELECT SUM(list_cost) as daily_cost FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date = CURRENT_DATE() - 1 HAVING SUM(list_cost) > 5000',
    'daily_cost',
    '>',
    'DOUBLE',
    5000.0,
    '0 0 6 * * ?',
    'America/Los_Angeles',
    array('default_email'),
    'finops@company.com',
    'system',
    TRUE
);
```

### 3. Deploy the Alert
```bash
# Validate queries first
databricks bundle run -t dev alert_query_validation_job

# Deploy (set dry_run: "false" in YAML first)
databricks bundle run -t dev sql_alert_deployment_job
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ALERTING FRAMEWORK                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌────────────────────┐    │
│  │   Alert Config   │    │   Notification   │    │   Alert Sync       │    │
│  │   Table (Delta)  │    │   Destinations   │    │   Metrics          │    │
│  │                  │    │   Table (Delta)  │    │   Table (Delta)    │    │
│  └────────┬─────────┘    └────────┬─────────┘    └────────────────────┘    │
│           │                       │                                         │
│           └───────────┬───────────┘                                         │
│                       │                                                      │
│                       ▼                                                      │
│           ┌──────────────────────┐                                          │
│           │   Query Validator    │ ◄── Pre-deployment validation            │
│           └──────────┬───────────┘                                          │
│                      │                                                       │
│                      ▼                                                       │
│           ┌──────────────────────┐                                          │
│           │   Alert Sync Engine  │ ◄── REST API to Databricks SQL Alerts    │
│           └──────────┬───────────┘                                          │
│                      │                                                       │
│                      ▼                                                       │
│           ┌──────────────────────┐                                          │
│           │  Databricks SQL      │                                          │
│           │  Alerts (v2)         │ ◄── Native alerting infrastructure       │
│           └──────────────────────┘                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Concepts

### Config-Driven Alerting
Alert rules are stored in a Delta table (`alert_configurations`), not hardcoded. This enables:
- Runtime updates without code changes
- Centralized alert management
- Version history via Delta time travel
- Easy enable/disable without deployment

### Two-Job Pattern
The framework separates concerns into two jobs:
1. **Setup Job**: Creates/updates config tables
2. **Deploy Job**: Syncs config to Databricks SQL Alerts

### Fully Qualified Table Names
SQL Alerts do NOT support query parameters. Templates must be rendered with fully qualified names:
```sql
-- Template (stored in config)
SELECT * FROM ${catalog}.${gold_schema}.fact_usage

-- Rendered (deployed to Databricks)
SELECT * FROM my_catalog.gold.fact_usage
```

---

## Components

### Tables

| Table | Purpose |
|-------|---------|
| `alert_configurations` | Central alert rules config |
| `notification_destinations` | Notification channel mappings |
| `alert_history` | Alert evaluation history (optional) |
| `alert_sync_metrics` | Sync operation observability |

### Jobs

| Job | Purpose |
|-----|---------|
| `alerting_layer_setup_job` | Complete framework setup (orchestrator) |
| `alert_query_validation_job` | Pre-deployment query validation |
| `sql_alert_deployment_job` | Deploy alerts to Databricks |
| `alerting_tables_setup_job` | Create/verify tables only |

### Modules

| Module | Purpose |
|--------|---------|
| `alerting_config.py` | Configuration helpers |
| `query_validator.py` | SQL validation |
| `alert_templates.py` | Pre-built templates |
| `alerting_metrics.py` | Metrics collection |
| `sync_sql_alerts.py` | Alert sync engine |
| `validate_all_queries.py` | Validation notebook |
| `sync_notification_destinations.py` | Destination sync |

---

## Alert Domains

Alerts are organized by domain for routing and management:

| Domain | Prefix | Examples |
|--------|--------|----------|
| **COST** | COST | Budget alerts, tag coverage, spend anomalies |
| **SECURITY** | SECU | Access violations, audit events |
| **PERFORMANCE** | PERF | Query latency, cluster utilization |
| **RELIABILITY** | RELI | Job failures, SLA violations |
| **QUALITY** | QUAL | Data freshness, NULL rates, schema drift |

---

## Severity Levels

| Severity | Action | Typical Response Time |
|----------|--------|----------------------|
| **CRITICAL** | Immediate action required | < 15 minutes |
| **WARNING** | Investigate soon | < 4 hours |
| **INFO** | Informational | Daily review |

---

## Support

- **Issues**: Create GitHub issue with `[ALERTING]` prefix
- **Questions**: #data-engineering Slack channel
- **Owner**: Data Platform Team

