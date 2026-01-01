# 07 - Quality Agent TVFs

## Overview

The Quality Agent domain provides **7 Table-Valued Functions** for data quality monitoring, freshness tracking, and governance compliance. These TVFs query system tables, lineage data, and job execution history to provide insights into data health.

## TVF Summary

| # | TVF Name | Purpose | Parameters |
|---|----------|---------|------------|
| 1 | `get_table_freshness` | Table update recency | days_back |
| 2 | `get_stale_tables` | Tables not updated recently | days_back, staleness_threshold_days |
| 3 | `get_data_lineage_summary` | Upstream/downstream dependencies | catalog_filter, schema_filter |
| 4 | `get_orphan_tables` | Tables with no recent access | days_back |
| 5 | `get_table_ownership_report` | Table ownership and metadata | catalog_filter |
| 6 | `get_data_freshness_by_domain` | Freshness by schema/domain | days_back |
| 7 | `get_governance_compliance` | Governance tag compliance | catalog_filter |

---

## TVF Definitions

### 1. get_table_freshness

**Purpose**: Monitor when tables were last updated to ensure data currency.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| catalog_name | STRING | Unity Catalog name |
| schema_name | STRING | Schema name |
| table_name | STRING | Table name |
| last_modified | TIMESTAMP | Last update time |
| hours_since_update | DOUBLE | Staleness in hours |
| days_since_update | DOUBLE | Staleness in days |
| update_frequency | STRING | Estimated frequency |
| freshness_status | STRING | FRESH/STALE/CRITICAL |

**Example Queries**:
```sql
-- Check freshness of all tables modified in last 30 days
SELECT * FROM TABLE(get_table_freshness(30));

-- Focus on recent 7 days
SELECT * FROM TABLE(get_table_freshness(7));
```

**Natural Language Examples**:
- "Which tables are stale?"
- "When was data last updated?"
- "Is our data fresh?"

---

### 2. get_stale_tables

**Purpose**: Identify tables that haven't been updated within expected thresholds.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |
| staleness_threshold_days | INT | No | 7 | Days without update to consider stale |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| catalog_name | STRING | Unity Catalog name |
| schema_name | STRING | Schema name |
| table_name | STRING | Table name |
| last_modified | TIMESTAMP | Last update time |
| days_stale | DOUBLE | Days since last update |
| owner | STRING | Table owner |
| expected_frequency | STRING | Expected update cadence |
| alert_level | STRING | CRITICAL/WARNING/INFO |

**Example Queries**:
```sql
-- Tables stale for more than 7 days
SELECT * FROM TABLE(get_stale_tables(30, 7));

-- Tables stale for more than 1 day (daily tables)
SELECT * FROM TABLE(get_stale_tables(30, 1));
```

---

### 3. get_data_lineage_summary

**Purpose**: Summarize data lineage - upstream sources and downstream consumers.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| catalog_filter | STRING | Yes | - | Catalog pattern (SQL LIKE) |
| schema_filter | STRING | No | '%' | Schema pattern (SQL LIKE) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| table_name | STRING | Table full name |
| upstream_count | BIGINT | Number of source tables |
| downstream_count | BIGINT | Number of consumers |
| upstream_tables | STRING | List of sources |
| downstream_tables | STRING | List of consumers |
| lineage_depth | INT | Levels of dependencies |
| last_lineage_event | TIMESTAMP | Most recent lineage event |

**Natural Language Examples**:
- "What are the dependencies for this table?"
- "Show me data lineage"
- "What feeds into gold tables?"

---

### 4. get_orphan_tables

**Purpose**: Identify tables with no recent access or usage.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| catalog_name | STRING | Unity Catalog name |
| schema_name | STRING | Schema name |
| table_name | STRING | Table name |
| last_accessed | TIMESTAMP | Last access time |
| days_since_access | DOUBLE | Days without access |
| storage_size_gb | DOUBLE | Table size |
| estimated_monthly_cost | DOUBLE | Storage cost |
| recommendation | STRING | DELETE/ARCHIVE/REVIEW |

**Natural Language Examples**:
- "Which tables are unused?"
- "Show me orphan tables"
- "What data can we clean up?"

---

### 5. get_table_ownership_report

**Purpose**: Report on table ownership and metadata completeness.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| catalog_filter | STRING | Yes | - | Catalog pattern (SQL LIKE) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| catalog_name | STRING | Unity Catalog name |
| schema_name | STRING | Schema name |
| table_name | STRING | Table name |
| owner | STRING | Current owner |
| has_description | BOOLEAN | Has table comment |
| has_column_comments | BOOLEAN | Has column descriptions |
| tag_count | BIGINT | Number of tags |
| metadata_completeness | DOUBLE | Metadata score (0-100) |

---

### 6. get_data_freshness_by_domain

**Purpose**: Aggregate freshness metrics by schema/domain for portfolio view.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| catalog_name | STRING | Unity Catalog name |
| schema_name | STRING | Schema/domain name |
| total_tables | BIGINT | Number of tables |
| fresh_tables | BIGINT | Tables updated recently |
| stale_tables | BIGINT | Tables not updated |
| avg_hours_since_update | DOUBLE | Average staleness |
| freshness_score | DOUBLE | Overall score (0-100) |
| health_status | STRING | HEALTHY/WARNING/CRITICAL |

**Example Queries**:
```sql
-- Domain freshness for last 30 days
SELECT * FROM TABLE(get_data_freshness_by_domain(30));
```

---

### 7. get_governance_compliance

**Purpose**: Check governance tag compliance across tables.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| catalog_filter | STRING | Yes | - | Catalog pattern (SQL LIKE) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| catalog_name | STRING | Unity Catalog name |
| schema_name | STRING | Schema name |
| table_name | STRING | Table name |
| has_owner_tag | BOOLEAN | Owner tag present |
| has_domain_tag | BOOLEAN | Domain tag present |
| has_classification_tag | BOOLEAN | Data classification tag |
| has_pii_tag | BOOLEAN | PII indicator |
| compliance_score | DOUBLE | Overall compliance (0-100) |
| missing_tags | STRING | List of missing tags |

**Natural Language Examples**:
- "Are our tables properly tagged?"
- "Show me governance compliance"
- "What tables need tags?"

---

## SQL Source

**File Location**: `src/semantic/tvfs/quality_tvfs.sql`

**Tables Used**:
- `information_schema.tables` - Table metadata
- `fact_table_lineage` - Lineage events
- `fact_audit_logs` - Access events for orphan detection
- `dim_job` - Job ownership information

## Next Steps

- **[08-Deployment Guide](08-deployment-guide.md)**: How to deploy TVFs
- **[09-Usage Examples](09-usage-examples.md)**: More query examples

