# 02 - Architecture Overview

## System Architecture

The Alerting Framework follows a **layered architecture** with clear separation between configuration, processing, and deployment:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ALERTING FRAMEWORK ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐          │
│   │  SQL Editor     │   │  Databricks CLI │   │  Asset Bundle   │          │
│   │  (Manual INSERT)│   │  (bundle run)   │   │  (DAB Deploy)   │          │
│   └────────┬────────┘   └────────┬────────┘   └────────┬────────┘          │
│            │                     │                     │                    │
└────────────┼─────────────────────┼─────────────────────┼────────────────────┘
             │                     │                     │
             ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CONFIGURATION LAYER (Delta Lake)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────────────────┐   ┌───────────────────────┐                    │
│   │ alert_configurations  │   │ notification_         │                    │
│   │                       │   │ destinations          │                    │
│   │ • alert_id (PK)       │   │                       │                    │
│   │ • alert_query_template│   │ • destination_id (PK) │                    │
│   │ • threshold_*         │   │ • destination_type    │                    │
│   │ • schedule_*          │   │ • databricks_dest_id  │                    │
│   │ • notification_*      │   │                       │                    │
│   └───────────────────────┘   └───────────────────────┘                    │
│                                                                             │
│   ┌───────────────────────┐   ┌───────────────────────┐                    │
│   │ alert_validation_     │   │ alert_sync_metrics    │                    │
│   │ results               │   │                       │                    │
│   │                       │   │ • sync_run_id (PK)    │                    │
│   │ • alert_id            │   │ • success_count       │                    │
│   │ • is_valid            │   │ • error_count         │                    │
│   │ • error_message       │   │ • latency metrics     │                    │
│   └───────────────────────┘   └───────────────────────┘                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROCESSING LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     Query Validator                                  │   │
│   │   • Renders ${catalog}/${gold_schema} placeholders                  │   │
│   │   • Executes spark.sql(f"EXPLAIN {query}")                          │   │
│   │   • Catches UNRESOLVED_COLUMN, TABLE_OR_VIEW_NOT_FOUND             │   │
│   │   • Saves results to alert_validation_results                       │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                           │                                                 │
│                           ▼                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     Alert Sync Engine                                │   │
│   │   • Reads enabled configs from Delta                                │   │
│   │   • Builds AlertV2 objects (typed SDK)                              │   │
│   │   • Maps notification channels → destination UUIDs                  │   │
│   │   • Calls ws.alerts_v2.create_alert() / update_alert()             │   │
│   │   • Handles RESOURCE_ALREADY_EXISTS gracefully                      │   │
│   │   • Updates config table with sync status                           │   │
│   │   • Logs metrics to alert_sync_metrics                              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DEPLOYMENT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                 Databricks SQL Alerts (v2 API)                       │   │
│   │                                                                      │   │
│   │   Endpoint: /api/2.0/alerts                                         │   │
│   │   Methods:  POST (create), PATCH (update), DELETE (trash)           │   │
│   │                                                                      │   │
│   │   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │   │
│   │   │ COST-001    │ │ SEC-001     │ │ PERF-001    │ │ RELI-001    │  │   │
│   │   │ Daily Cost  │ │ Failed      │ │ Query       │ │ Job Failure │  │   │
│   │   │ Spike       │ │ Access      │ │ Latency     │ │ Rate        │  │   │
│   │   └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘  │   │
│   │          │               │               │               │          │   │
│   │          └───────────────┼───────────────┼───────────────┘          │   │
│   │                          ▼               ▼                          │   │
│   │                 ┌───────────────────────────────┐                   │   │
│   │                 │   SQL Warehouse               │                   │   │
│   │                 │   (Alert Evaluation Engine)   │                   │   │
│   │                 └───────────────────────────────┘                   │   │
│   │                          │                                          │   │
│   └──────────────────────────┼──────────────────────────────────────────┘   │
│                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                 Notification Destinations                            │   │
│   │                                                                      │   │
│   │   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │   │
│   │   │  Email  │ │  Slack  │ │ Webhook │ │  Teams  │ │PagerDuty│      │   │
│   │   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘      │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Complete Alert Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ALERT LIFECYCLE DATA FLOW                             │
└─────────────────────────────────────────────────────────────────────────────┘

  PHASE 1: CONFIGURATION
  ──────────────────────
  
  ┌──────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
  │ Alert Author │────▶│ INSERT INTO          │────▶│ alert_configurations │
  │ (User/Admin) │     │ alert_configurations │     │ (Delta Table)        │
  └──────────────┘     └──────────────────────┘     └──────────────────────┘
                                                              │
                       OR                                     │
                                                              │
  ┌──────────────┐     ┌──────────────────────┐              │
  │ Seed Script  │────▶│ DataFrame.write()    │──────────────┘
  │ (seed_all_   │     │ (with explicit       │
  │  alerts.py)  │     │  schema)             │
  └──────────────┘     └──────────────────────┘
  
  
  PHASE 2: VALIDATION
  ────────────────────
  
  ┌──────────────────────┐     ┌──────────────────────┐
  │ alert_configurations │────▶│ Query Validator      │
  │ (is_enabled = TRUE)  │     │ (validate_alert_     │
  └──────────────────────┘     │  queries.py)         │
                               └──────────┬───────────┘
                                          │
                                          ▼
                               ┌──────────────────────┐
                               │ For each alert:      │
                               │ 1. Render template   │
                               │ 2. EXPLAIN {query}   │
                               │ 3. Catch errors      │
                               └──────────┬───────────┘
                                          │
                                          ▼
                               ┌──────────────────────┐
                               │ alert_validation_    │
                               │ results              │
                               │ (alert_id, is_valid, │
                               │  error_message)      │
                               └──────────────────────┘
  
  
  PHASE 3: DEPLOYMENT
  ───────────────────
  
  ┌──────────────────────┐     ┌──────────────────────┐
  │ alert_configurations │────▶│ Alert Sync Engine    │
  │ (is_enabled = TRUE   │     │ (sync_sql_alerts.py) │
  │  AND validated)      │     └──────────┬───────────┘
  └──────────────────────┘                │
                                          │
                               ┌──────────┴───────────┐
                               │                      │
                               ▼                      ▼
                    ┌──────────────────┐   ┌──────────────────┐
                    │ Build AlertV2    │   │ Map Notification │
                    │ Object:          │   │ Channels:        │
                    │ • display_name   │   │ • channel_id →   │
                    │ • query_text     │   │   dest_uuid      │
                    │ • warehouse_id   │   │ • email direct   │
                    │ • schedule       │   └────────┬─────────┘
                    │ • evaluation     │            │
                    └────────┬─────────┘            │
                             │                      │
                             └───────────┬──────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────┐
                    │ ws.alerts_v2.create_alert(alert)   │
                    │          OR                         │
                    │ ws.alerts_v2.update_alert(id, ...)  │
                    └────────────────┬────────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────────┐
                    │ Update alert_configurations:        │
                    │ • databricks_alert_id = <uuid>      │
                    │ • last_synced_at = NOW()            │
                    │ • last_sync_status = SUCCESS/ERROR  │
                    └─────────────────────────────────────┘
  
  
  PHASE 4: EXECUTION (Databricks-managed)
  ───────────────────────────────────────
  
  ┌──────────────────────┐     ┌──────────────────────┐
  │ Alert Schedule       │────▶│ SQL Warehouse        │
  │ (cron expression)    │     │ (execute query)      │
  └──────────────────────┘     └──────────┬───────────┘
                                          │
                                          ▼
                               ┌──────────────────────┐
                               │ Evaluate Condition:  │
                               │ threshold_column     │
                               │ threshold_operator   │
                               │ threshold_value      │
                               └──────────┬───────────┘
                                          │
                          ┌───────────────┴───────────────┐
                          │                               │
                          ▼                               ▼
               ┌──────────────────┐           ┌──────────────────┐
               │ Condition TRUE   │           │ Condition FALSE  │
               │ → TRIGGERED      │           │ → OK             │
               └────────┬─────────┘           └──────────────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Send Notification│
               │ to destinations  │
               └──────────────────┘
```

## Component Details

### 1. Configuration Layer

**Purpose**: Store all alert rules and notification channels in Delta tables.

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `alert_configurations` | Alert rules (29 pre-built) | alert_id, query_template, threshold_*, schedule_* |
| `notification_destinations` | Channel mappings | destination_id, destination_type, databricks_destination_id |
| `alert_validation_results` | Query validation status | alert_id, is_valid, error_message |
| `alert_sync_metrics` | Sync operation observability | sync_run_id, success_count, latency_* |

**Why Delta Lake?**
- ACID transactions for concurrent updates
- Time travel for audit history
- Schema evolution for new fields
- Optimized reads with Z-ordering

### 2. Processing Layer

**Purpose**: Transform configuration data into deployable alerts.

**Components:**

| Component | File | Purpose |
|-----------|------|---------|
| Query Validator | `validate_alert_queries.py` | EXPLAIN-based syntax checking |
| Template Renderer | `alerting_config.py` | ${catalog}/${gold_schema} substitution |
| Notification Builder | `alerting_config.py` | Channel → UUID mapping |
| Alert Sync Engine | `sync_sql_alerts.py` | SDK-based deployment |

### 3. Deployment Layer

**Purpose**: Manage alerts in Databricks SQL Alerts infrastructure.

**V2 API Characteristics:**
- Endpoint: `/api/2.0/alerts`
- Supports `query_text` (inline SQL, no saved queries needed)
- Typed SDK objects: `AlertV2`, `AlertV2Condition`, etc.
- Native pagination and error handling

## Technology Stack

### Core Technologies

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Configuration | Delta Lake | 3.0+ | ACID storage for alert rules |
| Deployment | Databricks SDK | ≥0.40.0 | Typed alert management |
| Infrastructure | SQL Alerts v2 | Latest | Native alerting |
| Orchestration | DAB | Latest | Job definitions |
| Governance | Unity Catalog | Latest | Access control |

### Python Dependencies

```python
# requirements.txt (for local development)
databricks-sdk>=0.40.0    # Alert management SDK
pyspark>=3.4.0            # DataFrame operations
delta-spark>=3.0.0        # Delta Lake support

# Automatically available in Databricks notebooks:
# - SparkSession
# - dbutils
# - Databricks SDK with notebook auth
```

### SDK Version Requirements

**Critical**: The alerting framework requires `databricks-sdk>=0.40.0` for the full `AlertV2` type hierarchy. Serverless environments may have older versions pre-installed.

**Solution**: Force upgrade at notebook start:

```python
# At top of sync_sql_alerts.py
%pip install --upgrade databricks-sdk>=0.40.0 --quiet
%restart_python
```

## Security Architecture

### Authentication Flow

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ DAB Job      │────▶│ Notebook Context │────▶│ WorkspaceClient()│
│ (serverless) │     │ (auto-auth)      │     │ (inherited creds)│
└──────────────┘     └──────────────────┘     └────────┬─────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │ Databricks API   │
                                              │ (SQL Alerts v2)  │
                                              └──────────────────┘
```

**Key Points:**
- No explicit PAT or token handling required
- `WorkspaceClient()` inherits notebook context credentials
- Falls back to environment variables if not in notebook

### SQL Injection Prevention

| Risk | Mitigation |
|------|------------|
| Raw SQL in INSERT | Use DataFrame with explicit schema |
| String values in UPDATE | Escape with `replace("'", "''")` |
| User input in queries | Queries are admin-authored only |

### Access Control

| Resource | Permission | Who |
|----------|------------|-----|
| Configuration tables | INSERT/UPDATE | Alert admins |
| Configuration tables | SELECT | Alert consumers |
| SQL Alerts | MANAGE | Deployment service |
| Notification destinations | MANAGE | Platform admins |

## Scalability Considerations

### Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Sync duration | <5 minutes | For 30 alerts |
| SDK call latency | <2s per alert | Create/update |
| Validation duration | <30s total | EXPLAIN parallelized |
| Config table reads | <5s | Optimized Delta |

### Parallel Processing

```python
# Parallel sync configuration
sync_alerts(
    enable_parallel=True,   # Enable ThreadPoolExecutor
    parallel_workers=10     # Concurrent SDK calls
)
```

**Trade-offs:**
- ✅ Faster sync for large alert counts
- ⚠️ May hit API rate limits
- ⚠️ Config table updates remain sequential

### Horizontal Scaling

The framework is designed for single-workspace deployment. For multi-workspace:
- Deploy separate instances per workspace
- Use separate configuration tables
- Consider centralized config with sync jobs

## Error Handling

### Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| SDK import error | ImportError | `%pip install --upgrade` |
| Query syntax error | EXPLAIN fails | Block deployment, log error |
| Alert already exists | RESOURCE_ALREADY_EXISTS | Find and update instead |
| API rate limit | 429 response | Exponential backoff |
| Network timeout | Connection error | Retry with backoff |

### Partial Success Pattern

```python
# Job continues if ≥90% succeed
if success_rate >= 0.90:
    print(f"⚠️ WARNING: {len(errors)} failures (rate: {success_rate:.1%})")
    # Log failed IDs for review
else:
    raise RuntimeError(f"Too many failures ({len(errors)})")
```

## Next Steps

- **[03-Config-Driven Alerting](03-config-driven-alerting.md)**: Delta table schema details
- **[04-Alert Query Patterns](04-alert-query-patterns.md)**: SQL query best practices
- **[05-Databricks SDK Integration](05-databricks-sdk-integration.md)**: SDK types and methods


