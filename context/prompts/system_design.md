You are a senior Databricks Solutions Architect and platform engineer. 

Create a COMPLETE architecture and implementation plan, structured as a set of Markdown “Plan” files (one file per major area), to be used in Cursor to build an internal Databricks App that:

- Uses **Databricks System Tables Bronze Layer** as primary data source
- Builds a **Gold Layer relational model** for platform observability
- Adds an **Analytics & ML layer** (metrics, forecasting, anomaly detection, optimization)
- Exposes everything via **GenAI agents** (Mosaic AI Agents) for:
  - Cost Monitoring & Optimization
  - Security & Governance Monitoring
  - Performance Optimization
  - Reliability / SLO & Workflow Monitoring

The app is for **internal platform monitoring only** (multi-workspace, but within one organization) and should use:

- Unity Catalog
- System Tables (access, billing, compute, lakeflow/jobs, query history, lineage, etc.)
- Delta / Medallion architecture (bronze/silver/gold)
- MLflow Model Registry
- Mosaic AI Agent Framework (tools + RAG)
- Databricks Apps (React/Next.js) **with Figma-based UI design as a starting point**

Use the following references as design inspiration and patterns (DO NOT copy code, but align with their concepts and data models):

- DBSQL Warehouse Advisor & multi-warehouse analytics
- Real-time query monitoring with alerts
- Security monitoring via system tables & audit logs
- Workflow Advisor / jobs observability
- Table Health Advisor dashboards and data models
- GitHub repos:
  - andyweaves/system-tables-audit-logs
  - CodyAustinDavis/dbsql_sme (Warehouse Advisor + Table Health)
  - yati1002/Workflowadvisor

---

## FILE STRUCTURE

Generate the plan as **separate Markdown files**, each with a clear H1 title and structured sections (Goals, Design, Implementation Steps, Deliverables, Risks).

### 00_core_setup.md — Core Infra & Data Foundation

Content to include:

- **Goals & Scope**
  - Single source of truth for platform telemetry via system tables
  - Long-term retention strategy (mirror/bronze) and medallion design

- **System Tables & Catalog Setup**
  - Enabling system tables
  - Creating an `observability` catalog / schemas
  - Permissions model (service principals, groups, row-level security via UC)

- **Ingestion & Medallion Pattern**
  - How to ingest system tables into:
    - **Bronze**: raw mirrored system tables
    - **Silver**: normalized/cleaned views
    - **Gold**: subject-area fact/dim tables per concern (cost, jobs, queries, security, reliability)
  - Use of:
    - Structured Streaming or DLT
    - DLT Sink API pattern to mirror system tables into long-retention Delta tables

- **Shared Infra**
  - Job orchestration (Databricks Workflows)
  - Cluster / SQL Warehouse strategy (serverless vs classic, scheduling)
  - Secrets, tokens, network/security considerations

- **Deliverables**
  - Concrete list of UC catalogs/schemas
  - Initial DLT/streaming pipeline skeletons
  - Checklist for “core infra ready”

---

### 01_gold_relational_model.md — Gold Layer Relational Model

Content to include:

- **Goals**
  - Define a **normalized yet analytics-friendly** relational model over system tables
  - Provide consistent, joinable entities across Cost, Security, Performance, Reliability

- **Modeling Principles**
  - Entity naming conventions
  - SCD patterns where needed (e.g., workspace/job/warehouse history)
  - Multi-workspace / multi-region considerations

- **Core Dimensions**
  - `dim_workspace`
  - `dim_user`
  - `dim_group`
  - `dim_job`
  - `dim_task`
  - `dim_cluster`
  - `dim_warehouse`
  - `dim_table` / `dim_asset` (for lineage, table health, UC objects)
  - `dim_slo` / `dim_policy` (for reliability/security definitions)

- **Core Facts**
  - `fact_cost_daily` (by workspace, job, warehouse, SKU, tags)
  - `fact_query_execution` (query-level, with SLA attributes)
  - `fact_job_run` (status, runtime, retries, associated cluster)
  - `fact_warehouse_utilization` (concurrency, scaling, runtime)
  - `fact_security_event` (derived from audit logs)
  - `fact_incident` (aggregated failures, SLO breaches)
  - `fact_table_health` (freshness, usage, size/fragmentation scores)

- **Schema Definitions**
  - For each dim/fact: table name, primary key, important columns, relationships
  - PK/FK relationships and cardinalities in words **and** as a Mermaid ERD

- **Implementation Steps**
  - How to derive each gold table from silver/system tables
  - Handling late-arriving events
  - Partitioning, clustering (e.g., Predictive Optimization, liquid clustering hints)

- **Deliverables**
  - ERD (Mermaid)
  - DDL or pseudo-DDL for gold tables
  - Mapping matrix: System Table → Silver View → Gold Fact/Dim

---

### 02_analytics_ml_layer.md — Analytics, Metrics & ML Layer

Content to include:

- **Goals**
  - Build an analytics & ML layer **on top of the Gold model**
  - Provide:
    - Metric views
    - Forecasts
    - Anomaly detection
    - Optimization/recommendation models

- **Metric Views**
  - Define **Metric Views** for:
    - Cost: daily/weekly/monthly cost by workspace, project, tag
    - Performance: P95/P99 latency, queue times, spill rates
    - Reliability: SLO attainment, MTTR, MTBF per job/warehouse/SLO
    - Security: risk scores, event counts by type/severity
    - Table Health: freshness, unused tables, hot vs cold assets
  - For each metric view:
    - Name
    - Inputs (gold facts/dims)
    - Grain (daily, hourly, per-run)
    - Example SQL

- **ML Models**
  - **Cost Forecasting**
    - Per-workspace and per-warehouse forecasting
    - Time-series model choice (e.g., Prophet/ARIMA/AutoML)
  - **Cost/Usage Anomaly Detection**
    - Residual-based or multivariate anomaly detection
  - **Right-Sizing / Performance Optimization**
    - Recommend cluster/warehouse configs (simple heuristic vs ML)
  - **Reliability / Incident Prediction**
    - Model probability of failure / SLO breach
  - **Security Risk Scoring**
    - Weighted or model-based risk scoring per workspace/project

  For each model:
  - Inputs (feature tables)
  - Targets & training strategy
  - Frequency of retrain
  - Registration in **MLflow Model Registry (UC)**

- **Feature Tables**
  - Define feature tables in a `features` schema that draw from gold facts/dims
  - Naming, primary keys, and refresh cadence
  - Example: `features_cost_workspace_daily`, `features_job_efficiency`, `features_security_surface`, `features_slo_reliability`

- **Tools for Agentic Use**
  - **SQL tools**:
    - Parameterized queries hitting metric views and gold tables
  - **ML inference tools**:
    - Functions wrapping MLflow models (e.g., `forecast_cost(workspace_id, horizon_days)`)
  - **Action tools (read/write)**:
    - Tools that can tag objects, create alerts, or write to config tables (e.g., writing new SLOs, budgets)

- **Implementation Steps**
  - How to build metric views in Databricks SQL
  - How to define feature tables and schedule refresh
  - How to train, register, and serve models (Mosaic AI Model Serving / Model Serving endpoints)
  - How to expose them as tools (high-level function signatures)

- **Deliverables**
  - List of metric views + pseudo-SQL
  - List of feature tables + schema
  - Model registry plan (names, stages)
  - Catalog of tools with their contracts (inputs/outputs)

---

### 03_agent_layer.md — Agent & RAG Layer

Content to include:

- **Goals**
  - Define the **agent architecture** that sits on top of the Analytics/ML layer
  - Provide specialized copilots for Cost, Security, Performance, Reliability
  - Provide knowledge agents for RAG over runbooks, policies, dashboards, docs

- **Agent Types**
  - Router Agent (“Platform Health Copilot”)
  - Sub-agents:
    - CostAgent
    - SecurityAgent
    - PerformanceAgent
    - ReliabilityAgent
  - KnowledgeAgent / DocsAgent for RAG over:
    - Cloud cost policies
    - Databricks platform hardening guides
    - Internal runbooks for SLOs / incident response

- **Tools & Capabilities**
  - For each sub-agent:
    - SQL tools (list specific queries / metric views)
    - ML tools (forecasts, recommendations)
    - Action tools (e.g., create SQL alert, open Jira ticket, propose DBR upgrade)
  - For KnowledgeAgent:
    - Vector search configuration (collections, chunking strategy)
    - Documents to index (internal docs + curated external docs if allowed)

- **Agent Orchestration**
  - Router logic (classification of user intent into Cost/Sec/Perf/Rel)
  - Example: Tools + instructions for each agent
  - Guardrails:
    - Scoping to user’s workspace/project
    - Read-only vs write-capable tools (and approval steps)

- **Prompt & Flow Design**
  - System prompt patterns per agent (Cost, Security, etc.)
  - Example multi-tool call flows:
    - “Explain yesterday’s cost spike in workspace X and propose savings”
    - “List top 3 security risks in workspace Y and recommend mitigations”
    - “Check if SLO for Job Z is at risk this week”
  - How agents blend:
    - e.g., ReliabilityAgent consulting KnowledgeAgent for runbook snippets

- **Implementation Steps**
  - Define tool schemas in code
  - Configure Mosaic AI Agent framework with tools & routing
  - Set up vector search index and ingestion jobs
  - Logging & monitoring of agent calls (using inference/system tables)

- **Deliverables**
  - Agent catalog (router + sub-agents + knowledge agent)
  - Tool catalog (names, IO schemas, backing SQL/models/APIs)
  - Example prompts & conversation flows

---

### 10_cost_agent.md — Cost Monitor / Optimizer Plan

For **CostAgent**, include:

- Goals & personas
- System tables → gold facts used
- Key metric views, dashboards
- Forecast, anomaly detection, optimization models
- SQL tools, ML tools, action tools
- Example prompts / flows
- Alerting & scheduling

(Same pattern for the others:)

### 11_performance_agent.md — Performance Optimizer Plan  
### 12_security_agent.md — Security & Governance Plan  
### 13_reliability_agent.md — Reliability & SLO Plan  

Each file should reuse the structure but specialize:

- Which facts/dims/metrics they use
- Which models they call
- Which actions they can take
- Specialized sample prompts

---

### 20_app_frontend_figma.md — Databricks App & Figma Integration

Content to include:

- **Goals**
  - Expose the agents & metrics in a clean internal “Platform Health” app
  - Use Figma designs as source of truth for UI layout

- **App Architecture**
  - Databricks App (React/Next.js) structure
  - Backend calls to:
    - Mosaic AI Agent endpoint
    - Metric view queries via SQL Warehouse
  - Auth & workspace scoping via UC & tokens

- **Pages & Components**
  - Overview page (health score tiles, cross-domain summary)
  - Per-agent pages (Cost, Security, Performance, Reliability)
  - Agent chat panel embedded with context selectors (workspace, time range)
  - Alert center (list alerts, link back to DBSQL Alert configs or dashboards)

- **Figma → Implementation Workflow**
  - How to:
    - Export design tokens (colors, spacing, typography)
    - Map Figma components to React components
    - Iterate Figma ↔ code changes
  - Guidance for front-end devs using Cursor

- **Integration Details**
  - How the frontend calls:
    - Agent tools (via a single Mosaic AI endpoint)
    - Metric APIs (via DBSQL REST / backend proxy)
  - Error handling & loading states
  - Telemetry of UI usage (optional)

- **Deployment**
  - As a Databricks App
  - Config needed (env vars, secrets, endpoints)
  - Roles & permissions for end users

- **Deliverables**
  - Page/component inventory
  - Data contracts between frontend and backend
  - Checklists for shipping MVP vs full version

---

## STYLE & OUTPUT REQUIREMENTS

- Output **each plan as if it is a standalone Markdown file**, with:
  - `#` H1 title
  - Clear sections: Goals, Architecture/Design, Implementation Steps, Deliverables, Risks/Tradeoffs (if any)
- Use:
  - Bullet points
  - Numbered steps
  - Code blocks for pseudo-SQL / pseudo-API
  - Mermaid where helpful (e.g., ERDs or high-level diagrams)
- Assume the audience is a **senior engineer using Cursor**: plans should be **directly actionable** and implementation-oriented.
