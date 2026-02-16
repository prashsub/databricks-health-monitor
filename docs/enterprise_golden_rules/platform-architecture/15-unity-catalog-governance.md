# Unity Catalog Governance

> **Document Owner:** Platform Team | **Status:** Approved | **Last Updated:** February 2026

## Overview

Unity Catalog provides centralized governance for data and AI assets. This document defines the mandatory patterns for identity management, privilege assignment, and storage configuration.

---

## Golden Rules

| ID | Rule | Severity |
|----|------|----------|
| **GOV-01** | Provision identities at account level via SCIM | Critical |
| **GOV-02** | Define and manage groups in your identity provider | Critical |
| **GOV-03** | Assign admin roles sparingly; avoid ALL PRIVILEGES | Required |
| **GOV-04** | Use catalog-level managed storage for data isolation | Required |
| **GOV-05** | Prefer managed tables over external tables | Required |
| **GOV-06** | Use service principals for production jobs | Required |
| **GOV-07** | Assign object ownership to groups, not individuals | Required |

---

## GOV-01: Provision Identities via SCIM

### Rule
All users, groups, and service principals must be provisioned at the Databricks **account level** via SCIM from your identity provider.

### Why It Matters
- Ensures consistent identity management across all workspaces
- Enables unified access control for Unity Catalog objects
- Simplifies onboarding/offboarding through IdP automation

### Implementation
```
Identity Provider (Okta, Azure AD, etc.)
    │
    └── SCIM Provisioning ──► Databricks Account
                                   │
                                   └── Automatic Sync to Workspaces
```

### Common Mistakes
| ❌ Don't | ✅ Do |
|----------|-------|
| Add users manually in Databricks | Provision through IdP with SCIM |
| Use workspace-level SCIM | Use account-level SCIM |

---

## GOV-02: Manage Groups in Identity Provider

### Rule
All groups must be created and managed in your identity provider, then synced to Databricks via SCIM.

### Why It Matters
- Single source of truth for organizational structure
- Changes propagate automatically across all Databricks resources
- Maintains consistency with enterprise identity governance

### Recommended Groups
| Group | Purpose |
|-------|---------|
| `data-platform-admins` | Infrastructure and account management |
| `data-engineers` | Bronze/Silver pipeline development |
| `analytics-engineers` | Gold layer and semantic development |
| `data-scientists` | ML and experimentation |
| `business-analysts` | Read-only access to Gold layer |

### Migration Note
Workspace-local groups do not sync automatically. Migrate them to account-level groups through your IdP.

---

## GOV-03: Limit Admin Roles

### Rule
Assign admin roles (`account admin`, `metastore admin`) sparingly. Avoid granting `ALL PRIVILEGES` or `MANAGE` permissions.

### Why It Matters
- Reduces risk of accidental data exposure or deletion
- Follows least-privilege security principle
- Simplifies audit and compliance

### Privilege Strategy
```sql
-- ✅ CORRECT: Specific grants
GRANT USE CATALOG ON CATALOG prod_catalog TO `data-engineers`;
GRANT SELECT ON SCHEMA prod_catalog.gold TO `business-analysts`;

-- ❌ WRONG: Overly broad
GRANT ALL PRIVILEGES ON CATALOG prod_catalog TO `data-engineers`;
```

### Admin Role Limits
| Role | Recommendation |
|------|----------------|
| Account Admin | 2-3 people maximum |
| Metastore Admin | Only if required; optional |
| Catalog Owner | Team groups only |

---

## GOV-04: Catalog-Level Storage

### Rule
Configure managed storage at the **catalog level** as the primary unit of data isolation.

### Why It Matters
- Provides clear data isolation boundaries
- Simplifies storage security management
- Enables environment-specific storage policies

### Implementation
```sql
-- Create catalog with dedicated storage
CREATE CATALOG production_catalog
MANAGED LOCATION 's3://prod-data/unity-catalog/';

-- Separate storage for development
CREATE CATALOG development_catalog
MANAGED LOCATION 's3://dev-data/unity-catalog/';
```

### Storage Security
- Never reuse DBFS root bucket for managed storage
- Restrict IAM access to Databricks only
- Do not allow external service access to managed storage locations

---

## GOV-05: Prefer Managed Tables

### Rule
Use Unity Catalog managed tables for all new tables. External tables require documented justification.

### Why It Matters
| Feature | Managed | External |
|---------|---------|----------|
| Auto compaction | ✅ | ❌ |
| Auto optimize | ✅ | ❌ |
| Full governance | ✅ | Limited |
| File lifecycle | Automatic | Manual |

### When External Tables Are Acceptable
- Migrating from Hive metastore (temporary)
- Disaster recovery requirements not met by managed
- External readers/writers required

---

## GOV-06: Service Principals for Production

### Rule
All production jobs must run as service principals, not individual users.

### Why It Matters
- Eliminates dependency on individual user accounts
- Reduces accidental overwrites of production data
- Provides clear audit trail for automated processes
- Jobs continue running when employees leave

### Implementation
```yaml
# In Asset Bundle
resources:
  jobs:
    production_etl:
      run_as:
        service_principal_name: "etl-service-principal"
```

---

## GOV-07: Group Ownership

### Rule
Assign ownership of catalogs, schemas, and tables to groups—never to individual users.

### Why It Matters
- Ownership persists through employee turnover
- Enables team collaboration on data assets
- Scales with organizational growth

### Implementation
```sql
-- Correct: Group ownership
ALTER CATALOG production SET OWNER TO `data-platform-admins`;
ALTER SCHEMA production.gold SET OWNER TO `analytics-engineers`;

-- Wrong: Individual ownership (avoid)
-- ALTER TABLE prod.gold.sales SET OWNER TO `john@company.com`;
```

---

## Privilege Assignment Quick Reference

### Required Privileges by Role

| Role | USE CATALOG | USE SCHEMA | SELECT | MODIFY |
|------|-------------|------------|--------|--------|
| Platform Admins | All | All | All | All |
| Data Engineers | All | Bronze/Silver | Bronze/Silver | Bronze/Silver |
| Analytics Engineers | All | Silver/Gold | Silver/Gold | Gold |
| Business Analysts | All | Gold only | Gold only | None |

### Enable Data Discovery
```sql
-- Allow all users to browse catalog metadata
GRANT BROWSE ON CATALOG production TO `all-account-users`;
```

---

## Validation Checklist

### Identity Management
- [ ] SCIM provisioning configured at account level
- [ ] Groups defined and managed in IdP
- [ ] No workspace-local groups in use

### Privileges
- [ ] Service principals used for production jobs
- [ ] Ownership assigned to groups
- [ ] No ALL PRIVILEGES grants
- [ ] BROWSE granted for discoverability

### Storage
- [ ] Catalog-level managed storage configured
- [ ] Managed tables used (external tables documented)
- [ ] Storage buckets not accessible outside Unity Catalog

---

## References

- [Unity Catalog Best Practices](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)
- [Manage Users and Groups](https://docs.databricks.com/en/admin/users-groups/)
- [Manage Privileges](https://docs.databricks.com/en/data-governance/unity-catalog/manage-privileges/)
