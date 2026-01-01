# 04 - Reliability Agent TVFs

## Overview

The Reliability Agent domain provides **12 Table-Valued Functions** for job health monitoring, SLA compliance tracking, and failure analysis. These TVFs query the `fact_job_run_timeline` and `fact_usage` tables to provide insights into job execution patterns and reliability metrics.

## TVF Summary

| # | TVF Name | Purpose | Parameters |
|---|----------|---------|------------|
| 1 | `get_failed_jobs_summary` | Jobs with recent failures | days_back, min_failures |
| 2 | `get_job_success_rates` | Success rates by job | start_date, end_date, min_runs |
| 3 | `get_job_duration_trends` | Duration trends over time | start_date, end_date |
| 4 | `get_job_sla_compliance` | SLA compliance tracking | start_date, end_date |
| 5 | `get_job_failure_patterns` | Error pattern analysis | days_back |
| 6 | `get_long_running_jobs` | Jobs exceeding thresholds | days_back, duration_threshold_min |
| 7 | `get_job_retry_analysis` | Retry effectiveness | days_back |
| 8 | `get_job_duration_percentiles` | Duration P50/P90/P95/P99 | days_back |
| 9 | `get_job_failure_cost` | Cost of failed jobs | start_date, end_date |
| 10 | `get_pipeline_health` | DLT pipeline status | days_back |
| 11 | `get_job_schedule_drift` | Schedule adherence | days_back |
| 12 | `get_repair_cost_analysis` | Cost of repairs/retries | start_date, end_date |

---

## TVF Definitions

### 1. get_failed_jobs_summary

**Purpose**: Identify jobs with failures for immediate attention and remediation.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |
| min_failures | INT | No | 1 | Minimum failures to include |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| job_id | STRING | Job identifier |
| job_name | STRING | Job display name |
| workspace_id | STRING | Workspace ID |
| failure_count | BIGINT | Number of failures |
| success_count | BIGINT | Number of successes |
| success_rate | DOUBLE | Percentage successful |
| last_failure_time | TIMESTAMP | Most recent failure |
| last_error_message | STRING | Last error (truncated) |
| run_as | STRING | Job owner |

**Example Queries**:
```sql
-- Jobs with failures in last 7 days
SELECT * FROM TABLE(get_failed_jobs_summary(7, 1));

-- Jobs with 3+ failures in last 30 days
SELECT * FROM TABLE(get_failed_jobs_summary(30, 3));
```

**Natural Language Examples**:
- "Which jobs failed this week?"
- "Show me failing pipelines"
- "What jobs have errors?"

---

### 2. get_job_success_rates

**Purpose**: Track job reliability over time with success rate metrics.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |
| min_runs | INT | No | 5 | Minimum runs for inclusion |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| job_id | STRING | Job identifier |
| job_name | STRING | Job display name |
| total_runs | BIGINT | Total executions |
| successful_runs | BIGINT | Successful completions |
| failed_runs | BIGINT | Failed executions |
| success_rate | DOUBLE | Success percentage |
| avg_duration_min | DOUBLE | Average duration |
| last_run_time | TIMESTAMP | Most recent run |

**Example Queries**:
```sql
-- Success rates for December
SELECT * FROM TABLE(get_job_success_rates('2024-12-01', '2024-12-31', 5));

-- All jobs regardless of run count
SELECT * FROM TABLE(get_job_success_rates('2024-12-01', '2024-12-31', 1));
```

---

### 3. get_job_duration_trends

**Purpose**: Analyze job duration trends to identify performance degradation.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| run_date | DATE | Date of runs |
| job_id | STRING | Job identifier |
| job_name | STRING | Job display name |
| avg_duration_min | DOUBLE | Average duration |
| min_duration_min | DOUBLE | Minimum duration |
| max_duration_min | DOUBLE | Maximum duration |
| run_count | BIGINT | Number of runs |
| trend | STRING | INCREASING/DECREASING/STABLE |

---

### 4. get_job_sla_compliance

**Purpose**: Track SLA compliance for jobs with defined thresholds.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| job_id | STRING | Job identifier |
| job_name | STRING | Job display name |
| total_runs | BIGINT | Total executions |
| runs_within_sla | BIGINT | Runs meeting SLA |
| runs_breaching_sla | BIGINT | Runs exceeding SLA |
| sla_compliance_pct | DOUBLE | Compliance percentage |
| avg_duration_min | DOUBLE | Average duration |
| p95_duration_min | DOUBLE | 95th percentile |

**Natural Language Examples**:
- "Which jobs are missing SLA?"
- "Show me SLA compliance this month"
- "What's our pipeline reliability?"

---

### 5. get_job_failure_patterns

**Purpose**: Analyze failure patterns to identify common error categories.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| error_category | STRING | Categorized error type |
| failure_count | BIGINT | Occurrences |
| affected_jobs | BIGINT | Number of affected jobs |
| sample_error | STRING | Sample error message |
| first_seen | TIMESTAMP | First occurrence |
| last_seen | TIMESTAMP | Most recent occurrence |
| trend | STRING | INCREASING/DECREASING/STABLE |

**Example Queries**:
```sql
-- Error patterns in last 14 days
SELECT * FROM TABLE(get_job_failure_patterns(14));
```

---

### 6. get_long_running_jobs

**Purpose**: Identify jobs exceeding duration thresholds for optimization.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |
| duration_threshold_min | INT | No | 60 | Threshold in minutes |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| job_id | STRING | Job identifier |
| job_name | STRING | Job display name |
| run_id | STRING | Run identifier |
| duration_min | DOUBLE | Actual duration |
| threshold_exceeded_by_min | DOUBLE | Minutes over threshold |
| start_time | TIMESTAMP | Run start time |
| end_time | TIMESTAMP | Run end time |
| run_as | STRING | Job owner |

**Example Queries**:
```sql
-- Jobs running over 60 minutes in last 7 days
SELECT * FROM TABLE(get_long_running_jobs(7, 60));

-- Jobs running over 30 minutes
SELECT * FROM TABLE(get_long_running_jobs(7, 30));
```

---

### 7. get_job_retry_analysis

**Purpose**: Analyze retry effectiveness and wasted compute.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| job_id | STRING | Job identifier |
| job_name | STRING | Job display name |
| total_attempts | BIGINT | Total run attempts |
| first_try_successes | BIGINT | Successful on first try |
| retry_successes | BIGINT | Successful after retry |
| final_failures | BIGINT | Failed after all retries |
| retry_effectiveness_pct | DOUBLE | Percentage recovered by retry |
| wasted_compute_min | DOUBLE | Minutes spent on failures |

---

### 8. get_job_duration_percentiles

**Purpose**: Calculate duration percentiles for capacity planning.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| job_id | STRING | Job identifier |
| job_name | STRING | Job display name |
| run_count | BIGINT | Number of runs |
| p50_duration_min | DOUBLE | Median duration |
| p90_duration_min | DOUBLE | 90th percentile |
| p95_duration_min | DOUBLE | 95th percentile |
| p99_duration_min | DOUBLE | 99th percentile |
| max_duration_min | DOUBLE | Maximum duration |

**Example Queries**:
```sql
-- Duration percentiles for last 30 days
SELECT * FROM TABLE(get_job_duration_percentiles(30));
```

---

### 9. get_job_failure_cost

**Purpose**: Calculate the cost of failed job runs.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| job_id | STRING | Job identifier |
| job_name | STRING | Job display name |
| failure_count | BIGINT | Number of failures |
| estimated_failure_cost | DOUBLE | Estimated wasted cost |
| avg_failure_duration_min | DOUBLE | Average failed run duration |
| total_failure_duration_hr | DOUBLE | Total wasted time |

---

### 10. get_pipeline_health

**Purpose**: DLT pipeline status and health metrics.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| pipeline_id | STRING | Pipeline identifier |
| pipeline_name | STRING | Pipeline display name |
| total_updates | BIGINT | Update count |
| successful_updates | BIGINT | Successful completions |
| failed_updates | BIGINT | Failed updates |
| success_rate | DOUBLE | Success percentage |
| avg_update_duration_min | DOUBLE | Average duration |
| last_update_time | TIMESTAMP | Most recent update |

---

### 11. get_job_schedule_drift

**Purpose**: Identify jobs not running on schedule.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | INT | Yes | - | Days of history to analyze |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| job_id | STRING | Job identifier |
| job_name | STRING | Job display name |
| expected_runs | BIGINT | Expected run count |
| actual_runs | BIGINT | Actual run count |
| missed_runs | BIGINT | Runs not executed |
| drift_pct | DOUBLE | Deviation percentage |
| schedule | STRING | Configured schedule |

---

### 12. get_repair_cost_analysis

**Purpose**: Analyze cost of repairs and retry runs.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | STRING | Yes | - | Start date (YYYY-MM-DD) |
| end_date | STRING | Yes | - | End date (YYYY-MM-DD) |

**Returns**:
| Column | Type | Description |
|--------|------|-------------|
| job_id | STRING | Job identifier |
| job_name | STRING | Job display name |
| repair_count | BIGINT | Number of repairs |
| repair_cost | DOUBLE | Cost of repairs |
| repair_duration_hr | DOUBLE | Time spent on repairs |
| repair_success_rate | DOUBLE | Percentage successful |

---

## SQL Source

**File Location**: `src/semantic/tvfs/reliability_tvfs.sql`

**Tables Used**:
- `fact_job_run_timeline` - Job execution history
- `fact_usage` - Billing data for cost calculations
- `dim_job` - Job metadata

## Next Steps

- **[05-Performance Agent TVFs](05-performance-agent-tvfs.md)**: Query and compute optimization
- **[09-Usage Examples](09-usage-examples.md)**: More query examples

