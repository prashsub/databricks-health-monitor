"""
Alerting Metrics Collection

Collects and logs metrics for alert sync operations.
Metrics are stored in alert_sync_metrics table for monitoring and analytics.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class AlertSyncMetrics:
    """Metrics for a single alert sync operation."""

    sync_run_id: str
    sync_started_at: datetime
    sync_ended_at: Optional[datetime] = None
    total_alerts: int = 0
    success_count: int = 0
    error_count: int = 0
    created_count: int = 0
    updated_count: int = 0
    deleted_count: int = 0
    skipped_count: int = 0
    api_latencies_ms: List[float] = field(default_factory=list)
    dry_run: bool = False
    catalog: str = ""
    gold_schema: str = ""
    errors: List[str] = field(default_factory=list)

    @staticmethod
    def start(catalog: str, gold_schema: str, dry_run: bool = False) -> "AlertSyncMetrics":
        """Start a new metrics collection."""
        return AlertSyncMetrics(
            sync_run_id=str(uuid.uuid4()),
            sync_started_at=datetime.now(),
            catalog=catalog,
            gold_schema=gold_schema,
            dry_run=dry_run,
        )

    def record_api_call(self, latency_seconds: float) -> None:
        """Record an API call latency."""
        self.api_latencies_ms.append(latency_seconds * 1000)

    def record_create(self, latency_seconds: float) -> None:
        """Record a successful CREATE operation."""
        self.created_count += 1
        self.success_count += 1
        self.record_api_call(latency_seconds)

    def record_update(self, latency_seconds: float) -> None:
        """Record a successful UPDATE operation."""
        self.updated_count += 1
        self.success_count += 1
        self.record_api_call(latency_seconds)

    def record_delete(self, latency_seconds: float) -> None:
        """Record a successful DELETE operation."""
        self.deleted_count += 1
        self.success_count += 1
        self.record_api_call(latency_seconds)

    def record_skip(self) -> None:
        """Record a skipped operation."""
        self.skipped_count += 1

    def record_error(self, alert_id: str, error: str) -> None:
        """Record an error."""
        self.error_count += 1
        self.errors.append(f"{alert_id}: {error[:500]}")

    def finish(self) -> None:
        """Mark sync as complete."""
        self.sync_ended_at = datetime.now()

    @property
    def total_duration_seconds(self) -> float:
        """Total sync duration in seconds."""
        if not self.sync_ended_at:
            return (datetime.now() - self.sync_started_at).total_seconds()
        return (self.sync_ended_at - self.sync_started_at).total_seconds()

    @property
    def avg_api_latency_ms(self) -> float:
        """Average API latency in milliseconds."""
        if not self.api_latencies_ms:
            return 0.0
        return sum(self.api_latencies_ms) / len(self.api_latencies_ms)

    @property
    def max_api_latency_ms(self) -> float:
        """Maximum API latency in milliseconds."""
        if not self.api_latencies_ms:
            return 0.0
        return max(self.api_latencies_ms)

    @property
    def min_api_latency_ms(self) -> float:
        """Minimum API latency in milliseconds."""
        if not self.api_latencies_ms:
            return 0.0
        return min(self.api_latencies_ms)

    @property
    def p95_api_latency_ms(self) -> float:
        """95th percentile API latency in milliseconds."""
        if not self.api_latencies_ms:
            return 0.0
        sorted_latencies = sorted(self.api_latencies_ms)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]


def create_metrics_table_ddl(catalog: str, gold_schema: str) -> str:
    """
    Generate DDL for alert_sync_metrics table.

    This table stores metrics for each alert sync operation.
    """
    return f"""
CREATE TABLE IF NOT EXISTS {catalog}.{gold_schema}.alert_sync_metrics (
    sync_run_id STRING NOT NULL
        COMMENT 'Unique identifier for this sync operation (UUID).',
    sync_started_at TIMESTAMP NOT NULL
        COMMENT 'When the sync operation started.',
    sync_ended_at TIMESTAMP NOT NULL
        COMMENT 'When the sync operation completed.',
    
    total_alerts INT NOT NULL
        COMMENT 'Total number of alert configurations processed.',
    success_count INT NOT NULL
        COMMENT 'Number of successful operations (create + update + delete).',
    error_count INT NOT NULL
        COMMENT 'Number of failed operations.',
    created_count INT NOT NULL
        COMMENT 'Number of new alerts created.',
    updated_count INT NOT NULL
        COMMENT 'Number of existing alerts updated.',
    deleted_count INT NOT NULL
        COMMENT 'Number of disabled alerts deleted.',
    skipped_count INT NOT NULL
        COMMENT 'Number of alerts skipped (unchanged).',
    
    avg_api_latency_ms DOUBLE NOT NULL
        COMMENT 'Average API call latency in milliseconds.',
    max_api_latency_ms DOUBLE NOT NULL
        COMMENT 'Maximum API call latency in milliseconds.',
    min_api_latency_ms DOUBLE NOT NULL
        COMMENT 'Minimum API call latency in milliseconds.',
    p95_api_latency_ms DOUBLE NOT NULL
        COMMENT '95th percentile API call latency in milliseconds.',
    
    total_duration_seconds DOUBLE NOT NULL
        COMMENT 'Total sync operation duration in seconds.',
    
    dry_run BOOLEAN NOT NULL
        COMMENT 'Whether this was a dry run (no actual changes).',
    catalog STRING NOT NULL
        COMMENT 'Target catalog for alerts.',
    gold_schema STRING NOT NULL
        COMMENT 'Target schema for alerts.',
    
    error_summary STRING
        COMMENT 'Summary of errors if any occurred.',
    
    record_created_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
        COMMENT 'When this metrics record was created.',
    
    CONSTRAINT pk_alert_sync_metrics PRIMARY KEY (sync_run_id) NOT ENFORCED
)
USING DELTA
CLUSTER BY AUTO
COMMENT 'Alert sync operation metrics for monitoring and observability. Each row represents one sync execution.'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.enableRowTracking' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'layer' = 'gold',
    'domain' = 'alerting',
    'entity_type' = 'metric'
)
"""


def log_sync_metrics_spark(spark, metrics: AlertSyncMetrics) -> None:
    """
    Log sync metrics to alert_sync_metrics table using Spark SQL.

    Args:
        spark: SparkSession
        metrics: AlertSyncMetrics to log
    """
    metrics_table = f"{metrics.catalog}.{metrics.gold_schema}.alert_sync_metrics"

    # Ensure table exists
    spark.sql(create_metrics_table_ddl(metrics.catalog, metrics.gold_schema))

    # Escape error summary
    error_summary = ""
    if metrics.errors:
        error_summary = "; ".join(metrics.errors[:10])  # Limit to first 10
        error_summary = error_summary.replace("'", "''")[:2000]  # Escape and truncate

    # Insert metrics
    spark.sql(f"""
INSERT INTO {metrics_table} (
    sync_run_id,
    sync_started_at,
    sync_ended_at,
    total_alerts,
    success_count,
    error_count,
    created_count,
    updated_count,
    deleted_count,
    skipped_count,
    avg_api_latency_ms,
    max_api_latency_ms,
    min_api_latency_ms,
    p95_api_latency_ms,
    total_duration_seconds,
    dry_run,
    catalog,
    gold_schema,
    error_summary
) VALUES (
    '{metrics.sync_run_id}',
    TIMESTAMP'{metrics.sync_started_at.strftime("%Y-%m-%d %H:%M:%S")}',
    TIMESTAMP'{metrics.sync_ended_at.strftime("%Y-%m-%d %H:%M:%S") if metrics.sync_ended_at else datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
    {metrics.total_alerts},
    {metrics.success_count},
    {metrics.error_count},
    {metrics.created_count},
    {metrics.updated_count},
    {metrics.deleted_count},
    {metrics.skipped_count},
    {metrics.avg_api_latency_ms},
    {metrics.max_api_latency_ms},
    {metrics.min_api_latency_ms},
    {metrics.p95_api_latency_ms},
    {metrics.total_duration_seconds},
    {str(metrics.dry_run).lower()},
    '{metrics.catalog}',
    '{metrics.gold_schema}',
    {f"'{error_summary}'" if error_summary else 'NULL'}
)
""")

    print(f"✓ Metrics logged: {metrics.sync_run_id}")


def print_metrics_summary(metrics: AlertSyncMetrics) -> None:
    """Print metrics summary to console."""
    print("\n" + "=" * 60)
    print("SYNC METRICS SUMMARY")
    print("=" * 60)
    print(f"Run ID:          {metrics.sync_run_id[:8]}...")
    print(f"Duration:        {metrics.total_duration_seconds:.2f}s")
    print(f"Dry Run:         {metrics.dry_run}")
    print("-" * 60)
    print(f"Total Processed: {metrics.total_alerts}")
    print(f"  ✓ Created:     {metrics.created_count}")
    print(f"  ✓ Updated:     {metrics.updated_count}")
    print(f"  ✓ Deleted:     {metrics.deleted_count}")
    print(f"  → Skipped:     {metrics.skipped_count}")
    print(f"  ✗ Errors:      {metrics.error_count}")
    print("-" * 60)
    print(f"API Latency (ms):")
    print(f"  Avg: {metrics.avg_api_latency_ms:.0f}")
    print(f"  Max: {metrics.max_api_latency_ms:.0f}")
    print(f"  P95: {metrics.p95_api_latency_ms:.0f}")
    if metrics.errors:
        print("-" * 60)
        print(f"Errors ({len(metrics.errors)}):")
        for err in metrics.errors[:5]:
            print(f"  - {err[:80]}")
        if len(metrics.errors) > 5:
            print(f"  ... and {len(metrics.errors) - 5} more")
    print("=" * 60 + "\n")

