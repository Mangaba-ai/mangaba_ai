"""Implementação de armazenamento de vetores SQLite para Mangaba AI."""

import sqlite3
import json
import uuid
import math
from typing import List, Dict, Any, Optional
from mangaba.vectorstores import BaseVectorStore


class SQLiteVectorStore(BaseVectorStore):
    """Armazenamento de vetores apoiado por SQLite com busca de similaridade de cosseno.

    Esta implementação armazena embeddings como JSON no SQLite e realiza
    busca de similaridade de cosseno em Python.

    Attributes:
        conn: A conexão com o banco de dados SQLite.
    """

    def __init__(self, db_path: str = "mangaba_memory.db"):
        """Inicializa o SQLiteVectorStore.

        Args:
            db_path: O caminho para o arquivo de banco de dados SQLite (padrão: "mangaba_memory.db").
        """
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self) -> None:
        """Cria a tabela de armazenamento de vetores se ela não existir."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS vector_store (
                id TEXT PRIMARY KEY, content TEXT, embedding TEXT, metadata TEXT
            )
        """)
        self.conn.commit()

    def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Armazena textos com seus embeddings no SQLite.

        Args:
            texts: Uma lista de strings de texto para armazenar.
            embeddings: Uma lista de vetores de embedding correspondentes aos textos.
            metadatas: Lista opcional de dicionários de metadados para cada texto.

        Returns:
            Uma lista de IDs para as entradas armazenadas.
        """
        ids = []
        for i, (text, emb) in enumerate(zip(texts, embeddings)):
            eid = uuid.uuid4().hex[:12]
            meta = json.dumps(metadatas[i] if metadatas else {})
            self.conn.execute(
                "INSERT INTO vector_store VALUES (?, ?, ?, ?)",
                (eid, text, json.dumps(emb), meta),
            )
            ids.append(eid)
        self.conn.commit()
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
        cursor = self.conn.execute(
            "SELECT id, content, embedding, metadata FROM vector_store"
        )
        results = []
        for row in cursor:
            emb = json.loads(row[2])
            score = self._cosine_similarity(query_embedding, emb)
            results.append(
                {
                    "id": row[0],
                    "content": row[1],
                    "score": score,
                    "metadata": json.loads(row[3]),
                }
            )
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Calcula a similaridade de cosseno entre dois vetores.

        Args:
            v1: Primeiro vetor.
            v2: Segundo vetor.

        Returns:
            A pontuação de similaridade de cosseno entre 0 e 1.
        """
        dot = sum(x * y for x, y in zip(v1, v2))
        mag1 = math.sqrt(sum(x**2 for x in v1))
        mag2 = math.sqrt(sum(x**2 for x in v2))
        return dot / (mag1 * mag2) if mag1 * mag2 != 0 else 0.0

    def delete(self, ids: List[str]) -> None:
        """Exclui entradas por ID.

        Args:
            ids: Uma lista de IDs para excluir.
        """
        self.conn.executemany(
            "DELETE FROM vector_store WHERE id = ?", [(i,) for i in ids]
        )
        self.conn.commit()

    def clear(self) -> None:
        """Remove todas as entradas da tabela."""
        self.conn.execute("DELETE FROM vector_store")
        self.conn.commit()

    @property
    def count(self) -> int:
        """Retorna o número de entradas armazenadas.

        Returns:
            O número de entradas na tabela.
        """
        return self.conn.execute("SELECT COUNT(*) FROM vector_store").fetchone()[0]
