#!/usr/bin/env python3
"""
Update Job Health Monitor Genie Space benchmarks with:
- 20 basic questions (8 TVF, 4 MV, 3 ML, 2 Monitoring, 2 Fact, 1 Dim)
- 5 deep research questions
Total: 25 questions

Based on actual_assets_inventory.json
"""

import json
import uuid
from pathlib import Path

def generate_id():
    """Generate a 32-char hex ID without dashes."""
    return uuid.uuid4().hex

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
JSON_FILE = PROJECT_ROOT / "src/genie/job_health_monitor_genie_export.json"
SPEC_FILE = PROJECT_ROOT / "src/genie/job_health_monitor_genie.md"

# Define benchmarks based on actual assets
BENCHMARKS = {
    "tvf": [
        # 8 TVF questions
        ("What jobs have failed recently?", "SELECT * FROM TABLE(get_failed_jobs(7)) LIMIT 20;"),
        ("What is the job success rate?", "SELECT * FROM TABLE(get_job_success_rate(30)) LIMIT 20;"),
        ("Show job duration percentiles", "SELECT * FROM TABLE(get_job_duration_percentiles(30)) LIMIT 20;"),
        ("Are jobs meeting their SLAs?", "SELECT * FROM TABLE(get_job_sla_compliance(30)) LIMIT 20;"),
        ("Show job failure trends", "SELECT * FROM TABLE(get_job_failure_trends(30)) LIMIT 20;"),
        ("Identify outlier job runs", "SELECT * FROM TABLE(get_job_outlier_runs(30)) LIMIT 20;"),
        ("What are job repair costs?", "SELECT * FROM TABLE(get_job_repair_costs(30)) LIMIT 20;"),
        ("Which jobs lack autoscaling?", "SELECT * FROM TABLE(get_jobs_without_autoscaling()) LIMIT 20;"),
    ],
    "metric_view": [
        # 4 Metric View questions
        ("Show overall job performance metrics", "SELECT * FROM mv_job_performance LIMIT 20;"),
        ("Which jobs have the most failures?", "SELECT job_name, failure_count FROM mv_job_performance ORDER BY failure_count DESC LIMIT 10;"),
        ("What is the overall success rate?", "SELECT AVG(success_rate) as avg_success_rate FROM mv_job_performance;"),
        ("Show top jobs by run count", "SELECT job_name, run_count FROM mv_job_performance ORDER BY run_count DESC LIMIT 10;"),
    ],
    "ml": [
        # 3 ML table questions
        ("Which jobs might fail?", "SELECT * FROM job_failure_predictions ORDER BY prediction DESC LIMIT 20;"),
        ("Show retry success predictions", "SELECT * FROM retry_success_predictions ORDER BY prediction DESC LIMIT 20;"),
        ("Are there SLA breach risks?", "SELECT * FROM sla_breach_predictions ORDER BY prediction DESC LIMIT 20;"),
    ],
    "monitoring": [
        # 2 Monitoring table questions
        ("Show job profile metrics", "SELECT * FROM fact_job_run_timeline_profile_metrics WHERE log_type = 'INPUT' LIMIT 20;"),
        ("Show job drift metrics", "SELECT * FROM fact_job_run_timeline_drift_metrics LIMIT 20;"),
    ],
    "fact": [
        # 2 Fact table questions
        ("Show recent job runs", "SELECT job_id, job_name, result_state, run_duration_seconds FROM fact_job_run_timeline ORDER BY period_start_time DESC LIMIT 20;"),
        ("Show recent task runs", "SELECT task_key, result_state, run_duration_seconds FROM fact_job_task_run_timeline ORDER BY period_start_time DESC LIMIT 20;"),
    ],
    "dim": [
        # 1 Dimension table question
        ("List all jobs", "SELECT job_id, job_name FROM dim_job ORDER BY job_name LIMIT 20;"),
    ],
    "deep_research": [
        # 5 Deep Research questions
        (
            "🔬 DEEP RESEARCH: Comprehensive job reliability analysis",
            """WITH job_stats AS (
  SELECT job_name, run_count, success_count, failure_count,
         ROUND(success_count * 100.0 / NULLIF(run_count, 0), 1) as success_rate
  FROM mv_job_performance
)
SELECT job_name, run_count, failure_count, success_rate
FROM job_stats
WHERE failure_count > 0
ORDER BY failure_count DESC
LIMIT 15;"""
        ),
        (
            "🔬 DEEP RESEARCH: Job failure patterns with ML predictions",
            """SELECT jf.job_id, jf.prediction as failure_probability,
       j.job_name
FROM job_failure_predictions jf
JOIN dim_job j ON jf.job_id = j.job_id
WHERE jf.prediction > 0.5
ORDER BY jf.prediction DESC
LIMIT 15;"""
        ),
        (
            "🔬 DEEP RESEARCH: SLA breach analysis with predictions",
            """SELECT sb.job_id, sb.prediction as breach_probability,
       j.job_name
FROM sla_breach_predictions sb
JOIN dim_job j ON sb.job_id = j.job_id
WHERE sb.prediction > 0.3
ORDER BY sb.prediction DESC
LIMIT 15;"""
        ),
        (
            "🔬 DEEP RESEARCH: Job duration analysis with predictions",
            """SELECT d.job_id, d.prediction as predicted_duration,
       j.job_name
FROM duration_predictions d
JOIN dim_job j ON d.job_id = j.job_id
ORDER BY d.prediction DESC
LIMIT 15;"""
        ),
        (
            "🔬 DEEP RESEARCH: Job reliability dashboard combining metrics and predictions",
            """SELECT j.job_name,
       mv.run_count,
       mv.success_count,
       mv.failure_count,
       ROUND(mv.success_count * 100.0 / NULLIF(mv.run_count, 0), 1) as success_rate
FROM mv_job_performance mv
JOIN dim_job j ON mv.job_id = j.job_id
WHERE mv.run_count >= 5
ORDER BY mv.failure_count DESC
LIMIT 20;"""
        ),
    ]
}

def build_benchmark_questions():
    """Build the benchmark questions array."""
    questions = []
    
    # Add all question types
    for category, items in BENCHMARKS.items():
        for question_text, sql in items:
            questions.append({
                "id": generate_id(),
                "question": [question_text],
                "answer": [{
                    "format": "SQL",
                    "content": [sql]
                }]
            })
    
    return questions

def update_json_file():
    """Update the JSON file with new benchmarks."""
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)
    
    # Replace benchmarks
    questions = build_benchmark_questions()
    data['benchmarks'] = {'questions': questions}
    
    with open(JSON_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Updated {JSON_FILE}")
    print(f"   Total benchmarks: {len(questions)}")
    
    # Count by type
    counts = {k: len(v) for k, v in BENCHMARKS.items()}
    print(f"   Distribution: {counts}")
    
    return questions

def generate_spec_section_h(questions):
    """Generate the Section H markdown content."""
    lines = [
        "## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████",
        "",
        "> **TOTAL: 25 Questions (20 Normal + 5 Deep Research)**",
        "> **Grounded in:** mv_job_performance, TVFs, ML Tables, Lakehouse Monitors, Fact/Dim Tables",
        "",
        "### ✅ Normal Benchmark Questions (Q1-Q20)",
        ""
    ]
    
    q_num = 1
    for q in questions[:20]:  # First 20 are normal questions
        question_text = q['question'][0]
        sql = q['answer'][0]['content'][0]
        
        lines.append(f"### Question {q_num}: \"{question_text}\"")
        lines.append("**Expected SQL:**")
        lines.append("```sql")
        lines.append(sql)
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")
        q_num += 1
    
    # Deep research section
    lines.append("### 🔬 Deep Research Questions (Q21-Q25)")
    lines.append("")
    
    for q in questions[20:]:  # Last 5 are deep research
        question_text = q['question'][0]
        sql = q['answer'][0]['content'][0]
        
        lines.append(f"### Question {q_num}: \"{question_text}\"")
        lines.append("**Expected SQL:**")
        lines.append("```sql")
        lines.append(sql)
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")
        q_num += 1
    
    return "\n".join(lines)

def update_spec_file(questions):
    """Update the spec file Section H."""
    with open(SPEC_FILE, 'r') as f:
        content = f.read()
    
    # Find Section H
    import re
    section_h_pattern = r'## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████.*?(?=## ✅ DELIVERABLE CHECKLIST|## Agent Domain Tag|$)'
    
    new_section_h = generate_spec_section_h(questions)
    
    if re.search(section_h_pattern, content, re.DOTALL):
        content = re.sub(section_h_pattern, new_section_h, content, flags=re.DOTALL)
        print(f"✅ Updated Section H in {SPEC_FILE}")
    else:
        print(f"⚠️ Could not find Section H in {SPEC_FILE}")
        return
    
    with open(SPEC_FILE, 'w') as f:
        f.write(content)

def main():
    print("=" * 60)
    print("JOB HEALTH MONITOR BENCHMARK UPDATE")
    print("=" * 60)
    print()
    
    # Update JSON
    questions = update_json_file()
    print()
    
    # Update spec file
    update_spec_file(questions)
    print()
    
    print("=" * 60)
    print("✅ JOB HEALTH MONITOR BENCHMARKS UPDATED")
    print("=" * 60)

if __name__ == "__main__":
    main()
