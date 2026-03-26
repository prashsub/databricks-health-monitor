# Databricks Health Monitor

**Production-ready AI-powered observability platform for Databricks with intelligent cost, performance, reliability, security, and quality monitoring.**

[![Databricks](https://img.shields.io/badge/Databricks-Asset_Bundles-FF3621?logo=databricks)](https://docs.databricks.com/dev-tools/bundles/)
[![Unity Catalog](https://img.shields.io/badge/Unity_Catalog-Required-blue)](https://docs.databricks.com/data-governance/unity-catalog/)
[![Delta Lake](https://img.shields.io/badge/Delta_Lake-Native-00ADD8)](https://delta.io/)
[![MLflow](https://img.shields.io/badge/MLflow-3.0-0194E2)](https://mlflow.org/)

---

## 🎯 Overview

The Databricks Health Monitor is a **comprehensive, production-ready observability platform** that transforms Databricks system tables into actionable insights through:

- **🥉 Bronze Layer**: Streaming ingestion of 35 system tables via DLT pipelines
- **🥇 Gold Layer**: 38-table dimensional model (star schema) optimized for analytics
- **🤖 ML Framework**: 25+ ML models for prediction, anomaly detection, and optimization
- **💬 Semantic Layer**: Natural language querying via 6 Genie Spaces (60 TVFs, 10 Metric Views)
- **📊 Dashboards**: Unified AI/BI dashboard with 12 domain-specific tabs
- **🔔 Alerting**: Config-driven SQL alerting with automated deployment
- **🔍 Monitoring**: 8 Lakehouse monitors tracking 210+ custom metrics
- **🤝 GenAI Agents**: LangGraph-based multi-agent system with Lakebase memory

**Key Differentiators:**
- ✅ **Production-Ready**: Deployed via Databricks Asset Bundles with CI/CD patterns
- ✅ **AI-Native**: Natural language queries, ML-powered insights, GenAI agent orchestration
- ✅ **Enterprise-Scale**: Handles petabyte-scale workloads with serverless compute
- ✅ **Cost-Optimized**: Real-time cost intelligence and FinOps automation
- ✅ **Security-First**: Comprehensive audit trails and compliance monitoring

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Databricks System Tables (35)                        │
└──────────────────────┬──────────────────────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────────────────┐
         │   🥉 Bronze Layer (system_bronze)   │
         │  ✅ 8 DLT Streaming Pipelines       │
         │  ✅ 27 streaming tables             │
         │  ✅ 8 non-streaming tables (MERGE)  │
         └──────────────┬──────────────────────┘
                        │
                        ▼
         ┌─────────────────────────────────────┐
         │     🥇 Gold Layer (system_gold)     │
         │  ✅ 38 dimensional tables           │
         │     • 23 dimensions (SCD Type 1/2)  │
         │     • 15 facts (transactional)      │
         └──────────────┬──────────────────────┘
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
      ┌──────────┐           ┌──────────┐
      │ 🤖 ML    │           │ 🔍 Lake  │
      │ Models   │           │house Mon │
      ├──────────┤           ├──────────┤
      │ 25 models│           │8 monitors│
      │ 5 domains│           │210 metric│
      │ Auto inf.│           │Profile   │
      │          │           │& Drift   │
      └─────┬────┘           └────┬─────┘
            │                     │
            └──────────┬──────────┘
                       │
        ┌──────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ 💬 Genie │  │ 📊 AI/BI │  │ 🔔 Alert │  │ 🤝 Agent │
  │ Spaces   │  │Dashboard │  │Framework │  │Framework │
  ├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤
  │ 6 spaces │  │ 12 tabs  │  │ 60+ SQL  │  │LangGraph │
  │ 60 TVFs  │  │ 65+ wdgt │  │ alerts   │  │5 workers │
  │ 10 MVs   │  │ Unified  │  │ Config   │  │Lakebase  │
  └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

### Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Orchestration** | Databricks Asset Bundles, Workflows |
| **Ingestion** | Delta Live Tables, Auto Loader |
| **Storage** | Delta Lake, Unity Catalog |
| **Transformation** | PySpark, SQL |
| **ML** | MLflow 3.0, scikit-learn, XGBoost |
| **Semantic Layer** | Genie Spaces, Metric Views, TVFs |
| **Monitoring** | Lakehouse Monitoring, SQL Alerts |
| **AI Agents** | LangGraph, Claude Sonnet 4.5, Lakebase |
| **Dashboards** | Databricks AI/BI (Lakeview) |

---

## 📊 Feature Matrix

### By Agent Domain

| Domain | Gold Tables | ML Models | TVFs | Metric Views | Genie Space | Dashboard Tabs |
|--------|-------------|-----------|------|--------------|-------------|----------------|
| 💰 **Cost** | 4 | 6 | 15 | 2 | ✅ | 3 |
| 🔄 **Reliability** | 6 | 5 | 12 | 1 | ✅ | 2 |
| ⚡ **Performance** | 6 | 7 | 16 | 3 | ✅ | 3 |
| 🔒 **Security** | 7 | 4 | 10 | 2 | ✅ | 2 |
| ✅ **Quality** | 14 | 3 | 7 | 2 | ✅ | 1 |
| 🌐 **Unified** | 38 | 25 | 60 | 10 | ✅ | 1 |
| **Totals** | **38** | **25** | **60** | **10** | **6** | **12** |

---

## 🚀 Quick Start

### Prerequisites

- **Databricks Workspace**: Unity Catalog enabled
- **Permissions**: Account admin, metastore admin
- **CLI**: Databricks CLI v0.213+ installed
- **Compute**: SQL Warehouse (serverless recommended)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/prashanth-subrahmanyam_data/databricks-health-monitor.git
cd databricks-health-monitor

# 2. Configure bundle
# Edit databricks.yml:
#   - catalog: your_catalog
#   - warehouse_id: your_warehouse_id

# 3. Validate configuration
databricks bundle validate

# 4. Deploy to dev environment
databricks bundle deploy -t dev

# 5. Run master setup orchestrator (first-time only)
databricks bundle run -t dev master_setup_orchestrator

# 6. Run master refresh orchestrator (daily)
databricks bundle run -t dev master_refresh_orchestrator
```

### What Gets Deployed

| Component | Resources | Description |
|-----------|-----------|-------------|
| **Bronze Layer** | 8 DLT pipelines, 2 jobs | Ingests 35 system tables |
| **Gold Layer** | 1 setup job, 1 refresh job | Creates/updates 38 dimensional tables |
| **Semantic Layer** | 2 deployment jobs | Deploys 60 TVFs, 10 Metric Views |
| **ML Framework** | 3 pipelines | Feature engineering, training, inference |
| **Genie Spaces** | 1 validation job | Validates 6 Genie Space configurations |
| **Dashboards** | 1 deployment job | Deploys unified dashboard (12 tabs) |
| **Lakehouse Monitoring** | 1 setup job | Creates 8 monitors with custom metrics |
| **Alerting** | 6 jobs | Deploys 60+ SQL alerts |
| **Agent Framework** | 2 jobs | Deploys GenAI agent system |

---

## 📚 Documentation

### For Users

| Guide | Purpose | Path |
|-------|---------|------|
| **Quick Start** | Get up and running in 15 minutes | [`QUICKSTART.md`](QUICKSTART.md) |
| **Genie Spaces Guide** | Natural language querying | [`docs/deployment/genie-spaces/`](docs/deployment/genie-spaces/) |
| **Dashboard Guide** | Using the AI/BI dashboard | [`docs/dashboard-framework-design/`](docs/dashboard-framework-design/) |
| **Alerting Guide** | Configuring SQL alerts | [`docs/alerting-framework-design/`](docs/alerting-framework-design/) |
| **Deployed Assets** | Inventory of all deployed assets | [`docs/actual-assets.md`](docs/actual-assets.md) |

### For Developers

| Guide | Purpose | Path |
|-------|---------|------|
| **Gold Layer Design** | Dimensional model ERDs | [`gold_layer_design/erd/`](gold_layer_design/erd/) |
| **ML Framework** | Training and inference | [`docs/ml-framework-design/`](docs/ml-framework-design/) |
| **Agent Framework** | GenAI agent architecture | [`docs/agent-framework-design/`](docs/agent-framework-design/) |
| **Semantic Layer** | TVFs, Metric Views, Genie | [`docs/semantic-framework/`](docs/semantic-framework/) |
| **Lakehouse Monitoring** | Custom metrics patterns | [`docs/lakehouse-monitoring-design/`](docs/lakehouse-monitoring-design/) |
| **Troubleshooting** | Debug sessions and fix reports | [`docs/troubleshooting/`](docs/troubleshooting/) |

### Architecture & Reference

- **System Architecture**: [`docs/architecture/`](docs/architecture/)
- **Project Architecture Design**: [`docs/project-architecture-design/`](docs/project-architecture-design/)
- **Master ERD**: [`gold_layer_design/erd/00_master_erd.md`](gold_layer_design/erd/00_master_erd.md)
- **Agent Implementation**: [`docs/agent-framework-design/actual-implementation/`](docs/agent-framework-design/actual-implementation/)
- **Deployment History**: [`docs/deployment/deployment-history/`](docs/deployment/deployment-history/)
- **Reference & Inventories**: [`docs/reference/`](docs/reference/)

---

## 🤖 ML Models (25)

### Cost Intelligence (6 models)

| Model | Purpose | Output Table |
|-------|---------|--------------|
| `cost_anomaly_detector` | Detect unusual spending patterns | `cost_anomaly_predictions` |
| `budget_forecaster` | Forecast monthly costs | `cost_forecast_predictions` |
| `job_cost_optimizer` | Recommend cluster optimizations | `migration_recommendations` |
| `tag_recommender` | Auto-tag resources | `tag_recommendations` |
| `commitment_recommender` | Optimize commit usage | `budget_alert_predictions` |
| `chargeback_attribution` | User/team cost allocation | — |

### Reliability (5 models)

| Model | Purpose | Output Table |
|-------|---------|--------------|
| `job_failure_predictor` | Predict job failures | `job_failure_predictions` |
| `job_duration_forecaster` | Forecast job durations | `job_duration_predictions` |
| `sla_breach_predictor` | Predict SLA violations | `sla_breach_predictions` |
| `pipeline_health_scorer` | Score DLT pipeline health | `pipeline_health_predictions` |
| `retry_success_predictor` | Predict retry outcomes | `retry_success_predictions` |

### Performance (7 models)

| Model | Purpose | Output Table |
|-------|---------|--------------|
| `query_performance_forecaster` | Predict query durations | `query_optimization_recommendations` |
| `warehouse_optimizer` | Optimize warehouse sizing | `cluster_capacity_recommendations` |
| `cache_hit_predictor` | Predict cache effectiveness | `cache_hit_predictions` |
| `query_optimization_recommender` | Recommend query optimizations | `query_optimization_classifications` |
| `cluster_sizing_recommender` | Right-size clusters | `cluster_rightsizing_recommendations` |
| `cluster_capacity_planner` | Plan capacity needs | `cluster_capacity_recommendations` |
| `regression_detector` | Detect performance regressions | — |

### Security (4 models)

| Model | Purpose | Output Table |
|-------|---------|--------------|
| `security_threat_detector` | Detect unusual access patterns | `access_anomaly_predictions` |
| `user_behavior_baseline` | Baseline normal behavior | `access_classifications` |
| `compliance_risk_classifier` | Score compliance risks | `user_risk_scores` |
| `privilege_escalation` | Detect permission escalations | — |

### Quality (3 models)

| Model | Purpose | Output Table |
|-------|---------|--------------|
| `data_drift_detector` | Detect data quality drift | `quality_anomaly_predictions` |
| `schema_change_predictor` | Predict schema changes | `quality_trend_predictions` |
| `freshness_predictor` | Predict stale data | `freshness_alert_predictions` |

---

## 💬 Genie Spaces (6)

Natural language interfaces for querying platform health without SQL.

| Genie Space | Purpose | Sample Questions |
|-------------|---------|------------------|
| **Cost Intelligence** | FinOps and billing analytics | "What's our total spend this month?" |
| **Job Health Monitor** | Job reliability tracking | "Show me failed jobs today" |
| **Performance** | Query + cluster performance | "Which queries are slow?" |
| **Security Auditor** | Audit and compliance | "Who accessed sensitive data?" |
| **Data Quality Monitor** | Freshness and quality | "Which tables are stale?" |
| **Unified Health Monitor** | All domains combined | "What's the overall platform health?" |

**Assets per Space:**
- 60 Table-Valued Functions (TVFs)
- 10 Metric Views
- 25 ML prediction tables
- 16 Lakehouse Monitoring tables

---

## 📊 Unified Dashboard

**Single dashboard with 12 tabs** providing comprehensive observability:

### Cost Tabs (3)

1. **Executive Overview** - Leadership KPIs (cost, success rate, users)
2. **Cost Management** - FinOps analysis (contributors, WoW, tags)
3. **Commit Tracking** - Budget vs actual spend

### Reliability Tabs (2)

4. **Job Reliability** - Job success rates and failures
5. **Job Optimization** - Autoscaling, stale datasets, outliers

### Performance Tabs (3)

6. **Query Performance** - Slow queries, warehouse utilization
7. **Cluster Utilization** - CPU/memory efficiency, right-sizing
8. **DBR Migration** - Legacy runtime tracking, serverless adoption

### Security Tabs (2)

9. **Security Audit** - User activity, sensitive actions
10. **Governance Hub** - Lineage, tags, inactive tables

### Quality Tabs (1)

11. **Table Health** - Storage health, compaction needs

### Global (1)

12. **Filters** - Cross-tab workspace and date filtering

---

## 🔔 Alerting Framework

**Config-driven SQL alerting** with automated deployment and validation.

### Features

- ✅ **60+ pre-configured alerts** across all domains
- ✅ **Hierarchical job architecture** for staged deployments
- ✅ **Query validation** before deployment
- ✅ **Template-based alert creation** for consistency
- ✅ **Notification destination sync** with external systems
- ✅ **Partial success patterns** for resilient deployments

### Alert Categories

| Category | Alert Count | Examples |
|----------|-------------|----------|
| **Cost** | 12 | Budget overrun, cost anomalies, untagged resources |
| **Reliability** | 15 | Job failures, SLA breaches, long-running jobs |
| **Performance** | 18 | Slow queries, underutilized clusters, high spill |
| **Security** | 10 | Off-hours access, sensitive data access, permission changes |
| **Quality** | 5 | Stale data, quality violations, schema drift |

---

## 🤝 GenAI Agent Framework

**Production-ready multi-agent system** using LangGraph for intelligent troubleshooting.

### Architecture

- **Orchestrator**: Intent classification and routing
- **5 Worker Agents**: Cost, Performance, Reliability, Security, Quality
- **Memory System**: Lakebase-backed conversation history
- **Tracing**: MLflow tracing for observability
- **Evaluation**: LLM-as-judge with automated scoring

### Features

- ✅ **Natural language querying** via Claude Sonnet 4.5
- ✅ **Genie Space integration** for data retrieval
- ✅ **40+ tools** for SQL, ML, and actions
- ✅ **Production monitoring** via inference tables
- ✅ **Review App** for stakeholder feedback
- ✅ **OBO authentication** for multi-user scenarios

### Deployment

Deployed via Agent Framework `agents.deploy()` with:
- Real-time tracing
- Inference tables
- Review App
- Automatic scaling

---

## 🔍 Lakehouse Monitoring

**8 monitors** tracking 210+ custom metrics across all domains.

| Monitor | Table | Custom Metrics | Purpose |
|---------|-------|----------------|---------|
| **Cost** | `fact_usage` | 38 | Spend trends, anomalies, forecasts |
| **Job** | `fact_job_run_timeline` | 35 | Success rates, durations, retries |
| **Query** | `fact_query_history` | 28 | Query performance, efficiency |
| **Cluster** | `fact_node_timeline` | 24 | Resource utilization, efficiency |
| **Security** | `fact_audit_logs` | 32 | Access patterns, anomalies |
| **Quality** | Multiple tables | 28 | Freshness, quality, drift |
| **Governance** | Multiple tables | 15 | Lineage, tags, activity |
| **Inference** | `fact_endpoint_usage` | 10 | Model serving metrics |

---

## 🗂️ Project Structure

```
databricks-health-monitor/
├── databricks.yml                    # Bundle configuration
├── README.md                         # This file
├── QUICKSTART.md                     # Quick start guide
│
├── src/                              # Source code
│   ├── pipelines/                    # Bronze/Gold layer
│   │   ├── bronze/                   # 15 DLT notebooks
│   │   └── gold/                     # 15 merge scripts
│   ├── semantic/                     # Semantic layer
│   │   ├── metric_views/             # 10 YAML configs
│   │   └── tvfs/                     # 6 SQL files
│   ├── genie/                        # 6 Genie Space exports
│   ├── ml/                           # 25 ML training scripts
│   │   ├── cost/, performance/, reliability/, security/, quality/
│   │   ├── features/, inference/, deployment/
│   │   └── common/                   # Shared utilities
│   ├── monitoring/                   # 12 monitor setup scripts
│   ├── alerting/                     # 10 alerting scripts
│   ├── dashboards/                   # 12 dashboard components
│   └── agents/                       # GenAI agent framework
│       ├── orchestrator/             # LangGraph workflow
│       ├── workers/                  # 5 domain agents
│       ├── memory/                   # Lakebase integration
│       ├── evaluation/               # LLM-as-judge
│       └── setup/                    # Deployment scripts
│
├── resources/                        # Asset Bundle resources
│   ├── pipelines/bronze/             # 8 DLT pipeline YAMLs
│   ├── pipelines/gold/               # 3 job YAMLs
│   ├── semantic/                     # 3 deployment jobs
│   ├── genie/                        # 2 validation jobs
│   ├── ml/                           # 3 pipeline YAMLs
│   ├── monitoring/                   # 1 setup job
│   ├── alerting/                     # 6 job YAMLs
│   ├── dashboards/                   # 2 deployment jobs
│   ├── agents/                       # 2 agent jobs
│   └── orchestrators/                # 2 master orchestrators
│
├── docs/                             # Comprehensive documentation
│   ├── gold/                         # Gold layer lineage, progress
│   ├── ml-framework-design/          # ML architecture (10 chapters)
│   ├── semantic-framework/           # Semantic layer guide (27 docs)
│   ├── lakehouse-monitoring-design/  # Monitor catalog (11 docs)
│   ├── alerting-framework-design/    # Alert patterns (12 chapters)
│   ├── agent-framework-design/       # Agent architecture (51 docs)
│   ├── dashboard-framework-design/   # Dashboard specs (32 docs)
│   ├── frontend-framework-design/    # Figma designs (40 docs)
│   ├── deployment/                   # Deployment guides (43 docs)
│   ├── reference/                    # Reference materials (60 docs)
│   └── enterprise_golden_rules/      # Best practices (32 docs)
│
├── gold_layer_design/                # Dimensional modeling
│   ├── erd/                          # 14 ERD diagrams
│   ├── yaml/                         # 37 YAML schemas
│   └── design/                       # Design documentation
│
├── scripts/                          # Utility scripts (139 files)
│   ├── Validation, deployment, migration scripts
│   └── Data generation utilities
│
├── tests/                            # Test suite
│   ├── alerting/, dashboards/, genie/, metric_views/
│   ├── ml/, monitoring/, optimizer/, pipelines/, tvfs/
│   └── fixtures/                     # Test data
│
├── context/                          # Reference materials
│   ├── branding/                     # 600+ SVG icons, colors
│   ├── prompts/                      # Agent prompts (63 files)
│   └── systemtables/                 # System table schemas
│
└── .cursor/rules/                    # AI-assisted dev patterns (42 rules)
    ├── admin/, bronze/, common/, gold/, ml/
    ├── monitoring/, semantic-layer/, silver/
    ├── exploration/, planning/, front-end/
    └── genai-agents/
```

---

## 🎯 Use Cases

### For FinOps Teams

- **Cost Intelligence**: Real-time spend tracking, anomaly detection, forecasting
- **Budget Management**: Commit tracking, chargeback, tag coverage
- **Optimization**: Right-sizing recommendations, migration opportunities

### For Platform Engineers

- **Performance Monitoring**: Query and cluster optimization
- **Capacity Planning**: Resource utilization, forecasting
- **DBR Migration**: Track legacy runtime adoption

### For DevOps/SREs

- **Job Reliability**: Success rates, failure prediction, retry analysis
- **SLA Compliance**: Track and predict SLA breaches
- **Pipeline Health**: DLT pipeline monitoring and scoring

### For Security/Compliance

- **Audit Trails**: Complete activity tracking across all workspaces
- **Threat Detection**: Anomalous access patterns, privilege escalation
- **Compliance Reporting**: Permission changes, sensitive data access

### For Data Governance

- **Data Quality**: Freshness, drift detection, quality violations
- **Lineage**: Column and table-level lineage tracking
- **Asset Management**: Tag coverage, inactive tables, storage optimization

### For Executives

- **Executive Dashboard**: Single-pane-of-glass platform health view
- **Natural Language Queries**: Ask questions in plain English via Genie
- **AI-Powered Insights**: ML-driven recommendations and predictions

---

## 🔧 Configuration

### Bundle Variables

Edit `databricks.yml` to configure:

```yaml
variables:
  catalog: your_catalog                           # Unity Catalog
  warehouse_id: "your_warehouse_id"               # SQL Warehouse
  dashboard_folder: "/Shared/health_monitor"      # Dashboard location
  
  # Genie Space IDs (after creating spaces in UI)
  cost_genie_space_id: "01..."
  performance_genie_space_id: "01..."
  reliability_genie_space_id: "01..."
  security_genie_space_id: "01..."
  quality_genie_space_id: "01..."
  unified_genie_space_id: "01..."
```

### Notification Destinations

Update email addresses in:
- `src/alerting/alerting_config.py` - Alert notification recipients
- `resources/**/*.yml` - Job failure notifications

---

## 📈 Monitoring & Operations

### Check Deployment Status

```sql
-- Check job runs
SELECT * FROM system.lakeflow.job_run_timeline
WHERE job_name LIKE '%health_monitor%'
ORDER BY period_start_time DESC;

-- Check table counts
SELECT COUNT(*) as table_count
FROM system.information_schema.tables
WHERE table_catalog = 'your_catalog'
  AND table_schema = 'system_gold';

-- Check Genie Space status
-- Visit: https://<workspace>.databricks.com/genie/spaces
```

### Daily Operations

1. **Master Refresh Orchestrator** runs nightly (2 AM UTC)
   - Bronze ingestion
   - Gold transformations
   - ML inference
   - Monitor refresh

2. **Alerts** check thresholds every 15-60 minutes

3. **Dashboards** refresh on query (live data)

4. **Genie Spaces** query live data

---

## 🧪 Testing

Comprehensive test suite covering all components:

```bash
# Run all tests
pytest tests/

# Run specific domain tests
pytest tests/alerting/
pytest tests/dashboards/
pytest tests/genie/
pytest tests/ml/
pytest tests/monitoring/
```

Test coverage:
- ✅ Bronze → Gold lineage validation
- ✅ SQL query validation (alerts, TVFs, dashboards)
- ✅ Dashboard widget encoding validation
- ✅ Genie Space benchmark SQL validation
- ✅ ML model prediction schema validation
- ✅ Monitor custom metric validation

---

## 🚦 Deployment Stages

### Stage 1: Bronze Layer (Week 1)

```bash
databricks bundle deploy -t dev
databricks bundle run -t dev bronze_setup_job
databricks bundle run -t dev bronze_streaming_pipeline
```

### Stage 2: Gold Layer (Weeks 2-3)

```bash
databricks bundle run -t dev gold_setup_job
databricks bundle run -t dev gold_merge_job
```

### Stage 3: Semantic Layer (Week 4)

```bash
databricks bundle run -t dev tvf_deployment_job
databricks bundle run -t dev metric_view_deployment_job
# Create Genie Spaces manually in UI
```

### Stage 4: ML & Monitoring (Weeks 5-6)

```bash
databricks bundle run -t dev ml_feature_pipeline
databricks bundle run -t dev ml_training_pipeline
databricks bundle run -t dev lakehouse_monitors_job
```

### Stage 5: Dashboards & Alerts (Week 7)

```bash
databricks bundle run -t dev dashboard_deployment_job
databricks bundle run -t dev alerting_setup_orchestrator_job
```

### Stage 6: Agent Framework (Week 8)

```bash
databricks bundle run -t dev agent_setup_job
databricks bundle run -t dev agent_deployment_job
```

---

## 🔒 Security & Compliance

### Data Classification

All tables tagged with:
- `data_classification`: `confidential` or `internal`
- `contains_pii`: `true` or `false`
- `business_owner`, `technical_owner`

### Access Control

- **Bronze/Gold**: Read access via UC grants
- **ML Models**: Restricted to ML team
- **Genie Spaces**: User-based access control
- **Dashboards**: Workspace-level permissions
- **Alerts**: Admin-only configuration

### Audit Trails

Complete audit logging via:
- `fact_audit_logs` - All user actions
- `fact_table_lineage` - Data access patterns
- ML inference tables - Agent query history

---

## 🛠️ Troubleshooting

### Common Issues

**Issue: Bronze pipeline fails**
```bash
# Check DLT pipeline event logs
# Common cause: Schema evolution
# Solution: Already handled via schema evolution settings
```

**Issue: Gold merge fails with duplicate keys**
```bash
# Check deduplication logic in merge_*.py scripts
# All scripts use mandatory deduplication pattern
```

**Issue: Genie Space returns "no results"**
```bash
# Verify TVFs are deployed:
SHOW USER FUNCTIONS IN your_catalog.system_gold;

# Verify Metric Views are registered:
SELECT * FROM system.lakeflow.metric_views
WHERE catalog_name = 'your_catalog';
```

**Issue: ML inference fails**
```bash
# Check model registration:
SELECT * FROM your_catalog.system_gold_ml.registered_models;

# Check feature tables exist:
SHOW TABLES IN your_catalog.system_gold_ml;
```

**Issue: Alerts not firing**
```bash
# Check alert configuration:
SELECT * FROM your_catalog.system_gold.alert_config;

# Check alert query execution:
SELECT * FROM system.query.history
WHERE statement_text LIKE '%alert_query%';
```

---

## 📖 Learning Resources

### Databricks Documentation

- [System Tables](https://docs.databricks.com/admin/system-tables/)
- [Delta Live Tables](https://docs.databricks.com/delta-live-tables/)
- [Asset Bundles](https://docs.databricks.com/dev-tools/bundles/)
- [Unity Catalog](https://docs.databricks.com/data-governance/unity-catalog/)
- [Genie Spaces](https://docs.databricks.com/genie/)
- [AI/BI Dashboards](https://docs.databricks.com/visualizations/lakeview)
- [Lakehouse Monitoring](https://docs.databricks.com/lakehouse-monitoring/)
- [Agent Framework](https://docs.databricks.com/generative-ai/agent-framework/)

### Internal Documentation

- **Cursor Rules**: `.cursor/rules/` - AI-assisted development patterns
- **Reference Docs**: `docs/reference/` - Inventories, rule improvements, and technical references
- **Deployment History**: `docs/deployment/deployment-history/` - Historical deployment session logs
- **Operations**: `docs/operations/` - Operational runbooks and procedures
- **Development**: `docs/development/` - Development setup and roadmap

---

## 🤝 Contributing

### Development Workflow

1. **Create feature branch**: `git checkout -b feature/your-feature`
2. **Follow patterns**: Reference `.cursor/rules/` for standards
3. **Test thoroughly**: Add tests to `tests/`
4. **Document changes**: Update relevant docs in `docs/`
5. **Validate bundle**: `databricks bundle validate`
6. **Create PR**: Submit for review

### Code Standards

- **Python**: PEP 8, type hints, docstrings
- **SQL**: Qualified table names, consistent formatting
- **YAML**: Asset Bundle best practices
- **Documentation**: Markdown with clear examples

---

## 📝 Changelog

See [scratchpad/change_log.md](scratchpad/change_log.md) for detailed version history.

**Recent Major Updates:**
- **2026-01-26**: Agent Framework deployment refactor using `agents.deploy()`
- **2026-01-26**: Lakebase memory verification and initialization tools
- **2026-01-26**: OBO authentication patterns for multi-user scenarios
- **2025-12-20**: Complete Genie Space validation framework
- **2025-12-19**: Unified dashboard with 12 tabs
- **2025-12-18**: Alerting framework with hierarchical jobs
- **2025-12-15**: Gold layer complete (38 tables)
- **2025-12-10**: ML framework with 25 models
- **2025-12-05**: Bronze layer complete (35 tables)

---

## 📊 Project Statistics

| Metric | Count |
|--------|-------|
| **Code Files** | 300+ Python, 40+ SQL, 30+ YAML |
| **Documentation** | 493 Markdown files |
| **Test Coverage** | 25+ test modules |
| **Gold Tables** | 38 dimensional tables |
| **ML Models** | 25 production models |
| **TVFs** | 60 table-valued functions |
| **Metric Views** | 10 semantic views |
| **Genie Spaces** | 6 natural language interfaces |
| **Dashboard Widgets** | 65+ interactive widgets |
| **SQL Alerts** | 60+ configured alerts |
| **Lakehouse Monitors** | 8 monitors, 210+ metrics |
| **Icons/Branding** | 600+ SVG files |
| **Cursor Rules** | 42 development patterns |

---

## 📄 License

Internal use only - Platform Operations team.

**Proprietary and Confidential**

---

## 📧 Support

For questions or issues:

1. **Documentation**: Check `docs/` for comprehensive guides
2. **Troubleshooting**: See troubleshooting section above
3. **Databricks Support**: Contact your Databricks account team
4. **Internal Team**: data-engineering@company.com

---

## 🙏 Acknowledgments

Built with:
- [Databricks Platform](https://databricks.com/)
- [Delta Lake](https://delta.io/)
- [MLflow](https://mlflow.org/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [Claude AI](https://www.anthropic.com/claude)

Special thanks to the Databricks community for excellent documentation and support.

---

**🎉 Ready to transform your Databricks observability? Deploy now!**

```bash
databricks bundle deploy -t dev
databricks bundle run -t dev master_setup_orchestrator
```
