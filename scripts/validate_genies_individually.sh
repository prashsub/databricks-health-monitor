#!/bin/bash

# Validate each Genie Space individually
# This allows us to isolate errors by Genie Space

set -e

CATALOG="prashanth_subrahmanyam_catalog"
GOLD_SCHEMA="dev_prashanth_subrahmanyam_system_gold"
FEATURE_SCHEMA="dev_prashanth_subrahmanyam_system_gold_ml"

GENIE_SPACES=(
    "cost_intelligence_genie"
    "job_health_monitor_genie"
    "performance_genie"
    "security_auditor_genie"
    "data_quality_monitor_genie"
    "unified_health_monitor_genie"
)

echo "========================================"
echo "Validating Genie Spaces Individually"
echo "========================================"
echo ""

for GENIE in "${GENIE_SPACES[@]}"; do
    echo "------------------------------------------------------------"
    echo "Validating: $GENIE"
    echo "------------------------------------------------------------"
    
    # Upload notebook if not already uploaded
    databricks workspace import \
        --profile health_monitor \
        --language PYTHON \
        --format SOURCE \
        src/genie/validate_single_genie_space.py \
        /Users/prashanth.subrahmanyam@databricks.com/validate_single_genie_space \
        --overwrite 2>/dev/null || true
    
    # Run validation
    databricks workspace run \
        --profile health_monitor \
        /Users/prashanth.subrahmanyam@databricks.com/validate_single_genie_space \
        --parameters catalog="$CATALOG" \
        --parameters gold_schema="$GOLD_SCHEMA" \
        --parameters feature_schema="$FEATURE_SCHEMA" \
        --parameters genie_space="$GENIE" \
        || echo "❌ Validation failed for $GENIE"
    
    echo ""
done

echo "========================================"
echo "Validation Complete"
echo "========================================"
