"""
Motor de provedor LLM para Mangaba AI v3.0

Suporta chamada de função nativa (uso de ferramenta), streaming, contagem de tokens
e um formato de resposta unificado em Google, OpenAI, Anthropic e
Hugging Face.
"""

from __future__ import annotations

import logging
from typing import Any, List, Iterator, Dict, Optional

from mangaba.core.events import EventBus, Event, EventType
from mangaba.core.types import LLMResponse, TokenUsage
from .providers.constants import _resolve_provider_class


log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cliente de alto nível
# ---------------------------------------------------------------------------


class LLMClient:
    """Cliente LLM de alto nível unificado com suporte a uso de ferramenta e streaming."""

    def __init__(self, provider: str, api_key: str, model: str, **options: Any) -> None:
        """Inicializa o cliente LLM com um provedor específico.

        Args:
            provider: Nome do provedor (ex: "google", "openai", "anthropic").
            api_key: Chave de API para o serviço do provedor.
            model: Nome/identificador do modelo a ser usado.
            **options: Opções adicionais específicas do provedor (ex: temperature,
                max_output_tokens, system_prompt).

        Attributes:
            provider_name: O nome do provedor resolvido.
            _provider: A instância do provedor subjacente.
            _usage_tracker: Lista rastreando uso de token em todas as chamadas.
        """
        provider_cls = _resolve_provider_class(provider)
        self.provider_name = provider_cls.name
        self._provider = provider_cls(api_key=api_key, model=model, **options)
        self._usage_tracker: List[TokenUsage] = []

    # -- geração básica ---------------------------------------------------

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Gera uma resposta do LLM.

        Emite eventos LLM_START, LLM_END e LLM_ERROR para o EventBus.

        Args:
            prompt: O prompt de entrada para gerar uma resposta.
            **kwargs: Parâmetros adicionais específicos do provedor.

        Returns:
            LLMResponse contendo o texto gerado, metadados de uso e
            informações adicionais.

        Raises:
            Exception: Propaga qualquer exceção do provedor subjacente.
        """
        EventBus.emit(
            Event(
                event_type=EventType.LLM_START,
                data={"prompt_preview": prompt[:200], "provider": self.provider_name},
            )
        )
        try:
            resp = self._provider.generate(prompt, **kwargs)
            self._track_usage(resp.usage)
            EventBus.emit(
                Event(
                    event_type=EventType.LLM_END,
                    data={
                        "tokens": resp.usage.total_tokens,
                        "finish_reason": resp.finish_reason.value,
                    },
                )
            )
            return resp
        except Exception as exc:
            EventBus.emit(
                Event(event_type=EventType.LLM_ERROR, data={"error": str(exc)})
            )
            raise

    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        """Gera uma resposta e retorna apenas o conteúdo de texto.

        Método de conveniência que retorna o campo de texto do LLMResponse.

        Args:
            prompt: O prompt de entrada para gerar uma resposta.
            **kwargs: Parâmetros adicionais específicos do provedor.

        Returns:
            O conteúdo de texto gerado.
        """
        return self.generate(prompt, **kwargs).text

    # -- uso de ferramentas -----------------------------------------------------------

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Gera uma resposta com suporte opcional de chamada de ferramenta/função.

        Emite eventos LLM_START, LLM_END e LLM_ERROR para o EventBus com
        metadados de uso de ferramenta.

        Args:
            messages: Lista de dicionários de mensagem com chaves 'role' e 'content'.
            tools: Lista opcional de definições de ferramenta/função para o LLM usar.
            **kwargs: Parâmetros adicionais específicos do provedor.

        Returns:
            LLMResponse contendo o texto gerado, chamadas de ferramenta (se houver),
            metadados de uso e informações adicionais.

        Raises:
            Exception: Propaga qualquer exceção do provedor subjacente.
        """
        EventBus.emit(
            Event(
                event_type=EventType.LLM_START,
                data={
                    "mode": "tool_use",
                    "tools_count": len(tools or []),
                    "provider": self.provider_name,
                },
            )
        )
        try:
            resp = self._provider.generate_with_tools(messages, tools, **kwargs)
            self._track_usage(resp.usage)
            EventBus.emit(
                Event(
                    event_type=EventType.LLM_END,
                    data={
                        "tokens": resp.usage.total_tokens,
                        "tool_calls": len(resp.tool_calls),
                        "finish_reason": resp.finish_reason.value,
                    },
                )
            )
            return resp
        except Exception as exc:
            EventBus.emit(
                Event(event_type=EventType.LLM_ERROR, data={"error": str(exc)})
            )
            raise

    # -- streaming ----------------------------------------------------------

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Transmite a resposta token por token.

        Args:
            prompt: O prompt de entrada para gerar uma resposta.
            **kwargs: Parâmetros adicionais específicos do provedor.

        Yields:
            str: Tokens ou chunks de resposta conforme são gerados.
        """
        return self._provider.stream(prompt, **kwargs)

    # -- contagem de tokens -----------------------------------------------------

    def count_tokens(self, text: str) -> int:
        """Estima a contagem de tokens para o texto fornecido.

        Args:
            text: O texto para estimar a contagem de tokens.

        Returns:
            Número estimado de tokens.
        """
        return self._provider.count_tokens(text)

    # -- rastreamento de uso -----------------------------------------------------

    @property
    def total_usage(self) -> TokenUsage:
        """Obtém o uso total de token em todas as chamadas LLM.

        Returns:
            Objeto TokenUsage com prompt_tokens, completion_tokens
            e total_tokens acumulados.
        """
        total = TokenUsage()
        for u in self._usage_tracker:
            total.prompt_tokens += u.prompt_tokens
            total.completion_tokens += u.completion_tokens
            total.total_tokens += u.total_tokens
        return total

    def _track_usage(self, usage: TokenUsage) -> None:
        """Rastreia o uso de token de uma única chamada LLM.

        Args:
            usage: Objeto TokenUsage da resposta LLM.
        """
        if usage.total_tokens > 0:
            self._usage_tracker.append(usage)
