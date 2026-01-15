#!/usr/bin/env python3
"""
Debug the cost_intelligence transformation to see what's being sent to the API.
"""

import json

def transform_custom_format_to_api(custom_data: dict) -> dict:
    """
    Transform custom simplified Genie Space format to Databricks API format.
    (Copied from deploy_genie_space.py)
    """
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
                    {"id": str(uuid.uuid4().hex), "question": [q]} 
                    for q in sample_qs
                ]
            else:
                # Already in API format (array of objects with id/question)
                api_config["sample_questions"] = sample_qs
        
        api_data["config"] = api_config
    
    # Copy data_sources as-is (except metric_views needs transformation)
    if "data_sources" in custom_data:
        api_data["data_sources"] = custom_data["data_sources"].copy()
        
        # Transform metric_views: {"id", "name", "full_name"} → {"identifier": full_name}
        if "metric_views" in api_data["data_sources"]:
            mvs = api_data["data_sources"]["metric_views"]
            transformed_mvs = []
            for mv in mvs:
                if "full_name" in mv:
                    # API format uses identifier (not id/name/full_name)
                    transformed_mvs.append({
                        "identifier": mv["full_name"],
                        "column_configs": mv.get("column_configs", [])
                    })
                else:
                    # Already in API format
                    transformed_mvs.append(mv)
            api_data["data_sources"]["metric_views"] = transformed_mvs
    
    # Copy instructions as-is
    if "instructions" in custom_data:
        api_data["instructions"] = custom_data["instructions"]
    
    # DON'T copy benchmarks - not part of API payload
    
    return api_data


# Load and transform
with open("src/genie/cost_intelligence_genie_export.json", "r") as f:
    cost = json.load(f)

print("=== BEFORE TRANSFORMATION ===")
print(f"Top-level keys: {sorted(cost.keys())}")
print(f"Has config: {'config' in cost}")
print(f"Has data_sources: {'data_sources' in cost}")
print(f"Has benchmarks: {'benchmarks' in cost}")

transformed = transform_custom_format_to_api(cost)

print("\n=== AFTER TRANSFORMATION ===")
print(f"Top-level keys: {sorted(transformed.keys())}")
print(f"Has config: {'config' in transformed}")
print(f"Has data_sources: {'data_sources' in transformed}")
print(f"Has benchmarks: {'benchmarks' in transformed}")

if "config" in transformed:
    print(f"\nconfig keys: {sorted(transformed['config'].keys())}")
    if "sample_questions" in transformed["config"]:
        sq = transformed["config"]["sample_questions"]
        if len(sq) > 0:
            print(f"First sample question: {sq[0]}")

# Save transformed to see structure
with open("debug_cost_transformed.json", "w") as f:
    json.dump(transformed, f, indent=2)

print("\n✓ Saved transformed data to debug_cost_transformed.json")
