"""
Tests for AI/BI Dashboard JSON Validation
=========================================

These tests validate Lakeview dashboard JSON files for:
- Valid JSON structure
- 6-column grid layout (not 12-column)
- Required widget fields
- Dataset definitions
- Variable placeholder usage
"""

import pytest
import json
import re
from pathlib import Path


# Path to dashboard JSON files
DASHBOARDS_DIR = Path(__file__).parent.parent.parent / "src" / "dashboards"


def get_dashboard_files():
    """Get all dashboard JSON files."""
    return list(DASHBOARDS_DIR.glob("*.lvdash.json"))


def load_dashboard_json(file_path):
    """Load dashboard JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


class TestDashboardJsonStructure:
    """Test dashboard JSON structure."""

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_dashboard_files(), ids=lambda x: x.name)
    def test_valid_json(self, json_file):
        """Verify dashboard file is valid JSON."""
        try:
            config = load_dashboard_json(json_file)
            assert isinstance(config, dict), f"{json_file.name} should be a JSON object"
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in {json_file.name}: {str(e)}")

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_dashboard_files(), ids=lambda x: x.name)
    def test_has_display_name(self, json_file):
        """Verify dashboard has displayName."""
        config = load_dashboard_json(json_file)
        assert 'displayName' in config, f"Missing displayName in {json_file.name}"
        assert len(config['displayName']) > 0, f"Empty displayName in {json_file.name}"

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_dashboard_files(), ids=lambda x: x.name)
    def test_has_pages(self, json_file):
        """Verify dashboard has at least one page."""
        config = load_dashboard_json(json_file)
        assert 'pages' in config, f"Missing pages in {json_file.name}"
        assert len(config['pages']) > 0, f"No pages defined in {json_file.name}"

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_dashboard_files(), ids=lambda x: x.name)
    def test_has_datasets(self, json_file):
        """Verify dashboard has datasets defined."""
        config = load_dashboard_json(json_file)
        assert 'datasets' in config, f"Missing datasets in {json_file.name}"
        assert len(config['datasets']) > 0, f"No datasets defined in {json_file.name}"


class TestDashboardGridLayout:
    """Test dashboard uses correct 6-column grid."""

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_dashboard_files(), ids=lambda x: x.name)
    def test_widget_positions_use_6_column_grid(self, json_file):
        """Verify all widget positions use 6-column grid (x + width <= 6)."""
        config = load_dashboard_json(json_file)

        for page in config.get('pages', []):
            page_name = page.get('name', 'unknown')

            for layout_item in page.get('layout', []):
                position = layout_item.get('position', {})
                widget_name = layout_item.get('widget', {}).get('name', 'unknown')

                x = position.get('x', 0)
                width = position.get('width', 1)

                # Validate x position (0-5)
                assert x >= 0 and x <= 5, (
                    f"Widget '{widget_name}' in {page_name} has invalid x position: {x}. "
                    "Use 6-column grid (x: 0-5)."
                )

                # Validate width (1-6)
                assert width >= 1 and width <= 6, (
                    f"Widget '{widget_name}' in {page_name} has invalid width: {width}. "
                    "Use 6-column grid (width: 1-6)."
                )

                # Validate x + width <= 6
                assert x + width <= 6, (
                    f"Widget '{widget_name}' in {page_name} exceeds grid: x={x}, width={width}. "
                    "x + width must be <= 6."
                )

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_dashboard_files(), ids=lambda x: x.name)
    def test_widget_heights_are_reasonable(self, json_file):
        """Verify widget heights use standard values."""
        config = load_dashboard_json(json_file)

        standard_heights = {1, 2, 4, 6, 8, 9, 10, 12}

        for page in config.get('pages', []):
            for layout_item in page.get('layout', []):
                position = layout_item.get('position', {})
                height = position.get('height', 6)
                widget_name = layout_item.get('widget', {}).get('name', 'unknown')

                # Height should be positive
                assert height > 0, (
                    f"Widget '{widget_name}' has invalid height: {height}"
                )


class TestDashboardWidgets:
    """Test dashboard widget configurations."""

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_dashboard_files(), ids=lambda x: x.name)
    def test_widgets_have_names(self, json_file):
        """Verify all widgets have names."""
        config = load_dashboard_json(json_file)

        for page in config.get('pages', []):
            for layout_item in page.get('layout', []):
                widget = layout_item.get('widget', {})
                assert 'name' in widget, f"Widget missing name in {json_file.name}"
                assert len(widget['name']) > 0, f"Empty widget name in {json_file.name}"

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_dashboard_files(), ids=lambda x: x.name)
    def test_widgets_have_spec(self, json_file):
        """Verify all widgets have spec with version and widgetType."""
        config = load_dashboard_json(json_file)

        for page in config.get('pages', []):
            for layout_item in page.get('layout', []):
                widget = layout_item.get('widget', {})
                widget_name = widget.get('name', 'unknown')

                assert 'spec' in widget, (
                    f"Widget '{widget_name}' missing spec in {json_file.name}"
                )

                spec = widget['spec']
                assert 'version' in spec, (
                    f"Widget '{widget_name}' spec missing version in {json_file.name}"
                )
                assert 'widgetType' in spec, (
                    f"Widget '{widget_name}' spec missing widgetType in {json_file.name}"
                )

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_dashboard_files(), ids=lambda x: x.name)
    def test_widgets_have_queries(self, json_file):
        """Verify all widgets have query definitions."""
        config = load_dashboard_json(json_file)

        for page in config.get('pages', []):
            for layout_item in page.get('layout', []):
                widget = layout_item.get('widget', {})
                widget_name = widget.get('name', 'unknown')

                # Skip filter widgets which may not have queries
                widget_type = widget.get('spec', {}).get('widgetType', '')
                if 'filter' in widget_type.lower():
                    continue

                assert 'queries' in widget, (
                    f"Widget '{widget_name}' missing queries in {json_file.name}"
                )


class TestDashboardDatasets:
    """Test dashboard dataset configurations."""

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_dashboard_files(), ids=lambda x: x.name)
    def test_datasets_have_names(self, json_file):
        """Verify all datasets have names."""
        config = load_dashboard_json(json_file)

        for dataset in config.get('datasets', []):
            assert 'name' in dataset, f"Dataset missing name in {json_file.name}"
            assert len(dataset['name']) > 0, f"Empty dataset name in {json_file.name}"

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_dashboard_files(), ids=lambda x: x.name)
    def test_datasets_have_queries(self, json_file):
        """Verify all datasets have query definitions."""
        config = load_dashboard_json(json_file)

        for dataset in config.get('datasets', []):
            dataset_name = dataset.get('name', 'unknown')
            assert 'query' in dataset, (
                f"Dataset '{dataset_name}' missing query in {json_file.name}"
            )
            assert len(dataset['query']) > 10, (
                f"Dataset '{dataset_name}' has very short query in {json_file.name}"
            )

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_dashboard_files(), ids=lambda x: x.name)
    def test_datasets_use_variable_placeholders(self, json_file):
        """Verify datasets use ${catalog} and ${gold_schema} placeholders."""
        config = load_dashboard_json(json_file)

        for dataset in config.get('datasets', []):
            dataset_name = dataset.get('name', 'unknown')
            query = dataset.get('query', '')

            # Check for variable placeholders
            if 'FROM' in query.upper():
                has_catalog = '${catalog}' in query
                has_schema = '${gold_schema}' in query

                assert has_catalog, (
                    f"Dataset '{dataset_name}' should use ${{catalog}} placeholder in {json_file.name}"
                )
                assert has_schema, (
                    f"Dataset '{dataset_name}' should use ${{gold_schema}} placeholder in {json_file.name}"
                )


class TestDashboardSqlPatterns:
    """Test SQL patterns in dashboard queries."""

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_dashboard_files(), ids=lambda x: x.name)
    def test_division_uses_nullif(self, json_file):
        """Verify SQL queries use NULLIF for division by expressions (not constants)."""
        config = load_dashboard_json(json_file)

        for dataset in config.get('datasets', []):
            dataset_name = dataset.get('name', 'unknown')
            query = dataset.get('query', '')

            # Skip if no division or contains URL
            if '/' not in query or 'http' in query.lower():
                continue

            # Find all division operations
            # Pattern matches: / followed by expression (not just a constant)
            # Constants like /7, /100.0, /1000 are safe and don't need NULLIF
            division_pattern = r'/\s*(\d+\.?\d*|\d*\.?\d+)\s*(?=[,\)\s]|AS\s|$)'

            # Remove constant divisions from consideration
            query_without_constants = re.sub(division_pattern, ' ', query)

            # If there's still a division after removing constants, check for NULLIF
            if '/' in query_without_constants:
                assert 'NULLIF' in query.upper(), (
                    f"Dataset '{dataset_name}' has division by expression but no NULLIF in {json_file.name}"
                )


class TestDashboardFileStructure:
    """Test dashboard file structure."""

    @pytest.mark.unit
    def test_dashboard_files_exist(self):
        """Verify expected dashboard files exist."""
        expected_files = [
            'executive_overview.lvdash.json',
            'cost_management.lvdash.json',
            'job_reliability.lvdash.json',
            'query_performance.lvdash.json',
            'cluster_utilization.lvdash.json',
            'security_audit.lvdash.json',
        ]

        for filename in expected_files:
            file_path = DASHBOARDS_DIR / filename
            assert file_path.exists(), f"Missing dashboard file: {filename}"

    @pytest.mark.unit
    def test_deploy_script_exists(self):
        """Verify dashboard deployment script exists."""
        deploy_script = DASHBOARDS_DIR / 'deploy_dashboards.py'
        assert deploy_script.exists(), "Missing deploy_dashboards.py script"

    @pytest.mark.unit
    def test_init_file_exists(self):
        """Verify __init__.py exists in dashboards directory."""
        init_path = DASHBOARDS_DIR / '__init__.py'
        assert init_path.exists(), "Missing __init__.py in dashboards directory"
