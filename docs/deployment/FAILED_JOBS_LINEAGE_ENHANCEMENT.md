# Failed Jobs with Lineage-Based Impact Analysis

## **Use Case**

When a job fails, we need to understand the **downstream impact**:
1. **What tables does this failed job write to?**
2. **Which other jobs depend on those tables (downstream jobs)?**
3. **Who owns those downstream jobs (for notifications)?**

This enables:
- **Proactive notifications** to downstream owners
- **Impact assessment** - understanding blast radius of failures
- **Priority triage** - jobs with many dependents get higher priority

---

## **Data Sources**

### 1. `system.access.table_lineage`

**Key Columns:**
- `entity_type` = 'JOB'
- `entity_id` = job_id (STRING)
- `workspace_id` = workspace identifier
- `target_table_full_name` = table written by the job
- `source_table_full_name` = table read by the job
- `created_by` = user who ran the job
- `event_date` = date of lineage event (partitioned)
- `event_time` = timestamp of lineage event

**Important Notes:**
- Lineage is recorded when a job **reads or writes** a table
- `target_table_full_name` IS NOT NULL → job writes to this table
- `source_table_full_name` IS NOT NULL → job reads from this table
- Recent lineage (last 30-90 days) is most relevant

### 2. `fact_job_run_timeline`

**Key Columns:**
- `workspace_id`, `job_id`, `run_id`
- `run_date`, `result_state`, `termination_code`
- Used to identify failed jobs

### 3. `dim_job`

**Key Columns:**
- `workspace_id`, `job_id`
- `name`, `run_as`, `creator_id`
- Used to get job metadata and owners

---

## **SQL Logic Design**

### **Step 1: Identify Failed Jobs**

```sql
WITH failed_jobs AS (
  SELECT DISTINCT
    f.workspace_id,
    f.job_id,
    COALESCE(j.name, CAST(f.job_id AS STRING)) AS job_name,
    f.run_date,
    f.termination_code,
    COALESCE(u.email, j.run_as, j.creator_id, 'Unknown') AS owner
  FROM fact_job_run_timeline f
  LEFT JOIN dim_job j ON f.workspace_id = j.workspace_id AND f.job_id = j.job_id
  LEFT JOIN dim_user u ON CAST(COALESCE(j.run_as, j.creator_id) AS STRING) = u.user_id
  WHERE f.run_date BETWEEN :time_range.min AND :time_range.max
    AND f.termination_code IS NOT NULL 
    AND f.termination_code NOT IN ('SUCCESS', 'SKIPPED')
)
```

### **Step 2: Find Tables Written by Failed Jobs**

```sql
failed_job_outputs AS (
  SELECT DISTINCT
    fj.workspace_id,
    fj.job_id,
    fj.job_name,
    l.target_table_full_name AS output_table
  FROM failed_jobs fj
  JOIN system.access.table_lineage l
    ON CAST(fj.job_id AS STRING) = l.entity_id
    AND fj.workspace_id = l.workspace_id
    AND l.entity_type = 'JOB'
    AND l.target_table_full_name IS NOT NULL
    AND l.event_date >= CURRENT_DATE() - INTERVAL 90 DAYS
)
```

**Key Points:**
- Join on `job_id` (cast to STRING) = `entity_id`
- Filter for `entity_type = 'JOB'`
- `target_table_full_name IS NOT NULL` = writes to this table
- Recent lineage (90 days) is sufficient

### **Step 3: Find Downstream Jobs that Read Those Tables**

```sql
downstream_jobs AS (
  SELECT
    fjo.workspace_id AS failed_workspace_id,
    fjo.job_id AS failed_job_id,
    fjo.job_name AS failed_job_name,
    fjo.output_table,
    l.entity_id AS downstream_job_id,
    l.workspace_id AS downstream_workspace_id,
    dj.name AS downstream_job_name,
    COALESCE(du.email, dj.run_as, dj.creator_id, 'Unknown') AS downstream_owner
  FROM failed_job_outputs fjo
  JOIN system.access.table_lineage l
    ON fjo.output_table = l.source_table_full_name
    AND l.entity_type = 'JOB'
    AND l.source_table_full_name IS NOT NULL
    AND l.event_date >= CURRENT_DATE() - INTERVAL 90 DAYS
  LEFT JOIN dim_job dj 
    ON l.workspace_id = dj.workspace_id 
    AND CAST(l.entity_id AS STRING) = CAST(dj.job_id AS STRING)
  LEFT JOIN dim_user du 
    ON CAST(COALESCE(dj.run_as, dj.creator_id) AS STRING) = du.user_id
  WHERE l.entity_id != CAST(fjo.job_id AS STRING)  -- Exclude self-references
)
```

**Key Points:**
- `source_table_full_name = output_table` → downstream job reads the table
- Exclude self (same job reading and writing same table)
- Get downstream job metadata and owner

### **Step 4: Aggregate Downstream Dependencies**

```sql
SELECT
  fj.workspace_id,
  fj.job_id,
  fj.job_name,
  fj.termination_code,
  fj.run_date AS run_time,
  ROUND(fj.run_duration_seconds / 60.0, 1) AS duration_minutes,
  fj.owner,
  fj.tags,
  -- Dependency columns
  COUNT(DISTINCT dj.downstream_job_id) AS affected_jobs_count,
  COLLECT_SET(dj.output_table)[0:3] AS affected_tables,  -- First 3 tables
  COLLECT_SET(dj.downstream_job_name)[0:5] AS downstream_jobs,  -- First 5 jobs
  COLLECT_SET(dj.downstream_owner)[0:5] AS downstream_owners  -- First 5 owners
FROM failed_jobs fj
LEFT JOIN failed_job_outputs fjo 
  ON fj.workspace_id = fjo.workspace_id AND fj.job_id = fjo.job_id
LEFT JOIN downstream_jobs dj 
  ON fjo.workspace_id = dj.failed_workspace_id AND fjo.job_id = dj.failed_job_id
GROUP BY 1,2,3,4,5,6,7,8
ORDER BY affected_jobs_count DESC, fj.run_date DESC
```

**Aggregated Columns:**
- `affected_jobs_count` - Number of downstream jobs impacted
- `affected_tables` - List of tables (first 3)
- `downstream_jobs` - List of downstream job names (first 5)
- `downstream_owners` - List of downstream owners (first 5) for notifications

---

## **Final Comprehensive Query**

```sql
-- Failed Jobs with Lineage-Based Downstream Impact Analysis
WITH failed_jobs AS (
  SELECT 
    f.workspace_id,
    f.job_id,
    COALESCE(j.name, CAST(f.job_id AS STRING)) AS job_name,
    f.run_date,
    f.termination_code,
    f.run_duration_seconds,
    COALESCE(u.email, j.run_as, j.creator_id, 'Unknown') AS owner,
    COALESCE(j.tags_json, '{}') AS tags
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline f
  LEFT JOIN ${catalog}.${gold_schema}.dim_job j 
    ON f.workspace_id = j.workspace_id AND f.job_id = j.job_id
  LEFT JOIN ${catalog}.${gold_schema}.dim_user u 
    ON CAST(COALESCE(j.run_as, j.creator_id) AS STRING) = u.user_id
  WHERE f.run_date BETWEEN :time_range.min AND :time_range.max
    AND f.termination_code IS NOT NULL 
    AND f.termination_code NOT IN ('SUCCESS', 'SKIPPED')
),
-- Tables written by failed jobs
failed_job_outputs AS (
  SELECT DISTINCT
    fj.workspace_id,
    fj.job_id,
    l.target_table_full_name AS output_table
  FROM failed_jobs fj
  JOIN system.access.table_lineage l
    ON CAST(fj.job_id AS STRING) = l.entity_id
    AND fj.workspace_id = l.workspace_id
    AND l.entity_type = 'JOB'
    AND l.target_table_full_name IS NOT NULL
    AND l.event_date >= CURRENT_DATE() - INTERVAL 90 DAYS
),
-- Downstream jobs that read those tables
downstream_dependencies AS (
  SELECT
    fjo.workspace_id AS failed_workspace_id,
    fjo.job_id AS failed_job_id,
    fjo.output_table AS affected_table,
    l.entity_id AS downstream_job_id,
    dj.name AS downstream_job_name,
    COALESCE(du.email, dj.run_as, dj.creator_id, 'Unknown') AS downstream_owner
  FROM failed_job_outputs fjo
  JOIN system.access.table_lineage l
    ON fjo.output_table = l.source_table_full_name
    AND l.entity_type = 'JOB'
    AND l.source_table_full_name IS NOT NULL
    AND l.event_date >= CURRENT_DATE() - INTERVAL 90 DAYS
  LEFT JOIN ${catalog}.${gold_schema}.dim_job dj 
    ON l.workspace_id = dj.workspace_id 
    AND CAST(l.entity_id AS STRING) = CAST(dj.job_id AS STRING)
  LEFT JOIN ${catalog}.${gold_schema}.dim_user du 
    ON CAST(COALESCE(dj.run_as, dj.creator_id) AS STRING) = du.user_id
  WHERE l.entity_id != CAST(fjo.job_id AS STRING)  -- Exclude self
)
-- Final aggregation
SELECT
  fj.job_name,
  COALESCE(w.workspace_name, CAST(fj.workspace_id AS STRING)) AS workspace_name,
  fj.termination_code,
  fj.run_date AS run_time,
  ROUND(fj.run_duration_seconds / 60.0, 1) AS duration_minutes,
  fj.owner,
  fj.tags,
  -- Impact analysis columns
  COALESCE(COUNT(DISTINCT dd.downstream_job_id), 0) AS affected_jobs_count,
  COALESCE(CONCAT_WS(', ', COLLECT_SET(dd.affected_table)), 'None') AS affected_tables,
  COALESCE(CONCAT_WS(', ', COLLECT_SET(dd.downstream_job_name)), 'None') AS downstream_jobs,
  COALESCE(CONCAT_WS(', ', COLLECT_SET(dd.downstream_owner)), 'None') AS notify_owners
FROM failed_jobs fj
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w 
  ON fj.workspace_id = w.workspace_id
LEFT JOIN downstream_dependencies dd 
  ON fj.workspace_id = dd.failed_workspace_id 
  AND fj.job_id = dd.failed_job_id
WHERE (ARRAY_CONTAINS(:param_workspace, 'all') OR ARRAY_CONTAINS(:param_workspace, w.workspace_name))
GROUP BY 
  fj.job_name, 
  w.workspace_name, 
  fj.workspace_id,
  fj.termination_code, 
  fj.run_date, 
  fj.run_duration_seconds,
  fj.owner, 
  fj.tags
ORDER BY affected_jobs_count DESC, fj.run_date DESC
LIMIT 50
```

---

## **New Columns Added**

| Column | Type | Description | Business Value |
|--------|------|-------------|----------------|
| `affected_jobs_count` | INT | Number of downstream jobs that may be impacted | **Prioritization** - higher count = higher priority |
| `affected_tables` | STRING | Comma-separated list of tables written by this job | **Root cause** - which tables are blocked |
| `downstream_jobs` | STRING | Comma-separated list of downstream job names | **Impact visibility** - which jobs may fail next |
| `notify_owners` | STRING | Comma-separated list of downstream job owners | **Actionable** - who to notify about the failure |

---

## **Widget Updates Required**

1. Add 4 new fields to widget query
2. Add 4 new columns to widget encodings
3. Order columns for best UX

---

## **Performance Considerations**

✅ **Optimizations:**
- Lineage filtered to last 90 days (partitioned on `event_date`)
- `COLLECT_SET` instead of `ARRAY_AGG` (removes duplicates automatically)
- Limited to 50 results
- Indexed on `entity_id`, `target_table_full_name`, `source_table_full_name`

⚠️ **Notes:**
- Lineage data may have delays (typically < 1 hour)
- Jobs without lineage data will show "None" for dependencies
- Self-referential jobs (reading and writing same table) are excluded

---

## **Testing Checklist**

- [ ] Failed job with downstream dependencies shows count > 0
- [ ] Failed job without dependencies shows "None"
- [ ] Table names are properly formatted (catalog.schema.table)
- [ ] Owner emails are deduplicated
- [ ] Sorting by `affected_jobs_count` works correctly
- [ ] Performance is acceptable (< 5 seconds for 50 results)

---

## **Future Enhancements**

1. **Real-time Alerts** - Trigger notifications to `notify_owners` via webhook
2. **Dependency Graph Visualization** - Visual lineage from failed job to downstream
3. **Historical Impact** - Track which downstream jobs actually failed after this failure
4. **SLA Impact** - Calculate SLA breach risk for downstream jobs

---

**References:**
- [System Table: table_lineage](https://docs.databricks.com/en/admin/system-tables/lineage.html)
- [Data Lineage Documentation](https://docs.databricks.com/en/data-governance/unity-catalog/data-lineage.html)

