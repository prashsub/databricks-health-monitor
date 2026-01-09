# On-Behalf-Of-User (OBO) Authentication Guide

## Overview

This guide documents the **On-Behalf-Of-User (OBO) authentication pattern** for the Health Monitor Agent, based on official Databricks/Microsoft documentation.

**Official References:**
- [Authentication for AI agents](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#on-behalf-of-user-authentication)
- [Initialize agent in predict function](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#initialize-the-agent-in-the-predict-function)
- [OBO Example Notebooks](https://docs.databricks.com/aws/en/notebooks/source/generative-ai/agents-sql-obo-example.html)

## Authentication Methods Comparison

| Method | Description | Security Posture | Setup Complexity |
|--------|-------------|------------------|------------------|
| **Automatic authentication passthrough** | Agent runs with permissions of the user who deployed it. Databricks manages short-lived credentials. | Short-lived credentials, automatic rotation | Low - declare dependencies at logging time |
| **On-behalf-of-user (OBO)** ✅ | Agent runs with permissions of the **end user** making the request | Uses end user's credentials with restricted scopes | Medium - requires scope declaration and runtime initialization |
| **Manual authentication** | Explicitly provide credentials via environment variables | Long-lived credentials need rotation management | High - requires manual credential management |

## Why OBO for Genie Spaces?

**OBO is the CORRECT approach for Genie Spaces because:**

1. **Per-user access control** - Each user sees only data they have permissions to access
2. **Unity Catalog enforcement** - Fine-grained data controls via UC are enforced
3. **Audit attribution** - Actions are attributed to the actual user, not the deployer
4. **Reduced attack surface** - Tokens are restricted ("downscoped") to declared API scopes only

---

## 🚨 CRITICAL: Initialize Agent in `predict()`, NOT `__init__()`

> **From [official docs](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#initialize-the-agent-in-the-predict-function):**
> 
> "Initialize your agent in predict, not `__init__`. This ensures user identity is known at runtime and resources are isolated between invocations."

```python
from mlflow.pyfunc import ResponsesAgent
from databricks.sdk import WorkspaceClient
from databricks_ai_bridge import ModelServingUserCredentials

class OBOResponsesAgent(ResponsesAgent):
    def initialize_agent(self):
        """Initialize OBO client - called from predict, not __init__"""
        user_client = WorkspaceClient(
            credentials_strategy=ModelServingUserCredentials()
        )
        system_authorized_client = WorkspaceClient()  # System auth for LLM
        
        return user_client, system_authorized_client

    def predict(self, request) -> ResponsesAgentResponse:
        # CRITICAL: Initialize the agent INSIDE predict()
        user_client, system_client = self.initialize_agent()
        
        # Now use user_client for Genie/SQL and system_client for LLM
        ...
```

**Why this matters:**
- `ModelServingUserCredentials()` extracts the user identity from the request headers
- If initialized in `__init__()`, the user identity is unknown (module load time)
- Each request gets isolated resources, preventing cross-request data leakage

---

## Required API Scopes for OBO

**Complete reference from [official docs](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#declare-rest-api-scopes-when-logging-the-agent):**

| Resource Type | Required API Scope |
|---------------|-------------------|
| **Model Serving endpoints** | `serving.serving-endpoints` |
| **Vector Search endpoints** | `vectorsearch.vector-search-endpoints` |
| **Vector Search indexes** | `vectorsearch.vector-search-indexes` |
| **SQL warehouses** | `sql.warehouses`, `sql.statement-execution` |
| **Genie spaces** | `dashboards.genie` |
| **UC connections** | `catalog.connections`, `serving.serving-endpoints` |
| **Databricks Apps** | `apps.apps` |
| **MCP Genie spaces** | `mcp.genie` |
| **MCP UC functions** | `mcp.functions` |
| **MCP Vector Search** | `mcp.vectorsearch` |
| **MCP DBSQL** | `mcp.sql`, `sql.warehouses`, `sql.statement-execution` |
| **MCP external functions** | `mcp.external` |

## Implementation Pattern

### 1. Model Logging with AuthPolicy

When logging the agent, use `auth_policy=` instead of `resources=` for Genie Spaces:

```python
import mlflow
from mlflow.models.auth_policy import AuthPolicy, SystemAuthPolicy, UserAuthPolicy
from mlflow.models.resources import DatabricksServingEndpoint

# System policy: LLM endpoint accessed with system credentials
system_policy = SystemAuthPolicy(
    resources=[DatabricksServingEndpoint(endpoint_name="databricks-claude-3-7-sonnet")]
)

# User policy: API scopes for OBO access to Genie Spaces
user_policy = UserAuthPolicy(api_scopes=[
    # Genie Space access
    "dashboards.genie",
    # SQL Warehouse access (required for Genie queries)
    "sql.warehouses",
    "sql.statement-execution",
    # Model Serving access
    "serving.serving-endpoints",
])

# Log the agent with both policies
with mlflow.start_run():
    mlflow.pyfunc.log_model(
        artifact_path="agent",
        python_model=agent,
        input_example=input_example,
        registered_model_name=model_name,
        auth_policy=AuthPolicy(
            system_auth_policy=system_policy,
            user_auth_policy=user_policy
        ),
        pip_requirements=[
            "mlflow>=3.0.0",
            "databricks-sdk>=0.28.0",
            "databricks-langchain",
            "databricks-agents>=1.2.0",
            "databricks-ai-bridge",  # Required for ModelServingUserCredentials
        ],
    )
```

### 2. Agent Code: Initialize OBO in `predict()`, NOT `__init__()`

**CRITICAL**: Because the user's identity is only known at query time, you must initialize the user-authenticated client **inside `predict()`**, not in the agent's `__init__()` method.

```python
from mlflow.pyfunc import ResponsesAgent
from databricks.sdk import WorkspaceClient
from databricks_ai_bridge import ModelServingUserCredentials
from databricks_langchain.genie import GenieAgent

class OBOResponsesAgent(ResponsesAgent):
    """Agent with On-Behalf-Of-User authentication for Genie Spaces."""
    
    def __init__(self):
        # DO NOT initialize user client here!
        # Only initialize system resources that don't need user identity
        pass
    
    def predict(self, request):
        # Initialize the OBO client INSIDE predict()
        # This ensures the user's identity is used for authentication
        user_client = WorkspaceClient(
            credentials_strategy=ModelServingUserCredentials()
        )
        
        # Create GenieAgent with OBO client
        genie_agent = GenieAgent(
            genie_space_id="<genie_space_id>",
            genie_agent_name="Cost Genie",
            description="Access cost data via Genie Space",
            client=user_client,  # CRITICAL: Pass the OBO client!
        )
        
        # Use the Genie agent
        try:
            response = genie_agent.invoke({"input": query})
            return self._format_response(response)
        except Exception as e:
            # Handle permission errors gracefully
            if "PERMISSION" in str(e).upper():
                return "Unable to access Genie Space. Please ensure you have permissions."
            raise
```

### 3. Using GenieAgent with OBO (LangChain Pattern)

**From [official docs - Genie Spaces with LangChain](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#genie-spaces-langchain):**

```python
from databricks_langchain.genie import GenieAgent
from databricks.sdk import WorkspaceClient
from databricks_ai_bridge import ModelServingUserCredentials

# Configure WorkspaceClient with OBO authentication
user_client = WorkspaceClient(
    credentials_strategy=ModelServingUserCredentials()
)

genie_agent = GenieAgent(
    genie_space_id="<genie_space_id>",
    genie_agent_name="Genie",
    description="This Genie space has access to sales data in Europe",
    client=user_client,  # ⚠️ CRITICAL: Specify the OBO-authenticated client!
)

# Use the Genie agent - handles permission errors gracefully
try:
    response = genie_agent.invoke("Your query here")
except Exception as e:
    _logger.debug("Skipping Genie due to no permissions")
```

> ⚠️ **CRITICAL**: The `client=user_client` parameter is REQUIRED for OBO authentication. Without it, the agent uses system/deployer credentials!

### 4. Using WorkspaceClient.genie SDK with OBO

**From [official docs - Genie Spaces with WorkspaceClient](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#genie-spaces-workspaceclient):**

```python
from databricks.sdk import WorkspaceClient
from databricks_ai_bridge import ModelServingUserCredentials

# Configure WorkspaceClient with OBO authentication
user_client = WorkspaceClient(
    credentials_strategy=ModelServingUserCredentials()
)

# Direct Genie SDK API calls
space_id = "01f0ea87..."

# Start conversation and wait for response
response = user_client.genie.start_conversation_and_wait(
    space_id=space_id,
    content="What were total costs yesterday?"
)

# Process attachments (text, SQL, query results)
for attachment in response.attachments:
    if attachment.text:
        print(f"Response: {attachment.text.content}")
    if attachment.query:
        # Get the actual query results
        query_result = user_client.genie.get_message_attachment_query_result(
            space_id=space_id,
            conversation_id=response.conversation_id,
            message_id=response.id,
            attachment_id=attachment.id,
        )
        # Process result.statement.result.data_array
```

### 5. Using Model Serving Endpoints with OBO

**From [official docs](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#on-behalf-of-user-authentication):**

```python
from databricks.sdk import WorkspaceClient
from databricks_ai_bridge import ModelServingUserCredentials

# Configure WorkspaceClient with OBO authentication
user_client = WorkspaceClient(
    credentials_strategy=ModelServingUserCredentials()
)

# Exclude exception handling if the agent should fail
# when users lack access to all required Databricks resources
try:
    user_client.serving_endpoints.query("endpoint_name", input="")
except Exception as e:
    _logger.debug("Skipping Model Serving Endpoint due to no permissions")
```

### 6. Using Vector Search with OBO

**From [official docs](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#on-behalf-of-user-authentication):**

```python
from databricks.sdk import WorkspaceClient
from databricks_ai_bridge import ModelServingUserCredentials
from databricks_langchain import VectorSearchRetrieverTool

# Configure WorkspaceClient with OBO authentication
user_client = WorkspaceClient(
    credentials_strategy=ModelServingUserCredentials()
)

vector_search_tools = []
# Exclude exception handling if the agent should fail
# when users lack access to all required Databricks resources
try:
    tool = VectorSearchRetrieverTool(
        index_name="<index_name>",
        description="...",
        tool_name="...",
        workspace_client=user_client  # Specify the OBO-authenticated client
    )
    vector_search_tools.append(tool)
except Exception as e:
    _logger.debug("Skipping adding tool as user does not have permissions")
```

### 7. Using MCP with OBO

**From [official docs](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#on-behalf-of-user-authentication):**

```python
from databricks.sdk import WorkspaceClient
from databricks_ai_bridge import ModelServingUserCredentials
from databricks_mcp import DatabricksMCPClient

# Configure WorkspaceClient with OBO authentication
user_client = WorkspaceClient(
    credentials_strategy=ModelServingUserCredentials()
)

mcp_client = DatabricksMCPClient(
    server_url="<mcp_server_url>",
    workspace_client=user_client,  # Specify the OBO-authenticated client
)
```

## End User Permissions Required

**For OBO to work, the END USER (not the deployer) must have:**

| Resource | Permission | How to Grant |
|----------|------------|--------------|
| **Genie Space** | `CAN RUN` or `CAN MANAGE` | Genie Space settings → Permissions |
| **SQL Warehouse** | `CAN USE` ⚠️ | SQL Warehouses → Permissions |
| **Unity Catalog tables** | `SELECT` | `GRANT SELECT ON TABLE ... TO user@company.com` |
| **Unity Catalog functions** | `EXECUTE` | `GRANT EXECUTE ON FUNCTION ... TO user@company.com` |

> ⚠️ **CRITICAL**: The user must have `CAN USE` on the SQL warehouse that the Genie Space uses. `CAN MONITOR` is NOT sufficient!

### Granting SQL Warehouse Permissions

```bash
# Via Databricks CLI
databricks warehouses set-permissions <warehouse_id> --json '{
  "access_control_list": [
    {
      "user_name": "user@company.com",
      "permission_level": "CAN_USE"
    }
  ]
}'

# Or grant to a group
databricks warehouses set-permissions <warehouse_id> --json '{
  "access_control_list": [
    {
      "group_name": "all_users",
      "permission_level": "CAN_USE"
    }
  ]
}'
```

## Common Issues and Solutions

### Issue 1: "Unable to access the Genie Space" Permission Error

**Error:**
```
Permission Error: Unable to access the Genie Space for cost. 
Please ensure you have CAN USE permissions on the SQL warehouse and the Genie Space.
Debug Info: <user_id> is not authorized to use or monitor this SQL Endpoint.
```

**Root Cause:** User has `CAN_MONITOR` but not `CAN_USE` on the SQL warehouse.

**Solution:**
1. Find the SQL warehouse ID used by the Genie Space
2. Grant `CAN_USE` permission to the user:
```bash
databricks warehouses set-permissions <warehouse_id> --json '{
  "access_control_list": [
    {"user_name": "user@company.com", "permission_level": "CAN_USE"}
  ]
}'
```

### Issue 2: WorkspaceClient Not Using User Credentials

**Symptom:** Agent uses deployer's permissions instead of end user's.

**Root Cause:** 
- Using `resources=` instead of `auth_policy=` when logging model
- Initializing client in `__init__()` instead of `predict()`

**Solution:** Follow the implementation pattern above.

### Issue 3: MLflow AuthPolicy Import Error

**Error:** `ImportError: cannot import name 'AuthPolicy' from 'mlflow.models.auth_policy'`

**Root Cause:** MLflow version < 2.22.1

**Solution:** Update MLflow:
```bash
pip install mlflow>=2.22.1
```

### Issue 4: OBO is Disabled in Workspace

**Error:** OBO authentication fails silently or with generic error.

**Root Cause:** OBO must be enabled by a workspace admin.

**Solution:** Contact your workspace admin to enable OBO authentication.

## Security Considerations

From the [official documentation](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#obo-security-considerations):

> **Expanded resource access**: Agents can access sensitive resources on behalf of users. While scopes restrict APIs, endpoints might allow more actions than your agent explicitly requests. For example, the `serving.serving-endpoints` API scope grants an agent permission to run a serving endpoint on behalf of the user. However, the serving endpoint can access additional API scopes that the original agent isn't authorized to use.

**Best practices:**
- Declare only the API scopes your agent actually needs
- Handle permission errors gracefully
- Log and monitor access patterns for anomalies

## Testing OBO Authentication

### 1. Test in AI Playground

1. Deploy the agent to a serving endpoint
2. Open AI Playground and select the endpoint
3. Ask a question that queries Genie: "What were costs yesterday?"
4. If you see permission errors, verify:
   - You have `CAN USE` on the SQL warehouse
   - You have `CAN RUN` on the Genie Space
   - OBO is enabled in your workspace

### 2. Verify AuthPolicy Configuration

```python
# Check if model was logged with auth_policy
import mlflow

model_uri = "models:/health_monitor_agent/1"
model_info = mlflow.models.get_model_info(model_uri)

# Print the auth policy (if present)
print(model_info.signature)  # Should show OBO configuration
```

## OBO Resources Supported

**From [official docs](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#obo-supported-resources):**

| Databricks Resource | Compatible Clients |
|--------------------|--------------------|
| **Vector Search Index** | `databricks_langchain.VectorSearchRetrieverTool`, `databricks_openai.VectorSearchRetrieverTool`, `VectorSearchClient` |
| **Model Serving Endpoint** | `databricks.sdk.WorkspaceClient` |
| **SQL Warehouse** | `databricks.sdk.WorkspaceClient` (Genie, SQL execution) |
| **Genie Space** | `databricks.sdk.WorkspaceClient`, `databricks_langchain.genie.GenieAgent` |
| **UC Connection** | `databricks.sdk.WorkspaceClient` |
| **MCP servers** | `databricks_mcp.DatabricksMCPClient` |

## References

### Primary Documentation
- [Authentication for AI agents](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication) - Main authentication guide
- [Initialize agent in predict function](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#initialize-the-agent-in-the-predict-function) - Critical initialization pattern
- [Declare REST API scopes](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#declare-rest-api-scopes-when-logging-the-agent) - API scope reference

### OBO Specific Resources
- [Genie Spaces with WorkspaceClient](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#genie-spaces-workspaceclient)
- [Genie Spaces with LangChain](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#genie-spaces-langchain)
- [OBO Security Considerations](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#obo-security-considerations)

### Example Notebooks
- [OBO with Vector Search](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#obo-example-notebooks) - Vector Search OBO example
- [OBO with SQL Execution](https://docs.databricks.com/aws/en/notebooks/source/generative-ai/agents-sql-obo-example.html) - SQL execution OBO example

### Related Patterns
- [Multi-Agent Genie Pattern](https://docs.databricks.com/aws/en/generative-ai/agent-framework/multi-agent-genie)
- [Connect tools to external services](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#authenticate-to-external-systems-and-mcp-servers)

---

**Last Updated:** 2026-01-08

