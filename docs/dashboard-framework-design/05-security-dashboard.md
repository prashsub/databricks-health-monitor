# Security Dashboard Specification

## Overview

**Purpose:** Security analytics, threat detection, access pattern analysis, geographic threat visualization, and compliance monitoring for the Databricks platform.

**Existing Dashboards to Consolidate:**
- `security_audit.lvdash.json` (25 datasets)
- Security-related elements from `governance_hub.lvdash.json`

**Target Dataset Count:** ~70 datasets (within 100 limit after enrichment)

**Pages:** 7 total
1. Security Overview (unified dashboard overview page)
2. Event Analysis
3. Access Control
4. Threat Detection
5. Compliance & Audit
6. **Geographic Security** *(NEW - map visualizations)*
7. Security Drift

---

## Page Structure

### Page 1: Security Overview (Overview Page for Unified)
**Purpose:** Executive summary of security health

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Total Events (24h) | KPI | ds_kpi_events | Monitor: total_events |
| Unique Users | KPI | ds_kpi_users | Monitor: distinct_users |
| High Risk Events | KPI | ds_kpi_high_risk | ML: security_threat_detector |
| Failed Auth Count | KPI | ds_kpi_failed_auth | Monitor: failed_auth_count |
| Event Trend | Line | ds_event_trend | - |
| Threat Alerts | Table | ds_ml_threats | ML: security_threat_detector |

### Page 2: Event Analysis
**Purpose:** Deep dive into security events

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Events by Action | Pie | ds_events_by_action | - |
| Events by Service | Bar | ds_events_by_service | - |
| Event Timeline | Line | ds_event_timeline | - |
| Top Users by Activity | Table | ds_top_users | - |
| Admin Actions | Table | ds_admin_actions | Monitor: admin_actions |
| Event Details | Table | ds_event_detail | - |

### Page 3: Access Control
**Purpose:** Authentication and access monitoring

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Failed Auth Trend | Line | ds_failed_auth_trend | Monitor: failed_auth_count |
| Failed Auth Rate | Gauge | ds_failed_auth_rate | Monitor: failed_auth_rate |
| Access Patterns | Table | ds_ml_access_patterns | ML: access_pattern_analyzer |
| Anomalous Access | Table | ds_anomalous_access | ML: access_pattern_analyzer |
| User Sessions | Table | ds_user_sessions | - |
| Permission Changes | Table | ds_perm_changes | - |

### Page 4: Threat Detection
**Purpose:** ML-based threat identification

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Threat Score Distribution | Histogram | ds_threat_dist | ML: security_threat_detector |
| Active Threats | Table | ds_ml_active_threats | ML: security_threat_detector |
| Threat Trend | Line | ds_threat_trend | - |
| Threat by Category | Pie | ds_threat_category | ML: security_threat_detector |
| Compromised Accounts | Table | ds_compromised | ML: security_threat_detector |
| Insider Threats | Table | ds_insider_threats | ML: access_pattern_analyzer |

### Page 5: Compliance & Audit
**Purpose:** Compliance monitoring and audit trails

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Compliance Risk Score | Gauge | ds_compliance_risk | ML: compliance_risk_classifier |
| High Risk Resources | Table | ds_ml_compliance_risk | ML: compliance_risk_classifier |
| Sensitive Actions | Table | ds_sensitive_actions | Monitor: sensitive_actions |
| Data Access Events | Table | ds_data_access | Monitor: data_access_events |
| Audit Trail | Table | ds_audit_trail | - |
| Permission Recommendations | Table | ds_ml_perm_recs | ML: permission_recommender |

### Page 6: Geographic Security
**Purpose:** Visualize global access patterns and detect unusual geographic activity

> ⚠️ **FUTURE CAPABILITY - REQUIRES NEW INFRASTRUCTURE**
> 
> This page requires `dim_ip_geolocation` lookup table which **DOES NOT CURRENTLY EXIST**.
> The `source_ip_address` column exists in `fact_audit_logs` but cannot be mapped to
> geographic locations without additional data infrastructure.
>
> **Prerequisites to implement:**
> 1. Create `dim_ip_geolocation` dimension table (see Implementation Notes below)
> 2. Populate with IP geolocation data (MaxMind GeoLite2 or similar)
> 3. Schedule periodic refresh job

**Widgets (Once Prerequisites Met):**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Access by Country | Choropleth Map | ds_geo_country_access | - |
| Top Access Regions | Bar | ds_geo_top_regions | - |
| Unusual Locations | Table | ds_geo_unusual_locations | ML: access_pattern_analyzer |
| Access Heatmap by Hour/Region | Heatmap | ds_geo_time_heatmap | - |
| Geographic Access Trend | Line | ds_geo_trend | - |
| High-Risk Countries | Table | ds_geo_high_risk | ML: security_threat_detector |
| Cross-Region Access | Table | ds_geo_cross_region | - |
| IP Reputation Alerts | Table | ds_geo_ip_reputation | - |

**Current State:**
- ✅ `source_ip_address` exists in `fact_audit_logs`
- ❌ `dim_ip_geolocation` does not exist - must be created
- ❌ No IP-to-country mapping available

**Available NOW (IP-only widgets):**
| Widget | Type | Dataset | Status |
|--------|------|---------|--------|
| Top Source IPs | Table | ds_ip_top_sources | ✅ Works Today |
| Suspicious IPs | Table | ds_ip_suspicious | ✅ Works Today |
| Users by IP Count | Table | ds_ip_user_mapping | ✅ Works Today |

### Page 7: Security Drift
**Purpose:** Monitor-based security drift detection

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Auth Failure Drift | KPI | ds_auth_drift | Monitor: auth_failure_drift |
| Event Volume Drift | KPI | ds_event_drift | - |
| Security Profile | Table | ds_security_profile | Monitor: profile metrics |
| Drift Trend | Line | ds_security_drift_trend | Monitor: drift metrics |
| Monitor Alerts | Table | ds_security_alerts | - |

---

## Datasets Specification

### Core Datasets

```sql
-- ds_kpi_events
SELECT COUNT(*) AS total_events
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date >= CURRENT_DATE() - INTERVAL 1 DAY

-- ds_kpi_users
SELECT COUNT(DISTINCT user_identity_email) AS unique_users
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date >= CURRENT_DATE() - INTERVAL 1 DAY

-- ds_failed_auth_trend
SELECT 
    event_date,
    SUM(CASE WHEN action_name LIKE '%AuthFail%' OR action_name LIKE '%LoginFail%' THEN 1 ELSE 0 END) AS failed_auth
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY event_date
ORDER BY event_date
```

### IP Analysis Datasets (Available Now)

These queries work **TODAY** with existing `fact_audit_logs` data:

```sql
-- ds_ip_top_sources (WORKS NOW)
-- Top source IP addresses by event count
SELECT 
  source_ip_address,
  COUNT(*) AS event_count,
  COUNT(DISTINCT user_identity_email) AS unique_users,
  SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) AS failed_events,
  ROUND(SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS failure_rate_pct,
  MIN(event_time) AS first_seen,
  MAX(event_time) AS last_seen
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND source_ip_address IS NOT NULL
GROUP BY source_ip_address
ORDER BY event_count DESC
LIMIT 100

-- ds_ip_suspicious (WORKS NOW)
-- IPs with high failure rates (potential brute force)
SELECT 
  source_ip_address,
  COUNT(*) AS total_events,
  SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) AS failed_events,
  ROUND(SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS failure_rate_pct,
  COUNT(DISTINCT user_identity_email) AS targeted_users,
  CASE 
    WHEN SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) > 100 THEN 'Critical - Possible Brute Force'
    WHEN SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) * 100.0 / COUNT(*) > 80 THEN 'High - High Failure Rate'
    WHEN COUNT(DISTINCT user_identity_email) > 10 THEN 'Medium - Multiple Target Users'
    ELSE 'Low'
  END AS risk_level
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND source_ip_address IS NOT NULL
GROUP BY source_ip_address
HAVING SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) >= 5
ORDER BY failed_events DESC
LIMIT 50

-- ds_ip_user_mapping (WORKS NOW)
-- Which IPs are used by which users
SELECT 
  user_identity_email,
  COUNT(DISTINCT source_ip_address) AS unique_ips,
  COLLECT_SET(source_ip_address) AS ip_addresses,
  COUNT(*) AS total_events
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND source_ip_address IS NOT NULL
  AND user_identity_email IS NOT NULL
GROUP BY user_identity_email
HAVING COUNT(DISTINCT source_ip_address) > 5
ORDER BY unique_ips DESC
LIMIT 50
```

### Geographic Datasets (FUTURE - Requires dim_ip_geolocation)

> ⚠️ **THESE QUERIES ARE COMMENTED OUT** - they require `dim_ip_geolocation` which does not exist.
> See "Geographic Security Implementation Notes" section for setup instructions.

```sql
/*
 * ============================================================================
 * COMMENTED OUT: Geographic queries require dim_ip_geolocation table
 * Uncomment these queries after creating the dim_ip_geolocation table
 * ============================================================================

-- ds_geo_country_access
-- Aggregates access events by country for world map visualization
-- ⚠️ REQUIRES: dim_ip_geolocation table (does not exist yet)
WITH ip_locations AS (
  SELECT 
    a.source_ip_address,
    a.event_date,
    a.user_identity_email,
    a.action_name,
    COALESCE(g.country_name, 'Unknown') AS country,
    COALESCE(g.country_iso_code, 'XX') AS country_code,
    COALESCE(g.region_name, 'Unknown') AS region,
    COALESCE(g.latitude, 0) AS latitude,
    COALESCE(g.longitude, 0) AS longitude
  FROM ${catalog}.${gold_schema}.fact_audit_logs a
  LEFT JOIN ${catalog}.${gold_schema}.dim_ip_geolocation g
    ON a.source_ip_address = g.ip_address
  WHERE a.event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND a.source_ip_address IS NOT NULL
)
SELECT 
  country,
  country_code,
  COUNT(*) AS event_count,
  COUNT(DISTINCT user_identity_email) AS unique_users,
  COUNT(DISTINCT source_ip_address) AS unique_ips
FROM ip_locations
GROUP BY country, country_code
ORDER BY event_count DESC;

-- ds_geo_top_regions
-- Top regions by access volume
SELECT 
  COALESCE(g.region_name, 'Unknown') AS region,
  COALESCE(g.country_name, 'Unknown') AS country,
  COUNT(*) AS event_count,
  COUNT(DISTINCT a.user_identity_email) AS unique_users,
  SUM(CASE WHEN a.is_failed_action THEN 1 ELSE 0 END) AS failed_events,
  ROUND(SUM(CASE WHEN a.is_failed_action THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS failure_rate_pct
FROM ${catalog}.${gold_schema}.fact_audit_logs a
LEFT JOIN ${catalog}.${gold_schema}.dim_ip_geolocation g
  ON a.source_ip_address = g.ip_address
WHERE a.event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  AND a.source_ip_address IS NOT NULL
GROUP BY g.region_name, g.country_name
ORDER BY event_count DESC
LIMIT 20;

-- ds_geo_unusual_locations, ds_geo_time_heatmap, ds_geo_trend, 
-- ds_geo_high_risk, ds_geo_cross_region, ds_geo_ip_reputation
-- ... all require dim_ip_geolocation - see Implementation Notes section

 * END COMMENTED SECTION
 */
```

### ML Datasets (FUTURE - Requires ML Pipeline Deployment)

> ⚠️ **THESE QUERIES ARE COMMENTED OUT** - they require ML prediction tables which do not exist yet.
> The following tables must be created by ML pipelines:
> - `security_threat_predictions`
> - `access_pattern_predictions`
> - `compliance_risk_predictions`
> - `permission_recommendations`

```sql
/*
 * ============================================================================
 * COMMENTED OUT: ML queries require prediction tables from ML pipelines
 * Uncomment these queries after deploying the security ML models
 * ============================================================================

-- ds_ml_threats
SELECT 
    detection_date,
    user_id,
    threat_type,
    threat_score,
    is_threat,
    risk_factors,
    recommended_actions
FROM ${catalog}.${gold_schema}.security_threat_predictions
WHERE detection_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND threat_score > 0.7
ORDER BY threat_score DESC
LIMIT 20;

-- ds_ml_access_patterns
SELECT 
    user_id,
    anomaly_probability,
    access_pattern_type,
    baseline_pattern,
    deviation_score,
    detection_date
FROM ${catalog}.${gold_schema}.access_pattern_predictions
WHERE detection_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND anomaly_probability > 0.7
ORDER BY anomaly_probability DESC
LIMIT 20;

-- ds_ml_compliance_risk
SELECT 
    resource_id,
    resource_type,
    risk_category,
    risk_score,
    risk_factors,
    recommended_remediation,
    classification_date
FROM ${catalog}.${gold_schema}.compliance_risk_predictions
WHERE classification_date = CURRENT_DATE()
  AND risk_category IN ('HIGH', 'CRITICAL')
ORDER BY risk_score DESC
LIMIT 20;

-- ds_ml_perm_recs
SELECT 
    user_id,
    current_permissions,
    recommended_permissions,
    permission_change_type,
    justification,
    risk_reduction_pct,
    recommendation_date
FROM ${catalog}.${gold_schema}.permission_recommendations
WHERE recommendation_date = CURRENT_DATE()
ORDER BY risk_reduction_pct DESC
LIMIT 20;

 * END COMMENTED SECTION
 */
```

### Monitor Datasets (Requires Lakehouse Monitoring Setup)

> ⚠️ **CONDITIONAL** - These queries work IF Lakehouse Monitoring has been set up for `fact_audit_logs`.
> The monitoring tables are auto-created in `${gold_schema}_monitoring` schema when monitoring is enabled.
> If monitoring is not set up, these queries will fail with TABLE_OR_VIEW_NOT_FOUND.

```sql
-- ds_security_profile
-- ⚠️ Requires: Lakehouse Monitor on fact_audit_logs (check if monitoring is enabled)
SELECT 
    window.start AS period_start,
    total_events,
    distinct_users,
    failed_auth_count,
    failed_auth_rate * 100 AS failed_auth_rate_pct,
    sensitive_actions,
    admin_actions,
    data_access_events
FROM ${catalog}.${gold_schema}_monitoring.fact_audit_logs_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
ORDER BY window.start DESC
LIMIT 30

-- ds_security_drift
-- ⚠️ Requires: Lakehouse Monitor on fact_audit_logs (check if monitoring is enabled)
SELECT 
    window.start AS period_start,
    auth_failure_drift
FROM ${catalog}.${gold_schema}_monitoring.fact_audit_logs_drift_metrics
WHERE column_name = ':table'
  AND drift_type = 'CONSECUTIVE'
ORDER BY window.start DESC
LIMIT 30
```

---

## Global Filter Integration

All datasets must include:
```sql
WHERE 
  (CASE 
    WHEN :time_window = 'Last 7 Days' THEN event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    WHEN :time_window = 'Last 30 Days' THEN event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    -- ... other time windows
  END)
  AND (:workspace_filter = 'All' OR CAST(workspace_id AS STRING) = :workspace_filter)
```

---

## ML Model Integration Summary (4 Models)

> **Source of Truth:** [07-model-catalog.md](../ml-framework-design/07-model-catalog.md)

| Model | Dashboard Use | Output Table |
|-------|---------------|--------------|
| security_threat_detector | Threat detection, risk alerts | security_threat_predictions |
| access_pattern_analyzer | Anomalous access detection | access_pattern_predictions |
| compliance_risk_classifier | Compliance risk scoring | compliance_risk_predictions |
| permission_recommender | Permission optimization | permission_recommendations |

---

## Monitor Metrics Used

| Monitor | Metrics Used |
|---------|--------------|
| fact_audit_logs_profile_metrics | total_events, distinct_users, failed_auth_count, failed_auth_rate, sensitive_actions, admin_actions, data_access_events |
| fact_audit_logs_drift_metrics | auth_failure_drift |

---

## Geographic Security Implementation Notes

### Required: IP Geolocation Dimension Table

The geographic security page requires an IP geolocation lookup table. Create this dimension table:

```sql
-- DDL for dim_ip_geolocation
CREATE TABLE IF NOT EXISTS ${catalog}.${gold_schema}.dim_ip_geolocation (
  ip_address STRING NOT NULL COMMENT 'IP address or CIDR range',
  ip_range_start BIGINT COMMENT 'Numeric start of IP range for efficient lookup',
  ip_range_end BIGINT COMMENT 'Numeric end of IP range for efficient lookup',
  country_iso_code STRING COMMENT 'ISO 3166-1 alpha-2 country code (e.g., US, GB, CN)',
  country_name STRING COMMENT 'Full country name',
  region_name STRING COMMENT 'State/province/region name',
  city_name STRING COMMENT 'City name (may be null for privacy)',
  postal_code STRING COMMENT 'Postal/ZIP code (optional)',
  latitude DOUBLE COMMENT 'Latitude for map plotting',
  longitude DOUBLE COMMENT 'Longitude for map plotting',
  timezone STRING COMMENT 'IANA timezone identifier',
  isp STRING COMMENT 'Internet Service Provider name',
  organization STRING COMMENT 'Organization name for the IP',
  is_vpn BOOLEAN COMMENT 'Flag indicating known VPN/proxy IP',
  is_datacenter BOOLEAN COMMENT 'Flag indicating datacenter IP (not residential)',
  risk_score INT COMMENT 'IP reputation risk score (0-100)',
  last_updated TIMESTAMP COMMENT 'When this record was last updated',
  CONSTRAINT pk_dim_ip_geolocation PRIMARY KEY (ip_address) NOT ENFORCED
)
USING DELTA
CLUSTER BY AUTO
COMMENT 'IP geolocation lookup table for geographic security analysis. Source: MaxMind GeoIP2 or similar.'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'layer' = 'gold',
  'domain' = 'security',
  'data_source' = 'MaxMind GeoIP2'
);
```

### Data Sources for IP Geolocation

| Source | Type | Cost | Update Frequency | Features |
|--------|------|------|------------------|----------|
| [MaxMind GeoIP2](https://www.maxmind.com/en/geoip2-databases) | Commercial | $$ | Weekly | Most accurate, ISP data, risk scores |
| [MaxMind GeoLite2](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data) | Free | Free | Weekly | Country/city, less accurate |
| [IP2Location](https://www.ip2location.com/) | Commercial | $$ | Monthly | Similar to MaxMind |
| [DB-IP](https://db-ip.com/) | Free/Paid | Free/$$ | Monthly | Good free tier |

### Recommended: Periodic IP Geolocation Refresh Job

```python
# src/pipelines/gold/refresh_ip_geolocation.py
# Schedule: Weekly
# Source: Download from MaxMind or load from external table

import requests
import gzip
from pyspark.sql.functions import *

def refresh_ip_geolocation(spark, catalog: str, schema: str):
    """
    Refresh IP geolocation data from MaxMind GeoLite2 or similar source.
    """
    # Option 1: Load from pre-staged CSV/Parquet in cloud storage
    geo_df = spark.read.format("csv") \
        .option("header", "true") \
        .load(f"s3://your-bucket/geo-data/GeoLite2-City-Blocks-IPv4.csv")
    
    # Option 2: Use Databricks partner integration
    # Some cloud providers have built-in IP geolocation functions
    
    # Transform and merge
    geo_df = geo_df.select(
        col("network").alias("ip_address"),
        col("geoname_id"),
        col("latitude"),
        col("longitude"),
        # ... additional transforms
    )
    
    # Merge into dimension table
    geo_df.write.format("delta") \
        .mode("overwrite") \
        .saveAsTable(f"{catalog}.{schema}.dim_ip_geolocation")
```

### Alternative: UDF-Based Approach (No Lookup Table)

If maintaining a lookup table is not desired, use a UDF:

```python
# Register UDF for IP to country lookup
# Note: This requires network access from the cluster

from pyspark.sql.functions import udf
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
import geoip2.database

# Path to GeoLite2 database file on DBFS
GEOIP_DB_PATH = "/dbfs/FileStore/geoip/GeoLite2-City.mmdb"

@udf(returnType=StructType([
    StructField("country_code", StringType()),
    StructField("country_name", StringType()),
    StructField("city", StringType()),
    StructField("latitude", DoubleType()),
    StructField("longitude", DoubleType())
]))
def ip_to_location(ip_address):
    try:
        with geoip2.database.Reader(GEOIP_DB_PATH) as reader:
            response = reader.city(ip_address)
            return (
                response.country.iso_code,
                response.country.name,
                response.city.name,
                response.location.latitude,
                response.location.longitude
            )
    except:
        return ("XX", "Unknown", "Unknown", 0.0, 0.0)

# Register for SQL usage
spark.udf.register("ip_to_location", ip_to_location)
```

### Lakeview Map Visualization Notes

Databricks Lakeview supports choropleth maps with these requirements:

1. **Country-level maps**: Use ISO 3166-1 alpha-2 codes (US, GB, CN, etc.)
2. **Encoding**: Map `country_code` to the `location` field, `event_count` to `color`
3. **Color scale**: Use diverging scale for risk (green → red)
4. **Widget spec example**:

```json
{
  "widgetType": "map",
  "spec": {
    "version": 3,
    "encodings": {
      "location": {"field": "country_code", "type": "nominal", "displayName": "Country"},
      "color": {"field": "event_count", "type": "quantitative", "displayName": "Events", "scale": {"scheme": "reds"}}
    }
  }
}
```

### Privacy Considerations

- **Do NOT** display precise coordinates or city-level data without user consent
- **Country/region level** is generally acceptable for security dashboards
- Consider **data retention policies** for IP address storage
- For GDPR compliance, consider hashing or anonymizing IP addresses after geolocation lookup

