# Security Domain ERD

## Overview
Access control, auditing, and network access tracking.

## Tables
- `fact_audit_logs` - Security audit trail
- `fact_assistant_events` - AI assistant usage
- `fact_clean_room_events` - Clean room activity
- `fact_inbound_network` - Inbound access denial events
- `fact_outbound_network` - Outbound access denial events

## Entity Relationship Diagram

```mermaid
erDiagram
    dim_workspace ||--o{ fact_audit_logs : "workspace_id"
    dim_workspace ||--o{ fact_assistant_events : "workspace_id"
    dim_workspace ||--o{ fact_clean_room_events : "workspace_id"
    dim_workspace ||--o{ fact_inbound_network : "workspace_id"
    dim_workspace ||--o{ fact_outbound_network : "workspace_id"

    dim_workspace {
        STRING workspace_id PK
        STRING workspace_name
    }

    fact_audit_logs {
        STRING workspace_id PK
        STRING request_id PK
        STRING action_name
        STRING service_name
        STRING user_identity
        TIMESTAMP event_time
        STRING source_ip_address
        STRING response_status_code
    }

    fact_assistant_events {
        STRING workspace_id PK
        STRING request_id PK
        STRING event_type
        STRING user_id
        TIMESTAMP event_time
    }

    fact_clean_room_events {
        STRING workspace_id PK
        STRING event_id PK
        STRING clean_room_name
        STRING event_type
        TIMESTAMP event_time
    }

    fact_inbound_network {
        STRING workspace_id PK
        STRING denied_entity_id PK
        TIMESTAMP event_time PK
        STRING source_ip
        STRING denied_resource
    }

    fact_outbound_network {
        STRING workspace_id PK
        STRING denied_entity_id PK
        TIMESTAMP event_time PK
        STRING dest_host
        STRING dest_port
    }
```

## Key Relationships

| From | To | Cardinality | FK Columns |
|------|-----|-------------|------------|
| dim_workspace | fact_audit_logs | 1:N | workspace_id |
| dim_workspace | fact_assistant_events | 1:N | workspace_id |
| dim_workspace | fact_clean_room_events | 1:N | workspace_id |
| dim_workspace | fact_inbound_network | 1:N | workspace_id |
| dim_workspace | fact_outbound_network | 1:N | workspace_id |

