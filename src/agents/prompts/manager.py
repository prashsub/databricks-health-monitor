"""
TRAINING MATERIAL: Production Prompt Management with Caching
============================================================

This module implements a thread-safe prompt manager with automatic
caching, TTL-based refresh, and graceful fallback to defaults.

PROMPT CACHING ARCHITECTURE:
----------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  PromptManager (Singleton)                                               │
│  ─────────────────────────                                               │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  prompt_cache: Dict[str, CachedPrompt]                          │   │
│  │  ┌──────────────┬───────────┬───────────┬──────────────────┐   │   │
│  │  │ orchestrator │ version=3 │ loaded_at │ age_seconds=120  │   │   │
│  │  │ synthesizer  │ version=2 │ loaded_at │ age_seconds=300  │   │   │
│  │  │ intent_clf   │ version=1 │ loaded_at │ age_seconds=50   │   │   │
│  │  └──────────────┴───────────┴───────────┴──────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  cache_ttl_seconds: 3600  (refresh after 1 hour)                       │
│  default_alias: "production"                                            │
└─────────────────────────────────────────────────────────────────────────┘

CACHING BENEFITS:
-----------------

1. PERFORMANCE
   - Prompts loaded once, served from memory
   - No database query per agent invocation

2. RESILIENCE
   - If registry unavailable, serve cached
   - Fallback to embedded defaults if cache empty

3. CONSISTENCY
   - TTL prevents stale prompts in long-running endpoints
   - Background refresh doesn't block requests

THREAD SAFETY:
--------------

    # Lock protects cache updates
    with self._lock:
        self._prompts[name] = cached_prompt

    # Get is lock-free (atomic dict access)
    return self._prompts.get(name)

LAZY LOADING PATTERN:
---------------------

    def get_prompt(self, name: str) -> str:
        # Check cache first
        if name in self._prompts:
            cached = self._prompts[name]
            if cached.age_seconds < self.cache_ttl_seconds:
                return cached.prompt  # Cache hit
        
        # Cache miss - load from registry
        self._load_prompt(name)
        return self._prompts[name].prompt

Reference:
    28-mlflow-genai-patterns.mdc cursor rule
    docs/agent-framework-design/10-prompt-registry.md

Usage:
    from agents.prompts import get_prompt_manager

    manager = get_prompt_manager()

    # Load prompt by component name
    prompt = manager.get_prompt("orchestrator")

    # Refresh prompts from registry
    manager.refresh_prompts()
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import threading
import mlflow
import mlflow.genai
from mlflow import MlflowClient

from .registry import (
    ORCHESTRATOR_PROMPT,
    INTENT_CLASSIFIER_PROMPT,
    SYNTHESIZER_PROMPT,
    WORKER_AGENT_PROMPT,
    get_domain_description,
    get_domain_capabilities,
)
from ..config import settings


@dataclass
class CachedPrompt:
    """Cached prompt with metadata."""

    prompt: str
    version: str
    alias: str
    loaded_at: datetime
    source: str  # "registry" or "fallback"

    @property
    def age_seconds(self) -> float:
        """Age of cached prompt in seconds."""
        return (datetime.now(timezone.utc) - self.loaded_at).total_seconds()


class PromptManager:
    """
    Production prompt manager with caching and refresh.

    Manages all prompts used by the Health Monitor agent,
    loading from MLflow Prompt Registry with fallback to
    hardcoded defaults.

    Attributes:
        alias: Default alias to load ("production", "staging", etc.)
        cache_ttl_seconds: Time to live for cached prompts
        prompts: Dict of prompt name to CachedPrompt
    """

    # Standard prompt components
    PROMPT_COMPONENTS = [
        "orchestrator",
        "intent_classifier",
        "synthesizer",
        "worker_cost",
        "worker_security",
        "worker_performance",
        "worker_reliability",
        "worker_quality",
    ]

    def __init__(
        self,
        alias: str = "production",
        cache_ttl_seconds: int = 300,
        auto_load: bool = True,
    ):
        """
        Initialize prompt manager.

        Args:
            alias: Default alias for loading prompts
            cache_ttl_seconds: Cache TTL in seconds (default: 5 minutes)
            auto_load: Whether to load all prompts on initialization
        """
        self.alias = alias
        self.cache_ttl_seconds = cache_ttl_seconds
        self._prompts: Dict[str, CachedPrompt] = {}
        self._lock = threading.Lock()
        self._client = MlflowClient()

        # Load fallback prompts
        self._fallbacks = self._get_fallback_prompts()

        if auto_load:
            self._load_all_prompts()

    def _get_fallback_prompts(self) -> Dict[str, str]:
        """Get hardcoded fallback prompts."""
        fallbacks = {
            "orchestrator": ORCHESTRATOR_PROMPT,
            "intent_classifier": INTENT_CLASSIFIER_PROMPT,
            "synthesizer": SYNTHESIZER_PROMPT,
        }

        # Add worker prompts
        for domain in ["cost", "security", "performance", "reliability", "quality"]:
            fallbacks[f"worker_{domain}"] = WORKER_AGENT_PROMPT.format(
                domain=domain.upper(),
                domain_description=get_domain_description(domain),
                capabilities=get_domain_capabilities(domain),
            )

        return fallbacks

    def _load_all_prompts(self) -> None:
        """Load all prompts from registry."""
        for component in self.PROMPT_COMPONENTS:
            try:
                self._load_prompt(component)
            except Exception as e:
                print(f"Warning: Could not load prompt '{component}': {e}")
                # Use fallback
                self._set_fallback(component)

    def _load_prompt(self, name: str) -> str:
        """
        Load a single prompt from registry.

        Args:
            name: Prompt component name

        Returns:
            Loaded prompt template string.
        """
        model_name = f"health_monitor_{name}_prompt"
        uri = f"prompts:/{model_name}/{self.alias}"

        try:
            prompt = mlflow.genai.load_prompt(uri)

            # Get version info
            version = self._get_version_for_alias(model_name, self.alias)

            with self._lock:
                self._prompts[name] = CachedPrompt(
                    prompt=prompt,
                    version=version or "unknown",
                    alias=self.alias,
                    loaded_at=datetime.now(timezone.utc),
                    source="registry",
                )

            return prompt

        except Exception as e:
            print(f"Failed to load prompt '{name}' from registry: {e}")
            self._set_fallback(name)
            return self._fallbacks.get(name, "")

    def _get_version_for_alias(self, model_name: str, alias: str) -> Optional[str]:
        """Get version number for an alias."""
        try:
            alias_info = self._client.get_model_version_by_alias(model_name, alias)
            return alias_info.version
        except Exception:
            return None

    def _set_fallback(self, name: str) -> None:
        """Set fallback prompt for a component."""
        fallback = self._fallbacks.get(name, "")

        with self._lock:
            self._prompts[name] = CachedPrompt(
                prompt=fallback,
                version="fallback",
                alias="fallback",
                loaded_at=datetime.now(timezone.utc),
                source="fallback",
            )

    def get_prompt(
        self,
        name: str,
        force_refresh: bool = False,
    ) -> str:
        """
        Get a prompt by component name.

        Args:
            name: Prompt component name (e.g., "orchestrator")
            force_refresh: Force reload from registry

        Returns:
            Prompt template string.

        Example:
            prompt = manager.get_prompt("orchestrator")
            formatted = prompt.format(user_context=context)
        """
        with self._lock:
            cached = self._prompts.get(name)

        # Check if refresh needed
        needs_refresh = (
            force_refresh
            or cached is None
            or cached.age_seconds > self.cache_ttl_seconds
        )

        if needs_refresh:
            return self._load_prompt(name)

        return cached.prompt

    def refresh_prompts(self) -> Dict[str, bool]:
        """
        Refresh all prompts from registry.

        Returns:
            Dict of component name to success status.

        Example:
            results = manager.refresh_prompts()
            # {"orchestrator": True, "intent_classifier": True, ...}
        """
        results = {}

        for component in self.PROMPT_COMPONENTS:
            try:
                self._load_prompt(component)
                results[component] = True
            except Exception as e:
                print(f"Failed to refresh '{component}': {e}")
                results[component] = False

        return results

    def refresh_single(self, name: str) -> bool:
        """
        Refresh a single prompt.

        Args:
            name: Prompt component name

        Returns:
            True if refresh succeeded.
        """
        try:
            self._load_prompt(name)
            return True
        except Exception:
            return False

    def get_prompt_info(self, name: str) -> Optional[Dict]:
        """
        Get metadata about a cached prompt.

        Args:
            name: Prompt component name

        Returns:
            Dict with version, alias, age, and source info.
        """
        with self._lock:
            cached = self._prompts.get(name)

        if not cached:
            return None

        return {
            "name": name,
            "version": cached.version,
            "alias": cached.alias,
            "age_seconds": cached.age_seconds,
            "source": cached.source,
            "loaded_at": cached.loaded_at.isoformat(),
        }

    def get_all_prompt_info(self) -> List[Dict]:
        """
        Get metadata for all cached prompts.

        Returns:
            List of prompt info dicts.
        """
        return [
            self.get_prompt_info(name)
            for name in self.PROMPT_COMPONENTS
            if self.get_prompt_info(name) is not None
        ]

    def set_alias(self, alias: str) -> None:
        """
        Change the default alias and refresh.

        Args:
            alias: New alias to use ("production", "staging", "development")
        """
        self.alias = alias
        self.refresh_prompts()

    def promote_to_production(
        self,
        name: str,
        version: str,
    ) -> bool:
        """
        Promote a prompt version to production.

        Args:
            name: Prompt component name
            version: Version number to promote

        Returns:
            True if promotion succeeded.
        """
        model_name = f"health_monitor_{name}_prompt"

        try:
            self._client.set_registered_model_alias(
                name=model_name,
                alias="production",
                version=str(version),
            )
            print(f"Promoted {model_name} version {version} to production")
            return True
        except Exception as e:
            print(f"Failed to promote: {e}")
            return False

    def rollback(
        self,
        name: str,
        to_version: str = None,
    ) -> bool:
        """
        Rollback a prompt to a previous version.

        Args:
            name: Prompt component name
            to_version: Version to rollback to (default: previous production)

        Returns:
            True if rollback succeeded.
        """
        model_name = f"health_monitor_{name}_prompt"

        try:
            if to_version is None:
                # Get previous production version
                versions = self._client.search_model_versions(f"name='{model_name}'")
                sorted_versions = sorted(versions, key=lambda v: int(v.version), reverse=True)

                # Find current production version
                current = self._get_version_for_alias(model_name, "production")

                # Get previous version
                for v in sorted_versions:
                    if v.version != current:
                        to_version = v.version
                        break

            if to_version:
                return self.promote_to_production(name, to_version)
            else:
                print("No previous version found for rollback")
                return False

        except Exception as e:
            print(f"Rollback failed: {e}")
            return False


# =============================================================================
# Global Instance
# =============================================================================

_prompt_manager: Optional[PromptManager] = None
_manager_lock = threading.Lock()


def get_prompt_manager(
    alias: str = "production",
    cache_ttl_seconds: int = 300,
) -> PromptManager:
    """
    Get the global PromptManager instance.

    Args:
        alias: Default alias for loading prompts
        cache_ttl_seconds: Cache TTL in seconds

    Returns:
        Singleton PromptManager instance.

    Example:
        manager = get_prompt_manager()
        prompt = manager.get_prompt("orchestrator")
    """
    global _prompt_manager

    with _manager_lock:
        if _prompt_manager is None:
            _prompt_manager = PromptManager(
                alias=alias,
                cache_ttl_seconds=cache_ttl_seconds,
            )

    return _prompt_manager


def reset_prompt_manager() -> None:
    """Reset the global PromptManager (for testing)."""
    global _prompt_manager
    with _manager_lock:
        _prompt_manager = None


# =============================================================================
# Convenience Functions
# =============================================================================

def get_prompt(name: str) -> str:
    """
    Quick function to get a prompt.

    Args:
        name: Prompt component name

    Returns:
        Prompt template string.
    """
    return get_prompt_manager().get_prompt(name)


def refresh_all_prompts() -> Dict[str, bool]:
    """
    Refresh all prompts from registry.

    Returns:
        Dict of component name to success status.
    """
    return get_prompt_manager().refresh_prompts()

