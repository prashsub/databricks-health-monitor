# Appendix E - Glossary & Acronyms

**Complete reference of terms, acronyms, and domain-specific vocabulary used in the Databricks Health Monitor project.**

---

## Core Terms

### A

**Agent**  
An AI-powered conversational interface specialized in a specific domain (e.g., Cost Agent, Security Agent). Uses tool calling to execute queries and ML models to provide insights.

**Agent Domain**  
One of 7 domains that organize all project artifacts: Cost, Security, Performance, Reliability, Quality, MLOps, Governance.

**Anomaly Detection**  
ML technique to identify unusual patterns in data (e.g., cost spikes, security threats, job failures) using algorithms like Isolation Forest, Autoencoders.

**Asset Bundle**  
See Databricks Asset Bundle (DAB).

**Atomic Job**  
Layer 1 in hierarchical job architecture. Contains actual notebook references and performs single-purpose tasks. Referenced by composite jobs.

---

### B

**Bronze Layer**  
First layer in medallion architecture. Raw data ingestion from system tables with minimal transformation. Optimized for append-only writes with CDF enabled.

**Batch Inference**  
ML model predictions run on large datasets via scheduled jobs (vs real-time serving). Uses `fe.score_batch()` pattern.

**Bottleneck**  
Resource constraint limiting system performance (e.g., memory, CPU, network). Detected via performance monitoring and ML models.

---

### C

**CDF (Change Data Feed)**  
Delta Lake feature that tracks row-level changes (INSERT, UPDATE, DELETE) in a separate log. Enables efficient incremental processing in Silver layer.

**Composite Job**  
Layer 2 in hierarchical job architecture. References atomic jobs via `run_job_task`. Coordinates domain-specific workflows (e.g., semantic layer setup).

**Config-Driven**  
Design pattern where behavior is controlled by configuration files (YAML, JSON) rather than hardcoded logic. Enables infrastructure as code.

**Constraint**  
Database rule enforcing data integrity. Unity Catalog supports PRIMARY KEY and FOREIGN KEY constraints (informational, NOT ENFORCED).

**Cost Attribution**  
Process of assigning DBU costs to specific workspaces, users, SKUs, or tags for chargeback and optimization.

**Custom Metric**  
User-defined aggregation or calculation in Lakehouse Monitoring (e.g., business KPIs, technical metrics, drift measures).

---

### D

**DAB (Databricks Asset Bundle)**  
Infrastructure-as-code framework for defining Databricks resources (jobs, pipelines, models) in YAML. Enables version control and automated deployment.

**Dashboard (AI/BI)**  
Lakeview dashboard with interactive visualizations. Uses serverless SQL to query semantic layer (never direct system tables).

**DBU (Databricks Unit)**  
Unit of compute pricing on Databricks platform. Different SKUs (Jobs Compute, SQL, ML Serving) have different DBU rates.

**Deletion Vector**  
Delta Lake optimization that marks deleted rows without rewriting files. Enabled via `delta.enableDeletionVectors` table property.

**Dimension Table**  
Table containing descriptive attributes (who, what, where). Often uses SCD Type 2 for historical tracking. Examples: `dim_workspace`, `dim_user`.

**DLT (Delta Live Tables)**  
Declarative ETL framework for building data pipelines with automatic dependency resolution, quality checks, and monitoring.

**DQ (Data Quality)**  
Measure of data fitness for use. Tracked via DLT expectations, Lakehouse Monitoring, and custom validation rules.

**Drift Metric**  
Statistical measure detecting distribution changes in data over time. Used in Lakehouse Monitoring and ML model monitoring.

**Dual-Purpose Comment**  
Documentation pattern serving both humans and LLMs. Format: `[Definition]. Business: [context]. Technical: [details]`.

---

### E

**Expectation (DLT)**  
Data quality rule in Delta Live Tables. Types: `@dlt.expect` (warn), `@dlt.expect_or_drop` (quarantine), `@dlt.expect_or_fail` (halt pipeline).

**ERD (Entity Relationship Diagram)**  
Visual representation of data model showing tables, columns, and relationships. Created using Mermaid for Gold layer design.

---

### F

**Fact Table**  
Table containing measurable events or metrics (when, how much). Grain defines uniqueness. Examples: `fact_usage`, `fact_job_run_timeline`.

**Feature Engineering**  
Process of transforming raw data into ML model inputs. Uses Unity Catalog Feature Engineering for centralized feature storage.

**Foreign Key (FK)**  
Column(s) referencing primary key of another table. Unity Catalog constraints are informational only (NOT ENFORCED).

---

### G

**Genie Space**  
Natural language SQL interface in Databricks. Configured with tables, functions, agent instructions, and benchmark questions for domain-specific queries.

**Gold Layer**  
Third layer in medallion architecture. Analytics-ready business entities with constraints, optimizations, and rich metadata. Optimized for consumption.

**Governance**  
Data management policies and processes. Implemented via Unity Catalog with lineage, tags, access control, and audit logs.

**Grain**  
Level of detail in a fact table. Defined by primary key columns. Examples: daily (date), hourly (date + hour), transaction-level (transaction_id).

---

### H

**Hierarchical Jobs**  
3-layer job architecture: Atomic (Layer 1) → Composite (Layer 2) → Master Orchestrator (Layer 3). Prevents notebook duplication.

---

### I

**Incremental Processing**  
Pattern that processes only new/changed data since last run. Enabled by CDF in Bronze, DLT streaming in Silver, and MERGE in Gold.

**Isolation Forest**  
Unsupervised ML algorithm for anomaly detection. Used in cost anomaly detection and security threat scoring models.

---

### J

**Job**  
Scheduled or triggered execution of notebooks, SQL, or pipelines. Defined in Databricks Asset Bundles and orchestrated via Workflows.

---

### K

**KPI (Key Performance Indicator)**  
Measurable value demonstrating effectiveness. Examples: job success rate, cost per workspace, security event count.

---

### L

**Lakebase**  
PostgreSQL OLTP database for Databricks Apps. Stores transactional app data (chat history, user preferences, alert rules).

**Lakehouse Monitoring**  
Databricks service for automated data quality and drift detection. Creates monitors with custom metrics on Delta tables.

**Lineage**  
Data flow tracking from source to consumption. Automatically captured by Unity Catalog for tables, columns, jobs, and models.

**Liquid Clustering**  
Adaptive data layout optimization in Delta Lake. `CLUSTER BY AUTO` lets Delta choose optimal clustering columns dynamically.

**LLM (Large Language Model)**  
AI model trained on text (e.g., GPT-4, Claude, DBRX). Used in agents for natural language understanding and generation.

---

### M

**Master Orchestrator**  
Layer 3 job that coordinates complete workflows across multiple domains. Examples: `master_setup_orchestrator`, `master_refresh_orchestrator`.

**Medallion Architecture**  
Data quality pattern: Bronze (raw) → Silver (validated) → Gold (business). Progressively improves data quality at each layer.

**Metric View**  
Databricks semantic layer object defining dimensions, measures, and metadata in YAML. Optimized for Genie natural language queries.

**MLflow**  
Open-source platform for ML lifecycle. Tracks experiments, registers models, and manages deployments. Integrated with Unity Catalog.

**Model Serving**  
Real-time ML inference via REST API endpoints. Uses serverless compute for auto-scaling and cost efficiency.

**Monitor (Lakehouse)**  
Configuration defining which table to monitor, granularity, and custom metrics. Creates `_profile_metrics` and `_drift_metrics` output tables.

---

### N

**Natural Language Query**  
User question in plain English converted to SQL. Enabled by Genie Spaces, Metric Views, and AI agents.

**NOT ENFORCED**  
Unity Catalog constraint modifier. Constraints are informational (metadata only), not physically enforced. Syntax: `CONSTRAINT pk PRIMARY KEY (id) NOT ENFORCED`.

---

### O

**Orchestrator**  
Job that coordinates multiple other jobs. See Composite Job or Master Orchestrator.

**Output Table**  
Table created by Lakehouse Monitoring containing profile metrics or drift metrics. Names: `{table_name}_profile_metrics`, `{table_name}_drift_metrics`.

---

### P

**Photon**  
Databricks vectorized query engine. Provides 2-5x performance improvement for SQL queries. Enabled on serverless SQL and DLT pipelines.

**PII (Personally Identifiable Information)**  
Data that can identify individuals (names, emails, SSNs). Tagged via `contains_pii` table property for governance.

**Pipeline (DLT)**  
Delta Live Tables workflow defining streaming transformations with dependencies, expectations, and schedules.

**Predictive Optimization**  
Databricks feature that automatically optimizes tables (compaction, clustering, statistics). Enabled at schema or catalog level.

**Primary Key (PK)**  
Column(s) uniquely identifying each row in a table. Unity Catalog constraints are informational (NOT ENFORCED).

---

### Q

**Quarantine**  
Pattern for isolating invalid records. DLT: `@dlt.expect_or_drop` sends failures to quarantine table. Gold: separate error tables.

**Query History**  
System table (`system.query.history`) tracking all SQL queries executed in workspace. Source for performance monitoring.

---

### R

**Real-Time Inference**  
ML predictions via synchronous API calls. Served by Model Serving endpoints with sub-200ms latency.

**Reliability**  
System ability to perform consistently over time. Monitored via SLA tracking, uptime metrics, and incident response.

**Row Tracking**  
Delta Lake feature tracking row-level changes for efficient updates. Enabled via `delta.enableRowTracking` table property.

---

### S

**SCD Type 2 (Slowly Changing Dimension Type 2)**  
Historical tracking pattern using effective dates and current flag. Columns: `effective_from`, `effective_to`, `is_current`.

**Semantic Layer**  
Abstraction layer between raw data and consumption. Includes TVFs, Metric Views, and Genie Spaces with business-friendly metadata.

**Serverless**  
Compute model where Databricks manages infrastructure. Auto-scaling, pay-per-use pricing. Used for SQL, Jobs, DLT, Model Serving.

**Silver Layer**  
Second layer in medallion architecture. Validated, deduplicated, streaming data with DLT expectations. Optimized for incremental processing.

**SKU (Stock Keeping Unit)**  
Databricks pricing category. Examples: Jobs Compute, SQL Warehouse, All-Purpose Compute, ML Training, Model Serving.

**SLA (Service Level Agreement)**  
Commitment to service quality (e.g., "95% of jobs complete within SLA"). Tracked via reliability monitoring.

**Snowflake Schema (joins)**  
Join pattern where dimension table joins to fact, which joins to another dimension. Supported in Metric Views v1.1+ via nested `joins:`.

**Streaming**  
Continuous data processing pattern. Used in Silver layer via DLT `dlt.read_stream()` for low-latency transformations.

**System Tables**  
Databricks-managed tables with platform telemetry. Located in `system.*` schemas (billing, lakeflow, access, etc.). Read-only.

**Synonym**  
Alternative term for dimension/measure in Metric Views. Helps Genie match natural language queries. Example: "revenue" synonyms = ["sales", "dollars"].

---

### T

**Table-Valued Function (TVF)**  
SQL function returning a table. Parameterized, reusable query logic. Example: `get_daily_cost_summary(start_date, end_date)`.

**Tag**  
Key-value metadata on Unity Catalog objects. Examples: `domain=cost`, `layer=gold`, `contains_pii=true`. Used for governance and discovery.

**Tool (Agent)**  
Function an AI agent can call to retrieve data or execute actions. Examples: query TVF, run ML model, fetch dashboard data.

**Tool Calling**  
LLM capability to invoke external functions during conversation. Enables agents to access real data instead of hallucinating.

---

### U

**Unity Catalog (UC)**  
Databricks unified governance solution. Provides centralized metadata, access control, lineage, and audit logging across workspaces.

**Upsert**  
Operation combining UPDATE (if exists) and INSERT (if not). Implemented via Delta `MERGE` command in Gold layer.

---

### V

**Validation**  
Data quality check. Types: schema validation (pre-creation), DLT expectations (Silver), custom metrics (Lakehouse Monitoring).

---

### W

**Warehouse (SQL)**  
Serverless SQL endpoint for query execution. Auto-scaling compute for dashboards, alerts, and ad-hoc queries.

**Workflow**  
Databricks Jobs orchestration engine. Supports multi-task DAGs with dependencies, retries, and notifications.

---

### X

**XGBoost (eXtreme Gradient Boosting)**  
ML algorithm for classification and regression. Used in job failure prediction and performance optimization models.

---

### Y

**YAML (YAML Ain't Markup Language)**  
Human-readable data serialization format. Used for DABs, Metric Views, alert definitions, and Gold table schemas.

**YAML-Driven**  
Pattern where schemas or configurations are defined in YAML files and processed at runtime. Example: Gold table creation from YAML.

---

### Z

**Z-Ordering**  
Data layout optimization technique deprecated in favor of liquid clustering. Manually specified clustering columns.

---

## Acronyms

### A-D

| Acronym | Expansion | Context |
|---------|-----------|---------|
| **ACID** | Atomicity, Consistency, Isolation, Durability | Database transaction properties guaranteed by Delta Lake |
| **AI** | Artificial Intelligence | Agent framework, ML models |
| **API** | Application Programming Interface | REST APIs, SQL APIs, serving endpoints |
| **AWS** | Amazon Web Services | Cloud platform option for Databricks |
| **BI** | Business Intelligence | Dashboards, visualizations |
| **CDF** | Change Data Feed | Delta Lake incremental processing feature |
| **CI/CD** | Continuous Integration/Continuous Deployment | GitHub Actions automated deployment |
| **CLI** | Command Line Interface | Databricks CLI for deployment |
| **CPU** | Central Processing Unit | Compute resource |
| **CRUD** | Create, Read, Update, Delete | Basic data operations |
| **CSV** | Comma-Separated Values | Data export format |
| **DAB** | Databricks Asset Bundle | Infrastructure as code framework |
| **DAG** | Directed Acyclic Graph | Workflow task dependencies |
| **DBR** | Databricks Runtime | Spark execution environment |
| **DBRX** | Databricks LLM | Foundation model option for agents |
| **DBU** | Databricks Unit | Compute pricing unit |
| **DDL** | Data Definition Language | SQL table creation statements |
| **DLT** | Delta Live Tables | Streaming ETL framework |
| **DML** | Data Manipulation Language | SQL INSERT, UPDATE, DELETE |
| **DQ** | Data Quality | Monitoring and validation |

### E-M

| Acronym | Expansion | Context |
|---------|-----------|---------|
| **ERD** | Entity Relationship Diagram | Data model visualization |
| **ETL** | Extract, Transform, Load | Data pipeline pattern |
| **FK** | Foreign Key | Referential integrity constraint |
| **GPU** | Graphics Processing Unit | ML training hardware |
| **HTTP** | Hypertext Transfer Protocol | API communication |
| **IAC** | Infrastructure as Code | DABs, YAML configurations |
| **IDE** | Integrated Development Environment | Development tools |
| **JSON** | JavaScript Object Notation | Data interchange format |
| **KPI** | Key Performance Indicator | Business metric |
| **LLM** | Large Language Model | AI foundation model |
| **LTS** | Long Term Support | Databricks Runtime version |
| **MERGE** | SQL MERGE command | Upsert operation in Gold layer |
| **ML** | Machine Learning | Predictive models, serving |
| **MLOps** | Machine Learning Operations | ML lifecycle management |
| **MTTR** | Mean Time To Resolution | Incident response metric |

### N-Z

| Acronym | Expansion | Context |
|---------|-----------|---------|
| **NL** | Natural Language | Genie queries, agent conversations |
| **NLP** | Natural Language Processing | Text analysis ML |
| **OLTP** | Online Transaction Processing | Lakebase PostgreSQL pattern |
| **PII** | Personally Identifiable Information | Data classification tag |
| **PK** | Primary Key | Uniqueness constraint |
| **PRD** | Product Requirements Document | Frontend design specifications |
| **REST** | Representational State Transfer | API architectural style |
| **RBAC** | Role-Based Access Control | Authorization pattern |
| **RTO** | Recovery Time Objective | Disaster recovery metric |
| **RPO** | Recovery Point Objective | Data loss tolerance |
| **SCD** | Slowly Changing Dimension | Historical tracking pattern |
| **SDK** | Software Development Kit | Client libraries |
| **SKU** | Stock Keeping Unit | Databricks pricing category |
| **SLA** | Service Level Agreement | Performance commitment |
| **SMTP** | Simple Mail Transfer Protocol | Email delivery |
| **SQL** | Structured Query Language | Database query language |
| **SSO** | Single Sign-On | Authentication method |
| **SUS** | System Usability Scale | UX survey instrument |
| **TVF** | Table-Valued Function | Parameterized SQL function |
| **UC** | Unity Catalog | Databricks governance layer |
| **UI** | User Interface | Frontend application |
| **UUID** | Universally Unique Identifier | ID generation pattern |
| **UX** | User Experience | Design and usability |
| **WCAG** | Web Content Accessibility Guidelines | Accessibility standard |
| **YAML** | YAML Ain't Markup Language | Configuration file format |

---

## Domain-Specific Vocabulary

### Cost Intelligence Domain

| Term | Definition |
|------|------------|
| **DBU Attribution** | Assigning DBU costs to workspaces, users, or tags |
| **Cost Spike** | Unexpected increase in spend detected via anomaly ML |
| **Commitment Discount** | Reserved capacity pricing (planned savings) |
| **Chargeback** | Allocating costs back to business units |
| **FinOps** | Financial operations for cloud cost management |

### Security Domain

| Term | Definition |
|------|------------|
| **Audit Event** | Logged action in `system.access.audit` table |
| **Failed Auth** | Authentication attempt that was rejected |
| **Access Anomaly** | Unusual access pattern detected via ML |
| **Breach Risk** | ML-scored likelihood of security incident |
| **Compliance** | Adherence to security policies and regulations |

### Performance Domain

| Term | Definition |
|------|------------|
| **Job Failure** | Job run with `result_state = 'FAILED'` |
| **Duration Prediction** | ML forecast of job runtime |
| **Bottleneck** | Resource constraint limiting performance |
| **Query Optimization** | SQL rewriting for improved performance |
| **P95 Latency** | 95th percentile response time |

### Reliability Domain

| Term | Definition |
|------|------------|
| **SLA Breach** | Job exceeding defined success criteria |
| **Uptime** | Percentage of time system is operational |
| **Incident** | Unplanned interruption or degradation |
| **MTTR** | Mean time to resolution for incidents |
| **Runbook** | Standard operating procedure for operations |

### Data Quality Domain

| Term | Definition |
|------|------------|
| **Expectation Failure** | DLT quality check violation |
| **Freshness** | Time since last data update |
| **Drift** | Statistical change in data distribution |
| **Quarantine** | Isolated invalid records for investigation |
| **Validation Rule** | Data quality check definition |

### MLOps Domain

| Term | Definition |
|------|------------|
| **Model Drift** | Degradation in model accuracy over time |
| **Feature Engineering** | Transformation of raw data to model inputs |
| **Batch Inference** | Scheduled predictions on large datasets |
| **Real-Time Inference** | Synchronous predictions via API |
| **Model Registry** | Centralized model versioning (Unity Catalog) |

---

## Databricks-Specific Terms

### Platform Features

| Term | Definition |
|------|------------|
| **Workspace** | Databricks environment for teams/projects |
| **Notebook** | Interactive document with code, text, visualizations |
| **Cluster** | Set of VMs for distributed computing |
| **Serverless** | Managed compute with auto-scaling |
| **Photon** | Vectorized query engine |
| **Repos** | Git integration for version control |
| **Jobs** | Scheduled execution of notebooks/tasks |
| **DLT** | Delta Live Tables streaming ETL |
| **Model Serving** | ML inference endpoints |
| **Genie** | Natural language SQL interface |
| **Lakebase** | PostgreSQL for Databricks Apps |

### Unity Catalog Terms

| Term | Definition |
|------|------------|
| **Metastore** | Top-level container for metadata |
| **Catalog** | Container for schemas (databases) |
| **Schema** | Container for tables, views, functions |
| **Managed Table** | Unity Catalog controls storage lifecycle |
| **External Table** | User manages storage location |
| **Volume** | File storage in Unity Catalog |
| **Lineage** | Data flow tracking |
| **Data Classification** | PII and sensitivity tagging |

### SQL Terms

| Term | Definition |
|------|------------|
| **MERGE** | Upsert command (UPDATE + INSERT) |
| **CLUSTER BY** | Data layout optimization |
| **COMMENT** | Metadata description |
| **TBLPROPERTIES** | Table configuration key-value pairs |
| **CONSTRAINT** | Data integrity rule (PK, FK, NOT NULL) |
| **CTE** | Common Table Expression (WITH clause) |
| **Window Function** | Calculation across row sets |
| **PIVOT** | Rotate rows to columns |

---

## Architecture Patterns

### Design Patterns

| Pattern | Definition |
|---------|------------|
| **Medallion** | Bronze → Silver → Gold quality progression |
| **Semantic Layer First** | Consumption via abstractions, not direct tables |
| **Config-Driven** | Behavior defined in YAML, not hardcoded |
| **Domain-Driven Design** | Organization by business domain (7 domains) |
| **Hierarchical Jobs** | 3-layer job architecture (Atomic/Composite/Orchestrator) |
| **YAML-Driven Schemas** | Tables created from YAML definitions |
| **Agent Domain Framework** | Artifacts tagged by AI agent domain |
| **Dual-Purpose Comments** | Metadata for humans and LLMs |

### ML Patterns

| Pattern | Definition |
|---------|------------|
| **Feature Engineering** | Centralized features in Unity Catalog |
| **Experiment Tracking** | MLflow logging of training runs |
| **Model Registry** | Versioned models in Unity Catalog |
| **Batch Inference** | `fe.score_batch()` for scheduled predictions |
| **Real-Time Serving** | Serverless endpoints for API inference |
| **Model Monitoring** | Drift detection and retraining triggers |

---

## Common Abbreviations

### File Extensions

| Extension | File Type |
|-----------|-----------|
| `.py` | Python script |
| `.sql` | SQL script |
| `.yaml` / `.yml` | YAML configuration |
| `.json` | JSON data |
| `.md` | Markdown documentation |
| `.txt` | Plain text |
| `.csv` | Comma-separated values |
| `.parquet` | Columnar data format (Delta uses internally) |

### Naming Conventions

| Pattern | Example | Usage |
|---------|---------|-------|
| `snake_case` | `fact_usage` | Tables, columns, functions |
| `kebab-case` | `cost-agent` | File names, URLs |
| `PascalCase` | `CostAgent` | Python classes (rare in project) |
| `SCREAMING_SNAKE_CASE` | `MAX_RETRIES` | Constants |
| `${var.name}` | `${var.catalog}` | DAB variable references |
| `dim_*` | `dim_workspace` | Dimension tables |
| `fact_*` | `fact_usage` | Fact tables |
| `get_*` | `get_daily_cost_summary` | TVF query functions |
| `*_profile_metrics` | `fact_usage_profile_metrics` | Lakehouse Monitoring output |

---

## Units of Measure

### Time

| Unit | Abbreviation | Context |
|------|-------------|---------|
| **Milliseconds** | ms | API latency, query performance |
| **Seconds** | s | Job duration, response time |
| **Minutes** | min | Pipeline duration |
| **Hours** | h | Job runtime, data freshness |
| **Days** | d | Data retention, trend analysis |

### Data Size

| Unit | Size | Context |
|------|------|---------|
| **KB (Kilobyte)** | 1,024 bytes | Small files |
| **MB (Megabyte)** | 1,024 KB | Medium files |
| **GB (Gigabyte)** | 1,024 MB | Large tables |
| **TB (Terabyte)** | 1,024 GB | Enterprise data lakes |
| **PB (Petabyte)** | 1,024 TB | Very large deployments |

### Compute

| Unit | Definition | Context |
|------|------------|---------|
| **DBU** | Databricks Unit | Compute pricing unit (varies by SKU) |
| **vCPU** | Virtual CPU | Cluster sizing |
| **RAM** | Memory | Cluster sizing (GB) |
| **IOPS** | I/O Operations Per Second | Storage performance |

---

## See Also

- [Appendix A: Technology Stack](A-technology-stack.md) - Complete technology inventory
- [Databricks Glossary](https://docs.databricks.com/lakehouse/glossary.html) - Official Databricks terms
- [Delta Lake Glossary](https://docs.delta.io/latest/delta-intro.html) - Official Delta terms
- [MLflow Glossary](https://mlflow.org/docs/latest/glossary.html) - Official MLflow terms

---

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Contributions:** Submit PRs to add missing terms

