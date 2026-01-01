# 01 - Introduction

## Purpose

This document defines the architecture for a **production-grade config-driven alerting framework** on Databricks. The framework enables platform teams to:

1. **Centralize alert management** in a single Delta table
2. **Deploy alerts programmatically** via Databricks SDK
3. **Validate queries before deployment** using EXPLAIN
4. **Organize alerts by domain** (Cost, Security, Performance, Reliability, Quality)
5. **Route notifications** to appropriate channels based on severity
6. **Track sync history** for debugging and audit

## Why Config-Driven Alerting?

Traditional alert implementations embed rules in code, leading to:

| Problem | Impact |
|---------|--------|
| **Hardcoded thresholds** | Code changes required for tuning |
| **Scattered definitions** | Alerts spread across multiple files |
| **No version history** | Can't track who changed what |
| **Deployment coupling** | Full redeploy for simple changes |
| **Limited visibility** | No central view of all alerts |

Config-driven alerting solves these problems:

| Solution | Benefit |
|----------|---------|
| **Delta table storage** | Time travel, audit history, ACID transactions |
| **Single source of truth** | Query all alerts with SQL |
| **Runtime updates** | Change thresholds without code deployment |
| **Decoupled sync** | Deploy alerts independently of code |
| **Centralized management** | One table to rule them all |

## Scope

### In Scope

- **Alert Configuration Table**: Delta table schema for storing alert rules
- **Query Templates**: SQL patterns with placeholder substitution
- **Threshold Evaluation**: Operators, value types, aggregations
- **Notification Destinations**: Email, Slack, Webhook, Teams, PagerDuty
- **Pre-Deployment Validation**: EXPLAIN-based query checking
- **Databricks SDK Integration**: Typed `AlertV2` object management
- **Hierarchical Job Architecture**: Atomic + composite job patterns
- **Partial Success Handling**: Resilience for large alert batches

### Out of Scope

- **Alert rule authoring UI** (future: Databricks Apps frontend)
- **Real-time streaming alerts** (use DLT expectations instead)
- **Cross-workspace alert sync** (single workspace focus)
- **Custom LLM-based anomaly detection** (covered in ML pipeline)

## Prerequisites

### Completed Components

The alerting framework requires:

| Component | Status | Purpose |
|-----------|--------|---------|
| Gold Layer Tables | Required | Data sources for alert queries |
| Unity Catalog | Required | Data governance and access control |
| SQL Warehouse | Required | Alert evaluation engine |
| Databricks CLI | Required | Job deployment |

### Infrastructure Requirements

| Requirement | Specification |
|-------------|---------------|
| Databricks Runtime | Any (serverless recommended) |
| Unity Catalog | Enabled with catalog/schema permissions |
| SQL Warehouse | Serverless or Pro recommended |
| Databricks SDK | >= 0.40.0 (auto-upgraded at runtime) |
| Python | 3.10+ |

### Required Permissions

| Permission | Scope | Purpose |
|------------|-------|---------|
| CREATE TABLE | Target schema | Create configuration tables |
| INSERT/UPDATE | alert_configurations | Manage alert rules |
| SELECT | Gold layer tables | Execute alert queries |
| MANAGE | SQL Alerts | Create/update/delete alerts |
| MANAGE | Notification Destinations | Configure channels |

## Best Practices Matrix

This implementation showcases **12 alerting best practices**:

| # | Best Practice | Implementation | Document |
|---|---------------|----------------|----------|
| 1 | **Config-Driven Rules** | Delta table for all alert definitions | [03-config-driven](03-config-driven-alerting.md) |
| 2 | **Typed SDK Objects** | `AlertV2`, `AlertV2Condition`, etc. | [05-sdk](05-databricks-sdk-integration.md) |
| 3 | **Pre-Deployment Validation** | EXPLAIN before sync | [07-validation](07-query-validation.md) |
| 4 | **Hierarchical Jobs** | Atomic + composite pattern | [08-jobs](08-hierarchical-job-architecture.md) |
| 5 | **Partial Success** | ≥90% threshold continues | [09-partial](09-partial-success-patterns.md) |
| 6 | **DataFrame Seeding** | Avoid SQL escaping bugs | [11-impl](11-implementation-guide.md) |
| 7 | **Domain Organization** | 5 domains with clear ownership | [03-config](03-config-driven-alerting.md) |
| 8 | **Severity Routing** | CRITICAL, WARNING, INFO levels | [06-notify](06-notification-destinations.md) |
| 9 | **Named Destinations** | Abstract notification channels | [06-notify](06-notification-destinations.md) |
| 10 | **UC Governance** | All tables Unity Catalog managed | [03-config](03-config-driven-alerting.md) |
| 11 | **Observability** | Sync metrics and validation results | [12-deploy](12-deployment-and-operations.md) |
| 12 | **Query Templates** | ${catalog}/${gold_schema} substitution | [04-queries](04-alert-query-patterns.md) |

## Alert ID Convention

All alerts follow a consistent naming pattern:

```
<DOMAIN>-<NUMBER>

Examples:
- COST-001   → First cost alert
- SEC-003    → Third security alert
- PERF-012   → Twelfth performance alert
- RELI-001   → First reliability alert
- QUAL-005   → Fifth quality alert
```

**Domain Prefixes:**

| Domain | Prefix | Description |
|--------|--------|-------------|
| Cost | COST | Billing, spend, budget alerts |
| Security | SEC | Access, audit, compliance alerts |
| Performance | PERF | Latency, throughput, resource alerts |
| Reliability | RELI | Job failures, SLA, availability alerts |
| Quality | QUAL | Data freshness, completeness, accuracy alerts |

## Severity Levels

| Severity | Action Required | Response Time | Notification |
|----------|-----------------|---------------|--------------|
| **CRITICAL** | Immediate | < 15 minutes | On-call page |
| **WARNING** | Investigate | < 4 hours | Team channel |
| **INFO** | Informational | Daily review | Email digest |

## Development Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| 1. Table Setup | 1 day | Create configuration tables |
| 2. Alert Seeding | 1 day | Seed 29 pre-built alerts |
| 3. Query Validation | 1 day | Implement EXPLAIN validator |
| 4. SDK Integration | 2 days | Sync engine with typed objects |
| 5. Notification Setup | 1 day | Configure destinations |
| 6. Job Architecture | 1 day | Hierarchical job structure |
| 7. Testing | 1 day | End-to-end validation |
| **Total** | **~8 days** | Production-ready framework |

## Success Criteria

| Criteria | Target | Measurement |
|----------|--------|-------------|
| Alert coverage | 29 alerts | Pre-built + validated |
| Query validation | 100% | All queries pass EXPLAIN |
| Sync success rate | ≥90% | Partial success threshold |
| Deployment time | <5 minutes | Full sync duration |
| Zero manual alerts | 100% | All alerts via config table |

## Document Conventions

### Code Examples

All code examples are:
- **Production-ready**: Copy directly into notebooks
- **Type-hinted**: Include type annotations
- **Well-commented**: Explain the "why"
- **Tested**: Validated on Databricks serverless

### Diagrams

- **Architecture diagrams**: ASCII art for portability
- **Data flow diagrams**: Show complete path from config to alert
- **Job dependency diagrams**: Show task relationships

### Configuration

- **No hardcoded values**: All parameterized via DAB variables
- **Environment support**: dev/staging/prod via bundle targets
- **Secrets management**: Notification credentials in Databricks Secrets

## Next Steps

1. **Read [02-Architecture Overview](02-architecture-overview.md)** for system design
2. **Understand [03-Config-Driven Alerting](03-config-driven-alerting.md)** for the data model
3. **Follow [11-Implementation Guide](11-implementation-guide.md)** for step-by-step setup


