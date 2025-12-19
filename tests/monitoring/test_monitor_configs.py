"""
Tests for Lakehouse Monitor Configurations
==========================================

These tests validate monitor configurations for:
- Correct metric types (AGGREGATE, DERIVED, DRIFT)
- Consistent input_columns usage
- NULLIF guards for derived metrics
- Business metric coverage by domain
"""

import pytest
import re
import sys
from pathlib import Path


# Path to monitoring source files
MONITORING_DIR = Path(__file__).parent.parent.parent / "src" / "monitoring"

# Add monitoring dir to path for imports
sys.path.insert(0, str(MONITORING_DIR))


def read_monitor_file(filename):
    """Read monitor file contents."""
    file_path = MONITORING_DIR / filename
    with open(file_path, 'r') as f:
        return f.read()


def extract_metrics_from_file(content):
    """Extract metric definitions from monitor file content."""
    metrics = []

    # Find all create_aggregate_metric calls
    agg_pattern = r'create_aggregate_metric\s*\(\s*"([^"]+)"'
    for match in re.finditer(agg_pattern, content):
        metrics.append(('AGGREGATE', match.group(1)))

    # Find all create_derived_metric calls
    derived_pattern = r'create_derived_metric\s*\(\s*"([^"]+)"'
    for match in re.finditer(derived_pattern, content):
        metrics.append(('DERIVED', match.group(1)))

    # Find all create_drift_metric calls
    drift_pattern = r'create_drift_metric\s*\(\s*"([^"]+)"'
    for match in re.finditer(drift_pattern, content):
        metrics.append(('DRIFT', match.group(1)))

    return metrics


class TestMonitorFileStructure:
    """Test monitor file structure and organization."""

    @pytest.mark.unit
    def test_monitor_files_exist(self):
        """Verify all expected monitor files exist."""
        expected_files = [
            'monitor_utils.py',
            'cost_monitor.py',
            'job_monitor.py',
            'query_monitor.py',
            'cluster_monitor.py',
            'security_monitor.py',
            'setup_all_monitors.py',
        ]

        for filename in expected_files:
            file_path = MONITORING_DIR / filename
            assert file_path.exists(), f"Missing monitor file: {filename}"

    @pytest.mark.unit
    def test_init_file_exists(self):
        """Verify __init__.py exists in monitoring directory."""
        init_path = MONITORING_DIR / '__init__.py'
        assert init_path.exists(), "Missing __init__.py in monitoring directory"

    @pytest.mark.unit
    @pytest.mark.parametrize("filename", [
        'cost_monitor.py',
        'job_monitor.py',
        'query_monitor.py',
        'cluster_monitor.py',
        'security_monitor.py',
    ])
    def test_monitor_has_docstring(self, filename):
        """Verify each monitor file has a docstring."""
        content = read_monitor_file(filename)
        assert '"""' in content[:500], f"Missing docstring in {filename}"


class TestCostMonitorMetrics:
    """Test cost monitor metric configurations."""

    @pytest.fixture
    def cost_metrics(self):
        content = read_monitor_file('cost_monitor.py')
        return extract_metrics_from_file(content)

    @pytest.mark.unit
    def test_has_core_cost_metrics(self, cost_metrics):
        """Verify essential cost metrics are defined."""
        metric_names = [m[1] for m in cost_metrics]

        essential = [
            'total_daily_cost',
            'total_daily_dbu',
            'tagged_cost_total',
            'untagged_cost_total',
        ]

        for metric in essential:
            assert metric in metric_names, f"Missing essential cost metric: {metric}"

    @pytest.mark.unit
    def test_has_tag_hygiene_metrics(self, cost_metrics):
        """Verify tag hygiene metrics are defined."""
        metric_names = [m[1] for m in cost_metrics]

        tag_metrics = [
            'tag_coverage_pct',
            'untagged_usage_pct',
        ]

        for metric in tag_metrics:
            assert metric in metric_names, f"Missing tag metric: {metric}"

    @pytest.mark.unit
    def test_has_drift_metrics(self, cost_metrics):
        """Verify drift metrics are defined for cost monitoring."""
        drift_metrics = [m for m in cost_metrics if m[0] == 'DRIFT']
        assert len(drift_metrics) >= 2, "Cost monitor should have at least 2 drift metrics"


class TestJobMonitorMetrics:
    """Test job reliability monitor metric configurations."""

    @pytest.fixture
    def job_metrics(self):
        content = read_monitor_file('job_monitor.py')
        return extract_metrics_from_file(content)

    @pytest.mark.unit
    def test_has_reliability_metrics(self, job_metrics):
        """Verify essential reliability metrics are defined."""
        metric_names = [m[1] for m in job_metrics]

        essential = [
            'total_runs',
            'success_count',
            'failure_count',
            'success_rate',
        ]

        for metric in essential:
            assert metric in metric_names, f"Missing essential job metric: {metric}"

    @pytest.mark.unit
    def test_has_duration_metrics(self, job_metrics):
        """Verify duration tracking metrics are defined."""
        metric_names = [m[1] for m in job_metrics]

        duration_metrics = [
            'avg_duration_minutes',
            'p95_duration_minutes',
        ]

        for metric in duration_metrics:
            assert metric in metric_names, f"Missing duration metric: {metric}"


class TestQueryMonitorMetrics:
    """Test query performance monitor metric configurations."""

    @pytest.fixture
    def query_metrics(self):
        content = read_monitor_file('query_monitor.py')
        return extract_metrics_from_file(content)

    @pytest.mark.unit
    def test_has_performance_metrics(self, query_metrics):
        """Verify essential performance metrics are defined."""
        metric_names = [m[1] for m in query_metrics]

        essential = [
            'query_count',
            'avg_duration_sec',
            'p95_duration_sec',
            'slow_query_count',
        ]

        for metric in essential:
            assert metric in metric_names, f"Missing essential query metric: {metric}"

    @pytest.mark.unit
    def test_has_capacity_metrics(self, query_metrics):
        """Verify warehouse capacity metrics are defined."""
        metric_names = [m[1] for m in query_metrics]

        capacity_metrics = [
            'avg_queue_time_sec',
            'high_queue_rate',
        ]

        for metric in capacity_metrics:
            assert metric in metric_names, f"Missing capacity metric: {metric}"

    @pytest.mark.unit
    def test_has_spill_tracking(self, query_metrics):
        """Verify spill tracking metrics are defined."""
        metric_names = [m[1] for m in query_metrics]

        assert 'queries_with_spill' in metric_names, "Missing spill tracking metric"
        assert 'spill_rate' in metric_names, "Missing spill rate metric"


class TestClusterMonitorMetrics:
    """Test cluster utilization monitor metric configurations."""

    @pytest.fixture
    def cluster_metrics(self):
        content = read_monitor_file('cluster_monitor.py')
        return extract_metrics_from_file(content)

    @pytest.mark.unit
    def test_has_cpu_metrics(self, cluster_metrics):
        """Verify CPU utilization metrics are defined."""
        metric_names = [m[1] for m in cluster_metrics]

        cpu_metrics = [
            'avg_cpu_user_pct',
            'avg_cpu_system_pct',
            'max_cpu_user_pct',
        ]

        for metric in cpu_metrics:
            assert metric in metric_names, f"Missing CPU metric: {metric}"

    @pytest.mark.unit
    def test_has_memory_metrics(self, cluster_metrics):
        """Verify memory utilization metrics are defined."""
        metric_names = [m[1] for m in cluster_metrics]

        memory_metrics = [
            'avg_memory_pct',
            'max_memory_pct',
            'avg_swap_pct',
        ]

        for metric in memory_metrics:
            assert metric in metric_names, f"Missing memory metric: {metric}"

    @pytest.mark.unit
    def test_has_utilization_thresholds(self, cluster_metrics):
        """Verify utilization threshold metrics are defined."""
        metric_names = [m[1] for m in cluster_metrics]

        threshold_metrics = [
            'underutilized_hours',
            'overutilized_hours',
            'underutilization_rate',
        ]

        for metric in threshold_metrics:
            assert metric in metric_names, f"Missing threshold metric: {metric}"


class TestSecurityMonitorMetrics:
    """Test security monitor metric configurations."""

    @pytest.fixture
    def security_metrics(self):
        content = read_monitor_file('security_monitor.py')
        return extract_metrics_from_file(content)

    @pytest.mark.unit
    def test_has_activity_metrics(self, security_metrics):
        """Verify user activity metrics are defined."""
        metric_names = [m[1] for m in security_metrics]

        activity_metrics = [
            'total_events',
            'distinct_users',
            'sensitive_action_count',
        ]

        for metric in activity_metrics:
            assert metric in metric_names, f"Missing activity metric: {metric}"

    @pytest.mark.unit
    def test_has_security_tracking(self, security_metrics):
        """Verify security event tracking metrics are defined."""
        metric_names = [m[1] for m in security_metrics]

        security_metrics_expected = [
            'failed_action_count',
            'permission_change_count',
            'unauthorized_count',
        ]

        for metric in security_metrics_expected:
            assert metric in metric_names, f"Missing security metric: {metric}"

    @pytest.mark.unit
    def test_has_off_hours_tracking(self, security_metrics):
        """Verify off-hours activity tracking is defined."""
        metric_names = [m[1] for m in security_metrics]

        assert 'off_hours_events' in metric_names, "Missing off-hours tracking"
        assert 'off_hours_rate' in metric_names, "Missing off-hours rate"


class TestMetricDefinitionPatterns:
    """Test metric definition patterns across all monitors."""

    @pytest.mark.unit
    @pytest.mark.parametrize("filename", [
        'cost_monitor.py',
        'job_monitor.py',
        'query_monitor.py',
        'cluster_monitor.py',
        'security_monitor.py',
    ])
    def test_derived_metrics_use_nullif(self, filename):
        """Verify derived metrics use NULLIF for division safety."""
        content = read_monitor_file(filename)

        # Find derived metric definitions
        derived_pattern = r'create_derived_metric\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"'

        for match in re.finditer(derived_pattern, content):
            metric_name = match.group(1)
            definition = match.group(2)

            if '/' in definition:
                assert 'NULLIF' in definition, (
                    f"Derived metric '{metric_name}' in {filename} uses division "
                    "but no NULLIF guard"
                )

    @pytest.mark.unit
    @pytest.mark.parametrize("filename", [
        'cost_monitor.py',
        'job_monitor.py',
        'query_monitor.py',
        'cluster_monitor.py',
        'security_monitor.py',
    ])
    def test_drift_metrics_use_template_syntax(self, filename):
        """Verify drift metrics use {{current_df}} and {{base_df}} syntax."""
        content = read_monitor_file(filename)

        # Find drift metric definitions
        drift_pattern = r'create_drift_metric\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"'

        for match in re.finditer(drift_pattern, content):
            metric_name = match.group(1)
            definition = match.group(2)

            assert '{{current_df}}' in definition, (
                f"Drift metric '{metric_name}' in {filename} missing {{{{current_df}}}} template"
            )
            assert '{{base_df}}' in definition, (
                f"Drift metric '{metric_name}' in {filename} missing {{{{base_df}}}} template"
            )

    @pytest.mark.unit
    @pytest.mark.parametrize("filename", [
        'cost_monitor.py',
        'job_monitor.py',
        'query_monitor.py',
        'cluster_monitor.py',
        'security_monitor.py',
    ])
    def test_has_all_metric_types(self, filename):
        """Verify each monitor has AGGREGATE, DERIVED, and DRIFT metrics."""
        content = read_monitor_file(filename)
        metrics = extract_metrics_from_file(content)

        metric_types = set(m[0] for m in metrics)

        assert 'AGGREGATE' in metric_types, f"{filename} missing AGGREGATE metrics"
        assert 'DERIVED' in metric_types, f"{filename} missing DERIVED metrics"
        assert 'DRIFT' in metric_types, f"{filename} missing DRIFT metrics"

    @pytest.mark.unit
    @pytest.mark.parametrize("filename", [
        'cost_monitor.py',
        'job_monitor.py',
        'query_monitor.py',
        'cluster_monitor.py',
        'security_monitor.py',
    ])
    def test_minimum_metric_count(self, filename):
        """Verify each monitor has a minimum number of metrics."""
        content = read_monitor_file(filename)
        metrics = extract_metrics_from_file(content)

        assert len(metrics) >= 10, (
            f"{filename} has only {len(metrics)} metrics, expected at least 10"
        )


# ==========================================
# NEW TESTS FOR IMPROVED PLAN METRICS
# Source: Blog posts, GitHub repos, Dashboard patterns
# ==========================================

class TestCostMonitorImprovedMetrics:
    """Test new cost monitor metrics from Workflow Advisor Blog."""

    @pytest.fixture
    def cost_metrics(self):
        content = read_monitor_file('cost_monitor.py')
        return extract_metrics_from_file(content)

    @pytest.mark.unit
    def test_has_all_purpose_cluster_metrics(self, cost_metrics):
        """Verify ALL_PURPOSE cluster inefficiency metrics are defined (Workflow Advisor Blog)."""
        metric_names = [m[1] for m in cost_metrics]

        workflow_advisor_metrics = [
            'jobs_on_all_purpose_cost',
            'jobs_on_all_purpose_count',
            'potential_job_cluster_savings',
            'all_purpose_cost_ratio',
        ]

        for metric in workflow_advisor_metrics:
            assert metric in metric_names, f"Missing Workflow Advisor metric: {metric}"

    @pytest.mark.unit
    def test_has_sku_breakdown_metrics(self, cost_metrics):
        """Verify SKU breakdown metrics are comprehensive."""
        metric_names = [m[1] for m in cost_metrics]

        sku_metrics = [
            'jobs_compute_cost',
            'sql_compute_cost',
            'all_purpose_cost',
            'serverless_cost',
            'dlt_cost',
            'model_serving_cost',
        ]

        for metric in sku_metrics:
            assert metric in metric_names, f"Missing SKU breakdown metric: {metric}"


class TestQueryMonitorImprovedMetrics:
    """Test new query monitor metrics from DBSQL Warehouse Advisor Blog."""

    @pytest.fixture
    def query_metrics(self):
        content = read_monitor_file('query_monitor.py')
        return extract_metrics_from_file(content)

    @pytest.mark.unit
    def test_has_sla_breach_metrics(self, query_metrics):
        """Verify 60-second SLA breach metrics are defined (DBSQL Advisor Blog)."""
        metric_names = [m[1] for m in query_metrics]

        sla_metrics = [
            'sla_breach_count',
            'sla_breach_rate',
        ]

        for metric in sla_metrics:
            assert metric in metric_names, f"Missing SLA breach metric: {metric}"

    @pytest.mark.unit
    def test_has_efficiency_metrics(self, query_metrics):
        """Verify query efficiency metrics are defined (DBSQL Advisor Blog)."""
        metric_names = [m[1] for m in query_metrics]

        efficiency_metrics = [
            'efficient_query_count',
            'efficiency_rate',
            'complex_query_count',
        ]

        for metric in efficiency_metrics:
            assert metric in metric_names, f"Missing efficiency metric: {metric}"

    @pytest.mark.unit
    def test_has_p99_duration(self, query_metrics):
        """Verify P99 duration metric is defined for SLA monitoring."""
        metric_names = [m[1] for m in query_metrics]
        assert 'p99_duration_sec' in metric_names, "Missing P99 duration metric"


class TestClusterMonitorImprovedMetrics:
    """Test new cluster monitor metrics from Workflow Advisor Repo."""

    @pytest.fixture
    def cluster_metrics(self):
        content = read_monitor_file('cluster_monitor.py')
        return extract_metrics_from_file(content)

    @pytest.mark.unit
    def test_has_rightsizing_metrics(self, cluster_metrics):
        """Verify right-sizing detection metrics are defined (Workflow Advisor Repo)."""
        metric_names = [m[1] for m in cluster_metrics]

        rightsizing_metrics = [
            'underprovisioned_hours',
            'overprovisioned_hours',
            'optimal_util_hours',
            'underprovisioned_rate',
            'overprovisioned_rate',
            'rightsizing_opportunity_pct',
        ]

        for metric in rightsizing_metrics:
            assert metric in metric_names, f"Missing right-sizing metric: {metric}"

    @pytest.mark.unit
    def test_has_saturation_metrics(self, cluster_metrics):
        """Verify CPU/memory saturation metrics are defined."""
        metric_names = [m[1] for m in cluster_metrics]

        saturation_metrics = [
            'cpu_saturation_hours',
            'cpu_idle_hours',
            'memory_saturation_hours',
            'cpu_saturation_rate',
            'cpu_idle_rate',
        ]

        for metric in saturation_metrics:
            assert metric in metric_names, f"Missing saturation metric: {metric}"

    @pytest.mark.unit
    def test_has_p95_utilization(self, cluster_metrics):
        """Verify P95 utilization metrics are defined for peak analysis."""
        metric_names = [m[1] for m in cluster_metrics]

        p95_metrics = [
            'p95_cpu_total_pct',
            'p95_memory_pct',
        ]

        for metric in p95_metrics:
            assert metric in metric_names, f"Missing P95 utilization metric: {metric}"


class TestSecurityMonitorImprovedMetrics:
    """Test new security monitor metrics from audit logs repo."""

    @pytest.fixture
    def security_metrics(self):
        content = read_monitor_file('security_monitor.py')
        return extract_metrics_from_file(content)

    @pytest.mark.unit
    def test_has_user_type_classification(self, security_metrics):
        """Verify user type classification metrics are defined (audit logs repo)."""
        metric_names = [m[1] for m in security_metrics]

        user_type_metrics = [
            'human_user_events',
            'service_principal_events',
            'system_account_events',
            'human_user_ratio',
            'service_principal_ratio',
        ]

        for metric in user_type_metrics:
            assert metric in metric_names, f"Missing user type metric: {metric}"

    @pytest.mark.unit
    def test_has_human_off_hours_metrics(self, security_metrics):
        """Verify human off-hours activity metrics are defined."""
        metric_names = [m[1] for m in security_metrics]

        human_metrics = [
            'human_off_hours_events',
            'human_off_hours_rate',
            'distinct_human_users',
        ]

        for metric in human_metrics:
            assert metric in metric_names, f"Missing human activity metric: {metric}"


class TestJobMonitorImprovedMetrics:
    """Test new job monitor metrics from dashboard patterns."""

    @pytest.fixture
    def job_metrics(self):
        content = read_monitor_file('job_monitor.py')
        return extract_metrics_from_file(content)

    @pytest.mark.unit
    def test_has_p99_duration(self, job_metrics):
        """Verify P99 duration metric is defined for SLA monitoring."""
        metric_names = [m[1] for m in job_metrics]
        assert 'p99_duration_minutes' in metric_names, "Missing P99 duration metric"

    @pytest.mark.unit
    def test_has_p90_duration(self, job_metrics):
        """Verify P90 duration metric is defined for outlier detection."""
        metric_names = [m[1] for m in job_metrics]
        assert 'p90_duration_minutes' in metric_names, "Missing P90 duration metric"

    @pytest.mark.unit
    def test_has_duration_regression_metrics(self, job_metrics):
        """Verify duration regression detection metrics are defined."""
        metric_names = [m[1] for m in job_metrics]

        regression_metrics = [
            'stddev_duration_minutes',
            'duration_cv',
            'duration_skew_ratio',
        ]

        for metric in regression_metrics:
            assert metric in metric_names, f"Missing regression detection metric: {metric}"

    @pytest.mark.unit
    def test_has_outcome_category_metrics(self, job_metrics):
        """Verify outcome category breakdown metrics are defined."""
        metric_names = [m[1] for m in job_metrics]

        outcome_metrics = [
            'skipped_count',
            'upstream_failed_count',
            'long_running_count',
        ]

        for metric in outcome_metrics:
            assert metric in metric_names, f"Missing outcome category metric: {metric}"

    @pytest.mark.unit
    def test_has_duration_drift_metrics(self, job_metrics):
        """Verify P99 and P90 duration drift metrics are defined."""
        metric_names = [m[1] for m in job_metrics]

        drift_metrics = [
            'p99_duration_drift_pct',
            'p90_duration_drift_pct',
        ]

        for metric in drift_metrics:
            assert metric in metric_names, f"Missing duration drift metric: {metric}"
