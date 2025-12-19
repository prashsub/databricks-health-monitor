"""
Table-Valued Functions (TVFs) for Databricks Health Monitor
===========================================================

This module contains SQL TVFs organized by agent domain:
- Cost: Cost analysis, chargeback, tag-based attribution
- Reliability: Job failures, success rates, SLA compliance
- Performance: Query latency, warehouse utilization
- Security: User activity, access patterns
- Quality: Data quality, freshness monitoring

All TVFs query the Gold layer tables (not system tables directly).
"""
