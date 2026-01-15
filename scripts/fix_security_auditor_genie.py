#!/usr/bin/env python3
"""
Fix Security Auditor Genie Space to match specification.

Issues:
1. Missing 10 tables (3 dim + 5 fact + 3 ML)
2. Missing 1 metric view (mv_governance_analytics)
3. Template variables instead of hardcoded paths
4. TVF names don't match spec
"""

import json
from pathlib import Path

# Hardcoded schema paths (from Session 23D)
SYSTEM_GOLD = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold"
SYSTEM_GOLD_ML = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_ml"
SYSTEM_GOLD_MONITORING = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_monitoring"

def fix_security_auditor():
    """Fix Security Auditor Genie Space JSON."""
    
    json_path = Path("src/genie/security_auditor_genie_export.json")
    data = json.load(open(json_path))
    
    print("Fixing Security Auditor Genie Space...")
    print("=" * 80)
    
    # 1. Fix metric views - add missing mv_governance_analytics and hardcode paths
    print("\n1. Fixing metric views...")
    data['data_sources']['metric_views'] = [
        {
            "identifier": f"{SYSTEM_GOLD}.mv_security_events",
            "description": [
                "Security event metrics for audit and compliance analytics."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD}.mv_governance_analytics",
            "description": [
                "Data lineage and governance metrics."
            ]
        }
    ]
    print("   ✅ Fixed 2 metric views (added mv_governance_analytics, hardcoded paths)")
    
    # 2. Add missing tables
    print("\n2. Adding missing tables...")
    
    # Missing dimension tables
    missing_dim_tables = [
        {
            "identifier": f"{SYSTEM_GOLD}.dim_user",
            "description": [
                "User information for access analysis.",
                "Business: Links events to user profiles and departments."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD}.dim_date",
            "description": [
                "Date dimension for time-based analysis.",
                "Business: Enables temporal analysis of security events."
            ]
        }
    ]
    
    # Missing fact tables
    missing_fact_tables = [
        {
            "identifier": f"{SYSTEM_GOLD}.fact_table_lineage",
            "description": [
                "Data lineage tracking table access patterns.",
                "Business: Governance and lineage analysis."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD}.fact_assistant_events",
            "description": [
                "AI assistant interaction events.",
                "Business: AI assistant usage tracking."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD}.fact_clean_room_events",
            "description": [
                "Clean room operation events.",
                "Business: Secure data collaboration tracking."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD}.fact_inbound_network",
            "description": [
                "Inbound network traffic events.",
                "Business: Network security monitoring."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD}.fact_outbound_network",
            "description": [
                "Outbound network traffic events.",
                "Business: Data exfiltration monitoring."
            ]
        }
    ]
    
    # Missing ML prediction tables
    missing_ml_tables = [
        {
            "identifier": f"{SYSTEM_GOLD_ML}.user_risk_scores",
            "description": [
                "ML user risk scores (1-5 scale).",
                "Business: Compliance risk assessment."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD_ML}.access_classifications",
            "description": [
                "ML access pattern classifications.",
                "Business: Normal vs suspicious access detection."
            ]
        },
        {
            "identifier": f"{SYSTEM_GOLD_ML}.off_hours_baseline_predictions",
            "description": [
                "ML off-hours activity baseline.",
                "Business: After-hours anomaly detection."
            ]
        }
    ]
    
    # Add all missing tables
    data['data_sources']['tables'].extend(missing_dim_tables)
    data['data_sources']['tables'].extend(missing_fact_tables)
    data['data_sources']['tables'].extend(missing_ml_tables)
    
    print(f"   ✅ Added {len(missing_dim_tables)} missing dim tables")
    print(f"   ✅ Added {len(missing_fact_tables)} missing fact tables")
    print(f"   ✅ Added {len(missing_ml_tables)} missing ML tables")
    
    # 3. Fix TVF identifiers (hardcode paths AND fix names to match spec)
    print("\n3. Fixing TVF identifiers...")
    
    # Mapping from current names to spec names
    tvf_name_map = {
        "get_user_activity_summary": "get_user_activity",
        "get_table_access_events": "get_table_access_audit",
        "get_permission_changes": "get_permission_change_events",
        "get_service_principal_activity": "get_service_account_audit",
        "get_failed_actions": "get_failed_authentication_events",
        "get_sensitive_table_access": "get_pii_access_events",
    }
    
    # Fix existing TVFs
    for tvf in data['instructions']['sql_functions']:
        old_name = tvf['identifier'].split('.')[-1]
        
        # Map to correct name if needed
        new_name = tvf_name_map.get(old_name, old_name)
        
        # Hardcode path
        tvf['identifier'] = f"{SYSTEM_GOLD}.{new_name}"
    
    # Add missing user_risk_scores TVF
    data['instructions']['sql_functions'].append({
        "id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
        "identifier": f"{SYSTEM_GOLD}.user_risk_scores"
    })
    
    print(f"   ✅ Fixed {len(tvf_name_map)} TVF names")
    print(f"   ✅ Hardcoded all {len(data['instructions']['sql_functions'])} TVF paths")
    print(f"   ✅ Added missing user_risk_scores TVF")
    
    # 4. Sort tables by category for better organization
    print("\n4. Organizing tables...")
    
    def get_table_category(identifier):
        table_name = identifier.split('.')[-1]
        if table_name.startswith('dim_'):
            return 0
        elif table_name.startswith('fact_') and 'metrics' not in table_name:
            return 1
        elif '_ml.' in identifier:
            return 2
        elif 'monitoring' in identifier:
            return 3
        return 4
    
    data['data_sources']['tables'].sort(key=lambda t: (get_table_category(t['identifier']), t['identifier']))
    print("   ✅ Sorted tables by category (dim → fact → ML → monitoring)")
    
    # Save
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print("\n" + "=" * 80)
    print("✅ Security Auditor Genie Space fixed successfully!")
    print()
    print("Summary of changes:")
    print(f"  - Added 10 missing tables (2 dim + 5 fact + 3 ML)")
    print(f"  - Added 1 missing metric view (mv_governance_analytics)")
    print(f"  - Fixed 6 TVF names to match spec")
    print(f"  - Added 1 missing TVF (user_risk_scores)")
    print(f"  - Hardcoded all template variables")
    print()
    print(f"Updated: {json_path}")

if __name__ == "__main__":
    fix_security_auditor()
