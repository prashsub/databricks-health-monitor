#!/usr/bin/env python3
"""
Fix Genie Export Deployment Issues
===================================
Removes references to non-existent tables and fixes duplicate IDs.

Issues to fix:
1. dim_date - doesn't exist, remove from tables section
2. ML tables that don't exist:
   - quality_anomaly_predictions
   - access_anomaly_predictions
   - user_risk_scores (table, not TVF)
   - access_classifications
3. Duplicate question IDs
"""

import json
from pathlib import Path
import re

# Tables that don't exist and should be removed
NON_EXISTENT_TABLES = [
    "dim_date",
    "quality_anomaly_predictions",
    "access_anomaly_predictions",
    "user_risk_scores",  # The TABLE doesn't exist, but the TVF get_user_risk_scores does
    "access_classifications",
    # Monitoring tables that don't exist
    "fact_table_quality_profile_metrics",
    "fact_table_quality_drift_metrics",
    "fact_governance_metrics_profile_metrics",
    # ML tables that don't exist
    "freshness_alert_predictions",
    "job_failure_predictions",
    "duration_predictions",
    "sla_breach_predictions",
    "retry_success_predictions",
    "pipeline_health_predictions",
    "cost_anomaly_predictions",
    # Tables/views that might not exist
    "dim_user",
]

# Metric views that don't exist
NON_EXISTENT_METRIC_VIEWS = [
    "mv_data_quality",
    "mv_governance_analytics",
]

GENIE_DIR = Path(__file__).parent.parent / "src" / "genie"

def remove_table_from_data_sources(data: dict, table_pattern: str) -> int:
    """Remove a table from data_sources.tables by identifier pattern."""
    if "data_sources" not in data or "tables" not in data["data_sources"]:
        return 0

    tables = data["data_sources"]["tables"]
    original_count = len(tables)

    # Filter out tables matching the pattern
    data["data_sources"]["tables"] = [
        t for t in tables
        if table_pattern not in t.get("identifier", "")
    ]

    removed = original_count - len(data["data_sources"]["tables"])
    return removed


def remove_metric_view_from_data_sources(data: dict, mv_pattern: str) -> int:
    """Remove a metric view from data_sources.metric_views by identifier pattern."""
    if "data_sources" not in data or "metric_views" not in data["data_sources"]:
        return 0

    metric_views = data["data_sources"]["metric_views"]
    original_count = len(metric_views)

    # Filter out metric views matching the pattern
    data["data_sources"]["metric_views"] = [
        mv for mv in metric_views
        if mv_pattern not in mv.get("identifier", "")
    ]

    removed = original_count - len(data["data_sources"]["metric_views"])
    return removed


def references_ml_table(sql_content, ml_tables: list) -> bool:
    """Check if SQL content references any non-existent ML tables."""
    if sql_content is None:
        return False
    sql_text = " ".join(sql_content) if isinstance(sql_content, list) else sql_content
    sql_lower = sql_text.lower()

    for table in ml_tables:
        if table.lower() in sql_lower:
            return True
    return False


def remove_questions_with_ml_refs(questions_list: list, ml_tables: list, section_name: str) -> tuple:
    """Remove questions that reference non-existent ML tables."""
    removed_questions = []
    original_count = len(questions_list)

    filtered_questions = []
    for q in questions_list:
        has_ml_ref = False

        # Check various SQL field formats
        # Format 1: answer[].content
        for answer in q.get("answer", []):
            content = answer.get("content", [])
            if references_ml_table(content, ml_tables):
                has_ml_ref = True
                break

        # Format 2: sql field
        if not has_ml_ref:
            sql = q.get("sql", [])
            if references_ml_table(sql, ml_tables):
                has_ml_ref = True

        # Format 3: query field
        if not has_ml_ref:
            query = q.get("query", [])
            if references_ml_table(query, ml_tables):
                has_ml_ref = True

        if has_ml_ref:
            q_text = q.get("question", ["unknown"])
            if isinstance(q_text, list):
                q_text = " ".join(q_text)
            removed_questions.append((q.get("id", "unknown"), q_text[:50], section_name))
        else:
            filtered_questions.append(q)

    return filtered_questions, removed_questions


def remove_benchmark_questions_with_ml_refs(data: dict, ml_tables: list) -> tuple:
    """Remove benchmark questions that reference non-existent ML tables."""
    total_removed = 0
    all_removed_details = []

    # Check benchmarks.questions
    if "benchmarks" in data and "questions" in data["benchmarks"]:
        data["benchmarks"]["questions"], removed = remove_questions_with_ml_refs(
            data["benchmarks"]["questions"], ml_tables, "benchmarks.questions"
        )
        total_removed += len(removed)
        all_removed_details.extend(removed)

    # Note: config.sample_questions is just a list of strings, not SQL objects
    # So we skip it - no SQL to check

    # Check instructions.example_question_sqls
    if "instructions" in data and "example_question_sqls" in data["instructions"]:
        data["instructions"]["example_question_sqls"], removed = remove_questions_with_ml_refs(
            data["instructions"]["example_question_sqls"], ml_tables, "instructions.example_question_sqls"
        )
        total_removed += len(removed)
        all_removed_details.extend(removed)

    # Check curated_questions (top-level)
    if "curated_questions" in data:
        data["curated_questions"], removed = remove_questions_with_ml_refs(
            data["curated_questions"], ml_tables, "curated_questions"
        )
        total_removed += len(removed)
        all_removed_details.extend(removed)

    return total_removed, all_removed_details


def fix_duplicate_question_ids(data: dict) -> int:
    """Fix duplicate question IDs by generating unique ones."""
    fixes = 0

    def fix_list(questions_list, prefix):
        nonlocal fixes
        seen_ids = set()
        for i, q in enumerate(questions_list):
            q_id = q.get("id", "")
            if q_id in seen_ids:
                # Generate new unique ID
                new_id = f"{prefix}{i:02d}{q_id[4:20]}_{i:04d}"[:32]
                q["id"] = new_id
                fixes += 1
                print(f"    Fixed duplicate ID: {q_id[:20]}... -> {new_id[:20]}...")
            seen_ids.add(q_id)

    # Check all question sections
    if "benchmarks" in data and "questions" in data["benchmarks"]:
        fix_list(data["benchmarks"]["questions"], "bm")

    # Note: config.sample_questions is just strings, no IDs to fix

    if "instructions" in data and "example_question_sqls" in data["instructions"]:
        fix_list(data["instructions"]["example_question_sqls"], "ex")

    if "curated_questions" in data:
        fix_list(data["curated_questions"], "cq")

    return fixes


def process_genie_export(filepath: Path) -> dict:
    """Process a single genie export file and return stats."""
    print(f"\n📁 Processing: {filepath.name}")

    with open(filepath, 'r') as f:
        data = json.load(f)

    stats = {
        "tables_removed": 0,
        "metric_views_removed": 0,
        "questions_removed": 0,
        "duplicate_ids_fixed": 0,
        "removed_question_details": []
    }

    # 1. Remove non-existent tables from data_sources
    for table in NON_EXISTENT_TABLES:
        removed = remove_table_from_data_sources(data, table)
        if removed > 0:
            print(f"   ✓ Removed {removed} table(s) matching '{table}'")
            stats["tables_removed"] += removed

    # 1b. Remove non-existent metric views from data_sources
    for mv in NON_EXISTENT_METRIC_VIEWS:
        removed = remove_metric_view_from_data_sources(data, mv)
        if removed > 0:
            print(f"   ✓ Removed {removed} metric view(s) matching '{mv}'")
            stats["metric_views_removed"] += removed

    # 2. Remove questions referencing non-existent ML tables (from all sections)
    ml_tables = [t for t in NON_EXISTENT_TABLES if t != "dim_date"]
    removed, details = remove_benchmark_questions_with_ml_refs(data, ml_tables)
    if removed > 0:
        print(f"   ✓ Removed {removed} question(s) with ML table refs")
        for d in details:
            print(f"      - {d[2]}: {d[1]}")
        stats["questions_removed"] += removed
        stats["removed_question_details"] = details

    # 3. Fix duplicate question IDs
    fixed = fix_duplicate_question_ids(data)
    if fixed > 0:
        print(f"   ✓ Fixed {fixed} duplicate question ID(s)")
        stats["duplicate_ids_fixed"] += fixed

    # Write back if changes were made
    if stats["tables_removed"] or stats["metric_views_removed"] or stats["questions_removed"] or stats["duplicate_ids_fixed"]:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"   💾 Saved changes")
    else:
        print(f"   ⏭️  No changes needed")

    return stats


def main():
    print("=" * 60)
    print("GENIE EXPORT DEPLOYMENT FIX")
    print("=" * 60)
    print(f"\nRemoving references to non-existent tables:")
    for t in NON_EXISTENT_TABLES:
        print(f"  - {t}")
    print(f"\nRemoving references to non-existent metric views:")
    for mv in NON_EXISTENT_METRIC_VIEWS:
        print(f"  - {mv}")

    # Find all genie export files
    export_files = list(GENIE_DIR.glob("*_genie_export.json"))
    print(f"\nFound {len(export_files)} export files")

    total_stats = {
        "tables_removed": 0,
        "metric_views_removed": 0,
        "questions_removed": 0,
        "duplicate_ids_fixed": 0
    }

    for filepath in sorted(export_files):
        stats = process_genie_export(filepath)
        total_stats["tables_removed"] += stats["tables_removed"]
        total_stats["metric_views_removed"] += stats["metric_views_removed"]
        total_stats["questions_removed"] += stats["questions_removed"]
        total_stats["duplicate_ids_fixed"] += stats["duplicate_ids_fixed"]

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Tables removed: {total_stats['tables_removed']}")
    print(f"Metric views removed: {total_stats['metric_views_removed']}")
    print(f"Questions removed: {total_stats['questions_removed']}")
    print(f"Duplicate IDs fixed: {total_stats['duplicate_ids_fixed']}")
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
