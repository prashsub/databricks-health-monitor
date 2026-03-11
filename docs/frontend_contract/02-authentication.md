# Authentication

> How the frontend authenticates with the Agent Serving Endpoint and the Alert APIs.

## Agent Serving Endpoint

### Bearer Token

Every request to the agent serving endpoint requires a `Bearer` token in the `Authorization` header:

```
POST https://<workspace>.cloud.databricks.com/serving-endpoints/<endpoint-name>/invocations
Authorization: Bearer <user-or-sp-token>
Content-Type: application/json
```

The token can be:

- **User PAT** (Personal Access Token) -- for development and testing.
- **OAuth token** -- for production frontends using Databricks OAuth flow.
- **Service Principal token** -- for server-side backends calling the agent.

### On-Behalf-Of (OBO) Authentication

The agent supports OBO authentication, which allows the agent to act on behalf of the end user when querying Genie Spaces. This is critical for respecting user-level permissions in Unity Catalog.

**How it works (from `_get_genie_client()` in `log_agent_model.py`):**

The agent detects the execution environment by checking three environment variables:

| Variable | Value When in Model Serving |
|---|---|
| `IS_IN_DB_MODEL_SERVING_ENV` | `"true"` |
| `DATABRICKS_SERVING_ENDPOINT` | endpoint name |
| `MLFLOW_DEPLOYMENT_FLAVOR_NAME` | `"databricks"` |

**Decision flow:**

```
Is any of those env vars set?
├── YES (Model Serving) → Use OBO via ModelServingUserCredentials()
│   └── Agent inherits the calling user's permissions
│   └── The Bearer token passed by frontend becomes the user identity
└── NO (Notebooks/Jobs/Evaluation) → Use default workspace auth
    └── Agent uses service principal or notebook credentials
```

### What the Frontend Must Do

1. **Always pass a Bearer token** in the `Authorization` header.
2. In Model Serving, this token is automatically used for OBO -- the agent queries Genie Spaces with the calling user's permissions.
3. The frontend does NOT need to configure OBO. It is handled entirely by the backend.

### What the Frontend Must NOT Do

- Do NOT pass a token in `custom_inputs`. The `Authorization` header is the only mechanism.
- Do NOT attempt to call Genie Spaces directly. The agent handles all Genie interaction.

### Auth Fallback Chain (Backend Detail)

If OBO fails, the backend falls through this chain (frontend does not need to handle this):

1. **OBO** via `ModelServingUserCredentials()` (Model Serving only)
2. **Service Principal** via `GENIE_SP_CLIENT_ID` + `GENIE_SP_CLIENT_SECRET` env vars
3. **Explicit PAT** via `DATABRICKS_TOKEN` env var
4. **dbutils context** (notebook environments only)
5. **Default `WorkspaceClient()`** (last resort)

---

## Alert API Authentication

### SQL Warehouse (Delta Tables)

The frontend queries `alert_configurations` and `alert_history` via a Databricks SQL Warehouse. Authentication uses the same Bearer token:

```bash
curl -X POST "https://<workspace-url>/api/2.0/sql/statements" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "warehouse_id": "<warehouse-id>",
    "statement": "SELECT * FROM catalog.schema.alert_configurations WHERE is_enabled = true",
    "wait_timeout": "30s"
  }'
```

### SQL Alerts V2 API

Real-time alert states are fetched from the V2 API:

```bash
curl -X GET "https://<workspace-url>/api/2.0/alerts" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Endpoint:** `GET /api/2.0/alerts`

This is NOT `/api/2.0/sql/alerts` or `/api/2.0/sql/alerts-v2`. The correct V2 endpoint is `/api/2.0/alerts`.

### Token Scope Requirements

| Operation | Required Scope |
|---|---|
| Agent queries (POST /invocations) | Model Serving access to the endpoint |
| SQL Warehouse queries | `CAN USE` on the warehouse + `SELECT` on the tables |
| V2 Alert API (GET /api/2.0/alerts) | Workspace-level alert read permissions |

---

## CORS and Proxy Considerations

The Databricks workspace APIs enforce CORS restrictions. For browser-based frontends:

- **Option A:** Route all API calls through a backend proxy server that adds the Bearer token server-side.
- **Option B:** Use the Databricks OAuth flow to obtain tokens directly in the browser (if your workspace supports OAuth for web apps).
- **Option C:** Use the Databricks Apps platform, which handles auth natively.

Do NOT embed PAT tokens in client-side JavaScript.
