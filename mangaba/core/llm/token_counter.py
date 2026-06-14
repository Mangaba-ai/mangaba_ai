"""
Contagem de tokens e rastreamento de uso em provedores.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from mangaba.core.types import TokenUsage

log = logging.getLogger(__name__)


class TokenCounter:
    """Estima contagens de tokens para vários provedores."""

    @staticmethod
    def count(text: str, provider: str = "openai", model: str = "") -> int:
        """Estima contagem de tokens para texto usando tokenização específica do provedor.

        Para OpenAI, usa a biblioteca tiktoken para contagens precisas. Para outros provedores,
        usa uma heurística aproximada (~4 caracteres por token).

        Args:
            text: O texto para contar tokens.
            provider: O nome do provedor (padrão: "openai").
            model: O nome do modelo para tokenização específica do provedor (padrão: "").

        Returns:
            Contagem de tokens estimada (mínimo 1).
        """
        if provider == "openai":
            return TokenCounter._count_openai(text, model)
        # Rough heuristic for other providers: ~4 chars per token
        return max(1, len(text) // 4)

    @staticmethod
    def _count_openai(text: str, model: str) -> int:
        """Conta tokens para modelos OpenAI usando tiktoken.

        Args:
            text: O texto para contar tokens.
            model: O nome do modelo para determinar a codificação (padrão: "gpt-4o-mini").

        Returns:
            Contagem de tokens precisa usando tiktoken, ou estimativa aproximada se tiktoken falhar.
        """
        try:
            import tiktoken  # type: ignore

            enc = tiktoken.encoding_for_model(model or "gpt-4o-mini")
            return len(enc.encode(text))
        except Exception:
            return max(1, len(text) // 4)

    @staticmethod
    def estimate_messages_tokens(
        messages: List[Dict[str, str]],
        provider: str = "openai",
        model: str = "",
    ) -> int:
        """Estima tokens totais para uma lista de mensagens de chat.

        Inclui sobrecarga para estrutura de mensagem (role, separadores, etc.).

        Args:
            messages: Lista de dicionários de mensagem com chaves 'role' e 'content'.
            provider: O nome do provedor (padrão: "openai").
            model: O nome do modelo para tokenização específica do provedor (padrão: "").

        Returns:
            Contagem total de tokens estimada para todas as mensagens incluindo sobrecarga.
        """
        total = 0
        overhead_per_msg = 4  # role + separators
        for msg in messages:
            total += overhead_per_msg
            total += TokenCounter.count(msg.get("content", ""), provider, model)
        total += 2  # start/end tokens
        return total


class UsageTracker:
    """Acumula uso de token em chamadas, opcionalmente por agente."""

    def __init__(self) -> None:
        """Inicializa o rastreador de uso.

        Attributes:
            _records: Lista de todos os registros TokenUsage rastreados.
            _by_agent: Dicionário mapeando IDs de agente para seus registros TokenUsage.
        """
        self._records: List[TokenUsage] = []
        self._by_agent: Dict[str, List[TokenUsage]] = {}

    def track(self, usage: TokenUsage, agent_id: Optional[str] = None) -> None:
        """Rastreia um registro de uso de token.

        Args:
            usage: Objeto TokenUsage para rastrear.
            agent_id: ID de agente opcional para associar o uso.
        """
        if usage.total_tokens <= 0:
            return
        self._records.append(usage)
        if agent_id:
            self._by_agent.setdefault(agent_id, []).append(usage)

    @property
    def total(self) -> TokenUsage:
        """Obtém o uso total de token acumulado em todas as chamadas.

        Returns:
            Objeto TokenUsage com prompt_tokens, completion_tokens
            e total_tokens acumulados.
        """
        t = TokenUsage()
        for u in self._records:
            t.prompt_tokens += u.prompt_tokens
            t.completion_tokens += u.completion_tokens
            t.total_tokens += u.total_tokens
        return t

    def total_for_agent(self, agent_id: str) -> TokenUsage:
        """Obtém o uso total de token para um agente específico.

        Args:
            agent_id: O ID do agente para obter uso.

        Returns:
            Objeto TokenUsage com uso acumulado para o agente especificado.
        """
        t = TokenUsage()
        for u in self._by_agent.get(agent_id, []):
            t.prompt_tokens += u.prompt_tokens
            t.completion_tokens += u.completion_tokens
            t.total_tokens += u.total_tokens
        return t

    @property
    def call_count(self) -> int:
        """Obtém o número total de chamadas rastreadas.

        Returns:
            Número de registros de uso rastreados.
        """
        return len(self._records)

    def reset(self) -> None:
        """Redefine todos os dados de uso rastreados."""
        self._records.clear()
        self._by_agent.clear()
