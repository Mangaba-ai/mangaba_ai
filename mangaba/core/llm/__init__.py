"""Motor LLM para Mangaba AI v3.0 — chamada de função, streaming, cache."""

from .client import LLMClient
from .llm_factory import create_llm_client, get_supported_providers
from .providers import (
    BaseLLMProvider,
    list_huggingface_models,
    hf_model_supports_tools,
    HF_OPEN_MODELS,
)
from .retry import with_retry
from .cache import LLMCache, InMemoryCache, DiskCache
from .token_counter import TokenCounter, UsageTracker
from .prompt_templates import PromptTemplate, ChatPromptTemplate, SystemPromptBuilder

__all__ = [
    "BaseLLMProvider",
    "LLMClient",
    "create_llm_client",
    "get_supported_providers",
    "list_huggingface_models",
    "hf_model_supports_tools",
    "HF_OPEN_MODELS",
    "with_retry",
    "LLMCache",
    "InMemoryCache",
    "DiskCache",
    "TokenCounter",
    "UsageTracker",
    "PromptTemplate",
    "ChatPromptTemplate",
    "SystemPromptBuilder",
]
