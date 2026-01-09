#!/usr/bin/env python3
"""
Offline SQL Validation for Genie Space Benchmark Queries

Validates all SQL queries in Genie Space JSON exports against actual deployed assets
WITHOUT executing queries in Databricks (fast, no timeout issues).

Checks:
1. TVF names exist
2. Table names exist
3. Column names exist in referenced tables
4. ML table references are correct
5. Monitoring table references are correct
"""

import json
import glob
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, List, Tuple

# ============================================================================
# ASSET LOADERS
# ============================================================================

def load_tvfs() -> Set[str]:
    """Load TVF names from tvfs.md (TSV format)"""
    tvf_file = Path('docs/reference/actual_assets/tvfs.md')
    tvfs = set()
    
    if not tvf_file.exists():
        print(f"⚠️  Warning: {tvf_file} not found")
        return tvfs
    
    for line in tvf_file.read_text().split('\n')[1:]:  # Skip header
        parts = line.split('\t')
        if len(parts) >= 3:
            tvfs.add(parts[2])  # routine_name column
    
    return tvfs


def load_tables_with_columns() -> Dict[str, Set[str]]:
    """Load table names and their columns from TSV files"""
    files = [
        'docs/reference/actual_assets/tables.md',
        'docs/reference/actual_assets/ml.md',
        'docs/reference/actual_assets/mvs.md',
        'docs/reference/actual_assets/monitoring.md'
    ]
    
    table_columns = defaultdict(set)
    
    for file_path in files:
        path = Path(file_path)
        if not path.exists():
            print(f"⚠️  Warning: {path} not found")
            continue
        
        for line in path.read_text().split('\n')[1:]:  # Skip header
            parts = line.split('\t')
            if len(parts) >= 4:
                table_name = parts[2]  # table_name column
                column_name = parts[3]  # column_name column
                table_columns[table_name].add(column_name)
    
    return dict(table_columns)


# ============================================================================
# SQL PARSERS
# ============================================================================

def extract_tvf_calls(sql: str) -> List[str]:
    """Extract TVF function names from SQL"""
    # Pattern: get_function_name(
    pattern = r'\b(get_\w+)\s*\('
    matches = re.findall(pattern, sql, re.IGNORECASE)
    return list(set(matches))


def extract_table_references(sql: str) -> List[str]:
    """Extract table names from SQL (excluding inline catalog/schema and TVFs)"""
    # Remove catalog.schema prefixes first
    sql_simple = re.sub(r'[a-z_]+\.[a-z_]+\.([a-z_]+)', r'\1', sql, flags=re.IGNORECASE)
    
    # Pattern: FROM table_name or JOIN table_name
    # BUT exclude get_* functions (those are TVFs)
    patterns = [
        r'\bFROM\s+([a-z_][a-z0-9_]+)(?!\s*\()',  # Not followed by (
        r'\bJOIN\s+([a-z_][a-z0-9_]+)(?!\s*\()',  # Not followed by (
        r'\bINTO\s+([a-z_][a-z0-9_]+)',
    ]
    
    tables = []
    for pattern in patterns:
        matches = re.findall(pattern, sql_simple, re.IGNORECASE)
        # Filter out TVF calls (get_*)
        tables.extend([m for m in matches if not m.startswith('get_')])
    
    return list(set(tables))


def extract_column_references(sql: str) -> List[Tuple[str, str]]:
    """Extract column references with table context if available"""
    # Pattern: table.column or just column in SELECT/WHERE
    columns = []
    
    # Qualified columns: table.column
    qualified = re.findall(r'\b([a-z_][a-z0-9_]+)\.([a-z_][a-z0-9_]+)\b', sql, re.IGNORECASE)
    for table, col in qualified:
        if table.lower() not in ['cast', 'date', 'interval', 'current']:
            columns.append((table, col))
    
    return columns


# ============================================================================
# VALIDATORS
# ============================================================================

def validate_query(
    sql: str,
    tvfs: Set[str],
    table_columns: Dict[str, Set[str]],
    genie_space: str,
    question_num: int,
    question_text: str
) -> List[Dict]:
    """Validate a single SQL query and return list of errors"""
    errors = []
    
    # 1. Validate TVF calls
    tvf_calls = extract_tvf_calls(sql)
    for tvf in tvf_calls:
        if tvf not in tvfs:
            errors.append({
                'genie_space': genie_space,
                'question_num': question_num,
                'question': question_text,
                'error_type': 'TVF_NOT_FOUND',
                'tvf_name': tvf,
                'suggestion': find_similar_tvfs(tvf, tvfs)
            })
    
    # 2. Validate table references
    table_refs = extract_table_references(sql)
    for table in table_refs:
        if table not in table_columns:
            # Check if it's a CTE or subquery alias
            if not is_cte_or_alias(sql, table):
                errors.append({
                    'genie_space': genie_space,
                    'question_num': question_num,
                    'question': question_text,
                    'error_type': 'TABLE_NOT_FOUND',
                    'table_name': table,
                    'suggestion': find_similar_tables(table, table_columns.keys())
                })
    
    # 3. Validate column references
    column_refs = extract_column_references(sql)
    for table, column in column_refs:
        if table in table_columns:
            if column not in table_columns[table]:
                errors.append({
                    'genie_space': genie_space,
                    'question_num': question_num,
                    'question': question_text,
                    'error_type': 'COLUMN_NOT_FOUND',
                    'table_name': table,
                    'column_name': column,
                    'suggestion': find_similar_columns(column, table_columns[table])
                })
    
    return errors


def is_cte_or_alias(sql: str, name: str) -> bool:
    """Check if name is a CTE or table alias in the query"""
    # Check for WITH clause CTE
    cte_pattern = rf'\bWITH\s+{name}\s+AS\s*\('
    if re.search(cte_pattern, sql, re.IGNORECASE):
        return True
    
    # Check for table alias
    alias_pattern = rf'\bFROM\s+\w+\s+AS\s+{name}\b'
    if re.search(alias_pattern, sql, re.IGNORECASE):
        return True
    
    return False


def find_similar_tvfs(name: str, tvfs: Set[str]) -> str:
    """Find similar TVF names using fuzzy matching"""
    name_lower = name.lower()
    matches = []
    
    for tvf in tvfs:
        tvf_lower = tvf.lower()
        # Check if names share significant parts
        name_parts = set(name_lower.split('_'))
        tvf_parts = set(tvf_lower.split('_'))
        overlap = len(name_parts & tvf_parts)
        
        if overlap >= 2:
            matches.append((overlap, tvf))
    
    if matches:
        matches.sort(reverse=True)
        return f"Did you mean: {', '.join([m[1] for m in matches[:3]])}"
    return "No similar TVFs found"


def find_similar_tables(name: str, tables: Set[str]) -> str:
    """Find similar table names"""
    name_lower = name.lower()
    matches = []
    
    for table in tables:
        if name_lower in table.lower() or table.lower() in name_lower:
            matches.append(table)
    
    if matches:
        return f"Did you mean: {', '.join(matches[:3])}"
    return "No similar tables found"


def find_similar_columns(name: str, columns: Set[str]) -> str:
    """Find similar column names"""
    name_lower = name.lower()
    matches = []
    
    for col in columns:
        if name_lower in col.lower() or col.lower() in name_lower:
            matches.append(col)
    
    if matches:
        return f"Did you mean: {', '.join(matches[:3])}"
    return f"Available columns: {len(columns)} total"


# ============================================================================
# MAIN VALIDATION
# ============================================================================

def main():
    print("=" * 80)
    print("GENIE SPACE SQL VALIDATION (OFFLINE)")
    print("=" * 80)
    print()
    
    # Load assets
    print("📂 Loading actual assets...")
    tvfs = load_tvfs()
    table_columns = load_tables_with_columns()
    
    print(f"  ✅ Loaded {len(tvfs)} TVFs")
    print(f"  ✅ Loaded {len(table_columns)} tables/views")
    print()
    
    # Validate all Genie Space JSON files
    all_errors = []
    total_queries = 0
    
    for json_file in sorted(glob.glob('src/genie/*_genie_export.json')):
        genie_name = Path(json_file).stem.replace('_genie_export', '')
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        questions = data.get('benchmarks', {}).get('questions', [])
        
        for idx, q in enumerate(questions, 1):
            if 'answer' in q and q['answer']:
                content = q['answer'][0].get('content', [])
                sql = ''.join(content) if isinstance(content, list) else content
                
                question_text = q.get('question', [''])[0]
                total_queries += 1
                
                errors = validate_query(
                    sql, tvfs, table_columns,
                    genie_name, idx, question_text
                )
                
                all_errors.extend(errors)
    
    # Report results
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print()
    
    if not all_errors:
        print("✅ ALL QUERIES VALID!")
        print(f"   Total queries validated: {total_queries}")
        return
    
    print(f"❌ FOUND {len(all_errors)} ERRORS in {total_queries} queries")
    print()
    
    # Group by error type
    by_type = defaultdict(list)
    for err in all_errors:
        by_type[err['error_type']].append(err)
    
    print("📊 Error Breakdown by Type:")
    for error_type, errors in sorted(by_type.items()):
        print(f"  • {error_type}: {len(errors)} errors")
    print()
    
    # Group by Genie Space
    by_space = defaultdict(list)
    for err in all_errors:
        by_space[err['genie_space']].append(err)
    
    print("📊 Error Breakdown by Genie Space:")
    for space, errors in sorted(by_space.items()):
        print(f"  • {space}: {len(errors)} errors")
    print()
    
    # Show detailed errors
    print("=" * 80)
    print("DETAILED ERRORS")
    print("=" * 80)
    print()
    
    for error_type in sorted(by_type.keys()):
        errors = by_type[error_type]
        print(f"\n### {error_type} ({len(errors)} errors)\n")
        
        for err in errors[:20]:  # Show first 20 per type
            print(f"📁 {err['genie_space']} Q{err['question_num']}: {err['question'][:60]}...")
            
            if error_type == 'TVF_NOT_FOUND':
                print(f"   ❌ TVF: {err['tvf_name']}")
                print(f"   💡 {err['suggestion']}")
            
            elif error_type == 'TABLE_NOT_FOUND':
                print(f"   ❌ Table: {err['table_name']}")
                print(f"   💡 {err['suggestion']}")
            
            elif error_type == 'COLUMN_NOT_FOUND':
                print(f"   ❌ Column: {err['table_name']}.{err['column_name']}")
                print(f"   💡 {err['suggestion']}")
            
            print()
        
        if len(errors) > 20:
            print(f"   ... and {len(errors) - 20} more {error_type} errors\n")
    
    # Generate fix recommendations
    print("=" * 80)
    print("FIX RECOMMENDATIONS")
    print("=" * 80)
    print()
    
    if 'TVF_NOT_FOUND' in by_type:
        print(f"1. Fix {len(by_type['TVF_NOT_FOUND'])} TVF name errors")
        print(f"   Update function names in JSON files based on suggestions above")
        print()
    
    if 'TABLE_NOT_FOUND' in by_type:
        print(f"2. Fix {len(by_type['TABLE_NOT_FOUND'])} table name errors")
        print(f"   Update table references in JSON files")
        print()
    
    if 'COLUMN_NOT_FOUND' in by_type:
        print(f"3. Fix {len(by_type['COLUMN_NOT_FOUND'])} column name errors")
        print(f"   Update column names in SELECT/WHERE clauses")
        print()


if __name__ == '__main__':
    main()

