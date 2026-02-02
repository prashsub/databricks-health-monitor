"""
Test case loader for the Genie Space Optimizer.

Loads golden query test cases from YAML files and converts them
to TestCase objects for the optimizer to use.
"""

from pathlib import Path
from typing import Optional

import yaml

from src.optimizer.models import TestCase


def load_test_cases(
    yaml_path: Optional[Path] = None,
    domain: Optional[str] = None,
    critical_only: bool = False,
) -> list[TestCase]:
    """
    Load test cases from the golden queries YAML file.
    
    Args:
        yaml_path: Path to YAML file (default: tests/optimizer/genie_golden_queries.yml)
        domain: Filter by domain (cost, reliability, etc.)
        critical_only: Only load critical test cases
        
    Returns:
        List of TestCase objects
    """
    if yaml_path is None:
        yaml_path = Path("tests/optimizer/genie_golden_queries.yml")
    
    if not yaml_path.exists():
        raise FileNotFoundError(f"Test cases file not found: {yaml_path}")
    
    with open(yaml_path, "r") as f:
        # Load all documents from YAML (separated by ---)
        documents = list(yaml.safe_load_all(f))
    
    test_cases = []
    
    for doc in documents:
        if doc is None:
            continue
        
        # Process each test section
        for key, tests in doc.items():
            if key == "metadata":
                continue
            
            if not isinstance(tests, list):
                continue
            
            for test_data in tests:
                if not isinstance(test_data, dict):
                    continue
                
                test_case = TestCase(
                    id=test_data.get("id", "unknown"),
                    category=test_data.get("category", "unknown"),
                    domain=test_data.get("domain", "unknown"),
                    question=test_data.get("question", ""),
                    validation=test_data.get("validation", {}),
                    critical=test_data.get("critical", False),
                    expected_sql=test_data.get("expected_sql"),
                    notes=test_data.get("notes"),
                )
                
                # Apply filters
                if domain and test_case.domain != domain:
                    continue
                
                if critical_only and not test_case.critical:
                    continue
                
                test_cases.append(test_case)
    
    return test_cases


def load_test_cases_by_category(
    yaml_path: Optional[Path] = None,
) -> dict[str, list[TestCase]]:
    """
    Load test cases grouped by category.
    
    Returns:
        Dictionary mapping category to list of test cases
    """
    test_cases = load_test_cases(yaml_path)
    
    by_category: dict[str, list[TestCase]] = {}
    for tc in test_cases:
        if tc.category not in by_category:
            by_category[tc.category] = []
        by_category[tc.category].append(tc)
    
    return by_category


def load_test_cases_by_domain(
    domain: str,
    yaml_path: Optional[Path] = None,
) -> list[TestCase]:
    """
    Load test cases filtered by domain.
    
    Args:
        domain: Domain to filter by (cost, reliability, performance, security, quality, unified)
        yaml_path: Optional path to YAML file
    
    Returns:
        List of test cases for the specified domain
    """
    return load_test_cases(yaml_path, domain=domain)


def group_test_cases_by_domain(
    yaml_path: Optional[Path] = None,
) -> dict[str, list[TestCase]]:
    """
    Load test cases grouped by domain.
    
    Returns:
        Dictionary mapping domain to list of test cases
    """
    test_cases = load_test_cases(yaml_path)
    
    by_domain: dict[str, list[TestCase]] = {}
    for tc in test_cases:
        if tc.domain not in by_domain:
            by_domain[tc.domain] = []
        by_domain[tc.domain].append(tc)
    
    return by_domain


def get_test_case_by_id(
    test_id: str,
    yaml_path: Optional[Path] = None,
) -> Optional[TestCase]:
    """
    Get a specific test case by ID.
    
    Args:
        test_id: Test case ID (e.g., "cost_001")
        yaml_path: Path to YAML file
        
    Returns:
        TestCase if found, None otherwise
    """
    test_cases = load_test_cases(yaml_path)
    
    for tc in test_cases:
        if tc.id == test_id:
            return tc
    
    return None


def get_test_summary(yaml_path: Optional[Path] = None) -> dict:
    """
    Get a summary of all test cases.
    
    Returns:
        Dictionary with counts by domain, category, and critical flag
    """
    test_cases = load_test_cases(yaml_path)
    
    by_domain = group_test_cases_by_domain(yaml_path)
    by_category = load_test_cases_by_category(yaml_path)
    
    critical_count = len([tc for tc in test_cases if tc.critical])
    
    return {
        "total": len(test_cases),
        "critical": critical_count,
        "non_critical": len(test_cases) - critical_count,
        "by_domain": {domain: len(tests) for domain, tests in by_domain.items()},
        "by_category": {cat: len(tests) for cat, tests in by_category.items()},
    }


def print_test_summary(yaml_path: Optional[Path] = None):
    """Print a formatted summary of test cases."""
    summary = get_test_summary(yaml_path)
    
    print("\n" + "=" * 60)
    print("GENIE GOLDEN QUERIES - TEST CASE SUMMARY")
    print("=" * 60)
    
    print(f"\nTotal Test Cases: {summary['total']}")
    print(f"  - Critical: {summary['critical']}")
    print(f"  - Non-Critical: {summary['non_critical']}")
    
    print("\nBy Domain:")
    for domain, count in sorted(summary['by_domain'].items()):
        emoji = {
            "cost": "💰",
            "reliability": "🔄",
            "performance": "⚡",
            "security": "🔒",
            "quality": "✅",
            "unified": "🌐",
        }.get(domain, "📋")
        print(f"  {emoji} {domain}: {count}")
    
    print("\nBy Category:")
    for category, count in sorted(summary['by_category'].items()):
        print(f"  - {category}: {count}")
    
    print("=" * 60)
