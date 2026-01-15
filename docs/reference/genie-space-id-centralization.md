# Genie Space ID Centralization

## Overview

All Genie Space IDs are now centralized in `databricks.yml` as Asset Bundle variables. This eliminates hardcoding and allows environment-specific overrides.

---

## Configuration Hierarchy

**Order of precedence (highest to lowest):**

1. **Runtime Parameters** (highest)
   - Passed as `base_parameters` to notebook task
   - Example: `cost_genie_space_id: ${var.cost_genie_space_id}`

2. **databricks.yml Variables**
   - Defined in `variables:` section
   - Can be overridden per target (dev/prod)

3. **Auto-Creation** (if blank)
   - If variable is blank/null, a new Genie Space is created via API
   - New space ID is printed for adding to `databricks.yml`

---

## Auto-Creation Workflow

### When to Use Auto-Creation

Leave Genie Space ID variables **blank** in `databricks.yml` to automatically create new spaces:

**Use Cases:**
- ✅ **New Environment** - Setting up dev/staging/prod from scratch
- ✅ **Fresh Start** - Want new spaces instead of updating existing ones
- ✅ **Testing** - Create temporary spaces for validation

### How Auto-Creation Works

```yaml
# databricks.yml - Leave IDs blank for auto-creation
variables:
  cost_genie_space_id:
    description: Cost Intelligence Genie Space ID
    default: ""  # ✅ Blank = auto-create
```

**Deployment Flow:**
1. Deploy bundle: `databricks bundle deploy -t dev`
2. Run Genie deployment job: Triggers `genie_spaces_job`
3. Script detects blank IDs and creates new spaces via API
4. New space IDs are printed in job output
5. Update `databricks.yml` with new IDs
6. Redeploy: `databricks bundle deploy -t dev`
7. Future runs will UPDATE existing spaces

**Example Output:**
```
✅ CREATED NEW GENIE SPACE
════════════════════════════════════════════════════════════════════════════════
  Space ID: 01f0ea871ffe176fa6aee6f895f83d3b
  Domain: cost
  Title: Health Monitor Cost Intelligence Space

⚠️  ACTION REQUIRED - Update databricks.yml:
════════════════════════════════════════════════════════════════════════════════
  File: databricks.yml
  Variable: cost_genie_space_id
  New Value: 01f0ea871ffe176fa6aee6f895f83d3b

  Example:
    cost_genie_space_id:
      description: Health Monitor Cost Intelligence Space
      default: "01f0ea871ffe176fa6aee6f895f83d3b"

  Then redeploy: databricks bundle deploy -t dev
════════════════════════════════════════════════════════════════════════════════
```

### Deployment Behavior: Blank vs Filled IDs

| Space ID Value | Deployment Behavior | Use Case |
|----|----|----|
| **Blank** (`""`) | ✅ **CREATE** new space via API | New environment, fresh start |
| **Valid ID** (`"01f0ea87..."`) | ✅ **UPDATE** existing space | Production, updates to config |
| **Invalid ID** | ❌ **ERROR** - space not found | Typo, deleted space |

**Example: Mixed Deployment**
```yaml
variables:
  cost_genie_space_id:
    default: "01f0ea871ffe176fa6aee6f895f83d3b"  # Will UPDATE
  
  reliability_genie_space_id:
    default: ""  # Will CREATE NEW
  
  quality_genie_space_id:
    default: "01f0ea93616c1978a99a59d3f2e805bd"  # Will UPDATE
```

**Result:**
- Cost Intelligence: **Updated** with new config
- Reliability: **New space created**, ID printed in output
- Quality: **Updated** with new config

---

## Single Source of Truth: databricks.yml

**File: `databricks.yml`**

```yaml
variables:
  # Genie Space IDs (Single Source of Truth for deployment)
  cost_genie_space_id:
    description: Cost Intelligence Genie Space ID
    default: "01f0ea871ffe176fa6aee6f895f83d3b"
  
  reliability_genie_space_id:
    description: Job Reliability Genie Space ID
    default: "01f0ea8724fd160e8e959b8a5af1a8c5"
  
  quality_genie_space_id:
    description: Data Quality Genie Space ID
    default: "01f0ea93616c1978a99a59d3f2e805bd"
  
  performance_genie_space_id:
    description: Performance Genie Space ID
    default: "01f0ea93671e12d490224183f349dba0"
  
  security_genie_space_id:
    description: Security Auditor Genie Space ID
    default: "01f0ea9367f214d6a4821605432234c4"
  
  unified_genie_space_id:
    description: Overall Health Monitor Genie Space ID
    default: "01f0ea9368801e019e681aa3abaa0089"

targets:
  dev:
    # Variables can be overridden per environment
    variables:
      cost_genie_space_id: "dev-space-id"  # Example override
  
  prod:
    # Production uses different Space IDs
    variables:
      cost_genie_space_id: "prod-space-id"
```

---

## How Variables Flow to Python Code

### Step 1: Bundle Variables → Task Parameters

**File: `resources/genie/genie_spaces_job.yml`**

```yaml
tasks:
  - task_key: deploy_genie_spaces
    environment_key: default
    notebook_task:
      notebook_path: ../../src/genie/deploy_genie_space.py
      base_parameters:
        catalog: ${var.catalog}
        # ✅ Genie Space IDs passed as task parameters
        cost_genie_space_id: ${var.cost_genie_space_id}
        reliability_genie_space_id: ${var.reliability_genie_space_id}
        quality_genie_space_id: ${var.quality_genie_space_id}
        performance_genie_space_id: ${var.performance_genie_space_id}
        security_genie_space_id: ${var.security_genie_space_id}
        unified_genie_space_id: ${var.unified_genie_space_id}
```

### Step 2: Task Parameters → Python Code via dbutils.widgets

**Python notebooks read these parameters and set as environment variables:**

```python
import os

# Read from task parameters (passed via databricks.yml)
cost_genie_space_id = dbutils.widgets.get("cost_genie_space_id")
reliability_genie_space_id = dbutils.widgets.get("reliability_genie_space_id")
# ... etc

# Set as environment variables (overrides defaults in genie_spaces.py)
os.environ["COST_GENIE_SPACE_ID"] = cost_genie_space_id
os.environ["RELIABILITY_GENIE_SPACE_ID"] = reliability_genie_space_id
# ... etc
```

### Step 3: Environment Variables → genie_spaces.py

**File: `src/agents/config/genie_spaces.py`**

```python
@dataclass
class GenieSpaceConfig:
    space_id: str  # Default value
    env_var: str   # Environment variable name
    
    def get_id(self) -> str:
        """Get space ID, with environment variable override."""
        return os.environ.get(self.env_var, self.space_id)

GENIE_SPACE_REGISTRY: Dict[str, GenieSpaceConfig] = {
    DOMAINS.COST: GenieSpaceConfig(
        space_id="01f0ea871ffe176fa6aee6f895f83d3b",  # Fallback
        env_var="COST_GENIE_SPACE_ID",  # Checked first
        domain=DOMAINS.COST,
        # ...
    ),
}

# Usage in agent code
cost_space_id = get_genie_space_id("cost")
# Returns: os.environ.get("COST_GENIE_SPACE_ID") or default
```

---

## Jobs That Need Genie Space IDs

### 1. Genie Deployment Job

**Purpose:** Deploy Genie Spaces via REST API

**File:** `resources/genie/genie_spaces_job.yml`

**Environment Variables:** ✅ Added

### 2. Agent Deployment Job

**Purpose:** Evaluate and promote agent model

**File:** `resources/agents/agent_deployment_job.yml`

**Environment Variables:** ✅ Added

**Why:** Agent needs Genie Space IDs to route queries during evaluation

### 3. Agent Setup Job

**Purpose:** Log agent model and run initial evaluation

**File:** `resources/agents/agent_setup_job.yml`

**Tasks Updated:**
- `log_agent_model` ✅ Added
- `run_evaluation` ✅ Added

**Why:** Agent initialization requires Genie Space IDs to create tools

---

## Environment-Specific Configuration

### Development Environment

```yaml
targets:
  dev:
    variables:
      # Use development Genie Spaces
      cost_genie_space_id: "dev-cost-space"
      reliability_genie_space_id: "dev-reliability-space"
```

### Production Environment

```yaml
targets:
  prod:
    variables:
      # Use production Genie Spaces
      cost_genie_space_id: "01f0ea871ffe176fa6aee6f895f83d3b"
      reliability_genie_space_id: "01f0ea8724fd160e8e959b8a5af1a8c5"
```

---

## Updating Genie Space IDs

### Option 1: Update databricks.yml (Recommended)

```yaml
# File: databricks.yml
variables:
  cost_genie_space_id:
    default: "new-space-id"  # Update here
```

Then redeploy:

```bash
databricks bundle deploy -t dev
```

### Option 2: Environment Variable Override (Runtime)

```bash
export COST_GENIE_SPACE_ID="temporary-space-id"
databricks bundle run -t dev agent_deployment_job
```

### Option 3: Target-Specific Override

```yaml
targets:
  prod:
    variables:
      cost_genie_space_id: "prod-specific-id"
```

---

## Benefits of Centralization

| Benefit | Description |
|---|---|
| **Single Source of Truth** | All IDs in one place (`databricks.yml`) |
| **Environment-Specific** | Different IDs for dev/prod |
| **No Hardcoding** | No need to edit Python code |
| **Easy Rotation** | Update one file, redeploy |
| **Audit Trail** | Git tracks all ID changes |
| **Consistent** | All jobs use same configuration pattern |

---

## Validation

### Check Current Configuration

```python
from agents.config.genie_spaces import print_genie_space_summary

print_genie_space_summary()
```

**Output:**

```
================================================================================
GENIE SPACE CONFIGURATION (Single Source of Truth)
================================================================================

Cost Intelligence Space
  Domain: cost
  ID: 01f0ea871ffe176fa6aee6f895f83d3b (env override)
  Status: ✓ Configured
  Env var: COST_GENIE_SPACE_ID
```

### Verify Environment Variables

```bash
# In Databricks notebook
import os
print(f"COST_GENIE_SPACE_ID: {os.environ.get('COST_GENIE_SPACE_ID', 'NOT SET')}")
```

---

## Migration from Old Pattern

### Before (Hardcoded)

```python
# OLD: Hardcoded in genie_spaces.py
GENIE_SPACES = {
    "cost": "01f0ea871ffe176fa6aee6f895f83d3b",
    "reliability": "01f0ea8724fd160e8e959b8a5af1a8c5",
}
```

### After (Centralized)

```yaml
# NEW: Centralized in databricks.yml
variables:
  cost_genie_space_id:
    default: "01f0ea871ffe176fa6aee6f895f83d3b"
  reliability_genie_space_id:
    default: "01f0ea8724fd160e8e959b8a5af1a8c5"
```

```python
# Python code unchanged - still uses get_genie_space_id()
from agents.config.genie_spaces import get_genie_space_id

cost_space = get_genie_space_id("cost")  # Now reads from env var
```

---

## Troubleshooting

### Issue: Agent Can't Find Genie Space

**Symptom:**

```
GenieAgent initialization failed: Space ID not found
```

**Solution:**

1. Check if environment variables are set:

```python
import os
print(os.environ.get("COST_GENIE_SPACE_ID"))
```

2. Verify job YAML has `environment_variables` block

3. Check `databricks.yml` has variable definitions

4. Redeploy bundle:

```bash
databricks bundle deploy -t dev
```

### Issue: Wrong Space ID Used

**Symptom:** Agent queries wrong Genie Space

**Solution:**

1. Check target-specific overrides in `databricks.yml`

2. Verify correct target is being deployed:

```bash
databricks bundle deploy -t prod  # Ensure correct target
```

3. Check runtime environment variables aren't overriding bundle config

---

## References

- [Databricks Asset Bundle Variables](https://docs.databricks.com/dev-tools/bundles/settings.html#variables)
- [Environment Variables in Jobs](https://docs.databricks.com/workflows/jobs/settings.html#environment-variables)
- [Agent Configuration](../../src/agents/config/genie_spaces.py)

---

**Last Updated:** January 13, 2026  
**Pattern:** Configuration centralization and environment-specific overrides

