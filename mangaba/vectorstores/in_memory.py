"""
Armazenamento de vetores em memória usando similaridade de cosseno em Python puro.

Sem dependências externas — adequado como padrão quando numpy/faiss
não estão instalados.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from mangaba.vectorstores.base import BaseVectorStore


class InMemoryVectorStore(BaseVectorStore):
    """Armazenamento de vetores simples em processo apoiado por uma lista Python.

    Esta implementação usa similaridade de cosseno em Python puro e não requer
    dependências externas, tornando-a adequada como padrão quando numpy/faiss
    não estão instalados.

    Attributes:
        _entries: Uma lista de dicionários contendo id, text, embedding e metadata.
    """

    def __init__(self) -> None:
        """Inicializa o InMemoryVectorStore."""
        self._entries: List[Dict[str, Any]] = []  # {id, text, embedding, metadata}

    def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Armazena textos com seus embeddings na memória.

        Args:
            texts: Uma lista de strings de texto para armazenar.
            embeddings: Uma lista de vetores de embedding correspondentes aos textos.
            metadatas: Lista opcional de dicionários de metadados para cada texto.

        Returns:
            Uma lista de IDs para as entradas armazenadas.
        """
        ids: List[str] = []
        for i, (text, emb) in enumerate(zip(texts, embeddings)):
            eid = uuid.uuid4().hex[:12]
            self._entries.append(
                {
                    "id": eid,
                    "text": text,
                    "embedding": emb,
                    "metadata": (
                        metadatas[i] if metadatas and i < len(metadatas) else {}
                    ),
                }
            )
            ids.append(eid)
        return ids

    def search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Busca entradas similares usando similaridade de cosseno.

        Args:
            query_embedding: O vetor de embedding de consulta.
            top_k: O número máximo de resultados para retornar (padrão: 5).

        Returns:
            Uma lista de dicionários contendo id, content, score e metadata
            para cada resultado, ordenados por pontuação de similaridade.
        """
        scored = []
        for entry in self._entries:
            sim = _cosine_similarity(query_embedding, entry["embedding"])
            scored.append((sim, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "id": e["id"],
                "content": e["text"],
                "score": s,
                "metadata": e["metadata"],
            }
            for s, e in scored[:top_k]
        ]

    def delete(self, ids: List[str]) -> None:
        """Exclui entradas por ID.

        Args:
            ids: Uma lista de IDs para excluir.
        """
        id_set = set(ids)
        self._entries = [e for e in self._entries if e["id"] not in id_set]

    def clear(self) -> None:
        """Remove todas as entradas do armazenamento."""
        self._entries.clear()

    @property
    def count(self) -> int:
        """Retorna o número de entradas armazenadas.

        Returns:
            O número de entradas no armazenamento.
        """
        return len(self._entries)


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calcula a similaridade de cosseno entre dois vetores.

    Args:
        a: Primeiro vetor.
        b: Segundo vetor.

    Returns:
        A pontuação de similaridade de cosseno entre 0 e 1.
    """
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
