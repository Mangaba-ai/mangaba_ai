"""
Memória de curto prazo (janela deslizante) para Mangaba AI v3.0

Mantém as últimas *N* interações em uma lista. Sem persistência — quando o
processo termina as memórias desaparecem.
"""

from __future__ import annotations

import uuid
from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional

from mangaba.memory.base import BaseMemory


class ShortTermMemory(BaseMemory):
    """Memória de janela deslizante em processo.

    Esta implementação de memória mantém as últimas N interações em um deque.
    Sem persistência — quando o processo termina as memórias desaparecem.

    Attributes:
        max_items: O número máximo de itens para armazenar na memória.
        _store: Um deque armazenando entradas de memória com limitação automática de tamanho.
    """

    def __init__(self, max_items: int = 50) -> None:
        """Inicializa a ShortTermMemory.

        Args:
            max_items: O número máximo de itens para armazenar (padrão: 50).
        """
        self.max_items = max_items
        self._store: Deque[Dict[str, Any]] = deque(maxlen=max_items)

    def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Adiciona uma entrada de memória à janela deslizante.

        Args:
            content: O conteúdo para armazenar.
            metadata: Metadados opcionais associados ao conteúdo.

        Returns:
            O ID único da entrada de memória armazenada.
        """
        entry_id = uuid.uuid4().hex[:12]
        entry: Dict[str, Any] = {
            "id": entry_id,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        self._store.append(entry)
        return entry_id

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Realiza busca simples por palavras-chave nas memórias armazenadas.

        Args:
            query: A consulta de busca.
            top_k: O número máximo de resultados a retornar (padrão: 5).

        Returns:
            Uma lista de entradas de memória ordenadas por pontuação de correspondência de palavras-chave.
        """
        q_lower = query.lower()
        scored = []
        for entry in self._store:
            text = entry["content"].lower()
            # Score = number of query words found in the content
            score = sum(1 for w in q_lower.split() if w in text)
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:top_k]]

    def get_all(self) -> List[Dict[str, Any]]:
        """Retorna todas as memórias armazenadas.

        Returns:
            Uma lista de todas as entradas de memória no armazenamento.
        """
        return list(self._store)

    def clear(self) -> None:
        """Limpa todas as memórias armazenadas."""
        self._store.clear()

    @property
    def size(self) -> int:
        """Retorna o número atual de memórias armazenadas.

        Returns:
            O número de itens atualmente no armazenamento de memória.
        """
        return len(self._store)
