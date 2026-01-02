"""
Assertion Helpers
=================

Custom assertion functions for testing PySpark DataFrames and data quality.

These helpers provide clear error messages and common validation patterns.
"""

from typing import List, Optional, Any, Union
from pyspark.sql import DataFrame
from pyspark.sql.types import StructType
import pyspark.sql.functions as F


def assert_dataframe_equal(
    df1: DataFrame,
    df2: DataFrame,
    check_order: bool = False,
    check_schema: bool = True,
    check_nullable: bool = False,
    msg: str = None,
) -> None:
    """
    Assert two PySpark DataFrames are equal.

    Args:
        df1: First DataFrame
        df2: Second DataFrame
        check_order: Whether row order matters
        check_schema: Whether to verify schemas match
        check_nullable: Whether to check nullable in schema
        msg: Custom message on failure

    Raises:
        AssertionError: If DataFrames are not equal
    """
    try:
        from chispa import assert_df_equality
        assert_df_equality(
            df1,
            df2,
            ignore_row_order=not check_order,
            ignore_nullable=not check_nullable,
        )
    except ImportError:
        # Fallback if chispa not available
        if check_schema:
            assert_schema_equal(df1, df2)

        # Compare counts
        count1 = df1.count()
        count2 = df2.count()
        if count1 != count2:
            raise AssertionError(
                msg or f"Row counts differ: {count1} vs {count2}"
            )

        # Compare content
        if check_order:
            rows1 = [row.asDict() for row in df1.collect()]
            rows2 = [row.asDict() for row in df2.collect()]
            if rows1 != rows2:
                raise AssertionError(msg or "DataFrame contents differ")
        else:
            # Use subtract to find differences
            diff1 = df1.subtract(df2).count()
            diff2 = df2.subtract(df1).count()
            if diff1 > 0 or diff2 > 0:
                raise AssertionError(
                    msg or f"DataFrames have different content: "
                    f"{diff1} in df1 only, {diff2} in df2 only"
                )


def assert_schema_equal(
    df1: DataFrame,
    df2: DataFrame,
    check_nullable: bool = False,
    msg: str = None,
) -> None:
    """
    Assert two DataFrames have the same schema.

    Args:
        df1: First DataFrame
        df2: Second DataFrame
        check_nullable: Whether to compare nullable attributes
        msg: Custom message on failure

    Raises:
        AssertionError: If schemas don't match
    """
    schema1 = df1.schema
    schema2 = df2.schema

    if not check_nullable:
        # Compare just field names and types
        fields1 = [(f.name, f.dataType) for f in schema1.fields]
        fields2 = [(f.name, f.dataType) for f in schema2.fields]
        if fields1 != fields2:
            raise AssertionError(
                msg or f"Schemas differ:\n{schema1}\nvs\n{schema2}"
            )
    else:
        if schema1 != schema2:
            raise AssertionError(
                msg or f"Schemas differ:\n{schema1}\nvs\n{schema2}"
            )


def assert_column_exists(
    df: DataFrame,
    column_name: str,
    msg: str = None,
) -> None:
    """
    Assert a column exists in the DataFrame.

    Args:
        df: DataFrame to check
        column_name: Name of column
        msg: Custom message on failure

    Raises:
        AssertionError: If column not found
    """
    if column_name not in df.columns:
        raise AssertionError(
            msg or f"Column '{column_name}' not found. "
            f"Available columns: {df.columns}"
        )


def assert_columns_exist(
    df: DataFrame,
    column_names: List[str],
    msg: str = None,
) -> None:
    """
    Assert multiple columns exist in the DataFrame.

    Args:
        df: DataFrame to check
        column_names: List of column names
        msg: Custom message on failure

    Raises:
        AssertionError: If any column not found
    """
    missing = [col for col in column_names if col not in df.columns]
    if missing:
        raise AssertionError(
            msg or f"Columns not found: {missing}. "
            f"Available columns: {df.columns}"
        )


def assert_no_nulls(
    df: DataFrame,
    column_name: str,
    msg: str = None,
) -> None:
    """
    Assert no null values in a column.

    Args:
        df: DataFrame to check
        column_name: Name of column
        msg: Custom message on failure

    Raises:
        AssertionError: If null values found
    """
    assert_column_exists(df, column_name)

    null_count = df.filter(F.col(column_name).isNull()).count()
    if null_count > 0:
        raise AssertionError(
            msg or f"Found {null_count} null values in column '{column_name}'"
        )


def assert_no_nulls_in_columns(
    df: DataFrame,
    column_names: List[str],
    msg: str = None,
) -> None:
    """
    Assert no null values in multiple columns.

    Args:
        df: DataFrame to check
        column_names: List of column names
        msg: Custom message on failure

    Raises:
        AssertionError: If null values found in any column
    """
    for col in column_names:
        assert_no_nulls(df, col, msg)


def assert_row_count(
    df: DataFrame,
    expected: int = None,
    min_count: int = None,
    max_count: int = None,
    msg: str = None,
) -> None:
    """
    Assert DataFrame has expected row count or is within range.

    Args:
        df: DataFrame to check
        expected: Exact expected count (mutually exclusive with min/max)
        min_count: Minimum row count
        max_count: Maximum row count
        msg: Custom message on failure

    Raises:
        AssertionError: If count doesn't match expectations
    """
    actual_count = df.count()

    if expected is not None:
        if actual_count != expected:
            raise AssertionError(
                msg or f"Expected {expected} rows, got {actual_count}"
            )
    else:
        if min_count is not None and actual_count < min_count:
            raise AssertionError(
                msg or f"Expected at least {min_count} rows, got {actual_count}"
            )
        if max_count is not None and actual_count > max_count:
            raise AssertionError(
                msg or f"Expected at most {max_count} rows, got {actual_count}"
            )


def assert_column_values_in_range(
    df: DataFrame,
    column_name: str,
    min_value: Any = None,
    max_value: Any = None,
    msg: str = None,
) -> None:
    """
    Assert all column values are within specified range.

    Args:
        df: DataFrame to check
        column_name: Name of column
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        msg: Custom message on failure

    Raises:
        AssertionError: If any value is out of range
    """
    assert_column_exists(df, column_name)

    violations = df.filter(
        (F.col(column_name) < min_value if min_value is not None else F.lit(False)) |
        (F.col(column_name) > max_value if max_value is not None else F.lit(False))
    ).count()

    if violations > 0:
        # Get sample of violations
        sample = df.filter(
            (F.col(column_name) < min_value if min_value is not None else F.lit(False)) |
            (F.col(column_name) > max_value if max_value is not None else F.lit(False))
        ).limit(5).collect()

        sample_values = [row[column_name] for row in sample]
        raise AssertionError(
            msg or f"Found {violations} values out of range [{min_value}, {max_value}] "
            f"in column '{column_name}'. Sample: {sample_values}"
        )


def assert_column_values_in_set(
    df: DataFrame,
    column_name: str,
    allowed_values: set,
    msg: str = None,
) -> None:
    """
    Assert all column values are in allowed set.

    Args:
        df: DataFrame to check
        column_name: Name of column
        allowed_values: Set of allowed values
        msg: Custom message on failure

    Raises:
        AssertionError: If any value is not in allowed set
    """
    assert_column_exists(df, column_name)

    actual_values = set(
        row[column_name] for row in df.select(column_name).distinct().collect()
    )

    invalid_values = actual_values - allowed_values
    if invalid_values:
        raise AssertionError(
            msg or f"Found unexpected values in column '{column_name}': {invalid_values}. "
            f"Allowed: {allowed_values}"
        )


def assert_unique_values(
    df: DataFrame,
    column_names: Union[str, List[str]],
    msg: str = None,
) -> None:
    """
    Assert values are unique across specified column(s).

    Args:
        df: DataFrame to check
        column_names: Column name or list of column names for uniqueness check
        msg: Custom message on failure

    Raises:
        AssertionError: If duplicate values found
    """
    if isinstance(column_names, str):
        column_names = [column_names]

    for col in column_names:
        assert_column_exists(df, col)

    total_count = df.count()
    distinct_count = df.select(*column_names).distinct().count()

    if total_count != distinct_count:
        duplicates = total_count - distinct_count
        raise AssertionError(
            msg or f"Found {duplicates} duplicate values for columns {column_names}"
        )


def assert_foreign_key_valid(
    fact_df: DataFrame,
    dim_df: DataFrame,
    fact_key: str,
    dim_key: str,
    allow_null: bool = True,
    msg: str = None,
) -> None:
    """
    Assert all foreign key values exist in dimension table.

    Args:
        fact_df: Fact table DataFrame
        dim_df: Dimension table DataFrame
        fact_key: Foreign key column in fact table
        dim_key: Primary key column in dimension table
        allow_null: Whether NULL values are allowed in foreign key
        msg: Custom message on failure

    Raises:
        AssertionError: If orphan foreign key values found
    """
    assert_column_exists(fact_df, fact_key)
    assert_column_exists(dim_df, dim_key)

    # Get distinct FK values from fact table
    fact_keys = fact_df.select(fact_key).distinct()

    if not allow_null:
        assert_no_nulls(fact_df, fact_key, "Foreign key column contains NULL values")
        fact_keys = fact_keys.filter(F.col(fact_key).isNotNull())
    else:
        fact_keys = fact_keys.filter(F.col(fact_key).isNotNull())

    # Get distinct PK values from dimension
    dim_keys = dim_df.select(dim_key).distinct()

    # Find orphans
    orphans = fact_keys.subtract(
        dim_keys.withColumnRenamed(dim_key, fact_key)
    )
    orphan_count = orphans.count()

    if orphan_count > 0:
        sample_orphans = [row[fact_key] for row in orphans.limit(10).collect()]
        raise AssertionError(
            msg or f"Found {orphan_count} orphan foreign key values in '{fact_key}'. "
            f"Sample: {sample_orphans}"
        )


def assert_column_type(
    df: DataFrame,
    column_name: str,
    expected_type: type,
    msg: str = None,
) -> None:
    """
    Assert column has expected data type.

    Args:
        df: DataFrame to check
        column_name: Name of column
        expected_type: Expected PySpark data type class
        msg: Custom message on failure

    Raises:
        AssertionError: If column type doesn't match
    """
    assert_column_exists(df, column_name)

    actual_type = df.schema[column_name].dataType
    if not isinstance(actual_type, expected_type):
        raise AssertionError(
            msg or f"Column '{column_name}' has type {type(actual_type).__name__}, "
            f"expected {expected_type.__name__}"
        )


def assert_no_duplicates_on_keys(
    df: DataFrame,
    key_columns: List[str],
    msg: str = None,
) -> None:
    """
    Assert no duplicate records exist on specified key columns.

    Args:
        df: DataFrame to check
        key_columns: List of columns that form the unique key
        msg: Custom message on failure

    Raises:
        AssertionError: If duplicate keys found
    """
    assert_columns_exist(df, key_columns)

    total = df.count()
    distinct = df.select(*key_columns).distinct().count()

    if total != distinct:
        # Find actual duplicates
        from pyspark.sql.window import Window

        w = Window.partitionBy(*key_columns)
        duplicates = df.withColumn(
            "_count", F.count("*").over(w)
        ).filter(F.col("_count") > 1)

        sample = duplicates.select(*key_columns).distinct().limit(5).collect()
        sample_keys = [row.asDict() for row in sample]

        raise AssertionError(
            msg or f"Found {total - distinct} duplicate keys. "
            f"Sample duplicates: {sample_keys}"
        )
