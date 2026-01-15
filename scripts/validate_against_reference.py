#!/usr/bin/env python3
"""
Comprehensive validation of Genie Space JSON files against reference structure.
Compares with context/genie/genie_space_export.json to ensure exact format match.
"""

import json
import os
from typing import Dict, List, Any

def parse_serialized_space(serialized: str) -> dict:
    """Parse the serialized_space JSON string."""
    return json.loads(serialized)

def validate_structure(data: dict, path: str = "root") -> List[str]:
    """Validate the structure of a Genie Space JSON."""
    errors = []
    
    # Parse serialized_space if it's a string
    if isinstance(data.get("serialized_space"), str):
        try:
            space = parse_serialized_space(data["serialized_space"])
        except json.JSONDecodeError as e:
            errors.append(f"{path}.serialized_space: Invalid JSON - {e}")
            return errors
    else:
        space = data
    
    # 1. Check version
    if "version" not in space:
        errors.append(f"{path}: Missing 'version' field")
    elif not isinstance(space["version"], int):
        errors.append(f"{path}.version: Must be integer, got {type(space['version'])}")
    
    # 2. Validate config.sample_questions
    if "config" in space and "sample_questions" in space["config"]:
        sq = space["config"]["sample_questions"]
        if not isinstance(sq, list):
            errors.append(f"{path}.config.sample_questions: Must be array")
        else:
            for i, q in enumerate(sq):
                if not isinstance(q, dict):
                    errors.append(f"{path}.config.sample_questions[{i}]: Must be object")
                    continue
                
                # Check required fields
                if "id" not in q:
                    errors.append(f"{path}.config.sample_questions[{i}]: Missing 'id'")
                elif not isinstance(q["id"], str) or len(q["id"]) != 32:
                    errors.append(f"{path}.config.sample_questions[{i}].id: Must be 32 hex chars, got '{q['id']}'")
                
                if "question" not in q:
                    errors.append(f"{path}.config.sample_questions[{i}]: Missing 'question'")
                elif not isinstance(q["question"], list):
                    errors.append(f"{path}.config.sample_questions[{i}].question: Must be array, got {type(q['question'])}")
                elif len(q["question"]) == 0:
                    errors.append(f"{path}.config.sample_questions[{i}].question: Empty array")
                
                # Check for INVALID fields
                invalid_fields = set(q.keys()) - {"id", "question"}
                if invalid_fields:
                    errors.append(f"{path}.config.sample_questions[{i}]: Invalid fields: {invalid_fields}")
    
    # 3. Validate data_sources.tables
    if "data_sources" in space:
        ds = space["data_sources"]
        
        if "tables" in ds:
            tables = ds["tables"]
            if not isinstance(tables, list):
                errors.append(f"{path}.data_sources.tables: Must be array")
            else:
                for i, table in enumerate(tables):
                    if not isinstance(table, dict):
                        errors.append(f"{path}.data_sources.tables[{i}]: Must be object")
                        continue
                    
                    # Check required fields
                    if "identifier" not in table:
                        errors.append(f"{path}.data_sources.tables[{i}]: Missing 'identifier'")
                    elif not isinstance(table["identifier"], str):
                        errors.append(f"{path}.data_sources.tables[{i}].identifier: Must be string")
                    elif "." not in table["identifier"]:
                        errors.append(f"{path}.data_sources.tables[{i}].identifier: Must be 3-part name")
                    elif "${" in table["identifier"]:
                        errors.append(f"{path}.data_sources.tables[{i}].identifier: Contains template variable (not substituted)")
                    
                    # Check column_configs if present
                    if "column_configs" in table:
                        if not isinstance(table["column_configs"], list):
                            errors.append(f"{path}.data_sources.tables[{i}].column_configs: Must be array")
                        else:
                            for j, cc in enumerate(table["column_configs"]):
                                if "column_name" not in cc:
                                    errors.append(f"{path}.data_sources.tables[{i}].column_configs[{j}]: Missing 'column_name'")
                    
                    # Check for INVALID fields
                    valid_fields = {"identifier", "description", "column_configs"}
                    invalid_fields = set(table.keys()) - valid_fields
                    if invalid_fields:
                        errors.append(f"{path}.data_sources.tables[{i}]: Invalid fields: {invalid_fields}")
        
        # 4. Validate data_sources.metric_views
        if "metric_views" in ds:
            mvs = ds["metric_views"]
            if not isinstance(mvs, list):
                errors.append(f"{path}.data_sources.metric_views: Must be array")
            else:
                for i, mv in enumerate(mvs):
                    if not isinstance(mv, dict):
                        errors.append(f"{path}.data_sources.metric_views[{i}]: Must be object")
                        continue
                    
                    # Check required fields
                    if "identifier" not in mv:
                        errors.append(f"{path}.data_sources.metric_views[{i}]: Missing 'identifier'")
                    elif not isinstance(mv["identifier"], str):
                        errors.append(f"{path}.data_sources.metric_views[{i}].identifier: Must be string")
                    elif "." not in mv["identifier"]:
                        errors.append(f"{path}.data_sources.metric_views[{i}].identifier: Must be 3-part name")
                    elif "${" in mv["identifier"]:
                        errors.append(f"{path}.data_sources.metric_views[{i}].identifier: Contains template variable (not substituted)")
                    
                    # Check for INVALID fields (like full_name, name, id)
                    valid_fields = {"identifier", "description", "column_configs"}
                    invalid_fields = set(mv.keys()) - valid_fields
                    if invalid_fields:
                        errors.append(f"{path}.data_sources.metric_views[{i}]: Invalid fields: {invalid_fields}")
    
    # 5. Validate instructions.text_instructions
    if "instructions" in space and "text_instructions" in space["instructions"]:
        ti = space["instructions"]["text_instructions"]
        if not isinstance(ti, list):
            errors.append(f"{path}.instructions.text_instructions: Must be array")
        else:
            for i, inst in enumerate(ti):
                if not isinstance(inst, dict):
                    errors.append(f"{path}.instructions.text_instructions[{i}]: Must be object")
                    continue
                
                if "id" not in inst:
                    errors.append(f"{path}.instructions.text_instructions[{i}]: Missing 'id'")
                elif not isinstance(inst["id"], str) or len(inst["id"]) != 32:
                    errors.append(f"{path}.instructions.text_instructions[{i}].id: Must be 32 hex chars")
                
                if "content" in inst:
                    if not isinstance(inst["content"], list):
                        errors.append(f"{path}.instructions.text_instructions[{i}].content: Must be array")
                
                # Check for INVALID fields
                valid_fields = {"id", "content"}
                invalid_fields = set(inst.keys()) - valid_fields
                if invalid_fields:
                    errors.append(f"{path}.instructions.text_instructions[{i}]: Invalid fields: {invalid_fields}")
    
    # 6. Validate instructions.sql_functions
    if "instructions" in space and "sql_functions" in space["instructions"]:
        sf = space["instructions"]["sql_functions"]
        if not isinstance(sf, list):
            errors.append(f"{path}.instructions.sql_functions: Must be array")
        else:
            for i, func in enumerate(sf):
                if not isinstance(func, dict):
                    errors.append(f"{path}.instructions.sql_functions[{i}]: Must be object")
                    continue
                
                if "id" not in func:
                    errors.append(f"{path}.instructions.sql_functions[{i}]: Missing 'id'")
                
                if "identifier" not in func:
                    errors.append(f"{path}.instructions.sql_functions[{i}]: Missing 'identifier'")
                
                # Check for INVALID fields (name, signature, full_name, description)
                valid_fields = {"id", "identifier"}
                invalid_fields = set(func.keys()) - valid_fields
                if invalid_fields:
                    errors.append(f"{path}.instructions.sql_functions[{i}]: Invalid fields: {invalid_fields}")
    
    # 7. Validate benchmarks.questions
    if "benchmarks" in space and "questions" in space["benchmarks"]:
        bq = space["benchmarks"]["questions"]
        if not isinstance(bq, list):
            errors.append(f"{path}.benchmarks.questions: Must be array")
        else:
            for i, q in enumerate(bq):
                if not isinstance(q, dict):
                    errors.append(f"{path}.benchmarks.questions[{i}]: Must be object")
                    continue
                
                if "id" not in q:
                    errors.append(f"{path}.benchmarks.questions[{i}]: Missing 'id'")
                
                if "question" not in q:
                    errors.append(f"{path}.benchmarks.questions[{i}]: Missing 'question'")
                elif not isinstance(q["question"], list):
                    errors.append(f"{path}.benchmarks.questions[{i}].question: Must be array")
                
                if "answer" not in q:
                    errors.append(f"{path}.benchmarks.questions[{i}]: Missing 'answer'")
                elif not isinstance(q["answer"], list):
                    errors.append(f"{path}.benchmarks.questions[{i}].answer: Must be array")
                elif len(q["answer"]) > 0:
                    ans = q["answer"][0]
                    if "format" not in ans or ans["format"] != "SQL":
                        errors.append(f"{path}.benchmarks.questions[{i}].answer[0].format: Must be 'SQL'")
                    if "content" not in ans:
                        errors.append(f"{path}.benchmarks.questions[{i}].answer[0]: Missing 'content'")
                    elif not isinstance(ans["content"], list):
                        errors.append(f"{path}.benchmarks.questions[{i}].answer[0].content: Must be array")
    
    return errors


def analyze_file(json_file: str, reference: dict) -> Dict[str, Any]:
    """Analyze a single Genie Space JSON file."""
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Parse serialized_space
    if isinstance(data, dict) and "serialized_space" in data:
        space = parse_serialized_space(data["serialized_space"])
    else:
        space = data
    
    ref_space = parse_serialized_space(reference["serialized_space"])
    
    result = {
        "file": os.path.basename(json_file),
        "structure_errors": [],
        "format_differences": [],
        "statistics": {}
    }
    
    # Validate structure
    result["structure_errors"] = validate_structure(data)
    
    # Compare format with reference
    # Check tables
    ref_has_tables = "data_sources" in ref_space and "tables" in ref_space["data_sources"]
    data_has_tables = "data_sources" in space and "tables" in space["data_sources"]
    
    if ref_has_tables and data_has_tables:
        ref_table = ref_space["data_sources"]["tables"][0]
        data_table = space["data_sources"]["tables"][0] if space["data_sources"]["tables"] else {}
        
        ref_keys = set(ref_table.keys())
        data_keys = set(data_table.keys()) if data_table else set()
        
        if ref_keys != data_keys:
            result["format_differences"].append(
                f"tables[0] keys: Reference has {ref_keys}, file has {data_keys}"
            )
    
    # Check metric_views
    ref_has_mvs = "data_sources" in ref_space and "metric_views" in ref_space["data_sources"]
    data_has_mvs = "data_sources" in space and "metric_views" in space["data_sources"]
    
    if ref_has_mvs and data_has_mvs:
        ref_mv = ref_space["data_sources"]["metric_views"][0]
        data_mv = space["data_sources"]["metric_views"][0] if space["data_sources"]["metric_views"] else {}
        
        ref_keys = set(ref_mv.keys())
        data_keys = set(data_mv.keys()) if data_mv else set()
        
        if ref_keys != data_keys:
            result["format_differences"].append(
                f"metric_views[0] keys: Reference has {ref_keys}, file has {data_keys}"
            )
    
    # Statistics
    result["statistics"] = {
        "sample_questions": len(space.get("config", {}).get("sample_questions", [])),
        "tables": len(space.get("data_sources", {}).get("tables", [])),
        "metric_views": len(space.get("data_sources", {}).get("metric_views", [])),
        "text_instructions": len(space.get("instructions", {}).get("text_instructions", [])),
        "sql_functions": len(space.get("instructions", {}).get("sql_functions", [])),
        "join_specs": len(space.get("instructions", {}).get("join_specs", [])),
        "benchmark_questions": len(space.get("benchmarks", {}).get("questions", []))
    }
    
    return result


def main():
    """Validate all Genie Space JSON files."""
    
    # Load reference
    ref_file = "context/genie/genie_space_export.json"
    with open(ref_file, 'r') as f:
        reference = json.load(f)
    
    print("="*100)
    print("GENIE SPACE JSON VALIDATION AGAINST REFERENCE")
    print("="*100)
    print(f"\nReference: {ref_file}")
    print(f"Validating against production Databricks Genie Space export format\n")
    
    # Files to validate
    genie_files = [
        "src/genie/cost_intelligence_genie_export.json",
        "src/genie/performance_genie_export.json",
        "src/genie/job_health_monitor_genie_export.json",
        "src/genie/data_quality_monitor_genie_export.json",
        "src/genie/security_auditor_genie_export.json",
        "src/genie/unified_health_monitor_genie_export.json"
    ]
    
    all_results = []
    total_errors = 0
    
    for json_file in genie_files:
        if not os.path.exists(json_file):
            print(f"⚠ File not found: {json_file}\n")
            continue
        
        result = analyze_file(json_file, reference)
        all_results.append(result)
        
        error_count = len(result["structure_errors"]) + len(result["format_differences"])
        total_errors += error_count
        
        # Print results
        print("-"*100)
        print(f"FILE: {result['file']}")
        print("-"*100)
        
        # Statistics
        stats = result["statistics"]
        print(f"Statistics:")
        print(f"  Sample Questions: {stats['sample_questions']}")
        print(f"  Tables: {stats['tables']}")
        print(f"  Metric Views: {stats['metric_views']}")
        print(f"  Text Instructions: {stats['text_instructions']}")
        print(f"  SQL Functions: {stats['sql_functions']}")
        print(f"  Join Specs: {stats['join_specs']}")
        print(f"  Benchmark Questions: {stats['benchmark_questions']}")
        
        # Structure errors
        if result["structure_errors"]:
            print(f"\n❌ Structure Errors ({len(result['structure_errors'])}):")
            for err in result["structure_errors"]:
                print(f"  • {err}")
        else:
            print(f"\n✅ No structure errors")
        
        # Format differences
        if result["format_differences"]:
            print(f"\n⚠️  Format Differences ({len(result['format_differences'])}):")
            for diff in result["format_differences"]:
                print(f"  • {diff}")
        else:
            print(f"\n✅ Format matches reference")
        
        print()
    
    # Summary
    print("="*100)
    print("SUMMARY")
    print("="*100)
    print(f"Files validated: {len(all_results)}")
    print(f"Total errors: {total_errors}")
    
    if total_errors == 0:
        print("\n✅ All files match reference structure!")
    else:
        print(f"\n❌ {total_errors} errors found - see details above")
    
    return total_errors


if __name__ == "__main__":
    exit_code = main()
    exit(0 if exit_code == 0 else 1)
