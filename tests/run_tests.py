#!/usr/bin/env python3
"""
Test Runner Script
==================

Provides programmatic access to test execution with various configurations.

Usage:
    # Run unit tests
    python tests/run_tests.py --unit

    # Run integration tests
    python tests/run_tests.py --integration

    # Run with coverage
    python tests/run_tests.py --coverage

    # Run specific module
    python tests/run_tests.py --module alerting

    # Run in parallel
    python tests/run_tests.py --parallel

    # Generate JUnit XML for CI
    python tests/run_tests.py --junit

Examples:
    # Quick unit tests
    python tests/run_tests.py --unit -q

    # Full test suite with coverage
    python tests/run_tests.py --coverage --fail-under 70

    # ML tests only
    python tests/run_tests.py --ml -v

    # Debug mode (stop on first failure)
    python tests/run_tests.py --debug
"""

import argparse
import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional


# Ensure we're in the right directory
TEST_DIR = Path(__file__).parent
PROJECT_DIR = TEST_DIR.parent
SRC_DIR = PROJECT_DIR / "src"


def build_pytest_command(args: argparse.Namespace) -> List[str]:
    """Build pytest command from arguments."""
    cmd = ["pytest"]

    # Add markers
    markers = []
    if args.unit:
        markers.append("unit")
    if args.integration:
        markers.append("integration")
    if args.ml:
        markers.append("ml")
    if args.slow:
        markers.append("slow")

    if markers:
        cmd.extend(["-m", " and ".join(markers)])
    elif not args.all:
        # Default: exclude slow tests
        cmd.extend(["-m", "not slow"])

    # Add specific module
    if args.module:
        module_path = TEST_DIR / args.module
        if module_path.exists():
            cmd.append(str(module_path))
        else:
            print(f"Warning: Module path not found: {module_path}")
            # Try as a test file pattern
            cmd.extend(["-k", args.module])

    # Add coverage
    if args.coverage:
        cmd.extend([
            f"--cov={SRC_DIR}",
            "--cov-report=html",
            "--cov-report=term-missing",
        ])
        if args.fail_under:
            cmd.append(f"--cov-fail-under={args.fail_under}")

    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    elif args.quiet:
        cmd.append("-q")
    else:
        cmd.append("-v")

    # Short traceback unless verbose
    if not args.verbose:
        cmd.append("--tb=short")

    # Parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.workers) if args.workers else "auto"])

    # JUnit output for CI
    if args.junit:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cmd.extend(["--junitxml", f"test-results-{timestamp}.xml"])

    # Debug mode
    if args.debug:
        cmd.extend(["-x", "--pdb"])

    # Rerun failures
    if args.rerun:
        cmd.append("--lf")

    # Show durations
    if args.durations:
        cmd.extend(["--durations", str(args.durations)])

    # Match pattern
    if args.match:
        cmd.extend(["-k", args.match])

    # Extra pytest args
    if args.pytest_args:
        cmd.extend(args.pytest_args)

    return cmd


def run_tests(args: argparse.Namespace) -> int:
    """Run tests with specified configuration."""
    cmd = build_pytest_command(args)

    # Print command if dry run
    if args.dry_run:
        print("Would run:")
        print(" ".join(cmd))
        return 0

    # Change to project directory
    os.chdir(PROJECT_DIR)

    # Print command
    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)

    # Execute
    result = subprocess.run(cmd)

    # Print coverage location if generated
    if args.coverage and result.returncode == 0:
        print("-" * 60)
        print(f"Coverage report: {TEST_DIR / 'htmlcov' / 'index.html'}")

    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Run Databricks Health Monitor tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Test type selection
    type_group = parser.add_argument_group("Test Selection")
    type_group.add_argument(
        "--unit", action="store_true",
        help="Run unit tests only (no Spark required)"
    )
    type_group.add_argument(
        "--integration", action="store_true",
        help="Run integration tests (requires Spark)"
    )
    type_group.add_argument(
        "--ml", action="store_true",
        help="Run ML model tests"
    )
    type_group.add_argument(
        "--slow", action="store_true",
        help="Include slow tests"
    )
    type_group.add_argument(
        "--all", action="store_true",
        help="Run ALL tests"
    )
    type_group.add_argument(
        "--module", "-m",
        help="Run tests for specific module (e.g., 'alerting', 'ml')"
    )
    type_group.add_argument(
        "--match", "-k",
        help="Run tests matching pattern"
    )

    # Coverage options
    cov_group = parser.add_argument_group("Coverage")
    cov_group.add_argument(
        "--coverage", "-c", action="store_true",
        help="Run with coverage report"
    )
    cov_group.add_argument(
        "--fail-under", type=int, default=70,
        help="Coverage threshold (default: 70)"
    )

    # Output options
    out_group = parser.add_argument_group("Output")
    out_group.add_argument(
        "--verbose", "-v", action="store_true",
        help="Verbose output"
    )
    out_group.add_argument(
        "--quiet", "-q", action="store_true",
        help="Quiet output"
    )
    out_group.add_argument(
        "--junit", action="store_true",
        help="Generate JUnit XML report"
    )
    out_group.add_argument(
        "--durations", type=int,
        help="Show N slowest tests"
    )

    # Execution options
    exec_group = parser.add_argument_group("Execution")
    exec_group.add_argument(
        "--parallel", "-p", action="store_true",
        help="Run tests in parallel"
    )
    exec_group.add_argument(
        "--workers", "-w", type=int,
        help="Number of parallel workers (default: auto)"
    )
    exec_group.add_argument(
        "--debug", action="store_true",
        help="Debug mode (stop on first failure, enter debugger)"
    )
    exec_group.add_argument(
        "--rerun", action="store_true",
        help="Run only last failed tests"
    )
    exec_group.add_argument(
        "--dry-run", action="store_true",
        help="Print command without executing"
    )

    # Extra arguments
    parser.add_argument(
        "pytest_args", nargs="*",
        help="Additional arguments to pass to pytest"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.verbose and args.quiet:
        parser.error("Cannot use both --verbose and --quiet")

    sys.exit(run_tests(args))


if __name__ == "__main__":
    main()
