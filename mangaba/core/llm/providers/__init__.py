"""Pacote de provedores de LLM"""

from .constants import (
    HF_OPEN_MODELS,
    _HF_MODELS_BY_CATEGORY,
    _HF_NATIVE_TOOL_MODELS,
    get_providers_dict,
)
from ..base import BaseLLMProvider
from .google import GoogleLLMProvider
from .openai import OpenAILLMProvider
from .anthropic import AnthropicLLMProvider
from .hugginface import (
    HuggingFaceLLMProvider,
    list_huggingface_models,
    hf_model_supports_tools,
)
from .openrouter import OpenRouterLLMProvider

# PROVIDERS dict for backwards compatibility
PROVIDERS = get_providers_dict()

__all__ = [
    "HF_OPEN_MODELS",
    "_HF_MODELS_BY_CATEGORY",
    "_HF_NATIVE_TOOL_MODELS",
    "PROVIDERS",
    "get_providers_dict",
    "BaseLLMProvider",
    "GoogleLLMProvider",
    "OpenAILLMProvider",
    "AnthropicLLMProvider",
    "HuggingFaceLLMProvider",
    "OpenRouterLLMProvider",
    "list_huggingface_models",
    "hf_model_supports_tools",
]
