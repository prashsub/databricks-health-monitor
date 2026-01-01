# Appendix B - Cursor Rule Reference

## Overview

The alerting framework is supported by a comprehensive Cursor rule that codifies best practices and patterns discovered during implementation.

## Rule Location

```
.cursor/rules/monitoring/19-sql-alerting-patterns.mdc
```

## Rule Contents

The rule documents:

1. **V2 API Reference** - Correct endpoint, payload structure, operators
2. **Alert ID Convention** - DOMAIN-NUMBER format
3. **Configuration Table Schema** - Complete Delta table DDL
4. **SQL Query Patterns** - 8 common query patterns
5. **SDK Integration** - Typed objects, authentication, methods
6. **REST API Alternative** - When and how to use
7. **DAB Job Configuration** - YAML patterns
8. **Hierarchical Job Architecture** - Atomic + composite pattern
9. **Partial Success Patterns** - Error handling
10. **Query Validation** - EXPLAIN-based validation
11. **Unity Catalog Limitations** - CHECK, DEFAULT, CLUSTER BY
12. **Troubleshooting** - Common issues and solutions

## Key Lessons Documented

From the rule version history:

### v2.3 (January 1, 2026)
- Hierarchical job architecture pattern
- Partial success handling (≥90% threshold)
- 29 pre-built alerts across 5 domains
- Full SDK types import list

### v2.2 (December 31, 2024)
- Query validation using EXPLAIN
- SQL escaping fix (DataFrame vs SQL INSERT)
- force_reseed parameter
- alert_validation_results table

### v2.1 (December 31, 2024)
- SDK as recommended approach
- %pip install --upgrade pattern
- %restart_python requirement
- V2 API list response key (alerts not results)

### v2.0 (December 2024)
- Correct V2 API endpoint (/api/2.0/alerts)
- update_mask requirement for PATCH
- RESOURCE_ALREADY_EXISTS handling
- Unity Catalog DDL limitations

## Using the Rule

When creating a new alerting framework:

```
1. Reference the rule: @.cursor/rules/monitoring/19-sql-alerting-patterns.mdc
2. Follow the patterns for:
   - Table schema
   - SDK integration
   - Query patterns
   - Job architecture
3. Adapt to your specific domains and use cases
```

## Related Rules

- **02-databricks-asset-bundles.mdc** - Job architecture patterns
- **17-lakehouse-monitoring-comprehensive.mdc** - Monitoring patterns
- **21-self-improvement.mdc** - Rule improvement process

## Rule Prompt

For easy reuse, see:

```
context/prompts/monitoring/14-sql-alerts-prompt.md
```

This prompt provides a template for creating similar alerting frameworks in other projects.


