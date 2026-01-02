"""
Spark Session Fixtures
======================

Provides SparkSession fixtures for local testing of PySpark code.

Usage:
    def test_with_spark(spark):
        df = spark.createDataFrame([{"id": 1}])
        assert df.count() == 1
"""

import pytest
from typing import Optional
import os
import logging

# Suppress verbose Spark logging
logging.getLogger("py4j").setLevel(logging.ERROR)
logging.getLogger("pyspark").setLevel(logging.ERROR)


@pytest.fixture(scope="session")
def spark():
    """
    Create a session-scoped local SparkSession for testing.

    Configuration is optimized for testing:
    - Uses local[2] for basic parallelism simulation
    - Reduced shuffle partitions (2 vs default 200)
    - Arrow optimization enabled for pandas interop
    - Limited driver memory (2g)
    - Temporary warehouse directory

    The session is shared across all tests in the test session
    to minimize JVM startup overhead.

    Yields:
        SparkSession: Configured local SparkSession

    Skips:
        If PySpark is not installed
    """
    try:
        from pyspark.sql import SparkSession
    except ImportError:
        pytest.skip("PySpark not installed")
        return

    # Set environment variables to reduce noise
    os.environ.setdefault("SPARK_HOME", "/tmp/spark")

    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("HealthMonitorTests")
        # Performance settings for testing
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.default.parallelism", "2")
        # Arrow for efficient pandas conversion
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .config("spark.sql.execution.arrow.pyspark.fallback.enabled", "true")
        # Memory settings
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "2g")
        # Warehouse directory
        .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse-test")
        # Disable UI
        .config("spark.ui.enabled", "false")
        # Reduce logging
        .config("spark.driver.extraJavaOptions", "-Xss4m -Dlog4j.logger.org=ERROR")
        # Delta Lake settings (if available)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .getOrCreate()
    )

    # Set log level
    spark.sparkContext.setLogLevel("ERROR")

    yield spark

    # Cleanup
    spark.stop()


# Alias for compatibility
spark_session = spark


@pytest.fixture(scope="function")
def spark_clean(spark):
    """
    Provide a clean Spark context for each test.

    Clears any cached DataFrames and temp views before and after each test.
    Use this when tests might interfere with each other.

    Yields:
        SparkSession: Clean SparkSession
    """
    # Clear temp views before test
    for table in spark.catalog.listTables():
        if table.isTemporary:
            spark.catalog.dropTempView(table.name)

    # Clear cache
    spark.catalog.clearCache()

    yield spark

    # Clear again after test
    for table in spark.catalog.listTables():
        if table.isTemporary:
            spark.catalog.dropTempView(table.name)
    spark.catalog.clearCache()


@pytest.fixture
def temp_view_context(spark):
    """
    Context manager for temporary view creation and cleanup.

    Usage:
        def test_with_views(spark, temp_view_context):
            with temp_view_context() as ctx:
                df = spark.createDataFrame([{"id": 1}])
                ctx.register("my_view", df)
                result = spark.sql("SELECT * FROM my_view")
    """
    class TempViewContext:
        def __init__(self, spark_session):
            self._spark = spark_session
            self._views = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            for view in self._views:
                try:
                    self._spark.catalog.dropTempView(view)
                except Exception:
                    pass

        def register(self, name: str, df) -> None:
            """Register DataFrame as temp view."""
            df.createOrReplaceTempView(name)
            self._views.append(name)

    def factory():
        return TempViewContext(spark)

    return factory


class SparkTestHelper:
    """
    Helper class for Spark testing utilities.

    Provides convenience methods for common testing operations.
    """

    def __init__(self, spark):
        self.spark = spark

    def create_df_from_dict(self, data: list, schema=None):
        """
        Create DataFrame from list of dictionaries.

        Args:
            data: List of dictionaries
            schema: Optional StructType schema

        Returns:
            DataFrame
        """
        if schema:
            return self.spark.createDataFrame(data, schema)
        return self.spark.createDataFrame(data)

    def assert_df_empty(self, df, msg: str = None):
        """Assert DataFrame is empty."""
        count = df.count()
        if count != 0:
            raise AssertionError(msg or f"Expected empty DataFrame, got {count} rows")

    def assert_df_not_empty(self, df, msg: str = None):
        """Assert DataFrame is not empty."""
        count = df.count()
        if count == 0:
            raise AssertionError(msg or "Expected non-empty DataFrame")

    def get_first_row_as_dict(self, df) -> Optional[dict]:
        """Get first row of DataFrame as dictionary."""
        row = df.first()
        return row.asDict() if row else None

    def collect_column(self, df, column: str) -> list:
        """Collect all values from a column."""
        return [row[column] for row in df.select(column).collect()]


@pytest.fixture
def spark_helper(spark):
    """Provide SparkTestHelper instance."""
    return SparkTestHelper(spark)
