"""
Genie Space Optimizer Toolkit

An LLM-driven interactive optimization toolkit for improving Genie Space accuracy.
This module provides tools for Claude (or other LLMs) to:

1. Test Genie Spaces with golden queries
2. Analyze failures and determine root causes
3. Apply surgical fixes to UC metadata, Genie instructions, etc.
4. Track progress and checkpoint state
5. Test repeatability by running same questions multiple times

Usage:
    from src.optimizer import GenieClient, OptimizerConfig, TestResult
    
    # Initialize client
    client = GenieClient(
        workspace_url="https://your-workspace.cloud.databricks.com",
        space_id="your-space-id"
    )
    
    # Ask a question
    response = client.ask_question("What is our total spend?")
    
    # Examine results
    print(response.sql)
    print(response.result_data)
    
    # Test repeatability
    from src.optimizer import RepeatabilityTester
    tester = RepeatabilityTester(space_id="your-space-id")
    report = tester.test_repeatability(test_cases, num_iterations=3)
"""

from src.optimizer.genie_client import GenieClient, create_client_for_domain
from src.optimizer.models import (
    GenieResponse,
    TestCase,
    TestResult,
    ValidationResult,
    ControlLever,
    Fix,
    OptimizerState,
    ResponseStatus,
    TestVerdict,
)
from src.optimizer.config import (
    OptimizerConfig,
    load_config,
    GENIE_SPACES,
    get_space_id,
    get_space_info,
    list_domains,
    print_spaces_summary,
)
from src.optimizer.test_loader import (
    load_test_cases,
    load_test_cases_by_domain,
    load_test_cases_by_category,
    group_test_cases_by_domain,
    get_test_case_by_id,
    get_test_summary,
    print_test_summary,
)
from src.optimizer.repeatability import (
    RepeatabilityTester,
    RepeatabilityResult,
    RepeatabilityReport,
    VarianceType,
    VarianceCause,
    SQLVariant,
    compare_sql_semantics,
)

__all__ = [
    # Client
    "GenieClient",
    "create_client_for_domain",
    # Models
    "GenieResponse",
    "TestCase",
    "TestResult",
    "ValidationResult",
    "ControlLever",
    "Fix",
    "OptimizerState",
    "ResponseStatus",
    "TestVerdict",
    # Config
    "OptimizerConfig",
    "load_config",
    "GENIE_SPACES",
    "get_space_id",
    "get_space_info",
    "list_domains",
    "print_spaces_summary",
    # Test Loader
    "load_test_cases",
    "load_test_cases_by_domain",
    "load_test_cases_by_category",
    "group_test_cases_by_domain",
    "get_test_case_by_id",
    "get_test_summary",
    "print_test_summary",
    # Repeatability Testing
    "RepeatabilityTester",
    "RepeatabilityResult",
    "RepeatabilityReport",
    "VarianceType",
    "VarianceCause",
    "SQLVariant",
    "compare_sql_semantics",
]

__version__ = "1.1.0"
