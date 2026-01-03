#!/bin/bash
# Delete monitoring dashboards from Databricks workspace

# Check for --yes flag
AUTO_CONFIRM=false
if [ "$1" = "--yes" ] || [ "$1" = "-y" ]; then
    AUTO_CONFIRM=true
fi

# Get Databricks host from CLI config
DATABRICKS_HOST=$(databricks auth describe 2>/dev/null | grep "Host:" | awk '{print $2}')

if [ -z "$DATABRICKS_HOST" ]; then
    echo "❌ Error: Could not get Databricks host. Run: databricks auth login"
    exit 1
fi

# Get token from databricks CLI
DATABRICKS_TOKEN=$(databricks auth token --host "$DATABRICKS_HOST" 2>/dev/null | grep '"access_token"' | sed 's/.*"access_token": "\([^"]*\)".*/\1/')

if [ -z "$DATABRICKS_TOKEN" ]; then
    echo "❌ Error: Could not get Databricks token. Run: databricks auth login"
    exit 1
fi

echo "✓ Connected to: $DATABRICKS_HOST"
echo ""

# Function to check if name matches our pattern
matches_pattern() {
    local name="$1"
    case "$name" in
        "fact_table_lineage Monitoring"|"fact_table_lineage Monitoring ("*")")
            return 0 ;;
        "fact_audit_logs Monitoring"|"fact_audit_logs Monitoring ("*")")
            return 0 ;;
        "fact_node_timeline Monitoring"|"fact_node_timeline Monitoring ("*")")
            return 0 ;;
        "fact_query_history Monitoring"|"fact_query_history Monitoring ("*")")
            return 0 ;;
        "fact_job_run_timeline Monitoring"|"fact_job_run_timeline Monitoring ("*")")
            return 0 ;;
        "fact_usage Monitoring"|"fact_usage Monitoring ("*")")
            return 0 ;;
        *)
            return 1 ;;
    esac
}

echo "📋 Searching for monitoring dashboards..."
echo ""

# Store found dashboards in temp file
TEMP_FILE=$(mktemp)
trap "rm -f $TEMP_FILE" EXIT

# Fetch dashboards page by page
PAGE_TOKEN=""
PAGE_COUNT=0

while true; do
    PAGE_COUNT=$((PAGE_COUNT + 1))
    
    # Build URL with pagination
    if [ -z "$PAGE_TOKEN" ]; then
        URL="${DATABRICKS_HOST}/api/2.0/lakeview/dashboards?page_size=200"
    else
        URL="${DATABRICKS_HOST}/api/2.0/lakeview/dashboards?page_size=200&page_token=${PAGE_TOKEN}"
    fi
    
    # Fetch page
    RESPONSE=$(curl -s -X GET "$URL" \
        -H "Authorization: Bearer $DATABRICKS_TOKEN" \
        -H "Content-Type: application/json")
    
    # Check for rate limit error
    if echo "$RESPONSE" | grep -q 'RESOURCE_EXHAUSTED'; then
        echo "   ⏳ Rate limited, waiting 10 seconds..."
        sleep 10
        continue
    fi
    
    # Check for other errors
    if echo "$RESPONSE" | grep -q '"error_code"'; then
        echo "❌ API Error: $RESPONSE"
        exit 1
    fi
    
    # Parse each dashboard from the JSON array
    # Split by },{ to get individual dashboard objects
    echo "$RESPONSE" | tr ',' '\n' | while read -r field; do
        if echo "$field" | grep -q '"dashboard_id"'; then
            CURRENT_ID=$(echo "$field" | sed 's/.*"dashboard_id":"\([^"]*\)".*/\1/')
        fi
        if echo "$field" | grep -q '"display_name"'; then
            CURRENT_NAME=$(echo "$field" | sed 's/.*"display_name":"\([^"]*\)".*/\1/')
            if [ -n "$CURRENT_ID" ] && [ -n "$CURRENT_NAME" ]; then
                if matches_pattern "$CURRENT_NAME"; then
                    echo "   Found: $CURRENT_NAME"
                    echo "$CURRENT_ID|$CURRENT_NAME" >> "$TEMP_FILE"
                fi
            fi
        fi
    done
    
    # Check for next page
    PAGE_TOKEN=$(echo "$RESPONSE" | grep -o '"next_page_token":"[^"]*"' | cut -d'"' -f4)
    
    if [ -z "$PAGE_TOKEN" ]; then
        break
    fi
    
    echo "   Page $PAGE_COUNT done..."
    sleep 0.5
done

# Count found dashboards
FOUND_COUNT=$(wc -l < "$TEMP_FILE" | tr -d ' ')

echo ""
echo "Found $FOUND_COUNT dashboards to delete"

if [ "$FOUND_COUNT" -eq 0 ]; then
    echo "✅ No matching dashboards found. Nothing to delete."
    exit 0
fi

# Show what will be deleted
echo ""
echo "📋 Dashboards to be deleted:"
echo "----------------------------------------"
while IFS='|' read -r id name; do
    echo "   - $name"
done < "$TEMP_FILE"
echo "----------------------------------------"

# Confirm
echo ""
if [ "$AUTO_CONFIRM" = true ]; then
    echo "⚠️  Auto-confirming deletion (--yes flag provided)"
    CONFIRM="yes"
else
    printf "⚠️  Delete these $FOUND_COUNT dashboards? (yes/no): "
    read CONFIRM
fi

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Cancelled."
    exit 0
fi

# Delete them
echo ""
echo "🗑️  Deleting dashboards..."
DELETED=0
FAILED=0

while IFS='|' read -r DASHBOARD_ID DISPLAY_NAME; do
    echo "   Deleting: $DISPLAY_NAME..."
    
    DELETE_RESPONSE=$(curl -s -X DELETE \
        "${DATABRICKS_HOST}/api/2.0/lakeview/dashboards/${DASHBOARD_ID}" \
        -H "Authorization: Bearer $DATABRICKS_TOKEN" \
        -H "Content-Type: application/json")
    
    if echo "$DELETE_RESPONSE" | grep -q '"error_code"'; then
        echo "   ❌ Failed"
        FAILED=$((FAILED + 1))
    else
        echo "   ✓ Deleted"
        DELETED=$((DELETED + 1))
    fi
    
    sleep 0.3
done < "$TEMP_FILE"

echo ""
echo "========================================"
echo "Summary:"
echo "   ✓ Deleted: $DELETED"
echo "   ❌ Failed: $FAILED"
echo "========================================"
