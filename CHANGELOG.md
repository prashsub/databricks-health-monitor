# Changelog

All notable milestones and improvements to the Databricks Health Monitor project.

This changelog is derived from the rule improvement history in
`.cursor/rules/admin/21-self-improvement.mdc`. For detailed case studies, see the
linked documents under `docs/reference/rule-improvement-*.md`.

---

## February 2026

### Genie Space Optimization Patterns
- Comprehensive patterns for optimizing Genie Spaces including accuracy testing
  and repeatability improvement across 5 domains.
- Production benchmarks: Quality 100% repeatability, Reliability 80%, Security 67%.
- New rule: `34-genie-space-optimization.mdc`.

---

## January 2026

### On-Behalf-Of (OBO) Authentication Context Detection (Jan 27)
- Fixed agent evaluation failures with permission errors.
- Added mandatory context detection for OBO vs default auth.
- See `docs/deployment/deployment-history/obo-auth-fix.md`.

### Genie Space Resource Declaration for MLflow Agents (Jan 27)
- Genie Spaces must be declared as resources when logging agent models.
- Added `DatabricksGenieSpace` and `DatabricksSQLWarehouse` to `SystemAuthPolicy`.

### AI/BI Dashboard Deployment Patterns (Jan 14)
- Production deployment of 6 Lakeview dashboards (1.2 MB JSON, ~185 datasets).
- SELECT LIMIT 1 validation reduces dev loop time by 90%.
- See `docs/reference/rule-improvement-aibi-dashboard-deployment.md`.

### MLflow ML Pipeline NaN Handling (Jan 4)
- Fixed 5 model inference failures from NaN/Inf asymmetry between training and
  scoring paths.
- Inference success rate improved from 76% to 96%.

---

## December 2025

### SQL Alerts V2 API Patterns
- Production deployment of 56 alerts across 5 domains.
- Discovered correct V2 API endpoint (`/api/2.0/alerts`).

### Lakehouse Monitoring Output Table Documentation for Genie
- Post-deployment documentation job that adds table and column comments to
  monitoring output tables for Genie/LLM interpretability.

### MLflow and ML Model Patterns
- 25 models across 5 domains with 70+ distinct errors documented.
- Rules for experiment paths, dataset logging, batch inference types.

### Systematic Gold Layer Debugging Patterns
- 41 tables, 7 domains, 88 bugs fixed in 6 hours.
- Created 6 proactive scanning scripts; 52% of bugs prevented proactively.

### YAML-Driven Gold Layer Table Setup
- Refactored 14 domain-specific setup scripts (~5000 lines) into a single
  300-line generic script reading 39 YAML files at runtime.

### Metric Views Schema Validation Patterns
- 100% of initial metric view deployments failed due to preventable schema issues.
- Added mandatory pre-creation schema validation and automated validator.

### Gold Layer Implementation Guidance
- Documented gap between design documentation and implementation requirements.
- Added Silver table naming conventions, join requirements, column source mapping.

---

## November 2025

### Ad-Hoc Exploration Notebooks
- Dual-format pattern for Databricks workspace and local Databricks Connect.
- New rule: `adhoc-exploration-notebooks.mdc`.

### Gold Table Constraint Setup Patterns
- 10+ deployment errors during Gold layer setup (38 tables, 7 domains).
- Never define FK constraints inline in CREATE TABLE; apply via ALTER TABLE.

### Python Notebook Parameter Passing in DABs
- Always use `dbutils.widgets.get()` for notebook_task, never `argparse`.
- 19+ files had to be fixed.

### Databricks Asset Bundle Deployment Error Prevention
- 10 critical deployment error patterns documented.
- Automated pre-deployment validation script catches 80% of errors.

---

## October 2025

### Root Path for DLT Pipelines
- Added Lakeflow Pipelines Editor best practices to Asset Bundles rule.

### Custom Metrics as Table Columns
- Documented where custom metrics appear in Lakehouse Monitoring tables.

### Table-Valued Functions SQL Patterns
- 3 critical SQL issues discovered during deployment of 15 functions.
- New rule: `databricks-table-valued-functions.mdc`.

### DQX Framework Integration
- Databricks Labs DQX data quality framework patterns.
- New rule: `dqx-patterns.mdc`.
