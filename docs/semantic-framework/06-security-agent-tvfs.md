# 06 - Security Agent TVFs

## Overview

The Security Agent domain provides **10 Table-Valued Functions** for security audit analysis, access pattern monitoring, and risk scoring. These TVFs query the `fact_audit_logs` and `fact_table_lineage` tables to provide insights into user activity and data access patterns.

## TVF Summary

| # | TVF Name | Purpose | Parameters |
|---|----------|---------|------------|
| 1 | `get_user_activity_summary` | User activity metrics | start_date, end_date, top_n |
| 2 | `get_table_access_audit` | Table access patterns | start_date, end_date |
| 3 | `get_permission_changes` | Permission modifications | days_back |
| 4 | `get_service_account_activity` | Service account monitoring | days_back |
| 5 | `get_failed_access_attempts` | Authentication failures | days_back |
| 6 | `get_sensitive_data_access` | PII/sensitive table access | start_date, end_date |
| 7 | `get_unusual_access_patterns` | Anomalous activity detection | days_back |
| 8 | `get_user_activity_patterns` | Activity patterns by time | days_back |
| 9 | `get_data_export_events` | Data download/export tracking | days_back |
| 10 | `get_user_risk_scores` | User risk assessment | days_back |

---

## TVF Definitions

### 1. get_user_activity_summary

**Purpose**: Comprehensive summary of user activity across the platform.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |
| top_n | INT | No | 50 | Number of users to return |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| rank | INT | Rank by activity volume |
| user_email | STRING | User email address |
| total_events | BIGINT | Total audit events |
| unique_actions | BIGINT | Distinct action types |
| unique_services | BIGINT | Services accessed |
| first_activity | TIMESTAMP | First event in period |
| last_activity | TIMESTAMP | Most recent event |
| primary_action | STRING | Most common action |
| activity_level | STRING | HIGH/MEDIUM/LOW |

**Example Queries**:
```sql
-- Top 50 most active users this month
SELECT * FROM TABLE(get_user_activity_summary('2024-12-01', '2024-12-31', 50));

-- All users in last week
SELECT * FROM TABLE(get_user_activity_summary('2024-12-24', '2024-12-31', 1000));
```

**Natural Language Examples**:
- "Who are the most active users?"
- "Show me user activity this month"
- "What are users doing in the platform?"

---

### 2. get_table_access_audit

**Purpose**: Track which tables are being accessed and by whom.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| catalog_name | STRING | Unity Catalog name |
| schema_name | STRING | Schema name |
| table_name | STRING | Table name |
| access_count | BIGINT | Number of accesses |
| unique_users | BIGINT | Distinct users |
| read_count | BIGINT | SELECT operations |
| write_count | BIGINT | INSERT/UPDATE/DELETE |
| last_accessed | TIMESTAMP | Most recent access |
| primary_accessor | STRING | Most frequent user |

**Natural Language Examples**:
- "Which tables are most accessed?"
- "Show me table access patterns"
- "Who is reading our data?"

---

### 3. get_permission_changes

**Purpose**: Track permission grants, revokes, and modifications.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| event_time | TIMESTAMP | When change occurred |
| action_type | STRING | GRANT/REVOKE/MODIFY |
| changed_by | STRING | Who made the change |
| target_principal | STRING | User/group affected |
| resource_type | STRING | Type of resource |
| resource_name | STRING | Resource affected |
| privilege_granted | STRING | Permission granted |
| privilege_revoked | STRING | Permission revoked |

**Example Queries**:
```sql
-- Permission changes in last 7 days
SELECT * FROM TABLE(get_permission_changes(7));

-- Last 30 days of permission activity
SELECT * FROM TABLE(get_permission_changes(30));
```

---

### 4. get_service_account_activity

**Purpose**: Monitor service account and automation activity.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| service_principal | STRING | Service account name |
| total_events | BIGINT | Total activity |
| unique_actions | BIGINT | Distinct actions |
| primary_action | STRING | Most common action |
| resources_accessed | BIGINT | Resources touched |
| first_activity | TIMESTAMP | First event |
| last_activity | TIMESTAMP | Most recent event |
| avg_daily_events | DOUBLE | Activity volume |

---

### 5. get_failed_access_attempts

**Purpose**: Track failed authentication and authorization attempts.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| user_email | STRING | User attempting access |
| failure_count | BIGINT | Number of failures |
| unique_resources | BIGINT | Resources attempted |
| failure_types | STRING | Types of failures |
| first_failure | TIMESTAMP | First failed attempt |
| last_failure | TIMESTAMP | Most recent failure |
| ip_addresses | STRING | Source IPs |
| risk_level | STRING | HIGH/MEDIUM/LOW |

**Natural Language Examples**:
- "Are there any failed login attempts?"
- "Show me access failures"
- "Who is having permission issues?"

---

### 6. get_sensitive_data_access

**Purpose**: Track access to tables tagged as sensitive or containing PII.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| table_name | STRING | Sensitive table |
| sensitivity_level | STRING | PII/CONFIDENTIAL/etc |
| access_count | BIGINT | Total accesses |
| unique_users | BIGINT | Distinct users |
| user_list | STRING | Users who accessed |
| last_accessed | TIMESTAMP | Most recent access |
| access_type | STRING | READ/WRITE |

---

### 7. get_unusual_access_patterns

**Purpose**: Detect anomalous user activity patterns.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| user_email | STRING | User with unusual activity |
| anomaly_type | STRING | Type of anomaly |
| anomaly_description | STRING | Description |
| event_count | BIGINT | Events in anomaly |
| baseline_count | BIGINT | Expected count |
| deviation_factor | DOUBLE | How far from normal |
| first_anomaly | TIMESTAMP | When started |
| risk_score | DOUBLE | Risk assessment |

**Natural Language Examples**:
- "Is there any unusual activity?"
- "Show me suspicious access patterns"
- "Are there security anomalies?"

---

### 8. get_user_activity_patterns

**Purpose**: Analyze activity patterns by time of day and day of week.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| user_email | STRING | User email |
| total_events | BIGINT | Total activity |
| peak_hour | INT | Most active hour (0-23) |
| peak_hour_events | BIGINT | Events in peak hour |
| weekend_events | BIGINT | Weekend activity |
| after_hours_events | BIGINT | Activity outside 8am-6pm |
| avg_daily_events | DOUBLE | Average per day |

---

### 9. get_data_export_events

**Purpose**: Track data download and export operations.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| event_time | TIMESTAMP | Export timestamp |
| user_email | STRING | User performing export |
| source_table | STRING | Table exported from |
| export_type | STRING | Type of export |
| row_count | BIGINT | Rows exported |
| data_size_mb | DOUBLE | Size of export |
| destination | STRING | Where exported to |

---

### 10. get_user_risk_scores

**Purpose**: Calculate risk scores based on user behavior.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| user_email | STRING | User email |
| risk_score | DOUBLE | Overall risk (0-100) |
| risk_level | STRING | HIGH/MEDIUM/LOW |
| failed_access_score | DOUBLE | Failed access factor |
| unusual_activity_score | DOUBLE | Anomaly factor |
| sensitive_data_score | DOUBLE | Sensitive access factor |
| after_hours_score | DOUBLE | Off-hours activity |
| top_risk_factor | STRING | Primary risk contributor |

**Example Queries**:
```sql
-- Risk scores for last 30 days
SELECT * FROM TABLE(get_user_risk_scores(30));
```

**Natural Language Examples**:
- "Which users have high risk scores?"
- "Show me security risk assessment"
- "Who should we monitor more closely?"

---

## SQL Source

**File Location**: `src/semantic/tvfs/security_tvfs.sql`

**Tables Used**:
- `fact_audit_logs` - Security audit events
- `fact_table_lineage` - Data lineage and access tracking
- `dim_workspace` - Workspace metadata

## Next Steps

- **[07-Quality Agent TVFs](07-quality-agent-tvfs.md)**: Data freshness and governance
- **[09-Usage Examples](09-usage-examples.md)**: More query examples

