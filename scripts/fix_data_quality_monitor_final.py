#!/usr/bin/env python3
"""
Fix data_quality_monitor Genie space errors (3 fixes)
- Q14 & Q15: Add dimension to enable MEASURE() aggregation
- Q16: Query source table directly instead of using MEASURE() in CTE
"""

import json
import re
from pathlib import Path

def fix_data_quality_monitor():
    """Fix all 3 data_quality_monitor errors."""
    
    json_path = Path("src/genie/data_quality_monitor_genie_export.json")
    
    with open(json_path) as f:
        data = json.load(f)
    
    questions = data.get("benchmarks", {}).get("questions", [])
    changes_made = False
    
    print("=" * 80)
    print("FIXING DATA_QUALITY_MONITOR ERRORS")
    print("=" * 80)
    
    # Fix Q14: Add dimension for MEASURE() aggregation
    if len(questions) >= 14:
        q14 = questions[13]
        answer = q14.get("answer", [])
        if answer:
            old_sql = answer[0].get("content", [""])[0]
            
            # New SQL: Group by dimension in subquery, then aggregate
            new_sql = """SELECT 
  SUM(total_predictions) as total_predictions,
  SUM(anomaly_count) as anomaly_count,
  AVG(avg_anomaly_score) as avg_anomaly_score
FROM (
  SELECT 
    workspace_name,
    MEASURE(total_predictions) as total_predictions,
    MEASURE(anomaly_count) as anomaly_count,
    MEASURE(avg_anomaly_score) as avg_anomaly_score
  FROM mv_ml_intelligence
  GROUP BY workspace_name
);"""
            
            answer[0]["content"] = [new_sql]
            print("\n✅ Q14: Added dimension for MEASURE() aggregation")
            print(f"   Fixed: Added GROUP BY for Metric View compatibility")
            changes_made = True
    
    # Fix Q15: Add dimension for MEASURE() aggregation
    if len(questions) >= 15:
        q15 = questions[14]
        answer = q15.get("answer", [])
        if answer:
            old_sql = answer[0].get("content", [""])[0]
            
            # New SQL: Group by dimension in subquery, then aggregate
            new_sql = """SELECT 
  AVG(anomaly_rate) as anomaly_rate,
  SUM(total_predictions) as total_predictions,
  SUM(high_risk_count) as high_risk_predictions
FROM (
  SELECT 
    workspace_name,
    MEASURE(anomaly_rate) as anomaly_rate,
    MEASURE(total_predictions) as total_predictions,
    MEASURE(high_risk_count) as high_risk_count
  FROM mv_ml_intelligence
  GROUP BY workspace_name
);"""
            
            answer[0]["content"] = [new_sql]
            print("\n✅ Q15: Added dimension for MEASURE() aggregation")
            print(f"   Fixed: Added GROUP BY for Metric View compatibility")
            changes_made = True
    
    # Fix Q16: Query source table directly in CTE
    if len(questions) >= 16:
        q16 = questions[15]
        answer = q16.get("answer", [])
        if answer:
            old_sql = answer[0].get("content", [""])[0]
            
            # New SQL: Query fact_data_quality directly instead of Metric View in CTE
            new_sql = """WITH table_scores AS (
  SELECT 
    table_full_name,
    freshness_rate as freshness_score
  FROM ${catalog}.${gold_schema}.fact_data_quality
)
SELECT 
  CASE 
    WHEN freshness_score >= 90 THEN 'Excellent (90-100)'
    WHEN freshness_score >= 70 THEN 'Good (70-89)'
    WHEN freshness_score >= 50 THEN 'Fair (50-69)'
    ELSE 'Poor (<50)'
  END as quality_tier,
  COUNT(*) as table_count
FROM table_scores
GROUP BY 
  CASE 
    WHEN freshness_score >= 90 THEN 'Excellent (90-100)'
    WHEN freshness_score >= 70 THEN 'Good (70-89)'
    WHEN freshness_score >= 50 THEN 'Fair (50-69)'
    ELSE 'Poor (<50)'
  END
ORDER BY quality_tier;"""
            
            answer[0]["content"] = [new_sql]
            print("\n✅ Q16: Changed to query source table directly")
            print(f"   Fixed: Query fact_data_quality instead of mv_data_quality in CTE")
            changes_made = True
    
    if changes_made:
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        print("\n" + "=" * 80)
        print("✅ DATA_QUALITY_MONITOR FIXES COMPLETE")
        print("=" * 80)
        print(f"Updated: {json_path}")
        return True
    else:
        print("\n⚠️  No changes needed")
        return False

if __name__ == "__main__":
    success = fix_data_quality_monitor()
    exit(0 if success else 1)

