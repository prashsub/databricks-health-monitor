"""
TRAINING MATERIAL: Agent Setup Module Architecture
==================================================

This module contains scripts for bootstrapping the agent infrastructure.
Setup is typically run once per environment (dev/staging/prod).

SETUP EXECUTION ORDER:
----------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 1: SCHEMA CREATION                                                 │
│  ─────────────────────────                                               │
│  create_schemas.py                                                       │
│  └── Creates Unity Catalog schemas for agent data                       │
│      - agent_config (prompts, settings)                                 │
│      - agent_traces (MLflow trace storage)                              │
│      - agent_memory (Lakebase tables)                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  STEP 2: PROMPT REGISTRATION                                             │
│  ────────────────────────────                                            │
│  register_prompts.py                                                     │
│  └── Registers prompts to:                                              │
│      - Unity Catalog agent_config table (runtime access)                │
│      - MLflow artifacts (versioning & lineage)                          │
├─────────────────────────────────────────────────────────────────────────┤
│  STEP 3: MEMORY INITIALIZATION                                           │
│  ──────────────────────────────                                          │
│  initialize_lakebase_tables.py                                           │
│  └── Pre-creates Lakebase tables (optional, auto-created on first use) │
│      - checkpoints (short-term, 24h retention)                          │
│      - store (long-term, 1yr retention)                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  STEP 4: MODEL LOGGING                                                   │
│  ─────────────────────                                                   │
│  log_agent_model.py                                                      │
│  └── Logs agent to Unity Catalog with:                                  │
│      - ResponsesAgent interface                                         │
│      - Genie Space resources                                            │
│      - Authentication policies                                          │
├─────────────────────────────────────────────────────────────────────────┤
│  STEP 5: ENDPOINT CREATION                                               │
│  ──────────────────────────                                              │
│  create_serving_endpoint.py                                              │
│  └── Creates Model Serving endpoint with:                               │
│      - AI Gateway (rate limits, usage tracking)                         │
│      - Inference logging                                                │
│      - Scale-to-zero configuration                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  STEP 6: EVALUATION DATASET                                              │
│  ──────────────────────────                                              │
│  create_evaluation_dataset.py                                            │
│  └── Creates hand-crafted evaluation questions for:                     │
│      - MLflow GenAI evaluation                                          │
│      - LLM judge scoring                                                │
│      - Regression testing                                               │
└─────────────────────────────────────────────────────────────────────────┘

Scripts for setting up agent infrastructure:
- Schema creation
- Prompt registration
- Model logging
"""

