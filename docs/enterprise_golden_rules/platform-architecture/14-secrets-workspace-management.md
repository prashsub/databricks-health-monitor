# Secrets & Workspace Management

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | PA-SEC-001 |
| **Version** | 1.0 |
| **Last Updated** | January 2026 |
| **Owner** | Platform Engineering |
| **Status** | Approved |

---

## Executive Summary

This document covers secrets management and workspace organization patterns. Secrets must be stored securely and accessed through approved methods. Workspace structure follows consistent naming and access patterns.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| PA-09 | All secrets in Databricks Secret Scopes | 🔴 Critical |
| PA-09a | Never hardcode credentials | 🔴 Critical |
| PA-09b | Use dbutils.secrets.get() only | 🔴 Critical |
| PA-11 | Workspace follows naming conventions | 🟡 Required |

---

## Secrets Management

### Rule PA-09: Secret Scopes Only

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           SECRETS ARCHITECTURE                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   ❌ NEVER                              ✅ ALWAYS                                   │
│   ────────                              ─────────                                   │
│   • Hardcoded in code                   • Databricks Secret Scopes                 │
│   • Environment variables               • dbutils.secrets.get()                    │
│   • Config files in repo                • Key Vault backed scopes                  │
│   • Notebook cells                      • Service principal for services           │
│   • Spark conf visible strings          • Redacted in logs                         │
│                                                                                     │
│   SECRET SCOPE STRUCTURE                                                            │
│   ┌────────────────────────────────────────────────────────────────────────────┐   │
│   │  Scope: data-platform                                                      │   │
│   │  ├── database-password                                                     │   │
│   │  ├── api-key-vendor-x                                                      │   │
│   │  ├── service-account-json                                                  │   │
│   │  └── encryption-key                                                        │   │
│   │                                                                            │   │
│   │  Scope: ml-team                                                            │   │
│   │  ├── model-registry-token                                                  │   │
│   │  └── feature-store-key                                                     │   │
│   └────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Creating Secret Scopes

```bash
# Create Databricks-backed scope
databricks secrets create-scope data-platform

# Create Azure Key Vault-backed scope (Azure)
databricks secrets create-scope --scope kv-backed \
  --scope-backend-type AZURE_KEYVAULT \
  --resource-id /subscriptions/.../Microsoft.KeyVault/vaults/my-vault \
  --dns-name https://my-vault.vault.azure.net/

# Create AWS Secrets Manager-backed scope (AWS) - via SDK
```

### Adding Secrets

```bash
# Add secret to scope
databricks secrets put-secret data-platform database-password

# List secrets (values never shown)
databricks secrets list-secrets data-platform
```

### Accessing Secrets in Code

```python
# ✅ CORRECT: Use dbutils.secrets.get()
password = dbutils.secrets.get(scope="data-platform", key="database-password")

# Use in connection (value redacted in logs)
jdbc_url = f"jdbc:postgresql://host:5432/db?user=admin&password={password}"

# ✅ CORRECT: Use in Spark config (redacted)
spark.conf.set("spark.datasource.password", 
               dbutils.secrets.get("data-platform", "database-password"))
```

### ❌ NEVER Do This

```python
# ❌ WRONG: Hardcoded password
password = "super_secret_123"

# ❌ WRONG: Environment variable
password = os.environ.get("DB_PASSWORD")

# ❌ WRONG: Config file in repo
with open("config/secrets.json") as f:
    password = json.load(f)["password"]

# ❌ WRONG: Visible in Spark conf
spark.conf.set("spark.custom.password", "plaintext_password")
```

### Secret Scope ACLs

```bash
# Grant READ permission to group
databricks secrets put-acl data-platform data_engineers READ

# Grant MANAGE permission (can add secrets)
databricks secrets put-acl data-platform platform_admins MANAGE

# List ACLs
databricks secrets list-acls data-platform
```

### ACL Permissions

| Permission | Can List | Can Read | Can Write | Can Manage ACL |
|------------|----------|----------|-----------|----------------|
| READ | ✅ | ✅ | ❌ | ❌ |
| WRITE | ✅ | ✅ | ✅ | ❌ |
| MANAGE | ✅ | ✅ | ✅ | ✅ |

---

## Workspace Organization

### Rule PA-11: Naming Conventions

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         WORKSPACE STRUCTURE                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   /Workspace                                                                        │
│   │                                                                                 │
│   ├── /Shared                          # Team-shared content                       │
│   │   ├── /data-platform               # Platform team                             │
│   │   │   ├── /notebooks               # Shared notebooks                          │
│   │   │   ├── /libraries               # Shared Python modules                     │
│   │   │   └── /configs                 # Configuration files                       │
│   │   │                                                                            │
│   │   ├── /ml-team                     # ML team                                   │
│   │   │   ├── /experiments             # MLflow experiments                        │
│   │   │   ├── /notebooks               # ML notebooks                              │
│   │   │   └── /models                  # Model artifacts                           │
│   │   │                                                                            │
│   │   └── /analytics                   # Analytics team                            │
│   │       ├── /dashboards              # Dashboard definitions                     │
│   │       └── /queries                 # Saved SQL queries                         │
│   │                                                                                 │
│   ├── /Users                           # Personal workspaces                       │
│   │   └── /user@company.com            # Individual user folders                   │
│   │                                                                                 │
│   └── /Repos                           # Git-connected repos                       │
│       └── /user@company.com                                                        │
│           └── /project-name            # Cloned repositories                       │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Folder Permissions

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Set folder permissions
w.workspace.set_permissions(
    path="/Workspace/Shared/data-platform",
    access_control_list=[
        {
            "group_name": "data_engineers",
            "permission_level": "CAN_EDIT"
        },
        {
            "group_name": "analysts",
            "permission_level": "CAN_READ"
        }
    ]
)
```

### Permission Levels

| Level | Description |
|-------|-------------|
| CAN_READ | View folders and files |
| CAN_RUN | Execute notebooks |
| CAN_EDIT | Modify notebooks |
| CAN_MANAGE | Full control including permissions |

---

## Multi-Workspace Strategy

### Workspace Types

| Workspace | Purpose | Access |
|-----------|---------|--------|
| **Development** | Development and testing | All engineers |
| **Staging** | Pre-production validation | Engineers + QA |
| **Production** | Production workloads | Restricted (CI/CD) |
| **Sandbox** | Experimentation | Data scientists |

### Cross-Workspace Patterns

```python
# Access different workspace via SDK
from databricks.sdk import WorkspaceClient

# Development workspace
dev_client = WorkspaceClient(
    host="https://dev-workspace.cloud.databricks.com",
    token=dbutils.secrets.get("scopes", "dev-token")
)

# Production workspace (for read-only queries)
prod_client = WorkspaceClient(
    host="https://prod-workspace.cloud.databricks.com",
    token=dbutils.secrets.get("scopes", "prod-token")
)
```

### Unity Catalog Cross-Workspace

```sql
-- Same metastore accessible from all workspaces
-- No data copying needed

-- Dev workspace
SELECT * FROM company_dev.gold.dim_customer;

-- Prod workspace (same metastore)
SELECT * FROM company_prod.gold.dim_customer;
```

---

## Service Principals

### When to Use

| Scenario | Authentication |
|----------|----------------|
| Interactive notebooks | User OAuth |
| Scheduled jobs | Service principal |
| CI/CD pipelines | Service principal |
| External integrations | Service principal |
| Model serving | Managed identity |

### Creating Service Principals

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Create service principal
sp = w.service_principals.create(
    display_name="data-pipeline-sp",
    active=True
)

# Add to group
w.groups.patch(
    id="data_engineers_group_id",
    operations=[{
        "op": "add",
        "path": "members",
        "value": [{"value": sp.id}]
    }]
)

# Generate OAuth token for service principal
# (Use Azure AD, AWS IAM, or Databricks OAuth)
```

### Service Principal in Jobs

```yaml
# Asset Bundle with service principal
resources:
  jobs:
    production_pipeline:
      name: "[prod] Production Pipeline"
      
      # Run as service principal (not user)
      run_as:
        service_principal_name: "data-pipeline-sp"
      
      tasks:
        - task_key: main
          # ...
```

---

## Environment Isolation

### Development vs Production

```yaml
# databricks.yml
targets:
  dev:
    mode: development
    default: true
    variables:
      catalog: company_dev
      secret_scope: dev-secrets
    workspace:
      host: https://dev.cloud.databricks.com
  
  prod:
    mode: production
    variables:
      catalog: company_prod
      secret_scope: prod-secrets
    workspace:
      host: https://prod.cloud.databricks.com
    run_as:
      service_principal_name: production-sp
```

### Secret Scope per Environment

```python
# Environment-aware secret access
def get_secret(key: str) -> str:
    """Get secret from environment-appropriate scope."""
    scope = spark.conf.get("secret_scope", "dev-secrets")
    return dbutils.secrets.get(scope=scope, key=key)

# Usage
db_password = get_secret("database-password")
```

---

## Audit and Compliance

### Secret Access Logging

```sql
-- Query secret access events
SELECT 
    event_time,
    user_identity.email as user,
    request_params.scope as scope,
    request_params.key as secret_key,
    response.status_code
FROM system.access.audit
WHERE action_name = 'getSecret'
    AND event_date >= CURRENT_DATE - 7
ORDER BY event_time DESC;
```

### Workspace Activity

```sql
-- User activity in workspace
SELECT 
    event_time,
    user_identity.email as user,
    action_name,
    request_params.path as resource_path
FROM system.access.audit
WHERE service_name = 'workspace'
    AND event_date >= CURRENT_DATE - 7
ORDER BY event_time DESC
LIMIT 100;
```

---

## Validation Checklist

### Secrets
- [ ] All secrets in Databricks Secret Scopes
- [ ] No hardcoded credentials in code
- [ ] ACLs set appropriately
- [ ] Secrets referenced via dbutils.secrets.get()
- [ ] Different scopes per environment

### Workspace
- [ ] Follows folder naming conventions
- [ ] Team folders under /Shared
- [ ] Appropriate folder permissions
- [ ] Production runs as service principal
- [ ] Cross-workspace access via SDK (not hardcoded)

### Service Principals
- [ ] Created for automated workloads
- [ ] Assigned to appropriate groups
- [ ] Token rotation policy in place
- [ ] Activity logged and monitored

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Secret not found" | Wrong scope/key | Verify scope and key names |
| "Permission denied" | Missing ACL | Grant READ on scope |
| "Secret value visible in logs" | Not using dbutils | Always use dbutils.secrets.get() |
| "Service principal expired" | Token expiration | Implement token rotation |

---

## Related Documents

- [Platform Overview](10-platform-overview.md)
- [Asset Bundle Standards](20-asset-bundle-standards.md)
- [Roles & Responsibilities](../enterprise-architecture/02-roles-responsibilities.md)

---

## References

- [Secret Scopes](https://docs.databricks.com/security/secrets/)
- [Workspace Organization](https://docs.databricks.com/workspace/)
- [Service Principals](https://docs.databricks.com/admin/service-principals/)
