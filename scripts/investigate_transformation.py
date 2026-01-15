#!/usr/bin/env python3
"""
Investigate the actual transformation that happens during Genie Space deployment.
Simulates the exact flow in deploy_genie_space.py to see what the API receives.
"""

import json
import sys
import os

# Add src to path to import the transformation functions
sys.path.insert(0, 'src/genie')

def substitute_variables(content: str, catalog: str, gold_schema: str, feature_schema: str) -> str:
    """Substitute variables."""
    result = content.replace("${catalog}", catalog)
    result = result.replace("${gold_schema}", gold_schema)
    result = result.replace("${feature_schema}", feature_schema)
    return result

def process_json_values(obj, catalog: str, gold_schema: str, feature_schema: str):
    """Recursively process JSON and substitute variables."""
    if isinstance(obj, dict):
        return {k: process_json_values(v, catalog, gold_schema, feature_schema) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [process_json_values(item, catalog, gold_schema, feature_schema) for item in obj]
    elif isinstance(obj, str):
        return substitute_variables(obj, catalog, gold_schema, feature_schema)
    else:
        return obj

def transform_custom_format_to_api(custom_data: dict) -> dict:
    """Transform custom format to API format."""
    import uuid
    
    api_data = {"version": custom_data.get("version", 1)}
    
    # Transform config section
    if "config" in custom_data:
        config = custom_data["config"]
        api_config = {}
        
        # Transform sample_questions: array of strings → array of objects with id/question
        if "sample_questions" in config:
            sample_qs = config["sample_questions"]
            if sample_qs and isinstance(sample_qs[0], str):
                # Custom format: array of strings
                api_config["sample_questions"] = [
                    {
                        "id": uuid.uuid4().hex,
                        "question": [q]
                    }
                    for q in sample_qs
                ]
            else:
                # Already in API format
                api_config["sample_questions"] = sample_qs
        
        api_data["config"] = api_config
    
    # Transform data_sources section
    if "data_sources" in custom_data:
        ds = custom_data["data_sources"]
        api_ds = {}
        
        # Transform metric_views: {id, name, full_name} → {identifier}
        if "metric_views" in ds:
            api_ds["metric_views"] = []
            for mv in ds["metric_views"]:
                if "identifier" in mv:
                    # Already API format
                    api_ds["metric_views"].append(mv)
                elif "full_name" in mv:
                    # Custom format: full_name → identifier
                    api_mv = {"identifier": mv["full_name"]}
                    if "description" in mv:
                        api_mv["description"] = mv["description"] if isinstance(mv["description"], list) else [mv["description"]]
                    if "column_configs" in mv:
                        api_mv["column_configs"] = mv["column_configs"]
                    api_ds["metric_views"].append(api_mv)
        
        # Transform tables similarly
        if "tables" in ds:
            api_ds["tables"] = []
            for tbl in ds["tables"]:
                if "identifier" in tbl:
                    api_ds["tables"].append(tbl)
                elif "full_name" in tbl:
                    api_tbl = {"identifier": tbl["full_name"]}
                    if "description" in tbl:
                        api_tbl["description"] = tbl["description"] if isinstance(tbl["description"], list) else [tbl["description"]]
                    if "column_configs" in tbl:
                        api_tbl["column_configs"] = tbl["column_configs"]
                    api_ds["tables"].append(api_tbl)
        
        api_data["data_sources"] = api_ds
    
    # Copy instructions and benchmarks as-is
    if "instructions" in custom_data:
        api_data["instructions"] = custom_data["instructions"]
    if "benchmarks" in custom_data:
        api_data["benchmarks"] = custom_data["benchmarks"]
    
    return api_data


def test_transformation(json_file: str):
    """Test the transformation for a single file."""
    
    # Parameters (same as dev environment)
    catalog = "prashanth_subrahmanyam_catalog"
    gold_schema = "dev_prashanth_subrahmanyam_system_gold"
    feature_schema = "dev_prashanth_subrahmanyam_system_gold_ml"
    
    print(f"\n{'='*100}")
    print(f"TRANSFORMATION TEST: {os.path.basename(json_file)}")
    print(f"{'='*100}")
    
    # Load JSON
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    print("\n1. BEFORE VARIABLE SUBSTITUTION:")
    ds = data.get("data_sources", {})
    mvs = ds.get("metric_views", [])
    tables = ds.get("tables", [])
    
    print(f"   Metric Views: {len(mvs)}")
    if mvs:
        mv = mvs[0]
        id_val = mv.get("identifier") or mv.get("full_name") or "N/A"
        print(f"     First MV: {id_val}")
    
    print(f"   Tables: {len(tables)}")
    if tables:
        id_val = tables[0].get("identifier") or "N/A"
        print(f"     First Table: {id_val[:80]}...")
    
    # Process variables
    processed = process_json_values(data, catalog, gold_schema, feature_schema)
    
    print("\n2. AFTER VARIABLE SUBSTITUTION:")
    ds = processed.get("data_sources", {})
    mvs = ds.get("metric_views", [])
    tables = ds.get("tables", [])
    
    if mvs:
        mv = mvs[0]
        id_val = mv.get("identifier") or mv.get("full_name") or "N/A"
        print(f"   First MV: {id_val}")
    
    if tables:
        id_val = tables[0].get("identifier") or "N/A"
        print(f"   First Table: {id_val[:80]}...")
    
    # Transform format
    api_format = transform_custom_format_to_api(processed)
    
    print("\n3. AFTER API TRANSFORMATION:")
    ds = api_format.get("data_sources", {})
    mvs = ds.get("metric_views", [])
    tables = ds.get("tables", [])
    
    print(f"   Metric Views: {len(mvs)}")
    if mvs:
        mv = mvs[0]
        print(f"     Keys: {list(mv.keys())}")
        print(f"     Identifier: {mv.get('identifier', 'N/A')}")
    
    print(f"   Tables: {len(tables)}")
    if tables:
        print(f"     Keys: {list(tables[0].keys())}")
        print(f"     Identifier: {tables[0].get('identifier', 'N/A')[:80]}...")
    
    return api_format


def main():
    """Test all 6 Genie Space JSON files."""
    
    files = [
        ("cost_intelligence_genie_export.json", "SUCCESS"),
        ("performance_genie_export.json", "SUCCESS"),
        ("job_health_monitor_genie_export.json", "FAILED"),
        ("data_quality_monitor_genie_export.json", "FAILED"),
        ("security_auditor_genie_export.json", "FAILED"),
        ("unified_health_monitor_genie_export.json", "FAILED")
    ]
    
    results = {}
    
    for filename, status in files:
        json_path = f"src/genie/{filename}"
        try:
            api_format = test_transformation(json_path)
            results[filename] = ("SUCCESS", api_format)
        except Exception as e:
            results[filename] = ("ERROR", str(e))
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n\n{'='*100}")
    print("SUMMARY")
    print(f"{'='*100}")
    
    for filename, (result_status, _) in results.items():
        print(f"{filename}: {result_status}")


if __name__ == "__main__":
    main()
