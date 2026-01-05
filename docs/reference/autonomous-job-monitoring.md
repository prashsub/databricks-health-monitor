# Autonomous Job Monitoring with AI Assistants

## Overview

This document describes how an AI assistant (like Claude in Cursor) can autonomously monitor, troubleshoot, and fix Databricks job runs without requiring manual intervention from the user.

## Capabilities

### 1. Job Status Monitoring

The AI can check job status using the Databricks CLI:

```bash
# Get job run status
DATABRICKS_CONFIG_PROFILE=health_monitor databricks jobs get-run <RUN_ID> --output json

# Key fields to check:
# - state.life_cycle_state: PENDING, RUNNING, TERMINATED, SKIPPED, INTERNAL_ERROR
# - state.result_state: SUCCESS, FAILED, TIMEDOUT, CANCELED (only when TERMINATED)
# - tasks[].state: Individual task status
```

### 2. Run Output Retrieval

**⚠️ IMPORTANT: Multi-Task Jobs Require Task-Level Queries**

`databricks jobs get-run-output` only works for single-task jobs. For multi-task jobs, you must:
1. Get the task run IDs from the parent job run
2. Query each task's output individually

```bash
# Step 1: Get task run IDs from parent job
DATABRICKS_CONFIG_PROFILE=health_monitor databricks jobs get-run <JOB_RUN_ID> --output json \
  | jq '.tasks[] | {task_key: .task_key, task_run_id: .run_id, state: .state.result_state}'

# Step 2: Get output for EACH task (using task_run_id, not job_run_id)
DATABRICKS_CONFIG_PROFILE=health_monitor databricks jobs get-run-output <TASK_RUN_ID> --output json

# Key fields in output:
# - notebook_output.result: The dbutils.notebook.exit() value
# - notebook_output.truncated: Whether output was truncated
# - logs: Execution logs URL (if available)
```

**Example for ML Training Pipeline (25 parallel tasks):**

```bash
# Get all task run IDs
TASK_RUN_IDS=$(databricks jobs get-run 123456 --output json | jq -r '.tasks[].run_id')

# Query each task's output
for TASK_ID in $TASK_RUN_IDS; do
  echo "=== Task $TASK_ID ==="
  databricks jobs get-run-output $TASK_ID --output json 2>/dev/null | jq -r '.notebook_output.result // "No output"'
done
```

### 3. Real-Time Log Access

For running jobs, the AI can:
1. Access the run URL directly
2. Use Databricks workspace API to fetch logs
3. Parse stdout/stderr from completed tasks

**Accessing Cluster Logs (for completed tasks):**

```bash
# Get cluster log destination from task
databricks jobs get-run <JOB_RUN_ID> --output json | jq '.cluster_spec.cluster_log_conf'

# If logs are on DBFS:
databricks fs ls dbfs:/cluster-logs/<CLUSTER_ID>/driver/
databricks fs cat dbfs:/cluster-logs/<CLUSTER_ID>/driver/stdout
```

**Using the Runs Export API (for notebook output):**

```bash
# Export the executed notebook with outputs
databricks workspace export /Users/.../notebook_path --format HTML -o output.html

# Or get the execution context
databricks jobs get-run <TASK_RUN_ID> --output json | jq '.cluster_instance'
```

### 4. Alternative: Parse Print Statements from Task Output

When `dbutils.notebook.exit()` isn't sufficient, look for print statements in the notebook output:

```bash
# The notebook_output may contain truncated logs
databricks jobs get-run-output <TASK_RUN_ID> --output json | jq -r '.notebook_output'

# If truncated, you may need to:
# 1. Access the run URL and view logs in UI
# 2. Check cluster logs on DBFS
# 3. Use the runs/get-output endpoint with longer timeout
```

## Multi-Task Job Monitoring (Critical Pattern)

**Problem:** `databricks jobs get-run-output` returns nothing for multi-task jobs.

**Solution:** Query each task individually using its `run_id` (not the parent job's `run_id`).

### Complete Multi-Task Monitoring Script

```bash
#!/bin/bash
# monitor_multitask_job.sh

JOB_RUN_ID=$1
PROFILE="health_monitor"

echo "=== Monitoring Job Run: $JOB_RUN_ID ==="

# Wait for completion
while true; do
  STATUS=$(DATABRICKS_CONFIG_PROFILE=$PROFILE databricks jobs get-run $JOB_RUN_ID --output json)
  LIFECYCLE=$(echo $STATUS | jq -r '.state.life_cycle_state')
  
  if [ "$LIFECYCLE" = "TERMINATED" ]; then
    echo "Job completed!"
    break
  fi
  
  # Show task progress
  echo "Status: $LIFECYCLE"
  echo $STATUS | jq -r '.tasks[] | "  \(.task_key): \(.state.life_cycle_state)"'
  sleep 30
done

# Get results from each task
echo ""
echo "=== Task Results ==="
TASKS=$(echo $STATUS | jq -c '.tasks[]')

SUCCESS=0
FAILED=0

echo "$TASKS" | while read task; do
  TASK_KEY=$(echo $task | jq -r '.task_key')
  TASK_RUN_ID=$(echo $task | jq -r '.run_id')
  RESULT=$(echo $task | jq -r '.state.result_state')
  
  echo ""
  echo "--- $TASK_KEY (run_id: $TASK_RUN_ID) ---"
  echo "Result: $RESULT"
  
  if [ "$RESULT" = "SUCCESS" ]; then
    # Get notebook output
    OUTPUT=$(DATABRICKS_CONFIG_PROFILE=$PROFILE databricks jobs get-run-output $TASK_RUN_ID --output json 2>/dev/null)
    NOTEBOOK_RESULT=$(echo $OUTPUT | jq -r '.notebook_output.result // "No output"')
    echo "Output: $NOTEBOOK_RESULT"
  else
    # Get error message
    ERROR=$(echo $task | jq -r '.state.state_message')
    echo "Error: $ERROR"
  fi
done

# Summary
echo ""
echo "=== Summary ==="
echo $STATUS | jq '{
  total: (.tasks | length),
  succeeded: ([.tasks[] | select(.state.result_state == "SUCCESS")] | length),
  failed: ([.tasks[] | select(.state.result_state == "FAILED")] | length),
  failed_tasks: [.tasks[] | select(.state.result_state == "FAILED") | .task_key]
}'
```

### Training Pipeline Example (25 Tasks)

```bash
# Get summary of all 25 training tasks
databricks jobs get-run <JOB_RUN_ID> --output json | jq '{
  total_tasks: (.tasks | length),
  running: ([.tasks[] | select(.state.life_cycle_state == "RUNNING")] | length),
  succeeded: ([.tasks[] | select(.state.result_state == "SUCCESS")] | length),
  failed: ([.tasks[] | select(.state.result_state == "FAILED")] | length),
  pending: ([.tasks[] | select(.state.life_cycle_state == "PENDING")] | length)
}'

# Get failed task details
databricks jobs get-run <JOB_RUN_ID> --output json | jq '.tasks[] | select(.state.result_state == "FAILED") | {
  task: .task_key,
  error: .state.state_message,
  run_url: .run_page_url
}'

# Get output from a specific failed task
FAILED_TASK_RUN_ID=$(databricks jobs get-run <JOB_RUN_ID> --output json | jq -r '.tasks[] | select(.task_key == "train_cost_anomaly_detector") | .run_id')
databricks jobs get-run-output $FAILED_TASK_RUN_ID --output json | jq '.notebook_output'
```

## Monitoring Workflow

### Step 1: Start a Job

```bash
# Start job and capture run URL
DATABRICKS_CONFIG_PROFILE=health_monitor databricks bundle run -t dev <job_name>

# Extract run ID from output:
# Run URL: https://...#job/<JOB_ID>/run/<RUN_ID>
```

### Step 2: Poll for Completion

```bash
# Check status every 30 seconds
while true; do
  STATUS=$(DATABRICKS_CONFIG_PROFILE=health_monitor databricks jobs get-run <RUN_ID> \
    --output json | jq -r '.state.life_cycle_state')
  
  if [ "$STATUS" = "TERMINATED" ]; then
    RESULT=$(DATABRICKS_CONFIG_PROFILE=health_monitor databricks jobs get-run <RUN_ID> \
      --output json | jq -r '.state.result_state')
    echo "Job completed: $RESULT"
    break
  fi
  
  echo "Status: $STATUS"
  sleep 30
done
```

### Step 3: Get Output on Completion

```bash
# For notebooks with dbutils.notebook.exit()
DATABRICKS_CONFIG_PROFILE=health_monitor databricks jobs get-run-output <RUN_ID> --output json

# Parse the notebook result
jq -r '.notebook_output.result' output.json
```

### Step 4: Troubleshoot Failures

When a job fails, the AI can:

1. **Extract error message:**
   ```bash
   databricks jobs get-run <RUN_ID> --output json | jq -r '.state.state_message'
   ```

2. **Get task-level errors:**
   ```bash
   databricks jobs get-run <RUN_ID> --output json | jq '.tasks[] | {task: .task_key, error: .state.state_message}'
   ```

3. **Analyze and fix:**
   - Read the relevant source files
   - Identify the error pattern
   - Apply fixes
   - Redeploy and rerun

## Example: Autonomous Monitoring Script

The AI can execute this monitoring pattern:

```python
"""
Autonomous Job Monitoring Pattern

This is the workflow the AI assistant follows:
"""

import json
import subprocess
import time

def get_run_status(run_id: str) -> dict:
    """Get current run status."""
    result = subprocess.run(
        ["databricks", "jobs", "get-run", str(run_id), "--output", "json"],
        capture_output=True, text=True,
        env={"DATABRICKS_CONFIG_PROFILE": "health_monitor"}
    )
    return json.loads(result.stdout)

def monitor_until_complete(run_id: str, poll_interval: int = 30) -> dict:
    """Poll job until completion."""
    while True:
        status = get_run_status(run_id)
        lifecycle = status["state"]["life_cycle_state"]
        
        if lifecycle == "TERMINATED":
            return status
        
        print(f"Status: {lifecycle}")
        time.sleep(poll_interval)

def analyze_failure(status: dict) -> list:
    """Extract failure information from run status."""
    failures = []
    for task in status.get("tasks", []):
        if task["state"].get("result_state") == "FAILED":
            failures.append({
                "task": task["task_key"],
                "error": task["state"].get("state_message", "Unknown error"),
                "run_url": task.get("run_page_url")
            })
    return failures
```

## AI Decision Tree for Troubleshooting

```
Job Failed?
├── YES: Get error details
│   ├── "ModuleNotFoundError" → Check imports, add to dependencies
│   ├── "UNRESOLVED_COLUMN" → Verify column names against schema
│   ├── "Model not found" → Check model registry, run training
│   ├── "TABLE_OR_VIEW_NOT_FOUND" → Check schema, run feature pipeline
│   ├── "MlflowException: signature" → Fix fe.log_model() parameters
│   └── Other → Read full logs, analyze stack trace
│
└── NO: Success!
    └── Get notebook output → Parse results
```

## Supported Databricks CLI Commands

| Command | Purpose |
|---------|---------|
| `databricks bundle deploy` | Deploy resources |
| `databricks bundle run` | Start a job |
| `databricks jobs get-run` | Get run status |
| `databricks jobs get-run-output` | Get notebook output |
| `databricks jobs list-runs` | List recent runs |
| `databricks jobs cancel-run` | Cancel a running job |

## Limitations

1. **Log Access**: Full execution logs may require workspace UI access
2. **Real-time Output**: Streaming logs not available via CLI
3. **Authentication**: Requires valid Databricks profile
4. **Rate Limits**: Polling too frequently may hit API limits

## Best Practices for Job Design

To enable better autonomous monitoring:

1. **Always use `dbutils.notebook.exit()`** with structured output:
   ```python
   import json
   dbutils.notebook.exit(json.dumps({
       "status": "SUCCESS" | "FAILED",
       "total_models": 25,
       "successful": 20,
       "failed": 5,
       "failed_models": ["model1", "model2"],
       "errors": {"model1": "error message"}
   }))
   ```

2. **Print clear progress messages** for log analysis
3. **Fail fast** with clear error messages
4. **Use structured error reporting** at job end

## Example: Full Autonomous Monitoring Session

```bash
# 1. Start the job
$ databricks bundle run -t dev ml_inference_pipeline
Run URL: https://...#job/123/run/456

# 2. AI polls status
$ databricks jobs get-run 456 --output json | jq '.state'
{"life_cycle_state": "RUNNING"}

# 3. Wait... then check again
$ databricks jobs get-run 456 --output json | jq '.state'
{"life_cycle_state": "TERMINATED", "result_state": "FAILED"}

# 4. Get error details
$ databricks jobs get-run 456 --output json | jq '.tasks[] | select(.state.result_state == "FAILED")'
{"task_key": "batch_inference", "state": {"state_message": "RuntimeError: ..."}}

# 5. AI analyzes error, edits code, redeploys
$ databricks bundle deploy -t dev
$ databricks bundle run -t dev ml_inference_pipeline
# ... repeat monitoring
```

## Integration with Cursor AI

When using Claude in Cursor:

1. **Terminal Access**: Use `run_terminal_cmd` tool
2. **Background Jobs**: Use `is_background: true` for long-running commands
3. **Output Files**: Read terminal output from `~/.cursor/projects/.../terminals/*.txt`
4. **File Editing**: Use `search_replace` or `write` tools to fix issues
5. **Iteration**: Deploy → Run → Monitor → Fix → Repeat

---

**Last Updated:** January 2026
**Author:** AI-assisted documentation

