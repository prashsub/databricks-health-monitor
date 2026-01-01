#!/bin/bash
# Delete monitoring dashboards from Databricks workspace
# Uses Databricks CLI for auth and curl for efficiency

set -e

# Get Databricks host from CLI config
DATABRICKS_HOST=$(databricks auth describe 2>/dev/null | grep "Host:" | awk '{print $2}')

if [ -z "$DATABRICKS_HOST" ]; then
    echo "❌ Error: Could not get Databricks host. Run: databricks auth login"
    exit 1
fi

# Get token from databricks CLI (it handles OAuth/token refresh)
DATABRICKS_TOKEN=$(databricks auth token --host "$DATABRICKS_HOST" 2>/dev/null | grep '"access_token"' | sed 's/.*"access_token": "\([^"]*\)".*/\1/')

if [ -z "$DATABRICKS_TOKEN" ]; then
    echo "❌ Error: Could not get Databricks token. Run: databricks auth login"
    exit 1
fi

echo "✓ Connected to: $DATABRICKS_HOST"
echo ""

# Dashboard names to delete (exact matches)
DASHBOARD_NAMES=(
    "fact_table_lineage Monitoring"
    "fact_audit_logs Monitoring"
    "fact_node_timeline Monitoring"
    "fact_query_history Monitoring"
    "fact_job_run_timeline Monitoring"
    "fact_usage Monitoring"
    "fact_usage Monitoring (1)"
    "fact_job_run_timeline Monitoring (1)"
    "fact_query_history Monitoring (1)"
    "fact_node_timeline Monitoring (1)"
    "fact_audit_logs Monitoring (1)"
    "fact_table_lineage Monitoring (1)"
    "fact_usage Monitoring (2)"
    "fact_job_run_timeline Monitoring (2)"
    "fact_query_history Monitoring (2)"
    "fact_node_timeline Monitoring (2)"
    "fact_audit_logs Monitoring (2)"
    "fact_table_lineage Monitoring (2)"
    "fact_usage Monitoring (3)"
    "fact_job_run_timeline Monitoring (3)"
    "fact_query_history Monitoring (3)"
    "fact_node_timeline Monitoring (3)"
    "fact_audit_logs Monitoring (3)"
    "fact_table_lineage Monitoring (3)"
    "fact_usage Monitoring (4)"
    "fact_job_run_timeline Monitoring (4)"
    "fact_query_history Monitoring (4)"
    "fact_node_timeline Monitoring (4)"
    "fact_audit_logs Monitoring (4)"
    "fact_table_lineage Monitoring (4)"
    "fact_usage Monitoring (5)"
    "fact_job_run_timeline Monitoring (5)"
    "fact_query_history Monitoring (5)"
    "fact_node_timeline Monitoring (5)"
    "fact_audit_logs Monitoring (5)"
    "fact_table_lineage Monitoring (5)"
    "fact_usage Monitoring (6)"
    "fact_job_run_timeline Monitoring (6)"
    "fact_query_history Monitoring (6)"
    "fact_node_timeline Monitoring (6)"
    "fact_audit_logs Monitoring (6)"
    "fact_table_lineage Monitoring (6)"
    "fact_usage Monitoring (7)"
    "fact_job_run_timeline Monitoring (7)"
    "fact_query_history Monitoring (7)"
    "fact_node_timeline Monitoring (7)"
    "fact_audit_logs Monitoring (7)"
    "fact_table_lineage Monitoring (7)"
)

echo "📋 Searching for ${#DASHBOARD_NAMES[@]} dashboard names..."
echo ""

# Fetch dashboards page by page
DELETED=0
FAILED=0
PAGE_TOKEN=""

while true; do
    # Build URL with pagination
    if [ -z "$PAGE_TOKEN" ]; then
        URL="${DATABRICKS_HOST}/api/2.0/lakeview/dashboards?page_size=100"
    else
        URL="${DATABRICKS_HOST}/api/2.0/lakeview/dashboards?page_size=100&page_token=${PAGE_TOKEN}"
    fi
    
    # Fetch page
    RESPONSE=$(curl -s -X GET "$URL" \
        -H "Authorization: Bearer $DATABRICKS_TOKEN" \
        -H "Content-Type: application/json")
    
    # Check for error (with retry for rate limits)
    if echo "$RESPONSE" | grep -q '"error_code"'; then
        if echo "$RESPONSE" | grep -q 'RESOURCE_EXHAUSTED'; then
            echo "   ⏳ Rate limited, waiting 10 seconds..."
            sleep 10
            continue
        fi
        echo "❌ API Error: $RESPONSE"
        exit 1
    fi
    
    # Process each dashboard in this page
    DASHBOARDS=$(echo "$RESPONSE" | grep -o '"dashboard_id":"[^"]*","display_name":"[^"]*"' || true)
    
    while IFS= read -r line; do
        if [ -z "$line" ]; then continue; fi
        
        DASHBOARD_ID=$(echo "$line" | grep -o '"dashboard_id":"[^"]*"' | cut -d'"' -f4)
        DISPLAY_NAME=$(echo "$line" | grep -o '"display_name":"[^"]*"' | cut -d'"' -f4)
        
        # Check if this dashboard matches any name to delete
        for NAME in "${DASHBOARD_NAMES[@]}"; do
            if [ "$DISPLAY_NAME" = "$NAME" ]; then
                echo "🗑️  Deleting: $DISPLAY_NAME (ID: $DASHBOARD_ID)"
                
                # Delete (trash) the dashboard
                DELETE_RESPONSE=$(curl -s -X DELETE \
                    "${DATABRICKS_HOST}/api/2.0/lakeview/dashboards/${DASHBOARD_ID}" \
                    -H "Authorization: Bearer $DATABRICKS_TOKEN" \
                    -H "Content-Type: application/json")
                
                if echo "$DELETE_RESPONSE" | grep -q '"error_code"'; then
                    echo "   ❌ Failed: $DELETE_RESPONSE"
                    ((FAILED++))
                else
                    echo "   ✓ Deleted"
                    ((DELETED++))
                fi
                sleep 0.5  # Rate limit: wait between deletes
                break
            fi
        done
    done <<< "$DASHBOARDS"
    
    # Check for next page
    PAGE_TOKEN=$(echo "$RESPONSE" | grep -o '"next_page_token":"[^"]*"' | cut -d'"' -f4 || true)
    
    if [ -z "$PAGE_TOKEN" ]; then
        break
    fi
    
    echo "   ... fetching next page ..."
    sleep 1  # Rate limit: wait 1 second between pages
done

echo ""
echo "========================================"
echo "Summary:"
echo "   ✓ Deleted: $DELETED"
echo "   ❌ Failed: $FAILED"
echo "========================================"

