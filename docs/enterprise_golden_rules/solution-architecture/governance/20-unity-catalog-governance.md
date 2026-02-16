# Unity Catalog Governance Best Practices

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | SA-GOV-001 |
| **Version** | 1.0 |
| **Last Updated** | February 2026 |
| **Owner** | Platform Team |
| **Status** | Approved |

### Version History
| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Feb 2026 | Initial compilation from official Databricks documentation |

### Source References
| Source | URL |
|--------|-----|
| Unity Catalog Best Practices | https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html |
| Manage Users and Groups | https://docs.databricks.com/en/admin/users-groups/ |
| Manage Privileges | https://docs.databricks.com/en/data-governance/unity-catalog/manage-privileges/ |

---

## Executive Summary

This document consolidates official Unity Catalog governance best practices from Databricks documentation. These patterns cover identity management, privilege assignment, admin roles, storage configuration, and data isolation strategies.

> **Key Principle:** Use Unity Catalog as your centralized governance layer. Manage identities through your IdP with SCIM, assign privileges to groups (not individuals), and use managed tables for full governance benefits.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| BP-08 | Use service principals for production jobs | 🟡 Required |
| BP-09 | Assign ownership to groups, not individuals | 🟡 Required |
| GOV-01 | Provision identities at account level via SCIM | 🔴 Critical |
| GOV-02 | Define groups in your IdP | 🔴 Critical |
| GOV-03 | Sparingly assign admin roles | 🟡 Required |
| GOV-04 | Use catalog-level managed storage | 🟡 Required |
| GOV-05 | Prefer managed tables over external | 🟡 Required |

---

## Identity Management

### GOV-01: Provision Identities at Account Level via SCIM (Critical)

> **Official Recommendation:** "Principals (users, groups, and service principals) must be defined at the Databricks account level in order to be assigned privileges on Unity Catalog securable objects. Databricks recommends that you use SCIM to provision principals to your Databricks account from your IdP." — [Databricks Docs](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)

### Identity Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    IDENTITY PROVIDER (IdP)                   │
│                (Okta, Azure AD, Google, etc.)               │
├─────────────────────────────────────────────────────────────┤
│                              │                               │
│                     SCIM Provisioning                        │
│                     (Account Level)                          │
│                              ▼                               │
│              ┌───────────────────────────────┐              │
│              │   DATABRICKS ACCOUNT LEVEL    │              │
│              │   ├── Users                   │              │
│              │   ├── Groups                  │              │
│              │   └── Service Principals      │              │
│              └───────────────────────────────┘              │
│                              │                               │
│                    Automatic Sync                            │
│                              ▼                               │
│              ┌───────────────────────────────┐              │
│              │     WORKSPACE LEVEL           │              │
│              │  (Workspace access assigned)  │              │
│              └───────────────────────────────┘              │
│                              │                               │
│                    Unity Catalog                             │
│                              ▼                               │
│              ┌───────────────────────────────┐              │
│              │   SECURABLE OBJECTS           │              │
│              │   ├── Catalogs                │              │
│              │   ├── Schemas                 │              │
│              │   └── Tables/Views/Functions  │              │
│              └───────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### Best Practices for Identities

| Do | Don't |
|----|-------|
| ✅ Provision at account level via SCIM | ❌ Use workspace-level SCIM provisioning |
| ✅ Define groups in your IdP | ❌ Create groups directly in Databricks |
| ✅ Use consistent organizational groups | ❌ Add users manually to account/workspace |
| ✅ Migrate workspace-local groups to account | ❌ Modify groups in Databricks (use IdP) |

---

### GOV-02: Define Groups in Your IdP (Critical)

> **Official Recommendation:** "Define and manage groups in your IdP. They should be consistent with your organizational group definitions." — [Databricks Docs](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)

### Group Strategy

```
IdP Groups → SCIM → Databricks Account Groups
                           │
                           ▼
              ┌───────────────────────────┐
              │     RECOMMENDED GROUPS    │
              ├───────────────────────────┤
              │ data-platform-admins      │ ◄── Account admins
              │ data-engineers            │ ◄── Bronze/Silver developers
              │ analytics-engineers       │ ◄── Gold/Semantic developers
              │ data-scientists           │ ◄── ML/experimentation
              │ business-analysts         │ ◄── Read-only Gold access
              │ etl-service-principals    │ ◄── Production jobs
              └───────────────────────────┘
```

### Group Migration

> **Official Recommendation:** "Groups behave differently than users and service principals. Although users and service principals that you add to a workspace are automatically synchronized with your Databricks account, workspace-level groups are not. If you have workspace-local groups, you should manually migrate them to the account." — [Databricks Docs](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)

```sql
-- Check for workspace-local groups
SELECT * FROM system.access.group_memberships
WHERE is_account_group = false;

-- Migration steps:
-- 1. Replicate groups in IdP
-- 2. Configure SCIM provisioning to account
-- 3. Verify groups appear at account level
-- 4. Reassign privileges from workspace groups to account groups
```

---

## BP-08: Use Service Principals for Production Jobs (Required)

> **Official Recommendation:** "Use service principals to run jobs. Service principals enable job automation. If you use users to run jobs that write into production, you risk overwriting production data by accident." — [Databricks Docs](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)

### Why Service Principals

| Aspect | User-Based Jobs | Service Principal Jobs |
|--------|-----------------|------------------------|
| **Accident risk** | High (user has broad access) | Low (scoped permissions) |
| **Audit trail** | User identity | Clear automation identity |
| **Password rotation** | Complex | Token-based, manageable |
| **Consistency** | Varies by user | Always consistent |
| **Offboarding** | Jobs break when user leaves | Jobs continue running |

### Implementation

```yaml
# Asset Bundle - Service Principal for production
resources:
  jobs:
    production_etl:
      name: "[${bundle.target}] Production ETL"
      
      # ✅ CRITICAL: Run as service principal
      run_as:
        service_principal_name: "etl-service-principal"
      
      tasks:
        - task_key: load_gold
          notebook_task:
            notebook_path: ../src/gold/load.py
```

### Service Principal Permissions

```sql
-- Grant service principal access to production schema
GRANT USE CATALOG ON CATALOG production_catalog 
TO `etl-service-principal`;

GRANT USE SCHEMA ON SCHEMA production_catalog.gold 
TO `etl-service-principal`;

GRANT SELECT, MODIFY ON SCHEMA production_catalog.gold 
TO `etl-service-principal`;

-- Users get read-only access
GRANT SELECT ON SCHEMA production_catalog.gold 
TO `business-analysts`;
```

---

## BP-09: Assign Ownership to Groups (Required)

> **Official Recommendation:** "Use groups to assign ownership to most securable objects. Avoid direct grants to users whenever possible." — [Databricks Docs](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)

### Why Group Ownership

| Aspect | Individual Ownership | Group Ownership |
|--------|---------------------|-----------------|
| **Continuity** | Lost when user leaves | Persists through turnover |
| **Collaboration** | Single point of control | Team can manage |
| **Scalability** | Doesn't scale | Scales with organization |
| **Auditability** | Harder to track | Clear team responsibility |

### Implementation

```sql
-- ✅ CORRECT: Group ownership for catalogs
ALTER CATALOG production_catalog 
SET OWNER TO `data-platform-admins`;

-- ✅ CORRECT: Group ownership for schemas
ALTER SCHEMA production_catalog.gold 
SET OWNER TO `analytics-engineers`;

-- ✅ CORRECT: Group ownership for tables
ALTER TABLE production_catalog.gold.fact_sales 
SET OWNER TO `analytics-engineers`;

-- ❌ WRONG: Individual ownership
ALTER TABLE production_catalog.gold.fact_sales 
SET OWNER TO `john.doe@company.com`;
```

### Ownership Assignment Pattern

```
Catalog Level:       data-platform-admins (infrastructure team)
    │
    ├── Bronze Schema:   data-engineers
    │       └── Tables:  data-engineers
    │
    ├── Silver Schema:   data-engineers
    │       └── Tables:  data-engineers
    │
    └── Gold Schema:     analytics-engineers
            └── Tables:  analytics-engineers
```

---

## GOV-03: Sparingly Assign Admin Roles (Required)

> **Official Recommendation:** "Assigning admin roles and powerful privileges like ALL PRIVILEGES and MANAGE requires care... Assign these roles to groups whenever possible. Metastore admins are optional. Assign them only if you need them." — [Databricks Docs](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)

### Admin Role Hierarchy

| Role | Scope | Recommendation |
|------|-------|----------------|
| **Account Admin** | Entire account | Very few (2-3 max) |
| **Workspace Admin** | Single workspace | Limited per workspace |
| **Metastore Admin** | Unity Catalog metastore | Optional, only if needed |
| **Catalog Owner** | Single catalog | Team groups |
| **Schema Owner** | Single schema | Team groups |

### Dangerous Privileges

| Privilege | Risk | Guidance |
|-----------|------|----------|
| `ALL PRIVILEGES` | Full access to object | Avoid; use specific grants |
| `MANAGE` | Can grant to others | Catalog/schema owners only |
| `CREATE CATALOG` | Can create catalogs | Platform admins only |
| `CREATE EXTERNAL LOCATION` | Storage access | Infrastructure admins only |

### Implementation

```sql
-- ✅ CORRECT: Specific grants
GRANT USE CATALOG ON CATALOG production_catalog TO `data-engineers`;
GRANT USE SCHEMA ON SCHEMA production_catalog.silver TO `data-engineers`;
GRANT SELECT, MODIFY ON SCHEMA production_catalog.silver TO `data-engineers`;

-- ❌ WRONG: Overly broad grants
GRANT ALL PRIVILEGES ON CATALOG production_catalog TO `data-engineers`;
```

---

## Privilege Assignment

### USE CATALOG and USE SCHEMA

> **Official Recommendation:** "USE CATALOG | SCHEMA grants the ability to view data in the catalog or schema. Alone, these privileges do not grant SELECT or READ on the objects inside the catalog or schema, but they are a prerequisite to granting users that access." — [Databricks Docs](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)

### Privilege Hierarchy

```
USE CATALOG ──────────────► Required to see catalog exists
       │
       └──► USE SCHEMA ──────► Required to see schema exists
                  │
                  └──► SELECT ──────► Required to read data
                  │
                  └──► MODIFY ──────► Required to write data
                  │
                  └──► CREATE ──────► Required to create objects
```

### Privilege Matrix by Role

| Role | USE CATALOG | USE SCHEMA | SELECT | MODIFY | CREATE |
|------|-------------|------------|--------|--------|--------|
| **Platform Admins** | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All |
| **Data Engineers** | ✅ All | ✅ Bronze/Silver | ✅ Bronze/Silver | ✅ Bronze/Silver | ✅ Bronze/Silver |
| **Analytics Engineers** | ✅ All | ✅ Silver/Gold | ✅ Silver/Gold | ✅ Gold | ✅ Gold |
| **Data Scientists** | ✅ All | ✅ Gold/Sandbox | ✅ Gold | ❌ (Sandbox only) | ✅ Sandbox |
| **Business Analysts** | ✅ All | ✅ Gold only | ✅ Gold only | ❌ | ❌ |
| **Service Principals** | ✅ Target | ✅ Target | ✅ Target | ✅ Target | ✅ Target |

### BROWSE Privilege for Discovery

> **Official Recommendation:** "BROWSE allows users to view metadata for objects in a catalog using Catalog Explorer... Databricks recommends granting BROWSE on catalogs to the All account users group at the catalog level to make data discoverable and support access requests." — [Databricks Docs](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)

```sql
-- ✅ Enable data discovery for all users
GRANT BROWSE ON CATALOG production_catalog 
TO `all-account-users`;

-- Users can:
-- ✓ See catalog in Catalog Explorer
-- ✓ View table metadata (schema, comments)
-- ✓ Request access to tables
-- ✗ Cannot read actual data without USE + SELECT
```

---

## GOV-04: Use Catalog-Level Managed Storage (Required)

> **Official Recommendation:** "Give preference to catalog-level storage as your primary unit of data isolation. Metastore-level storage was required in early Unity Catalog environments but is no longer required." — [Databricks Docs](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)

### Storage Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    STORAGE HIERARCHY                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Metastore Level (❌ NOT RECOMMENDED)                      │
│   └── s3://company-metastore-storage/                       │
│       └── Shared across all catalogs                        │
│                                                             │
│   Catalog Level (✅ RECOMMENDED)                            │
│   ├── production:   s3://prod-data/                         │
│   ├── development:  s3://dev-data/                          │
│   └── sandbox:      s3://sandbox-data/                      │
│                                                             │
│   Schema Level (When Additional Isolation Needed)           │
│   └── sensitive:    s3://sensitive-data/                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Implementation

```sql
-- Create catalog with dedicated storage
CREATE CATALOG production_catalog
MANAGED LOCATION 's3://company-production-data/unity-catalog/';

-- Create catalog for development (separate storage)
CREATE CATALOG development_catalog
MANAGED LOCATION 's3://company-dev-data/unity-catalog/';

-- Schema-level storage (if needed for sensitive data)
CREATE SCHEMA production_catalog.pii_data
MANAGED LOCATION 's3://company-pii-data/unity-catalog/pii/';
```

### Storage Security

> **Official Recommendation:** "Do not use a bucket that can be accessed from outside of Unity Catalog. If an external service or principal accesses data in the managed storage location, bypassing Unity Catalog, access control and auditability on managed tables and volumes are compromised." — [Databricks Docs](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)

| Do | Don't |
|----|-------|
| ✅ Dedicated buckets for UC | ❌ Reuse DBFS root bucket |
| ✅ Restrict IAM to Databricks only | ❌ Allow external service access |
| ✅ Separate buckets per catalog | ❌ Single bucket for all data |

---

## GOV-05: Prefer Managed Tables Over External (Required)

> **Official Recommendation:** "Databricks recommends managed tables and volumes because they allow you to take full advantage of Unity Catalog governance capabilities and performance optimizations." — [Databricks Docs](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)

### Managed vs External Tables

| Feature | Managed Tables | External Tables |
|---------|----------------|-----------------|
| **Governance** | Full UC control | Limited |
| **Auto compaction** | ✅ Yes | ❌ No |
| **Auto optimize** | ✅ Yes | ❌ No |
| **Metadata caching** | ✅ Yes | ❌ No |
| **File optimization** | ✅ Yes | ❌ No |
| **Lifecycle** | UC managed | User managed |

### When to Use External Tables

| Scenario | Table Type |
|----------|------------|
| All new tables | ✅ Managed |
| Migrating from Hive metastore | External (temporary) |
| DR requirements not met by managed | External |
| External readers/writers required | External |
| Non-Delta/non-Iceberg formats | External |

### Migration Path

```sql
-- Check for external tables
SELECT table_name, table_type, storage_location
FROM system.information_schema.tables
WHERE table_type = 'EXTERNAL';

-- Convert external to managed (Delta tables)
-- 1. Create new managed table
CREATE TABLE catalog.schema.my_table_managed
AS SELECT * FROM catalog.schema.my_table_external;

-- 2. Verify data
SELECT COUNT(*) FROM catalog.schema.my_table_managed;

-- 3. Drop external table
DROP TABLE catalog.schema.my_table_external;

-- 4. Rename managed table
ALTER TABLE catalog.schema.my_table_managed 
RENAME TO my_table;
```

---

## External Locations

> **Official Recommendation:** "External location securable objects, by combining storage credentials and storage paths, provide strong control and auditability of storage access. It is important to prevent users from accessing the buckets registered as external locations directly." — [Databricks Docs](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)

### External Location Best Practices

| Do | Don't |
|----|-------|
| ✅ Limit number of users with direct bucket access | ❌ Grant `READ FILES` to end users |
| ✅ Grant `CREATE EXTERNAL LOCATION` to admins only | ❌ Grant `WRITE FILES` (rare use cases) |
| ✅ Use volumes for file access | ❌ Create tables at external location root |
| ✅ Create one external location per schema | ❌ Allow path overlaps |

### External Location Usage

```sql
-- ✅ CORRECT: Create external location for landing zone
CREATE EXTERNAL LOCATION landing_zone
URL 's3://company-landing-zone/'
WITH (STORAGE CREDENTIAL landing_cred);

-- Grant to data engineers only
GRANT CREATE EXTERNAL TABLE ON EXTERNAL LOCATION landing_zone
TO `data-engineers`;

-- ❌ WRONG: Granting file access to end users
-- GRANT READ FILES ON EXTERNAL LOCATION landing_zone TO `all-users`;
```

---

## Cross-Region Sharing

> **Official Recommendation:** "You can have only one metastore per region. If you want to share data between workspaces on different regions, use Databricks-to-Databricks Delta Sharing." — [Databricks Docs](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)

### Delta Sharing Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CROSS-REGION SHARING                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Region A (us-east-1)          Region B (eu-west-1)       │
│   ┌─────────────────┐           ┌─────────────────┐        │
│   │   Metastore A   │           │   Metastore B   │        │
│   │   ├── Catalog   │           │   ├── Catalog   │        │
│   │   └── Tables    │           │   └── Tables    │        │
│   └────────┬────────┘           └────────┬────────┘        │
│            │                              │                 │
│            └──── Delta Sharing ───────────┘                │
│                 (Databricks-to-Databricks)                 │
│                                                             │
│   ⚠️ Limitations:                                          │
│   • Lineage doesn't cross region boundaries                │
│   • Privileges don't transfer with shares                  │
│   • Egress charges apply                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Important Limitation

> **Official Recommendation:** "Do not register frequently accessed tables as external tables in more than one metastore. If you do, changes to the schema, table properties, comments, and other metadata that occur as a result of writes to metastore A will not register at all with metastore B." — [Databricks Docs](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)

---

## Validation Checklist

### Identity Management
- [ ] SCIM provisioning configured at account level (GOV-01)
- [ ] Groups defined and managed in IdP (GOV-02)
- [ ] Workspace-level groups migrated to account level
- [ ] No manual user additions in Databricks

### Ownership & Privileges
- [ ] Service principals used for production jobs (BP-08)
- [ ] Ownership assigned to groups, not individuals (BP-09)
- [ ] Admin roles assigned sparingly (GOV-03)
- [ ] ALL PRIVILEGES avoided; specific grants used
- [ ] BROWSE granted for discoverability

### Storage
- [ ] Catalog-level managed storage configured (GOV-04)
- [ ] No metastore-level storage (unless legacy)
- [ ] Managed tables preferred over external (GOV-05)
- [ ] External locations restricted to admins

### Security
- [ ] Storage buckets not accessible outside UC
- [ ] READ FILES / WRITE FILES not granted to end users
- [ ] Cross-region sharing via Delta Sharing only

---

## Quick Reference

```sql
-- Grant catalog access to group
GRANT USE CATALOG ON CATALOG my_catalog TO `team-name`;

-- Grant schema access with read
GRANT USE SCHEMA ON SCHEMA my_catalog.my_schema TO `team-name`;
GRANT SELECT ON SCHEMA my_catalog.my_schema TO `team-name`;

-- Grant schema access with write
GRANT MODIFY ON SCHEMA my_catalog.my_schema TO `team-name`;

-- Transfer ownership to group
ALTER CATALOG my_catalog SET OWNER TO `platform-admins`;
ALTER SCHEMA my_catalog.gold SET OWNER TO `analytics-engineers`;
ALTER TABLE my_catalog.gold.fact_sales SET OWNER TO `analytics-engineers`;

-- Enable discovery
GRANT BROWSE ON CATALOG my_catalog TO `all-account-users`;

-- Check privileges
SHOW GRANTS ON CATALOG my_catalog;
SHOW GRANTS TO `team-name`;
```

---

## References

- [Unity Catalog Best Practices](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)
- [Manage Users, Service Principals, and Groups](https://docs.databricks.com/en/admin/users-groups/)
- [Sync Users and Groups via SCIM](https://docs.databricks.com/en/admin/users-groups/scim/)
- [Manage Privileges in Unity Catalog](https://docs.databricks.com/en/data-governance/unity-catalog/manage-privileges/)
- [Admin Privileges in Unity Catalog](https://docs.databricks.com/en/data-governance/unity-catalog/manage-privileges/admin-privileges)
- [Delta Sharing](https://docs.databricks.com/en/delta-sharing/)
