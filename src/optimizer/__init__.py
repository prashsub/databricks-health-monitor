"""
TRAINING MATERIAL: Genie Space Optimizer Toolkit
=================================================

An LLM-driven interactive optimization toolkit for improving Genie Space
accuracy and repeatability. This is a unique tool that enables AI-assisted
optimization of AI systems (Genie Spaces).

WHAT IS GENIE SPACE OPTIMIZATION:
---------------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  THE CHALLENGE: Making Genie Accurate and Consistent                     │
│                                                                         │
│  Genie Space takes natural language → generates SQL                     │
│  But accuracy depends on many factors:                                  │
│  - Unity Catalog metadata (table/column comments)                       │
│  - Genie Space instructions                                             │
│  - Sample queries                                                       │
│  - TVF design                                                           │
│  - Metric View structure                                                │
│                                                                         │
│  OPTIMIZATION GOAL: Tune these "control levers" for:                    │
│  - Accuracy: Correct SQL for questions                                  │
│  - Repeatability: Same SQL every time                                   │
│  - Coverage: Handle wide range of questions                             │
└─────────────────────────────────────────────────────────────────────────┘

CONTROL LEVERS (Priority Order):
--------------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  1. UC METADATA         (Most effective, scales to all queries)         │
│     Table/column comments guide Genie's understanding                   │
│                                                                         │
│  2. METRIC VIEWS        (Semantic layer for common aggregations)        │
│     Pre-defined measures that Genie can use                             │
│                                                                         │
│  3. TVFs                (Parameterized queries for complex logic)       │
│     Functions that handle tricky calculations                           │
│                                                                         │
│  4. SAMPLE QUERIES      (Few-shot learning for Genie)                   │
│     Example Q&A pairs that show correct patterns                        │
│                                                                         │
│  5. GENIE INSTRUCTIONS  (Explicit routing rules)                        │
│     "For cost questions, prefer get_daily_cost_summary TVF"             │
│     ⚠️ Limited to ~4000 chars, use sparingly!                            │
└─────────────────────────────────────────────────────────────────────────┘

OPTIMIZATION WORKFLOW:
----------------------

1. LOAD TEST CASES
   test_cases = load_test_cases_by_domain("cost")
   
2. RUN TESTS
   client = GenieClient(space_id="...")
   response = client.ask_question(test_case.question)
   
3. ANALYZE RESULTS
   - Compare generated SQL to expected
   - Identify variance patterns
   - Determine root cause

4. APPLY FIXES
   - Update UC metadata
   - Add Genie instructions
   - Add sample queries

5. RETEST
   - Verify fix worked
   - Check for regressions

6. TEST REPEATABILITY
   tester = RepeatabilityTester(space_id="...")
   report = tester.test_repeatability(test_cases)

MODULE STRUCTURE:
-----------------
- genie_client.py: API client for Genie Space interactions
- repeatability.py: Repeatability testing and analysis
- test_loader.py: Load test cases from JSON/exports
- models.py: Data classes for responses, tests, fixes
- config.py: Configuration and Genie Space registry

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
