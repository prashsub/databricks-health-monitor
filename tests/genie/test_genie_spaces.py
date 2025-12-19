"""
Tests for Genie Space Configuration Validation
===============================================

These tests validate Genie Space JSON configuration files for:
- Valid JSON structure
- Required fields (name, description, instructions, data_assets)
- Data asset completeness
- Benchmark questions format
- Variable placeholders
"""

import pytest
import json
from pathlib import Path


# Path to Genie Space configuration files
GENIE_DIR = Path(__file__).parent.parent.parent / "src" / "genie"


def get_genie_files():
    """Get all Genie Space JSON files."""
    return list(GENIE_DIR.glob("*.json"))


def load_genie_json(file_path):
    """Load Genie Space JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


class TestGenieSpaceStructure:
    """Test Genie Space JSON structure."""

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_genie_files(), ids=lambda x: x.name)
    def test_valid_json(self, json_file):
        """Verify Genie Space file is valid JSON."""
        try:
            config = load_genie_json(json_file)
            assert isinstance(config, dict), f"{json_file.name} should be a JSON object"
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in {json_file.name}: {str(e)}")

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_genie_files(), ids=lambda x: x.name)
    def test_has_name(self, json_file):
        """Verify Genie Space has name field."""
        config = load_genie_json(json_file)
        assert 'name' in config, f"Missing 'name' in {json_file.name}"
        assert len(config['name']) > 0, f"Empty name in {json_file.name}"

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_genie_files(), ids=lambda x: x.name)
    def test_has_display_name(self, json_file):
        """Verify Genie Space has display_name field."""
        config = load_genie_json(json_file)
        assert 'display_name' in config, f"Missing 'display_name' in {json_file.name}"
        assert len(config['display_name']) > 0, f"Empty display_name in {json_file.name}"

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_genie_files(), ids=lambda x: x.name)
    def test_has_description(self, json_file):
        """Verify Genie Space has description field."""
        config = load_genie_json(json_file)
        assert 'description' in config, f"Missing 'description' in {json_file.name}"
        assert len(config['description']) > 50, f"Description too short in {json_file.name}"

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_genie_files(), ids=lambda x: x.name)
    def test_has_instructions(self, json_file):
        """Verify Genie Space has comprehensive instructions."""
        config = load_genie_json(json_file)
        assert 'instructions' in config, f"Missing 'instructions' in {json_file.name}"
        # Instructions should be substantial (>500 chars for good context)
        assert len(config['instructions']) > 500, (
            f"Instructions too short in {json_file.name}. "
            "Genie needs comprehensive business context."
        )


class TestGenieSpaceDataAssets:
    """Test Genie Space data asset configurations."""

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_genie_files(), ids=lambda x: x.name)
    def test_has_data_assets(self, json_file):
        """Verify Genie Space has data_assets defined."""
        config = load_genie_json(json_file)
        assert 'data_assets' in config, f"Missing 'data_assets' in {json_file.name}"
        assert len(config['data_assets']) > 0, f"No data_assets defined in {json_file.name}"

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_genie_files(), ids=lambda x: x.name)
    def test_data_assets_have_type(self, json_file):
        """Verify all data assets have type field."""
        config = load_genie_json(json_file)

        valid_types = {'metric_view', 'function', 'table'}

        for asset in config.get('data_assets', []):
            assert 'type' in asset, (
                f"Data asset missing 'type' in {json_file.name}"
            )
            assert asset['type'] in valid_types, (
                f"Invalid asset type '{asset['type']}' in {json_file.name}. "
                f"Valid types: {valid_types}"
            )

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_genie_files(), ids=lambda x: x.name)
    def test_data_assets_have_name(self, json_file):
        """Verify all data assets have name field."""
        config = load_genie_json(json_file)

        for asset in config.get('data_assets', []):
            assert 'name' in asset, (
                f"Data asset missing 'name' in {json_file.name}"
            )
            assert len(asset['name']) > 0, (
                f"Empty asset name in {json_file.name}"
            )

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_genie_files(), ids=lambda x: x.name)
    def test_data_assets_use_variable_placeholders(self, json_file):
        """Verify data assets use ${catalog} and ${gold_schema} placeholders."""
        config = load_genie_json(json_file)

        for asset in config.get('data_assets', []):
            if 'catalog' in asset:
                assert '${catalog}' in asset['catalog'], (
                    f"Asset '{asset.get('name')}' should use ${{catalog}} placeholder in {json_file.name}"
                )
            if 'schema' in asset:
                assert '${gold_schema}' in asset['schema'], (
                    f"Asset '{asset.get('name')}' should use ${{gold_schema}} placeholder in {json_file.name}"
                )

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_genie_files(), ids=lambda x: x.name)
    def test_has_metric_view_or_tvf(self, json_file):
        """Verify Genie Space has at least one metric_view or function."""
        config = load_genie_json(json_file)

        asset_types = [asset.get('type') for asset in config.get('data_assets', [])]

        has_metric_view = 'metric_view' in asset_types
        has_function = 'function' in asset_types

        assert has_metric_view or has_function, (
            f"Genie Space {json_file.name} should have at least one "
            "metric_view or function for optimized queries."
        )


class TestGenieSpaceBenchmarks:
    """Test Genie Space benchmark questions."""

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_genie_files(), ids=lambda x: x.name)
    def test_has_benchmark_questions(self, json_file):
        """Verify Genie Space has benchmark questions."""
        config = load_genie_json(json_file)
        assert 'benchmark_questions' in config, (
            f"Missing 'benchmark_questions' in {json_file.name}"
        )
        assert len(config['benchmark_questions']) >= 3, (
            f"Should have at least 3 benchmark questions in {json_file.name}"
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_genie_files(), ids=lambda x: x.name)
    def test_benchmark_questions_have_required_fields(self, json_file):
        """Verify benchmark questions have question and expected fields."""
        config = load_genie_json(json_file)

        for i, question in enumerate(config.get('benchmark_questions', [])):
            assert 'question' in question, (
                f"Benchmark Q{i+1} missing 'question' in {json_file.name}"
            )
            assert len(question['question']) > 10, (
                f"Benchmark Q{i+1} question too short in {json_file.name}"
            )
            assert 'expected_result_type' in question, (
                f"Benchmark Q{i+1} missing 'expected_result_type' in {json_file.name}"
            )

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_genie_files(), ids=lambda x: x.name)
    def test_benchmark_result_types_valid(self, json_file):
        """Verify benchmark result types are valid."""
        config = load_genie_json(json_file)

        valid_result_types = {'single_value', 'table', 'chart', 'list'}

        for i, question in enumerate(config.get('benchmark_questions', [])):
            result_type = question.get('expected_result_type', '')
            assert result_type in valid_result_types, (
                f"Benchmark Q{i+1} has invalid result type '{result_type}' in {json_file.name}. "
                f"Valid types: {valid_result_types}"
            )


class TestGenieSpaceInstructions:
    """Test Genie Space instruction quality."""

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_genie_files(), ids=lambda x: x.name)
    def test_instructions_have_domain_knowledge(self, json_file):
        """Verify instructions include business domain knowledge."""
        config = load_genie_json(json_file)
        instructions = config.get('instructions', '').upper()

        # Should have domain knowledge section
        assert 'DOMAIN' in instructions or 'KNOWLEDGE' in instructions or 'CONCEPT' in instructions, (
            f"Instructions should include domain knowledge section in {json_file.name}"
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_genie_files(), ids=lambda x: x.name)
    def test_instructions_have_data_assets_section(self, json_file):
        """Verify instructions reference data assets."""
        config = load_genie_json(json_file)
        instructions = config.get('instructions', '').upper()

        # Should reference data assets
        assert 'DATA ASSET' in instructions or 'METRIC VIEW' in instructions or 'TVF' in instructions or 'FUNCTION' in instructions, (
            f"Instructions should reference available data assets in {json_file.name}"
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_genie_files(), ids=lambda x: x.name)
    def test_instructions_have_guardrails(self, json_file):
        """Verify instructions include guardrails."""
        config = load_genie_json(json_file)
        instructions = config.get('instructions', '').upper()

        # Should have guardrails/constraints
        assert 'GUARDRAIL' in instructions or 'READ-ONLY' in instructions or 'DO NOT' in instructions, (
            f"Instructions should include guardrails in {json_file.name}"
        )


class TestGenieSpaceFileStructure:
    """Test Genie Space file structure."""

    @pytest.mark.unit
    def test_expected_files_exist(self):
        """Verify expected Genie Space files exist."""
        expected_files = [
            'cost_intelligence.json',
            'job_health_monitor.json',
            'query_performance.json',
            'cluster_optimizer.json',
            'security_auditor.json',
            'health_monitor_unified.json',
        ]

        for filename in expected_files:
            file_path = GENIE_DIR / filename
            assert file_path.exists(), f"Missing Genie Space file: {filename}"

    @pytest.mark.unit
    def test_deploy_script_exists(self):
        """Verify Genie Space deployment script exists."""
        deploy_script = GENIE_DIR / 'deploy_genie_spaces.py'
        assert deploy_script.exists(), "Missing deploy_genie_spaces.py script"

    @pytest.mark.unit
    def test_init_file_exists(self):
        """Verify __init__.py exists in genie directory."""
        init_path = GENIE_DIR / '__init__.py'
        assert init_path.exists(), "Missing __init__.py in genie directory"


class TestGenieSpaceDescriptions:
    """Test Genie Space descriptions include example questions."""

    @pytest.mark.unit
    @pytest.mark.parametrize("json_file", get_genie_files(), ids=lambda x: x.name)
    def test_description_has_example_questions(self, json_file):
        """Verify description includes example questions for users."""
        config = load_genie_json(json_file)
        description = config.get('description', '').lower()

        # Should include example questions
        assert 'example' in description or '?' in description, (
            f"Description should include example questions in {json_file.name}"
        )
