"""
Abstração base de embedding para Mangaba AI v3.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class BaseEmbedding(ABC):
    """Interface abstrata para provedores de embedding de texto."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Retorna o vetor de embedding para um único texto."""
        ...

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings para múltiplos textos. Padrão: chama embed_text em loop."""
        return [self.embed_text(t) for t in texts]

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensionalidade dos vetores de embedding."""
        ...
