"""
Tests for Gold Layer Merge Helpers
===================================

Run with: pytest tests/pipelines/test_merge_helpers.py -v

Test coverage:
- Deduplication logic
- Incremental load high-water mark handling
- MERGE preparation
- Schema validation
- Foreign key validation
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Skip this module if pyspark is not installed (for unit tests without Spark)
pyspark = pytest.importorskip("pyspark", reason="PySpark required for integration tests")
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    TimestampType, DoubleType
)


class TestDeduplication:
    """Tests for deduplication logic."""

    @pytest.mark.integration
    def test_deduplicate_by_single_key(self, spark):
        """Test deduplication with single key column."""
        data = [
            {"id": 1, "value": 100, "timestamp": datetime(2024, 1, 1, 10)},
            {"id": 1, "value": 200, "timestamp": datetime(2024, 1, 1, 11)},
            {"id": 2, "value": 300, "timestamp": datetime(2024, 1, 1, 12)},
        ]
        df = spark.createDataFrame(data)

        # Keep latest by timestamp
        from pyspark.sql.window import Window
        w = Window.partitionBy("id").orderBy(F.desc("timestamp"))
        deduped = df.withColumn("rn", F.row_number().over(w)).filter(F.col("rn") == 1).drop("rn")

        assert deduped.count() == 2

        # Verify we kept the latest for id=1
        row = deduped.filter(F.col("id") == 1).first()
        assert row["value"] == 200

    @pytest.mark.integration
    def test_deduplicate_by_composite_key(self, spark):
        """Test deduplication with composite key."""
        data = [
            {"workspace_id": "ws1", "date": "2024-01-01", "sku": "A", "value": 100, "ts": 1},
            {"workspace_id": "ws1", "date": "2024-01-01", "sku": "A", "value": 150, "ts": 2},
            {"workspace_id": "ws1", "date": "2024-01-01", "sku": "B", "value": 200, "ts": 1},
            {"workspace_id": "ws2", "date": "2024-01-01", "sku": "A", "value": 300, "ts": 1},
        ]
        df = spark.createDataFrame(data)

        # Deduplicate by workspace_id, date, sku
        key_cols = ["workspace_id", "date", "sku"]
        from pyspark.sql.window import Window
        w = Window.partitionBy(*key_cols).orderBy(F.desc("ts"))
        deduped = df.withColumn("rn", F.row_number().over(w)).filter(F.col("rn") == 1).drop("rn")

        assert deduped.count() == 3

    @pytest.mark.integration
    def test_deduplicate_preserves_all_columns(self, spark):
        """Verify deduplication preserves all columns."""
        data = [
            {"id": 1, "col_a": "a", "col_b": "b", "col_c": "c", "ts": 1},
            {"id": 1, "col_a": "a2", "col_b": "b2", "col_c": "c2", "ts": 2},
        ]
        df = spark.createDataFrame(data)

        from pyspark.sql.window import Window
        w = Window.partitionBy("id").orderBy(F.desc("ts"))
        deduped = df.withColumn("rn", F.row_number().over(w)).filter(F.col("rn") == 1).drop("rn")

        # Should have all original columns except rn
        assert set(deduped.columns) == {"id", "col_a", "col_b", "col_c", "ts"}

        row = deduped.first()
        assert row["col_a"] == "a2"
        assert row["col_b"] == "b2"

    @pytest.mark.integration
    def test_deduplicate_handles_nulls_in_key(self, spark):
        """Test behavior when key columns contain NULLs."""
        data = [
            {"id": None, "value": 100, "ts": 1},
            {"id": None, "value": 200, "ts": 2},
            {"id": 1, "value": 300, "ts": 1},
        ]
        df = spark.createDataFrame(data)

        from pyspark.sql.window import Window
        w = Window.partitionBy("id").orderBy(F.desc("ts"))
        deduped = df.withColumn("rn", F.row_number().over(w)).filter(F.col("rn") == 1).drop("rn")

        # NULLs are treated as a single group
        assert deduped.count() == 2

        null_row = deduped.filter(F.col("id").isNull()).first()
        assert null_row["value"] == 200


class TestIncrementalLoad:
    """Tests for incremental load logic."""

    @pytest.mark.integration
    def test_high_water_mark_filtering(self, spark):
        """Test filtering by high water mark timestamp."""
        data = [
            {"id": 1, "ts": datetime(2024, 1, 1, 10)},
            {"id": 2, "ts": datetime(2024, 1, 2, 10)},
            {"id": 3, "ts": datetime(2024, 1, 3, 10)},
            {"id": 4, "ts": datetime(2024, 1, 4, 10)},
        ]
        df = spark.createDataFrame(data)

        # Filter for records after high water mark
        high_water_mark = datetime(2024, 1, 2, 0)
        incremental = df.filter(F.col("ts") > high_water_mark)

        assert incremental.count() == 2
        ids = [row["id"] for row in incremental.collect()]
        assert sorted(ids) == [3, 4]

    @pytest.mark.integration
    def test_first_run_full_load(self, spark):
        """Test first run loads all data when no high water mark."""
        data = [
            {"id": 1, "ts": datetime(2024, 1, 1)},
            {"id": 2, "ts": datetime(2024, 1, 2)},
            {"id": 3, "ts": datetime(2024, 1, 3)},
        ]
        df = spark.createDataFrame(data)

        # Simulate first run - no high water mark means load all
        high_water_mark = None

        if high_water_mark is None:
            incremental = df  # Load all
        else:
            incremental = df.filter(F.col("ts") > high_water_mark)

        assert incremental.count() == 3

    @pytest.mark.integration
    def test_backfill_limit(self, spark):
        """Test backfill is limited to configured number of days."""
        now = datetime.now()
        data = [
            {"id": i, "ts": now - timedelta(days=i)}
            for i in range(100)  # 100 days of data
        ]
        df = spark.createDataFrame(data)

        # Limit backfill to 30 days
        backfill_days = 30
        cutoff = now - timedelta(days=backfill_days)
        limited = df.filter(F.col("ts") >= cutoff)

        assert limited.count() == 30


class TestMergePreparation:
    """Tests for MERGE operation preparation."""

    @pytest.fixture
    def source_data(self, spark):
        """Sample source data for merge."""
        return spark.createDataFrame([
            {"id": 1, "value": 100, "ts": datetime(2024, 1, 1, 10)},
            {"id": 2, "value": 200, "ts": datetime(2024, 1, 1, 11)},
            {"id": 3, "value": 300, "ts": datetime(2024, 1, 1, 12)},
        ])

    @pytest.fixture
    def target_data(self, spark):
        """Sample target data for merge."""
        return spark.createDataFrame([
            {"id": 1, "value": 50, "ts": datetime(2024, 1, 1, 8)},
            {"id": 4, "value": 400, "ts": datetime(2024, 1, 1, 9)},
        ])

    @pytest.mark.integration
    def test_identify_inserts(self, spark, source_data, target_data):
        """Identify records that will be inserted (new keys)."""
        # Left anti join to find new keys
        inserts = source_data.join(target_data, on="id", how="left_anti")

        assert inserts.count() == 2
        ids = [row["id"] for row in inserts.collect()]
        assert sorted(ids) == [2, 3]

    @pytest.mark.integration
    def test_identify_updates(self, spark, source_data, target_data):
        """Identify records that will be updated (existing keys)."""
        # Inner join to find matching keys
        updates = source_data.alias("s").join(
            target_data.alias("t"),
            on="id",
            how="inner"
        ).select("s.*")

        assert updates.count() == 1
        assert updates.first()["id"] == 1

    @pytest.mark.integration
    def test_merge_would_not_delete(self, spark, source_data, target_data):
        """Verify MERGE (without delete) preserves target-only records."""
        # Records in target but not in source
        target_only = target_data.join(source_data, on="id", how="left_anti")

        assert target_only.count() == 1
        assert target_only.first()["id"] == 4


class TestSchemaValidation:
    """Tests for schema validation."""

    @pytest.mark.integration
    def test_validate_required_columns(self, spark):
        """Validate required columns are present."""
        required = ["id", "workspace_id", "timestamp"]

        # Good DataFrame
        good_df = spark.createDataFrame([
            {"id": 1, "workspace_id": "ws1", "timestamp": datetime.now(), "extra": "ok"}
        ])

        missing = [col for col in required if col not in good_df.columns]
        assert len(missing) == 0

        # Bad DataFrame
        bad_df = spark.createDataFrame([
            {"id": 1, "extra": "missing workspace_id and timestamp"}
        ])

        missing = [col for col in required if col not in bad_df.columns]
        assert len(missing) == 2
        assert "workspace_id" in missing
        assert "timestamp" in missing

    @pytest.mark.integration
    def test_validate_column_types(self, spark):
        """Validate column data types match expected."""
        expected_schema = StructType([
            StructField("id", IntegerType(), False),
            StructField("value", DoubleType(), True),
            StructField("name", StringType(), True),
        ])

        df = spark.createDataFrame([
            {"id": 1, "value": 100.0, "name": "test"}
        ])

        # Compare field types
        for expected_field in expected_schema.fields:
            if expected_field.name in df.columns:
                actual_field = df.schema[expected_field.name]
                assert actual_field.dataType == expected_field.dataType, \
                    f"Type mismatch for {expected_field.name}"


class TestForeignKeyValidation:
    """Tests for foreign key integrity validation."""

    @pytest.mark.integration
    def test_valid_foreign_keys(self, spark):
        """Test when all foreign keys are valid."""
        dim_workspace = spark.createDataFrame([
            {"workspace_id": "ws1"},
            {"workspace_id": "ws2"},
            {"workspace_id": "ws3"},
        ])

        fact_usage = spark.createDataFrame([
            {"id": 1, "workspace_id": "ws1"},
            {"id": 2, "workspace_id": "ws2"},
            {"id": 3, "workspace_id": "ws1"},
        ])

        # Check for orphan foreign keys
        orphans = fact_usage.select("workspace_id").distinct().join(
            dim_workspace,
            on="workspace_id",
            how="left_anti"
        )

        assert orphans.count() == 0

    @pytest.mark.integration
    def test_orphan_foreign_keys(self, spark):
        """Test detection of orphan foreign keys."""
        dim_workspace = spark.createDataFrame([
            {"workspace_id": "ws1"},
            {"workspace_id": "ws2"},
        ])

        fact_usage = spark.createDataFrame([
            {"id": 1, "workspace_id": "ws1"},
            {"id": 2, "workspace_id": "ws3"},  # Orphan!
            {"id": 3, "workspace_id": "ws4"},  # Orphan!
        ])

        orphans = fact_usage.select("workspace_id").distinct().join(
            dim_workspace,
            on="workspace_id",
            how="left_anti"
        )

        assert orphans.count() == 2
        orphan_ids = [row["workspace_id"] for row in orphans.collect()]
        assert sorted(orphan_ids) == ["ws3", "ws4"]

    @pytest.mark.integration
    def test_null_foreign_keys_allowed(self, spark):
        """Test NULL foreign keys are optionally allowed."""
        dim_workspace = spark.createDataFrame([
            {"workspace_id": "ws1"},
        ])

        fact_usage = spark.createDataFrame([
            {"id": 1, "workspace_id": "ws1"},
            {"id": 2, "workspace_id": None},  # NULL FK
        ])

        # Filter out NULLs before checking
        non_null_fks = fact_usage.filter(F.col("workspace_id").isNotNull())
        orphans = non_null_fks.select("workspace_id").distinct().join(
            dim_workspace,
            on="workspace_id",
            how="left_anti"
        )

        assert orphans.count() == 0


class TestDataQualityChecks:
    """Tests for data quality validation during merge."""

    @pytest.mark.integration
    def test_detect_negative_values(self, spark):
        """Detect negative values in quantity columns."""
        df = spark.createDataFrame([
            {"id": 1, "quantity": 100.0},
            {"id": 2, "quantity": -50.0},  # Invalid
            {"id": 3, "quantity": 0.0},
        ])

        invalid = df.filter(F.col("quantity") < 0)
        assert invalid.count() == 1

    @pytest.mark.integration
    def test_detect_future_dates(self, spark):
        """Detect dates in the future."""
        now = datetime.now()
        df = spark.createDataFrame([
            {"id": 1, "event_date": now - timedelta(days=1)},
            {"id": 2, "event_date": now + timedelta(days=10)},  # Future
            {"id": 3, "event_date": now},
        ])

        future_records = df.filter(F.col("event_date") > F.current_timestamp())
        assert future_records.count() == 1

    @pytest.mark.integration
    def test_detect_duplicate_primary_keys(self, spark):
        """Detect duplicate primary keys before merge."""
        df = spark.createDataFrame([
            {"id": 1, "value": 100},
            {"id": 1, "value": 200},  # Duplicate
            {"id": 2, "value": 300},
        ])

        duplicates = df.groupBy("id").count().filter(F.col("count") > 1)
        assert duplicates.count() == 1
        assert duplicates.first()["id"] == 1
