#!/usr/bin/env python3
"""
Fix ALL remaining COLUMN_NOT_FOUND errors based on ground truth analysis.

Ground Truth Sources:
- docs/reference/actual_assets/tvfs.md - TVF output columns
- docs/reference/actual_assets/ml.md - ML table columns  
- docs/reference/actual_assets/tables.md - Fact/dim table columns
- docs/reference/actual_assets/mvs.md - Metric view columns
"""
import json
from pathlib import Path

def fix_security_auditor(json_file: Path) -> int:
    """Fix security_auditor COLUMN_NOT_FOUND errors"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    fixed = 0
    questions = data.get('benchmarks', {}).get('questions', [])
    for q in questions:
        if 'answer' in q and q['answer']:
            sql = q['answer'][0]['content'][0]
            question_text = ''.join(q.get('question', []))
            
            # Q7: failed access attempts - ORDER BY failed_events → user_email
            # TVF get_failed_actions returns: event_time, user_email, service, action, status_code, error_message, source_ip
            if 'failed access attempts' in question_text and 'ORDER BY failed_events' in sql:
                new_sql = sql.replace('ORDER BY failed_events DESC', 'ORDER BY event_time DESC')
                q['answer'][0]['content'][0] = new_sql
                print(f"✅ security_auditor Q7: ORDER BY failed_events → event_time")
                fixed += 1
            
            # Q11: user activity patterns - ORDER BY event_hour → event_date
            # TVF get_off_hours_activity returns: event_date, user_email, off_hours_events, services_accessed, sensitive_actions, unique_ips
            elif 'user activity patterns' in question_text and 'event_hour' in sql:
                new_sql = sql.replace('event_hour', 'event_date')
                q['answer'][0]['content'][0] = new_sql
                print(f"✅ security_auditor Q11: event_hour → event_date")
                fixed += 1
    
    if fixed > 0:
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    return fixed

def fix_performance(json_file: Path) -> int:
    """Fix performance COLUMN_NOT_FOUND errors"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    fixed = 0
    questions = data.get('benchmarks', {}).get('questions', [])
    for q in questions:
        if 'answer' in q and q['answer']:
            sql = q['answer'][0]['content'][0]
            question_text = ''.join(q.get('question', []))
            
            # Q16: cluster right-sizing - potential_savings_usd doesn't exist in cluster_capacity_predictions
            # Available columns: prediction, query_count, sla_breach_rate, etc.
            # Remove ORDER BY potential_savings_usd - order by prediction instead
            if 'cluster right-sizing recommendations' in question_text and 'potential_savings_usd' in sql:
                new_sql = sql.replace('ORDER BY potential_savings_usd DESC', 'ORDER BY prediction DESC, query_count DESC')
                q['answer'][0]['content'][0] = new_sql
                print(f"✅ performance Q16: Remove potential_savings_usd, ORDER BY prediction")
                fixed += 1
    
    if fixed > 0:
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    return fixed

def fix_job_health_monitor(json_file: Path) -> int:
    """Fix job_health_monitor COLUMN_NOT_FOUND errors"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    fixed = 0
    questions = data.get('benchmarks', {}).get('questions', [])
    for q in questions:
        if 'answer' in q and q['answer']:
            sql = q['answer'][0]['content'][0]
            question_text = ''.join(q.get('question', []))
            
            # Q10: job retry analysis - retry_effectiveness doesn't exist
            # TVF get_job_retry_analysis returns: job_id, job_name, total_attempts, initial_failures, retry_count, 
            #                                      final_success_count, retry_rate_pct, eventual_success_pct
            if 'job retry analysis' in question_text and 'retry_effectiveness' in sql:
                new_sql = sql.replace('ORDER BY retry_effectiveness DESC', 'ORDER BY eventual_success_pct DESC')
                q['answer'][0]['content'][0] = new_sql
                print(f"✅ job_health_monitor Q10: retry_effectiveness → eventual_success_pct")
                fixed += 1
            
            # Q18: Cross-task dependency - depends_on doesn't exist
            # dim_job_task has: depends_on_keys_json (not depends_on)
            elif 'Cross-task dependency' in question_text and 'jt.depends_on' in sql:
                new_sql = sql.replace('jt.depends_on', 'jt.depends_on_keys_json')
                q['answer'][0]['content'][0] = new_sql
                print(f"✅ job_health_monitor Q18: depends_on → depends_on_keys_json")
                fixed += 1
    
    if fixed > 0:
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    return fixed

def fix_unified_health_monitor(json_file: Path) -> int:
    """Fix unified_health_monitor COLUMN_NOT_FOUND errors"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    fixed = 0
    questions = data.get('benchmarks', {}).get('questions', [])
    for q in questions:
        if 'answer' in q and q['answer']:
            sql = q['answer'][0]['content'][0]
            question_text = ''.join(q.get('question', []))
            
            # Q7: failed jobs today - ORDER BY error_message → start_time
            # TVF get_failed_jobs returns: workspace_id, job_id, job_name, run_id, result_state, termination_code, 
            #                              run_as, start_time, end_time, duration_minutes
            if 'failed jobs today' in question_text and 'ORDER BY error_message' in sql:
                new_sql = sql.replace('ORDER BY error_message DESC', 'ORDER BY start_time DESC')
                q['answer'][0]['content'][0] = new_sql
                print(f"✅ unified_health_monitor Q7: ORDER BY error_message → start_time")
                fixed += 1
            
            # Q13: DLT pipeline health - failed_count doesn't exist
            # TVF get_pipeline_data_lineage returns: entity_type, entity_id, entity_name, source_tables, target_tables,
            #                                         source_count, target_count, unique_days, total_events, last_run_date, complexity_score
            elif 'DLT pipeline health' in question_text and 'failed_count' in sql:
                # Remove the calculation using failed_count - use total_events instead
                new_sql = sql.replace(
                    'ROUND(100.0 * (total_events - failed_count) / NULLIF(total_events, 0), 2)',
                    'total_events'
                )
                new_sql = new_sql.replace('ORDER BY', 'ORDER BY total_events DESC,')  # Add fallback ordering
                q['answer'][0]['content'][0] = new_sql
                print(f"✅ unified_health_monitor Q13: Remove failed_count, use total_events")
                fixed += 1
            
            # Q18: cluster right-sizing - potential_savings_usd doesn't exist (same as performance Q16)
            elif 'cluster right-sizing recommendations' in question_text and 'potential_savings_usd' in sql:
                new_sql = sql.replace('ORDER BY potential_savings_usd DESC', 'ORDER BY prediction DESC, query_count DESC')
                q['answer'][0]['content'][0] = new_sql
                print(f"✅ unified_health_monitor Q18: Remove potential_savings_usd, ORDER BY prediction")
                fixed += 1
            
            # Q19: Platform health - sla_breach_rate column issue
            # This is a complex CTE query - sla_breach_rate might be from mv_query_performance or cluster_capacity_predictions
            # The ML table has sla_breach_rate, so this should work - might be a different issue
            # Skip for now and investigate after validation
    
    if fixed > 0:
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    return fixed

def fix_cost_intelligence(json_file: Path) -> int:
    """Fix cost_intelligence COLUMN_NOT_FOUND errors"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    fixed = 0
    questions = data.get('benchmarks', {}).get('questions', [])
    for q in questions:
        if 'answer' in q and q['answer']:
            sql = q['answer'][0]['content'][0]
            question_text = ''.join(q.get('question', []))
            
            # Q25: Predictive cost optimization - workspace_id doesn't exist in get_cost_forecast_summary output
            # The TVF returns domain-level forecasts, not workspace-level
            # Need to check the TVF output more carefully or remove the workspace_id join
            if 'Predictive cost optimization' in question_text and 'workspace_id' in sql:
                # This is a complex CTE query - need to investigate the TVF output more carefully
                # For now, skip and investigate after validation
                pass
    
    return fixed

def main():
    base_dir = Path('src/genie')
    total_fixed = 0
    
    # Fix security_auditor errors (Q7, Q11)
    security_file = base_dir / 'security_auditor_genie_export.json'
    fixed = fix_security_auditor(security_file)
    total_fixed += fixed
    if fixed > 0:
        print(f"✓ Fixed {fixed} errors in {security_file.name}")
    
    # Fix performance errors (Q16)
    perf_file = base_dir / 'performance_genie_export.json'
    fixed = fix_performance(perf_file)
    total_fixed += fixed
    if fixed > 0:
        print(f"✓ Fixed {fixed} errors in {perf_file.name}")
    
    # Fix job_health_monitor errors (Q10, Q18)
    job_file = base_dir / 'job_health_monitor_genie_export.json'
    fixed = fix_job_health_monitor(job_file)
    total_fixed += fixed
    if fixed > 0:
        print(f"✓ Fixed {fixed} errors in {job_file.name}")
    
    # Fix unified_health_monitor errors (Q7, Q13, Q18)
    unified_file = base_dir / 'unified_health_monitor_genie_export.json'
    fixed = fix_unified_health_monitor(unified_file)
    total_fixed += fixed
    if fixed > 0:
        print(f"✓ Fixed {fixed} errors in {unified_file.name}")
    
    # Fix cost_intelligence errors (Q25) - skipped for now
    # cost_file = base_dir / 'cost_intelligence_genie_export.json'
    # fixed = fix_cost_intelligence(cost_file)
    # total_fixed += fixed
    
    print(f"\n✅ Total fixes applied: {total_fixed}")
    print(f"\n📊 Remaining to investigate:")
    print(f"   - cost_intelligence Q25: workspace_id (complex CTE, needs careful analysis)")
    print(f"   - unified_health_monitor Q19: sla_breach_rate (may work, needs validation)")

if __name__ == '__main__':
    main()

