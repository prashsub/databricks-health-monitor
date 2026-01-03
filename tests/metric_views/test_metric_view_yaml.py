"""
Tests for Metric View YAML Validation
======================================

These tests validate Metric View YAML files for:
- Correct v1.1 schema structure
- Required fields (version, source, dimensions, measures)
- source. prefix usage in expressions
- Join configurations with 'on' quoted
- Measure aggregation functions
- Synonym definitions for Genie discoverability
"""

import pytest
import yaml
import re
from pathlib import Path


# Path to Metric View YAML files
METRIC_VIEWS_DIR = Path(__file__).parent.parent.parent / "src" / "semantic" / "metric_views"


def get_metric_view_files():
    """Get all Metric View YAML files."""
    return list(METRIC_VIEWS_DIR.glob("*.yaml"))


def load_yaml_file(file_path):
    """Load and return YAML file contents as dict."""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def read_yaml_raw(file_path):
    """Read YAML file as raw string for pattern matching."""
    with open(file_path, 'r') as f:
        return f.read()


class TestMetricViewSchema:
    """Test Metric View YAML schema compliance."""

    @pytest.mark.unit
    @pytest.mark.parametrize("yaml_file", get_metric_view_files(), ids=lambda x: x.name)
    def test_has_required_version(self, yaml_file):
        """Verify metric view has version field set to 1.1."""
        config = load_yaml_file(yaml_file)

        assert 'version' in config, f"Missing 'version' field in {yaml_file.name}"
        assert config['version'] == "1.1", (
            f"Version should be '1.1' in {yaml_file.name}, got: {config['version']}"
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("yaml_file", get_metric_view_files(), ids=lambda x: x.name)
    def test_has_source(self, yaml_file):
        """Verify metric view has source table defined with valid schema."""
        config = load_yaml_file(yaml_file)

        assert 'source' in config, f"Missing 'source' field in {yaml_file.name}"
        assert '${catalog}' in config['source'], (
            f"Source should use ${{catalog}} variable in {yaml_file.name}"
        )
        # Allow multiple valid schema patterns:
        # - ${gold_schema} for Gold layer tables
        # - information_schema for system tables
        # - ${feature_schema} or ${ml_schema} for ML tables
        valid_schema_patterns = [
            '${gold_schema}',
            'information_schema',
            '${feature_schema}',
            '${ml_schema}'
        ]
        has_valid_schema = any(pattern in config['source'] for pattern in valid_schema_patterns)
        assert has_valid_schema, (
            f"Source should use a valid schema variable in {yaml_file.name}. "
            f"Allowed: {valid_schema_patterns}. Got: {config['source']}"
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("yaml_file", get_metric_view_files(), ids=lambda x: x.name)
    def test_has_dimensions(self, yaml_file):
        """Verify metric view has dimensions defined."""
        config = load_yaml_file(yaml_file)

        assert 'dimensions' in config, f"Missing 'dimensions' field in {yaml_file.name}"
        assert len(config['dimensions']) > 0, f"No dimensions defined in {yaml_file.name}"

    @pytest.mark.unit
    @pytest.mark.parametrize("yaml_file", get_metric_view_files(), ids=lambda x: x.name)
    def test_has_measures(self, yaml_file):
        """Verify metric view has measures defined."""
        config = load_yaml_file(yaml_file)

        assert 'measures' in config, f"Missing 'measures' field in {yaml_file.name}"
        assert len(config['measures']) > 0, f"No measures defined in {yaml_file.name}"

    @pytest.mark.unit
    @pytest.mark.parametrize("yaml_file", get_metric_view_files(), ids=lambda x: x.name)
    def test_has_comment(self, yaml_file):
        """Verify metric view has top-level comment."""
        config = load_yaml_file(yaml_file)

        assert 'comment' in config, f"Missing 'comment' field in {yaml_file.name}"
        assert len(config['comment']) > 50, (
            f"Comment should be descriptive (>50 chars) in {yaml_file.name}"
        )


class TestDimensionFields:
    """Test dimension field requirements."""

    @pytest.mark.unit
    @pytest.mark.parametrize("yaml_file", get_metric_view_files(), ids=lambda x: x.name)
    def test_dimension_has_required_fields(self, yaml_file):
        """Verify each dimension has name, expr, and comment."""
        config = load_yaml_file(yaml_file)

        for i, dim in enumerate(config.get('dimensions', [])):
            assert 'name' in dim, f"Dimension {i} missing 'name' in {yaml_file.name}"
            assert 'expr' in dim, f"Dimension '{dim.get('name', i)}' missing 'expr' in {yaml_file.name}"
            assert 'comment' in dim, f"Dimension '{dim.get('name', i)}' missing 'comment' in {yaml_file.name}"

    @pytest.mark.unit
    @pytest.mark.parametrize("yaml_file", get_metric_view_files(), ids=lambda x: x.name)
    def test_dimension_uses_source_prefix(self, yaml_file):
        """Verify dimension expressions reference source. or joined table."""
        config = load_yaml_file(yaml_file)

        # Get join names for valid prefixes
        valid_prefixes = ['source.']
        for join in config.get('joins', []):
            if 'name' in join:
                valid_prefixes.append(f"{join['name']}.")

        for dim in config.get('dimensions', []):
            expr = dim.get('expr', '')
            # Check if expression uses a valid prefix or is a function like DATE()
            has_valid_prefix = any(prefix in expr for prefix in valid_prefixes)
            is_function = re.match(r'^[A-Z_]+\(', expr)

            assert has_valid_prefix or is_function, (
                f"Dimension '{dim.get('name')}' expr should use 'source.' prefix "
                f"or joined table name in {yaml_file.name}. Got: {expr}"
            )

    @pytest.mark.unit
    @pytest.mark.parametrize("yaml_file", get_metric_view_files(), ids=lambda x: x.name)
    def test_dimension_has_synonyms(self, yaml_file):
        """Verify dimensions have synonyms for Genie discoverability."""
        config = load_yaml_file(yaml_file)

        dims_with_synonyms = sum(1 for d in config.get('dimensions', []) if 'synonyms' in d)
        total_dims = len(config.get('dimensions', []))

        # At least 80% should have synonyms
        assert dims_with_synonyms >= total_dims * 0.8, (
            f"Only {dims_with_synonyms}/{total_dims} dimensions have synonyms in {yaml_file.name}. "
            "Add synonyms to improve Genie natural language queries."
        )


class TestMeasureFields:
    """Test measure field requirements."""

    @pytest.mark.unit
    @pytest.mark.parametrize("yaml_file", get_metric_view_files(), ids=lambda x: x.name)
    def test_measure_has_required_fields(self, yaml_file):
        """Verify each measure has name, expr, and comment."""
        config = load_yaml_file(yaml_file)

        for i, measure in enumerate(config.get('measures', [])):
            assert 'name' in measure, f"Measure {i} missing 'name' in {yaml_file.name}"
            assert 'expr' in measure, f"Measure '{measure.get('name', i)}' missing 'expr' in {yaml_file.name}"
            assert 'comment' in measure, f"Measure '{measure.get('name', i)}' missing 'comment' in {yaml_file.name}"

    @pytest.mark.unit
    @pytest.mark.parametrize("yaml_file", get_metric_view_files(), ids=lambda x: x.name)
    def test_measure_uses_aggregation(self, yaml_file):
        """Verify measure expressions use aggregation functions."""
        config = load_yaml_file(yaml_file)

        agg_functions = ['SUM', 'COUNT', 'AVG', 'MIN', 'MAX', 'PERCENTILE']

        for measure in config.get('measures', []):
            expr = measure.get('expr', '').upper()
            has_aggregation = any(agg in expr for agg in agg_functions)

            assert has_aggregation, (
                f"Measure '{measure.get('name')}' should use an aggregation function "
                f"(SUM, COUNT, AVG, etc.) in {yaml_file.name}. Got: {measure.get('expr')}"
            )

    @pytest.mark.unit
    @pytest.mark.parametrize("yaml_file", get_metric_view_files(), ids=lambda x: x.name)
    def test_measure_has_format(self, yaml_file):
        """Verify measures have format specifications."""
        config = load_yaml_file(yaml_file)

        measures_with_format = sum(1 for m in config.get('measures', []) if 'format' in m)
        total_measures = len(config.get('measures', []))

        # At least 80% should have format
        assert measures_with_format >= total_measures * 0.8, (
            f"Only {measures_with_format}/{total_measures} measures have format in {yaml_file.name}. "
            "Add format specifications for proper display."
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("yaml_file", get_metric_view_files(), ids=lambda x: x.name)
    def test_measure_has_synonyms(self, yaml_file):
        """Verify measures have synonyms for Genie discoverability."""
        config = load_yaml_file(yaml_file)

        measures_with_synonyms = sum(1 for m in config.get('measures', []) if 'synonyms' in m)
        total_measures = len(config.get('measures', []))

        # At least 80% should have synonyms
        assert measures_with_synonyms >= total_measures * 0.8, (
            f"Only {measures_with_synonyms}/{total_measures} measures have synonyms in {yaml_file.name}. "
            "Add synonyms to improve Genie natural language queries."
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("yaml_file", get_metric_view_files(), ids=lambda x: x.name)
    def test_division_uses_nullif(self, yaml_file):
        """Verify division operations use NULLIF to prevent divide-by-zero.

        Safe patterns (no NULLIF needed):
        - Division by numeric constants: / 1000.0, / 3600.0
        - Division by constant expressions: / (1024.0*1024.0*1024.0)
        """
        config = load_yaml_file(yaml_file)

        for measure in config.get('measures', []):
            expr = measure.get('expr', '')

            # Check if expression contains division
            if '/' in expr:
                # Check if dividing by a constant (safe) vs expression (needs NULLIF)
                # Safe patterns:
                # - / followed by digits/decimal: / 1000.0
                # - / followed by parenthesized constants: / (1024.0*1024.0*1024.0)
                constant_divisor = re.search(r'/\s*[\d.]+', expr)
                paren_constant = re.search(r'/\s*\([0-9.*\s]+\)', expr)

                if not constant_divisor and not paren_constant:
                    # Dividing by an expression - should use NULLIF
                    assert 'NULLIF' in expr.upper(), (
                        f"Measure '{measure.get('name')}' uses division by expression but no NULLIF in {yaml_file.name}. "
                        f"Use NULLIF(divisor, 0) to prevent divide-by-zero errors."
                    )


class TestJoinConfiguration:
    """Test join configuration requirements."""

    @pytest.mark.unit
    @pytest.mark.parametrize("yaml_file", get_metric_view_files(), ids=lambda x: x.name)
    def test_join_has_required_fields(self, yaml_file):
        """Verify each join has name, source, and 'on' clause."""
        config = load_yaml_file(yaml_file)

        for i, join in enumerate(config.get('joins', [])):
            assert 'name' in join, f"Join {i} missing 'name' in {yaml_file.name}"
            assert 'source' in join, f"Join '{join.get('name', i)}' missing 'source' in {yaml_file.name}"
            assert 'on' in join, f"Join '{join.get('name', i)}' missing 'on' clause in {yaml_file.name}"

    @pytest.mark.unit
    @pytest.mark.parametrize("yaml_file", get_metric_view_files(), ids=lambda x: x.name)
    def test_join_uses_is_current_filter(self, yaml_file):
        """Verify SCD Type 2 dimension joins filter on active records.

        Valid patterns:
        - is_current = true (explicit SCD2 flag)
        - delete_time IS NULL (soft delete pattern)

        Excluded dimensions (simple lookup tables, not SCD2):
        - dim_workspace: Simple lookup by workspace_id
        """
        config = load_yaml_file(yaml_file)

        # Dimensions that are simple lookups (not SCD2)
        simple_lookup_dims = {'dim_workspace'}

        for join in config.get('joins', []):
            join_name = join.get('name', '')
            on_clause = join.get('on', '').lower()

            # Check if joining to a dimension table (starts with dim_)
            if 'dim_' in join.get('source', ''):
                # Skip simple lookup dimensions that don't have SCD2
                if join_name in simple_lookup_dims:
                    continue

                # Accept either is_current or delete_time IS NULL pattern
                has_current_filter = 'is_current' in on_clause or 'delete_time' in on_clause
                assert has_current_filter, (
                    f"Join to dimension '{join_name}' in {yaml_file.name} missing SCD2 filter. "
                    f"Add 'AND {join_name}.is_current = true' or 'AND {join_name}.delete_time IS NULL' "
                    f"to prevent returning deleted/historical records."
                )

    @pytest.mark.unit
    @pytest.mark.parametrize("yaml_file", get_metric_view_files(), ids=lambda x: x.name)
    def test_on_clause_is_quoted(self, yaml_file):
        """Verify 'on' key is quoted in YAML (required for reserved word)."""
        raw_content = read_yaml_raw(yaml_file)

        # Look for unquoted 'on:' in join contexts
        # The pattern should be "'on':" not "on:"
        join_sections = re.findall(r'-\s+name:.*?(?=-\s+name:|dimensions:|$)', raw_content, re.DOTALL)

        for section in join_sections:
            if 'source:' in section:  # This is a join section
                # Check if 'on' is properly quoted
                if "on:" in section:
                    assert "'on':" in section, (
                        f"Join 'on' clause should be quoted as \"'on':\" in {yaml_file.name}. "
                        "The word 'on' is a YAML reserved word."
                    )


class TestMetricViewFileStructure:
    """Test metric view file structure and organization."""

    @pytest.mark.unit
    def test_expected_files_exist(self):
        """Verify expected metric view files exist."""
        expected_files = [
            'cost_analytics.yaml',
            'job_performance.yaml',
            'query_performance.yaml',
            'cluster_utilization.yaml',
            'security_events.yaml',
            'commit_tracking.yaml',
        ]

        for filename in expected_files:
            file_path = METRIC_VIEWS_DIR / filename
            assert file_path.exists(), f"Missing metric view file: {filename}"

    @pytest.mark.unit
    def test_deploy_script_exists(self):
        """Verify metric view deployment script exists."""
        deploy_script = METRIC_VIEWS_DIR / 'deploy_metric_views.py'
        assert deploy_script.exists(), "Missing deploy_metric_views.py script"

    @pytest.mark.unit
    @pytest.mark.parametrize("yaml_file", get_metric_view_files(), ids=lambda x: x.name)
    def test_file_has_header_comment(self, yaml_file):
        """Verify each YAML file has a descriptive header comment."""
        raw_content = read_yaml_raw(yaml_file)

        # Should start with a comment
        assert raw_content.strip().startswith('#'), (
            f"Metric view {yaml_file.name} should start with a header comment."
        )

        # Should identify it as a metric view (case-insensitive)
        header = raw_content[:200].lower()
        assert 'metric view' in header or 'metrics view' in header, (
            f"Header comment in {yaml_file.name} should identify it as a Metric View."
        )
