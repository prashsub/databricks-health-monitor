# Verification Checklist

## Golden Rules Compliance Verification

**Version:** 1.0  
**Usage:** Complete before each deployment and during quarterly audits

---

## Pre-Deployment Checklist

### Phase 1: Design Review

#### Rule 1: Unity Catalog Everywhere

| Check | Requirement | Pass/Fail |
|-------|-------------|-----------|
| 1.1 | All tables created in Unity Catalog (not HMS) | ☐ |
| 1.2 | Catalog naming follows convention (`{company}_{env}`) | ☐ |
| 1.3 | Schema naming follows convention (bronze/silver/gold) | ☐ |
| 1.4 | Table naming follows convention (`{layer}_{entity}`) | ☐ |
| 1.5 | External locations (if any) registered in UC | ☐ |
| 1.6 | Service principal configured for automation | ☐ |

**Sign-off:** _________________ Date: _________

---

#### Rule 2: Medallion Architecture

| Check | Requirement | Pass/Fail |
|-------|-------------|-----------|
| 2.1 | Bronze layer exists and is append-only | ☐ |
| 2.2 | Silver layer uses DLT streaming | ☐ |
| 2.3 | Gold layer follows star schema | ☐ |
| 2.4 | Data flows Bronze → Silver → Gold | ☐ |
| 2.5 | No direct Bronze → Gold transformations | ☐ |
| 2.6 | Layer tags applied to all tables | ☐ |

**Sign-off:** _________________ Date: _________

---

#### Rule 3: Data Quality by Design

| Check | Requirement | Pass/Fail |
|-------|-------------|-----------|
| 3.1 | DLT expectations defined (5+ per table) | ☐ |
| 3.2 | Critical fields use `expect_or_drop` | ☐ |
| 3.3 | Business rules use `expect` (warning) | ☐ |
| 3.4 | Quarantine tables capture failures | ☐ |
| 3.5 | Quarantine includes failure reason | ☐ |
| 3.6 | Quality metrics monitored | ☐ |

**Sign-off:** _________________ Date: _________

---

### Phase 2: Table Configuration

#### Rule 4: Delta Lake Everywhere

| Check | Requirement | Pass/Fail |
|-------|-------------|-----------|
| 4.1 | All tables use `USING DELTA` | ☐ |
| 4.2 | `CLUSTER BY AUTO` on all tables | ☐ |
| 4.3 | `delta.enableChangeDataFeed = true` | ☐ |
| 4.4 | `delta.autoOptimize.optimizeWrite = true` | ☐ |
| 4.5 | `delta.autoOptimize.autoCompact = true` | ☐ |
| 4.6 | Predictive optimization enabled at schema level | ☐ |

**Verification Query:**
```sql
-- Run for each table
SHOW TBLPROPERTIES {catalog}.{schema}.{table};
-- Verify: delta.enableChangeDataFeed = true
```

**Sign-off:** _________________ Date: _________

---

#### Rule 5: Dimensional Modeling with Constraints

| Check | Requirement | Pass/Fail |
|-------|-------------|-----------|
| 5.1 | Surrogate keys defined for dimensions | ☐ |
| 5.2 | Business keys preserved in dimensions | ☐ |
| 5.3 | PRIMARY KEY on surrogate key (NOT ENFORCED) | ☐ |
| 5.4 | FOREIGN KEY references PK (NOT ENFORCED) | ☐ |
| 5.5 | SCD Type assigned (1 or 2) | ☐ |
| 5.6 | `is_current` column for SCD Type 2 | ☐ |
| 5.7 | Fact table has composite PK | ☐ |
| 5.8 | Fact table has FKs to all dimensions | ☐ |

**Verification Query:**
```sql
-- Check constraints
SELECT * FROM information_schema.table_constraints
WHERE table_schema = '{schema}';
```

**Sign-off:** _________________ Date: _________

---

### Phase 3: Job Configuration

#### Rule 6: Serverless-First Compute

| Check | Requirement | Pass/Fail |
|-------|-------------|-----------|
| 6.1 | Jobs use serverless environment | ☐ |
| 6.2 | `environment_version: "4"` in YAML | ☐ |
| 6.3 | `environment_key` in every task | ☐ |
| 6.4 | DLT pipelines have `serverless: true` | ☐ |
| 6.5 | DLT pipelines have `photon: true` | ☐ |
| 6.6 | No hardcoded cluster configurations | ☐ |

**Verification:**
```yaml
# Check in resources/*.yml
environments:
  - environment_key: "default"
    spec:
      environment_version: "4"
```

**Sign-off:** _________________ Date: _________

---

#### Rule 7: Infrastructure as Code

| Check | Requirement | Pass/Fail |
|-------|-------------|-----------|
| 7.1 | `databricks.yml` exists and is valid | ☐ |
| 7.2 | Schemas defined in `resources/schemas.yml` | ☐ |
| 7.3 | All jobs defined in Asset Bundle | ☐ |
| 7.4 | All pipelines defined in Asset Bundle | ☐ |
| 7.5 | Variables defined for environment-specific values | ☐ |
| 7.6 | `databricks bundle validate` passes | ☐ |
| 7.7 | No manual UI-created resources | ☐ |

**Verification:**
```bash
databricks bundle validate -t dev
# Should complete without errors
```

**Sign-off:** _________________ Date: _________

---

### Phase 4: Documentation

#### Rule 8: LLM-Friendly Documentation

| Check | Requirement | Pass/Fail |
|-------|-------------|-----------|
| 8.1 | All tables have COMMENT (50+ chars) | ☐ |
| 8.2 | Table comments explain business purpose | ☐ |
| 8.3 | All columns have COMMENT | ☐ |
| 8.4 | Column comments explain business meaning | ☐ |
| 8.5 | TVFs use standardized comment format | ☐ |
| 8.6 | Metric Views have comprehensive comments | ☐ |
| 8.7 | PII columns are clearly marked | ☐ |

**Verification Query:**
```sql
-- Check table comments
SELECT 
    table_name,
    comment,
    LENGTH(comment) as comment_length
FROM information_schema.tables
WHERE table_schema = '{schema}'
AND (comment IS NULL OR LENGTH(comment) < 50);
-- Should return 0 rows
```

**Sign-off:** _________________ Date: _________

---

### Phase 5: Development Patterns

#### Rule 9: Schema-First Development

| Check | Requirement | Pass/Fail |
|-------|-------------|-----------|
| 9.1 | YAML schema exists for all Gold tables | ☐ |
| 9.2 | YAML defines all columns | ☐ |
| 9.3 | YAML defines PK/FK relationships | ☐ |
| 9.4 | Code extracts schema from YAML | ☐ |
| 9.5 | No hardcoded column names in code | ☐ |
| 9.6 | Schema validation runs before deployment | ☐ |

**Verification:**
```bash
# Check YAML files exist
ls gold_layer_design/yaml/{domain}/*.yaml
```

**Sign-off:** _________________ Date: _________

---

#### Rule 10: Deduplication Before MERGE

| Check | Requirement | Pass/Fail |
|-------|-------------|-----------|
| 10.1 | `.orderBy()` before `.dropDuplicates()` | ☐ |
| 10.2 | Order by timestamp descending | ☐ |
| 10.3 | Deduplicate key matches MERGE key | ☐ |
| 10.4 | Deduplication metrics logged | ☐ |
| 10.5 | MERGE uses correct business key | ☐ |
| 10.6 | SCD Type 2 MERGE includes `is_current = true` | ☐ |

**Verification Pattern:**
```python
# Correct pattern in code
silver_df = (
    spark.table(silver_table)
    .orderBy(col("processed_timestamp").desc())  # ✓ Order first
    .dropDuplicates([business_key])  # ✓ Then dedupe
)
```

**Sign-off:** _________________ Date: _________

---

## Production Deployment Checklist

### Pre-Deployment

| # | Check | Required By | Status |
|---|-------|-------------|--------|
| 1 | All design review checklists passed | Platform Lead | ☐ |
| 2 | Code review completed and approved | Peer + Lead | ☐ |
| 3 | `databricks bundle validate` passes | Automated | ☐ |
| 4 | Unit tests pass (if applicable) | Data Engineer | ☐ |
| 5 | Integration tests pass in dev | Data Engineer | ☐ |
| 6 | Security review completed (if PII) | Security Team | ☐ |
| 7 | Data Steward approval | Data Steward | ☐ |

### Deployment

| # | Step | Owner | Status |
|---|------|-------|--------|
| 1 | Deploy to production | Platform Admin | ☐ |
| 2 | Verify tables created | Data Engineer | ☐ |
| 3 | Verify constraints applied | Data Engineer | ☐ |
| 4 | Run initial pipeline | Data Engineer | ☐ |
| 5 | Verify data quality | Data Steward | ☐ |
| 6 | Enable monitoring | Platform Admin | ☐ |
| 7 | Enable schedules | Platform Admin | ☐ |

### Post-Deployment

| # | Check | Owner | Status |
|---|-------|-------|--------|
| 1 | First scheduled run successful | Data Engineer | ☐ |
| 2 | Data freshness SLA met | Data Steward | ☐ |
| 3 | No quality alerts triggered | Data Steward | ☐ |
| 4 | Stakeholders notified | Data Engineer | ☐ |
| 5 | Runbook documented | Data Engineer | ☐ |

---

## Quarterly Audit Checklist

### Scope Definition

| Domain | Tables | Last Audit | Auditor |
|--------|--------|------------|---------|
| [Domain 1] | [Count] | [Date] | [Name] |
| [Domain 2] | [Count] | [Date] | [Name] |

### Audit Results Summary

| Rule | Total Items | Compliant | Non-Compliant | % |
|------|-------------|-----------|---------------|---|
| Rule 1: Unity Catalog | | | | |
| Rule 2: Medallion | | | | |
| Rule 3: Data Quality | | | | |
| Rule 4: Delta Lake | | | | |
| Rule 5: Constraints | | | | |
| Rule 6: Serverless | | | | |
| Rule 7: IaC | | | | |
| Rule 8: Documentation | | | | |
| Rule 9: Schema-First | | | | |
| Rule 10: Deduplication | | | | |
| **Overall** | | | | |

### Remediation Plan

| Finding | Severity | Owner | Due Date | Status |
|---------|----------|-------|----------|--------|
| | | | | |

---

## Quick Reference: Common Violations

### High Severity (Must Fix Before Production)

| Violation | Impact | Fix |
|-----------|--------|-----|
| Missing PK constraint | BI tools can't auto-discover relationships | Add `PRIMARY KEY ... NOT ENFORCED` |
| No CDF enabled | Can't use incremental processing | Add `delta.enableChangeDataFeed = true` |
| Missing deduplication | MERGE failures in production | Add `orderBy().dropDuplicates()` |
| Hardcoded cluster | Cost overruns, maintenance burden | Use serverless environment |

### Medium Severity (Fix Within Sprint)

| Violation | Impact | Fix |
|-----------|--------|-----|
| Missing table comment | Genie/AI can't understand data | Add COMMENT with business context |
| Missing column comments | Self-service analytics impaired | Add COMMENT to all columns |
| No schema YAML | Schema drift risk | Create YAML definition |
| Few DLT expectations | Quality issues not detected | Add 5+ expectations per table |

### Low Severity (Fix When Possible)

| Violation | Impact | Fix |
|-----------|--------|-----|
| Short comments (<50 chars) | Limited AI understanding | Expand with business context |
| Missing domain tag | Catalog browsing harder | Add `domain` TBLPROPERTY |
| No quarantine table | Failed records lost | Add quarantine pattern |

---

## Sign-Off Sheet

### Design Review

| Reviewer | Role | Date | Signature |
|----------|------|------|-----------|
| | Platform Lead | | |
| | Data Steward | | |
| | Security (if PII) | | |

### Production Approval

| Approver | Role | Date | Signature |
|----------|------|------|-----------|
| | Platform Lead | | |
| | Executive Sponsor (major) | | |

---

## Related Documents

- [Golden Rules](../01-golden-rules-enterprise-data-platform.md)
- [Roles and Responsibilities](./01-roles-and-responsibilities-raci.md)
- [Implementation Workflow](./02-implementation-workflow.md)
