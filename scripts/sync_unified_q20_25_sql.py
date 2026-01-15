#!/usr/bin/env python3
"""
Sync SQL from unified_health_monitor_genie.md to unified_health_monitor_genie_export.json
for Q20, Q21, Q22, Q25 which currently have empty SQL.
"""

import json
from pathlib import Path

# SQL for Q20 (fixed syntax error - removed extra ))
q20_sql = """SELECT * FROM get_cluster_rightsizing_recommendations(30)
ORDER BY potential_savings DESC
LIMIT 15;"""

# SQL for Q21 (from MD - very long, single line)
q21_sql = """WITH cost_health AS (  SELECT     MEASURE(total_cost) as total_spend,    MEASURE(last_7_day_cost) as last_7_day_cost,    MEASURE(last_30_day_cost) as last_30_day_cost,    MEASURE(tag_coverage_pct) as tag_coverage  FROM mv_cost_analytics  WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS),job_health AS (  SELECT     MEASURE(success_rate) as job_success_rate,    MEASURE(failure_rate) as job_failure_rate,    MEASURE(total_runs) as total_job_runs  FROM mv_job_performance  WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS),query_health AS (  SELECT     MEASURE(p95_duration_seconds) as p95_latency,    MEASURE(spill_rate) as sla_breach_pct,    MEASURE(cache_hit_rate) as cache_pct  FROM mv_query_performance),security_health AS (  SELECT     (100 - MEASURE(failure_rate)) as auth_success_rate,    MEASURE(sensitive_events) as high_risk_count,    MEASURE(unique_users) as active_users  FROM mv_security_events  WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS),quality_health AS (  SELECT     MEASURE(freshness_rate) as data_quality,    MEASURE(freshness_rate) as freshness_pct,    MEASURE(staleness_rate) as staleness_pct  FROM mv_data_quality),cluster_health AS (  SELECT     MEASURE(avg_cpu_utilization) as avg_cpu,    MEASURE(efficiency_score) as efficiency  FROM mv_cluster_utilization  WHERE utilization_date >= CURRENT_DATE() - INTERVAL 7 DAYS)SELECT   ch.total_spend,  ch.last_7_day_cost,  ch.tag_coverage,  jh.job_success_rate,  jh.job_failure_rate,  jh.total_job_runs,  qh.p95_latency,  qh.sla_breach_pct,  qh.cache_pct,  sh.auth_success_rate,  sh.high_risk_count,  sh.active_users,  quh.data_quality,  quh.freshness_pct,  quh.staleness_pct,  clh.avg_cpu,  clh.efficiency,  CASE     WHEN jh.job_failure_rate > 10 OR qh.sla_breach_pct > 5 THEN 'Critical - Reliability Issues'    WHEN sh.high_risk_count > 20 OR sh.auth_success_rate < 95 THEN 'Critical - Security Concerns'    WHEN quh.data_quality < 70 OR quh.staleness_pct > 20 THEN 'Critical - Data Quality Crisis'    WHEN ch.last_7_day_cost * 30 > ch.last_30_day_cost * 1.2 THEN 'Warning - Cost Spike Detected'    WHEN qh.cache_pct > 80 AND jh.job_success_rate > 95 AND quh.data_quality >= 90 THEN 'Excellent Health'    ELSE 'Normal'  END as overall_platform_health,  CASE     WHEN jh.job_failure_rate > 10 THEN 'Investigate job failures immediately'    WHEN qh.sla_breach_pct > 5 THEN 'Optimize slow queries and warehouse sizing'    WHEN sh.high_risk_count > 20 THEN 'Review security events and threats'    WHEN quh.staleness_pct > 20 THEN 'Fix data pipeline freshness issues'    WHEN ch.last_7_day_cost * 30 > ch.last_30_day_cost * 1.2 THEN 'Analyze cost drivers and right-size resources'    WHEN clh.avg_cpu < 40 THEN 'Downsize underutilized clusters'    ELSE 'Continue monitoring'  END as top_priority_action FROM cost_health ch CROSS JOIN job_health jh CROSS JOIN query_health qh CROSS JOIN security_health sh CROSS JOIN quality_health quh CROSS JOIN cluster_health clh;"""

# SQL for Q22 (from MD)
q22_sql = """WITH underutilized AS (  SELECT    cluster_name,    avg_cpu_pct,    potential_savings as savings_from_underutilization  FROM get_underutilized_clusters(30)  WHERE avg_cpu_pct < 30),rightsizing AS (  SELECT    cluster_name,    current_size,    recommended_size,    potential_savings as savings_from_rightsizing  FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_ml.cluster_capacity_predictions  WHERE recommended_action != 'NO_CHANGE'),untagged AS (  SELECT     workspace_name,    MEASURE(total_cost) as untagged_cost  FROM mv_cost_analytics  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS      AND tag_team IS NULL  GROUP BY workspace_name),autoscaling_gaps AS (  SELECT    job_name,    estimated_savings  FROM get_jobs_without_autoscaling(30)),legacy_dbr AS (  SELECT    COUNT(*) as legacy_job_count  FROM get_jobs_on_legacy_dbr(30))SELECT   COALESCE(SUM(u.savings_from_underutilization), 0) as savings_underutil,  COALESCE(SUM(r.savings_from_rightsizing), 0) as savings_rightsize,  COALESCE(SUM(ut.untagged_cost * 0.1), 0) as estimated_waste_from_untagged,  COALESCE(SUM(ag.estimated_savings), 0) as savings_autoscaling,  ld.legacy_job_count,  COALESCE(SUM(u.savings_from_underutilization), 0) +   COALESCE(SUM(r.savings_from_rightsizing), 0) +   COALESCE(SUM(ag.estimated_savings), 0) as total_monthly_savings_potential,  CASE     WHEN COALESCE(SUM(u.savings_from_underutilization), 0) + COALESCE(SUM(r.savings_from_rightsizing), 0) > 10000 THEN 'Critical - Immediate Right-Sizing Required'    WHEN COALESCE(SUM(ut.untagged_cost), 0) > 5000 THEN 'High - Improve Tagging for Accountability'    WHEN ld.legacy_job_count > 20 THEN 'Medium - Modernize Legacy DBR Jobs'    ELSE 'Low - Continue Monitoring'  END as optimization_priority,  ARRAY(    CASE WHEN COALESCE(SUM(u.savings_from_underutilization), 0) > 5000 THEN 'Downsize or terminate underutilized clusters' END,    CASE WHEN COALESCE(SUM(r.savings_from_rightsizing), 0) > 5000 THEN 'Apply ML right-sizing recommendations' END,    CASE WHEN COALESCE(SUM(ut.untagged_cost), 0) > 5000 THEN 'Implement tagging policy and governance' END,    CASE WHEN COALESCE(SUM(ag.estimated_savings), 0) > 2000 THEN 'Enable autoscaling on fixed-size jobs' END,    CASE WHEN ld.legacy_job_count > 20 THEN 'Migrate to latest DBR versions' END  ) as recommended_actions FROM underutilized u FULL OUTER JOIN rightsizing r ON u.cluster_name = r.cluster_name FULL OUTER JOIN untagged ut ON 1=1 FULL OUTER JOIN autoscaling_gaps ag ON 1=1 CROSS JOIN legacy_dbr ld;"""

# SQL for Q25 (from MD - already in previous read)
q25_sql = """WITH cost_trends AS (  SELECT     MEASURE(total_cost) as cost_7d,    MEASURE(total_cost) as cost_30d,    MEASURE(total_cost) as cost_mtd,    MEASURE(tag_coverage_pct) as avg_tag_coverage  FROM mv_cost_analytics  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS),cost_by_domain AS (  SELECT     entity_type as domain,    MEASURE(total_cost) as domain_cost  FROM mv_cost_analytics  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS  GROUP BY entity_type  ORDER BY domain_cost DESC  LIMIT 5),commit_status AS (  SELECT     sku_name,    MEASURE(utilization_rate) as usage_pct,    MEASURE(remaining_dbu) as remaining_capacity  FROM mv_commit_tracking  WHERE usage_month = DATE_TRUNC('month', CURRENT_DATE())  GROUP BY sku_name),efficiency AS (  SELECT     MEASURE(avg_cpu_utilization) as avg_cpu_util,    MEASURE(efficiency_score) as avg_efficiency  FROM mv_cluster_utilization  WHERE utilization_date >= CURRENT_DATE() - INTERVAL 7 DAYS),optimization_potential AS (  SELECT    SUM(potential_savings) as total_savings_potential  FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_ml.cluster_capacity_predictions  WHERE recommended_action != 'NO_CHANGE'),serverless_adoption AS (  SELECT     MEASURE(serverless_percentage) as serverless_pct  FROM mv_cost_analytics  WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS)SELECT   ct.cost_7d,  ct.cost_30d,  ct.cost_mtd,  ct.cost_7d * 30 as projected_monthly_cost,  ct.avg_tag_coverage,  COALESCE(STRING_AGG(cbd.domain || ': $' || CAST(cbd.domain_cost as STRING), ', '), 'N/A') as top_5_cost_domains,  COALESCE(AVG(cs.usage_pct), 0) as avg_commit_utilization,  COALESCE(SUM(cs.remaining_capacity), 0) as total_remaining_commit,  ef.avg_cpu_util,  ef.avg_efficiency,  COALESCE(op.total_savings_potential, 0) as monthly_optimization_potential,  sa.serverless_pct,  CASE     WHEN ct.cost_7d * 30 > ct.cost_30d * 1.3 THEN 'Critical - Cost Spike Detected'    WHEN COALESCE(AVG(cs.usage_pct), 0) < 70 THEN 'Warning - Under-Utilizing Commitments'    WHEN ef.avg_cpu_util < 40 THEN 'Warning - Resource Inefficiency'    WHEN COALESCE(op.total_savings_potential, 0) > 10000 THEN 'High - Significant Optimization Opportunity'    WHEN sa.serverless_pct < 30 THEN 'Medium - Low Serverless Adoption'    ELSE 'Healthy FinOps Posture'  END as finops_health_status,  CASE     WHEN ct.cost_7d * 30 > ct.cost_30d * 1.3 THEN 'Investigate cost spike drivers and implement controls'    WHEN COALESCE(AVG(cs.usage_pct), 0) < 70 THEN 'Increase workload on committed capacity'    WHEN ef.avg_cpu_util < 40 THEN 'Right-size clusters and consolidate workloads'    WHEN COALESCE(op.total_savings_potential, 0) > 10000 THEN 'Apply ML right-sizing recommendations'    WHEN sa.serverless_pct < 30 THEN 'Migrate eligible workloads to serverless'    WHEN ct.avg_tag_coverage < 80 THEN 'Implement tagging policy for cost allocation'    ELSE 'Continue monitoring and optimizing'  END as top_priority_action FROM cost_trends ct CROSS JOIN cost_by_domain cbd CROSS JOIN commit_status cs CROSS JOIN efficiency ef CROSS JOIN optimization_potential op CROSS JOIN serverless_adoption sa GROUP BY   ct.cost_7d, ct.cost_30d, ct.cost_mtd, ct.avg_tag_coverage,  ef.avg_cpu_util, ef.avg_efficiency, op.total_savings_potential, sa.serverless_pct;"""

def main():
    json_file = Path("src/genie/unified_health_monitor_genie_export.json")
    
    with open(json_file) as f:
        data = json.load(f)
    
    questions = data['benchmarks']['questions']
    
    # Update Q20 (index 19)
    questions[19]['answer'] = [{"format": "SQL", "content": [q20_sql]}]
    print("✅ Updated Q20: Show me cluster right-sizing recommendations")
    
    # Update Q21 (index 20)
    questions[20]['answer'] = [{"format": "SQL", "content": [q21_sql]}]
    print("✅ Updated Q21: Platform health overview")
    
    # Update Q22 (index 21)
    questions[21]['answer'] = [{"format": "SQL", "content": [q22_sql]}]
    print("✅ Updated Q22: Cost optimization opportunities")
    
    # Update Q25 (index 24)
    questions[24]['answer'] = [{"format": "SQL", "content": [q25_sql]}]
    print("✅ Updated Q25: Executive FinOps dashboard")
    
    # Save
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print("\n✅ All 4 questions synced from MD to JSON")

if __name__ == "__main__":
    main()

