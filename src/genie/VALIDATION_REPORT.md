
================================================================================
VALIDATION REPORT
================================================================================
Generated: 2026-01-06 08:31:48

Total benchmark queries: 150
  ✓ Valid:   150
  ✗ Invalid: 0
  ⚠ Warnings: 53


--------------------------------------------------------------------------------
SUMMARY BY GENIE SPACE
--------------------------------------------------------------------------------
  ✓ cost_intelligence: 25 queries, 0 errors (10 warnings)
  ✓ data_quality_monitor: 25 queries, 0 errors (6 warnings)
  ✓ job_health_monitor: 25 queries, 0 errors (7 warnings)
  ✓ performance: 25 queries, 0 errors (8 warnings)
  ✓ security_auditor: 25 queries, 0 errors (11 warnings)
  ✓ unified_health_monitor: 25 queries, 0 errors (11 warnings)

--------------------------------------------------------------------------------
WARNINGS (recommended to review)
--------------------------------------------------------------------------------

⚠️ [cost_intelligence] Q6: Show me the top 10 cost contributors this month...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [cost_intelligence] Q7: What are the cost anomalies in the last 30 days?...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [cost_intelligence] Q8: Show me untagged resources...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [cost_intelligence] Q9: What is the cost breakdown by owner?...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [cost_intelligence] Q10: Show me serverless vs classic cost comparison...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [cost_intelligence] Q11: What is the daily cost summary?...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [cost_intelligence] Q14: Show me cost by team tag...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [cost_intelligence] Q15: What is the job cost breakdown?...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [cost_intelligence] Q17: Show me ALL_PURPOSE cluster costs and migration opportunitie...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [cost_intelligence] Q19: Show me warehouse cost analysis...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [data_quality_monitor] Q2: Show me tables with freshness issues...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [data_quality_monitor] Q4: Show me tables failing quality checks...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [data_quality_monitor] Q6: Show me the data quality summary...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [data_quality_monitor] Q8: Show me inactive tables...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [data_quality_monitor] Q10: Show me pipeline data lineage...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [data_quality_monitor] Q11: What is the job quality status?...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [job_health_monitor] Q4: Show me failed jobs today...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [job_health_monitor] Q6: Show me job duration percentiles...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [job_health_monitor] Q7: Which jobs have the lowest success rate?...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [job_health_monitor] Q8: Show me job failure trends...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [job_health_monitor] Q9: What jobs are running longer than their SLA?...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [job_health_monitor] Q10: Show me job retry analysis...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [job_health_monitor] Q12: Show me job repair costs from retries...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [performance] Q5: Show me slow queries from today...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [performance] Q7: Show me warehouse utilization metrics...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [performance] Q8: Which queries have high disk spill?...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [performance] Q10: Show me underutilized clusters...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [performance] Q12: Show me query volume trends...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [performance] Q14: Show me query latency percentiles by warehouse...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [performance] Q15: Which jobs don't have autoscaling enabled?...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [performance] Q16: Show me cluster right-sizing recommendations...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [security_auditor] Q5: Show me user activity summary...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [security_auditor] Q6: Who accessed sensitive tables?...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [security_auditor] Q7: Show me failed access attempts...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [security_auditor] Q8: What permission changes happened this week?...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [security_auditor] Q9: Show me unusual access patterns...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [security_auditor] Q11: Show me user activity patterns...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [security_auditor] Q13: Show me data export events...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [security_auditor] Q16: Show me service account activity...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [security_auditor] Q20: Show me table access audit...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [security_auditor] Q22: DEEP RESEARCH: Sensitive data access compliance audit - iden...
   WARNING: [MEASURE_OUTSIDE_SELECT] MEASURE() should be in SELECT clause

⚠️ [security_auditor] Q23: DEEP RESEARCH: Security event timeline with threat correlati...
   WARNING: [MEASURE_OUTSIDE_SELECT] MEASURE() should be in SELECT clause

⚠️ [unified_health_monitor] Q7: Show me failed jobs today...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [unified_health_monitor] Q8: Show me slow queries...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [unified_health_monitor] Q10: Show me stale tables...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [unified_health_monitor] Q13: Show me warehouse utilization...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [unified_health_monitor] Q14: What is the DLT pipeline health?...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [unified_health_monitor] Q15: Show me underutilized clusters...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [unified_health_monitor] Q17: Show me tables failing quality checks...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [unified_health_monitor] Q20: Show me cluster right-sizing recommendations...
   WARNING: [SELECT_STAR_NO_LIMIT] SELECT * without LIMIT may return large result sets

⚠️ [unified_health_monitor] Q22: 🔬 DEEP RESEARCH: Cost optimization opportunities - combine u...
   WARNING: [MEASURE_OUTSIDE_SELECT] MEASURE() should be in SELECT clause

⚠️ [unified_health_monitor] Q23: 🔬 DEEP RESEARCH: Security and compliance posture - correlate...
   WARNING: [MEASURE_OUTSIDE_SELECT] MEASURE() should be in SELECT clause

⚠️ [unified_health_monitor] Q24: 🔬 DEEP RESEARCH: Data platform reliability - correlate job f...
   WARNING: [MEASURE_OUTSIDE_SELECT] MEASURE() should be in SELECT clause

================================================================================
DEPLOYMENT READINESS
================================================================================

✅ READY FOR DEPLOYMENT
   All benchmark queries passed validation.
   Note: 53 warnings to review (non-blocking)
