#!/usr/bin/env python3
"""
Fix final 4 unified_health_monitor errors.

Q22: SYNTAX_ERROR - Fix COALESCE placement
Q23: TABLE_NOT_FOUND - Remove user_risk CTE (should have been removed)
Q24: COLUMN_NOT_FOUND - sla_breach_rate doesn't exist
Q25: COLUMN_NOT_FOUND - serverless_percentage → serverless_ratio
"""

import json
import re
from pathlib import Path

def fix_unified_final_4():
    """Fix final 4 unified errors."""
    json_path = Path("src/genie/unified_health_monitor_genie_export.json")
    
    with open(json_path) as f:
        data = json.load(f)
    
    print("=" * 80)
    print("UNIFIED HEALTH MONITOR - FINAL 4 ERRORS")
    print("=" * 80)
    print()
    
    # Q22: SYNTAX_ERROR - Fix underutilized CTE (potential_savings doesn't exist)
    # Just remove the underutilized CTE entirely and simplify
    q22_sql = """WITH untagged AS (
  SELECT 
    workspace_name,
    MEASURE(total_cost) as untagged_cost
  FROM ${catalog}.${gold_schema}.mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND tag_team IS NULL
  GROUP BY workspace_name
)
SELECT 
  COALESCE(SUM(untagged_cost), 0) as total_untagged_cost,
  COUNT(DISTINCT workspace_name) as workspaces_with_untagged_cost,
  CASE 
    WHEN SUM(untagged_cost) > 10000 THEN 'High Priority - Immediate Action'
    WHEN SUM(untagged_cost) > 5000 THEN 'Medium Priority - Review Soon'
    ELSE 'Low Priority - Monitor'
  END as optimization_priority
FROM untagged
LIMIT 1;"""
    data['benchmarks']['questions'][21]['answer'][0]['content'] = [q22_sql]
    print("✅ Q22: Simplified query (removed underutilized CTE)")
    
    # Q23: Remove user_risk CTE (ML table doesn't exist)
    q23 = data['benchmarks']['questions'][22]
    sql23 = q23['answer'][0]['content'][0]
    
    # Remove user_risk CTE
    sql23 = re.sub(r',\s*user_risk AS \(.*?\)', '', sql23, flags=re.DOTALL)
    # Remove references to user_risk
    sql23 = re.sub(r',\s*ur\.avg_risk_level', '', sql23)
    sql23 = re.sub(r'LEFT JOIN user_risk ur ON[^W]+', '', sql23)
    
    data['benchmarks']['questions'][22]['answer'][0]['content'] = [sql23]
    print("✅ Q23: Removed user_risk CTE")
    
    # Q24: sla_breach_rate doesn't exist - remove it
    q24 = data['benchmarks']['questions'][23]
    sql24 = q24['answer'][0]['content'][0]
    
    # Remove sla_breach_rate references
    sql24 = re.sub(r",\s*qh\.sla_breach_rate[^,]*", "", sql24)
    sql24 = re.sub(r"qh\.sla_breach_rate[^,]*,\s*", "", sql24)
    
    data['benchmarks']['questions'][23]['answer'][0]['content'] = [sql24]
    print("✅ Q24: Removed sla_breach_rate references")
    
    # Q25: serverless_percentage → serverless_ratio
    q25 = data['benchmarks']['questions'][24]
    sql25 = q25['answer'][0]['content'][0]
    
    sql25 = sql25.replace('serverless_percentage', 'serverless_ratio')
    
    data['benchmarks']['questions'][24]['answer'][0]['content'] = [sql25]
    print("✅ Q25: serverless_percentage → serverless_ratio")
    
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print()
    print("=" * 80)
    print("✅ ALL 4 UNIFIED FIXES COMPLETE")
    print("=" * 80)

def main():
    fix_unified_final_4()
    
    print()
    print("Summary:")
    print("  Q22: Simplified (removed underutilized CTE with non-existent columns)")
    print("  Q23: Removed user_risk CTE (ML table doesn't exist)")
    print("  Q24: Removed sla_breach_rate (column doesn't exist)")
    print("  Q25: serverless_percentage → serverless_ratio")

if __name__ == "__main__":
    main()

