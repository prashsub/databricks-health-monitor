#!/usr/bin/env python3
"""
Fix security_auditor validation errors.

Errors to fix:
1. Q21 & Q22: get_pii_access_events → get_sensitive_table_access
2. Q23: hour_of_day doesn't exist in get_off_hours_activity output
3. Q24: Syntax error - extra ) before GROUP BY
4. Q25: get_pii_access_events + missing ) in TVF call
"""

import json
import re
from pathlib import Path

def fix_security_auditor():
    """Fix all security_auditor errors."""
    json_path = Path("src/genie/security_auditor_genie_export.json")
    
    with open(json_path) as f:
        data = json.load(f)
    
    questions = data.get("benchmarks", {}).get("questions", [])
    changes_made = False
    
    # Q21 & Q22: Replace get_pii_access_events with get_sensitive_table_access
    for idx in [20, 21]:  # Q21, Q22 (0-indexed)
        if len(questions) > idx:
            q = questions[idx]
            answer = q.get("answer", [])
            if answer:
                sql = answer[0].get("content", [""])[0]
                old_sql = sql
                
                # Replace TVF name
                sql = sql.replace("get_pii_access_events", "get_sensitive_table_access")
                
                # The TVF returns: access_date, user_email, table_name, action, access_count, source_ips, is_off_hours
                # No need to change column names - they should match
                
                if sql != old_sql:
                    answer[0]["content"] = [sql]
                    print(f"✅ security_auditor Q{idx+1}: Fixed get_pii_access_events → get_sensitive_table_access")
                    changes_made = True
    
    # Q23: Remove hour_of_day (doesn't exist in get_off_hours_activity)
    if len(questions) > 22:
        q23 = questions[22]
        answer = q23.get("answer", [])
        if answer:
            sql = answer[0].get("content", [""])[0]
            old_sql = sql
            
            # Remove hour_of_day from SELECT list
            sql = re.sub(r',\s*hour_of_day', '', sql)
            sql = re.sub(r'hour_of_day,\s*', '', sql)
            
            if sql != old_sql:
                answer[0]["content"] = [sql]
                print("✅ security_auditor Q23: Removed hour_of_day column")
                changes_made = True
    
    # Q24: Fix syntax error - remove extra ) before GROUP BY
    if len(questions) > 23:
        q24 = questions[23]
        answer = q24.get("answer", [])
        if answer:
            sql = answer[0].get("content", [""])[0]
            old_sql = sql
            
            # Pattern: WHERE ... INTERVAL 7 DAYS)\n  GROUP BY
            # Should be: WHERE ... INTERVAL 7 DAYS\n  GROUP BY
            sql = re.sub(
                r'(WHERE evaluation_date >= CURRENT_DATE\(\) - INTERVAL 7 DAYS)\)\s*\n\s*(GROUP BY)',
                r'\1\n  \2',
                sql
            )
            
            if sql != old_sql:
                answer[0]["content"] = [sql]
                print("✅ security_auditor Q24: Fixed extra ) before GROUP BY")
                changes_made = True
    
    # Q25: Fix get_pii_access_events and missing ) in TVF call
    if len(questions) > 24:
        q25 = questions[24]
        answer = q25.get("answer", [])
        if answer:
            sql = answer[0].get("content", [""])[0]
            old_sql = sql
            
            # Replace TVF name
            sql = sql.replace("get_pii_access_events", "get_sensitive_table_access")
            
            # Fix missing ) after TVF parameters
            # Pattern: FROM get_sensitive_table_access(...)\n),
            # Check if the ) is missing after the CAST(CURRENT_DATE() AS STRING) line
            sql = re.sub(
                r"(FROM get_sensitive_table_access\([^)]+CAST\(CURRENT_DATE\(\) AS STRING\))\s*\n\s*\),",
                r"\1)\n),",
                sql
            )
            
            if sql != old_sql:
                answer[0]["content"] = [sql]
                print("✅ security_auditor Q25: Fixed get_pii_access_events and added missing )")
                changes_made = True
    
    if changes_made:
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    return False

def main():
    print("=" * 80)
    print("FIXING SECURITY_AUDITOR VALIDATION ERRORS")
    print("=" * 80)
    print()
    
    if fix_security_auditor():
        print()
        print("=" * 80)
        print("✅ Fixed all security_auditor errors (5 queries)")
        print("=" * 80)
    else:
        print("⚠️  No changes made")

if __name__ == "__main__":
    main()
