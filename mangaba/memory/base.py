"""
Abstração base de memória para Mangaba AI v3.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseMemory(ABC):
    """Armazenamento de memória abstrato que agentes podem ler e escrever.

    Esta classe base define a interface para todas as implementações de memória,
    fornecendo métodos para armazenar, recuperar e gerenciar entradas de memória.
    """

    @abstractmethod
    def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Armazena uma informação na memória.

        Args:
            content: O conteúdo para armazenar na memória.
            metadata: Metadados opcionais associados ao conteúdo.

        Returns:
            Um identificador único para a entrada de memória armazenada.
        """
        ...

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Recupera as memórias mais relevantes para uma consulta.

        Args:
            query: A consulta de busca para encontrar memórias relevantes.
            top_k: O número máximo de resultados a retornar (padrão: 5).

        Returns:
            Uma lista de entradas de memória, cada uma como um dicionário contendo
            conteúdo e metadados.
        """
        ...

    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Retorna todas as entradas de memória armazenadas.

        Returns:
            Uma lista de todas as entradas de memória no armazenamento de memória.
        """
        ...

    @abstractmethod
    def clear(self) -> None:
        """Apaga todas as memórias armazenadas."""
        ...

    def get_relevant(self, query: str, max_results: int = 5) -> str:
        """Retorna memórias relevantes como uma string formatada para injeção de prompt.

        Args:
            query: A consulta de busca para encontrar memórias relevantes.
            max_results: O número máximo de resultados a retornar (padrão: 5).

        Returns:
            Uma string formatada contendo memórias relevantes, ou uma string
            vazia se nenhuma memória relevante for encontrada.
        """
        results = self.search(query, top_k=max_results)
        if not results:
            return ""
        lines = [f"- {r.get('content', '')}" for r in results]
        return "Relevant memories:\n" + "\n".join(lines)
