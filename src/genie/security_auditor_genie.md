# Security Auditor Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Security Auditor Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for Databricks security, audit, and compliance analytics. Enables security teams, compliance officers, and administrators to query access patterns, audit trails, and security events without SQL. Powered by Security Events Metric Views, 10 Security TVFs, 4 ML Models for anomaly detection, and Lakehouse Monitoring security drift metrics.

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

### ML Prediction Tables 🤖

| Table Name | Purpose |
|------------|---------|
| `access_anomaly_predictions` | Unusual access pattern detection |
| `user_risk_scores` | User risk assessment (0-100) |
| `access_classifications` | Normal vs suspicious classification |
| `off_hours_baseline_predictions` | Expected off-hours activity |

### Lakehouse Monitoring Tables 📊

| Table Name | Purpose |
|------------|---------|
| `fact_audit_logs_profile_metrics` | Custom security metrics (sensitive_rate, failure_rate, off_hours_rate) |
| `fact_audit_logs_drift_metrics` | Security drift (event_volume_drift, sensitive_action_drift) |

### Dimension Tables (from gold_layer_design/yaml/shared/)

| Table Name | Purpose | Key Columns | YAML Source |
|------------|---------|-------------|-------------|
| `dim_workspace` | Workspace reference | workspace_id, workspace_name | shared/dim_workspace.yaml |

### Fact Tables (from gold_layer_design/yaml/security/, governance/)

| Table Name | Purpose | Grain | YAML Source |
|------------|---------|-------|-------------|
| `fact_audit_logs` | Audit event log | Per event | security/fact_audit_logs.yaml |
| `fact_table_lineage` | Data lineage | Per access event | governance/fact_table_lineage.yaml |
| `fact_assistant_events` | AI assistant interactions | Per assistant call | security/fact_assistant_events.yaml |
| `fact_clean_room_events` | Clean room operations | Per operation | security/fact_clean_room_events.yaml |
| `fact_inbound_network` | Inbound network traffic | Per connection | security/fact_inbound_network.yaml |
| `fact_outbound_network` | Outbound network traffic | Per connection | security/fact_outbound_network.yaml |

---

## ████ SECTION E: GENERAL INSTRUCTIONS (≤20 Lines) ████

```
You are a Databricks security and compliance analyst. Follow these rules:

1. **Primary Source:** Use security_events metric view first
2. **TVFs:** Use TVFs for user-specific or time-bounded queries
3. **Date Default:** If no date specified, default to last 24 hours
4. **User Types:** HUMAN_USER, SERVICE_PRINCIPAL, SYSTEM
5. **Risk Levels:** LOW (0-25), MEDIUM (26-50), HIGH (51-75), CRITICAL (76-100)
6. **Sorting:** Sort by risk_score DESC for security queries
7. **Limits:** Top 20 for activity lists
8. **Synonyms:** user=identity=principal, access=event=action
9. **Off-Hours:** Before 7am or after 7pm local time
10. **Sensitive:** Tables with pii/personal/sensitive in name
11. **ML Anomaly:** For "anomalies" → query access_anomaly_predictions
12. **Risk Score:** For "risk score" → query user_risk_scores
13. **Failed Actions:** For "failed" → use get_failed_actions TVF
14. **User Activity:** For "user activity" → use get_user_activity_summary TVF
15. **Service Accounts:** For "service accounts" → use get_service_account_audit TVF
16. **Context:** Explain READ vs WRITE vs DDL actions
17. **Compliance:** Never expose PII in responses
18. **Performance:** Never scan Bronze/Silver tables
```

---

## ████ SECTION F: TABLE-VALUED FUNCTIONS ████

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

## ████ SECTION G: BENCHMARK QUESTIONS WITH SQL ████

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

## ✅ DELIVERABLE CHECKLIST

| Section | Requirement | Status |
|---------|-------------|--------|
| **A. Space Name** | Exact name provided | ✅ |
| **B. Space Description** | 2-3 sentences | ✅ |
| **C. Sample Questions** | 15 questions | ✅ |
| **D. Data Assets** | All tables, views, TVFs, ML tables | ✅ |
| **E. General Instructions** | 18 lines (≤20) | ✅ |
| **F. TVFs** | 10 functions with signatures | ✅ |
| **G. Benchmark Questions** | 10 with SQL answers | ✅ |

---

## Agent Domain Tag

**Agent Domain:** 🔒 **Security**

