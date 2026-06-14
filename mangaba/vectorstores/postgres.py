"""
Armazenamento de vetores PostgreSQL usando extensão pgvector para busca de similaridade de vetores.

Requer servidor PostgreSQL com extensão pgvector habilitada.
Instale com: pip install mangaba[postgres]
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, List, Optional

from mangaba.vectorstores.base import BaseVectorStore

try:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb

    POSTGRES_AVAILABLE = True
except ImportError:
    psycopg = None
    dict_row = None
    Jsonb = None
    POSTGRES_AVAILABLE = False


class PostgresVectorStore(BaseVectorStore):
    """Armazenamento de vetores apoiado por PostgreSQL com extensão pgvector.

    Esta implementação usa a extensão pgvector do PostgreSQL para busca
    eficiente de similaridade de vetores usando índices HNSW.

    Attributes:
        _table_name: O nome da tabela que armazena vetores.
        _vector_dimensions: A dimensionalidade dos vetores.
        _conn: A conexão com o banco de dados PostgreSQL.
    """

    def __init__(
        self,
        url: str | None = None,
        table_name: str = "mangaba_vectors",
        vector_dimensions: int = 1536,
        create_table: bool = True,
        **kwargs: Any,
    ) -> None:
        """Inicializa o PostgresVectorStore.

        Args:
            url: URL de conexão PostgreSQL. Se não fornecido, tentará ler das
                variáveis de ambiente MANGABA_VECTORSTORE_URL ou DATABASE_URL.
            table_name: O nome da tabela para usar (padrão: "mangaba_vectors").
            vector_dimensions: A dimensionalidade dos vetores (padrão: 1536).
            create_table: Se deve criar a tabela se ela não existir (padrão: True).
            **kwargs: Argumentos adicionais passados para psycopg.connect.

        Raises:
            ImportError: Se o pacote psycopg não estiver instalado.
            ValueError: Se nenhuma URL de conexão for fornecida.
        """
        if psycopg is None:
            raise ImportError(
                "psycopg package is required. Install with: pip install mangaba[postgres]"
            )

        resolved_url = (
            url or os.getenv("MANGABA_VECTORSTORE_URL") or os.getenv("DATABASE_URL")
        )
        if not resolved_url:
            raise ValueError(
                "PostgreSQL connection URL is required. "
                "Pass it as 'url' parameter or set MANGABA_VECTORSTORE_URL / DATABASE_URL env var."
            )

        self._table_name = table_name
        self._vector_dimensions = vector_dimensions
        self._conn: psycopg.Connection = psycopg.connect(
            resolved_url, row_factory=dict_row, **kwargs
        )

        if create_table:
            self._ensure_table()

    def _ensure_table(self) -> None:
        """Garante que a tabela e extensões necessárias existam."""
        with self._conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._table_name} (
                    id VARCHAR(12) PRIMARY KEY,
                    text TEXT NOT NULL,
                    embedding VECTOR({self._vector_dimensions}),
                    metadata JSONB DEFAULT '{{}}'
                )
            """)
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS {self._table_name}_embedding_idx
                ON {self._table_name}
                USING hnsw (embedding vector_cosine_ops)
            """)
        self._conn.commit()

    def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Armazena textos com seus embeddings no PostgreSQL.

        Args:
            texts: Uma lista de strings de texto para armazenar.
            embeddings: Uma lista de vetores de embedding correspondentes aos textos.
            metadatas: Lista opcional de dicionários de metadados para cada texto.

        Returns:
            Uma lista de IDs para as entradas armazenadas.
        """
        ids: List[str] = []
        rows = []

        for i, (text, emb) in enumerate(zip(texts, embeddings)):
            eid = uuid.uuid4().hex[:12]
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            rows.append((eid, text, emb, metadata))
            ids.append(eid)

        with self._conn.cursor() as cur:
            for eid, text, emb, metadata in rows:
                metadata_value = Jsonb(metadata) if Jsonb is not None else metadata
                cur.execute(
                    f"INSERT INTO {self._table_name} (id, text, embedding, metadata) VALUES (%s, %s, %s::vector, %s::jsonb)",
                    (eid, text, json.dumps(emb), metadata_value),
                )
        self._conn.commit()
        return ids

    def search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Busca entradas similares usando similaridade de vetores.

        Args:
            query_embedding: O vetor de embedding de consulta.
            top_k: O número máximo de resultados para retornar (padrão: 5).

        Returns:
            Uma lista de dicionários contendo id, content, score e metadata
            para cada resultado, ordenados por pontuação de similaridade.
        """
        emb_str = json.dumps(query_embedding)
        with self._conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, text, metadata,
                       1 - (embedding <=> %s::vector) AS score
                FROM {self._table_name}
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (emb_str, emb_str, top_k),
            )
            rows = cur.fetchall()

        output = []
        for row in rows:
            metadata = row["metadata"] if isinstance(row["metadata"], dict) else {}
            output.append(
                {
                    "id": row["id"],
                    "content": row["text"],
                    "score": float(row["score"]),
                    "metadata": metadata,
                }
            )

        return output

    def delete(self, ids: List[str]) -> None:
        """Exclui entradas por ID.

        Args:
            ids: Uma lista de IDs para excluir.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {self._table_name} WHERE id = ANY(%s)",
                (ids,),
            )
        self._conn.commit()

    def clear(self) -> None:
        """Remove todas as entradas da tabela."""
        with self._conn.cursor() as cur:
            cur.execute(f"DELETE FROM {self._table_name}")
        self._conn.commit()

    @property
    def count(self) -> int:
        """Retorna o número de entradas armazenadas.

        Returns:
            O número de entradas na tabela.
        """
        with self._conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {self._table_name}")
            return cur.fetchone()["count"]

    def close(self) -> None:
        """Fecha a conexão com o banco de dados."""
        self._conn.close()

    def __del__(self) -> None:
        """Limpeza quando o objeto é excluído."""
        try:
            self.close()
        except Exception:
            pass
