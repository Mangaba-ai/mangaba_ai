"""Constantes gerais para provedores de LLM"""

from typing import List, Dict, Any, Type
from ..base import BaseLLMProvider


def _resolve_provider_class(provider_name: str) -> Type[BaseLLMProvider]:
    """Resolve a classe do provedor a partir de um nome ou alias do provedor.

    Args:
        provider_name: O nome ou alias do provedor (insensível a maiúsculas/minúsculas).

    Returns:
        A classe do provedor que corresponde ao nome ou alias fornecido.

    Raises:
        ValueError: Se o nome do provedor não for reconhecido.
    """
    # Import here to avoid circular dependency
    from .google import GoogleLLMProvider
    from .openai import OpenAILLMProvider
    from .anthropic import AnthropicLLMProvider
    from .hugginface import HuggingFaceLLMProvider
    from .openrouter import OpenRouterLLMProvider

    provider_map = {
        GoogleLLMProvider.name: GoogleLLMProvider,
        OpenAILLMProvider.name: OpenAILLMProvider,
        AnthropicLLMProvider.name: AnthropicLLMProvider,
        HuggingFaceLLMProvider.name: HuggingFaceLLMProvider,
        OpenRouterLLMProvider.name: OpenRouterLLMProvider,
    }

    provider_name = provider_name.lower()
    for provider_cls in provider_map.values():
        if provider_cls.matches(provider_name):
            return provider_cls
    raise ValueError(f"Unknown provider: {provider_name}")


HF_OPEN_MODELS: List[Dict[str, Any]] = [
    # ── Geral com ajuste de instrução ──────────────────────────────────────────
    {
        "id": "mistralai/Mistral-7B-Instruct-v0.3",
        "name": "Mistral 7B Instruct v0.3",
        "category": "general",
        "context": 32768,
        "tool_calling": True,
        "streaming": True,
        "notes": "default; native function calling",
    },
    {
        "id": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "name": "Mixtral 8x7B Instruct",
        "category": "general",
        "context": 32768,
        "tool_calling": True,
        "streaming": True,
        "notes": "MoE; native function calling",
    },
    {
        "id": "mistralai/Mixtral-8x22B-Instruct-v0.1",
        "name": "Mixtral 8x22B Instruct",
        "category": "general",
        "context": 65536,
        "tool_calling": True,
        "streaming": True,
        "notes": "MoE; near GPT-4 quality; native function calling",
    },
    {
        "id": "mistralai/Mistral-Nemo-Instruct-2407",
        "name": "Mistral Nemo 12B Instruct",
        "category": "general",
        "context": 128000,
        "tool_calling": True,
        "streaming": True,
        "notes": "128k context; native function calling",
    },
    # ── Meta Llama 3 ──────────────────────────────────────────────────────
    {
        "id": "meta-llama/Meta-Llama-3-8B-Instruct",
        "name": "Llama 3 8B Instruct",
        "category": "general",
        "context": 8192,
        "tool_calling": False,
        "streaming": True,
        "notes": "fast, lightweight; prompt-based tools",
    },
    {
        "id": "meta-llama/Meta-Llama-3-70B-Instruct",
        "name": "Llama 3 70B Instruct",
        "category": "general",
        "context": 8192,
        "tool_calling": False,
        "streaming": True,
        "notes": "high quality; prompt-based tools",
    },
    {
        "id": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "name": "Llama 3.1 8B Instruct",
        "category": "general",
        "context": 128000,
        "tool_calling": True,
        "streaming": True,
        "notes": "128k context; native function calling",
    },
    {
        "id": "meta-llama/Meta-Llama-3.1-70B-Instruct",
        "name": "Llama 3.1 70B Instruct",
        "category": "general",
        "context": 128000,
        "tool_calling": True,
        "streaming": True,
        "notes": "128k context; native function calling",
    },
    {
        "id": "meta-llama/Meta-Llama-3.1-405B-Instruct",
        "name": "Llama 3.1 405B Instruct",
        "category": "general",
        "context": 128000,
        "tool_calling": True,
        "streaming": True,
        "notes": "largest open model; PRO required; native function calling",
    },
    {
        "id": "meta-llama/Llama-3.2-1B-Instruct",
        "name": "Llama 3.2 1B Instruct",
        "category": "general",
        "context": 128000,
        "tool_calling": False,
        "streaming": True,
        "notes": "ultra-light edge model; prompt-based tools",
    },
    {
        "id": "meta-llama/Llama-3.2-3B-Instruct",
        "name": "Llama 3.2 3B Instruct",
        "category": "general",
        "context": 128000,
        "tool_calling": False,
        "streaming": True,
        "notes": "edge-friendly; prompt-based tools",
    },
    # ── Code ──────────────────────────────────────────────────────────────
    {
        "id": "bigcode/starcoder2-15b-instruct-v0.1",
        "name": "StarCoder2 15B Instruct",
        "category": "code",
        "context": 16384,
        "tool_calling": False,
        "streaming": True,
        "notes": "code generation & completion; prompt-based tools",
    },
    {
        "id": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "name": "Qwen 2.5 Coder 7B Instruct",
        "category": "code",
        "context": 32768,
        "tool_calling": True,
        "streaming": True,
        "notes": "strong coding; native function calling",
    },
    {
        "id": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "name": "Qwen 2.5 Coder 32B Instruct",
        "category": "code",
        "context": 32768,
        "tool_calling": True,
        "streaming": True,
        "notes": "top open code model; native function calling",
    },
    {
        "id": "deepseek-ai/deepseek-coder-33b-instruct",
        "name": "DeepSeek Coder 33B Instruct",
        "category": "code",
        "context": 16384,
        "tool_calling": False,
        "streaming": True,
        "notes": "competitive code assistant; prompt-based tools",
    },
    # ── Qwen general ──────────────────────────────────────────────────────
    {
        "id": "Qwen/Qwen2.5-7B-Instruct",
        "name": "Qwen 2.5 7B Instruct",
        "category": "general",
        "context": 32768,
        "tool_calling": True,
        "streaming": True,
        "notes": "multilingual; native function calling",
    },
    {
        "id": "Qwen/Qwen2.5-72B-Instruct",
        "name": "Qwen 2.5 72B Instruct",
        "category": "general",
        "context": 32768,
        "tool_calling": True,
        "streaming": True,
        "notes": "near GPT-4 quality; native function calling",
    },
    # ── Phi (Microsoft) ───────────────────────────────────────────────────
    {
        "id": "microsoft/Phi-3-mini-4k-instruct",
        "name": "Phi-3 Mini 4K Instruct",
        "category": "general",
        "context": 4096,
        "tool_calling": False,
        "streaming": True,
        "notes": "3.8B, efficient small model",
    },
    {
        "id": "microsoft/Phi-3-medium-128k-instruct",
        "name": "Phi-3 Medium 128K Instruct",
        "category": "general",
        "context": 128000,
        "tool_calling": False,
        "streaming": True,
        "notes": "14B, 128k context",
    },
    {
        "id": "microsoft/Phi-3.5-mini-instruct",
        "name": "Phi-3.5 Mini Instruct",
        "category": "general",
        "context": 128000,
        "tool_calling": False,
        "streaming": True,
        "notes": "3.8B, multilingual",
    },
    # ── Gemma (Google) ────────────────────────────────────────────────────
    {
        "id": "google/gemma-2-2b-it",
        "name": "Gemma 2 2B Instruct",
        "category": "general",
        "context": 8192,
        "tool_calling": False,
        "streaming": True,
        "notes": "tiny but capable",
    },
    {
        "id": "google/gemma-2-9b-it",
        "name": "Gemma 2 9B Instruct",
        "category": "general",
        "context": 8192,
        "tool_calling": False,
        "streaming": True,
        "notes": "strong 9B model",
    },
    {
        "id": "google/gemma-2-27b-it",
        "name": "Gemma 2 27B Instruct",
        "category": "general",
        "context": 8192,
        "tool_calling": False,
        "streaming": True,
        "notes": "top Gemma, near 70B quality",
    },
    # ── Math / Reasoning ──────────────────────────────────────────────────
    {
        "id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "name": "DeepSeek R1 Distill Qwen 7B",
        "category": "reasoning",
        "context": 32768,
        "tool_calling": False,
        "streaming": True,
        "notes": "chain-of-thought reasoning",
    },
    {
        "id": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
        "name": "DeepSeek R1 Distill Llama 70B",
        "category": "reasoning",
        "context": 32768,
        "tool_calling": False,
        "streaming": True,
        "notes": "top open reasoning model",
    },
    # ── Embeddings ────────────────────────────────────────────────────────
    {
        "id": "BAAI/bge-m3",
        "name": "BGE-M3",
        "category": "embedding",
        "context": 8192,
        "tool_calling": False,
        "streaming": False,
        "notes": "multilingual, multi-granularity",
    },
    {
        "id": "sentence-transformers/all-MiniLM-L6-v2",
        "name": "all-MiniLM-L6-v2",
        "category": "embedding",
        "context": 512,
        "tool_calling": False,
        "streaming": False,
        "notes": "fast, lightweight embeddings",
    },
    {
        "id": "intfloat/multilingual-e5-large-instruct",
        "name": "Multilingual E5 Large Instruct",
        "category": "embedding",
        "context": 512,
        "tool_calling": False,
        "streaming": False,
        "notes": "100+ languages",
    },
]

# Índice por categoria para busca rápida
_HF_MODELS_BY_CATEGORY: Dict[str, List[Dict[str, Any]]] = {}
for _m in HF_OPEN_MODELS:
    _HF_MODELS_BY_CATEGORY.setdefault(_m["category"], []).append(_m)

# Conjunto de IDs de modelos com suporte nativo a chamada de função
_HF_NATIVE_TOOL_MODELS: set = {m["id"] for m in HF_OPEN_MODELS if m["tool_calling"]}


# Dicionário PROVIDERS definido preguiçosamente para evitar importações circulares
def get_providers_dict() -> Dict[str, Type[BaseLLMProvider]]:
    """Obtém o dicionário de provedores, importando preguiçosamente para evitar dependência circular."""
    from .google import GoogleLLMProvider
    from .openai import OpenAILLMProvider
    from .anthropic import AnthropicLLMProvider
    from .hugginface import HuggingFaceLLMProvider
    from .openrouter import OpenRouterLLMProvider

    return {
        GoogleLLMProvider.name: GoogleLLMProvider,
        OpenAILLMProvider.name: OpenAILLMProvider,
        AnthropicLLMProvider.name: AnthropicLLMProvider,
        HuggingFaceLLMProvider.name: HuggingFaceLLMProvider,
        OpenRouterLLMProvider.name: OpenRouterLLMProvider,
    }


# Para compatibilidade retroativa
PROVIDERS = get_providers_dict()
