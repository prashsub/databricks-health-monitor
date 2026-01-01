# Databricks notebook source
"""
Alert Query Validator
=====================

Proactively validates all alert queries in the configuration table by running
EXPLAIN on each query. This catches column reference errors, table not found errors,
and syntax errors BEFORE alerts are deployed.

Usage:
1. Run after seeding alerts to catch issues early
2. Run before deployment to validate all queries
3. Can be run in dry-run mode for CI/CD pipelines
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from typing import List, Tuple, Optional
import re


def validate_single_query(
    spark: SparkSession,
    alert_id: str,
    query: str,
) -> Tuple[str, bool, Optional[str]]:
    """
    Validate a single query using EXPLAIN.
    
    Returns:
        Tuple of (alert_id, is_valid, error_message)
    """
    try:
        # Use EXPLAIN to validate without executing
        explain_sql = f"EXPLAIN {query}"
        spark.sql(explain_sql)
        return (alert_id, True, None)
    except Exception as e:
        # Debug: Print the query that failed for troubleshooting
        if "PARSE_SYNTAX_ERROR" in str(e):
            print(f"DEBUG {alert_id} - Query causing syntax error:")
            print(f"  First 300 chars: {query[:300]}")
        error_msg = str(e)
        # Extract the most useful part of the error
        if "UNRESOLVED_COLUMN" in error_msg:
            # Extract column name suggestion
            match = re.search(r"with name `([^`]+)`", error_msg)
            col_name = match.group(1) if match else "unknown"
            return (alert_id, False, f"Column not found: `{col_name}` - {error_msg[:200]}")
        elif "TABLE_OR_VIEW_NOT_FOUND" in error_msg:
            match = re.search(r"Table or view not found: `?([^`\s]+)`?", error_msg)
            table_name = match.group(1) if match else "unknown"
            return (alert_id, False, f"Table not found: `{table_name}`")
        elif "PARSE_SYNTAX_ERROR" in error_msg:
            return (alert_id, False, f"Syntax error: {error_msg[:200]}")
        else:
            return (alert_id, False, f"Error: {error_msg[:300]}")


def validate_all_alerts(
    spark: SparkSession,
    catalog: str,
    gold_schema: str,
    only_enabled: bool = True,
) -> Tuple[List[Tuple[str, bool, Optional[str]]], int, int]:
    """
    Validate all alert queries in the configuration table.
    
    Args:
        spark: SparkSession
        catalog: Target catalog
        gold_schema: Target schema
        only_enabled: If True, only validate enabled alerts
        
    Returns:
        Tuple of (results_list, valid_count, invalid_count)
    """
    cfg_table = f"{catalog}.{gold_schema}.alert_configurations"
    
    # Load alerts
    query = spark.table(cfg_table)
    if only_enabled:
        query = query.where(col("is_enabled") == True)  # noqa: E712
    
    alerts = query.select(
        "alert_id", 
        "alert_name", 
        "alert_query_template",
        "agent_domain",
        "severity"
    ).orderBy("agent_domain", "alert_id").collect()
    
    print("=" * 80)
    print("ALERT QUERY VALIDATOR")
    print("=" * 80)
    print(f"Catalog:        {catalog}")
    print(f"Schema:         {gold_schema}")
    print(f"Only enabled:   {only_enabled}")
    print(f"Alerts to test: {len(alerts)}")
    print("-" * 80)
    
    results: List[Tuple[str, bool, Optional[str]]] = []
    valid_count = 0
    invalid_count = 0
    
    for i, row in enumerate(alerts, 1):
        alert_id = row["alert_id"]
        alert_name = row["alert_name"]
        query_template = row["alert_query_template"]
        domain = row["agent_domain"]
        severity = row["severity"]
        
        # Render any remaining template variables (should already be rendered)
        rendered_query = query_template.replace("${catalog}", catalog).replace("${gold_schema}", gold_schema)
        
        print(f"\n[{i}/{len(alerts)}] Testing: {alert_id} - {alert_name}")
        print(f"           Domain: {domain}, Severity: {severity}")
        
        alert_id, is_valid, error = validate_single_query(spark, alert_id, rendered_query)
        results.append((alert_id, is_valid, error))
        
        if is_valid:
            valid_count += 1
            print(f"           ✅ VALID")
        else:
            invalid_count += 1
            print(f"           ❌ INVALID: {error}")
    
    return results, valid_count, invalid_count


def save_validation_results(
    spark: SparkSession,
    catalog: str,
    gold_schema: str,
    results: List[Tuple[str, bool, Optional[str]]],
) -> None:
    """Save validation results to a table for easy querying."""
    from datetime import datetime
    from pyspark.sql.types import StructType, StructField, StringType, BooleanType, TimestampType
    
    schema = StructType([
        StructField("alert_id", StringType(), False),
        StructField("is_valid", BooleanType(), False),
        StructField("error_message", StringType(), True),
        StructField("validated_at", TimestampType(), False),
    ])
    
    data = [
        (alert_id, is_valid, error, datetime.now())
        for alert_id, is_valid, error in results
    ]
    
    df = spark.createDataFrame(data, schema)
    
    # Write to validation results table (overwrite each run)
    table_name = f"{catalog}.{gold_schema}.alert_validation_results"
    df.write.mode("overwrite").saveAsTable(table_name)
    print(f"\n📊 Validation results saved to: {table_name}")


def generate_validation_report(
    results: List[Tuple[str, bool, Optional[str]]],
    valid_count: int,
    invalid_count: int,
) -> str:
    """Generate a detailed validation report."""
    report = []
    report.append("\n" + "=" * 80)
    report.append("VALIDATION SUMMARY")
    report.append("=" * 80)
    report.append(f"Total alerts:   {len(results)}")
    report.append(f"Valid:          {valid_count} ✅")
    report.append(f"Invalid:        {invalid_count} ❌")
    report.append(f"Success rate:   {valid_count / len(results) * 100:.1f}%")
    
    if invalid_count > 0:
        report.append("\n" + "-" * 80)
        report.append("FAILED ALERTS (requires fixing before deployment)")
        report.append("-" * 80)
        
        for alert_id, is_valid, error in results:
            if not is_valid:
                report.append(f"\n❌ {alert_id}")
                report.append(f"   Error: {error}")
        
        report.append("\n" + "-" * 80)
        report.append("RECOMMENDED FIXES:")
        report.append("-" * 80)
        
        # Categorize errors
        column_errors = [(a, e) for a, v, e in results if not v and e and "Column not found" in e]
        table_errors = [(a, e) for a, v, e in results if not v and e and "Table not found" in e]
        syntax_errors = [(a, e) for a, v, e in results if not v and e and "Syntax error" in e]
        other_errors = [(a, e) for a, v, e in results if not v and e and 
                        "Column not found" not in e and 
                        "Table not found" not in e and 
                        "Syntax error" not in e]
        
        if column_errors:
            report.append(f"\n1. COLUMN ERRORS ({len(column_errors)} alerts)")
            report.append("   → Check column names against actual table schemas")
            report.append("   → Run: DESCRIBE TABLE catalog.schema.table_name")
            for alert_id, error in column_errors[:5]:
                report.append(f"      - {alert_id}: {error[:100]}")
        
        if table_errors:
            report.append(f"\n2. TABLE ERRORS ({len(table_errors)} alerts)")
            report.append("   → Verify table exists and user has access")
            report.append("   → Check catalog and schema names")
            for alert_id, error in table_errors[:5]:
                report.append(f"      - {alert_id}: {error[:100]}")
        
        if syntax_errors:
            report.append(f"\n3. SYNTAX ERRORS ({len(syntax_errors)} alerts)")
            report.append("   → Review SQL syntax in alert_query_template")
            for alert_id, error in syntax_errors[:5]:
                report.append(f"      - {alert_id}: {error[:100]}")
        
        if other_errors:
            report.append(f"\n4. OTHER ERRORS ({len(other_errors)} alerts)")
            for alert_id, error in other_errors[:5]:
                report.append(f"      - {alert_id}: {error[:100]}")
    
    report.append("\n" + "=" * 80)
    
    return "\n".join(report)


def main() -> None:
    """Main entry point."""
    # Initialize widgets
    dbutils.widgets.text("catalog", "prashanth_subrahmanyam_catalog", "Catalog")  # type: ignore[name-defined]
    dbutils.widgets.text("gold_schema", "health_monitor_gold", "Gold Schema")  # type: ignore[name-defined]
    dbutils.widgets.text("only_enabled", "true", "Only enabled alerts (true/false)")  # type: ignore[name-defined]
    dbutils.widgets.text("fail_on_error", "true", "Fail if any invalid (true/false)")  # type: ignore[name-defined]
    
    catalog = dbutils.widgets.get("catalog")  # type: ignore[name-defined]
    gold_schema = dbutils.widgets.get("gold_schema")  # type: ignore[name-defined]
    only_enabled = dbutils.widgets.get("only_enabled").lower() == "true"  # type: ignore[name-defined]
    fail_on_error = dbutils.widgets.get("fail_on_error").lower() == "true"  # type: ignore[name-defined]
    
    spark = SparkSession.builder.getOrCreate()
    
    # Validate all alerts
    results, valid_count, invalid_count = validate_all_alerts(
        spark, catalog, gold_schema, only_enabled
    )
    
    # Save results to table for easy querying
    save_validation_results(spark, catalog, gold_schema, results)
    
    # Generate and print report
    report = generate_validation_report(results, valid_count, invalid_count)
    print(report)
    
    # Optionally fail
    if fail_on_error and invalid_count > 0:
        raise RuntimeError(
            f"Alert validation failed: {invalid_count} alerts have invalid queries. "
            f"See report above for details."
        )
    
    # Include failed alert IDs and errors in exit message for debugging
    failed_alerts = [(alert_id, error[:80] if error else "Unknown") for alert_id, is_valid, error in results if not is_valid]
    if failed_alerts:
        failed_summary = "; ".join([f"{aid}: {err}" for aid, err in failed_alerts])
        dbutils.notebook.exit(f"Validated {len(results)} alerts: {valid_count} valid, {invalid_count} invalid. FAILED: {failed_summary}")  # type: ignore[name-defined]
    else:
        dbutils.notebook.exit(f"Validated {len(results)} alerts: {valid_count} valid, {invalid_count} invalid")  # type: ignore[name-defined]


if __name__ == "__main__":
    main()

