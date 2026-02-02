"""
TRAINING MATERIAL: Prompt Registry Architecture
===============================================

This module implements a production-grade prompt management system
with versioning, caching, AB testing, and MLflow integration.

PROMPT LIFECYCLE:
-----------------

┌─────────────────────────────────────────────────────────────────────────┐
│                        PROMPT LIFECYCLE                                  │
│                                                                         │
│  1. DEFINE         2. REGISTER         3. LOAD           4. EVALUATE   │
│  ────────          ──────────          ─────             ──────────    │
│  registry.py  →  register_prompts  →  PromptManager  →  AB Testing     │
│  (templates)      (Unity Catalog)      (runtime)         (champion/    │
│                   (MLflow)             (cached)          challenger)    │
└─────────────────────────────────────────────────────────────────────────┘

STORAGE PATTERN:
----------------

| Storage | Purpose | Benefits |
|---|---|---|
| Unity Catalog Table | Runtime retrieval | Fast reads, SQL queryable |
| MLflow Artifacts | Version tracking | History, rollback, lineage |

COMPONENT OVERVIEW:
-------------------

1. registry.py - Prompt template definitions
   - ORCHESTRATOR_PROMPT: Multi-domain coordinator
   - WORKER_AGENT_PROMPT: Domain-specific template
   - SYNTHESIZER_PROMPT: Response composer

2. manager.py - Production prompt loading
   - PromptManager: Singleton with caching
   - get_prompt_manager(): Get global instance
   - CachedPrompt: Metadata + TTL

3. ab_testing.py - Prompt experimentation
   - PromptABTest: Champion vs challenger
   - select_variant(): User-based routing
   - evaluate_variants(): Compare metrics

AB TESTING PATTERN:
-------------------

    ab_test = create_ab_test("orchestrator", treatment_version="v3")
    variant, prompt = ab_test.select_variant(user_id)
    
    # 90% champion (production), 10% challenger (experimental)
    # Track metrics per variant
    # Promote challenger to champion if better

Reference:
    28-mlflow-genai-patterns.mdc cursor rule
    docs/agent-framework-design/10-prompt-registry.md

Usage:
    # Basic prompt access
    from agents.prompts import ORCHESTRATOR_PROMPT, load_prompt

    # Production management
    from agents.prompts import get_prompt_manager, get_prompt

    manager = get_prompt_manager()
    prompt = manager.get_prompt("orchestrator")

    # A/B testing
    from agents.prompts import PromptABTest, create_ab_test

    ab_test = create_ab_test("orchestrator", treatment_version="v3")
    variant, prompt = ab_test.select_variant(user_id)
"""

# Prompt Templates
from .registry import (
    ORCHESTRATOR_PROMPT,
    INTENT_CLASSIFIER_PROMPT,
    SYNTHESIZER_PROMPT,
    WORKER_AGENT_PROMPT,
)

# Registry Functions
from .registry import (
    register_prompt,
    register_all_prompts,
    load_prompt,
    set_prompt_alias,
    get_domain_description,
    get_domain_capabilities,
)

# Production Manager
from .manager import (
    PromptManager,
    CachedPrompt,
    get_prompt_manager,
    reset_prompt_manager,
    get_prompt,
    refresh_all_prompts,
)

# A/B Testing
from .ab_testing import (
    PromptABTest,
    ABTestMetrics,
    create_ab_test,
    create_multi_variant_test,
)

__all__ = [
    # Templates
    "ORCHESTRATOR_PROMPT",
    "INTENT_CLASSIFIER_PROMPT",
    "SYNTHESIZER_PROMPT",
    "WORKER_AGENT_PROMPT",
    # Registry Functions
    "register_prompt",
    "register_all_prompts",
    "load_prompt",
    "set_prompt_alias",
    "get_domain_description",
    "get_domain_capabilities",
    # Production Manager
    "PromptManager",
    "CachedPrompt",
    "get_prompt_manager",
    "reset_prompt_manager",
    "get_prompt",
    "refresh_all_prompts",
    # A/B Testing
    "PromptABTest",
    "ABTestMetrics",
    "create_ab_test",
    "create_multi_variant_test",
]
