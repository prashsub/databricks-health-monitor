"""
Prompt Registry Module
======================

Versioned prompts for the Health Monitor agent system.
All prompts are registered to MLflow for tracking and deployment.

Includes:
- Prompt templates (orchestrator, intent classifier, synthesizer)
- Prompt registry functions (register, load, alias management)
- PromptManager for production prompt management with caching
- PromptABTest for A/B testing prompt variants

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
