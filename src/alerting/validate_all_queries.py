# Databricks notebook source
"""
Alert Query Validation Job

Validates all enabled alert queries before deployment.
This job should run BEFORE the alert sync job to catch:
1. SQL syntax errors
2. Security violations (DROP, DELETE, etc.)
3. Missing table references

If any queries fail validation, the job fails to prevent bad deployments.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Import query validator (pure Python, no SDK)
from query_validator import (
    ValidationResult,
    validate_alert_query,
    validate_template_placeholders,
)


def get_parameters() -> tuple[str, str, bool]:
    """Get job parameters from dbutils widgets."""
    dbutils.widgets.text("catalog", "health_monitor", "Target Catalog")
    dbutils.widgets.text("gold_schema", "gold", "Gold Schema")
    dbutils.widgets.text("fail_on_warning", "false", "Fail on Warnings (true/false)")

    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    fail_on_warning = dbutils.widgets.get("fail_on_warning").lower() == "true"

    return catalog, gold_schema, fail_on_warning


def validate_all_alert_queries(
    spark: SparkSession,
    catalog: str,
    gold_schema: str,
    fail_on_warning: bool = False,
) -> tuple[int, int, int]:
    """
    Validate all enabled alert queries.

    Args:
        spark: SparkSession
        catalog: Target catalog
        gold_schema: Target schema
        fail_on_warning: If True, treat warnings as errors

    Returns:
        (valid_count, warning_count, error_count)
    """
    cfg_table = f"{catalog}.{gold_schema}.alert_configurations"

    print("=" * 80)
    print("ALERT QUERY VALIDATION")
    print("=" * 80)
    print(f"Config table: {cfg_table}")
    print(f"Fail on warning: {fail_on_warning}")
    print("-" * 80)

    # Load enabled configs
    configs = (
        spark.table(cfg_table)
        .where(col("is_enabled") == True)  # noqa: E712
        .select(
            "alert_id",
            "alert_name",
            "alert_query_template",
            "custom_subject_template",
            "custom_body_template",
            "use_custom_template",
        )
        .collect()
    )

    print(f"Found {len(configs)} enabled alert configurations\n")

    valid_count = 0
    warning_count = 0
    error_count = 0
    errors_detail = []

    for i, cfg in enumerate(configs, 1):
        alert_id = cfg["alert_id"]
        alert_name = cfg["alert_name"]
        query_template = cfg["alert_query_template"]

        print(f"[{i}/{len(configs)}] Validating: {alert_id} - {alert_name}")

        # Validate query
        result = validate_alert_query(
            spark,
            query_template,
            catalog,
            gold_schema,
            check_syntax=True,
            check_references=True,
        )

        # Validate custom templates if enabled
        if cfg["use_custom_template"]:
            if cfg["custom_subject_template"]:
                is_valid, invalid = validate_template_placeholders(
                    cfg["custom_subject_template"]
                )
                if not is_valid:
                    result.warnings.append(f"Invalid subject placeholders: {invalid}")

            if cfg["custom_body_template"]:
                is_valid, invalid = validate_template_placeholders(
                    cfg["custom_body_template"]
                )
                if not is_valid:
                    result.warnings.append(f"Invalid body placeholders: {invalid}")

        # Report result
        if result.is_valid:
            if result.warnings:
                warning_count += 1
                print(f"  ⚠️  WARNINGS: {len(result.warnings)}")
                for w in result.warnings:
                    print(f"      - {w}")
                if fail_on_warning:
                    error_count += 1
                    errors_detail.append((alert_id, f"Warnings: {result.warnings}"))
            else:
                valid_count += 1
                print(f"  ✅ Valid ({len(result.tables_referenced)} tables)")
        else:
            error_count += 1
            print(f"  ❌ ERRORS:")
            for e in result.errors:
                print(f"      - {e}")
            errors_detail.append((alert_id, result.errors))

    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total:    {len(configs)}")
    print(f"✅ Valid:  {valid_count}")
    print(f"⚠️  Warnings: {warning_count}")
    print(f"❌ Errors: {error_count}")
    print("=" * 80)

    if errors_detail:
        print("\nFailed validations:")
        for alert_id, errors in errors_detail[:25]:
            print(f"  - {alert_id}: {errors}")

    return valid_count, warning_count, error_count


def main() -> None:
    """Main entry point."""
    catalog, gold_schema, fail_on_warning = get_parameters()
    spark = SparkSession.builder.getOrCreate()

    try:
        valid, warnings, errors = validate_all_alert_queries(
            spark, catalog, gold_schema, fail_on_warning
        )

        if errors > 0:
            raise RuntimeError(
                f"Query validation failed: {errors} error(s). "
                "Fix the queries before deploying alerts."
            )

        print("\n✅ All alert queries validated successfully!")
        dbutils.notebook.exit(f"SUCCESS: {valid} valid, {warnings} warnings")

    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        dbutils.notebook.exit(f"FAILED: {e}")
        raise


if __name__ == "__main__":
    main()

