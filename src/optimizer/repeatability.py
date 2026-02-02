"""
Repeatability Testing Module for Genie Space Optimizer.

This module tests Genie Space consistency by:
1. Running the same questions multiple times
2. Comparing SQL outputs for consistency
3. Analyzing variance patterns
4. Providing optimization recommendations to improve repeatability

Usage:
    from src.optimizer.repeatability import RepeatabilityTester
    
    tester = RepeatabilityTester(space_id="...")
    results = tester.test_repeatability(questions, num_iterations=3)
    tester.generate_report(results)
"""

import hashlib
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from enum import Enum
from typing import Any, Optional

from src.optimizer.genie_client import GenieClient
from src.optimizer.models import GenieResponse, TestCase


class VarianceType(str, Enum):
    """Types of SQL variance detected."""
    IDENTICAL = "identical"  # SQL is exactly the same
    SEMANTICALLY_EQUIVALENT = "semantically_equivalent"  # Different SQL, same results
    MINOR_VARIANCE = "minor_variance"  # Small differences (ordering, aliases)
    SIGNIFICANT_VARIANCE = "significant_variance"  # Different tables/joins/logic
    COMPLETE_DIVERGENCE = "complete_divergence"  # Completely different approaches


class VarianceCause(str, Enum):
    """Root causes of SQL variance."""
    AMBIGUOUS_QUESTION = "ambiguous_question"  # Question can be interpreted multiple ways
    AMBIGUOUS_METADATA = "ambiguous_metadata"  # Table/column descriptions are unclear
    MISSING_INSTRUCTION = "missing_instruction"  # Needs explicit instruction
    COMPETING_ASSETS = "competing_assets"  # Multiple valid tables/TVFs
    LLM_NONDETERMINISM = "llm_nondeterminism"  # Random LLM variation
    UNKNOWN = "unknown"


@dataclass
class SQLVariant:
    """Represents a unique SQL variant observed for a question."""
    sql: str
    sql_hash: str
    occurrence_count: int = 1
    first_seen: datetime = field(default_factory=datetime.now)
    responses: list[GenieResponse] = field(default_factory=list)
    
    @property
    def normalized_sql(self) -> str:
        """Normalize SQL for comparison (lowercase, remove extra whitespace)."""
        if not self.sql:
            return ""
        return " ".join(self.sql.lower().split())


@dataclass 
class RepeatabilityResult:
    """Result of repeatability testing for a single question."""
    test_case: TestCase
    question: str
    num_iterations: int
    variants: list[SQLVariant]
    variance_type: VarianceType
    variance_cause: Optional[VarianceCause] = None
    repeatability_score: float = 0.0  # 0-100%
    analysis: str = ""
    recommended_fixes: list[str] = field(default_factory=list)
    
    @property
    def is_repeatable(self) -> bool:
        """Check if results are acceptably repeatable (90%+ same SQL)."""
        return self.repeatability_score >= 90.0
    
    @property
    def unique_variant_count(self) -> int:
        """Number of unique SQL variants observed."""
        return len(self.variants)
    
    @property
    def dominant_variant(self) -> Optional[SQLVariant]:
        """Get the most common SQL variant."""
        if not self.variants:
            return None
        return max(self.variants, key=lambda v: v.occurrence_count)


@dataclass
class RepeatabilityReport:
    """Overall repeatability report for a Genie Space."""
    space_id: str
    space_name: str
    test_date: datetime = field(default_factory=datetime.now)
    total_questions: int = 0
    repeatable_count: int = 0
    variable_count: int = 0
    overall_repeatability: float = 0.0
    results: list[RepeatabilityResult] = field(default_factory=list)
    fixes_applied: list[str] = field(default_factory=list)
    
    @property
    def repeatability_rate(self) -> float:
        """Calculate overall repeatability rate."""
        if self.total_questions == 0:
            return 0.0
        return (self.repeatable_count / self.total_questions) * 100
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "space_id": self.space_id,
            "space_name": self.space_name,
            "test_date": self.test_date.isoformat(),
            "total_questions": self.total_questions,
            "repeatable_count": self.repeatable_count,
            "variable_count": self.variable_count,
            "overall_repeatability": self.overall_repeatability,
            "results": [
                {
                    "question": r.question,
                    "repeatability_score": r.repeatability_score,
                    "variance_type": r.variance_type.value,
                    "variance_cause": r.variance_cause.value if r.variance_cause else None,
                    "unique_variants": r.unique_variant_count,
                    "recommended_fixes": r.recommended_fixes,
                }
                for r in self.results
            ],
        }


class RepeatabilityTester:
    """
    Tests Genie Space repeatability by running same questions multiple times.
    
    Workflow:
    1. Run each test question N times
    2. Collect and hash SQL outputs
    3. Compare variants and calculate repeatability score
    4. Analyze variance causes
    5. Generate recommendations for improvement
    """
    
    def __init__(
        self,
        space_id: str,
        client: Optional[GenieClient] = None,
    ):
        """
        Initialize the repeatability tester.
        
        Args:
            space_id: Genie Space ID to test
            client: Optional pre-configured GenieClient
        """
        self.space_id = space_id
        self.client = client or GenieClient(space_id=space_id)
    
    def _hash_sql(self, sql: Optional[str]) -> str:
        """Create a hash of normalized SQL for comparison."""
        if not sql:
            return "NO_SQL"
        normalized = " ".join(sql.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def _calculate_sql_similarity(self, sql1: Optional[str], sql2: Optional[str]) -> float:
        """Calculate similarity ratio between two SQL strings."""
        if not sql1 or not sql2:
            return 0.0 if (sql1 or sql2) else 1.0
        
        norm1 = " ".join(sql1.lower().split())
        norm2 = " ".join(sql2.lower().split())
        
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def _classify_variance(
        self,
        variants: list[SQLVariant],
        num_iterations: int,
    ) -> VarianceType:
        """Classify the type of variance observed."""
        if len(variants) == 1:
            return VarianceType.IDENTICAL
        
        # Check if dominant variant is >90%
        dominant = max(variants, key=lambda v: v.occurrence_count)
        if dominant.occurrence_count / num_iterations >= 0.9:
            return VarianceType.MINOR_VARIANCE
        
        # Compare SQL similarity between variants
        sqls = [v.sql for v in variants if v.sql]
        if len(sqls) < 2:
            return VarianceType.COMPLETE_DIVERGENCE
        
        similarities = []
        for i, sql1 in enumerate(sqls):
            for sql2 in sqls[i+1:]:
                similarities.append(self._calculate_sql_similarity(sql1, sql2))
        
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0
        
        if avg_similarity >= 0.8:
            return VarianceType.SEMANTICALLY_EQUIVALENT
        elif avg_similarity >= 0.5:
            return VarianceType.SIGNIFICANT_VARIANCE
        else:
            return VarianceType.COMPLETE_DIVERGENCE
    
    def _analyze_variance_cause(
        self,
        question: str,
        variants: list[SQLVariant],
        variance_type: VarianceType,
    ) -> tuple[VarianceCause, str]:
        """
        Analyze the root cause of variance.
        
        Returns:
            Tuple of (cause, analysis string)
        """
        if variance_type == VarianceType.IDENTICAL:
            return (VarianceCause.LLM_NONDETERMINISM, "No variance - results are perfectly consistent.")
        
        # Analyze SQL patterns
        sqls = [v.sql for v in variants if v.sql]
        if not sqls:
            return (VarianceCause.UNKNOWN, "No SQL generated in any variant.")
        
        analysis_parts = []
        
        # Check for different tables
        tables_used = []
        for sql in sqls:
            tables = self._extract_tables(sql)
            tables_used.append(set(tables))
        
        if len(set(frozenset(t) for t in tables_used)) > 1:
            analysis_parts.append("Different tables used across variants - may indicate ambiguous metadata or competing assets.")
            cause = VarianceCause.COMPETING_ASSETS
        
        # Check for different aggregations
        agg_patterns = []
        for sql in sqls:
            aggs = self._extract_aggregations(sql)
            agg_patterns.append(tuple(aggs))
        
        if len(set(agg_patterns)) > 1:
            analysis_parts.append("Different aggregation functions used - question may be ambiguous.")
            cause = VarianceCause.AMBIGUOUS_QUESTION
        
        # Check for different joins
        join_patterns = []
        for sql in sqls:
            if "join" in sql.lower():
                join_patterns.append("has_join")
            else:
                join_patterns.append("no_join")
        
        if len(set(join_patterns)) > 1:
            analysis_parts.append("Inconsistent join usage - may need explicit instruction.")
            cause = VarianceCause.MISSING_INSTRUCTION
        
        if not analysis_parts:
            analysis_parts.append("Minor variations in SQL structure - likely LLM non-determinism.")
            cause = VarianceCause.LLM_NONDETERMINISM
        
        return (cause, " ".join(analysis_parts))
    
    def _extract_tables(self, sql: str) -> list[str]:
        """Extract table names from SQL."""
        if not sql:
            return []
        
        import re
        # Match FROM/JOIN followed by table name
        pattern = r'(?:from|join)\s+[`"]?(\w+(?:\.\w+)*)[`"]?'
        matches = re.findall(pattern, sql.lower())
        return list(set(matches))
    
    def _extract_aggregations(self, sql: str) -> list[str]:
        """Extract aggregation functions from SQL."""
        if not sql:
            return []
        
        import re
        # Match aggregation functions
        pattern = r'\b(sum|count|avg|min|max|measure)\s*\('
        matches = re.findall(pattern, sql.lower())
        return sorted(set(matches))
    
    def _generate_recommendations(
        self,
        question: str,
        variants: list[SQLVariant],
        variance_cause: VarianceCause,
    ) -> list[str]:
        """Generate fix recommendations based on variance analysis."""
        recommendations = []
        
        if variance_cause == VarianceCause.AMBIGUOUS_QUESTION:
            recommendations.append(
                f"Consider adding a sample query for: '{question}' to establish the expected pattern."
            )
        
        if variance_cause == VarianceCause.AMBIGUOUS_METADATA:
            tables = []
            for v in variants:
                tables.extend(self._extract_tables(v.sql or ""))
            unique_tables = list(set(tables))
            recommendations.append(
                f"Update table/column comments to clarify which table should be used. "
                f"Tables observed: {', '.join(unique_tables)}"
            )
        
        if variance_cause == VarianceCause.COMPETING_ASSETS:
            # Find the dominant SQL pattern
            dominant = max(variants, key=lambda v: v.occurrence_count)
            dominant_tables = self._extract_tables(dominant.sql or "")
            recommendations.append(
                f"Add instruction to prefer: {', '.join(dominant_tables)} for this type of query."
            )
        
        if variance_cause == VarianceCause.MISSING_INSTRUCTION:
            dominant = max(variants, key=lambda v: v.occurrence_count)
            recommendations.append(
                f"Add explicit instruction with the preferred SQL pattern: {dominant.sql[:200]}..."
            )
        
        if variance_cause == VarianceCause.LLM_NONDETERMINISM:
            recommendations.append(
                "Minor LLM variation is expected. Consider adding a sample query "
                "if consistency is critical for this question."
            )
        
        return recommendations
    
    def test_single_question(
        self,
        test_case: TestCase,
        num_iterations: int = 3,
        verbose: bool = True,
    ) -> RepeatabilityResult:
        """
        Test repeatability for a single question.
        
        Args:
            test_case: TestCase to test
            num_iterations: Number of times to run the question
            verbose: Whether to print progress
            
        Returns:
            RepeatabilityResult with analysis
        """
        if verbose:
            print(f"\n🔄 Testing repeatability: \"{test_case.question[:50]}...\"")
            print(f"   Running {num_iterations} iterations...")
        
        # Track variants by SQL hash
        variants_by_hash: dict[str, SQLVariant] = {}
        
        for i in range(num_iterations):
            if verbose:
                print(f"   Iteration {i+1}/{num_iterations}...", end=" ")
            
            # Ask question
            response = self.client.ask_question(
                test_case.question,
                verbose=False,
            )
            
            # Hash and track SQL
            sql = response.sql
            sql_hash = self._hash_sql(sql)
            
            if sql_hash in variants_by_hash:
                variants_by_hash[sql_hash].occurrence_count += 1
                variants_by_hash[sql_hash].responses.append(response)
            else:
                variants_by_hash[sql_hash] = SQLVariant(
                    sql=sql,
                    sql_hash=sql_hash,
                    occurrence_count=1,
                    responses=[response],
                )
            
            if verbose:
                status = "✅" if response.is_success else "❌"
                print(f"{status} (hash: {sql_hash})")
            
            # Rate limiting (already handled by client, but extra safety)
            time.sleep(1)
        
        # Analyze results
        variants = list(variants_by_hash.values())
        
        # Calculate repeatability score
        if variants:
            dominant = max(variants, key=lambda v: v.occurrence_count)
            repeatability_score = (dominant.occurrence_count / num_iterations) * 100
        else:
            repeatability_score = 0.0
        
        # Classify variance
        variance_type = self._classify_variance(variants, num_iterations)
        
        # Analyze cause
        variance_cause, analysis = self._analyze_variance_cause(
            test_case.question,
            variants,
            variance_type,
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            test_case.question,
            variants,
            variance_cause,
        )
        
        if verbose:
            print(f"   📊 Repeatability: {repeatability_score:.1f}%")
            print(f"   📈 Unique variants: {len(variants)}")
            print(f"   🔍 Variance type: {variance_type.value}")
        
        return RepeatabilityResult(
            test_case=test_case,
            question=test_case.question,
            num_iterations=num_iterations,
            variants=variants,
            variance_type=variance_type,
            variance_cause=variance_cause,
            repeatability_score=repeatability_score,
            analysis=analysis,
            recommended_fixes=recommendations,
        )
    
    def test_repeatability(
        self,
        test_cases: list[TestCase],
        num_iterations: int = 3,
        verbose: bool = True,
    ) -> RepeatabilityReport:
        """
        Test repeatability for multiple questions.
        
        Args:
            test_cases: List of test cases to test
            num_iterations: Number of times to run each question
            verbose: Whether to print progress
            
        Returns:
            RepeatabilityReport with all results
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"🔄 REPEATABILITY TEST")
            print(f"   Space ID: {self.space_id}")
            print(f"   Questions: {len(test_cases)}")
            print(f"   Iterations per question: {num_iterations}")
            print(f"   Total API calls: {len(test_cases) * num_iterations}")
            print(f"{'='*60}")
        
        results = []
        repeatable_count = 0
        total_repeatability = 0.0
        
        for i, test_case in enumerate(test_cases):
            if verbose:
                print(f"\n[{i+1}/{len(test_cases)}]")
            
            result = self.test_single_question(
                test_case,
                num_iterations=num_iterations,
                verbose=verbose,
            )
            results.append(result)
            
            if result.is_repeatable:
                repeatable_count += 1
            
            total_repeatability += result.repeatability_score
        
        # Calculate overall metrics
        overall_repeatability = (
            total_repeatability / len(test_cases)
            if test_cases else 0.0
        )
        
        report = RepeatabilityReport(
            space_id=self.space_id,
            space_name=f"space_{self.space_id[:8]}",  # Will be updated
            total_questions=len(test_cases),
            repeatable_count=repeatable_count,
            variable_count=len(test_cases) - repeatable_count,
            overall_repeatability=overall_repeatability,
            results=results,
        )
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"📊 REPEATABILITY SUMMARY")
            print(f"{'='*60}")
            print(f"   Overall repeatability: {overall_repeatability:.1f}%")
            print(f"   Repeatable questions: {repeatable_count}/{len(test_cases)}")
            print(f"   Variable questions: {len(test_cases) - repeatable_count}")
            print(f"{'='*60}")
        
        return report
    
    def generate_markdown_report(
        self,
        report: RepeatabilityReport,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generate a detailed markdown report.
        
        Args:
            report: RepeatabilityReport to document
            output_path: Optional path to save the report
            
        Returns:
            Markdown string
        """
        md = f"""# Genie Space Repeatability Report

**Space ID:** {report.space_id}  
**Test Date:** {report.test_date.strftime('%Y-%m-%d %H:%M:%S')}  
**Total Questions Tested:** {report.total_questions}  
**Iterations per Question:** {report.results[0].num_iterations if report.results else 0}  

---

## Executive Summary

| Metric | Value |
|---|---|
| **Overall Repeatability** | {report.overall_repeatability:.1f}% |
| **Repeatable Questions** | {report.repeatable_count}/{report.total_questions} |
| **Variable Questions** | {report.variable_count} |
| **Target** | 90%+ |

### Repeatability Status

"""
        
        if report.overall_repeatability >= 90:
            md += "✅ **GOOD** - Genie Space shows consistent behavior.\n\n"
        elif report.overall_repeatability >= 70:
            md += "⚠️ **NEEDS IMPROVEMENT** - Some questions show inconsistent responses.\n\n"
        else:
            md += "❌ **CRITICAL** - Significant repeatability issues detected.\n\n"
        
        md += """---

## Detailed Results

"""
        
        # Group by variance type
        by_variance = defaultdict(list)
        for result in report.results:
            by_variance[result.variance_type].append(result)
        
        # Variable questions first (most actionable)
        for variance_type in [
            VarianceType.COMPLETE_DIVERGENCE,
            VarianceType.SIGNIFICANT_VARIANCE,
            VarianceType.MINOR_VARIANCE,
            VarianceType.SEMANTICALLY_EQUIVALENT,
            VarianceType.IDENTICAL,
        ]:
            results_of_type = by_variance.get(variance_type, [])
            if not results_of_type:
                continue
            
            variance_emoji = {
                VarianceType.IDENTICAL: "✅",
                VarianceType.SEMANTICALLY_EQUIVALENT: "✅",
                VarianceType.MINOR_VARIANCE: "⚠️",
                VarianceType.SIGNIFICANT_VARIANCE: "❌",
                VarianceType.COMPLETE_DIVERGENCE: "🚨",
            }.get(variance_type, "❓")
            
            md += f"\n### {variance_emoji} {variance_type.value.replace('_', ' ').title()} ({len(results_of_type)} questions)\n\n"
            
            for result in results_of_type:
                md += f"""#### {result.test_case.id}: {result.question}

**Repeatability Score:** {result.repeatability_score:.1f}%  
**Unique Variants:** {result.unique_variant_count}  
**Variance Cause:** {result.variance_cause.value if result.variance_cause else 'N/A'}  

**Analysis:** {result.analysis}

"""
                
                # Show SQL variants
                if result.variants:
                    md += "**SQL Variants Observed:**\n\n"
                    for i, variant in enumerate(sorted(
                        result.variants,
                        key=lambda v: v.occurrence_count,
                        reverse=True,
                    )):
                        pct = (variant.occurrence_count / result.num_iterations) * 100
                        md += f"*Variant {i+1} ({variant.occurrence_count} occurrences, {pct:.0f}%):*\n"
                        if variant.sql:
                            sql_display = variant.sql[:500] + "..." if len(variant.sql) > 500 else variant.sql
                            md += f"```sql\n{sql_display}\n```\n\n"
                        else:
                            md += "*No SQL generated*\n\n"
                
                # Show recommendations
                if result.recommended_fixes:
                    md += "**Recommended Fixes:**\n"
                    for fix in result.recommended_fixes:
                        md += f"- {fix}\n"
                    md += "\n"
                
                md += "---\n\n"
        
        # Summary recommendations
        md += """## Summary of Recommended Fixes

"""
        
        all_recommendations = []
        for result in report.results:
            if not result.is_repeatable and result.recommended_fixes:
                for fix in result.recommended_fixes:
                    if fix not in all_recommendations:
                        all_recommendations.append(fix)
        
        if all_recommendations:
            for i, rec in enumerate(all_recommendations, 1):
                md += f"{i}. {rec}\n"
        else:
            md += "No critical fixes required - repeatability is acceptable.\n"
        
        md += f"""

---

*Generated by Databricks Health Monitor Genie Space Optimizer*
"""
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(md)
            print(f"📝 Report saved to: {output_path}")
        
        return md


def _extract_tables_from_sql(sql: str) -> list[str]:
    """Extract table names from SQL (standalone function)."""
    if not sql:
        return []
    import re
    pattern = r'(?:from|join)\s+[`"]?(\w+(?:\.\w+)*)[`"]?'
    matches = re.findall(pattern, sql.lower())
    return list(set(matches))


def _extract_aggregations_from_sql(sql: str) -> list[str]:
    """Extract aggregation functions from SQL (standalone function)."""
    if not sql:
        return []
    import re
    pattern = r'\b(sum|count|avg|min|max|measure)\s*\('
    matches = re.findall(pattern, sql.lower())
    return sorted(set(matches))


def compare_sql_semantics(sql1: str, sql2: str) -> dict:
    """
    Compare two SQL queries for semantic equivalence.
    
    Returns:
        Dictionary with comparison details
    """
    if not sql1 or not sql2:
        return {
            "equivalent": False,
            "similarity": 0.0,
            "same_tables": False,
            "same_aggregations": False,
            "details": "One or both queries are empty",
        }
    
    # Normalize
    norm1 = " ".join(sql1.lower().split())
    norm2 = " ".join(sql2.lower().split())
    
    # Calculate similarity
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    
    # Extract components using standalone functions
    tables1 = set(_extract_tables_from_sql(sql1))
    tables2 = set(_extract_tables_from_sql(sql2))
    aggs1 = set(_extract_aggregations_from_sql(sql1))
    aggs2 = set(_extract_aggregations_from_sql(sql2))
    
    same_tables = tables1 == tables2
    same_aggregations = aggs1 == aggs2
    
    # Determine equivalence
    equivalent = similarity >= 0.9 or (same_tables and same_aggregations and similarity >= 0.7)
    
    return {
        "equivalent": equivalent,
        "similarity": similarity,
        "same_tables": same_tables,
        "same_aggregations": same_aggregations,
        "tables_1": list(tables1),
        "tables_2": list(tables2),
        "aggregations_1": list(aggs1),
        "aggregations_2": list(aggs2),
        "details": (
            "Queries are semantically equivalent" if equivalent
            else f"Differences detected: tables={not same_tables}, aggregations={not same_aggregations}"
        ),
    }
