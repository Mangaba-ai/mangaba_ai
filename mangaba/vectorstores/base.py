"""
Abstração base de armazenamento de vetores para Mangaba AI v3.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseVectorStore(ABC):
    """Armazenamento de vetores abstrato para busca de similaridade baseada em embeddings.

    Esta classe base define a interface para todas as implementações de armazenamento
    de vetores, fornecendo métodos para armazenar, buscar e gerenciar embeddings de vetores.
    """

    @abstractmethod
    def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Armazena textos com seus embeddings.

        Args:
            texts: Uma lista de strings de texto para armazenar.
            embeddings: Uma lista de vetores de embedding correspondentes aos textos.
            metadatas: Lista opcional de dicionários de metadados para cada texto.

        Returns:
            Uma lista de IDs para as entradas armazenadas.
        """
        ...

    @abstractmethod
    def search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Encontra as entradas mais similares ao embedding de consulta.

        Args:
            query_embedding: O vetor de embedding de consulta.
            top_k: O número máximo de resultados para retornar (padrão: 5).

        Returns:
            Uma lista de dicionários contendo id, content, score e metadata
            para cada resultado.
        """
        ...

    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """Exclui entradas por ID.

        Args:
            ids: Uma lista de IDs para excluir.
        """
        ...

    @abstractmethod
    def clear(self) -> None:
        """Remove todas as entradas do armazenamento de vetores."""
        ...

    @property
    @abstractmethod
    def count(self) -> int:
        """Retorna o número de entradas armazenadas.

        Returns:
            O número de entradas no armazenamento de vetores.
        """
        ...
