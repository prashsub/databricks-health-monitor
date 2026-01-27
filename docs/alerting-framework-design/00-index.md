# Alerting Framework Design Documentation

## Overview

This documentation suite provides **comprehensive architecture, implementation, and best practices** for building a **config-driven SQL alerting framework** on Databricks. The system uses Delta Lake for configuration storage, Databricks SDK for deployment, and follows enterprise patterns for reliability and maintainability.

## Design Principle

> **Alerts are defined as DATA, not CODE.**
> All alert rules live in a Delta table, not hardcoded in scripts.
> This enables runtime updates, version history, and centralized management.

## Document Index

| # | Document | Description |
|---|----------|-------------|
| 01 | [Introduction](01-introduction.md) | Purpose, scope, prerequisites, best practices matrix |
| 02 | [Architecture Overview](02-architecture-overview.md) | System architecture, data flow, technology stack |
| 03 | [Config-Driven Alerting](03-config-driven-alerting.md) | Delta table schema, alert configuration model |
| 04 | [Alert Query Patterns](04-alert-query-patterns.md) | SQL query patterns, threshold logic, best practices |
| 05 | [Databricks SDK Integration](05-databricks-sdk-integration.md) | SDK types, authentication, API patterns |
| 06 | [Notification Destinations](06-notification-destinations.md) | Email, Slack, Webhook, Teams, PagerDuty |
| 07 | [Query Validation](07-query-validation.md) | EXPLAIN-based pre-deployment validation |
| 08 | [Hierarchical Job Architecture](08-hierarchical-job-architecture.md) | Atomic + composite job patterns |
| 09 | [Partial Success Patterns](09-partial-success-patterns.md) | Resilience and error handling |
| 10 | [Alert Templates](10-alert-templates.md) | Pre-built templates and customization |
| 11 | [Implementation Guide](11-implementation-guide.md) | Step-by-step implementation phases |
| 12 | [Deployment and Operations](12-deployment-and-operations.md) | Production deployment and monitoring |
| 13 | [Frontend Alert Management](13-frontend-alert-management.md) | UI design for alert CRUD via Delta table |

## Appendices

| # | Document | Description |
|---|----------|-------------|
| A | [Code Examples](appendices/A-code-examples.md) | Complete working code snippets |
| B | [Cursor Rule Reference](appendices/B-cursor-rule-reference.md) | Link to `19-sql-alerting-patterns.mdc` |
| C | [Official Documentation](appendices/C-official-documentation.md) | Databricks documentation links |
| D | [Troubleshooting Guide](appendices/D-troubleshooting.md) | Common issues and solutions |

## Framework Summary

```
ALERTING FRAMEWORK (v2.3)
├── CONFIGURATION LAYER
│   ├── alert_configurations      # 29 pre-built alerts across 5 domains
│   ├── notification_destinations # Email, Slack, Webhook channels
│   ├── alert_validation_results  # Query validation status
│   └── alert_sync_metrics        # Sync operation observability
│
├── PROCESSING LAYER
│   ├── Query Validator           # EXPLAIN-based syntax validation
│   ├── Template Renderer         # ${catalog}/${gold_schema} substitution
│   ├── Notification Builder      # Channel → destination UUID mapping
│   └── Alert Sync Engine         # Databricks SDK (WorkspaceClient)
│
├── DEPLOYMENT LAYER (Hierarchical Jobs)
│   ├── LAYER 2: alerting_setup_orchestrator_job (Composite)
│   │   └── Orchestrates 5 atomic jobs via run_job_task
│   └── LAYER 1: Atomic Jobs
│       ├── alerting_tables_job
│       ├── alerting_seed_job
│       ├── alerting_validation_job
│       ├── alerting_notifications_job
│       └── alerting_deploy_job
│
└── OUTPUT LAYER
    └── Databricks SQL Alerts (v2 API)
        └── Native alerting infrastructure
```

## Quick Start

1. **Understand the Architecture**: Start with [02-architecture-overview.md](02-architecture-overview.md)
2. **Learn Configuration**: Read [03-config-driven-alerting.md](03-config-driven-alerting.md)
3. **Follow Implementation**: Step through [11-implementation-guide.md](11-implementation-guide.md)
4. **Deploy**: Follow [12-deployment-and-operations.md](12-deployment-and-operations.md)

## Best Practices Showcased

| # | Best Practice | Implementation |
|---|---------------|----------------|
| 1 | **Config-Driven Architecture** | Alert rules in Delta table, not code |
| 2 | **Databricks SDK Integration** | Typed `AlertV2` objects, auto-auth |
| 3 | **Pre-Deployment Validation** | EXPLAIN-based query checking |
| 4 | **Hierarchical Job Architecture** | Atomic + composite job pattern |
| 5 | **Partial Success Handling** | ≥90% threshold, graceful failures |
| 6 | **DataFrame Seeding** | Avoid SQL escaping issues |
| 7 | **Domain Organization** | COST, SECURITY, PERFORMANCE, RELIABILITY, QUALITY |
| 8 | **Severity-Based Routing** | CRITICAL, WARNING, INFO levels |
| 9 | **Notification Abstraction** | Named destinations, multiple channels |
| 10 | **Unity Catalog Governance** | All tables UC-managed |
| 11 | **Observability** | Sync metrics, validation results |
| 12 | **Version History** | Delta time travel for audit |

## Alert Domain Distribution

| Domain | Prefix | Alert Count | Examples |
|--------|--------|-------------|----------|
| **COST** | COST | 6 | Budget threshold, tag coverage, spend anomalies |
| **SECURITY** | SEC | 8 | Access violations, audit events, permission changes |
| **PERFORMANCE** | PERF | 5 | Query latency, cluster utilization, warehouse queue |
| **RELIABILITY** | RELI | 5 | Job failures, SLA breaches, pipeline health |
| **QUALITY** | QUAL | 5 | Data freshness, NULL rates, schema drift |
| **Total** | - | **29** | Pre-built, validated alerts |

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Configuration Storage | Delta Lake | Alert rules, notification destinations |
| Alert Infrastructure | SQL Alerts v2 | Native Databricks alerting |
| Deployment | Databricks SDK | Programmatic alert management |
| Job Orchestration | Databricks Asset Bundles | Infrastructure-as-code |
| Governance | Unity Catalog | Access control, lineage |

## Related Documentation

- [Phase 3.7: Alerting Framework Plan](../../plans/phase3-addendum-3.7-alerting-framework.md)
- [SQL Alerting Patterns Cursor Rule](../../.cursor/rules/monitoring/19-sql-alerting-patterns.mdc)
- [Databricks Asset Bundles Rule](../../.cursor/rules/common/02-databricks-asset-bundles.mdc)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.3 | Jan 1, 2026 | Comprehensive documentation refactor, training guide format |
| 2.1 | Dec 31, 2025 | SDK integration, hierarchical jobs, partial success |
| 2.0 | Dec 30, 2025 | Query validation, REST API improvements |
| 1.0 | Dec 2025 | Initial release |


