-- =============================================================================
-- SECURITY AGENT TVFs
-- =============================================================================
-- Table-Valued Functions for security monitoring and audit analysis
--
-- All TVFs query Gold layer tables (fact_audit_logs, dim_workspace)
-- Parameters use STRING type for dates (Genie compatibility)
--
-- SCHEMA REFERENCE (from fact_audit_logs.yaml):
-- - user_identity_email: User email (flattened from user_identity.email)
-- - request_params: MAP<STRING, STRING> - use request_params['tableName']
-- - is_failed_action: BOOLEAN - derived failure flag
-- - is_sensitive_action: BOOLEAN - derived sensitive action flag
-- - response_status_code: INT - HTTP status code
-- - source_ip_address: STRING
-- - event_time: TIMESTAMP
-- - event_date: DATE
-- - service_name, action_name: STRING
-- =============================================================================

-- -----------------------------------------------------------------------------
-- TVF 1: get_user_activity_summary
-- Returns user activity patterns and risk indicators
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_user_activity_summary(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    top_n INT DEFAULT 50 COMMENT 'Number of top users to return'
)
RETURNS TABLE(
    rank INT COMMENT 'Activity rank',
    user_email STRING COMMENT 'User email address',
    event_count INT COMMENT 'Total audit events',
    unique_actions INT COMMENT 'Number of unique actions',
    unique_services INT COMMENT 'Number of services accessed',
    failed_events INT COMMENT 'Failed action count',
    sensitive_events INT COMMENT 'Sensitive action count',
    unique_ips INT COMMENT 'Unique IP addresses',
    off_hours_events INT COMMENT 'Events outside business hours',
    risk_score INT COMMENT 'Risk score (0-100)'
)
COMMENT '
- PURPOSE: User activity summary with risk scoring for security monitoring and anomaly detection
- BEST FOR: "Show user activity summary" "Who are most active users?" "User risk analysis"
- NOT FOR: Activity patterns (use get_user_activity_patterns), service accounts (use get_service_account_audit)
- RETURNS: Users ranked by activity with event count, failures, sensitive actions, IPs, and risk score
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), top_n (default 50)
- SYNTAX: SELECT * FROM TABLE(get_user_activity_summary("2024-01-01", "2024-12-31", 50))
- NOTE: Risk score (0-100) based on failures, IP diversity, sensitive actions, and off-hours activity
'
RETURN
    WITH user_stats AS (
        SELECT
            user_identity_email AS user_email,
            COUNT(*) AS event_count,
            COUNT(DISTINCT action_name) AS unique_actions,
            COUNT(DISTINCT service_name) AS unique_services,
            SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) AS failed_events,
            SUM(CASE WHEN is_sensitive_action THEN 1 ELSE 0 END) AS sensitive_events,
            COUNT(DISTINCT source_ip_address) AS unique_ips,
            SUM(CASE WHEN HOUR(event_time) < 7 OR HOUR(event_time) > 19 THEN 1 ELSE 0 END) AS off_hours_events
        FROM ${catalog}.${gold_schema}.fact_audit_logs
        WHERE event_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND user_identity_email IS NOT NULL
        GROUP BY user_identity_email
    ),
    with_risk AS (
        SELECT *,
            -- Risk score: high failures, many IPs, sensitive actions, off-hours
            LEAST(100,
                (failed_events * 10) +
                (CASE WHEN unique_ips > 5 THEN 20 ELSE 0 END) +
                (sensitive_events * 2) +
                (CASE WHEN off_hours_events > event_count * 0.3 THEN 30 ELSE 0 END)
            ) AS risk_score,
            ROW_NUMBER() OVER (ORDER BY event_count DESC) AS rank
        FROM user_stats
    )
    SELECT rank, user_email, event_count, unique_actions, unique_services,
           failed_events, sensitive_events, unique_ips, off_hours_events, risk_score
    FROM with_risk
    WHERE rank <= top_n
    ORDER BY rank;


-- -----------------------------------------------------------------------------
-- TVF 2: get_sensitive_table_access
-- Returns access to sensitive tables (data access audit)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_sensitive_table_access(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    table_pattern STRING DEFAULT '%' COMMENT 'Table name pattern to filter (SQL LIKE pattern)'
)
RETURNS TABLE(
    access_date DATE COMMENT 'Date of access',
    user_email STRING COMMENT 'User who accessed the table',
    table_name STRING COMMENT 'Table accessed',
    action STRING COMMENT 'Action performed',
    access_count INT COMMENT 'Number of accesses',
    source_ips STRING COMMENT 'Source IP addresses',
    is_off_hours BOOLEAN COMMENT 'True if any access was off-hours'
)
COMMENT '
- PURPOSE: Table access pattern analysis for PII monitoring and compliance auditing
- BEST FOR: "Who accessed PII tables?" "Show access to customer data" "Table access audit"
- NOT FOR: Full lineage tracking (use get_table_access_audit), permission changes (use get_permission_changes)
- RETURNS: Table access by user with date, action, count, source IPs, and off-hours flag
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), table_pattern (SQL LIKE pattern)
- SYNTAX: SELECT * FROM TABLE(get_sensitive_table_access("2024-01-01", "2024-12-31", "%customer%"))
'
RETURN
    SELECT
        event_date AS access_date,
        user_identity_email AS user_email,
        request_params['tableName'] AS table_name,
        action_name AS action,
        COUNT(*) AS access_count,
        CONCAT_WS(', ', COLLECT_SET(source_ip_address)) AS source_ips,
        MAX(CASE WHEN HOUR(event_time) < 7 OR HOUR(event_time) > 19 THEN TRUE ELSE FALSE END) AS is_off_hours
    FROM ${catalog}.${gold_schema}.fact_audit_logs
    WHERE event_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND request_params['tableName'] IS NOT NULL
        AND request_params['tableName'] LIKE table_pattern
        AND action_name IN ('getTable', 'selectFromTable', 'readTable', 'queryTable')
    GROUP BY event_date, user_identity_email, request_params['tableName'], action_name
    ORDER BY access_date DESC, access_count DESC;


-- -----------------------------------------------------------------------------
-- TVF 3: get_failed_actions
-- Returns failed actions for security investigation
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_failed_actions(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    user_filter STRING DEFAULT 'ALL' COMMENT 'User email filter, or ALL'
)
RETURNS TABLE(
    event_time TIMESTAMP COMMENT 'Event timestamp',
    user_email STRING COMMENT 'User who attempted the action',
    service STRING COMMENT 'Databricks service',
    action STRING COMMENT 'Action attempted',
    status_code INT COMMENT 'HTTP status code',
    error_message STRING COMMENT 'Error message',
    source_ip STRING COMMENT 'Source IP address'
)
COMMENT '
- PURPOSE: Failed action investigation for unauthorized access attempts and permission issues
- BEST FOR: "Show failed actions" "What actions failed today?" "Access denied events"
- NOT FOR: User risk scoring (use get_user_activity_summary), all security events (use get_security_events_timeline)
- RETURNS: Failed actions with user, service, action, status code, error message, and source IP
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), user_filter (email or ALL)
- SYNTAX: SELECT * FROM TABLE(get_failed_actions("2024-01-01", "2024-12-31", "ALL"))
'
RETURN
    SELECT
        event_time,
        user_identity_email AS user_email,
        service_name AS service,
        action_name AS action,
        response_status_code AS status_code,
        response_error_message AS error_message,
        source_ip_address AS source_ip
    FROM ${catalog}.${gold_schema}.fact_audit_logs
    WHERE event_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND is_failed_action = TRUE
        AND (user_filter = 'ALL' OR user_identity_email = user_filter)
    ORDER BY event_time DESC
    LIMIT 500;


-- -----------------------------------------------------------------------------
-- TVF 4: get_permission_changes
-- Returns permission/access changes for audit
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_permission_changes(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE(
    event_time TIMESTAMP COMMENT 'Event timestamp',
    changed_by STRING COMMENT 'User who made the change',
    service STRING COMMENT 'Service affected',
    action STRING COMMENT 'Permission action (grant, revoke)',
    target_resource STRING COMMENT 'Resource affected',
    permission STRING COMMENT 'Permission changed',
    source_ip STRING COMMENT 'Source IP address',
    success BOOLEAN COMMENT 'Whether change succeeded'
)
COMMENT '
- PURPOSE: Permission change audit trail for compliance and privilege escalation detection
- BEST FOR: "Show permission changes" "Who changed permissions?" "Grant/revoke audit"
- NOT FOR: Data access audit (use get_sensitive_table_access), user activity (use get_user_activity_summary)
- RETURNS: Permission changes with user, service, action, resource, permission, IP, and success flag
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD)
- SYNTAX: SELECT * FROM TABLE(get_permission_changes("2024-01-01", "2024-12-31"))
'
RETURN
    SELECT
        event_time,
        user_identity_email AS changed_by,
        service_name AS service,
        action_name AS action,
        COALESCE(
            request_params['tableName'],
            request_params['schemaName'],
            request_params['catalogName'],
            request_params['clusterName'],
            request_params['warehouseId']
        ) AS target_resource,
        COALESCE(
            request_params['permission'],
            request_params['privileges'],
            request_params['access_level']
        ) AS permission,
        source_ip_address AS source_ip,
        NOT is_failed_action AS success
    FROM ${catalog}.${gold_schema}.fact_audit_logs
    WHERE event_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND (
            action_name LIKE '%grant%' OR
            action_name LIKE '%revoke%' OR
            action_name LIKE '%permission%' OR
            action_name LIKE '%access%' OR
            action_name IN ('updatePermissions', 'changeOwner', 'setPermissions')
        )
    ORDER BY event_time DESC;


-- -----------------------------------------------------------------------------
-- TVF 5: get_off_hours_activity
-- Returns activity outside business hours
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_off_hours_activity(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    business_hours_start INT DEFAULT 7 COMMENT 'Business hours start (0-23)',
    business_hours_end INT DEFAULT 19 COMMENT 'Business hours end (0-23)'
)
RETURNS TABLE(
    event_date DATE COMMENT 'Date',
    user_email STRING COMMENT 'User email',
    off_hours_events INT COMMENT 'Number of off-hours events',
    services_accessed STRING COMMENT 'Services accessed',
    sensitive_actions INT COMMENT 'Sensitive actions performed',
    unique_ips INT COMMENT 'Unique IP addresses'
)
COMMENT '
- PURPOSE: Off-hours activity detection for suspicious behavior and anomaly identification
- BEST FOR: "Who is working off hours?" "Show late night activity" "After-hours access"
- NOT FOR: Activity patterns (use get_user_activity_patterns), risk scoring (use get_user_activity_summary)
- RETURNS: Users with off-hours event count, services accessed, sensitive actions, and unique IPs
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), business_hours_start (default 7), business_hours_end (default 19)
- SYNTAX: SELECT * FROM TABLE(get_off_hours_activity("2024-01-01", "2024-12-31", 7, 19))
'
RETURN
    SELECT
        event_date,
        user_identity_email AS user_email,
        COUNT(*) AS off_hours_events,
        CONCAT_WS(', ', COLLECT_SET(service_name)) AS services_accessed,
        SUM(CASE WHEN is_sensitive_action THEN 1 ELSE 0 END) AS sensitive_actions,
        COUNT(DISTINCT source_ip_address) AS unique_ips
    FROM ${catalog}.${gold_schema}.fact_audit_logs
    WHERE event_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND (HOUR(event_time) < business_hours_start OR HOUR(event_time) >= business_hours_end)
        AND user_identity_email IS NOT NULL
    GROUP BY event_date, user_identity_email
    HAVING COUNT(*) >= 5
    ORDER BY off_hours_events DESC;


-- -----------------------------------------------------------------------------
-- TVF 6: get_security_events_timeline
-- Returns security events timeline for investigation
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_security_events_timeline(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    user_filter STRING DEFAULT 'ALL' COMMENT 'User email filter, or ALL'
)
RETURNS TABLE(
    event_time TIMESTAMP COMMENT 'Event timestamp',
    user_email STRING COMMENT 'User email',
    event_type STRING COMMENT 'Event classification',
    service STRING COMMENT 'Service',
    action STRING COMMENT 'Action',
    target_resource STRING COMMENT 'Target resource',
    success BOOLEAN COMMENT 'Whether action succeeded',
    source_ip STRING COMMENT 'Source IP'
)
COMMENT '
- PURPOSE: Chronological security event timeline for incident investigation and forensics
- BEST FOR: "Show security timeline for user X" "What did user Y do today?" "Security forensics"
- NOT FOR: Aggregated activity (use get_user_activity_summary), failed actions only (use get_failed_actions)
- RETURNS: Security events in order with user, type, service, action, resource, success, and IP
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), user_filter (email or ALL)
- SYNTAX: SELECT * FROM TABLE(get_security_events_timeline("2024-01-01", "2024-12-31", "user@example.com"))
- NOTE: Event types: FAILED_SENSITIVE, SENSITIVE, FAILED, NORMAL
'
RETURN
    SELECT
        event_time,
        user_identity_email AS user_email,
        CASE
            WHEN is_sensitive_action AND is_failed_action THEN 'FAILED_SENSITIVE'
            WHEN is_sensitive_action THEN 'SENSITIVE'
            WHEN is_failed_action THEN 'FAILED'
            ELSE 'NORMAL'
        END AS event_type,
        service_name AS service,
        action_name AS action,
        COALESCE(
            request_params['tableName'],
            request_params['schemaName'],
            request_params['clusterName'],
            request_params['warehouseId'],
            request_params['jobId']
        ) AS target_resource,
        NOT is_failed_action AS success,
        source_ip_address AS source_ip
    FROM ${catalog}.${gold_schema}.fact_audit_logs
    WHERE event_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND (user_filter = 'ALL' OR user_identity_email = user_filter)
        AND (is_sensitive_action OR is_failed_action)
    ORDER BY event_time DESC
    LIMIT 1000;


-- -----------------------------------------------------------------------------
-- TVF 7: get_ip_address_analysis
-- Returns analysis of IP addresses for anomaly detection
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_ip_address_analysis(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE(
    source_ip STRING COMMENT 'Source IP address',
    unique_users INT COMMENT 'Number of unique users',
    user_list STRING COMMENT 'List of users',
    event_count INT COMMENT 'Total events',
    failed_events INT COMMENT 'Failed events',
    services_accessed STRING COMMENT 'Services accessed',
    first_seen TIMESTAMP COMMENT 'First activity',
    last_seen TIMESTAMP COMMENT 'Last activity',
    is_shared_ip BOOLEAN COMMENT 'True if multiple users'
)
COMMENT '
- PURPOSE: IP address analysis for shared account detection and suspicious IP identification
- BEST FOR: "Show IP address analysis" "Which IPs are used by multiple users?" "Shared accounts"
- NOT FOR: User-centric analysis (use get_user_activity_summary), activity patterns (use get_user_activity_patterns)
- RETURNS: IPs with unique users, user list, event count, failures, services, first/last seen, shared flag
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD)
- SYNTAX: SELECT * FROM TABLE(get_ip_address_analysis("2024-01-01", "2024-12-31"))
'
RETURN
    SELECT
        source_ip_address AS source_ip,
        COUNT(DISTINCT user_identity_email) AS unique_users,
        CONCAT_WS(', ', COLLECT_SET(user_identity_email)) AS user_list,
        COUNT(*) AS event_count,
        SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) AS failed_events,
        CONCAT_WS(', ', COLLECT_SET(service_name)) AS services_accessed,
        MIN(event_time) AS first_seen,
        MAX(event_time) AS last_seen,
        COUNT(DISTINCT user_identity_email) > 1 AS is_shared_ip
    FROM ${catalog}.${gold_schema}.fact_audit_logs
    WHERE event_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND source_ip_address IS NOT NULL
    GROUP BY source_ip_address
    ORDER BY unique_users DESC, event_count DESC;


-- -----------------------------------------------------------------------------
-- TVF 8: get_table_access_audit
-- Returns table access audit trail for compliance and lineage
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_table_access_audit(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    table_pattern STRING DEFAULT '%' COMMENT 'Table name pattern (use % for wildcards)'
)
RETURNS TABLE(
    event_date DATE COMMENT 'Date of access',
    table_full_name STRING COMMENT 'Full table name (catalog.schema.table)',
    access_type STRING COMMENT 'READ or WRITE',
    user_email STRING COMMENT 'User who accessed the table',
    entity_type STRING COMMENT 'JOB, NOTEBOOK, or QUERY',
    entity_id STRING COMMENT 'ID of the accessing entity',
    access_count INT COMMENT 'Number of accesses',
    first_access TIMESTAMP COMMENT 'First access time',
    last_access TIMESTAMP COMMENT 'Last access time'
)
COMMENT '
- PURPOSE: Table access audit trail for compliance, lineage tracking, and access pattern analysis
- BEST FOR: "Who accessed this table?" "Show table access history" "Data lineage audit"
- NOT FOR: Sensitive table monitoring (use get_sensitive_table_access), permission changes (use get_permission_changes)
- RETURNS: Table access with access type, user, entity type/ID, count, and first/last access times
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), table_pattern (SQL LIKE with % wildcards)
- SYNTAX: SELECT * FROM TABLE(get_table_access_audit("2024-01-01", "2024-12-31", "%customer%"))
'
RETURN
    WITH table_access AS (
        SELECT
            event_date,
            COALESCE(source_table_full_name, target_table_full_name) AS table_full_name,
            CASE
                WHEN target_table_full_name IS NOT NULL THEN 'WRITE'
                ELSE 'READ'
            END AS access_type,
            created_by AS user_email,
            entity_type,
            entity_id,
            event_time
        FROM ${catalog}.${gold_schema}.fact_table_lineage
        WHERE event_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND (source_table_full_name LIKE table_pattern OR target_table_full_name LIKE table_pattern)
    )
    SELECT
        event_date,
        table_full_name,
        access_type,
        user_email,
        entity_type,
        entity_id,
        COUNT(*) AS access_count,
        MIN(event_time) AS first_access,
        MAX(event_time) AS last_access
    FROM table_access
    WHERE table_full_name IS NOT NULL
    GROUP BY event_date, table_full_name, access_type, user_email, entity_type, entity_id
    ORDER BY event_date DESC, access_count DESC;


-- -----------------------------------------------------------------------------
-- TVF 9: get_user_activity_patterns
-- Returns temporal activity patterns with burst detection and user classification
-- Source: Audit Logs Security Dashboard patterns
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_user_activity_patterns(
    days_back INT DEFAULT 7 COMMENT 'Number of days to analyze',
    burst_threshold INT DEFAULT 50 COMMENT 'Events per hour threshold for burst detection',
    exclude_system_accounts BOOLEAN DEFAULT TRUE COMMENT 'Exclude system/service accounts'
)
RETURNS TABLE(
    user_email STRING COMMENT 'User email address',
    user_type STRING COMMENT 'HUMAN_USER, SERVICE_PRINCIPAL, SYSTEM, or PLATFORM',
    total_events BIGINT COMMENT 'Total events in period',
    active_days INT COMMENT 'Number of days with activity',
    avg_daily_events DOUBLE COMMENT 'Average events per active day',
    peak_hour INT COMMENT 'Hour with most activity (0-23)',
    peak_hour_events BIGINT COMMENT 'Events in peak hour',
    off_hours_pct DOUBLE COMMENT 'Percentage of events outside business hours',
    weekend_pct DOUBLE COMMENT 'Percentage of events on weekends',
    burst_count INT COMMENT 'Number of burst hours detected',
    unique_services INT COMMENT 'Unique services accessed',
    unique_ips INT COMMENT 'Unique IP addresses',
    failed_action_rate DOUBLE COMMENT 'Percentage of failed actions',
    activity_pattern STRING COMMENT 'NORMAL, AFTER_HOURS, BURSTY, or ANOMALOUS'
)
COMMENT '
- PURPOSE: Temporal activity pattern analysis with burst detection and anomaly classification
- BEST FOR: "Show user activity patterns" "Who has bursty activity?" "Anomalous user behavior"
- NOT FOR: Risk scoring (use get_user_activity_summary), service accounts (use get_service_account_audit)
- RETURNS: Users with activity pattern, burst count, off-hours %, weekend %, and classification
- PARAMS: days_back (default 7), burst_threshold (default 50 events/hour), exclude_system_accounts (default true)
- SYNTAX: SELECT * FROM TABLE(get_user_activity_patterns(7, 50, true))
- NOTE: Patterns: NORMAL, AFTER_HOURS, BURSTY, ANOMALOUS. Excludes system accounts by default.
'
RETURN
    WITH user_activity AS (
        SELECT
            user_identity_email AS user_email,
            -- Classify user type based on email pattern
            CASE
                -- System accounts (Databricks internal)
                WHEN user_identity_email LIKE '%@databricks.com'
                     AND user_identity_email LIKE 'System-%' THEN 'SYSTEM'
                WHEN user_identity_email LIKE 'system-%' THEN 'SYSTEM'
                -- Platform accounts (automated)
                WHEN user_identity_email IN ('Unity Catalog', 'Delta Sharing', 'Catalog', 'Schema') THEN 'PLATFORM'
                WHEN user_identity_email LIKE 'DBX_%' THEN 'PLATFORM'
                -- Service principals (apps)
                WHEN user_identity_email LIKE '%@%.iam.gserviceaccount.com' THEN 'SERVICE_PRINCIPAL'
                WHEN user_identity_email LIKE '%spn@%' THEN 'SERVICE_PRINCIPAL'
                WHEN user_identity_email NOT LIKE '%@%' THEN 'SERVICE_PRINCIPAL'
                -- Human users (everyone else with @ sign)
                ELSE 'HUMAN_USER'
            END AS user_type,
            event_date,
            HOUR(event_time) AS event_hour,
            DAYOFWEEK(event_date) AS day_of_week,
            is_failed_action,
            service_name,
            source_ip_address
        FROM ${catalog}.${gold_schema}.fact_audit_logs
        WHERE event_date >= CURRENT_DATE() - INTERVAL days_back DAY
            AND user_identity_email IS NOT NULL
    ),
    -- Calculate hourly activity for burst detection
    hourly_activity AS (
        SELECT
            user_email,
            user_type,
            event_date,
            event_hour,
            COUNT(*) AS hourly_events
        FROM user_activity
        GROUP BY user_email, user_type, event_date, event_hour
    ),
    -- Aggregate user metrics
    user_metrics AS (
        SELECT
            ua.user_email,
            ua.user_type,
            COUNT(*) AS total_events,
            COUNT(DISTINCT ua.event_date) AS active_days,
            COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT ua.event_date), 0) AS avg_daily_events,
            -- Peak hour analysis
            FIRST_VALUE(ua.event_hour) OVER (
                PARTITION BY ua.user_email
                ORDER BY COUNT(*) DESC
            ) AS peak_hour,
            -- Off-hours: before 7am or after 7pm
            SUM(CASE WHEN ua.event_hour < 7 OR ua.event_hour >= 19 THEN 1 ELSE 0 END) * 100.0 /
                NULLIF(COUNT(*), 0) AS off_hours_pct,
            -- Weekend activity
            SUM(CASE WHEN ua.day_of_week IN (1, 7) THEN 1 ELSE 0 END) * 100.0 /
                NULLIF(COUNT(*), 0) AS weekend_pct,
            COUNT(DISTINCT ua.service_name) AS unique_services,
            COUNT(DISTINCT ua.source_ip_address) AS unique_ips,
            SUM(CASE WHEN ua.is_failed_action THEN 1 ELSE 0 END) * 100.0 /
                NULLIF(COUNT(*), 0) AS failed_action_rate
        FROM user_activity ua
        GROUP BY ua.user_email, ua.user_type
    ),
    -- Count burst hours per user
    burst_counts AS (
        SELECT
            user_email,
            COUNT(*) AS burst_count,
            MAX(hourly_events) AS peak_hour_events
        FROM hourly_activity
        WHERE hourly_events >= burst_threshold
        GROUP BY user_email
    ),
    -- Combine all metrics
    final_metrics AS (
        SELECT
            um.user_email,
            um.user_type,
            um.total_events,
            um.active_days,
            um.avg_daily_events,
            um.peak_hour,
            COALESCE(bc.peak_hour_events, 0) AS peak_hour_events,
            um.off_hours_pct,
            um.weekend_pct,
            COALESCE(bc.burst_count, 0) AS burst_count,
            um.unique_services,
            um.unique_ips,
            um.failed_action_rate,
            -- Classify activity pattern
            CASE
                WHEN bc.burst_count >= 3 AND um.off_hours_pct > 30 THEN 'ANOMALOUS'
                WHEN bc.burst_count >= 3 THEN 'BURSTY'
                WHEN um.off_hours_pct > 50 THEN 'AFTER_HOURS'
                ELSE 'NORMAL'
            END AS activity_pattern
        FROM user_metrics um
        LEFT JOIN burst_counts bc ON um.user_email = bc.user_email
    )
    SELECT *
    FROM final_metrics
    WHERE (NOT exclude_system_accounts OR user_type NOT IN ('SYSTEM', 'PLATFORM'))
    ORDER BY
        CASE activity_pattern
            WHEN 'ANOMALOUS' THEN 1
            WHEN 'BURSTY' THEN 2
            WHEN 'AFTER_HOURS' THEN 3
            ELSE 4
        END,
        total_events DESC;


-- -----------------------------------------------------------------------------
-- TVF 10: get_service_account_audit
-- Returns service principal and system account activity for security review
-- Source: Audit logs repo system account filtering pattern
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_service_account_audit(
    days_back INT DEFAULT 7 COMMENT 'Number of days to analyze'
)
RETURNS TABLE(
    account_email STRING COMMENT 'Service account email',
    account_type STRING COMMENT 'SERVICE_PRINCIPAL, SYSTEM, or PLATFORM',
    total_events BIGINT COMMENT 'Total events',
    unique_actions INT COMMENT 'Unique actions performed',
    unique_services INT COMMENT 'Services accessed',
    failed_events BIGINT COMMENT 'Failed action count',
    failure_rate DOUBLE COMMENT 'Percentage of failed actions',
    unique_ips INT COMMENT 'Unique source IPs',
    sensitive_events BIGINT COMMENT 'Sensitive action count',
    first_activity TIMESTAMP COMMENT 'First event in period',
    last_activity TIMESTAMP COMMENT 'Last event in period',
    risk_level STRING COMMENT 'HIGH, MEDIUM, or LOW'
)
COMMENT '
- PURPOSE: Service account audit for reviewing automated activity and detecting compromised accounts
- BEST FOR: "Show service account activity" "Which service principals are most active?" "Automated account audit"
- NOT FOR: Human user activity (use get_user_activity_summary), activity patterns (use get_user_activity_patterns)
- RETURNS: Service accounts with type, events, failures, failure rate, IPs, sensitive actions, and risk level
- PARAMS: days_back (default 7)
- SYNTAX: SELECT * FROM TABLE(get_service_account_audit(7))
- NOTE: Risk levels: HIGH (>20% failure or >100 sensitive), MEDIUM (>10 IPs or >10 failures), LOW
'
RETURN
    WITH service_accounts AS (
        SELECT
            user_identity_email AS account_email,
            CASE
                WHEN user_identity_email LIKE '%@databricks.com'
                     AND user_identity_email LIKE 'System-%' THEN 'SYSTEM'
                WHEN user_identity_email LIKE 'system-%' THEN 'SYSTEM'
                WHEN user_identity_email IN ('Unity Catalog', 'Delta Sharing', 'Catalog', 'Schema') THEN 'PLATFORM'
                WHEN user_identity_email LIKE 'DBX_%' THEN 'PLATFORM'
                WHEN user_identity_email LIKE '%@%.iam.gserviceaccount.com' THEN 'SERVICE_PRINCIPAL'
                WHEN user_identity_email LIKE '%spn@%' THEN 'SERVICE_PRINCIPAL'
                WHEN user_identity_email NOT LIKE '%@%' THEN 'SERVICE_PRINCIPAL'
                ELSE NULL  -- Human users, exclude
            END AS account_type,
            event_time,
            action_name,
            service_name,
            source_ip_address,
            is_failed_action,
            is_sensitive_action
        FROM ${catalog}.${gold_schema}.fact_audit_logs
        WHERE event_date >= CURRENT_DATE() - INTERVAL days_back DAY
            AND user_identity_email IS NOT NULL
    )
    SELECT
        account_email,
        account_type,
        COUNT(*) AS total_events,
        COUNT(DISTINCT action_name) AS unique_actions,
        COUNT(DISTINCT service_name) AS unique_services,
        SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) AS failed_events,
        SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0) AS failure_rate,
        COUNT(DISTINCT source_ip_address) AS unique_ips,
        SUM(CASE WHEN is_sensitive_action THEN 1 ELSE 0 END) AS sensitive_events,
        MIN(event_time) AS first_activity,
        MAX(event_time) AS last_activity,
        CASE
            -- High risk: high failure rate or many sensitive actions from non-Databricks IPs
            WHEN SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0) > 20 THEN 'HIGH'
            WHEN SUM(CASE WHEN is_sensitive_action THEN 1 ELSE 0 END) > 100 THEN 'HIGH'
            WHEN COUNT(DISTINCT source_ip_address) > 10 THEN 'MEDIUM'
            WHEN SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) > 10 THEN 'MEDIUM'
            ELSE 'LOW'
        END AS risk_level
    FROM service_accounts
    WHERE account_type IS NOT NULL  -- Only service accounts
    GROUP BY account_email, account_type
    ORDER BY
        CASE risk_level WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END,
        total_events DESC;
