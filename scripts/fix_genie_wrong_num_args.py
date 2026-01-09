#!/usr/bin/env python3
"""
Fix WRONG_NUM_ARGS errors in Genie Space JSON files.

This script adds missing parameters to TVF calls based on the correct signatures:
- get_off_hours_activity: requires (start_date, end_date, business_hours_start, business_hours_end)
- get_job_retry_analysis: requires (start_date, end_date)

Usage:
    python scripts/fix_genie_wrong_num_args.py
"""

import json
import os
import re
from pathlib import Path

# Fixes to apply
FIXES = [
    {
        "genie_space": "security_auditor",
        "question_num": "Q9",
        "tvf": "get_off_hours_activity",
        "current_params": 1,
        "required_params": 4,
        "fix_pattern": r"get_off_hours_activity\(\s*7\s*\)",
        "fix_replacement": """get_off_hours_activity(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  7,
  19
)""",
    },
    {
        "genie_space": "security_auditor",
        "question_num": "Q11",
        "tvf": "get_off_hours_activity",
        "current_params": 1,
        "required_params": 4,
        "fix_pattern": r"get_off_hours_activity\(\s*30\s*\)",
        "fix_replacement": """get_off_hours_activity(
  CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  7,
  19
)""",
    },
    {
        "genie_space": "job_health_monitor",
        "question_num": "Q10",
        "tvf": "get_job_retry_analysis",
        "current_params": 1,
        "required_params": 2,
        "fix_pattern": r"get_job_retry_analysis\(\s*30\s*\)",
        "fix_replacement": """get_job_retry_analysis(
  CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING)
)""",
    },
]


def main():
    """Main execution function."""
    print("=" * 80)
    print("GENIE SPACE WRONG_NUM_ARGS FIXER")
    print("=" * 80)
    print()
    
    fixes_applied = 0
    files_modified = set()
    
    for fix in FIXES:
        genie_space = fix["genie_space"]
        question_num = fix["question_num"]
        tvf = fix["tvf"]
        
        file_path = f"src/genie/{genie_space}_genie_export.json"
        
        if not os.path.exists(file_path):
            print(f"⚠️  {file_path} not found")
            continue
        
        # Read JSON
        with open(file_path, 'r') as f:
            content = json.load(f)
        
        # Find the question by index
        questions = content.get("benchmarks", {}).get("questions", [])
        q_index = int(question_num.replace("Q", "")) - 1
        
        if q_index < 0 or q_index >= len(questions):
            print(f"⚠️  {genie_space} {question_num}: Question not found")
            continue
        
        question = questions[q_index]
        
        # Get the SQL
        if "answer" in question and isinstance(question["answer"], list):
            for answer_item in question["answer"]:
                if "content" in answer_item and isinstance(answer_item["content"], list):
                    original_sql = answer_item["content"][0]
                    
                    # Apply the fix
                    if re.search(fix["fix_pattern"], original_sql):
                        modified_sql = re.sub(fix["fix_pattern"], fix["fix_replacement"], original_sql)
                        
                        if modified_sql != original_sql:
                            answer_item["content"][0] = modified_sql
                            fixes_applied += 1
                            files_modified.add(file_path)
                            print(f"✅ Fixed {genie_space} {question_num}: {tvf} ({fix['current_params']} → {fix['required_params']} params)")
                        else:
                            print(f"⚠️  {genie_space} {question_num}: Pattern not matched")
                    else:
                        print(f"⚠️  {genie_space} {question_num}: Pattern '{fix['fix_pattern']}' not found in SQL")
        
        # Write back if modified
        if file_path in files_modified:
            with open(file_path, 'w') as f:
                json.dump(content, f, indent=2)
    
    print()
    print("=" * 80)
    print(f"✅ COMPLETE: Applied {fixes_applied} fixes across {len(files_modified)} files")
    print("=" * 80)
    print()
    
    # Generate report
    report_path = Path(__file__).parent.parent / "docs" / "deployment" / "GENIE_PARAM_FIXES_APPLIED.md"
    with open(report_path, 'w') as f:
        f.write("# Genie Space WRONG_NUM_ARGS Fixes Report\n\n")
        f.write(f"**Date:** {os.popen('date').read().strip()}\n")
        f.write(f"**Total Fixes Applied:** {fixes_applied}\n")
        f.write(f"**Files Modified:** {len(files_modified)}\n\n")
        
        f.write("## Fixes Applied:\n\n")
        for fix in FIXES:
            f.write(f"- **{fix['genie_space']} {fix['question_num']}:** `{fix['tvf']}` ")
            f.write(f"({fix['current_params']} → {fix['required_params']} params)\n")
        
        f.write("\n## Files Modified:\n\n")
        for file_path in sorted(files_modified):
            f.write(f"- `{file_path}`\n")
        
        f.write("\n## Next Steps:\n\n")
        f.write("1. Deploy bundle: `databricks bundle deploy -t dev`\n")
        f.write("2. Re-run validation to verify fixes\n")
    
    print(f"📄 Report written to: {report_path}")
    print()


if __name__ == "__main__":
    main()
