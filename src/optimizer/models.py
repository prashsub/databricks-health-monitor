"""
Data models for the Genie Space Optimizer.

These models provide structured representations of:
- Genie API responses
- Test cases and results
- Applied fixes and control levers
- Optimizer state for checkpointing
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ResponseStatus(str, Enum):
    """Status values for Genie API responses."""
    IN_PROGRESS = "IN_PROGRESS"
    EXECUTING_QUERY = "EXECUTING_QUERY"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TestVerdict(str, Enum):
    """Verdict for a test case evaluation."""
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class ControlLever(str, Enum):
    """
    Control levers for optimizing Genie Spaces (in order of preference).
    
    Priority:
    1. UC Tables & Columns Metadata - Most durable, preferred
    2. UC Metric Views Metadata - For metric-related issues
    3. UC Functions (TVFs) - For calculation issues
    4. Lakehouse Monitoring Tables - For time-series queries
    5. ML Model Inference Tables - For prediction queries
    6. Genie Space Instructions - Last resort (~4000 char limit)
    """
    UC_TABLE_METADATA = "uc_table_metadata"
    UC_COLUMN_METADATA = "uc_column_metadata"
    UC_METRIC_VIEW = "uc_metric_view"
    UC_FUNCTION = "uc_function"
    LAKEHOUSE_MONITORING = "lakehouse_monitoring"
    ML_INFERENCE_TABLE = "ml_inference_table"
    GENIE_INSTRUCTION = "genie_instruction"
    GENIE_SAMPLE_QUERY = "genie_sample_query"


@dataclass
class GenieResponse:
    """
    Represents a response from the Genie API.
    
    Attributes:
        status: Response status (COMPLETED, FAILED, etc.)
        sql: Generated SQL query (if any)
        result_data: Query results as list of dicts
        result_columns: Column names from results
        error: Error message if failed
        conversation_id: Genie conversation ID
        message_id: Genie message ID
        attachments: List of attachment IDs
        raw_response: Full raw API response for debugging
    """
    status: ResponseStatus
    sql: Optional[str] = None
    result_data: Optional[list[dict[str, Any]]] = None
    result_columns: Optional[list[str]] = None
    error: Optional[str] = None
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    attachments: Optional[list[str]] = None
    raw_response: Optional[dict] = None
    
    @property
    def is_success(self) -> bool:
        """Check if response completed successfully."""
        return self.status == ResponseStatus.COMPLETED and self.error is None
    
    @property
    def row_count(self) -> int:
        """Get number of result rows."""
        return len(self.result_data) if self.result_data else 0


@dataclass
class ValidationAssertion:
    """
    A single validation assertion for test cases.
    
    Types:
    - not_empty: Results should not be empty
    - column_exists: Specific columns should exist
    - table_used: Specific tables should be in SQL
    - value_check: Specific values should be in results
    """
    type: str
    columns: Optional[list[str]] = None
    tables: Optional[list[str]] = None
    expected_value: Optional[Any] = None
    column_name: Optional[str] = None


@dataclass
class TestCase:
    """
    A test case for validating Genie Space accuracy.
    
    Attributes:
        id: Unique test case identifier
        category: Category (simple_aggregation, join_query, etc.)
        domain: Domain (cost, reliability, etc.)
        question: Natural language question to ask Genie
        validation: Validation criteria (hints for LLM evaluation)
        critical: Whether this is a critical test case
        expected_sql: Optional expected SQL for reference
        notes: Additional notes for the evaluator
    """
    id: str
    category: str
    domain: str
    question: str
    validation: dict[str, Any] = field(default_factory=dict)
    critical: bool = False
    expected_sql: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class TestResult:
    """
    Result of running a test case.
    
    Attributes:
        test_case: The test case that was run
        response: Genie API response
        verdict: PASS/FAIL/NEEDS_REVIEW
        analysis: LLM's analysis of why it passed/failed
        suggested_fix: Suggested fix if failed
        timestamp: When the test was run
    """
    test_case: TestCase
    response: GenieResponse
    verdict: TestVerdict
    analysis: str
    suggested_fix: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationResult:
    """
    Detailed validation result with breakdown.
    
    Attributes:
        passed: Whether validation passed
        assertions_passed: Number of assertions that passed
        assertions_failed: Number of assertions that failed
        details: Detailed breakdown of each assertion
    """
    passed: bool
    assertions_passed: int
    assertions_failed: int
    details: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Fix:
    """
    A fix applied to improve Genie accuracy.
    
    Attributes:
        id: Unique fix identifier
        control_lever: Which control lever was used
        test_case_id: Which test case this fixes
        description: What the fix does
        before: Previous value/state
        after: New value/state
        sql: SQL command used (if applicable)
        verified: Whether the fix was verified to work
        timestamp: When the fix was applied
    """
    id: str
    control_lever: ControlLever
    test_case_id: str
    description: str
    before: Optional[str] = None
    after: Optional[str] = None
    sql: Optional[str] = None
    verified: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OptimizerState:
    """
    Current state of the optimizer for checkpointing.
    
    Attributes:
        space_id: Genie Space being optimized
        space_name: Human-readable space name
        total_tests: Total number of test cases
        tests_run: Number of tests run so far
        tests_passed: Number of tests passed
        tests_failed: Number of tests failed
        tests_needs_review: Number of tests needing review
        current_accuracy: Current accuracy percentage
        target_accuracy: Target accuracy (default 95%)
        fixes_applied: List of fixes applied
        test_results: Results for each test
        last_checkpoint: Last checkpoint timestamp
        session_start: When optimization session started
    """
    space_id: str
    space_name: str
    total_tests: int = 0
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_needs_review: int = 0
    current_accuracy: float = 0.0
    target_accuracy: float = 95.0
    fixes_applied: list[Fix] = field(default_factory=list)
    test_results: list[TestResult] = field(default_factory=list)
    last_checkpoint: datetime = field(default_factory=datetime.now)
    session_start: datetime = field(default_factory=datetime.now)
    
    @property
    def accuracy(self) -> float:
        """Calculate current accuracy percentage."""
        if self.tests_run == 0:
            return 0.0
        return (self.tests_passed / self.tests_run) * 100
    
    @property
    def is_target_met(self) -> bool:
        """Check if target accuracy is met."""
        return self.accuracy >= self.target_accuracy
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "space_id": self.space_id,
            "space_name": self.space_name,
            "total_tests": self.total_tests,
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "tests_needs_review": self.tests_needs_review,
            "current_accuracy": self.accuracy,
            "target_accuracy": self.target_accuracy,
            "fixes_applied_count": len(self.fixes_applied),
            "last_checkpoint": self.last_checkpoint.isoformat(),
            "session_start": self.session_start.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "OptimizerState":
        """Create from dictionary."""
        return cls(
            space_id=data["space_id"],
            space_name=data["space_name"],
            total_tests=data.get("total_tests", 0),
            tests_run=data.get("tests_run", 0),
            tests_passed=data.get("tests_passed", 0),
            tests_failed=data.get("tests_failed", 0),
            tests_needs_review=data.get("tests_needs_review", 0),
            target_accuracy=data.get("target_accuracy", 95.0),
            last_checkpoint=datetime.fromisoformat(data.get("last_checkpoint", datetime.now().isoformat())),
            session_start=datetime.fromisoformat(data.get("session_start", datetime.now().isoformat())),
        )
