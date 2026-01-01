# Security Domain Metric Views

The Security Domain provides security auditing, compliance monitoring, and data governance analytics.

## Views in This Domain

| View | Source | Primary Use Case |
|------|--------|------------------|
| `mv_security_events` | `fact_audit_logs` | Audit event analytics |
| `mv_governance_analytics` | `fact_table_lineage` | Data lineage and governance |

---

## mv_security_events

**Full Name**: `{catalog}.{gold_schema}.mv_security_events`

### Purpose

Security and audit event analytics for compliance monitoring, access tracking, and security incident investigation.

### Key Features

- **User activity tracking** (humans vs service principals)
- **Action categorization** (CRUD + PERMISSION)
- **Sensitive action flagging**
- **Event growth monitoring**

### Example Questions

| Question | Relevant Measures |
|----------|-------------------|
| "Who accessed this resource?" | Filter by `user_email` |
| "Show failed access attempts" | `failed_events` |
| "Sensitive actions in last 24 hours?" | `sensitive_events_24h` |
| "Security events by user" | `total_events` grouped by `user_email` |
| "Event growth rate?" | `event_growth_rate` |

### Key Dimensions

| Dimension | Description |
|-----------|-------------|
| `user_email` | User identity |
| `user_type` | HUMAN, SERVICE_PRINCIPAL, SYSTEM |
| `action_category` | CREATE, READ, UPDATE, DELETE, PERMISSION |
| `service_name` | Databricks service |
| `is_sensitive_action` | Sensitive action flag |
| `workspace_name` | Workspace identifier |

### Key Measures

| Measure | Format | Description |
|---------|--------|-------------|
| `total_events` | number | Total audit events |
| `failed_events` | number | Failed action count |
| `sensitive_events_24h` | number | Recent sensitive actions |
| `unique_users` | number | Distinct users |
| `event_growth_rate` | percentage | Day-over-day change |

### SQL Examples

```sql
-- Events by user type
SELECT 
    user_type,
    MEASURE(total_events) as events,
    MEASURE(unique_users) as users
FROM mv_security_events
GROUP BY user_type;

-- Sensitive actions in last 24 hours
SELECT 
    user_email,
    action_category,
    MEASURE(total_events) as count
FROM mv_security_events
WHERE is_sensitive_action = true
GROUP BY user_email, action_category
ORDER BY count DESC;

-- Failed events by service
SELECT 
    service_name,
    MEASURE(failed_events) as failures,
    MEASURE(total_events) as total
FROM mv_security_events
GROUP BY service_name
HAVING MEASURE(failed_events) > 0;
```

---

## mv_governance_analytics

**Full Name**: `{catalog}.{gold_schema}.mv_governance_analytics`

### Purpose

Data lineage and governance analytics for tracking data access patterns and identifying stale or orphaned data assets.

### Key Features

- **Read/write event tracking**
- **Activity status classification** (ACTIVE, MODERATE, INACTIVE)
- **Entity type breakdown** (NOTEBOOK, JOB, PIPELINE)
- **Stale data detection**

### Example Questions

| Question | Relevant Measures |
|----------|-------------------|
| "Show data lineage" | Query by source/target tables |
| "What tables are actively used?" | `active_table_count` |
| "Which tables are inactive?" | `inactive_table_count` |
| "Read vs write events?" | `read_events`, `write_events` |

### Key Dimensions

| Dimension | Description |
|-----------|-------------|
| `source_table_full_name` | Read table FQN |
| `target_table_full_name` | Write table FQN |
| `entity_type` | NOTEBOOK, JOB, PIPELINE |
| `activity_status` | ACTIVE, MODERATE, INACTIVE |

### Key Measures

| Measure | Format | Description |
|---------|--------|-------------|
| `read_events` | number | Read operation counts |
| `write_events` | number | Write operation counts |
| `active_table_count` | number | Tables accessed in 30d |
| `inactive_table_count` | number | Stale tables |

### SQL Examples

```sql
-- Activity summary
SELECT 
    MEASURE(active_table_count) as active,
    MEASURE(inactive_table_count) as inactive,
    MEASURE(read_events) as reads,
    MEASURE(write_events) as writes
FROM mv_governance_analytics;

-- Tables by activity status
SELECT 
    activity_status,
    MEASURE(active_table_count) as count
FROM mv_governance_analytics
GROUP BY activity_status;

-- Lineage by entity type
SELECT 
    entity_type,
    MEASURE(read_events) as reads,
    MEASURE(write_events) as writes
FROM mv_governance_analytics
GROUP BY entity_type;
```

---

## When to Use Which View

| Use Case | Recommended View |
|----------|------------------|
| User access audit | `mv_security_events` |
| Security incident investigation | `mv_security_events` |
| Compliance reporting | `mv_security_events` |
| Data lineage tracking | `mv_governance_analytics` |
| Stale data identification | `mv_governance_analytics` |
| Data catalog health | `mv_governance_analytics` |

## Related Resources

- [TVFs: Security Agent TVFs](../06-security-agent-tvfs.md)
