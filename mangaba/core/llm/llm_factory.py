"""
Módulo de Fábrica LLM

Este módulo fornece uma função de fábrica para criar clientes LLM para diferentes provedores.
"""

from __future__ import annotations

from typing import Any, Tuple

from .providers.constants import get_providers_dict
from .client import LLMClient


def create_llm_client(
    provider: str, api_key: str, model: str, **options: Any
) -> "LLMClient":
    """Cria um cliente LLM unificado para o provedor especificado.

    Provedores suportados:
        - "google" / "gemini": Modelos Google Gemini
        - "openai": Modelos OpenAI GPT
        - "anthropic": Modelos Anthropic Claude
        - "huggingface" / "hf": Modelos HuggingFace Inference API
        - "openrouter" / "or" / "open-router": Modelos OpenRouter

    Args:
        provider: Nome do provedor (ver provedores suportados acima).
        api_key: Chave de API para o provedor.
        model: Nome/ID do modelo (ex: "gpt-4o", "anthropic/claude-3-haiku").
        **options: Opções específicas do provedor (ex: base_url, temperature, max_tokens).

    Para OpenRouter:
        - Use formato de modelo como "openai/gpt-4o" ou "anthropic/claude-3-haiku"
        - Opcional: base_url (padrão: https://openrouter.ai/api/v1)
        - Opcional: site_url, site_name para cabeçalhos OpenRouter

    Returns:
        Instância LLMClient com métodos generate/generate_with_tools.

    Raises:
        ValueError: Se provider, api_key ou model não forem fornecidos.
    """
    from .client import LLMClient

    if not provider:
        raise ValueError("LLM provider name is required")
    if not api_key:
        raise ValueError("API key is required to initialise LLM provider")
    if not model:
        raise ValueError("Model name is required")

    return LLMClient(provider=provider, api_key=api_key, model=model, **options)


def get_supported_providers() -> Tuple[str, ...]:
    """Obtém todos os nomes de provedores suportados e aliases.

    Returns:
        Tupla de todos os nomes de provedores suportados e seus aliases, ordenados alfabeticamente.
    """
    aliases: set[str] = set()
    PROVIDERS = get_providers_dict()
    for provider_cls in PROVIDERS.values():
        aliases.add(provider_cls.name)
        aliases.update(provider_cls.aliases)
    return tuple(sorted(aliases))
