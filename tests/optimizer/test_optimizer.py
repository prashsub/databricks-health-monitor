"""
Tests for the Genie Space Optimizer toolkit.

These tests verify the optimizer components work correctly
without requiring actual API calls.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.optimizer.models import (
    ControlLever,
    Fix,
    GenieResponse,
    OptimizerState,
    ResponseStatus,
    TestCase,
    TestVerdict,
)
from src.optimizer.config import (
    GENIE_SPACES,
    get_space_id,
    get_space_info,
    list_domains,
)
from src.optimizer.test_loader import (
    load_test_cases,
    load_test_cases_by_domain,
    get_test_summary,
)


class TestGenieSpaceConfig:
    """Test Genie Space configuration."""
    
    def test_all_domains_defined(self):
        """Verify all expected domains are defined."""
        expected_domains = ["cost", "reliability", "quality", "performance", "security", "unified"]
        for domain in expected_domains:
            assert domain in GENIE_SPACES
    
    def test_space_ids_are_valid(self):
        """Verify space IDs are valid format."""
        for domain, info in GENIE_SPACES.items():
            assert "id" in info
            assert len(info["id"]) == 32  # Genie space IDs are 32 chars
    
    def test_get_space_id(self):
        """Test get_space_id function."""
        cost_id = get_space_id("cost")
        assert cost_id == "01f0f1a3c2dc1c8897de11d27ca2cb6f"
    
    def test_get_space_id_invalid_domain(self):
        """Test get_space_id with invalid domain."""
        with pytest.raises(KeyError):
            get_space_id("invalid_domain")
    
    def test_get_space_info(self):
        """Test get_space_info function."""
        info = get_space_info("cost")
        assert "id" in info
        assert "name" in info
        assert "description" in info
        assert "emoji" in info
    
    def test_list_domains(self):
        """Test list_domains function."""
        domains = list_domains()
        assert len(domains) == 6
        assert "cost" in domains
        assert "unified" in domains


class TestGenieResponse:
    """Test GenieResponse model."""
    
    def test_successful_response(self):
        """Test a successful response."""
        response = GenieResponse(
            status=ResponseStatus.COMPLETED,
            sql="SELECT * FROM fact_usage",
            result_data=[{"total": 100}],
            result_columns=["total"],
        )
        
        assert response.is_success
        assert response.row_count == 1
        assert response.sql is not None
    
    def test_failed_response(self):
        """Test a failed response."""
        response = GenieResponse(
            status=ResponseStatus.FAILED,
            error="Query timeout",
        )
        
        assert not response.is_success
        assert response.row_count == 0
        assert response.error == "Query timeout"
    
    def test_empty_results(self):
        """Test response with empty results."""
        response = GenieResponse(
            status=ResponseStatus.COMPLETED,
            sql="SELECT * FROM empty_table",
            result_data=[],
        )
        
        assert response.is_success
        assert response.row_count == 0


class TestOptimizerState:
    """Test OptimizerState model."""
    
    def test_accuracy_calculation(self):
        """Test accuracy percentage calculation."""
        state = OptimizerState(
            space_id="test",
            space_name="Test Space",
            tests_run=10,
            tests_passed=9,
            tests_failed=1,
        )
        
        assert state.accuracy == 90.0
    
    def test_target_met(self):
        """Test target accuracy check."""
        state_met = OptimizerState(
            space_id="test",
            space_name="Test Space",
            tests_run=100,
            tests_passed=96,
            tests_failed=4,
        )
        assert state_met.is_target_met  # 96% >= 95%
        
        state_not_met = OptimizerState(
            space_id="test",
            space_name="Test Space",
            tests_run=100,
            tests_passed=90,
            tests_failed=10,
        )
        assert not state_not_met.is_target_met  # 90% < 95%
    
    def test_to_dict(self):
        """Test serialization to dict."""
        state = OptimizerState(
            space_id="test123",
            space_name="Test Space",
            tests_run=5,
            tests_passed=4,
        )
        
        data = state.to_dict()
        assert data["space_id"] == "test123"
        assert data["tests_run"] == 5
        assert "current_accuracy" in data
    
    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "space_id": "test123",
            "space_name": "Test Space",
            "tests_run": 5,
            "tests_passed": 4,
            "tests_failed": 1,
            "target_accuracy": 95.0,
        }
        
        state = OptimizerState.from_dict(data)
        assert state.space_id == "test123"
        assert state.tests_run == 5


class TestTestCase:
    """Test TestCase model."""
    
    def test_create_test_case(self):
        """Test creating a test case."""
        tc = TestCase(
            id="cost_001",
            category="simple_aggregation",
            domain="cost",
            question="What is our total spend?",
            validation={"type": "result_check"},
            critical=True,
        )
        
        assert tc.id == "cost_001"
        assert tc.critical is True
        assert tc.domain == "cost"


class TestFix:
    """Test Fix model."""
    
    def test_create_fix(self):
        """Test creating a fix."""
        fix = Fix(
            id="fix_001",
            control_lever=ControlLever.UC_TABLE_METADATA,
            test_case_id="cost_004",
            description="Updated fact_usage comment",
            before="Old comment",
            after="New comment with cost context",
            sql="ALTER TABLE fact_usage SET TBLPROPERTIES...",
            verified=True,
        )
        
        assert fix.control_lever == ControlLever.UC_TABLE_METADATA
        assert fix.verified is True


class TestTestLoader:
    """Test the test case loader."""
    
    def test_load_test_cases(self):
        """Test loading test cases from YAML."""
        test_cases = load_test_cases()
        
        assert len(test_cases) > 0
        assert all(isinstance(tc, TestCase) for tc in test_cases)
    
    def test_load_test_cases_by_domain(self):
        """Test loading test cases grouped by domain."""
        by_domain = load_test_cases_by_domain()
        
        assert "cost" in by_domain
        assert "reliability" in by_domain
        assert all(isinstance(tc, TestCase) for tc in by_domain["cost"])
    
    def test_load_critical_only(self):
        """Test loading only critical test cases."""
        all_tests = load_test_cases()
        critical_tests = load_test_cases(critical_only=True)
        
        assert len(critical_tests) < len(all_tests)
        assert all(tc.critical for tc in critical_tests)
    
    def test_load_by_domain_filter(self):
        """Test filtering by domain."""
        cost_tests = load_test_cases(domain="cost")
        
        assert len(cost_tests) > 0
        assert all(tc.domain == "cost" for tc in cost_tests)
    
    def test_get_test_summary(self):
        """Test getting test summary."""
        summary = get_test_summary()
        
        assert "total" in summary
        assert "critical" in summary
        assert "by_domain" in summary
        assert "by_category" in summary


class TestControlLeverPriority:
    """Test control lever definitions."""
    
    def test_all_levers_defined(self):
        """Verify all expected control levers are defined."""
        expected_levers = [
            ControlLever.UC_TABLE_METADATA,
            ControlLever.UC_COLUMN_METADATA,
            ControlLever.UC_METRIC_VIEW,
            ControlLever.UC_FUNCTION,
            ControlLever.LAKEHOUSE_MONITORING,
            ControlLever.ML_INFERENCE_TABLE,
            ControlLever.GENIE_INSTRUCTION,
            ControlLever.GENIE_SAMPLE_QUERY,
        ]
        
        for lever in expected_levers:
            assert lever.value is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
