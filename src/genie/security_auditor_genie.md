# Security Auditor Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Security Auditor Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for Databricks security, audit, and compliance analytics. Enables security teams, compliance officers, and administrators to query access patterns, audit trails, and security events without SQL.

**Powered by:**
- 2 Metric Views (security_events, governance_analytics)
- 10 Table-Valued Functions (user activity, sensitive access, audit queries)
- 4 ML Prediction Tables (threat detection, risk scoring, access classification)
- 2 Lakehouse Monitoring Tables (security drift and profile metrics)
- 3 Dimension Tables (workspace, user, date)
- 6 Fact Tables (audit logs, lineage, network traffic, clean rooms)

---

## ████ SECTION C: SAMPLE QUESTIONS ████

### Access Monitoring
1. "Who accessed this table?"
2. "Show me user activity for john@company.com"
3. "Which tables are most frequently accessed?"
4. "Who accessed sensitive data this week?"

### Audit Analysis
5. "Show me failed access attempts"
6. "What permission changes happened today?"
7. "Show me off-hours activity"
8. "Which service accounts are most active?"

### Security Patterns
9. "Show me bursty user activity"
10. "What sensitive actions occurred?"
11. "Show me security events timeline"
12. "Which users have the most failed actions?"

### ML-Powered Insights 🤖
13. "Are there any security anomalies?"
14. "What's the risk score for this user?"
15. "Show me suspicious activity patterns"

---

## ████ SECTION D: DATA ASSETS ████

### Metric Views (PRIMARY - Use First)

| Metric View Name | Purpose | Key Measures |
|------------------|---------|--------------|
| `security_events` | Audit event metrics | total_events, failed_events, success_rate, unique_users, high_risk_events |
| `governance_analytics` | Data lineage metrics | read_events, write_events, active_table_count, unique_data_consumers |

### Table-Valued Functions (10 TVFs)

| Function Name | Purpose | When to Use |
|---------------|---------|-------------|
| `get_user_activity_summary` | User activity with risk scoring | "user activity" |
| `get_sensitive_table_access` | Sensitive data access | "sensitive data access" |
| `get_failed_actions` | Failed operations | "failed actions" |
| `get_permission_changes` | Permission modifications | "permission changes" |
| `get_off_hours_activity` | Off-hours access | "off-hours activity" |
| `get_security_events_timeline` | Chronological timeline | "security timeline" |
| `get_ip_address_analysis` | IP address patterns | "IP analysis" |
| `get_table_access_audit` | Table access trail | "table access" |
| `get_user_activity_patterns` | Temporal patterns | "activity patterns" |
| `get_service_account_audit` | Service account activity | "service accounts" |

### ML Prediction Tables 🤖 (4 Models)

| Table Name | Purpose | Model | Key Columns |
|---|---|---|---|
| `access_anomaly_predictions` | Unusual access pattern detection | Security Threat Detector | `threat_score`, `is_threat`, `threat_indicators`, `user_identity` |
| `user_risk_scores` | User risk assessment (0-100) | Compliance Risk Classifier | `risk_score`, `risk_level`, `risk_category`, `risk_factors` |
| `access_classifications` | Normal vs suspicious access classification | Access Pattern Analyzer | `pattern_class`, `probability`, `pattern_description` |
| `off_hours_baseline_predictions` | Expected off-hours activity baseline | Off-Hours Baseline Predictor | `expected_activity_level`, `baseline_deviation`, `alert_threshold` |

**Training Source:** `src/ml/security/` | **Inference:** `src/ml/inference/batch_inference_all_models.py`

### Lakehouse Monitoring Tables 📊

| Table Name | Purpose |
|------------|---------|
| `fact_audit_logs_profile_metrics` | Custom security metrics (sensitive_access_rate, failure_rate, off_hours_rate) |
| `fact_audit_logs_drift_metrics` | Security drift (event_volume_drift, sensitive_action_drift) |

#### ⚠️ CRITICAL: Custom Metrics Query Patterns

**Always include these filters when querying Lakehouse Monitoring tables:**

```sql
-- ✅ CORRECT: Get security metrics
SELECT 
  window.start AS window_start,
  total_events,
  sensitive_access_rate,
  failure_rate,
  off_hours_rate
FROM ${catalog}.${gold_schema}.fact_audit_logs_profile_metrics
WHERE column_name = ':table'     -- REQUIRED: Table-level custom metrics
  AND log_type = 'INPUT'         -- REQUIRED: Input data statistics
  AND slice_key IS NULL          -- For overall metrics
ORDER BY window.start DESC;

-- ✅ CORRECT: Get events by user (sliced)
SELECT 
  slice_value AS user_identity,
  SUM(total_events) AS event_count
FROM ${catalog}.${gold_schema}.fact_audit_logs_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'user_identity_email'
GROUP BY slice_value
ORDER BY event_count DESC;

-- ✅ CORRECT: Get security drift
SELECT 
  window.start AS window_start,
  event_volume_drift,
  sensitive_action_drift
FROM ${catalog}.${gold_schema}.fact_audit_logs_drift_metrics
WHERE drift_type = 'CONSECUTIVE'
  AND column_name = ':table'
ORDER BY window.start DESC;
```

#### Available Slicing Dimensions (Security Monitor)

| Slice Key | Use Case |
|-----------|----------|
| `workspace_id` | Events by workspace |
| `service_name` | Events by service |
| `audit_level` | By audit level |
| `action_name` | By action type |
| `user_identity_email` | Events by user |

### Dimension Tables (3 Tables)

**Sources:** `gold_layer_design/yaml/shared/`

| Table Name | Purpose | Key Columns | YAML Source |
|---|---|---|---|
| `dim_workspace` | Workspace reference | `workspace_id`, `workspace_name`, `region`, `cloud_provider` | shared/dim_workspace.yaml |
| `dim_user` | User information for access analysis | `user_id`, `user_name`, `email`, `department_tag`, `is_service_principal` | shared/dim_user.yaml |
| `dim_date` | Date dimension for time analysis | `date_key`, `day_of_week`, `month`, `quarter`, `year`, `is_weekend`, `is_business_hours` | shared/dim_date.yaml |

### Fact Tables (from gold_layer_design/yaml/security/, governance/)

| Table Name | Purpose | Grain | YAML Source |
|------------|---------|-------|-------------|
| `fact_audit_logs` | Audit event log | Per event | security/fact_audit_logs.yaml |
| `fact_table_lineage` | Data lineage | Per access event | governance/fact_table_lineage.yaml |
| `fact_assistant_events` | AI assistant interactions | Per assistant call | security/fact_assistant_events.yaml |
| `fact_clean_room_events` | Clean room operations | Per operation | security/fact_clean_room_events.yaml |
| `fact_inbound_network` | Inbound network traffic | Per connection | security/fact_inbound_network.yaml |
| `fact_outbound_network` | Outbound network traffic | Per connection | security/fact_outbound_network.yaml |

### Data Model Relationships 🔗

**Foreign Key Constraints** (extracted from `gold_layer_design/yaml/security/`)

| Fact Table | → | Dimension Table | Join Keys | Join Type |
|------------|---|-----------------|-----------|-----------|
| `fact_audit_logs` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_audit_logs` | → | `dim_user` | `user_identity_email` = `email` | LEFT |
| `fact_table_lineage` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_assistant_events` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_clean_room_events` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_inbound_network` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_outbound_network` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |

**Join Patterns:**
- **Workspace scope:** All security facts join to `dim_workspace` on `workspace_id`
- **User identity:** `fact_audit_logs` joins to `dim_user` on email for user details

---

## ████ SECTION E: ASSET SELECTION FRAMEWORK ████

### Semantic Layer Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    ASSET SELECTION DECISION TREE                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  USER QUERY PATTERN                → USE THIS ASSET             │
│  ─────────────────────────────────────────────────────────────  │
│  "Total audit events today"        → Metric View (security_events)│
│  "Failed events count"             → Metric View (security_events)│
│  ─────────────────────────────────────────────────────────────  │
│  "Is auth failure increasing?"     → Custom Metrics (_drift_metrics)│
│  "Security event trend"            → Custom Metrics (_profile_metrics)│
│  ─────────────────────────────────────────────────────────────  │
│  "Who accessed sensitive data?"    → TVF (get_sensitive_table_access)│
│  "Failed actions today"            → TVF (get_failed_actions)    │
│  "User activity for X"             → TVF (get_user_activity_summary)│
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Asset Selection Rules

| Query Intent | Asset Type | Example |
|--------------|-----------|---------|
| **Total events count** | Metric View | "Audit events today" → `security_events` |
| **Auth failure trend** | Custom Metrics | "Is failure increasing?" → `_drift_metrics` |
| **User activity list** | TVF | "Activity for user X" → `get_user_activity_summary` |
| **Anomaly detection** | ML Tables | "Security anomalies" → `access_anomaly_predictions` |
| **Risk assessment** | TVF/ML | "User risk scores" → `get_user_risk_scores` |

### Priority Order

1. **If user asks for a LIST** → TVF
2. **If user asks about TREND** → Custom Metrics
3. **If user asks for CURRENT VALUE** → Metric View
4. **If user asks for ANOMALY/RISK** → ML Tables

---

## ████ SECTION F: GENERAL INSTRUCTIONS (≤20 Lines) ████

```
You are a Databricks security and compliance analyst. Follow these rules:

1. **Asset Selection:** Use Metric View for current state, TVFs for lists, Custom Metrics for trends
2. **Primary Source:** Use security_events metric view for dashboard KPIs
3. **TVFs for Lists:** Use TVFs for user-specific or "who accessed" queries
4. **Trends:** For "is failure rate increasing?" check _drift_metrics tables
5. **Date Default:** If no date specified, default to last 24 hours
6. **User Types:** HUMAN_USER, SERVICE_PRINCIPAL, SYSTEM
7. **Risk Levels:** LOW (0-25), MEDIUM (26-50), HIGH (51-75), CRITICAL (76-100)
8. **Sorting:** Sort by risk_score DESC for security queries
9. **Limits:** Top 20 for activity lists
10. **Synonyms:** user=identity=principal, access=event=action
11. **ML Anomaly:** For "anomalies" → query access_anomaly_predictions
12. **Risk Score:** For "risk score" → query user_risk_scores
13. **Custom Metrics:** Always include required filters (column_name=':table', log_type='INPUT')
14. **Context:** Explain READ vs WRITE vs DDL actions
15. **Compliance:** Never expose PII in responses
16. **Performance:** Never scan Bronze/Silver tables
```

---

## ████ SECTION G: TABLE-VALUED FUNCTIONS ████

### TVF Quick Reference

| Function Name | Signature | Purpose | When to Use |
|---------------|-----------|---------|-------------|
| `get_user_activity_summary` | `(user_email STRING, start_date STRING, end_date STRING)` | User activity | "activity for user X" |
| `get_sensitive_table_access` | `(start_date STRING, end_date STRING)` | PII table access | "sensitive data access" |
| `get_failed_actions` | `(start_date STRING, end_date STRING)` | Failed ops | "failed actions" |
| `get_permission_changes` | `(start_date STRING, end_date STRING)` | Perm changes | "permission changes" |
| `get_off_hours_activity` | `(start_date STRING, end_date STRING)` | Off-hours | "off-hours activity" |

### TVF Details

#### get_user_activity_summary
- **Signature:** `get_user_activity_summary(user_email STRING, start_date STRING, end_date STRING)`
- **Returns:** user_identity, total_events, read_events, write_events, failed_events, risk_score
- **Use When:** User asks for "activity for john@company.com"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_user_activity_summary('john@company.com', '2024-12-01', '2024-12-31')`

#### get_sensitive_table_access
- **Signature:** `get_sensitive_table_access(start_date STRING, end_date STRING)`
- **Returns:** table_name, user_identity, access_count, access_type, last_access
- **Use When:** User asks for "who accessed sensitive data"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_sensitive_table_access('2024-12-01', '2024-12-31')`

#### get_off_hours_activity
- **Signature:** `get_off_hours_activity(start_date STRING, end_date STRING)`
- **Returns:** user_identity, event_date, event_hour, event_count, action_types
- **Use When:** User asks for "off-hours access" or "after-hours activity"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_off_hours_activity('2024-12-01', '2024-12-31')`

---

## ████ SECTION G: ML MODEL INTEGRATION (4 Models) ████

### Security ML Models Quick Reference

| ML Model | Prediction Table | Key Columns | Use When |
|----------|-----------------|-------------|----------|
| `security_threat_detector` | `access_anomaly_predictions` | `threat_score`, `is_threat` | "Detect threats" |
| `access_pattern_analyzer` | `access_classifications` | `pattern_class`, `probability` | "Classify access" |
| `compliance_risk_classifier` | `user_risk_scores` | `risk_level` (1-5) | "User risk score" |
| `permission_recommender` | — | `recommended_action` | "Permission changes" |

### ML Model Usage Patterns

#### security_threat_detector (Threat Detection)
- **Question Triggers:** "threat", "anomaly", "suspicious", "unusual access", "security risk"
- **Query Pattern:**
```sql
SELECT user_identity, event_date, threat_score, is_threat, threat_indicators
FROM ${catalog}.${gold_schema}.access_anomaly_predictions
WHERE prediction_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND is_threat = TRUE
ORDER BY threat_score ASC;
```
- **Interpretation:** `is_threat = TRUE` or `threat_score < -0.5` = Security concern

#### compliance_risk_classifier (User Risk Scores)
- **Question Triggers:** "risk score", "risky users", "compliance risk", "high risk"
- **Query Pattern:**
```sql
SELECT user_identity, risk_level, risk_category, risk_factors
FROM ${catalog}.${gold_schema}.user_risk_scores
WHERE risk_level >= 4
ORDER BY risk_level DESC, last_activity DESC;
```
- **Interpretation:** `risk_level >= 4` = High risk, requires attention

#### access_pattern_analyzer (Access Classification)
- **Question Triggers:** "access pattern", "behavior", "classify user", "normal access"
- **Query Pattern:**
```sql
SELECT user_identity, pattern_class, probability, pattern_description
FROM ${catalog}.${gold_schema}.access_classifications
WHERE pattern_class != 'NORMAL'
ORDER BY probability DESC;
```

### ML vs Other Methods Decision Tree

```
USER QUESTION                           → USE THIS
────────────────────────────────────────────────────
"Who are the risky users?"              → ML: user_risk_scores
"Any security threats?"                 → ML: access_anomaly_predictions
"Classify access patterns"              → ML: access_classifications
"Permission recommendations"            → ML: permission_recommender
────────────────────────────────────────────────────
"How many security events?"             → Metric View: security_events
"Is event volume increasing?"           → Custom Metrics: _drift_metrics
"Show failed access attempts"           → TVF: get_failed_access_attempts
```

---

## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████

### Question 1: "Who are the most active users this week?"
**Expected SQL:**
```sql
SELECT 
  user_identity,
  MEASURE(total_events) as event_count
FROM ${catalog}.${gold_schema}.security_events
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY user_identity
ORDER BY event_count DESC
LIMIT 10;
```
**Expected Result:** Top 10 users by event count

---

### Question 2: "Show me failed access attempts today"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_failed_actions(
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY event_timestamp DESC;
```
**Expected Result:** Table of failed actions

---

### Question 3: "Who accessed sensitive data this week?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_sensitive_table_access(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY access_count DESC;
```
**Expected Result:** Users who accessed PII/sensitive tables

---

### Question 4: "Show me off-hours activity"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_off_hours_activity(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY event_count DESC
LIMIT 20;
```
**Expected Result:** Activity outside business hours

---

### Question 5: "What permission changes happened today?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_permission_changes(
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY event_timestamp DESC;
```
**Expected Result:** Permission modification events

---

### Question 6: "Are there any security anomalies?"
**Expected SQL:**
```sql
SELECT 
  user_identity,
  anomaly_score,
  is_anomaly,
  reason
FROM ${catalog}.${gold_schema}.access_anomaly_predictions
WHERE prediction_date = CURRENT_DATE()
  AND is_anomaly = TRUE
ORDER BY anomaly_score DESC;
```
**Expected Result:** Detected anomalous access patterns

---

### Question 7: "What's the risk score for users?"
**Expected SQL:**
```sql
SELECT 
  user_id,
  risk_score,
  risk_factors,
  CASE 
    WHEN risk_score >= 76 THEN 'CRITICAL'
    WHEN risk_score >= 51 THEN 'HIGH'
    WHEN risk_score >= 26 THEN 'MEDIUM'
    ELSE 'LOW'
  END as risk_level
FROM ${catalog}.${gold_schema}.user_risk_scores
ORDER BY risk_score DESC
LIMIT 20;
```
**Expected Result:** Users with risk classifications

---

### Question 8: "Which service accounts are most active?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_service_account_audit(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY event_count DESC
LIMIT 20;
```
**Expected Result:** Service principal activity summary

---

### Question 9: "Show me security event trends"
**Expected SQL:**
```sql
SELECT 
  event_date,
  MEASURE(total_events) as total_events,
  MEASURE(failed_events) as failed_events,
  MEASURE(high_risk_events) as high_risk_events
FROM ${catalog}.${gold_schema}.security_events
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY event_date
ORDER BY event_date;
```
**Expected Result:** Daily security event trends

---

### Question 10: "Is there unusual activity volume?"
**Expected SQL:**
```sql
SELECT 
  window_start,
  event_volume_drift,
  sensitive_action_drift
FROM ${catalog}.${gold_schema}.fact_audit_logs_drift_metrics
WHERE column_name = ':table'
  AND (ABS(event_volume_drift) > 50 OR ABS(sensitive_action_drift) > 20)
ORDER BY window_start DESC
LIMIT 10;
```
**Expected Result:** Significant security drift alerts

---

### Question 11: "Show me IP address analysis"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_ip_address_analysis(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY event_count DESC
LIMIT 20;
```
**Expected Result:** Activity by IP address

---

### Question 12: "Who has the most DDL operations?"
**Expected SQL:**
```sql
SELECT 
  user_identity,
  COUNT(*) as ddl_count
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE action_name LIKE '%DDL%'
  AND event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY user_identity
ORDER BY ddl_count DESC
LIMIT 20;
```
**Expected Result:** Users with most DDL operations

---

### Question 13: "Show me data lineage for sensitive tables"
**Expected SQL:**
```sql
SELECT 
  source_table,
  target_table,
  user_identity,
  event_count
FROM ${catalog}.${gold_schema}.fact_table_lineage
WHERE source_table LIKE '%pii%' OR target_table LIKE '%pii%'
  AND event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY event_count DESC
LIMIT 20;
```
**Expected Result:** Lineage for PII tables

---

### Question 14: "What is the user activity pattern?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_user_activity_patterns(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 30 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY event_count DESC
LIMIT 20;
```
**Expected Result:** Temporal patterns by user

---

### Question 15: "Show me clean room operations"
**Expected SQL:**
```sql
SELECT 
  operation_type,
  user_identity,
  clean_room_name,
  event_timestamp
FROM ${catalog}.${gold_schema}.fact_clean_room_events
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY event_timestamp DESC
LIMIT 20;
```
**Expected Result:** Recent clean room activity

---

### Question 16: "What are the access classification patterns?"
**Expected SQL:**
```sql
SELECT 
  pattern_class,
  COUNT(*) as pattern_count,
  AVG(probability) as avg_confidence
FROM ${catalog}.${gold_schema}.access_classifications
WHERE pattern_class != 'NORMAL'
GROUP BY pattern_class
ORDER BY pattern_count DESC;
```
**Expected Result:** Non-normal access patterns

---

### Question 17: "Show me outbound network traffic"
**Expected SQL:**
```sql
SELECT 
  destination_host,
  COUNT(*) as connection_count,
  SUM(bytes_sent) as total_bytes
FROM ${catalog}.${gold_schema}.fact_outbound_network
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY destination_host
ORDER BY total_bytes DESC
LIMIT 20;
```
**Expected Result:** Outbound network destinations

---

### Question 18: "Who accessed AI assistant features?"
**Expected SQL:**
```sql
SELECT 
  user_identity,
  assistant_type,
  COUNT(*) as interaction_count
FROM ${catalog}.${gold_schema}.fact_assistant_events
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY user_identity, assistant_type
ORDER BY interaction_count DESC
LIMIT 20;
```
**Expected Result:** AI assistant usage by user

---

### Question 19: "What is the off-hours baseline deviation?"
**Expected SQL:**
```sql
SELECT 
  user_identity,
  expected_activity_level,
  actual_activity_level,
  baseline_deviation
FROM ${catalog}.${gold_schema}.off_hours_baseline_predictions
WHERE baseline_deviation > alert_threshold
ORDER BY baseline_deviation DESC
LIMIT 20;
```
**Expected Result:** Users exceeding off-hours baseline

---

### Question 20: "Show me table access audit trail"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_table_access_audit(
  'catalog.schema.table_name',
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY access_time DESC
LIMIT 50;
```
**Expected Result:** Complete access history for a table

---

### 🔬 DEEP RESEARCH QUESTIONS (Complex Multi-Source Analysis)

### Question 21: "Which users show the highest risk score deviation from their historical baseline, and what specific access patterns are contributing to elevated risk?"
**Deep Research Complexity:** Combines current risk scoring, historical baseline analysis, access pattern classification, and specific risk factor decomposition.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Get current risk scores
WITH current_risk AS (
  SELECT 
    user_identity,
    risk_score,
    risk_level,
    risk_category,
    risk_factors
  FROM ${catalog}.${gold_schema}.user_risk_scores
  WHERE score_date = CURRENT_DATE()
),
-- Step 2: Calculate historical baseline risk
historical_baseline AS (
  SELECT 
    user_identity,
    AVG(risk_score) as baseline_risk_score,
    STDDEV(risk_score) as risk_volatility
  FROM ${catalog}.${gold_schema}.user_risk_scores
  WHERE score_date >= CURRENT_DATE() - INTERVAL 90 DAYS
    AND score_date < CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY user_identity
),
-- Step 3: Get access pattern classifications
access_patterns AS (
  SELECT 
    user_identity,
    pattern_class,
    probability as pattern_confidence,
    pattern_description
  FROM ${catalog}.${gold_schema}.access_classifications
  WHERE classification_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND pattern_class != 'NORMAL'
),
-- Step 4: Get recent activity summary
recent_activity AS (
  SELECT 
    user_identity,
    COUNT(*) as event_count_7d,
    SUM(CASE WHEN action_name LIKE '%WRITE%' OR action_name LIKE '%DELETE%' THEN 1 ELSE 0 END) as write_operations,
    SUM(CASE WHEN response_code != '200' THEN 1 ELSE 0 END) as failed_attempts,
    COUNT(DISTINCT source_ip) as unique_ips
  FROM ${catalog}.${gold_schema}.fact_audit_logs
  WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY user_identity
)
SELECT 
  cr.user_identity,
  cr.risk_score as current_risk_score,
  ROUND(hb.baseline_risk_score, 1) as baseline_risk_score,
  cr.risk_score - hb.baseline_risk_score as risk_deviation,
  ROUND((cr.risk_score - hb.baseline_risk_score) / NULLIF(hb.risk_volatility, 0), 2) as deviation_z_score,
  cr.risk_category,
  cr.risk_factors,
  ap.pattern_class as detected_anomalous_pattern,
  ap.pattern_description,
  ra.event_count_7d,
  ra.write_operations,
  ra.failed_attempts,
  ra.unique_ips,
  CASE 
    WHEN (cr.risk_score - hb.baseline_risk_score) > 30 AND ap.pattern_class IS NOT NULL 
      THEN '🔴 CRITICAL: Major risk spike with anomalous behavior - IMMEDIATE INVESTIGATION'
    WHEN (cr.risk_score - hb.baseline_risk_score) > 20 
      THEN '🟠 HIGH: Significant risk increase - REVIEW WITHIN 24H'
    WHEN (cr.risk_score - hb.baseline_risk_score) > 10 OR ap.pattern_class IS NOT NULL
      THEN '🟡 ELEVATED: Notable change - MONITOR CLOSELY'
    ELSE '🟢 NORMAL: Within expected variance'
  END as investigation_priority
FROM current_risk cr
LEFT JOIN historical_baseline hb ON cr.user_identity = hb.user_identity
LEFT JOIN access_patterns ap ON cr.user_identity = ap.user_identity
LEFT JOIN recent_activity ra ON cr.user_identity = ra.user_identity
WHERE cr.risk_score > hb.baseline_risk_score + 10  -- Only show users with elevated risk
ORDER BY (cr.risk_score - COALESCE(hb.baseline_risk_score, 0)) DESC
LIMIT 15;
```
**Expected Result:** Users with risk deviations from baseline, specific anomalous patterns detected, and prioritized investigation recommendations.

---

### Question 22: "What is the correlation between off-hours activity spikes and failed access attempts, and which accounts should be prioritized for security review based on combined risk signals?"
**Deep Research Complexity:** Combines off-hours analysis, failure correlation, baseline deviation, threat detection, and multi-signal risk aggregation.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Identify off-hours activity spikes
WITH off_hours_activity AS (
  SELECT 
    user_identity,
    COUNT(*) as off_hours_events,
    SUM(CASE WHEN response_code != '200' THEN 1 ELSE 0 END) as off_hours_failures
  FROM ${catalog}.${gold_schema}.fact_audit_logs
  WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND (HOUR(event_timestamp) < 6 OR HOUR(event_timestamp) > 22 
         OR DAYOFWEEK(event_timestamp) IN (1, 7))  -- Weekends or outside 6AM-10PM
  GROUP BY user_identity
),
-- Step 2: Get off-hours baseline predictions
baseline_comparison AS (
  SELECT 
    user_identity,
    expected_activity_level,
    baseline_deviation,
    alert_threshold
  FROM ${catalog}.${gold_schema}.off_hours_baseline_predictions
),
-- Step 3: Get all failed access attempts
failure_analysis AS (
  SELECT 
    user_identity,
    COUNT(*) as total_failures,
    COUNT(DISTINCT action_name) as unique_failed_actions,
    COUNT(DISTINCT source_ip) as failure_source_ips,
    MAX(event_timestamp) as last_failure_time
  FROM ${catalog}.${gold_schema}.fact_audit_logs
  WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND response_code != '200'
  GROUP BY user_identity
),
-- Step 4: Get threat detection signals
threat_signals AS (
  SELECT 
    user_identity,
    threat_score,
    is_threat,
    threat_indicators
  FROM ${catalog}.${gold_schema}.access_anomaly_predictions
  WHERE is_threat = TRUE
),
-- Step 5: Aggregate combined risk score
combined_risk AS (
  SELECT 
    COALESCE(o.user_identity, f.user_identity, t.user_identity) as user_identity,
    COALESCE(o.off_hours_events, 0) as off_hours_events,
    COALESCE(o.off_hours_failures, 0) as off_hours_failures,
    COALESCE(b.baseline_deviation, 0) as baseline_deviation,
    COALESCE(f.total_failures, 0) as total_failures,
    COALESCE(f.unique_failed_actions, 0) as unique_failed_actions,
    t.threat_score,
    t.threat_indicators,
    -- Calculate correlation: high off-hours + high failures = high correlation
    CASE 
      WHEN o.off_hours_events > 50 AND f.total_failures > 10 THEN 'STRONG'
      WHEN o.off_hours_events > 20 OR f.total_failures > 5 THEN 'MODERATE'
      ELSE 'WEAK'
    END as off_hours_failure_correlation,
    -- Composite risk score (0-100)
    LEAST(100, 
      COALESCE(o.off_hours_failures, 0) * 2 + 
      COALESCE(b.baseline_deviation, 0) * 0.5 + 
      COALESCE(f.total_failures, 0) * 1.5 +
      CASE WHEN t.is_threat THEN 30 ELSE 0 END
    ) as composite_risk_score
  FROM off_hours_activity o
  FULL OUTER JOIN failure_analysis f ON o.user_identity = f.user_identity
  FULL OUTER JOIN baseline_comparison b ON o.user_identity = b.user_identity
  LEFT JOIN threat_signals t ON o.user_identity = t.user_identity
)
SELECT 
  user_identity,
  off_hours_events,
  off_hours_failures,
  ROUND(baseline_deviation, 1) as off_hours_baseline_deviation,
  total_failures,
  unique_failed_actions,
  off_hours_failure_correlation,
  ROUND(threat_score, 2) as ml_threat_score,
  threat_indicators,
  ROUND(composite_risk_score, 0) as composite_risk_score,
  CASE 
    WHEN composite_risk_score >= 80 THEN '🔴 CRITICAL: Multiple high-risk signals - IMMEDIATE SECURITY REVIEW'
    WHEN composite_risk_score >= 60 THEN '🟠 HIGH: Strong correlation of off-hours activity and failures - REVIEW WITHIN 4H'
    WHEN composite_risk_score >= 40 THEN '🟡 MEDIUM: Elevated activity patterns - REVIEW WITHIN 24H'
    ELSE '🟢 LOW: Normal activity levels'
  END as security_review_priority,
  CASE 
    WHEN off_hours_failure_correlation = 'STRONG' AND threat_indicators IS NOT NULL 
      THEN 'Potential compromised account: ' || threat_indicators
    WHEN off_hours_failure_correlation = 'STRONG' 
      THEN 'Suspicious automation or credential stuffing attempt'
    WHEN baseline_deviation > 50 
      THEN 'Significant behavior change from baseline'
    ELSE 'Monitor for continued patterns'
  END as investigation_focus
FROM combined_risk
WHERE composite_risk_score >= 30
ORDER BY composite_risk_score DESC
LIMIT 15;
```
**Expected Result:** Accounts with correlated off-hours and failure signals, composite risk scores from multiple ML and heuristic signals, and prioritized security review recommendations.

---

### Question 23: "What's the comprehensive security posture assessment for each workspace, including permission gaps, audit coverage, sensitive data exposure, and compliance risk indicators?"
**Deep Research Complexity:** Combines permission analysis, audit log coverage, sensitive table access patterns, and compliance indicators to produce workspace-level security posture scores.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Analyze permission configurations per workspace
WITH permission_analysis AS (
  SELECT 
    workspace_id,
    COUNT(DISTINCT user_identity) as total_users,
    COUNT(CASE WHEN action_name LIKE '%ADMIN%' THEN 1 END) as admin_actions,
    COUNT(DISTINCT CASE WHEN action_name LIKE '%GRANT%' OR action_name LIKE '%REVOKE%' THEN user_identity END) as users_with_grant_perms,
    COUNT(CASE WHEN action_name = 'permissionAssignments' THEN 1 END) as permission_changes_30d
  FROM ${catalog}.${gold_schema}.fact_audit_logs
  WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY workspace_id
),
-- Step 2: Analyze sensitive data access patterns
sensitive_access AS (
  SELECT 
    workspace_id,
    COUNT(*) as sensitive_accesses,
    COUNT(DISTINCT user_identity) as users_accessing_sensitive,
    COUNT(DISTINCT table_name) as sensitive_tables_accessed,
    SUM(CASE WHEN response_code != '200' THEN 1 ELSE 0 END) as failed_sensitive_access
  FROM ${catalog}.${gold_schema}.fact_audit_logs
  WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND (table_name LIKE '%pii%' OR table_name LIKE '%sensitive%' OR action_name LIKE '%READ%')
    AND service_name IN ('unityCatalog', 'sqlPermissions')
  GROUP BY workspace_id
),
-- Step 3: Get audit log coverage metrics
audit_coverage AS (
  SELECT 
    workspace_id,
    COUNT(DISTINCT service_name) as services_audited,
    COUNT(DISTINCT action_name) as action_types_logged,
    COUNT(*) as total_events,
    COUNT(DISTINCT DATE_TRUNC('day', event_timestamp)) as days_with_logs
  FROM ${catalog}.${gold_schema}.fact_audit_logs
  WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY workspace_id
),
-- Step 4: Get ML security risk indicators
ml_risk_indicators AS (
  SELECT 
    workspace_id,
    COUNT(*) as threat_detections,
    AVG(threat_score) as avg_threat_score,
    MAX(threat_score) as max_threat_score
  FROM ${catalog}.${gold_schema}.access_anomaly_predictions
  WHERE prediction_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND is_threat = TRUE
  GROUP BY workspace_id
),
-- Step 5: Calculate security posture score
security_posture AS (
  SELECT 
    w.workspace_id,
    w.workspace_name,
    -- Permission risk (0-25 points, lower is better)
    LEAST(25, (COALESCE(p.users_with_grant_perms, 0) * 5 + COALESCE(p.permission_changes_30d, 0) * 0.5)) as permission_risk_score,
    -- Sensitive access risk (0-25 points)
    LEAST(25, (COALESCE(s.failed_sensitive_access, 0) * 3 + COALESCE(s.users_accessing_sensitive, 0) * 2)) as sensitive_access_risk,
    -- Audit coverage bonus (0-25 points, higher is better)
    LEAST(25, (COALESCE(a.services_audited, 0) * 2 + CASE WHEN a.days_with_logs >= 30 THEN 10 ELSE 0 END)) as audit_coverage_score,
    -- Threat detection penalty (0-25 points)
    LEAST(25, (COALESCE(m.threat_detections, 0) * 5 + COALESCE(m.max_threat_score, 0) * 10)) as threat_penalty_score
  FROM ${catalog}.${gold_schema}.dim_workspace w
  LEFT JOIN permission_analysis p ON w.workspace_id = p.workspace_id
  LEFT JOIN sensitive_access s ON w.workspace_id = s.workspace_id
  LEFT JOIN audit_coverage a ON w.workspace_id = a.workspace_id
  LEFT JOIN ml_risk_indicators m ON w.workspace_id = m.workspace_id
)
SELECT 
  workspace_name,
  permission_risk_score,
  sensitive_access_risk,
  audit_coverage_score,
  threat_penalty_score,
  -- Calculate overall posture score (100 = perfect, 0 = worst)
  100 - (permission_risk_score + sensitive_access_risk + threat_penalty_score) + audit_coverage_score as security_posture_score,
  CASE 
    WHEN 100 - (permission_risk_score + sensitive_access_risk + threat_penalty_score) + audit_coverage_score >= 80 THEN '🟢 STRONG POSTURE'
    WHEN 100 - (permission_risk_score + sensitive_access_risk + threat_penalty_score) + audit_coverage_score >= 60 THEN '🟡 MODERATE POSTURE'
    WHEN 100 - (permission_risk_score + sensitive_access_risk + threat_penalty_score) + audit_coverage_score >= 40 THEN '🟠 WEAK POSTURE'
    ELSE '🔴 CRITICAL POSTURE'
  END as posture_classification,
  CASE 
    WHEN permission_risk_score > 15 THEN 'PRIORITY: Review permission assignments and reduce admin access'
    WHEN sensitive_access_risk > 15 THEN 'PRIORITY: Review sensitive data access policies'
    WHEN threat_penalty_score > 15 THEN 'PRIORITY: Investigate detected threats immediately'
    WHEN audit_coverage_score < 15 THEN 'PRIORITY: Enable comprehensive audit logging'
    ELSE 'MAINTAIN: Continue monitoring and periodic reviews'
  END as top_recommendation
FROM security_posture
ORDER BY security_posture_score ASC
LIMIT 15;
```
**Expected Result:** Workspace security posture scores with component breakdown, classification, and prioritized recommendations.

---

### Question 24: "What sensitive data access patterns have changed most significantly in the past 30 days, and which changes indicate potential data exfiltration or unauthorized access expansion?"
**Deep Research Complexity:** Analyzes sensitive data access trends, detects significant pattern changes, correlates with user behavior anomalies, and flags potential exfiltration indicators.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Establish 60-day baseline for sensitive data access
WITH baseline_patterns AS (
  SELECT 
    user_identity,
    table_name,
    COUNT(*) as baseline_access_count,
    COUNT(DISTINCT DATE_TRUNC('day', event_timestamp)) as baseline_active_days,
    AVG(HOUR(event_timestamp)) as typical_access_hour,
    STDDEV(HOUR(event_timestamp)) as access_hour_variance
  FROM ${catalog}.${gold_schema}.fact_audit_logs
  WHERE event_date BETWEEN CURRENT_DATE() - INTERVAL 60 DAYS AND CURRENT_DATE() - INTERVAL 30 DAYS
    AND (table_name LIKE '%pii%' OR table_name LIKE '%sensitive%' OR table_name LIKE '%confidential%')
    AND action_name LIKE '%READ%'
  GROUP BY user_identity, table_name
),
-- Step 2: Calculate recent patterns (last 30 days)
recent_patterns AS (
  SELECT 
    user_identity,
    table_name,
    COUNT(*) as recent_access_count,
    COUNT(DISTINCT DATE_TRUNC('day', event_timestamp)) as recent_active_days,
    AVG(HOUR(event_timestamp)) as recent_access_hour,
    SUM(CASE WHEN HOUR(event_timestamp) < 6 OR HOUR(event_timestamp) > 22 THEN 1 ELSE 0 END) as off_hours_accesses,
    SUM(total_bytes_read) / 1e9 as total_data_read_gb
  FROM ${catalog}.${gold_schema}.fact_audit_logs
  WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND (table_name LIKE '%pii%' OR table_name LIKE '%sensitive%' OR table_name LIKE '%confidential%')
    AND action_name LIKE '%READ%'
  GROUP BY user_identity, table_name
),
-- Step 3: Identify new sensitive table accesses
new_accesses AS (
  SELECT 
    r.user_identity,
    r.table_name,
    'NEW_ACCESS' as change_type,
    r.recent_access_count as access_count,
    r.total_data_read_gb
  FROM recent_patterns r
  LEFT JOIN baseline_patterns b ON r.user_identity = b.user_identity AND r.table_name = b.table_name
  WHERE b.user_identity IS NULL  -- No baseline access
),
-- Step 4: Identify significant access increases
access_increases AS (
  SELECT 
    r.user_identity,
    r.table_name,
    'INCREASED_ACCESS' as change_type,
    r.recent_access_count as current_count,
    b.baseline_access_count as baseline_count,
    (r.recent_access_count - b.baseline_access_count) * 100.0 / NULLIF(b.baseline_access_count, 0) as increase_pct,
    r.total_data_read_gb
  FROM recent_patterns r
  JOIN baseline_patterns b ON r.user_identity = b.user_identity AND r.table_name = b.table_name
  WHERE r.recent_access_count > b.baseline_access_count * 2  -- More than 2x baseline
),
-- Step 5: Identify timing pattern changes
timing_changes AS (
  SELECT 
    r.user_identity,
    r.table_name,
    'TIMING_SHIFT' as change_type,
    ABS(r.recent_access_hour - b.typical_access_hour) as hour_shift,
    r.off_hours_accesses,
    r.total_data_read_gb
  FROM recent_patterns r
  JOIN baseline_patterns b ON r.user_identity = b.user_identity AND r.table_name = b.table_name
  WHERE ABS(r.recent_access_hour - b.typical_access_hour) > 4  -- >4 hour shift
    OR r.off_hours_accesses > 5
),
-- Step 6: Get ML anomaly flags
ml_anomalies AS (
  SELECT 
    user_identity,
    threat_score,
    threat_indicators
  FROM ${catalog}.${gold_schema}.access_anomaly_predictions
  WHERE prediction_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND is_threat = TRUE
)
SELECT 
  COALESCE(n.user_identity, i.user_identity, t.user_identity) as user_identity,
  COALESCE(n.table_name, i.table_name, t.table_name) as sensitive_table,
  COALESCE(n.change_type, i.change_type, t.change_type) as pattern_change,
  COALESCE(n.access_count, i.current_count, 0) as current_access_count,
  COALESCE(i.increase_pct, 0) as increase_percentage,
  COALESCE(t.off_hours_accesses, 0) as off_hours_count,
  COALESCE(n.total_data_read_gb, i.total_data_read_gb, t.total_data_read_gb, 0) as data_volume_gb,
  m.threat_score as ml_threat_score,
  m.threat_indicators,
  CASE 
    WHEN n.change_type = 'NEW_ACCESS' AND n.access_count > 50 THEN '🔴 HIGH RISK: New bulk access to sensitive data'
    WHEN i.increase_pct > 500 THEN '🔴 HIGH RISK: >5x access increase - potential exfiltration'
    WHEN t.off_hours_accesses > 10 THEN '🟠 MEDIUM RISK: Significant off-hours sensitive access'
    WHEN m.threat_score > 0.7 THEN '🟠 MEDIUM RISK: ML detected anomalous pattern'
    ELSE '🟡 LOW RISK: Pattern change warrants review'
  END as exfiltration_risk,
  CASE 
    WHEN n.change_type = 'NEW_ACCESS' THEN 'Verify user has legitimate business need for this data'
    WHEN i.increase_pct > 500 THEN 'Review recent queries and validate data access necessity'
    WHEN t.off_hours_accesses > 10 THEN 'Interview user about off-hours activity justification'
    ELSE 'Monitor and log for continued changes'
  END as investigation_action
FROM new_accesses n
FULL OUTER JOIN access_increases i ON n.user_identity = i.user_identity AND n.table_name = i.table_name
FULL OUTER JOIN timing_changes t ON COALESCE(n.user_identity, i.user_identity) = t.user_identity 
                                  AND COALESCE(n.table_name, i.table_name) = t.table_name
LEFT JOIN ml_anomalies m ON COALESCE(n.user_identity, i.user_identity, t.user_identity) = m.user_identity
ORDER BY 
  CASE 
    WHEN n.change_type = 'NEW_ACCESS' AND n.access_count > 50 THEN 1
    WHEN i.increase_pct > 500 THEN 2
    WHEN t.off_hours_accesses > 10 THEN 3
    ELSE 4
  END
LIMIT 20;
```
**Expected Result:** Significant changes in sensitive data access patterns with exfiltration risk assessment and investigation recommendations.

---

### Question 25: "What's the complete privilege escalation chain analysis - showing which users gained elevated access, through what mechanism, and whether the escalation was authorized?"
**Deep Research Complexity:** Traces permission changes through audit logs, identifies escalation chains, validates against approval workflows, and flags potentially unauthorized escalations.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Identify all permission grant events
WITH permission_grants AS (
  SELECT 
    event_timestamp,
    user_identity as granter,
    target_user as grantee,
    permission_type,
    resource_type,
    resource_name,
    workspace_id,
    action_name
  FROM (
    SELECT 
      event_timestamp,
      user_identity,
      COALESCE(
        GET_JSON_OBJECT(request_params, '$.user_name'),
        GET_JSON_OBJECT(request_params, '$.principal')
      ) as target_user,
      GET_JSON_OBJECT(request_params, '$.privilege') as permission_type,
      GET_JSON_OBJECT(request_params, '$.securable_type') as resource_type,
      GET_JSON_OBJECT(request_params, '$.securable_full_name') as resource_name,
      workspace_id,
      action_name
    FROM ${catalog}.${gold_schema}.fact_audit_logs
    WHERE action_name IN ('grantPermission', 'addMember', 'updatePermissions', 'permissionAssignments')
      AND event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
      AND response_code = '200'
  )
  WHERE target_user IS NOT NULL
),
-- Step 2: Identify admin/elevated permission types
elevated_permissions AS (
  SELECT *,
    CASE 
      WHEN permission_type IN ('ALL_PRIVILEGES', 'MANAGE', 'ADMIN') THEN 'ADMIN'
      WHEN permission_type IN ('CREATE', 'MODIFY', 'DELETE') THEN 'WRITE'
      WHEN permission_type IN ('SELECT', 'READ', 'USAGE') THEN 'READ'
      ELSE 'OTHER'
    END as permission_level,
    CASE 
      WHEN permission_type IN ('ALL_PRIVILEGES', 'MANAGE', 'ADMIN') THEN 3
      WHEN permission_type IN ('CREATE', 'MODIFY', 'DELETE') THEN 2
      ELSE 1
    END as privilege_score
  FROM permission_grants
),
-- Step 3: Track user privilege history (before vs after)
privilege_changes AS (
  SELECT 
    grantee,
    DATE_TRUNC('day', event_timestamp) as grant_date,
    permission_type,
    permission_level,
    privilege_score,
    granter,
    resource_name,
    LAG(permission_level, 1) OVER (PARTITION BY grantee ORDER BY event_timestamp) as prev_permission_level,
    LAG(privilege_score, 1) OVER (PARTITION BY grantee ORDER BY event_timestamp) as prev_privilege_score
  FROM elevated_permissions
),
-- Step 4: Identify escalation events
escalations AS (
  SELECT 
    grantee,
    grant_date,
    permission_type as new_permission,
    permission_level as new_level,
    COALESCE(prev_permission_level, 'NONE') as previous_level,
    privilege_score - COALESCE(prev_privilege_score, 0) as privilege_increase,
    granter,
    resource_name
  FROM privilege_changes
  WHERE privilege_score > COALESCE(prev_privilege_score, 0)  -- Escalation occurred
),
-- Step 5: Check for approval workflow (looking for corresponding approve events)
approval_check AS (
  SELECT 
    e.grantee,
    e.grant_date,
    e.new_permission,
    e.granter,
    CASE 
      WHEN a.approval_id IS NOT NULL THEN TRUE
      ELSE FALSE
    END as has_approval,
    a.approver
  FROM escalations e
  LEFT JOIN (
    SELECT 
      GET_JSON_OBJECT(request_params, '$.request_id') as approval_id,
      GET_JSON_OBJECT(request_params, '$.user_name') as grantee,
      user_identity as approver,
      DATE_TRUNC('day', event_timestamp) as approval_date
    FROM ${catalog}.${gold_schema}.fact_audit_logs
    WHERE action_name LIKE '%approve%'
      AND event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  ) a ON e.grantee = a.grantee AND e.grant_date = a.approval_date
),
-- Step 6: Get user risk context
user_risk AS (
  SELECT 
    user_identity,
    risk_level,
    threat_score
  FROM ${catalog}.${gold_schema}.user_risk_scores
  WHERE prediction_date = CURRENT_DATE()
)
SELECT 
  e.grantee as escalated_user,
  e.previous_level as from_level,
  e.new_level as to_level,
  e.new_permission,
  e.privilege_increase,
  e.granter as granted_by,
  e.resource_name,
  e.grant_date,
  ac.has_approval,
  ac.approver,
  COALESCE(ur.risk_level, 0) as user_risk_level,
  CASE 
    WHEN e.privilege_increase >= 2 AND NOT COALESCE(ac.has_approval, FALSE) THEN '🔴 CRITICAL: Major escalation without approval'
    WHEN e.new_level = 'ADMIN' AND NOT COALESCE(ac.has_approval, FALSE) THEN '🔴 CRITICAL: Admin access without approval'
    WHEN COALESCE(ur.risk_level, 0) >= 4 AND e.privilege_increase > 0 THEN '🟠 HIGH: Escalation for high-risk user'
    WHEN e.privilege_increase > 0 AND NOT COALESCE(ac.has_approval, FALSE) THEN '🟡 MEDIUM: Escalation without documented approval'
    ELSE '🟢 LOW: Authorized escalation'
  END as escalation_risk,
  CASE 
    WHEN e.privilege_increase >= 2 AND NOT COALESCE(ac.has_approval, FALSE) THEN 'IMMEDIATE: Revert access, investigate granter'
    WHEN e.new_level = 'ADMIN' THEN 'VERIFY: Confirm business justification for admin'
    WHEN COALESCE(ur.risk_level, 0) >= 4 THEN 'REVIEW: Assess if elevated access is appropriate for user risk profile'
    ELSE 'LOG: Document for audit trail'
  END as required_action
FROM escalations e
JOIN approval_check ac ON e.grantee = ac.grantee AND e.grant_date = ac.grant_date
LEFT JOIN user_risk ur ON e.grantee = ur.user_identity
WHERE e.privilege_increase > 0
ORDER BY 
  CASE 
    WHEN e.privilege_increase >= 2 AND NOT COALESCE(ac.has_approval, FALSE) THEN 1
    WHEN e.new_level = 'ADMIN' THEN 2
    ELSE 3
  END,
  e.grant_date DESC
LIMIT 20;
```
**Expected Result:** Privilege escalation chain analysis showing who gained elevated access, through whom, whether approved, and risk classification with required actions.

---

## ✅ DELIVERABLE CHECKLIST

| Section | Requirement | Status |
|---------|-------------|--------|
| **A. Space Name** | Exact name provided | ✅ |
| **B. Space Description** | 2-3 sentences | ✅ |
| **C. Sample Questions** | 15 questions | ✅ |
| **D. Data Assets** | All tables, views, TVFs, ML tables | ✅ |
| **E. General Instructions** | 18 lines (≤20) | ✅ |
| **F. TVFs** | 10 functions with signatures | ✅ |
| **H. Benchmark Questions** | 25 with SQL answers (incl. 5 Deep Research) | ✅ |

---

## Agent Domain Tag

**Agent Domain:** 🔒 **Security**

---

## References

### 📊 Semantic Layer Framework (Essential Reading)
- [**Metrics Inventory**](../../docs/reference/metrics-inventory.md) - **START HERE**: Complete inventory of 277 measurements across TVFs, Metric Views, and Custom Metrics
- [**Semantic Layer Rationalization**](../../docs/reference/semantic-layer-rationalization.md) - Design rationale: why overlaps are intentional and complementary
- [**Genie Asset Selection Guide**](../../docs/reference/genie-asset-selection-guide.md) - Quick decision tree for choosing correct asset type

### 📈 Lakehouse Monitoring Documentation
- [Monitor Catalog](../../docs/lakehouse-monitoring-design/04-monitor-catalog.md) - Complete metric definitions for Security Monitor
- [Genie Integration](../../docs/lakehouse-monitoring-design/05-genie-integration.md) - Critical query patterns and required filters
- [Custom Metrics Reference](../../docs/lakehouse-monitoring-design/03-custom-metrics.md) - 13 security-specific custom metrics

### 📁 Asset Inventories
- [TVF Inventory](../semantic/tvfs/TVF_INVENTORY.md) - 10 Security TVFs
- [Metric Views Inventory](../semantic/metric_views/METRIC_VIEWS_INVENTORY.md) - 2 Security Metric Views
- [ML Models Inventory](../ml/ML_MODELS_INVENTORY.md) - 4 Security ML Models

### 🚀 Deployment Guides
- [Genie Spaces Deployment Guide](../../docs/deployment/GENIE_SPACES_DEPLOYMENT_GUIDE.md) - Comprehensive setup and troubleshooting

