"""
Memória de longo prazo apoiada por SQLite para Mangaba AI v3.0

Persiste memórias em disco e suporta busca de similaridade vetorial opcional
quando um provedor de embedding está disponível (retorna para busca por palavras-chave).
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from mangaba.memory.base import BaseMemory


_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    embedding TEXT DEFAULT NULL,
    created_at TEXT NOT NULL
);
"""


class LongTermMemory(BaseMemory):
    """Memória persistente apoiada por SQLite com busca de embedding opcional.

    Esta implementação de memória persiste memórias em disco e suporta
    busca de similaridade vetorial opcional quando um provedor de embedding
    está disponível (retorna para busca por palavras-chave).

    Attributes:
        db_path: O caminho para o arquivo de banco de dados SQLite.
        embedding_fn: Callable opcional que recebe texto e retorna um vetor.
        _conn: A conexão do banco de dados SQLite.
    """

    def __init__(
        self,
        db_path: str = "mangaba_memory.db",
        embedding_fn: Optional[Any] = None,
    ) -> None:
        """Inicializa a LongTermMemory.

        Args:
            db_path: O caminho para o arquivo de banco de dados SQLite (padrão: "mangaba_memory.db").
            embedding_fn: Callable opcional que recebe texto e retorna um vetor
                para busca de similaridade.
        """
        self.db_path = db_path
        self.embedding_fn = embedding_fn  # callable(text) -> List[float]
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(_CREATE_TABLE)
        self._conn.commit()

    # ── public API ─────────────────────────────────────────────────────

    def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Adiciona uma entrada de memória ao banco de dados.

        Args:
            content: O conteúdo para armazenar.
            metadata: Metadados opcionais associados ao conteúdo.

        Returns:
            O ID único da entrada de memória armazenada.
        """
        entry_id = uuid.uuid4().hex[:12]
        embedding_json: Optional[str] = None
        if self.embedding_fn:
            vec = self.embedding_fn(content)
            embedding_json = json.dumps(vec)

        self._conn.execute(
            "INSERT INTO memories (id, content, metadata, embedding, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                entry_id,
                content,
                json.dumps(metadata or {}),
                embedding_json,
                datetime.now().isoformat(),
            ),
        )
        self._conn.commit()
        return entry_id

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Busca por memórias relevantes para a consulta.

        Args:
            query: A consulta de busca.
            top_k: O número máximo de resultados a retornar (padrão: 5).

        Returns:
            Uma lista de entradas de memória ordenadas por relevância.
        """
        if self.embedding_fn:
            return self._vector_search(query, top_k)
        return self._keyword_search(query, top_k)

    def get_all(self) -> List[Dict[str, Any]]:
        """Retorna todas as memórias armazenadas.

        Returns:
            Uma lista de todas as entradas de memória no banco de dados, ordenadas por tempo de criação.
        """
        rows = self._conn.execute(
            "SELECT id, content, metadata, created_at FROM memories ORDER BY created_at DESC"
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def clear(self) -> None:
        """Limpa todas as memórias armazenadas do banco de dados."""
        self._conn.execute("DELETE FROM memories")
        self._conn.commit()

    def close(self) -> None:
        """Fecha a conexão do banco de dados."""
        self._conn.close()

    # ── internals ──────────────────────────────────────────────────────

    def _keyword_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Realiza busca baseada em palavras-chave.

        Args:
            query: A consulta de busca.
            top_k: O número máximo de resultados a retornar.

        Returns:
            Uma lista de entradas de memória ordenadas por pontuação de correspondência de palavras-chave.
        """
        rows = self._conn.execute(
            "SELECT id, content, metadata, created_at FROM memories"
        ).fetchall()
        q_lower = query.lower()
        scored = []
        for r in rows:
            text = r[1].lower()
            score = sum(1 for w in q_lower.split() if w in text)
            if score > 0:
                scored.append((score, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [self._row_to_dict(r) for _, r in scored[:top_k]]

    def _vector_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Realiza busca de similaridade vetorial.

        Args:
            query: A consulta de busca.
            top_k: O número máximo de resultados a retornar.

        Returns:
            Uma lista de entradas de memória ordenadas por similaridade de cosseno.
        """
        query_vec = self.embedding_fn(query)
        rows = self._conn.execute(
            "SELECT id, content, metadata, created_at, embedding FROM memories WHERE embedding IS NOT NULL"
        ).fetchall()
        scored = []
        for r in rows:
            vec = json.loads(r[4])
            sim = self._cosine_similarity(query_vec, vec)
            scored.append((sim, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [self._row_to_dict(r[:4]) for _, r in scored[:top_k]]

    @staticmethod
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
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def _row_to_dict(row: tuple) -> Dict[str, Any]:
        """Converte uma linha do banco de dados para um dicionário.

        Args:
            row: Uma tupla representando uma linha do banco de dados.

        Returns:
            Um dicionário com chaves: id, content, metadata, created_at.
        """
        return {
            "id": row[0],
            "content": row[1],
            "metadata": json.loads(row[2]) if row[2] else {},
            "created_at": row[3],
        }
